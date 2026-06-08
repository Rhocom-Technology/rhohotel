import hashlib
import hmac
import json

import frappe
import requests
from frappe.utils import cint, date_diff, flt, getdate, nowdate


@frappe.whitelist(allow_guest=True)
def room_list_with_rates():
    room_types = frappe.get_all(
        "Hotel Room Type",
        filters={"is_active": 1},
        fields=[
            "name",
            "room_type",
            "capacity",
            "base_adult",
            "max_adult",
            "base_child",
            "max_child",
            "extra_bed_capacity",
            "show_on_home",
            "show_on_website",
        ],
    )

    # Fetch only default rates
    all_rates = frappe.get_all(
        "Hotel Room Rate",
        filters={"is_active": 1, "is_default": 1},
        fields=[
            "room_type",
            "rate_code",
            "rate_amount",
            "description",
            "market_segment",
            "plan",
            "meal_plan",
            "cancellation_policy",
            "min_stay",
            "max_stay",
        ],
    )

    default_rate_map = {r["room_type"]: r for r in all_rates}

    result = []

    for rt in room_types:
        rt_name = rt["name"]
        doc = frappe.get_doc("Hotel Room Type", rt_name)

        amenities = [
            {"item": row.item, "billable": row.billable}
            for row in (doc.amenities or [])
        ]
        inventory = [
            {"item": row.item, "quantity": row.quantity}
            for row in (doc.standard_inventory or [])
        ]
        images = [
            {"image": row.image, "caption": row.caption}
            for row in (doc.hotel_room_images or [])
        ]

        result.append({
            **rt,
            "short_description":   doc.short_description   or "",
            "website_description": doc.website_description or "",
            "amenities":           amenities,
            "standard_inventory":  inventory,
            "images":              images,
            "rate":                default_rate_map.get(rt_name),
        })

    return {"success": True, "room_types": result}


# ---------------------------------------------------------------------------
# Helpers – room type / capacity
# ---------------------------------------------------------------------------


def _normalise_room_type(value):
    """Return None for any sentinel that means 'any room type'."""
    if not value or str(value).strip().lower() in ("", "any available room", "all"):
        return None
    return str(value).strip()


def _validate_room_type_capacity(room_type, adults, children):
    """
    Check that the given guest count fits within the room type's configured limits.
    Returns (True, None) when OK, or (False, error_message) on failure.
    Limits that are zero / unset on the doctype are skipped.
    """
    if not room_type:
        return True, None

    rt_doc = frappe.db.get_value(
        "Hotel Room Type",
        room_type,
        ["capacity", "max_adult", "max_child"],
        as_dict=True,
    )

    if not rt_doc:
        return False, f"Room type '{room_type}' not found."

    capacity  = cint(rt_doc.get("capacity")  or 0)
    max_adult = cint(rt_doc.get("max_adult") or 0)
    max_child = cint(rt_doc.get("max_child") or 0)

    if capacity and (adults + children) > capacity:
        return False, (
            f"Room type '{room_type}' has a maximum capacity of {capacity} guest(s). "
            f"Requested: {adults + children}."
        )
    if max_adult and adults > max_adult:
        return False, (
            f"Room type '{room_type}' allows a maximum of {max_adult} adult(s). "
            f"Requested: {adults}."
        )
    if max_child and children > max_child:
        return False, (
            f"Room type '{room_type}' allows a maximum of {max_child} child(ren). "
            f"Requested: {children}."
        )

    return True, None


def _parse_rooms_requested(rooms_requested, fallback_room_type, fallback_count):
    """
    Normalise rooms_requested into a list of {"room_type": str, "count": int} dicts.
    Every entry MUST have a valid room_type — None / blank is rejected.
    Returns (parsed_list, error_string_or_None).
    """
    if rooms_requested:
        if isinstance(rooms_requested, str):
            try:
                rooms_requested = json.loads(rooms_requested)
            except (ValueError, TypeError):
                rooms_requested = None

    if not rooms_requested:
        rt = _normalise_room_type(fallback_room_type)
        if not rt:
            return None, "Room type is required."
        return [{"room_type": rt, "count": max(1, cint(fallback_count or 1))}], None

    parsed = []
    for idx, item in enumerate(rooms_requested, start=1):
        rt    = _normalise_room_type(item.get("room_type"))
        count = max(1, cint(item.get("count") or 1))
        if not rt:
            return None, f"Room type is required for item {idx} in rooms_requested."
        parsed.append({"room_type": rt, "count": count})

    return parsed, None


# ---------------------------------------------------------------------------
# Helpers – Paystack
# ---------------------------------------------------------------------------


def _get_paystack_keys():
    """
    Return (public_key, secret_key) from Hotel Settings.
    Raises a clean ValidationError if either key is missing.
    """
    settings   = frappe.get_single("Hotel Settings")
    public_key = (settings.paystack_public_key or "").strip()
    secret_key = (settings.get_password("paystack_secret_key") or "").strip()

    if not public_key or not secret_key:
        frappe.throw("Paystack keys are not configured in Hotel Settings.")

    return public_key, secret_key


def _call_paystack(method, path, secret_key, payload=None):
    """
    Make an authenticated request to the Paystack API.
    Returns the parsed JSON response dict.
    Raises frappe.ValidationError on non-2xx or network failure.
    """
    url     = f"https://api.paystack.co{path}"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type":  "application/json",
    }

    try:
        if method.upper() == "POST":
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.RequestException as exc:
        frappe.log_error(str(exc), "Paystack – network error")
        frappe.throw(f"Could not reach Paystack: {exc}")

    try:
        data = resp.json()
    except Exception:
        frappe.throw(f"Unexpected Paystack response (HTTP {resp.status_code}).")

    if not resp.ok:
        msg = data.get("message") or f"Paystack error (HTTP {resp.status_code})"
        frappe.log_error(json.dumps(data), "Paystack – API error")
        frappe.throw(msg)

    return data


def _verify_paystack_signature(payload_bytes, signature_header, secret_key):
    """
    Verify Paystack webhook HMAC-SHA512 signature.
    Returns True if valid, False otherwise.
    """
    expected = hmac.new(
        secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def _create_invoice_for_online_reservation(reservation_name):
    """
    Create a Sales Invoice for an online reservation without touching the
    reservation_invoices child table (which causes an append/meta bug when
    the doc is freshly reloaded after a db_set).

    Returns the Sales Invoice name or None.
    """
    from frappe.utils import flt, getdate

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    # Already has an invoice — return it
    if doc.sales_invoice:
        return doc.sales_invoice

    if not doc.rooms:
        frappe.log_error(
            f"Reservation {reservation_name} has no rooms — cannot create invoice.",
            "online_reservation_invoice",
        )
        return None

    # Resolve or create customer
    customer = doc.customer
    if not customer:
        customer = frappe.db.get_value(
            "Customer",
            {"customer_name": doc.primary_guest_name or ""},
            "name",
        )
    if not customer:
        cust_doc = frappe.get_doc({
            "doctype":        "Customer",
            "customer_name":  doc.primary_guest_name or reservation_name,
            "customer_type":  "Individual",
            "customer_group": frappe.db.get_default("customer_group") or "Individual",
            "territory":      frappe.db.get_default("territory")       or "Nigeria",
            "mobile_no":      doc.primary_guest_phone or "",
            "email_id":       doc.primary_guest_email or "",
        })
        cust_doc.insert(ignore_permissions=True)
        customer = cust_doc.name
        frappe.db.set_value("Hotel Reservation", reservation_name, "customer", customer)

    # Build invoice items from room rows
    items = []
    for room in doc.rooms:
        item_code = (
            frappe.db.get_value("Hotel Room", room.room_number, "erpnext_item")
            or room.room_number
        )
        if not frappe.db.exists("Item", item_code):
            frappe.log_error(
                f"No Item found for room {room.room_number} — skipping.",
                "online_reservation_invoice",
            )
            continue
        items.append({
            "item_code":   item_code,
            "qty":         1,
            "rate":        flt(room.room_total or 0),
            "description": (
                f"Reservation {reservation_name} – room {room.room_number} "
                f"({doc.number_of_nights} night(s), {doc.from_date} to {doc.to_date})"
            ),
        })

    if not items:
        frappe.log_error(
            f"No billable items for reservation {reservation_name}.",
            "online_reservation_invoice",
        )
        return None

    si = frappe.get_doc({
        "doctype":       "Sales Invoice",
        "customer":      customer,
        "posting_date":  frappe.utils.today(),
        "due_date":      str(doc.to_date or frappe.utils.today()),
        "update_stock":  0,
        "items":         items,
    })
    si.set_taxes()
    previous_user = frappe.session.user
    try:
        frappe.set_user("Administrator")
        si.insert(ignore_permissions=True)
        si.submit()
    finally:
        frappe.set_user(previous_user)

    # Store invoice on reservation via db_set to avoid child table issues
    frappe.db.set_value(
        "Hotel Reservation", reservation_name, "sales_invoice", si.name,
        update_modified=False,
    )

    return si.name


@frappe.whitelist(allow_guest=True)
def _confirm_reservation_after_payment(reservation_name, paystack_reference, amount_paid):
    """
    Shared post-payment confirmation logic — called by both verify_reservation_payment
    and paystack_webhook so the logic never diverges.

    Steps:
      1. Set reservation_status = Confirmed, payment_status = Paid
      2. Store Paystack reference in transaction_id
      3. Create the Sales Invoice
      4. Create the Payment Entry

    Fully idempotent — safe to call multiple times for the same reservation
    (handles duplicate webhook deliveries gracefully).
    """
    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    # Already confirmed and paid — nothing to do
    if doc.reservation_status == "Confirmed" and doc.payment_status == "Paid":
        return doc

    # 1. Update reservation status and submit the document
    # Submission is required so ERPNext can create accounting entries against it.
    doc.reservation_status = "Confirmed"
    doc.payment_status     = "Paid"
    doc.transaction_id     = paystack_reference

    if doc.docstatus == 0:
        # Save first to capture the status changes, then submit
        doc.save(ignore_permissions=True)
        doc.submit()
    else:
        # Already submitted — just update the fields via db_set
        frappe.db.set_value(
            "Hotel Reservation",
            reservation_name,
            {
                "reservation_status": "Confirmed",
                "payment_status":     "Paid",
                "transaction_id":     paystack_reference,
            },
            update_modified=True,
        )

    frappe.db.commit()

    # 2. Create Sales Invoice (uses our own helper to avoid child-table append bug)
    sales_invoice = None
    try:
        sales_invoice = _create_invoice_for_online_reservation(reservation_name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Invoice creation failed for reservation {reservation_name}",
        )

    # 3. Create Payment Entry
    if sales_invoice:
        try:
            _create_payment_entry_for_online_reservation(
                reservation_name, sales_invoice, paystack_reference, flt(amount_paid)
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Payment Entry creation failed for reservation {reservation_name}",
            )

    frappe.db.commit()
    
    try:
        confirmed_doc = frappe.get_doc("Hotel Reservation", reservation_name)
        _send_confirmation_email(confirmed_doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"_confirm_reservation_after_payment – confirmation email failed for {reservation_name}",
        )

    # Return a fresh copy so callers get the updated status fields
    return frappe.get_doc("Hotel Reservation", reservation_name)


def _create_payment_entry_for_online_reservation(
    reservation_name, sales_invoice, paystack_reference, amount_paid
):
    """
    Create and submit a Payment Entry for an online reservation payment.
    Links the entry to the Sales Invoice and the reservation.
    """
    invoice  = frappe.get_doc("Sales Invoice", sales_invoice)
    company  = invoice.company or frappe.db.get_single_value("Global Defaults", "default_company")

    # Resolve Paystack Mode of Payment account
    mop_account = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": "Paystack", "company": company},
        "default_account",
    )
    if not mop_account:
        frappe.log_error(
            f"No account configured for Paystack Mode of Payment in company {company}.",
            "online_reservation_payment_entry",
        )
        return None

    receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")
    if not receivable_account:
        frappe.log_error(
            f"No default receivable account for company {company}.",
            "online_reservation_payment_entry",
        )
        return None

    allocated = min(flt(amount_paid), flt(invoice.outstanding_amount))
    if allocated <= 0:
        return None

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type    = "Receive"
    pe.company         = company
    pe.party_type      = "Customer"
    pe.party           = invoice.customer
    pe.paid_from       = receivable_account
    pe.paid_to         = mop_account
    pe.paid_amount     = allocated
    pe.received_amount = allocated
    pe.posting_date    = nowdate()
    pe.mode_of_payment = "Paystack"
    pe.reference_no    = paystack_reference
    pe.reference_date  = nowdate()
    pe.remarks         = f"Online payment via Paystack - {paystack_reference}"

    pe.append("references", {
        "reference_doctype":  "Sales Invoice",
        "reference_name":     sales_invoice,
        "total_amount":       flt(invoice.grand_total),
        "outstanding_amount": flt(invoice.outstanding_amount),
        "allocated_amount":   allocated,
    })

    previous_user = frappe.session.user
    try:
        frappe.set_user("Administrator")
        pe.insert(ignore_permissions=True)
        pe.submit()
    finally:
        frappe.set_user(previous_user)

    frappe.db.set_value(
        "Hotel Reservation", reservation_name, "payment_entry", pe.name,
        update_modified=False,
    )

    return pe.name


# ---------------------------------------------------------------------------
# Expiry – scheduled job to expire unpaid Hold reservations
# ---------------------------------------------------------------------------


def expire_unpaid_online_reservations():
    """
    Mark Hold reservations as Expired when their check-in date has passed
    and payment is still Pending.

    Called by a scheduled job (daily). Releasing expired reservations back to
    inventory is automatic since get_available_rooms() already excludes
    'Expired' from its conflict query.
    """
    today = nowdate()

    expired = frappe.get_all(
        "Hotel Reservation",
        filters={
            "reservation_status": "Hold",
            "payment_status":     "Pending",
            "source_channel":     "Online",
            "to_date":            ["<", today],
        },
        fields=["name"],
    )

    for res in expired:
        try:
            frappe.db.set_value(
                "Hotel Reservation",
                res["name"],
                "reservation_status",
                "Expired",
                update_modified=True,
            )
            frappe.logger().info(f"Expired unpaid online reservation: {res['name']}")
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Failed to expire reservation {res['name']}",
            )

    if expired:
        frappe.db.commit()


# ---------------------------------------------------------------------------
# Online Reservation - Availability Check
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def check_online_availability(
    check_in_date=None,
    check_out_date=None,
    room_type=None,
    number_of_rooms=1,
    adults=1,
    children=0,
):
    """
    Return available room types (with counts and pricing) for the requested period.

    All conflict detection is delegated entirely to get_available_rooms() in
    room_availability.py — no availability logic is duplicated here.

    Returns:
        {
            "success": True,
            "available": bool,
            "check_in_date": "...",
            "check_out_date": "...",
            "nights": int,
            "adults": int,
            "children": int,
            "number_of_rooms": int,
            "room_types": [
                {
                    "room_type": "Standard",
                    "available_count": 3,
                    "rate_per_night": 25000.0,
                    "total_amount": 75000.0,
                    "description": "...",
                    "image": "...",
                }
            ]
        }
    """
    from rhohotel.rhocom_hotel.utils.room_availability import get_available_rooms

    if not check_in_date:
        return {"success": False, "message": "Check-in date is required."}
    if not check_out_date:
        return {"success": False, "message": "Check-out date is required."}

    try:
        nights = date_diff(getdate(check_out_date), getdate(check_in_date))
    except Exception:
        return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}

    if nights < 1:
        return {"success": False, "message": "Check-out date must be after check-in date."}

    if getdate(check_in_date) < getdate(nowdate()):
        return {"success": False, "message": "Check-in date cannot be in the past."}

    room_type_filter = _normalise_room_type(room_type)
    number_of_rooms  = max(1, cint(number_of_rooms or 1))
    adults           = max(1, cint(adults   or 1))
    children         = max(0, cint(children or 0))

    try:
        available_rooms = get_available_rooms(
            check_in_dt=check_in_date,
            check_out_dt=check_out_date,
            room_type=room_type_filter,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "check_online_availability failed")
        return {"success": False, "message": "Could not check availability. Please try again."}

    type_map = {}
    for room in available_rooms:
        rt = room.get("room_type")
        if not rt:
            continue
        valid, _ = _validate_room_type_capacity(rt, adults, children)
        if not valid:
            continue
        if rt not in type_map:
            type_map[rt] = {
                "room_type":       rt,
                "available_count": 0,
                "rate_per_night":  flt(room.get("rate_per_night") or 0),
                "total_amount":    flt(room.get("total_amount")   or 0),
            }
        type_map[rt]["available_count"] += 1

    for rt_name, rt_data in type_map.items():
        doc = frappe.get_doc("Hotel Room Type", rt_name)

        rt_data["short_description"]   = doc.short_description   or ""
        rt_data["website_description"] = doc.website_description or ""
        rt_data["capacity"]            = doc.capacity            or 0
        rt_data["max_adult"]           = doc.max_adult           or 0
        rt_data["max_child"]           = doc.max_child           or 0

        rt_data["amenities"] = [
            {"item": row.item, "billable": row.billable}
            for row in (doc.amenities or [])
        ]
        rt_data["images"] = [
            {"image": row.image, "caption": row.caption}
            for row in (doc.hotel_room_images or [])
        ]
        rt_data["standard_inventory"] = [
            {"item": row.item, "quantity": row.quantity}
            for row in (doc.standard_inventory or [])
        ]

    room_types = [
        data for data in type_map.values()
        if data["available_count"] >= number_of_rooms
    ]
    room_types.sort(key=lambda x: x["room_type"])

    return {
        "success":         True,
        "available":       len(room_types) > 0,
        "check_in_date":   check_in_date,
        "check_out_date":  check_out_date,
        "nights":          nights,
        "adults":          adults,
        "children":        children,
        "number_of_rooms": number_of_rooms,
        "room_types":      room_types,
    }


# ---------------------------------------------------------------------------
# Online Reservation – Submit Booking
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def submit_online_reservation(
    check_in_date=None,
    check_out_date=None,
    room_type=None,
    number_of_rooms=1,
    rooms_requested=None,
    adults=1,
    children=0,
    guest_name=None,
    guest_email=None,
    guest_phone=None,
    special_requests=None,
    extras=None,
):
    """
    Create a Hotel Reservation (status = Hold) from an online booking submission.

    Simple call:
        room_type="Deluxe", number_of_rooms=2

    Multi-type call:
        rooms_requested='[{"room_type": "Deluxe", "count": 1}, {"room_type": "Standard", "count": 2}]'

    Returns:
        {
            "success": True,
            "reservation": "RES-2026-00001",
            "message": "...",
            "summary": { ... }
        }
    """
    from rhohotel.rhocom_hotel.utils.room_availability import get_available_rooms

    if not guest_name:
        return {"success": False, "message": "Guest name is required."}
    if not guest_email:
        return {"success": False, "message": "Guest email is required."}
    if not check_in_date:
        return {"success": False, "message": "Check-in date is required."}
    if not check_out_date:
        return {"success": False, "message": "Check-out date is required."}

    try:
        nights = date_diff(getdate(check_out_date), getdate(check_in_date))
    except Exception:
        return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}

    if nights < 1:
        return {"success": False, "message": "Check-out date must be after check-in date."}

    # Check-in date must not be in the past
    if getdate(check_in_date) < getdate(nowdate()):
        return {"success": False, "message": "Check-in date cannot be in the past."}

    adults   = max(1, cint(adults   or 1))
    children = max(0, cint(children or 0))

    requests_list, parse_error = _parse_rooms_requested(rooms_requested, room_type, number_of_rooms)
    if parse_error:
        return {"success": False, "message": parse_error}

    # Single availability query — one round-trip, per-type selection done in Python
    try:
        all_available = get_available_rooms(
            check_in_dt=check_in_date,
            check_out_dt=check_out_date,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "submit_online_reservation – availability failed")
        return {"success": False, "message": "Could not check availability. Please try again."}

    pool_by_type = {}
    for room in all_available:
        rt = room.get("room_type")
        if not rt:
            continue
        pool_by_type.setdefault(rt, []).append(room)

    selected_rooms = []

    for req in requests_list:
        rt    = req["room_type"]
        count = req["count"]

        valid, msg = _validate_room_type_capacity(rt, adults, children)
        if not valid:
            return {"success": False, "message": msg}

        already_selected = {r["name"] for r in selected_rooms}
        candidates = [
            r for r in pool_by_type.get(rt, [])
            if r["name"] not in already_selected
        ]

        if len(candidates) < count:
            return {
                "success": False,
                "message": (
                    f"Only {len(candidates)} room(s) of type '{rt}' are available "
                    f"for the selected dates, but {count} were requested."
                ),
            }

        selected_rooms.extend(candidates[:count])

    if not selected_rooms:
        return {"success": False, "message": "No rooms could be selected. Please adjust your request."}

    notes_parts = [f"Adults: {adults}"]
    if children:
        notes_parts.append(f"Children: {children}")
    if extras and str(extras).strip() not in ("", "No extras"):
        notes_parts.append(f"Extras: {extras}")
    if special_requests and str(special_requests).strip():
        notes_parts.append(f"Special requests: {special_requests.strip()}")
    notes_text = " | ".join(notes_parts)

    try:
        reservation = frappe.new_doc("Hotel Reservation")
        reservation.reservation_type   = "Individual"
        reservation.reservation_status = "Hold"
        reservation.payment_status     = "Pending"
        reservation.guest_profile_kind = "Primary Guest"
        reservation.primary_guest_name  = guest_name
        reservation.primary_guest_email = guest_email
        reservation.primary_guest_phone = guest_phone or ""
        reservation.from_date           = check_in_date
        reservation.to_date             = check_out_date
        reservation.number_of_nights    = nights
        reservation.source_channel      = "Online"

        if notes_text:
            reservation.comp_reason = notes_text

        for room in selected_rooms:
            reservation.append("rooms", {
                "room_number":      room["name"],
                "room_type":        room.get("room_type") or "",
                "rate_per_night":   flt(room.get("rate_per_night") or 0),
                "number_of_nights": nights,
                "room_total":       flt(room.get("total_amount")   or 0),
                "occupant_name":    guest_name,
                "occupant_email":   guest_email,
                "occupant_phone":   guest_phone or "",
            })

        # insert() triggers HotelReservation.validate() which recalculates totals
        reservation.insert(ignore_permissions=True)
        frappe.db.commit()

    except frappe.ValidationError as ve:
        return {"success": False, "message": str(ve)}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "submit_online_reservation – doc creation failed")
        return {
            "success": False,
            "message": (
                "We could not process your reservation at this time. "
                "Please try again or contact the hotel directly."
            ),
        }
        
    # Send payment link email
    try:
        link_result = create_reservation_payment_link(reservation.name)
        if link_result.get("success") and link_result.get("payment_url"):
            _send_payment_link_email(
                reservation_name=reservation.name,
                guest_email=guest_email,
                guest_name=guest_name,
                payment_url=link_result["payment_url"],
                amount=link_result.get("amount", 0),
            )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"submit_online_reservation – payment link email failed for {reservation.name}",
        )

    total_amount = sum(flt(r.get("total_amount") or 0) for r in selected_rooms)

    booked_type_counts = {}
    for room in selected_rooms:
        rt = room.get("room_type") or "Room"
        booked_type_counts[rt] = booked_type_counts.get(rt, 0) + 1
    room_type_summary = ", ".join(
        f"{cnt}x {rt}" for rt, cnt in sorted(booked_type_counts.items())
    )

    return {
        "success":     True,
        "reservation": reservation.name,
        "message":     (
            f"Your reservation ({reservation.name}) has been received. "
            f"Please proceed to payment to confirm your booking."
        ),
        "summary": {
            "reservation_number":  reservation.name,
            "guest_name":          guest_name,
            "guest_email":         guest_email,
            "check_in_date":       check_in_date,
            "check_out_date":      check_out_date,
            "nights":              nights,
            "adults":              adults,
            "children":            children,
            "rooms_booked":        len(selected_rooms),
            "room_types_booked":   room_type_summary,
            "total_amount":        total_amount,
            "status":              "Hold – Awaiting Payment",
        },
    }


# ---------------------------------------------------------------------------
# Paystack – Create Payment Link
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def create_reservation_payment_link(reservation_name=None):
    """
    Generate a Paystack payment link for a Hotel Reservation in Hold status.

    If a link was already generated (transaction_id is set), the existing
    Paystack checkout URL is returned — no duplicate transaction is created.

    Returns:
        {
            "success": True,
            "payment_url": "https://checkout.paystack.com/<access_code>",
            "access_code": "...",
            "reference": "RES-2026-00001",
            "amount": 75000.0,
            "public_key": "pk_live_...",
        }
    """
    if not reservation_name:
        return {"success": False, "message": "Reservation name is required."}

    try:
        doc = frappe.get_doc("Hotel Reservation", reservation_name)
    except frappe.DoesNotExistError:
        return {"success": False, "message": f"Reservation '{reservation_name}' not found."}

    if doc.reservation_status not in ("Hold", "Confirmed"):
        return {
            "success": False,
            "message": (
                f"Payment link can only be generated for a Hold or Confirmed reservation. "
                f"Current status: {doc.reservation_status}."
            ),
        }

    if doc.payment_status == "Paid":
        return {"success": False, "message": "This reservation has already been paid."}

    try:
        public_key, secret_key = _get_paystack_keys()
    except frappe.ValidationError as exc:
        return {"success": False, "message": str(exc)}

    # Re-use existing link if one was already generated
    if doc.transaction_id:
        access_code = doc.transaction_id
        return {
            "success":     True,
            "payment_url": f"https://checkout.paystack.com/{access_code}",
            "access_code": access_code,
            "reference":   reservation_name,
            "amount":      flt(doc.total_amount or doc.net_total or 0),
            "public_key":  public_key,
            "message":     "Using existing payment link.",
        }

    amount_naira = flt(doc.total_amount or doc.net_total or 0)
    if amount_naira <= 0:
        return {"success": False, "message": "Reservation total is zero. Cannot create payment link."}

    # Paystack requires amount in kobo (× 100, integer)
    amount_kobo = int(amount_naira * 100)

    payload = {
        "email":     doc.primary_guest_email or "guest@hotel.com",
        "amount":    amount_kobo,
        "reference": reservation_name,   # reservation name is unique — ties webhook back to doc
        "currency":  "NGN",
        "callback_url": (
            f"{frappe.utils.get_url()}/booking-success"
            f"?reference={reservation_name}"
        ),
        # "callback_url": (
        #     f"{frappe.utils.get_url()}/api/method/"
        #     f"rhohotel.hotel_api.verify_reservation_payment"
        #     f"?reference={reservation_name}"
        # ),
        "metadata": {
            "reservation": reservation_name,
            "guest_name":  doc.primary_guest_name or "",
            "check_in":    str(doc.from_date or ""),
            "check_out":   str(doc.to_date   or ""),
        },
    }

    try:
        data = _call_paystack("POST", "/transaction/initialize", secret_key, payload)
    except frappe.ValidationError as exc:
        return {"success": False, "message": str(exc)}

    if not data.get("status"):
        return {"success": False, "message": data.get("message", "Paystack initialisation failed.")}

    tx_data     = data.get("data") or {}
    access_code = tx_data.get("access_code") or ""
    payment_url = tx_data.get("authorization_url") or f"https://checkout.paystack.com/{access_code}"

    # Persist access_code in transaction_id for retry / re-use
    doc.flags.ignore_validate_update_after_submit = True
    doc.transaction_id = access_code
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success":     True,
        "payment_url": payment_url,
        "access_code": access_code,
        "reference":   reservation_name,
        "amount":      amount_naira,
        "public_key":  public_key,
        "message":     "Redirect to payment URL.",
    }


# ---------------------------------------------------------------------------
# Paystack – Verify Payment  (browser callback after redirect)
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def verify_reservation_payment(reference=None):
    """
    Verify a Paystack transaction and confirm the reservation.

    Paystack redirects the guest's browser here after checkout.
    The `reference` query param is the Hotel Reservation name.

    Returns:
        {
            "success": True,
            "reservation": "RES-2026-00001",
            "payment_status": "Paid",
            "reservation_status": "Confirmed",
            "message": "Payment verified. Your reservation is confirmed.",
        }
    """
    if not reference:
        return {"success": False, "message": "Payment reference is required."}

    try:
        _, secret_key = _get_paystack_keys()
    except frappe.ValidationError as exc:
        return {"success": False, "message": str(exc)}

    try:
        data = _call_paystack("GET", f"/transaction/verify/{reference}", secret_key)
    except frappe.ValidationError as exc:
        return {"success": False, "message": str(exc)}

    tx_data = data.get("data") or {}
    status  = tx_data.get("status")

    if status != "success":
        return {
            "success": False,
            "message": f"Payment not successful. Paystack status: {status}.",
        }

    amount_kobo  = flt(tx_data.get("amount") or 0)
    amount_naira = amount_kobo / 100
    paystack_ref = tx_data.get("reference") or reference

    if not frappe.db.exists("Hotel Reservation", reference):
        return {"success": False, "message": f"Reservation '{reference}' not found."}

    try:
        doc = _confirm_reservation_after_payment(reference, paystack_ref, amount_naira)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"verify_reservation_payment – confirm failed for {reference}",
        )
        return {
            "success": False,
            "message": "Payment verified but reservation confirmation failed. Please contact the hotel.",
        }
        
    room_type_counts = {}

    for room in (doc.rooms or []):
        room_type = room.room_type or "Unknown"
        room_type_counts[room_type] = room_type_counts.get(room_type, 0) + 1
        
    return {
        "success": True,
        "reservation": reference,

        "guest_name": doc.primary_guest_name,
        "guest_email": doc.primary_guest_email,
        "guest_phone": doc.primary_guest_phone,

        "check_in_date": str(doc.from_date or ""),
        "check_out_date": str(doc.to_date or ""),
        "number_of_nights": doc.number_of_nights,

        "number_of_rooms": len(doc.rooms or []),

        # e.g. {"Deluxe Room": 2, "Executive Suite": 1}
        "room_type_summary": room_type_counts,

        "subtotal": flt(doc.subtotal or 0),
        "discount_amount": flt(doc.discount_amount or 0),
        "total_amount": flt(doc.total_amount or 0),
        "net_total": flt(doc.net_total or doc.total_amount or 0),

        "payment_status": doc.payment_status,
        "reservation_status": doc.reservation_status,

        "message": "Payment verified. Your reservation is confirmed.",
    }

# ---------------------------------------------------------------------------
# Paystack – Webhook  (server-to-server, authoritative confirmation)
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def paystack_webhook():
    """
    Receive and process Paystack webhook events.

    Endpoint (POST):
        /api/method/rhohotel.rhohotel.hotel_api.paystack_webhook

    The HMAC-SHA512 signature in X-Paystack-Signature is verified before
    any processing happens. Unrecognised events are acknowledged with 200
    so Paystack stops retrying them.

    Supported event: charge.success
    """
    if frappe.request.method != "POST":
        frappe.throw("Method not allowed.", frappe.PermissionError)

    raw_body  = frappe.request.data
    signature = frappe.get_request_header("X-Paystack-Signature") or ""

    try:
        _, secret_key = _get_paystack_keys()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "paystack_webhook – could not load keys")
        return {"status": "error", "message": "Configuration error."}

    # Signature verification — reject unsigned / tampered payloads
    if not _verify_paystack_signature(raw_body, signature, secret_key):
        frappe.log_error(
            f"Invalid signature. Header: {signature}",
            "paystack_webhook – signature mismatch",
        )
        # Return 200 so Paystack doesn't keep retrying; logged for investigation
        return {"status": "ignored", "message": "Invalid signature."}

    try:
        event = json.loads(raw_body)
    except (ValueError, TypeError):
        frappe.log_error(str(raw_body), "paystack_webhook – invalid JSON")
        return {"status": "error", "message": "Invalid JSON body."}

    event_type = event.get("event")
    tx_data    = event.get("data") or {}

    if event_type != "charge.success":
        return {"status": "ignored", "message": f"Event '{event_type}' not handled."}

    if tx_data.get("status") != "success":
        return {"status": "ignored", "message": "Transaction not successful."}

    paystack_ref     = tx_data.get("reference") or ""
    amount_naira     = flt(tx_data.get("amount") or 0) / 100
    reservation_name = paystack_ref   # reference was set to reservation name during init

    if not reservation_name:
        frappe.log_error(str(event), "paystack_webhook – missing reference in payload")
        return {"status": "error", "message": "Missing reference."}

    if not frappe.db.exists("Hotel Reservation", reservation_name):
        frappe.log_error(
            f"Reservation '{reservation_name}' not found.",
            "paystack_webhook – unknown reservation",
        )
        return {"status": "ignored", "message": "Reservation not found."}

    try:
        _confirm_reservation_after_payment(reservation_name, paystack_ref, amount_naira)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"paystack_webhook – confirmation failed for {reservation_name}",
        )
        return {"status": "error", "message": "Reservation confirmation failed."}

    return {"status": "success", "reservation": reservation_name}


def _send_payment_link_email(reservation_name, guest_email, guest_name, payment_url, amount):
    try:
        template = frappe.get_doc("Email Template", "reservation-payment-link")
        context = frappe._dict(
            name=reservation_name,
            guest_name=guest_name,
            payment_url=payment_url,
            amount=amount,
        )
        frappe.sendmail(
            recipients=[guest_email],
            subject=frappe.render_template(template.subject, {"doc": context}),
            message=frappe.render_template(template.response_html, {"doc": context}),
            now=True,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"_send_payment_link_email – failed for {reservation_name}",
        )


def _send_confirmation_email(doc):
    if not doc.primary_guest_email:
        return

    try:
        template = frappe.get_doc("Email Template", "reservation-confirmation")

        room_type_counts = {}
        for room in (doc.rooms or []):
            rt = room.room_type or "Room"
            room_type_counts[rt] = room_type_counts.get(rt, 0) + 1

        context = frappe._dict(
            name=doc.name,
            guest_name=doc.primary_guest_name or "Guest",
            from_date=frappe.utils.formatdate(str(doc.from_date), "MMMM d, yyyy"),
            to_date=frappe.utils.formatdate(str(doc.to_date), "MMMM d, yyyy"),
            number_of_nights=doc.number_of_nights,
            total_amount=flt(doc.total_amount or doc.net_total or 0),
            room_type_summary=room_type_counts,
        )

        frappe.sendmail(
            recipients=[doc.primary_guest_email],
            subject=frappe.render_template(template.subject, {"doc": context}),
            message=frappe.render_template(template.response_html, {"doc": context}),
            now=True,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"_send_confirmation_email – failed for {doc.name}",
        )