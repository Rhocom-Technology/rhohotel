import frappe
from frappe.utils import now_datetime, add_days, flt, cint, get_datetime
import json


@frappe.whitelist()
def get_checkin_list(limit=500):
    """Return check-in list with real-time payment status computed from linked Sales Invoices."""
    checkins = frappe.db.sql("""
        SELECT
            ci.name,
            ci.guest,
            ci.room_number,
            ci.check_in_datetime,
            ci.expected_check_out_datetime,
            ci.actual_check_out_datetime,
            ci.status,
            ci.reservation_source,
            ci.number_of_nights,
            COALESCE(SUM(si.grand_total), 0) AS total_invoiced,
            COALESCE(SUM(si.outstanding_amount), 0) AS total_outstanding
        FROM `tabHotel Room Check In` ci
        LEFT JOIN `tabSales Invoice` si
            ON si.custom_hotel_room_check_in = ci.name
            AND si.docstatus = 1
        GROUP BY ci.name
        ORDER BY ci.check_in_datetime DESC
        LIMIT %(limit)s
    """, {"limit": cint(limit)}, as_dict=1)
    return checkins


@frappe.whitelist()
def get_checkin_stats():
    """Header stat cards for check-in list and overview."""
    total = frappe.db.count("Hotel Room Check In")
    in_house = frappe.db.count("Hotel Room Check In", {"status": "Checked In", "docstatus": 1})
    overdue = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabHotel Room Check In`
        WHERE status = 'Checked In' AND docstatus = 1
        AND expected_check_out_datetime < NOW()
    """)[0][0]
    outstanding_total = frappe.db.sql("""
        SELECT COALESCE(SUM(total_outstanding_amount), 0)
        FROM `tabHotel Room Check In`
        WHERE status = 'Checked In' AND docstatus = 1
        AND total_outstanding_amount > 0
    """)[0][0] or 0

    return {
        "total": total,
        "in_house": in_house,
        "overdue": int(overdue),
        "outstanding": f"\u20a6{flt(outstanding_total):,.2f}",
    }


@frappe.whitelist()
def get_checkin_detail(name):
    """Load single check-in with invoices, acquired bills, and payment entries."""
    if not frappe.db.exists("Hotel Room Check In", name):
        frappe.throw(f"Check-in {name} not found")

    doc = frappe.get_doc("Hotel Room Check In", name)
    checkin = doc.as_dict()
    checkin["reservation"] = checkin.get("reservation") or doc.canonical_reservation or ""
    if doc.canonical_reservation and not checkin.get("reservation_source"):
        checkin["reservation_source"] = "Reservation"

    # Fetch invoices linked via custom field — gracefully skip if column doesn't exist
    invoices = []
    try:
        invoices = frappe.db.sql("""
            SELECT name AS invoice, grand_total AS amount, outstanding_amount, is_return,
                   posting_date, status, 'Sales Invoice' AS invoice_type
            FROM `tabSales Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, name, as_dict=1) or []
    except Exception:
        pass

    pos_invoices = []
    try:
        pos_invoices = frappe.db.sql("""
            SELECT name AS invoice, grand_total AS amount, outstanding_amount,
                   posting_date, status, 'POS Invoice' AS invoice_type,
                   consolidated_invoice
            FROM `tabPOS Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, name, as_dict=1) or []
    except Exception:
        pass

    # ── Room-posting detection ────────────────────────────────────────────
    # POS Invoices posted to a room have `consolidated_invoice` pointing to
    # the Sales Invoice created by post_bill_to_room.  Use this link to:
    #  1. Re-label the Sales Invoice as 'Restaurant' (it's an F&B folio charge).
    #  2. Exclude the consolidated POS Invoice from the list — the Sales Invoice
    #     already carries the correct outstanding balance; showing both would
    #     create a duplicate row.

    si_names = [inv["invoice"] for inv in invoices]
    room_posting_pos_names = set()  # POS Invoice names that are room-posting refs

    if si_names:
        try:
            room_pi_rows = frappe.db.sql("""
                SELECT name AS invoice, consolidated_invoice
                FROM `tabPOS Invoice`
                WHERE consolidated_invoice IN %s AND docstatus = 1
            """, (tuple(si_names),), as_dict=1) or []

            for row in room_pi_rows:
                room_posting_pos_names.add(row["invoice"])
                # Mark matching Sales Invoice as a restaurant/F&B charge
                for inv in invoices:
                    if inv["invoice"] == row["consolidated_invoice"]:
                        inv["invoice_type"] = "Restaurant"
        except Exception:
            pass

    # Exclude consolidated room-posting POS Invoices — already represented
    # by their corresponding Sales Invoice on the folio.
    filtered_pos_invoices = [
        inv for inv in pos_invoices
        if inv["invoice"] not in room_posting_pos_names
    ]

    merged_invoices = list(invoices) + list(filtered_pos_invoices)

    # Acquired bills — Bill Transfer records where this check-in is the recipient
    acquired_bills = []
    try:
        acquired_bills = frappe.db.sql("""
            SELECT name, from_guest, source_invoice, total_amount, status,
                   creation AS transfer_date, reason, journal_entry
            FROM `tabBill Transfer`
            WHERE to_check_in = %s AND status != 'Cancelled'
            ORDER BY creation DESC
        """, name, as_dict=1) or []
    except Exception:
        pass

    # Compute outstanding amount for each approved acquired bill from its JE
    for bill in acquired_bills:
        outstanding = 0.0
        je_name = bill.get("journal_entry")
        if je_name and bill.get("status") == "Approved":
            try:
                debit_total = frappe.db.sql("""
                    SELECT COALESCE(SUM(debit_in_account_currency), 0)
                    FROM `tabJournal Entry Account`
                    WHERE parent = %s AND debit_in_account_currency > 0 AND party_type = 'Customer'
                """, je_name)[0][0] or 0

                paid = frappe.db.sql("""
                    SELECT COALESCE(SUM(per.allocated_amount), 0)
                    FROM `tabPayment Entry Reference` per
                    JOIN `tabPayment Entry` pe ON per.parent = pe.name
                    WHERE per.reference_doctype = 'Journal Entry'
                    AND per.reference_name = %s
                    AND pe.docstatus = 1
                    AND pe.payment_type = 'Receive'
                """, je_name)[0][0] or 0

                outstanding = max(0.0, float(debit_total) - float(paid))
            except Exception:
                outstanding = float(bill.get("total_amount") or 0)
        bill["outstanding_amount"] = outstanding

    checkin["acquired_bills"] = list(acquired_bills)

    # Payment entries linked to this check-in (include draft=0 in case submit failed)
    payments = []
    try:
        payments = frappe.db.sql("""
            SELECT name AS payment_id, paid_amount, payment_type,
                   posting_date, mode_of_payment, remarks, docstatus
            FROM `tabPayment Entry`
            WHERE custom_hotel_room_check_in = %s AND docstatus IN (0, 1)
            ORDER BY posting_date DESC
        """, name, as_dict=1) or []
    except Exception:
        pass

    merged_payments = list(payments)

    # If this check-in came from a canonical reservation, include reservation-level
    # invoice/payment ledger so front desk does not lose billing context.
    # Corporate reservations are billed on the corporate account and should not
    # show reservation-level invoices on individual occupant folios.
    include_reservation_ledger = True
    if doc.canonical_reservation and frappe.db.exists("Hotel Reservation", doc.canonical_reservation):
        reservation_type = frappe.db.get_value(
            "Hotel Reservation",
            doc.canonical_reservation,
            "reservation_type",
        )
        if reservation_type == "Corporate":
            include_reservation_ledger = False

    if include_reservation_ledger and doc.canonical_reservation and frappe.db.exists("Hotel Reservation", doc.canonical_reservation):
        try:
            from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import get_payment_summary_for_reservation

            summary = get_payment_summary_for_reservation(doc.canonical_reservation) or {}

            existing_invoice_names = {row.get("invoice") for row in merged_invoices}
            for inv in summary.get("invoices") or []:
                inv_name = inv.get("name")
                if not inv_name or inv_name in existing_invoice_names:
                    continue
                merged_invoices.append(
                    {
                        "invoice": inv_name,
                        "amount": inv.get("grand_total") or 0,
                        "outstanding_amount": inv.get("outstanding_amount") or 0,
                        "is_return": inv.get("is_return") or 0,
                        "posting_date": inv.get("posting_date"),
                        "status": inv.get("status"),
                        "invoice_type": "Reservation Invoice",
                    }
                )
                existing_invoice_names.add(inv_name)

            existing_payment_names = {row.get("payment_id") or row.get("name") for row in merged_payments}
            for payment in summary.get("payment_entries") or []:
                pay_name = payment.get("name")
                if not pay_name or pay_name in existing_payment_names:
                    continue
                merged_payments.append(
                    {
                        "payment_id": pay_name,
                        "paid_amount": payment.get("amount") or payment.get("paid_amount") or 0,
                        "payment_type": "Receive",
                        "posting_date": payment.get("posting_date"),
                        "mode_of_payment": payment.get("mode_of_payment"),
                        "remarks": payment.get("remarks"),
                        "docstatus": 1,
                    }
                )
                existing_payment_names.add(pay_name)
        except Exception:
            pass

    checkin["invoices"] = merged_invoices
    checkin["payments"] = merged_payments

    return checkin


@frappe.whitelist()
def search_guests(query="", guest_type="", in_house_only=""):
    """Search Hotel Guest by name/phone/email for autocomplete."""
    if not query or len(query.strip()) < 2:
        return []

    q = f"%{query.strip()}%"
    type_clause = "AND hg.guest_type = %s" if guest_type else ""
    params = (q, q, q, q, guest_type) if guest_type else (q, q, q, q)

    # When in_house_only is set, restrict to guests with an active check-in
    in_house_clause = ""
    if in_house_only and str(in_house_only) not in ("0", "false", "False", ""):
        in_house_clause = "AND EXISTS (SELECT 1 FROM `tabHotel Room Check In` ci WHERE ci.guest = hg.name AND ci.status = 'Checked In')"

    guests = frappe.db.sql(f"""
        SELECT hg.name, hg.hotel_guest_name, hg.phone_number, hg.email, hg.guest_type,
               hg.preference, hg.id_type, hg.id_number,
               (SELECT ci.room_number FROM `tabHotel Room Check In` ci
                WHERE ci.guest = hg.name AND ci.status = 'Checked In'
                ORDER BY ci.check_in_datetime DESC LIMIT 1) AS room_number
        FROM `tabHotel Guest` hg
        WHERE (hg.hotel_guest_name LIKE %s
            OR hg.phone_number LIKE %s
            OR hg.email LIKE %s
            OR hg.name LIKE %s)
        {type_clause}
        {in_house_clause}
        ORDER BY hg.hotel_guest_name
        LIMIT 10
    """, params, as_dict=1)

    return guests


@frappe.whitelist()
def search_reservations(query=""):
    """Search canonical Hotel Reservation by name, guest name, or phone for autocomplete.

    Returns active reservations not yet fully checked in.
    """
    # -----------------------------------------------------------------------
    # Canonical: Hotel Reservation
    # -----------------------------------------------------------------------
    canonical_base = """
        hr.reservation_status NOT IN ('Cancelled', 'Checked Out', 'No Show', 'Expired')
        AND hr.docstatus != 2
    """

    if query and len(query.strip()) >= 1:
        q = f"%{query.strip()}%"
        canonical_rows = frappe.db.sql(
            f"""
            SELECT hr.name, hr.primary_guest_name AS guest_name,
                   hr.primary_guest_phone AS guest_phone,
                   hr.primary_guest_email AS guest_email,
                   NULL AS room_number,
                   hr.from_date, hr.to_date,
                   hr.reservation_status AS status,
                   hr.number_of_nights,
                   NULL AS rate,
                   hr.reservation_type,
                   hr.group_name,
                   'canonical' AS source_type
            FROM `tabHotel Reservation` hr
            WHERE {canonical_base}
              AND (hr.name LIKE %s OR hr.primary_guest_name LIKE %s OR hr.primary_guest_phone LIKE %s OR hr.group_name LIKE %s)
            ORDER BY hr.from_date ASC
            LIMIT 10
            """,
            (q, q, q, q),
            as_dict=1,
        )
    else:
        canonical_rows = frappe.db.sql(
            f"""
            SELECT hr.name, hr.primary_guest_name AS guest_name,
                   hr.primary_guest_phone AS guest_phone,
                   hr.primary_guest_email AS guest_email,
                   NULL AS room_number,
                   hr.from_date, hr.to_date,
                   hr.reservation_status AS status,
                   hr.number_of_nights,
                   NULL AS rate,
                   hr.reservation_type,
                   hr.group_name,
                   'canonical' AS source_type
            FROM `tabHotel Reservation` hr
            WHERE {canonical_base}
            ORDER BY hr.from_date ASC
            LIMIT 10
            """,
            as_dict=1,
        )

    canonical_rows.sort(key=lambda r: str(r.get("from_date") or ""))
    return canonical_rows[:15]


@frappe.whitelist()
def get_room_types():
    """List available Hotel Room Types."""
    types = frappe.get_all("Hotel Room Type", fields=["name"], order_by="name")
    return types


@frappe.whitelist()
def get_rooms_for_transfer(current_room="", check_in_dt=None, check_out_dt=None):
    """Return rooms eligible for a room-transfer operation.

    Unlike get_available_rooms (which restricts to status=Vacant), this returns
    all rooms that do NOT have an active, overlapping check-in — excluding the
    guest's current room and rooms under Maintenance.
    """
    from rhohotel.rhocom_hotel.utils.room_availability import _normalize_dt

    # Get all rooms except Maintenance and the current room
    filters = {"status": ["not in", ["Maintenance"]]}
    if current_room:
        filters["name"] = ["!=", current_room]

    rooms = frappe.get_all(
        "Hotel Room",
        fields=["name", "room_number", "room_type", "floor", "status"],
        filters=filters,
        order_by="room_number",
    )
    if not rooms:
        return []

    # Exclude rooms with overlapping active check-ins
    if check_in_dt and check_out_dt:
        ci_str = _normalize_dt(check_in_dt).strftime("%Y-%m-%d %H:%M:%S")
        co_str = _normalize_dt(check_out_dt).strftime("%Y-%m-%d %H:%M:%S")
        room_names = [r.name for r in rooms]
        placeholders = ", ".join(["%s"] * len(room_names))
        busy = frappe.db.sql(
            f"""
            SELECT DISTINCT room_number
            FROM `tabHotel Room Check In`
            WHERE room_number IN ({placeholders})
              AND status IN ('Draft', 'Checked In')
              AND check_in_datetime < %s
              AND expected_check_out_datetime > %s
            """,
            tuple(room_names) + (co_str, ci_str),
            as_dict=True,
        )
        busy_set = {r.room_number for r in busy}
        rooms = [r for r in rooms if r.name not in busy_set]
    else:
        # No dates: only return Vacant rooms (safe default)
        rooms = [r for r in rooms if r.get("status") == "Vacant"]

    # Attach tariff rate
    tariff_map = {}
    for room in rooms:
        rt = room.get("room_type")
        if rt and rt not in tariff_map:
            tariff = frappe.get_all(
                "Hotel Room Tariff",
                filters={"room_type": rt, "is_active": 1},
                fields=["rate_amount"],
                limit=1,
            )
            tariff_map[rt] = tariff[0].rate_amount if tariff else 0
        room["default_rate"] = tariff_map.get(rt, 0)

    return rooms


@frappe.whitelist()
def get_available_rooms(room_type="", check_in_dt=None, check_out_dt=None, exclude_reservation=None):
    """Get rooms available for the given period, optionally filtered by room type.

    When check_in_dt / check_out_dt are supplied the result is filtered through
    the full room-availability engine (all three booking surfaces).  When dates
    are omitted the function falls back to a simple status = 'Vacant' query.

    exclude_reservation: Hotel Reservation name whose room allocations should be
    treated as available (used when checking in from an existing reservation).
    """
    from rhohotel.rhocom_hotel.utils.room_availability import _normalize_dt

    use_availability = bool(check_in_dt and check_out_dt)

    if use_availability:
        ci_dt = _normalize_dt(check_in_dt)
        co_dt = _normalize_dt(check_out_dt)
        ci_str = ci_dt.strftime("%Y-%m-%d %H:%M:%S")
        co_str = co_dt.strftime("%Y-%m-%d %H:%M:%S")

    # --- 1. Candidate rooms (basic filters) ---
    filters = {"status": "Vacant"}
    if room_type:
        filters["room_type"] = room_type

    rooms = frappe.get_all(
        "Hotel Room",
        fields=["name", "room_number", "room_type", "floor"],
        filters=filters,
        order_by="room_number",
    )

    if not rooms:
        return []

    # --- 2. Exclude rooms with active bookings across all surfaces ---
    if use_availability:
        room_names = [r.name for r in rooms]
        placeholders = ", ".join(["%s"] * len(room_names))

        # Active check-ins overlapping the period
        checkin_rows = frappe.db.sql(
            f"""
            SELECT DISTINCT room_number
            FROM `tabHotel Room Check In`
            WHERE room_number IN ({placeholders})
              AND status IN ('Draft', 'Checked In')
              AND check_in_datetime < %s
              AND expected_check_out_datetime > %s
            """,
            tuple(room_names) + (co_str, ci_str),
            as_dict=True,
        )

        # Canonical Hotel Reservation allocations overlapping the period
        canonical_rows = frappe.db.sql(
            f"""
            SELECT DISTINCT rr.room_number
            FROM `tabHotel Reservation Room` rr
            INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
            WHERE rr.room_number IN ({placeholders})
              AND hr.docstatus != 2
              AND hr.reservation_status NOT IN
                  ('Cancelled', 'Checked Out', 'No Show', 'Expired')
              AND hr.from_date < %s
              AND hr.to_date > %s
              AND hr.name != %s
            """,
            tuple(room_names) + (co_str, ci_str, exclude_reservation or ''),
            as_dict=True,
        )

        unavailable = set(
            [r.room_number for r in checkin_rows]
            + [r.room_number for r in canonical_rows]
        )
        rooms = [r for r in rooms if r.name not in unavailable]

    # --- 3. Attach default tariff rate ---
    tariff_map = {}
    for room in rooms:
        rt = room.get("room_type")
        if rt and rt not in tariff_map:
            tariff = frappe.get_all(
                "Hotel Room Tariff",
                filters={"room_type": rt, "is_active": 1},
                fields=["rate_amount"],
                limit=1,
            )
            tariff_map[rt] = tariff[0].rate_amount if tariff else 0
        room["default_rate"] = tariff_map.get(rt, 0)

    return rooms


@frappe.whitelist()
def create_checkin(
    guest,
    room_number,
    room_type,
    rate_amount,
    number_of_nights,
    check_in_datetime=None,
    rate_type="",
    reservation="",
    canonical_reservation="",
    reservation_source="",
    discount_type="",
    discount=0,
    late_checkout=0,
    housekeeping_notes="",
    keycard_assigned="",
    room_preferences="",
    id_type="",
    contact_number="",
):
    """Create and submit a Hotel Room Check In."""
    frappe.has_permission("Hotel Room Check In", "create", throw=True)

    if not check_in_datetime:
        check_in_datetime = now_datetime()

    ci_dt = get_datetime(check_in_datetime)
    expected_out = add_days(ci_dt, cint(number_of_nights))

    from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available

    # Guard against duplicate check-ins from the same canonical reservation room.
    if canonical_reservation:
        existing_row_ref = frappe.db.get_value(
            "Hotel Reservation Room",
            {"parent": canonical_reservation, "room_number": room_number},
            ["name", "check_in_reference"],
            as_dict=True,
        )
        if existing_row_ref and existing_row_ref.get("check_in_reference"):
            frappe.throw(
                f"Room {room_number} is already checked in for reservation {canonical_reservation} "
                f"(Check-in: {existing_row_ref.get('check_in_reference')})."
            )

    # Ensure the room is actually available at this time.
    assert_room_available(
        room_number,
        ci_dt,
        expected_out,
        exclude_canonical=canonical_reservation or None,
    )

    doc = frappe.new_doc("Hotel Room Check In")
    doc.guest = guest
    doc.room_number = room_number
    doc.room_type = room_type
    doc.rate_type = rate_type or ""
    doc.rate_amount = flt(rate_amount)
    doc.number_of_nights = cint(number_of_nights)
    doc.check_in_datetime = ci_dt
    doc.expected_check_out_datetime = expected_out
    doc.reservation = reservation or canonical_reservation or ""
    doc.canonical_reservation = canonical_reservation or ""
    doc.reservation_source = reservation_source or ("Reservation" if canonical_reservation else "")
    doc.discount_type = discount_type or "None"
    doc.discount = flt(discount)
    doc.late_checkout = cint(late_checkout)
    doc.housekeeping_notes = housekeeping_notes or ""
    doc.keycard_assigned = keycard_assigned or ""
    if frappe.get_meta("Hotel Room Check In").has_field("room_preferences"):
        doc.room_preferences = room_preferences or ""
    elif room_preferences:
        pref_note = f"Room Preferences: {room_preferences}"
        doc.housekeeping_notes = (
            f"{doc.housekeeping_notes}\n{pref_note}".strip()
            if doc.housekeeping_notes else pref_note
        )
    doc.id_type = id_type or ""
    # Use the passed contact_number; fall back to the guest's phone_number (not contact_number
    # which is the "Contact Person Number" — a different person's number).
    doc.contact_number = contact_number or frappe.db.get_value("Hotel Guest", guest, "phone_number") or ""
    # Reservation check-ins often use rooms in Reserved status; allow submit after
    # explicit availability assertion above.
    doc.flags.skip_availability_check = bool(canonical_reservation)

    doc.insert(ignore_permissions=True)
    doc.submit()

    # If a canonical reservation was linked, update its status to Checked In
    # and back-link this check-in to the matching room row
    if canonical_reservation and frappe.db.exists("Hotel Reservation", canonical_reservation):
        try:
            res_doc = frappe.get_doc("Hotel Reservation", canonical_reservation)
            if res_doc.reservation_status in ("Confirmed", "Hold"):
                res_doc.flags.ignore_validate_update_after_submit = True
                res_doc.reservation_status = "Checked In"
                res_doc.check_in_time = ci_dt
                res_doc.save(ignore_permissions=True)

            # Link check-in reference to the matching room row
            for row in res_doc.rooms:
                if row.room_number == room_number and not row.check_in_reference:
                    frappe.db.set_value(
                        "Hotel Reservation Room",
                        row.name,
                        "check_in_reference",
                        doc.name,
                        update_modified=False,
                    )
                    break
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Canonical reservation update failed at check-in")

    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def create_refund(check_in_name, reason="", amount=None):
    """Create and submit a Hotel Refund for a check-in.

    amount: explicit refund amount (optional). If omitted, defaults to overpayment
            (total payments received − total invoiced charges).
    """
    frappe.has_permission("Hotel Refund", "create", throw=True)

    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(f"Check-in {check_in_name} not found")

    check_in = frappe.get_doc("Hotel Room Check In", check_in_name)

    # Total submitted payments received for this check-in
    paid_result = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0) AS total_paid
        FROM `tabPayment Entry`
        WHERE custom_hotel_room_check_in = %s AND docstatus = 1 AND payment_type = 'Receive'
    """, check_in_name, as_dict=1)
    total_paid = flt(paid_result[0].total_paid) if paid_result else 0

    if total_paid <= 0:
        frappe.throw("No confirmed payments found for this check-in. Cannot create refund.")

    # Total invoiced charges for this check-in (excluding credit notes)
    charged_result = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) AS total_charged
        FROM `tabSales Invoice`
        WHERE custom_hotel_room_check_in = %s AND docstatus = 1 AND is_return = 0
    """, check_in_name, as_dict=1)
    total_charged = flt(charged_result[0].total_charged) if charged_result else 0

    # Total already refunded via submitted Hotel Refund records
    refunded_result = frappe.db.sql("""
        SELECT COALESCE(SUM(refund_amount), 0) AS total_refunded
        FROM `tabHotel Refund`
        WHERE check_in = %s AND docstatus = 1
    """, check_in_name, as_dict=1)
    total_refunded = flt(refunded_result[0].total_refunded) if refunded_result else 0

    # Net overpayment after accounting for previous refunds
    net_overpayment = max(0.0, total_paid - total_charged - total_refunded)

    if net_overpayment <= 0:
        frappe.throw(
            "No refundable overpayment remaining for this check-in. "
            f"Total paid: ₦{total_paid:,.2f}, Total charged: ₦{total_charged:,.2f}, "
            f"Already refunded: ₦{total_refunded:,.2f}."
        )

    # Resolve refund amount
    requested = flt(amount) if amount else 0
    if requested > 0:
        if requested > net_overpayment:
            frappe.throw(
                f"Refund amount (₦{requested:,.2f}) exceeds remaining overpayment "
                f"(₦{net_overpayment:,.2f})."
            )
        refund_amount = requested
    else:
        refund_amount = net_overpayment

    refund = frappe.new_doc("Hotel Refund")
    refund.guest = check_in.guest
    refund.check_in = check_in.name
    refund.refund_amount = refund_amount
    refund.reason = reason or f"Refund for Check In {check_in.name}"
    refund.insert(ignore_permissions=True)
    refund.submit()

    return {"name": refund.name, "refund_amount": refund_amount, "total_paid": total_paid, "total_charged": total_charged, "total_refunded": total_refunded}


@frappe.whitelist()
def get_checkout_detail(check_in_name):
    """Load check-in data formatted for the checkout detail page."""
    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(f"Check-in {check_in_name} not found")

    doc = frappe.get_doc("Hotel Room Check In", check_in_name)

    # Fetch all invoices (Sales + POS) linked to this check-in — split into separate
    # queries so a missing column on one table does not silently kill both.
    invoices = []
    try:
        si_rows = frappe.db.sql("""
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount, is_return,
                   posting_date, status, 'Sales Invoice' AS invoice_type
            FROM `tabSales Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, check_in_name, as_dict=1) or []
        invoices.extend(si_rows)
    except Exception:
        pass

    try:
        pos_rows = frappe.db.sql("""
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount, 0 AS is_return,
                   posting_date, status, 'POS Invoice' AS invoice_type
            FROM `tabPOS Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, check_in_name, as_dict=1) or []
        invoices.extend(pos_rows)
    except Exception:
        pass

    # Fetch payment entries linked to this check-in
    payments = []
    try:
        payments = frappe.db.sql("""
            SELECT name AS payment_id, paid_amount, posting_date, mode_of_payment
            FROM `tabPayment Entry`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, check_in_name, as_dict=1) or []
    except Exception:
        pass

    # Exclude credit notes (is_return=1) from charge/outstanding totals
    charge_invoices = [inv for inv in invoices if not inv.get("is_return")]
    total_invoice = sum(flt(inv.get("amount")) for inv in charge_invoices)
    total_outstanding = sum(flt(inv.get("outstanding_amount")) for inv in charge_invoices)
    total_paid = total_invoice - total_outstanding

    # If no invoices, fall back to doc fields
    if not invoices:
        total_invoice = flt(doc.total_charges)
        total_outstanding = flt(doc.total_outstanding_amount)
        total_paid = total_invoice - total_outstanding

    # Fetch guest display name
    guest_display = doc.guest or ""
    if doc.guest:
        g = frappe.db.get_value(
            "Hotel Guest", doc.guest,
            ["hotel_guest_name", "phone_number"],
            as_dict=1,
        )
        if g and g.get("hotel_guest_name"):
            guest_display = g.hotel_guest_name

    return {
        "name": doc.name,
        "guest": doc.guest,
        "guest_name": guest_display,
        "room_number": doc.room_number,
        "room_type": doc.room_type,
        "check_in_datetime": str(doc.check_in_datetime) if doc.check_in_datetime else None,
        "expected_check_out_datetime": str(doc.expected_check_out_datetime) if doc.expected_check_out_datetime else None,
        "number_of_nights": doc.number_of_nights,
        "status": doc.status,
        "total_charges": flt(doc.total_charges),
        "total_outstanding_amount": flt(doc.total_outstanding_amount),
        "total_invoice": total_invoice,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "late_checkout": doc.late_checkout,
        "reservation_source": doc.reservation_source or "Walk-in",
        "invoices": invoices,
        "payments": payments,
    }


@frappe.whitelist()
def create_bill_transfer(from_check_in, to_guest, invoices, reason="", note=""):
    """Create Bill Transfer document(s) in Pending Approval state for selected invoices."""
    invoices = json.loads(invoices) if isinstance(invoices, str) else invoices
    if not invoices:
        frappe.throw("Please select at least one invoice to transfer.")

    if not frappe.db.exists("Hotel Room Check In", from_check_in):
        frappe.throw(f"Check-in {from_check_in} not found.")

    check_in_doc = frappe.get_doc("Hotel Room Check In", from_check_in)
    from_guest = check_in_doc.guest

    if from_guest == to_guest:
        frappe.throw("Cannot transfer a bill to the same guest.")

    # Determine recipient guest type
    to_guest_doc = frappe.db.get_value(
        "Hotel Guest", to_guest, ["hotel_guest_name", "guest_type"], as_dict=True
    ) or {}
    to_guest_name = to_guest_doc.get("hotel_guest_name") or to_guest
    to_guest_type = to_guest_doc.get("guest_type") or "Individual"

    # Corporate guests are billed directly — no check-in required
    if to_guest_type == "Corporate":
        to_check_in = None
        # Ensure corporate guest has a linked Customer for the JE
        corporate_customer = frappe.db.get_value("Hotel Guest", to_guest, "customer")
        if not corporate_customer:
            frappe.throw(
                f"Corporate account '{to_guest_name}' does not have a linked Customer record. "
                "Please link a Customer before transferring bills."
            )
    else:
        # Individual guests must be currently checked in
        to_check_in = frappe.db.get_value(
            "Hotel Room Check In",
            {"guest": to_guest, "status": "Checked In"},
            "name"
        )
        if not to_check_in:
            frappe.throw(
                f"{to_guest_name} is not currently checked in. "
                "Bill transfers can only be made to in-house guests or corporate accounts."
            )

    full_reason = reason
    if note:
        full_reason = f"{reason} — {note}" if reason else note

    created = []
    for inv_name in invoices:
        if not frappe.db.exists("Sales Invoice", inv_name):
            continue  # Skip POS Invoices and non-existing docs

        inv_doc = frappe.get_doc("Sales Invoice", inv_name)
        total_amount = flt(inv_doc.outstanding_amount)

        if total_amount <= 0:
            continue

        bt = frappe.new_doc("Bill Transfer")
        bt.from_guest = from_guest
        bt.from_check_in = from_check_in
        bt.to_guest = to_guest
        bt.to_check_in = to_check_in
        bt.source_invoice = inv_name
        bt.total_amount = total_amount
        bt.reason = full_reason
        bt.status = "Pending Approval"
        bt.insert(ignore_permissions=True)

        created.append({
            "name": bt.name,
            "invoice": inv_name,
            "amount": total_amount,
        })

    if not created:
        frappe.throw(
            "No eligible Sales Invoices found with outstanding balances. "
            "Only submitted Sales Invoices with outstanding amounts can be transferred."
        )

    return created


@frappe.whitelist()
def process_checkout(check_in_name, remarks="", check_out_datetime=None):
    """Create and submit Hotel Room Check Out for a given check-in."""
    frappe.has_permission("Hotel Room Check Out", "create", throw=True)

    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(f"Check-in {check_in_name} not found")

    checkin = frappe.get_doc("Hotel Room Check In", check_in_name)

    if checkin.status == "Checked Out":
        frappe.throw("This guest has already been checked out")

    if checkin.status != "Checked In":
        frappe.throw(f"Check-in is in status '{checkin.status}' — cannot check out")

    if not check_out_datetime:
        check_out_datetime = now_datetime()

    co = frappe.new_doc("Hotel Room Check Out")
    co.check_in = check_in_name
    co.room_number = checkin.room_number
    co.guest_name = checkin.guest
    co.check_in_datetime = checkin.check_in_datetime
    co.check_out_datetime = check_out_datetime
    co.late_checkout = checkin.late_checkout
    co.remarks = remarks or ""
    co.payment_status = "Paid" if flt(checkin.total_outstanding_amount) <= 0 else "Unpaid"

    co.insert(ignore_permissions=True)
    co.submit()

    return {"name": co.name, "check_in": check_in_name, "status": "Checked Out"}
