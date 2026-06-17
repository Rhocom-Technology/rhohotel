import frappe
from frappe.utils import flt, getdate, nowdate, add_days, date_diff
from datetime import timedelta


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None, hall=None, status=None):
    from_date = getdate(from_date or get_first_day_of_current_month())
    to_date = getdate(to_date or nowdate())

    if to_date < from_date:
        frappe.throw("To Date cannot be before From Date.")

    bookings = get_bookings(from_date, to_date, hall, status)
    halls = frappe.db.get_all(
        "Hall",
        fields=["name", "hall_name", "hall_type", "capacity", "rate"],
        order_by="hall_name asc"
    )

    return {
        "filters": {
            "from_date": str(from_date),
            "to_date": str(to_date),
            "hall": hall or "",
            "status": status or ""
        },
        "halls": halls,
        "stats": build_stats(bookings, halls, from_date, to_date),
        "payment": build_payment_summary(bookings),
        "alerts": build_alerts(bookings),
        "booking_status": build_booking_status(bookings),
        "revenue_trend": build_revenue_trend(bookings, from_date, to_date),
        "occupancy": build_hall_occupancy(halls, bookings, from_date, to_date),
        "upcoming_events": get_upcoming_events(hall),
    }


def get_bookings(from_date, to_date, hall=None, status=None):
    filters = [
        ["start_datetime", "<=", str(to_date) + " 23:59:59"],
        ["end_datetime", ">=", str(from_date) + " 00:00:00"],
    ]

    if hall:
        filters.append(["hall", "=", hall])

    if status:
        if status == "Draft":
            filters.append(["docstatus", "=", 0])
        elif status == "Confirmed":
            filters.append(["docstatus", "=", 1])
        elif status == "Cancelled":
            filters.append(["docstatus", "=", 2])

    rows = frappe.db.get_all(
        "Hall Booking",
        filters=filters,
        fields=[
            "name",
            "customer_name",
            "mobile_number",
            "hall",
            "event_type",
            "start_datetime",
            "end_datetime",
            "rate",
            "total_days",
            "total_amount",
            "discount_type",
            "discount_amount",
            "net_total",
            "docstatus",
            "sales_invoice",
            "creation",
            "modified",
        ],
        order_by="start_datetime asc"
    )

    for row in rows:
        row["status_label"] = get_status_label(row.docstatus)
        row["payment_status"] = get_payment_status(row.sales_invoice, row.docstatus)
        row["hall_name"] = frappe.db.get_value("Hall", row.hall, "hall_name") or row.hall

    return rows

def build_stats(bookings, halls, from_date, to_date):
    today = getdate(nowdate())

    total_bookings = len(bookings)

    today_bookings = [
        b for b in bookings
        if b.docstatus == 1
        and getdate(b.start_datetime) <= today
        and getdate(b.end_datetime) >= today
    ]

    if today_bookings:
        today_start_date = str(min(getdate(b.start_datetime) for b in today_bookings))
        today_end_date = str(max(getdate(b.end_datetime) for b in today_bookings))
    else:
        today_start_date = str(today)
        today_end_date = str(today)

    pending_payment = sum(
        flt(b.net_total)
        for b in bookings
        if b.payment_status in ["Unpaid", "Partial", "No Invoice"]
    )

    submitted = [b for b in bookings if b.docstatus == 1]

    total_possible_days = max(
        1,
        len(halls) * get_period_days(from_date, to_date)
    )

    booked_days = 0

    for b in submitted:
        booked_days += get_overlap_days(
            getdate(b.start_datetime),
            getdate(b.end_datetime),
            from_date,
            to_date
        )

    utilization = round((booked_days / total_possible_days) * 100) if halls else 0

    return {
        "total_bookings": total_bookings,
        "today": len(today_bookings),
        "today_start_date": today_start_date,
        "today_end_date": today_end_date,
        "pending_payment": pending_payment,
        "utilization": utilization,
    }

def build_payment_summary(bookings):
    paid = 0
    pending = 0

    for b in bookings:
        if b.payment_status == "Paid":
            paid += flt(b.net_total)
        elif b.payment_status in ["Unpaid", "Partial", "No Invoice"]:
            pending += flt(b.net_total)

    return {
        "paid_today": paid,
        "pending": pending,
    }


def build_alerts(bookings):
    return {
        "pending_approval": len([b for b in bookings if b.docstatus == 0]),
        "maintenance": 0,
        "pending_invoice": len([b for b in bookings if b.payment_status in ["Unpaid", "Partial"]]),
    }


def build_booking_status(bookings):
    return {
        "draft": len([b for b in bookings if b.docstatus == 0]),
        "confirmed": len([b for b in bookings if b.docstatus == 1]),
        "cancelled": len([b for b in bookings if b.docstatus == 2]),
        "paid": len([b for b in bookings if b.payment_status == "Paid"]),
        "unpaid": len([b for b in bookings if b.payment_status in ["Unpaid", "Partial", "No Invoice"]]),
    }


def build_revenue_trend(bookings, from_date, to_date):
    period_days = get_period_days(from_date, to_date)
    chunk_size = max(1, int(period_days / 4))

    trend = []

    for i in range(4):
        chunk_start = add_days(from_date, i * chunk_size)
        chunk_end = add_days(chunk_start, chunk_size - 1)

        if getdate(chunk_end) > to_date or i == 3:
            chunk_end = to_date

        amount = sum(
            flt(b.net_total)
            for b in bookings
            if b.docstatus == 1
            and getdate(b.start_datetime) >= getdate(chunk_start)
            and getdate(b.start_datetime) <= getdate(chunk_end)
        )

        trend.append({
            "label": "Week {}".format(i + 1),
            "amount": amount,
        })

    max_amount = max([x["amount"] for x in trend] or [1])

    for row in trend:
        row["bar"] = 20 if max_amount <= 0 else max(20, round((row["amount"] / max_amount) * 140))

    return trend


def build_hall_occupancy(halls, bookings, from_date, to_date):
    total_days = get_period_days(from_date, to_date)
    result = []

    for hall in halls:
        hall_bookings = [
            b for b in bookings
            if b.hall == hall.name and b.docstatus == 1
        ]

        booked_days = 0

        for b in hall_bookings:
            booked_days += get_overlap_days(
                getdate(b.start_datetime),
                getdate(b.end_datetime),
                from_date,
                to_date
            )

        percent = min(100, round((booked_days / max(1, total_days)) * 100))

        if percent >= 100:
            status = "Fully Booked"
        elif percent > 0:
            status = "Partial"
        else:
            status = "Free"

        result.append({
            "name": hall.hall_name or hall.name,
            "hall": hall.name,
            "booked_days": booked_days,
            "total_days": total_days,
            "percent": percent,
            "status": status,
        })

    return result


def get_upcoming_events(hall=None):
    filters = [
        ["docstatus", "=", 1],
        ["start_datetime", ">=", nowdate()]
    ]

    if hall:
        filters.append(["hall", "=", hall])

    rows = frappe.db.get_all(
        "Hall Booking",
        filters=filters,
        fields=[
            "name",
            "customer_name",
            "hall",
            "event_type",
            "start_datetime",
            "end_datetime",
            "docstatus",
            "sales_invoice",
        ],
        order_by="start_datetime asc",
        limit=6,
    )

    for row in rows:
        row["hall_name"] = frappe.db.get_value("Hall", row.hall, "hall_name") or row.hall
        row["status_label"] = get_status_label(row.docstatus)
        row["payment_status"] = get_payment_status(row.sales_invoice, row.docstatus)

    return rows


def get_payment_status(invoice_name, docstatus):
    if docstatus == 0:
        return "Draft"

    if not invoice_name:
        return "No Invoice"

    outstanding = flt(frappe.db.get_value("Sales Invoice", invoice_name, "outstanding_amount") or 0)
    grand_total = flt(frappe.db.get_value("Sales Invoice", invoice_name, "grand_total") or 0)

    if outstanding <= 0:
        return "Paid"

    if outstanding < grand_total:
        return "Partial"

    return "Unpaid"


def get_status_label(docstatus):
    if docstatus == 0:
        return "Draft"
    if docstatus == 1:
        return "Confirmed"
    if docstatus == 2:
        return "Cancelled"
    return "Unknown"


def get_period_days(from_date, to_date):
    return max(1, date_diff(to_date, from_date) + 1)


def get_overlap_days(start_date, end_date, period_start, period_end):
    overlap_start = max(getdate(start_date), getdate(period_start))
    overlap_end = min(getdate(end_date), getdate(period_end))

    if overlap_end < overlap_start:
        return 0

    return max(1, date_diff(overlap_end, overlap_start))


def get_first_day_of_current_month():
    today = getdate(nowdate())
    return today.replace(day=1)