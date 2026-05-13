import frappe
from frappe.utils import now_datetime, add_days, flt, cint, get_datetime
import json


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
    """Load single check-in with invoices."""
    if not frappe.db.exists("Hotel Room Check In", name):
        frappe.throw(f"Check-in {name} not found")

    doc = frappe.get_doc("Hotel Room Check In", name)
    checkin = doc.as_dict()

    # Fetch invoices linked via custom field — gracefully skip if column doesn't exist
    invoices = []
    try:
        invoices = frappe.db.sql("""
            SELECT name AS invoice, grand_total AS amount, outstanding_amount,
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
                   posting_date, status, 'POS Invoice' AS invoice_type
            FROM `tabPOS Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, name, as_dict=1) or []
    except Exception:
        pass

    checkin["invoices"] = list(invoices) + list(pos_invoices)
    return checkin


@frappe.whitelist()
def search_guests(query=""):
    """Search Hotel Guest by name/phone/email for autocomplete."""
    if not query or len(query.strip()) < 2:
        return []

    q = f"%{query.strip()}%"
    guests = frappe.db.sql("""
        SELECT name, hotel_guest_name, phone_number, email, guest_type, preference, id_type
        FROM `tabHotel Guest`
        WHERE hotel_guest_name LIKE %s
            OR phone_number LIKE %s
            OR email LIKE %s
            OR name LIKE %s
        ORDER BY hotel_guest_name
        LIMIT 10
    """, (q, q, q, q), as_dict=1)

    return guests


@frappe.whitelist()
def search_reservations(query=""):
    """Search Hotel Room Reservation by name, guest name, or phone for autocomplete.

    Returns active reservations not yet checked in. When query is empty,
    returns the next 10 reservations by from_date.
    """
    # Status labels vary by deployment; exclude only terminal states.
    base_conditions = """
        IFNULL(r.status, '') NOT IN ('Cancelled', 'Completed', 'Checked-In', 'Checked In')
        AND NOT EXISTS (
            SELECT 1 FROM `tabHotel Room Check In` ci
            WHERE ci.reservation = r.name AND ci.docstatus != 2
        )
    """

    if query and len(query.strip()) >= 1:
        q = f"%{query.strip()}%"
        rows = frappe.db.sql(
            f"""
            SELECT r.name, r.guest_name, r.guest_phone, r.guest_email, r.room_number,
                   r.from_date, r.to_date, r.status, r.number_of_nights, r.rate
            FROM `tabHotel Room Reservation` r
            WHERE {base_conditions}
              AND (r.name LIKE %s OR r.guest_name LIKE %s OR r.guest_phone LIKE %s)
            ORDER BY r.from_date ASC
            LIMIT 10
            """,
            (q, q, q),
            as_dict=1,
        )
    else:
        rows = frappe.db.sql(
            f"""
            SELECT r.name, r.guest_name, r.guest_phone, r.guest_email, r.room_number,
                   r.from_date, r.to_date, r.status, r.number_of_nights, r.rate
            FROM `tabHotel Room Reservation` r
            WHERE {base_conditions}
            ORDER BY r.from_date ASC
            LIMIT 10
            """,
            as_dict=1,
        )

    return rows


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

        # Legacy reservations overlapping the period
        reservation_rows = frappe.db.sql(
            f"""
            SELECT DISTINCT room_number
            FROM `tabHotel Room Reservation`
            WHERE room_number IN ({placeholders})
              AND docstatus != 2
              AND status NOT IN ('Cancelled', 'Completed', 'No Show')
              AND from_date < %s
              AND to_date > %s
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
            + [r.room_number for r in reservation_rows]
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

    doc = frappe.new_doc("Hotel Room Check In")
    doc.guest = guest
    doc.room_number = room_number
    doc.room_type = room_type
    doc.rate_type = rate_type or ""
    doc.rate_amount = flt(rate_amount)
    doc.number_of_nights = cint(number_of_nights)
    doc.check_in_datetime = ci_dt
    doc.expected_check_out_datetime = expected_out
    doc.reservation = reservation or ""
    doc.reservation_source = reservation_source or ""
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
    doc.contact_number = contact_number or ""
    # Skip room availability overlap check for direct front desk check-in
    doc.flags.skip_availability_check = True

    doc.insert(ignore_permissions=True)
    doc.submit()

    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def create_refund(check_in_name, reason=""):
    """Create and submit a Hotel Refund for a check-in based on total payments received."""
    frappe.has_permission("Hotel Refund", "create", throw=True)

    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(f"Check-in {check_in_name} not found")

    check_in = frappe.get_doc("Hotel Room Check In", check_in_name)

    result = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0) AS total_paid
        FROM `tabPayment Entry`
        WHERE custom_hotel_room_check_in = %s AND docstatus = 1
    """, check_in_name, as_dict=1)
    total_paid = flt(result[0].total_paid) if result else 0

    if total_paid <= 0:
        frappe.throw("No confirmed payments found for this check-in. Cannot create refund.")

    refund = frappe.new_doc("Hotel Refund")
    refund.guest = check_in.guest
    refund.check_in = check_in.name
    refund.refund_amount = total_paid
    refund.reason = reason or f"Refund for Check In {check_in.name}"
    refund.insert(ignore_permissions=True)
    refund.submit()

    return {"name": refund.name, "refund_amount": total_paid}


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
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount,
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
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount,
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

    total_invoice = sum(flt(inv.get("amount")) for inv in invoices)
    total_outstanding = sum(flt(inv.get("outstanding_amount")) for inv in invoices)
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
