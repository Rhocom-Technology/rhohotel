import frappe
from frappe.utils import add_days, flt, format_datetime, get_datetime, getdate, nowdate


def _has_doctype(doctype):
    try:
        return bool(frappe.db.exists("DocType", doctype))
    except Exception:
        return False


def _has_column(doctype, column):
    try:
        return bool(frappe.db.has_column(doctype, column))
    except Exception:
        return False


def _date_or_default(value, default_value):
    try:
        return getdate(value) if value else getdate(default_value)
    except Exception:
        return getdate(default_value)


def _money(value):
    return flt(value or 0, 2)


def _to_date_str(value):
    if not value:
        return ""
    return str(value)[:10]


def _get_guest_profiles(guest=None, include_corporate=0):
    if not _has_doctype("Hotel Guest"):
        return []

    conditions = ["IFNULL(hg.customer, '') != ''"]
    params = {}

    if not int(include_corporate or 0):
        conditions.append("IFNULL(hg.guest_type, '') != 'Corporate'")

    if guest:
        conditions.append("hg.name = %(guest)s")
        params["guest"] = guest

    return frappe.db.sql(
        """
        SELECT
            hg.name AS guest,
            hg.hotel_guest_name AS guest_name,
            hg.customer,
            hg.phone_number,
            hg.contact_number
        FROM `tabHotel Guest` hg
        WHERE {conditions}
        ORDER BY IFNULL(hg.hotel_guest_name, ''), hg.name
        """.format(conditions=" AND ".join(conditions)),
        params,
        as_dict=True,
    )


def _build_guest_scope(guest_profiles, selected_guest=None):
    customer_to_guest = {}
    guest_options = []
    seen_guest = set()

    if selected_guest:
        for row in guest_profiles:
            if row.get("guest") == selected_guest and row.get("customer"):
                customer_to_guest[row.get("customer")] = {
                    "guest": row.get("guest") or "",
                    "guest_name": row.get("guest_name") or row.get("guest") or "Unknown Guest",
                }
                break

    for row in guest_profiles:
        guest_id = row.get("guest") or ""
        guest_name = row.get("guest_name") or guest_id or "Unknown Guest"
        customer = row.get("customer") or ""

        if guest_id and guest_id not in seen_guest:
            seen_guest.add(guest_id)
            guest_options.append({"guest": guest_id, "guest_name": guest_name})

        if customer and customer not in customer_to_guest:
            customer_to_guest[customer] = {
                "guest": guest_id,
                "guest_name": guest_name,
            }

    customers = sorted(customer_to_guest.keys())
    return customers, customer_to_guest, guest_options


def _get_checkins_for_customers(customers):
    if not customers or not _has_doctype("Hotel Room Check In"):
        return []

    return frappe.db.sql(
        """
        SELECT
            ci.name,
            ci.guest,
            ci.room_number,
            ci.room_type,
            ci.status,
            ci.check_in_datetime,
            ci.actual_check_out_datetime,
            ci.expected_check_out_datetime,
            g.hotel_guest_name,
            g.customer
        FROM `tabHotel Room Check In` ci
        LEFT JOIN `tabHotel Guest` g ON g.name = ci.guest
        WHERE ci.docstatus != 2
          AND IFNULL(g.customer, '') IN %(customers)s
        ORDER BY ci.check_in_datetime DESC, ci.creation DESC
        """,
        {"customers": tuple(customers)},
        as_dict=True,
    )


def _build_checkin_maps(checkins):
    checkin_map = {}
    latest_checkin_by_customer = {}

    for row in checkins:
        checkin_name = row.get("name")
        if not checkin_name:
            continue

        info = {
            "check_in": checkin_name,
            "guest": row.get("guest") or "",
            "guest_name": row.get("hotel_guest_name") or row.get("guest") or "Unknown Guest",
            "room_number": row.get("room_number") or "—",
            "room_type": row.get("room_type") or "",
            "status": row.get("status") or "",
            "customer": row.get("customer") or "",
        }

        checkin_map[checkin_name] = info

        customer = info.get("customer")
        if customer and customer not in latest_checkin_by_customer:
            latest_checkin_by_customer[customer] = info

    return checkin_map, latest_checkin_by_customer


def _get_payment_ledger_rows(customers, date_to):
    if not customers or not _has_doctype("Payment Ledger Entry"):
        return []

    return frappe.db.sql(
        """
        SELECT
            ple.name,
            ple.creation,
            ple.posting_date,
            ple.party,
            ple.voucher_type,
            ple.voucher_no,
            ple.against_voucher_type,
            ple.against_voucher_no,
            ple.amount,
            ple.remarks
        FROM `tabPayment Ledger Entry` ple
        WHERE ple.docstatus = 1
          AND ple.account_type = 'Receivable'
          AND ple.party_type = 'Customer'
          AND ple.delinked = 0
          AND ple.party IN %(customers)s
          AND ple.posting_date <= %(date_to)s
        ORDER BY ple.posting_date ASC, ple.creation ASC, ple.name ASC
        """,
        {"customers": tuple(customers), "date_to": str(date_to)},
        as_dict=True,
    )


def _get_sales_invoice_meta(invoice_names):
    if not invoice_names:
        return {}

    has_checkin = _has_column("Sales Invoice", "custom_hotel_room_check_in")
    has_source = _has_column("Sales Invoice", "custom_invoice_source")

    rows = frappe.db.sql(
        """
        SELECT
            si.name,
            si.is_return,
            si.remarks,
            {checkin_field},
            {source_field}
        FROM `tabSales Invoice` si
        WHERE si.name IN %(names)s
        """.format(
            checkin_field="si.custom_hotel_room_check_in AS check_in" if has_checkin else "'' AS check_in",
            source_field="si.custom_invoice_source AS invoice_source" if has_source else "'' AS invoice_source",
        ),
        {"names": tuple(invoice_names)},
        as_dict=True,
    )

    return {row.get("name"): row for row in rows}


def _get_payment_entry_meta(payment_names):
    if not payment_names or not _has_doctype("Payment Entry"):
        return {}

    has_checkin = _has_column("Payment Entry", "custom_hotel_room_check_in")

    rows = frappe.db.sql(
        """
        SELECT
            pe.name,
            pe.remarks,
            pe.reference_no,
            pe.mode_of_payment,
            {checkin_field}
        FROM `tabPayment Entry` pe
        WHERE pe.name IN %(names)s
        """.format(
            checkin_field="pe.custom_hotel_room_check_in AS check_in" if has_checkin else "'' AS check_in"
        ),
        {"names": tuple(payment_names)},
        as_dict=True,
    )

    return {row.get("name"): row for row in rows}


def _get_journal_entry_meta(journal_names):
    if not journal_names or not _has_doctype("Journal Entry"):
        return {}

    has_checkin = _has_column("Journal Entry", "custom_hotel_room_check_in")
    has_user_remark = _has_column("Journal Entry", "user_remark")
    has_remark = _has_column("Journal Entry", "remark")

    if has_user_remark and has_remark:
        remarks_field = "CONCAT_WS('\\n', NULLIF(je.user_remark, ''), NULLIF(je.remark, '')) AS remarks"
    elif has_user_remark:
        remarks_field = "je.user_remark AS remarks"
    elif has_remark:
        remarks_field = "je.remark AS remarks"
    else:
        remarks_field = "'' AS remarks"

    rows = frappe.db.sql(
        """
        SELECT
            je.name,
            {remarks_field},
            {checkin_field}
        FROM `tabJournal Entry` je
        WHERE je.name IN %(names)s
        """.format(
            remarks_field=remarks_field,
            checkin_field="je.custom_hotel_room_check_in AS check_in" if has_checkin else "'' AS check_in",
        ),
        {"names": tuple(journal_names)},
        as_dict=True,
    )

    return {row.get("name"): row for row in rows}


def _get_voucher_meta(ple_rows):
    si_names = set()
    pe_names = set()
    je_names = set()
    against_si_names = set()

    for row in ple_rows:
        voucher_type = row.get("voucher_type")
        voucher_no = row.get("voucher_no")

        if voucher_type == "Sales Invoice" and voucher_no:
            si_names.add(voucher_no)
        elif voucher_type == "Payment Entry" and voucher_no:
            pe_names.add(voucher_no)
        elif voucher_type == "Journal Entry" and voucher_no:
            je_names.add(voucher_no)

        if row.get("against_voucher_type") == "Sales Invoice" and row.get("against_voucher_no"):
            against_si_names.add(row.get("against_voucher_no"))

    all_si_names = si_names | against_si_names
    return {
        "sales_invoice": _get_sales_invoice_meta(all_si_names),
        "payment_entry": _get_payment_entry_meta(pe_names),
        "journal_entry": _get_journal_entry_meta(je_names),
    }


def _resolve_voucher_row_meta(ple_row, voucher_meta):
    voucher_type = ple_row.get("voucher_type")
    voucher_no = ple_row.get("voucher_no")

    si_meta = {}
    voucher_row_meta = {}

    if voucher_type == "Sales Invoice":
        si_meta = voucher_meta.get("sales_invoice", {}).get(voucher_no, {})
        voucher_row_meta = si_meta
    elif voucher_type == "Payment Entry":
        voucher_row_meta = voucher_meta.get("payment_entry", {}).get(voucher_no, {})
    elif voucher_type == "Journal Entry":
        voucher_row_meta = voucher_meta.get("journal_entry", {}).get(voucher_no, {})

    against_si_meta = {}
    if ple_row.get("against_voucher_type") == "Sales Invoice" and ple_row.get("against_voucher_no"):
        against_si_meta = voucher_meta.get("sales_invoice", {}).get(ple_row.get("against_voucher_no"), {})

    return voucher_row_meta, si_meta, against_si_meta


def _resolve_transaction_type(ple_row, voucher_row_meta, si_meta):
    voucher_type = (ple_row.get("voucher_type") or "").strip()
    amount = flt(ple_row.get("amount") or 0)

    if voucher_type == "Sales Invoice":
        if int(si_meta.get("is_return") or 0):
            return "Credit Note"
        return "Credit Note" if amount < 0 else "Sales Invoice"

    if voucher_type == "Payment Entry":
        return "Payment Refund" if amount > 0 else "Payment Entry"

    if voucher_type == "Journal Entry":
        text = "{0} {1}".format(ple_row.get("remarks") or "", voucher_row_meta.get("remarks") or "").lower()
        if "bill transfer" in text:
            return "Bill Transfer In" if amount > 0 else "Bill Transfer Out"
        return "Journal Entry"

    return voucher_type or "Ledger Entry"


def _resolve_remarks(ple_row, voucher_row_meta, si_meta):
    remarks = (ple_row.get("remarks") or "").strip()
    if remarks:
        return remarks

    remarks = (voucher_row_meta.get("remarks") or "").strip()
    if remarks:
        return remarks

    source = (si_meta.get("invoice_source") or "").strip()
    if source:
        return source

    invoice_remarks = (si_meta.get("remarks") or "").strip()
    if invoice_remarks:
        return invoice_remarks

    voucher_type = ple_row.get("voucher_type") or "Transaction"
    voucher_no = ple_row.get("voucher_no") or ""
    return "{0} {1}".format(voucher_type, voucher_no).strip()


def _row_matches_search(row, search_query):
    if not search_query:
        return True

    query = str(search_query).strip().lower()
    if not query:
        return True

    fields = [
        row.get("date"),
        row.get("guest"),
        row.get("guest_name"),
        row.get("customer"),
        row.get("check_in"),
        row.get("room_number"),
        row.get("transaction_type"),
        row.get("voucher_no"),
        row.get("remarks"),
        row.get("checkin_status"),
        row.get("room_type"),
    ]

    for value in fields:
        if query in str(value or "").lower():
            return True
    return False


def _build_ledger_rows(ple_rows, voucher_meta, customer_to_guest, checkin_map):
    rows = []

    for ple in ple_rows:
        customer = ple.get("party") or ""
        voucher_row_meta, si_meta, against_si_meta = _resolve_voucher_row_meta(ple, voucher_meta)

        check_in = (voucher_row_meta.get("check_in") or "").strip()
        if not check_in:
            check_in = (against_si_meta.get("check_in") or "").strip()

        checkin_info = checkin_map.get(check_in, {})
        guest_info = customer_to_guest.get(customer, {})

        guest = checkin_info.get("guest") or guest_info.get("guest") or ""
        guest_name = (
            checkin_info.get("guest_name")
            or guest_info.get("guest_name")
            or customer
            or "Unknown Guest"
        )

        amount = flt(ple.get("amount") or 0)
        debit = _money(amount if amount > 0 else 0)
        credit = _money(abs(amount) if amount < 0 else 0)

        row = {
            "date": _to_date_str(ple.get("posting_date")),
            "guest": guest,
            "guest_name": guest_name,
            "customer": customer,
            "check_in": check_in,
            "room_number": checkin_info.get("room_number") or "—",
            "transaction_type": _resolve_transaction_type(ple, voucher_row_meta, si_meta),
            "voucher_no": ple.get("voucher_no") or "",
            "remarks": _resolve_remarks(ple, voucher_row_meta, si_meta),
            "debit": debit,
            "credit": credit,
            "checkin_status": checkin_info.get("status") or "",
            "room_type": checkin_info.get("room_type") or "",
            "_sort_creation": str(ple.get("creation") or ""),
            "_sort_name": ple.get("name") or "",
        }

        rows.append(row)

    return rows


def _filter_rows(rows, checkin_status=None, room_type=None, search=None):
    filtered = []
    for row in rows:
        if checkin_status and row.get("checkin_status") != checkin_status:
            continue

        if room_type and row.get("room_type") != room_type:
            continue

        if not _row_matches_search(row, search):
            continue

        filtered.append(row)

    return filtered


def _row_sort_key(row):
    return (
        row.get("date") or "",
        row.get("_sort_creation") or "",
        row.get("voucher_no") or "",
        row.get("_sort_name") or "",
    )


def _empty_payload(date_from, date_to, guest_options=None):
    return {
        "summary": {
            "opening_balance": 0.0,
            "total_debit": 0.0,
            "total_credit": 0.0,
            "closing_balance": 0.0,
            "transaction_count": 0,
            "guest_count": 0,
        },
        "rows": [],
        "room_types": [],
        "checkin_statuses": [],
        "guest_options": guest_options or [],
        "transaction_types": [],
        "generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
        "filters": {
            "date_from": str(date_from),
            "date_to": str(date_to),
        },
    }


@frappe.whitelist()
def get_guest_ledger_report(
    date_from=None,
    date_to=None,
    guest=None,
    checkin_status=None,
    room_type=None,
    transaction_type=None,
    search=None,
    include_corporate=0,
):
    date_from = _date_or_default(date_from, add_days(nowdate(), -30))
    date_to = _date_or_default(date_to, nowdate())

    guest_profiles = _get_guest_profiles(guest=guest, include_corporate=include_corporate)
    customers, customer_to_guest, guest_options = _build_guest_scope(guest_profiles, selected_guest=guest)

    if not customers:
        return _empty_payload(date_from, date_to, guest_options=guest_options)

    checkins = _get_checkins_for_customers(customers)
    checkin_map, _latest_checkin_by_customer = _build_checkin_maps(checkins)

    ple_rows = _get_payment_ledger_rows(customers, date_to)
    if not ple_rows:
        return _empty_payload(date_from, date_to, guest_options=guest_options)

    voucher_meta = _get_voucher_meta(ple_rows)
    all_rows = _build_ledger_rows(ple_rows, voucher_meta, customer_to_guest, checkin_map)
    scoped_rows = _filter_rows(all_rows, checkin_status=checkin_status, room_type=room_type, search=search)

    from_date_str = str(date_from)
    to_date_str = str(date_to)

    opening_rows = [row for row in scoped_rows if row.get("date") and row["date"] < from_date_str]
    opening_debit = _money(sum(flt(row.get("debit")) for row in opening_rows))
    opening_credit = _money(sum(flt(row.get("credit")) for row in opening_rows))
    opening_balance = _money(opening_debit - opening_credit)

    in_range_rows = [
        row
        for row in scoped_rows
        if row.get("date") and from_date_str <= row["date"] <= to_date_str
    ]

    if transaction_type:
        in_range_rows = [row for row in in_range_rows if row.get("transaction_type") == transaction_type]

    in_range_rows.sort(key=_row_sort_key)

    running_balance = opening_balance
    ledger_rows = []
    for row in in_range_rows:
        running_balance = _money(running_balance + flt(row.get("debit")) - flt(row.get("credit")))
        row_copy = dict(row)
        row_copy["running_balance"] = running_balance
        row_copy.pop("_sort_creation", None)
        row_copy.pop("_sort_name", None)
        ledger_rows.append(row_copy)

    total_debit = _money(sum(flt(row.get("debit")) for row in ledger_rows))
    total_credit = _money(sum(flt(row.get("credit")) for row in ledger_rows))
    closing_balance = _money(opening_balance + total_debit - total_credit)

    summary = {
        "opening_balance": opening_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "closing_balance": closing_balance,
        "transaction_count": len(ledger_rows),
        "guest_count": len({(row.get("guest") or row.get("guest_name")) for row in ledger_rows if (row.get("guest") or row.get("guest_name"))}),
    }

    room_types = sorted({row.get("room_type") for row in checkins if row.get("room_type")})
    checkin_statuses = sorted({row.get("status") for row in checkins if row.get("status")})
    guest_options = sorted(guest_options, key=lambda x: (x.get("guest_name") or "", x.get("guest") or ""))
    transaction_types = sorted({row.get("transaction_type") for row in scoped_rows if row.get("transaction_type")})

    return {
        "summary": summary,
        "rows": ledger_rows,
        "room_types": room_types,
        "checkin_statuses": checkin_statuses,
        "guest_options": guest_options,
        "transaction_types": transaction_types,
        "generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
        "filters": {
            "date_from": str(date_from),
            "date_to": str(date_to),
        },
    }
