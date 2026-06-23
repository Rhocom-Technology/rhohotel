import frappe
from frappe.utils import add_days, flt, format_datetime, get_datetime, getdate, nowdate

from rhohotel.rhocom_hotel.utils.folio import get_checkin_folio


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


def _get_checkins(guest=None, checkin_status=None, room_type=None, search=None):
    conditions = ["ci.docstatus != 2"]
    params = {}

    if guest:
        conditions.append("ci.guest = %(guest)s")
        params["guest"] = guest

    if checkin_status:
        conditions.append("ci.status = %(checkin_status)s")
        params["checkin_status"] = checkin_status

    if room_type:
        conditions.append("ci.room_type = %(room_type)s")
        params["room_type"] = room_type

    if search:
        conditions.append(
            "(" 
            "ci.name LIKE %(search)s OR "
            "ci.guest LIKE %(search)s OR "
            "IFNULL(ci.room_number, '') LIKE %(search)s OR "
            "IFNULL(g.hotel_guest_name, '') LIKE %(search)s"
            ")"
        )
        params["search"] = "%{0}%".format(str(search).strip())

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
            g.phone_number,
            g.contact_number
        FROM `tabHotel Room Check In` ci
        LEFT JOIN `tabHotel Guest` g ON g.name = ci.guest
        WHERE {conditions}
        ORDER BY ci.check_in_datetime DESC
        """.format(conditions=" AND ".join(conditions)),
        params,
        as_dict=True,
    )


def _get_payment_entries(checkin_names):
    if not checkin_names:
        return {}
    if not (_has_doctype("Payment Entry") and _has_column("Payment Entry", "custom_hotel_room_check_in")):
        return {}

    rows = frappe.db.sql(
        """
        SELECT
            name,
            posting_date,
            payment_type,
            paid_amount,
            remarks,
            reference_no,
            mode_of_payment,
            custom_hotel_room_check_in AS check_in
        FROM `tabPayment Entry`
        WHERE docstatus = 1
          AND custom_hotel_room_check_in IN %(checkins)s
        ORDER BY posting_date ASC, creation ASC
        """,
        {"checkins": tuple(checkin_names)},
        as_dict=True,
    )

    result = {}
    for row in rows:
        result.setdefault(row.check_in, []).append(row)
    return result


def _build_transaction_rows(checkins, payment_map):
    transactions = []

    for checkin in checkins:
        check_in_name = checkin.get("name")
        guest_name = checkin.get("hotel_guest_name") or checkin.get("guest") or "Unknown Guest"

        folio = get_checkin_folio(check_in_name)

        for inv in folio.get("sales_invoices") or []:
            is_return = bool(inv.get("is_return"))
            amount = _money(inv.get("amount" if is_return else "grand_total"))
            if amount <= 0:
                amount = _money(inv.get("amount"))

            debit = 0 if is_return else amount
            credit = amount if is_return else 0

            transactions.append(
                {
                    "date": _to_date_str(inv.get("posting_date")),
                    "guest": checkin.get("guest") or "",
                    "guest_name": guest_name,
                    "check_in": check_in_name,
                    "room_number": checkin.get("room_number") or "—",
                    "transaction_type": "Credit Note" if is_return else "Sales Invoice",
                    "voucher_no": inv.get("name") or "",
                    "remarks": inv.get("invoice_type") or "Guest folio invoice",
                    "debit": _money(debit),
                    "credit": _money(credit),
                    "checkin_status": checkin.get("status") or "",
                    "room_type": checkin.get("room_type") or "",
                }
            )

        for transfer in folio.get("acquired_bills") or []:
            amount = _money(transfer.get("total_amount"))
            if amount <= 0:
                continue
            transactions.append(
                {
                    "date": _to_date_str(transfer.get("transfer_date")),
                    "guest": checkin.get("guest") or "",
                    "guest_name": guest_name,
                    "check_in": check_in_name,
                    "room_number": checkin.get("room_number") or "—",
                    "transaction_type": "Bill Transfer In",
                    "voucher_no": transfer.get("name") or "",
                    "remarks": "Transferred from {0}".format(transfer.get("from_guest") or "another guest"),
                    "debit": amount,
                    "credit": 0,
                    "checkin_status": checkin.get("status") or "",
                    "room_type": checkin.get("room_type") or "",
                }
            )

        for payment in payment_map.get(check_in_name, []):
            payment_type = payment.get("payment_type") or "Receive"
            amount = _money(payment.get("paid_amount"))
            if amount <= 0:
                continue

            is_refund = payment_type == "Pay"
            debit = amount if is_refund else 0
            credit = 0 if is_refund else amount
            remarks = payment.get("remarks") or payment.get("reference_no") or payment.get("mode_of_payment") or "Payment Entry"

            transactions.append(
                {
                    "date": _to_date_str(payment.get("posting_date")),
                    "guest": checkin.get("guest") or "",
                    "guest_name": guest_name,
                    "check_in": check_in_name,
                    "room_number": checkin.get("room_number") or "—",
                    "transaction_type": "Payment Refund" if is_refund else "Payment Entry",
                    "voucher_no": payment.get("name") or "",
                    "remarks": remarks,
                    "debit": _money(debit),
                    "credit": _money(credit),
                    "checkin_status": checkin.get("status") or "",
                    "room_type": checkin.get("room_type") or "",
                }
            )

    return transactions


def _row_sort_key(row):
    return (row.get("date") or "", row.get("voucher_no") or "")


@frappe.whitelist()
def get_guest_ledger_report(
    date_from=None,
    date_to=None,
    guest=None,
    checkin_status=None,
    room_type=None,
    transaction_type=None,
    search=None,
):
    date_from = _date_or_default(date_from, add_days(nowdate(), -30))
    date_to = _date_or_default(date_to, nowdate())

    checkins = _get_checkins(
        guest=guest,
        checkin_status=checkin_status,
        room_type=room_type,
        search=search,
    )
    checkin_names = [row.name for row in checkins]

    payment_map = _get_payment_entries(checkin_names)
    all_rows = _build_transaction_rows(checkins, payment_map)

    from_date_str = str(date_from)
    to_date_str = str(date_to)

    opening_rows = [row for row in all_rows if row.get("date") and row["date"] < from_date_str]
    opening_debit = _money(sum(flt(row.get("debit")) for row in opening_rows))
    opening_credit = _money(sum(flt(row.get("credit")) for row in opening_rows))
    opening_balance = _money(opening_debit - opening_credit)

    in_range_rows = [
        row
        for row in all_rows
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
        "guest_count": len({row.get("guest") for row in ledger_rows if row.get("guest")}),
    }

    room_types = sorted({row.get("room_type") for row in checkins if row.get("room_type")})
    checkin_statuses = sorted({row.get("status") for row in checkins if row.get("status")})
    guest_options = sorted(
        [
            {
                "guest": row.get("guest") or "",
                "guest_name": row.get("hotel_guest_name") or row.get("guest") or "Unknown Guest",
            }
            for row in checkins
            if row.get("guest")
        ],
        key=lambda x: (x.get("guest_name") or "", x.get("guest") or ""),
    )

    unique_guest_options = []
    seen = set()
    for item in guest_options:
        key = item.get("guest")
        if key in seen:
            continue
        seen.add(key)
        unique_guest_options.append(item)

    transaction_types = sorted({row.get("transaction_type") for row in all_rows if row.get("transaction_type")})

    return {
        "summary": summary,
        "rows": ledger_rows,
        "room_types": room_types,
        "checkin_statuses": checkin_statuses,
        "guest_options": unique_guest_options,
        "transaction_types": transaction_types,
        "generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
        "filters": {
            "date_from": str(date_from),
            "date_to": str(date_to),
        },
    }
