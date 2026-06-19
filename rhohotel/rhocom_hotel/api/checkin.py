import frappe
from frappe.utils import now_datetime, add_days, flt, cint, get_datetime, getdate
import json


def _valid_marketplace_source(source):
    source = (source or "").strip()
    if source and frappe.db.exists("Market Place", source):
        return source
    return ""


def _invoice_names(rows, key):
    return [row.get(key) for row in rows or [] if row.get(key)]


def _set_invoice_type(rows, key, invoice_name, invoice_type):
    for row in rows or []:
        if row.get(key) == invoice_name:
            row["invoice_type"] = invoice_type


def _normalize_sales_invoice_types(rows, key="invoice"):
    """Apply user-facing folio labels without depending on optional custom fields."""
    names = _invoice_names(rows, key)
    if not names:
        return rows

    try:
        has_source_col = frappe.db.has_column("Sales Invoice", "custom_invoice_source")
        source_select = ", COALESCE(NULLIF(si.custom_invoice_source, ''), 'Restaurant') AS invoice_source" if has_source_col else ", 'Restaurant' AS invoice_source"
        pos_links = frappe.db.sql(
            f"""
            SELECT pi.name AS pos_invoice, pi.consolidated_invoice, si.name AS si_name{source_select}
            FROM `tabPOS Invoice` pi
            LEFT JOIN `tabSales Invoice` si ON si.name = pi.consolidated_invoice
            WHERE pi.consolidated_invoice IN %s
              AND pi.docstatus = 1
            """,
            (tuple(names),),
            as_dict=1,
        ) or []
        for row in pos_links:
            if row.get("consolidated_invoice"):
                _set_invoice_type(rows, key, row.get("consolidated_invoice"), row.get("invoice_source") or "Restaurant")
    except Exception:
        pass

    try:
        meta_rows = frappe.db.sql(
            """
            SELECT
                si.name,
                COALESCE(si.remarks, '') AS remarks,
                GROUP_CONCAT(DISTINCT COALESCE(i.item_group, '') SEPARATOR ',') AS item_groups
            FROM `tabSales Invoice` si
            LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            LEFT JOIN `tabItem` i ON i.name = sii.item_code
            WHERE si.name IN %s
            GROUP BY si.name
            """,
            (tuple(names),),
            as_dict=1,
        ) or []
    except Exception:
        return rows

    meta_map = {row.name: row for row in meta_rows}
    restaurant_groups = {"kitchen", "drinks", "food", "beverage", "bar", "restaurant"}
    for row in rows or []:
        current = row.get("invoice_type")
        if current and current not in ("Sales Invoice", "POS Invoice"):
            continue

        meta = meta_map.get(row.get(key)) or {}
        remarks = str(meta.get("remarks") or "").lower()
        item_groups = {
            group.strip().lower()
            for group in str(meta.get("item_groups") or "").split(",")
            if group.strip()
        }

        if "room transfer" in remarks:
            row["invoice_type"] = "Room Transfer"
        elif "stay extension" in remarks or "stay reduction" in remarks:
            row["invoice_type"] = "Stay Adjustment"
        elif "late check-out" in remarks or "late checkout" in remarks:
            row["invoice_type"] = "Late Charges"
        elif "discount applied" in remarks:
            row["invoice_type"] = "Discount"
        elif item_groups & restaurant_groups:
            row["invoice_type"] = "Restaurant"

    return rows


def _get_group_reservation_room_for_checkin(reservation_name, check_in_name, room_number=None):
    if not reservation_name or not check_in_name:
        return None

    fields = ["name", "room_number", "split_invoice"]
    for fieldname in ("occupant_name", "guest_name", "hotel_guest"):
        if frappe.db.has_column("Hotel Reservation Room", fieldname):
            fields.append(fieldname)

    row = frappe.db.get_value(
        "Hotel Reservation Room",
        {"parent": reservation_name, "check_in_reference": check_in_name},
        fields,
        as_dict=True,
    )
    if row:
        return row

    if room_number:
        return frappe.db.get_value(
            "Hotel Reservation Room",
            {"parent": reservation_name, "room_number": room_number},
            fields,
            as_dict=True,
        )

    return None


def _get_group_room_invoice_names(reservation_doc, room_row):
    if not reservation_doc or not room_row:
        return []

    invoice_names = []
    if room_row.get("split_invoice"):
        invoice_names.append(room_row.get("split_invoice"))

    try:
        from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import _get_split_room_adjustment_invoice_names

        invoice_names.extend(_get_split_room_adjustment_invoice_names(reservation_doc, room_row))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Group room adjustment invoice lookup failed")

    return list(dict.fromkeys([name for name in invoice_names if name]))


def _get_invoice_rows_for_checkin_detail(invoice_names, invoice_type="Reservation Invoice"):
    if not invoice_names:
        return []

    invoice_type_expr = "'Sales Invoice'"
    if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
        invoice_type_expr = "COALESCE(NULLIF(custom_invoice_source, ''), %(fallback_type)s)"

    return frappe.db.sql(
        f"""
        SELECT name AS invoice, grand_total AS amount, outstanding_amount, is_return,
               posting_date, status,
               {invoice_type_expr} AS invoice_type
        FROM `tabSales Invoice`
        WHERE name IN %(invoice_names)s
          AND docstatus = 1
        ORDER BY posting_date DESC, creation DESC
        """,
        {"invoice_names": tuple(invoice_names), "fallback_type": invoice_type},
        as_dict=1,
    ) or []


def _get_payment_rows_for_invoice_names(invoice_names):
    if not invoice_names:
        return []

    return frappe.db.sql(
        """
        SELECT
            pe.name AS payment_id,
            SUM(ABS(per.allocated_amount)) AS paid_amount,
            pe.payment_type,
            pe.posting_date,
            pe.mode_of_payment,
            pe.remarks,
            pe.docstatus,
            MAX(pe.creation) AS created_at
        FROM `tabPayment Entry Reference` per
        INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE per.reference_doctype = 'Sales Invoice'
          AND per.reference_name IN %(invoice_names)s
          AND pe.docstatus IN (0, 1)
        GROUP BY pe.name, pe.payment_type, pe.posting_date, pe.mode_of_payment, pe.remarks, pe.docstatus
        ORDER BY pe.posting_date DESC, created_at DESC
        """,
        {"invoice_names": tuple(invoice_names)},
        as_dict=1,
    ) or []


@frappe.whitelist()
def get_checkin_list(limit=500):
    """Return check-in list using the synced folio balance on the check-in."""
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
            COALESCE(ci.total_outstanding_amount, 0) AS total_outstanding
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
    from rhohotel.rhocom_hotel.utils.folio import get_checkin_folio, sync_checkin_folio_totals

    try:
        folio = sync_checkin_folio_totals(name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Check-in folio summary failed")
        folio = {"sales_invoices": [], "acquired_bills": [], "summary": {}}

    checkin = doc.as_dict()
    checkin["reservation"] = checkin.get("reservation") or doc.canonical_reservation or ""
    if doc.canonical_reservation and not checkin.get("reservation_source"):
        checkin["reservation_source"] = "Reservation"

    # Fetch invoices linked via custom field. Some sites may not have the optional
    # custom_invoice_source column migrated yet, so build the label expression safely.
    invoices = []
    try:
        invoice_type_expr = "'Sales Invoice'"
        if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
            invoice_type_expr = "COALESCE(NULLIF(custom_invoice_source, ''), 'Sales Invoice')"

        invoices = frappe.db.sql(f"""
            SELECT name AS invoice, grand_total AS amount, outstanding_amount, is_return,
                   posting_date, status,
                   {invoice_type_expr} AS invoice_type
            FROM `tabSales Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, name, as_dict=1) or []
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Check-in detail invoice fetch failed")

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
            has_source_col = frappe.db.has_column("Sales Invoice", "custom_invoice_source")
            source_select = ", COALESCE(NULLIF(si.custom_invoice_source, ''), 'Restaurant') AS invoice_source" if has_source_col else ", 'Restaurant' AS invoice_source"
            room_pi_rows = frappe.db.sql(
                f"""
                SELECT pi.name AS invoice, pi.consolidated_invoice{source_select}
                FROM `tabPOS Invoice` pi
                LEFT JOIN `tabSales Invoice` si ON si.name = pi.consolidated_invoice
                WHERE pi.consolidated_invoice IN %s AND pi.docstatus = 1
                """,
                (tuple(si_names),), as_dict=1) or []

            for row in room_pi_rows:
                room_posting_pos_names.add(row["invoice"])
                # Mark matching Sales Invoice with its real source (Laundry, Bar, etc.)
                for inv in invoices:
                    if inv["invoice"] == row["consolidated_invoice"]:
                        inv["invoice_type"] = row.get("invoice_source") or "Restaurant"
        except Exception:
            pass

    _normalize_sales_invoice_types(invoices, key="invoice")

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

    folio_acquired = folio.get("acquired_bills") or []
    if folio_acquired:
        acquired_bills = folio_acquired

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

    # If this check-in came from a canonical reservation, include relevant
    # reservation ledger context. Group/corporate master ledgers must not leak
    # into one occupant's folio. For group split billing, only include the
    # reservation room row's own split invoice, adjustments, and allocations.
    include_reservation_ledger = True
    added_reservation_ledger = False
    reservation_doc = None
    reservation_type = ""
    if doc.canonical_reservation and frappe.db.exists("Hotel Reservation", doc.canonical_reservation):
        reservation_doc = frappe.get_doc("Hotel Reservation", doc.canonical_reservation)
        reservation_type = reservation_doc.reservation_type
        if reservation_type in ("Corporate", "Group"):
            include_reservation_ledger = False

    if reservation_type == "Group" and reservation_doc:
        try:
            room_row = _get_group_reservation_room_for_checkin(
                reservation_doc.name,
                doc.name,
                doc.room_number,
            )
            room_invoice_names = _get_group_room_invoice_names(reservation_doc, room_row)
            if room_invoice_names:
                existing_invoice_names = {row.get("invoice") for row in merged_invoices}
                for inv in _get_invoice_rows_for_checkin_detail(room_invoice_names, "Split Reservation Invoice"):
                    if inv.get("invoice") in existing_invoice_names:
                        continue
                    merged_invoices.append(inv)
                    added_reservation_ledger = True
                    existing_invoice_names.add(inv.get("invoice"))

                existing_payment_names = {row.get("payment_id") or row.get("name") for row in merged_payments}
                for payment in _get_payment_rows_for_invoice_names(room_invoice_names):
                    if payment.get("payment_id") in existing_payment_names:
                        continue
                    merged_payments.append(payment)
                    added_reservation_ledger = True
                    existing_payment_names.add(payment.get("payment_id"))
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Group check-in scoped ledger fetch failed")

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
                        "raw_outstanding_amount": inv.get("raw_outstanding_amount"),
                        "source_transfer_amount": inv.get("source_transfer_amount") or 0,
                        "is_return": inv.get("is_return") or 0,
                        "posting_date": inv.get("posting_date"),
                        "status": inv.get("status"),
                        "invoice_type": "Reservation Invoice",
                    }
                )
                added_reservation_ledger = True
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
                added_reservation_ledger = True
                existing_payment_names.add(pay_name)
        except Exception:
            pass

    folio_invoice_map = {row.get("name"): row for row in (folio.get("sales_invoices") or [])}
    for inv in merged_invoices:
        folio_row = folio_invoice_map.get(inv.get("invoice"))
        if not folio_row:
            continue
        inv["amount"] = folio_row.get("amount")
        inv["outstanding_amount"] = folio_row.get("net_outstanding_amount") if not folio_row.get("is_return") else folio_row.get("open_credit_amount")
        inv["raw_outstanding_amount"] = folio_row.get("raw_outstanding_amount")
        inv["net_outstanding_amount"] = folio_row.get("net_outstanding_amount")
        inv["credit_applied"] = folio_row.get("credit_applied")
        inv["open_credit_amount"] = folio_row.get("open_credit_amount")
        inv["source_transfer_amount"] = folio_row.get("source_transfer_amount")
        inv["return_against"] = folio_row.get("return_against")

    checkin["invoices"] = merged_invoices
    checkin["payments"] = merged_payments
    checkin["late_checkout_charge"] = _get_late_checkout_charge_preview(name)
    checkin["billing_summary"] = {} if added_reservation_ledger else (folio.get("summary") or {})
    if checkin["billing_summary"]:
        checkin["total_outstanding_amount"] = flt(
            checkin["billing_summary"].get("balance_amount", checkin.get("total_outstanding_amount") or 0)
        )
    else:
        invoice_due = sum(
            flt(inv.get("outstanding_amount"))
            for inv in merged_invoices
            if not inv.get("is_return") and flt(inv.get("outstanding_amount")) > 0
        )
        invoice_credit = sum(
            abs(flt(inv.get("outstanding_amount")))
            for inv in merged_invoices
            if inv.get("is_return") or flt(inv.get("outstanding_amount")) < 0
        )
        checkin["total_outstanding_amount"] = flt(invoice_due - invoice_credit)

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
        hr.reservation_status NOT IN ('Cancelled', 'Checked In', 'Checked Out', 'No Show', 'Expired')
        AND hr.docstatus != 2
        AND NOT EXISTS (
            SELECT 1
            FROM `tabHotel Reservation Room` hrr
            WHERE hrr.parent = hr.name
              AND hrr.parenttype = 'Hotel Reservation'
              AND (
                  COALESCE(hrr.check_in_reference, '') != ''
                  OR hrr.status IN ('Checked In', 'Checked Out')
              )
        )
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
def get_rooms_for_transfer(current_room="", check_in_dt=None, check_out_dt=None, exclude_reservation=None):
    """Return rooms eligible for a room-transfer operation.

    Returns vacant rooms that do NOT have an active, overlapping check-in,
    excluding the guest's current room.
    """
    from rhohotel.rhocom_hotel.utils.room_availability import _normalize_dt

    # Transfer targets must match transfer_room(), which only accepts Vacant rooms.
    filters = {"status": "Vacant"}
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

        reserved = frappe.db.sql(
            f"""
            SELECT DISTINCT rr.room_number
            FROM `tabHotel Reservation Room` rr
            INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
            WHERE rr.room_number IN ({placeholders})
              AND hr.docstatus != 2
              AND hr.reservation_status NOT IN
                  ('Cancelled', 'Checked Out', 'No Show', 'Expired')
              AND COALESCE(rr.check_in_reference, '') = ''
              AND COALESCE(rr.status, 'Reserved') NOT IN
                  ('Checked In', 'Checked Out', 'Cancelled')
              AND hr.from_date < %s
              AND hr.to_date > %s
              AND hr.name != %s
            """,
            tuple(room_names) + (co_str, ci_str, exclude_reservation or ""),
            as_dict=True,
        )
        unavailable = busy_set | {r.room_number for r in reserved}
        rooms = [r for r in rooms if r.name not in unavailable]

    # Attach room-rate pricing using the same source as new check-in and transfer billing.
    from rhohotel.api import get_room_rate

    check_in_date = str(getdate(check_in_dt)) if check_in_dt else None
    rate_map = {}
    for room in rooms:
        rt = room.get("room_type")
        if rt and rt not in rate_map:
            rate_map[rt] = get_room_rate(rt, check_in_date=check_in_date) or 0
        rate = rate_map.get(rt, 0)
        room["default_rate"] = rate
        room["rate_per_night"] = rate
        room["rate"] = rate

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
    from rhohotel.rhocom_hotel.utils.room_availability import (
        _normalize_checkin_dt,
        _normalize_checkout_dt,
        _get_hotel_time_strings,
    )

    use_availability = bool(check_in_dt and check_out_dt)

    if use_availability:
        ci_dt = _normalize_checkin_dt(check_in_dt)
        co_dt = _normalize_checkout_dt(check_out_dt)
        ci_str = ci_dt.strftime("%Y-%m-%d %H:%M:%S")
        co_str = co_dt.strftime("%Y-%m-%d %H:%M:%S")
        ci_time_str, co_time_str = _get_hotel_time_strings()

    # --- 1. Candidate rooms (basic filters) ---
    # Include both Vacant and Reserved rooms — Reserved means a future booking
    # exists, but the room may still be free for the requested period.
    filters = {"status": ["in", ["Vacant", "Reserved"]], "operational_status": "In Service", "maintenance_flag": 0}
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
              AND COALESCE(rr.check_in_reference, '') = ''
              AND COALESCE(rr.status, 'Reserved') NOT IN
                  ('Checked In', 'Checked Out', 'Cancelled')
              AND TIMESTAMP(hr.from_date, %s) < %s
              AND TIMESTAMP(hr.to_date,   %s) > %s
              AND hr.name != %s
            """,
            tuple(room_names) + (ci_time_str, co_str, co_time_str, ci_str, exclude_reservation or ''),
            as_dict=True,
        )

        unavailable = set(
            [r.room_number for r in checkin_rows]
            + [r.room_number for r in canonical_rows]
        )
        rooms = [r for r in rooms if r.name not in unavailable]

    # --- 3. Attach default room rate ---
    from rhohotel.api import get_room_rate

    tariff_map = {}
    for room in rooms:
        rt = room.get("room_type")
        if rt and rt not in tariff_map:
            tariff_map[rt] = get_room_rate(rt) or 0
        rate = tariff_map.get(rt, 0)
        room["default_rate"] = rate
        room["rate_per_night"] = rate
        room["rate"] = rate

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
        if canonical_reservation:
            from rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings import get_default_check_in_datetime

            check_in_datetime = get_default_check_in_datetime()
        else:
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
    if frappe.get_meta("Hotel Room Check In").has_field("reservation"):
        doc.reservation = reservation or canonical_reservation or ""
    doc.canonical_reservation = canonical_reservation or ""
    doc.reservation_source = _valid_marketplace_source(reservation_source)
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
    from rhohotel.rhocom_hotel.utils.phone import validate_phone_number

    doc.contact_number = validate_phone_number(
        contact_number or frappe.db.get_value("Hotel Guest", guest, "phone_number") or "",
        label="Guest Phone Number",
        required=True,
    )
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
                    try:
                        from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import (
                            link_reservation_invoices_to_check_in,
                        )

                        link_reservation_invoices_to_check_in(canonical_reservation, doc.name, row.name)
                    except Exception:
                        frappe.log_error(
                            frappe.get_traceback(),
                            "Reservation invoice link failed at check-in",
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

    reason = (reason or "").strip()
    valid_reasons = _get_hotel_refund_reason_options()
    if not reason:
        frappe.throw("Please select a refund reason.")
    if valid_reasons and reason not in valid_reasons:
        frappe.throw("Please select a valid refund reason.")

    check_in = frappe.get_doc("Hotel Room Check In", check_in_name)
    from rhohotel.rhocom_hotel.utils.folio import get_checkin_folio

    folio = get_checkin_folio(check_in_name)
    summary = folio.get("summary") or {}
    total_paid = flt(summary.get("total_received"))

    if total_paid <= 0:
        frappe.throw("No confirmed payments found for this check-in. Cannot create refund.")

    total_charged = flt(summary.get("net_bill"))
    total_refunded = flt(summary.get("reserved_refunds_total"))
    net_overpayment = flt(summary.get("refundable_balance"))

    if net_overpayment <= 0:
        frappe.throw(
            "No refundable overpayment remaining for this check-in. "
            f"Total paid: ₦{total_paid:,.2f}, Net bill: ₦{total_charged:,.2f}, "
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
    refund.reasons = reason
    refund.insert(ignore_permissions=True)
    refund.submit()
    try:
        from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

        sync_checkin_folio_totals(check_in.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after refund request")

    return {"name": refund.name, "refund_amount": refund_amount, "total_paid": total_paid, "total_charged": total_charged, "total_refunded": total_refunded}


def _get_hotel_refund_reason_options():
    meta = frappe.get_meta("Hotel Refund")
    field = meta.get_field("reasons") if meta else None
    options = (field.options or "") if field else ""
    return [row.strip() for row in options.splitlines() if row.strip()]


@frappe.whitelist()
def get_checkout_detail(check_in_name):
    """Load check-in data formatted for the checkout detail page."""
    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(f"Check-in {check_in_name} not found")

    doc = frappe.get_doc("Hotel Room Check In", check_in_name)
    from rhohotel.rhocom_hotel.utils.folio import get_checkin_folio, sync_checkin_folio_totals

    try:
        folio = sync_checkin_folio_totals(check_in_name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Checkout folio summary failed")
        folio = {"sales_invoices": [], "acquired_bills": [], "summary": {}}

    # Fetch all invoices (Sales + POS) linked to this check-in — split into separate
    # queries so a missing column on one table does not silently kill both.
    invoices = []
    try:
        invoice_type_expr = "'Sales Invoice'"
        if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
            invoice_type_expr = "COALESCE(NULLIF(custom_invoice_source, ''), 'Sales Invoice')"

        si_rows = frappe.db.sql(f"""
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount, is_return,
                   posting_date, status,
                   {invoice_type_expr} AS invoice_type
            FROM `tabSales Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, check_in_name, as_dict=1) or []
        invoices.extend(si_rows)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Checkout detail invoice fetch failed")

    try:
        pos_rows = frappe.db.sql("""
            SELECT name AS invoice_id, grand_total AS amount, outstanding_amount, 0 AS is_return,
                   posting_date, status, 'POS Invoice' AS invoice_type,
                   consolidated_invoice
            FROM `tabPOS Invoice`
            WHERE custom_hotel_room_check_in = %s AND docstatus = 1
            ORDER BY posting_date DESC
        """, check_in_name, as_dict=1) or []
    except Exception:
        pos_rows = []

    si_names = {row.get("invoice_id") for row in invoices}
    room_posting_pos_names = set()
    for row in pos_rows:
        if row.get("consolidated_invoice") in si_names:
            room_posting_pos_names.add(row.get("invoice_id"))
            for inv in invoices:
                if inv.get("invoice_id") == row.get("consolidated_invoice"):
                    inv["invoice_type"] = "Restaurant"

    invoices.extend([row for row in pos_rows if row.get("invoice_id") not in room_posting_pos_names])
    _normalize_sales_invoice_types(invoices, key="invoice_id")

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

    folio_invoice_map = {row.get("name"): row for row in (folio.get("sales_invoices") or [])}
    for inv in invoices:
        folio_row = folio_invoice_map.get(inv.get("invoice_id"))
        if not folio_row:
            continue
        inv["amount"] = folio_row.get("amount")
        inv["outstanding_amount"] = folio_row.get("net_outstanding_amount") if not folio_row.get("is_return") else folio_row.get("open_credit_amount")
        inv["raw_outstanding_amount"] = folio_row.get("raw_outstanding_amount")
        inv["net_outstanding_amount"] = folio_row.get("net_outstanding_amount")
        inv["credit_applied"] = folio_row.get("credit_applied")
        inv["open_credit_amount"] = folio_row.get("open_credit_amount")

    summary = folio.get("summary") or {}
    total_invoice = flt(summary.get("net_bill", doc.total_charges))
    total_outstanding = flt(summary.get("balance_amount", doc.total_outstanding_amount))
    total_paid = flt(summary.get("total_received", 0))

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
        "total_outstanding_amount": flt(summary.get("balance_amount", doc.total_outstanding_amount)),
        "total_invoice": total_invoice,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "collectible_outstanding": flt(summary.get("collectible_outstanding", max(0, total_outstanding))),
        "billing_summary": summary,
        "late_checkout": doc.late_checkout,
        "late_checkout_charge": _get_late_checkout_charge_preview(check_in_name),
        "reservation_source": doc.reservation_source or "Walk-in",
        "invoices": invoices,
        "acquired_bills": folio.get("acquired_bills") or [],
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
    from rhohotel.rhocom_hotel.utils.folio import get_invoice_net_outstanding

    for inv_name in invoices:
        if not frappe.db.exists("Sales Invoice", inv_name):
            continue  # Skip POS Invoices and non-existing docs

        inv_doc = frappe.get_doc("Sales Invoice", inv_name)
        if cint(inv_doc.is_return):
            continue
        if inv_doc.custom_hotel_room_check_in != from_check_in:
            frappe.throw(f"Invoice {inv_name} is not linked to check-in {from_check_in}.")

        total_amount = flt(get_invoice_net_outstanding(from_check_in, inv_name))

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
def process_checkout(check_in_name, remarks="", check_out_datetime=None, charge_late_checkout=0):
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

    charge_late_checkout = cint(charge_late_checkout)
    late_checkout_invoice = None
    if charge_late_checkout:
        late_checkout_invoice = _apply_due_late_checkout_charge(
            check_in_name,
            reference_datetime=check_out_datetime,
        )

    from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

    folio = sync_checkin_folio_totals(check_in_name)
    summary = folio.get("summary") or {}
    outstanding = flt(summary.get("collectible_outstanding") or summary.get("balance_amount"))
    if outstanding > 0:
        roles = frappe.get_roles(frappe.session.user)
        if frappe.session.user != "Administrator" and "Front Desk Manager" not in roles:
            return {
                "check_in": check_in_name,
                "status": "Payment Required",
                "late_checkout_invoice": late_checkout_invoice,
                "outstanding": outstanding,
                "message": (
                    "Late check-out charge was posted. Please collect payment before completing checkout."
                    if late_checkout_invoice
                    else "Please collect payment before completing checkout."
                ),
            }

    co = frappe.new_doc("Hotel Room Check Out")
    co.check_in = check_in_name
    co.room_number = checkin.room_number
    co.guest_name = checkin.guest
    co.check_in_datetime = checkin.check_in_datetime
    co.check_out_datetime = check_out_datetime
    co.late_checkout = 1 if late_checkout_invoice else checkin.late_checkout
    co.remarks = remarks or ""
    co.payment_status = "Paid" if flt(summary.get("balance_amount")) <= 0 else "Unpaid"
    if not charge_late_checkout:
        co.flags.skip_late_checkout_charge = True
    elif late_checkout_invoice:
        co.flags.applied_late_checkout_amount = flt(late_checkout_invoice.get("amount"))

    co.insert(ignore_permissions=True)
    co.submit()

    # --- Smart lock key cancellation (non-blocking) ---
    lock_cancellation = None
    cancel_setting = frappe.db.get_single_value("Hotel Settings", "cancel_keys_on_checkout")
    if cancel_setting:
        try:
            from rhohotel.integrations.locks.service import cancel_keys_for_check_in
            lock_cancellation = cancel_keys_for_check_in(check_in_name, requested_by=frappe.session.user)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"lock cancellation at checkout failed: {check_in_name}")

    return {
        "name": co.name,
        "check_in": check_in_name,
        "status": "Checked Out",
        "late_checkout_invoice": late_checkout_invoice,
        "lock_cancellation": lock_cancellation,
    }


def _get_late_checkout_charge_preview(check_in_name, reference_datetime=None):
    try:
        from rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings import check_late_checkout

        result = check_late_checkout(check_in_name, reference_datetime=reference_datetime) or {}
        if not result.get("late"):
            return None
        policy = result.get("policy") or {}
        raw_amount = flt(policy.get("amount"))
        amount = raw_amount
        if policy.get("charge_type") == "Percentage":
            rate = flt(frappe.db.get_value("Hotel Room Check In", check_in_name, "rate_amount") or 0)
            amount = (rate * amount) / 100
        return {
            "hours_late": flt(result.get("hours_late")),
            "item": policy.get("item"),
            "charge_type": policy.get("charge_type"),
            "raw_amount": raw_amount,
            "amount": flt(amount),
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Late checkout preview failed")
        return None


def _apply_due_late_checkout_charge(check_in_name, reference_datetime=None):
    preview = _get_late_checkout_charge_preview(
        check_in_name,
        reference_datetime=reference_datetime,
    )
    if not preview or not preview.get("item"):
        return None

    from rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in import apply_late_checkout_charge

    return apply_late_checkout_charge(
        check_in_name,
        preview.get("item"),
        preview.get("charge_type"),
        preview.get("raw_amount"),
    )
