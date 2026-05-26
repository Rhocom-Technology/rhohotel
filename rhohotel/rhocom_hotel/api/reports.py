import frappe
from frappe.utils import now_datetime, format_datetime
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def download_daily_occupancy_report(
    date_from=None,
    date_to=None,
    room=None,
    floor=None,
    status=None,
    payment=None,
    search=None,
    overdue_only=0
):
    from rhohotel.rhocom_hotel.api.daily_occupany_report import get_daily_occupancy_report

    result = get_daily_occupancy_report(
        date_from=date_from,
        date_to=date_to,
        room=room,
        floor=floor,
        status=status,
        payment=payment,
        search=search,
        overdue_only=overdue_only
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    context = {
        "company": company,
        "rows": result.get("rows", []),
        "stats": result.get("stats", {}),
        "totals": result.get("totals", {}),
        "filters": result.get("filters", {}),
        "generated_at": result.get("generated_at", ""),
        "applied_filters": {
            "room": room or "All Rooms",
            "floor": floor or "All Floors",
            "status": status or "All Status",
            "payment": payment or "All Payment",
            "search": search or "",
            "overdue_only": "Yes" if str(overdue_only) == "1" else "No"
        }
    }

    # html = frappe.render_template(
    #     "rhohotel/rhocom_hotel/templates/reports/daily_occupancy_report.html",
    #     context
    # )
    
    settings = frappe.get_single("Hotel Settings")

    print_format = settings.daily_occupancy_print_format

    if not print_format:
        frappe.throw("Please set Daily Occupancy Report Print Format in Hotel Settings.")

    html_template = frappe.db.get_value(
        "Print Format",
        print_format,
        "html"
    )

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(
        html_template,
        context
    )

    pdf = get_pdf(html)

    filename = "Daily-Occupancy-Report-{0}-to-{1}.pdf".format(
        context["filters"].get("date_from") or date_from,
        context["filters"].get("date_to") or date_to
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    









@frappe.whitelist()
def download_guest_stay_history_report(
    date_from=None,
    date_to=None,
    guest_type=None,
    room_type=None,
    payment=None,
    source=None,
    search=None
):
    from rhohotel.rhocom_hotel.api.guest_stay_history_report import get_guest_stay_history

    result = get_guest_stay_history(
        date_from=date_from,
        date_to=date_to,
        guest_type=guest_type,
        room_type=room_type,
        payment=payment,
        source=source,
        search=search
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    context = {
        "company": company,
        "rows": result.get("rows", []),
        "stats": result.get("stats", {}),
        "totals": result.get("totals", {}),
        "filters": result.get("filters", {}),
        "generated_at": result.get("generated_at", ""),
        "applied_filters": {
            "guest_type": guest_type or "All Guests",
            "room_type": room_type or "All Room Types",
            "payment": payment or "All Payment Status",
            "source": source or "All Channels",
            "search": search or ""
        }
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.guest_stay_history_print_format

    if not print_format:
        frappe.throw("Please set Guest Stay History Print Format in Hotel Settings.")

    html_template = frappe.db.get_value(
        "Print Format",
        print_format,
        "html"
    )

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)

    pdf = get_pdf(html)

    filename = "Guest-Stay-History-{0}-to-{1}.pdf".format(
        context["filters"].get("date_from") or date_from,
        context["filters"].get("date_to") or date_to
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    
    
import frappe
from frappe.utils import now_datetime, format_datetime, flt
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def download_night_audit_summary_report(
    audit_date=None,
    revenue_type=None,
    pos_profile=None,
    status=None,
    search=None
):
    from rhohotel.rhocom_hotel.api.night_audit_summary_report import (
        get_night_audit_summary_report
    )

    result = get_night_audit_summary_report(
        audit_date=audit_date,
        revenue_type=revenue_type,
        pos_profile=pos_profile,
        status=status,
        search=search
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    rows = result.get("rows", [])

    context = {
        "company": company,
        "rows": rows,
        "summary": result.get("summary", {}),
        "payment_breakdown": result.get("payment_breakdown", []),
        "revenue_breakdown": result.get("revenue_breakdown", []),
        "exceptions": result.get("exceptions", []),
        "generated_at": format_datetime(
            now_datetime(),
            "dd-MM-yyyy HH:mm:ss"
        ),
        "filters": {
            "audit_date": audit_date or "",
            "revenue_type": revenue_type or "All Revenue",
            "pos_profile": pos_profile or "All POS Profiles",
            "status": status or "All Status",
            "search": search or "",
        },
        "totals": {
            "gross_amount": sum(
                flt(r.get("gross_amount"))
                for r in rows
            ),
            "tax": sum(
                flt(r.get("tax"))
                for r in rows
            ),
            "discount": sum(
                flt(r.get("discount"))
                for r in rows
            ),
            "paid_amount": sum(
                flt(r.get("paid_amount"))
                for r in rows
            ),
            "outstanding_amount": sum(
                flt(r.get("outstanding_amount"))
                for r in rows
            ),
        },
    }

    settings = frappe.get_single("Hotel Settings")

    print_format = settings.night_audit_print_format

    if not print_format:
        frappe.throw(
            "Please set Night Audit Summary Print Format in Hotel Settings."
        )

    html_template = frappe.db.get_value(
        "Print Format",
        print_format,
        "html"
    )

    if not html_template:
        frappe.throw(
            "The selected Print Format has no HTML content."
        )

    html = frappe.render_template(
        html_template,
        context
    )

    pdf = get_pdf(html)

    filename = "Night-Audit-Summary-{0}.pdf".format(
        audit_date or context["summary"].get("audit_date")
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    
    




@frappe.whitelist()
def download_corporate_account_statement_report(
    date_from=None,
    date_to=None,
    customer=None,
    transaction_type=None,
    search=None
):
    from rhohotel.rhocom_hotel.api.corporate_account_statement import (
        get_corporate_account_statement
    )

    result = get_corporate_account_statement(
        date_from=date_from,
        date_to=date_to,
        customer=customer,
        transaction_type=transaction_type,
        search=search,
        account_page=1,
        account_page_size=5000
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    customer_label = "All Customers"
    if customer:
        customer_label = (
            frappe.db.get_value("Customer", customer, "customer_name")
            or customer
        )

    context = {
        "company": company,
        "rows": result.get("rows", []),
        "account_summary": result.get("account_summary", []),
        "summary": result.get("summary", {}),
        "generated_at": format_datetime(
            now_datetime(),
            "dd-MM-yyyy HH:mm:ss"
        ),
        "filters": {
            "date_from": date_from or "",
            "date_to": date_to or "",
            "customer": customer or "",
            "customer_label": customer_label,
            "transaction_type": transaction_type or "All Transactions",
            "search": search or "",
        },
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.corporate_account_statement_print_format

    if not print_format:
        frappe.throw(
            "Please set Corporate Account Statement Print Format in Hotel Settings."
        )

    html_template = frappe.db.get_value(
        "Print Format",
        print_format,
        "html"
    )

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)

    pdf = get_pdf(html)

    filename = "Corporate-Account-Statement-{0}-to-{1}.pdf".format(
        date_from or "from",
        date_to or "to"
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    
    


import frappe
from frappe.utils import now_datetime, format_datetime, flt
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def download_corporate_billing_statement_report(
    date_from=None,
    date_to=None,
    company=None,
    status=None,
    aging_bucket=None,
    search=None,
):
    from rhohotel.rhocom_hotel.api.corporate_billing_statement import (
        get_corporate_billing_statement
    )

    result = get_corporate_billing_statement(
        date_from=date_from,
        date_to=date_to,
        company=company,
        status=status,
        aging_bucket=aging_bucket,
        search=search,
        company_page=1,
        company_page_size=5000,
        aging_page=1,
        aging_page_size=100,
    )

    hotel_company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    rows = result.get("rows", [])

    context = {
        "company": hotel_company,
        "rows": rows,
        "summary": result.get("summary", {}),
        "company_summary": result.get("company_summary", []),
        "aging_breakdown": result.get("aging_breakdown", []),
        "generated_at": format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
        "filters": {
            "date_from": date_from or "",
            "date_to": date_to or "",
            "company": company or "All Companies",
            "status": status or "All Status",
            "aging_bucket": aging_bucket or "All Aging",
            "search": search or "",
        },
        "totals": {
            "billed_amount": sum(flt(r.get("billed_amount")) for r in rows),
            "paid_amount": sum(flt(r.get("paid_amount")) for r in rows),
            "outstanding_amount": sum(flt(r.get("outstanding_amount")) for r in rows),
        },
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.corporate_billing_print_format

    if not print_format:
        frappe.throw("Please set Corporate Billing Statement Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf = get_pdf(html)

    filename = "Corporate-Billing-Statement-{0}-to-{1}.pdf".format(
        date_from or "from",
        date_to or "to"
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    
import frappe
from frappe.utils import now_datetime, format_datetime, flt
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def download_pos_sales_performance_report(
    date_from=None,
    date_to=None,
    pos_profile=None,
    cashier=None,
    payment_mode=None,
    search=None
):
    from rhohotel.rhocom_hotel.api.pos_sales_performance import (
        get_pos_sales_performance_report
    )

    result = get_pos_sales_performance_report(
        date_from=date_from,
        date_to=date_to,
        pos_profile=pos_profile,
        cashier=cashier,
        payment_mode=payment_mode,
        search=search
    )

    sales = result.get("sales", [])

    summary = {
        "gross_sales": sum(flt(row.get("gross_amount")) for row in sales),
        "net_sales": sum(flt(row.get("net_amount")) for row in sales),
        "total_orders": len(sales),
        "average_order_value": (
            sum(flt(row.get("net_amount")) for row in sales) / len(sales)
            if sales else 0
        ),
        "total_discount": sum(flt(row.get("discount")) for row in sales),
        "outstanding": sum(flt(row.get("outstanding")) for row in sales),
    }

    totals = {
        "gross_amount": sum(flt(row.get("gross_amount")) for row in sales),
        "discount": sum(flt(row.get("discount")) for row in sales),
        "tax": sum(flt(row.get("tax")) for row in sales),
        "net_amount": sum(flt(row.get("net_amount")) for row in sales),
    }

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    context = {
        "company": company,
        "sales": sales,
        "shifts": result.get("shifts", []),
        "top_items": result.get("top_items", []),
        "summary": summary,
        "totals": totals,
        "payment_breakdown": _build_pos_payment_breakdown(sales),
        "cashier_performance": _build_pos_cashier_performance(sales),
        "generated_at": result.get("generated_at") or format_datetime(
            now_datetime(),
            "dd-MM-yyyy HH:mm:ss"
        ),
        "filters": {
            "date_from": result.get("filters", {}).get("date_from") or date_from or "",
            "date_to": result.get("filters", {}).get("date_to") or date_to or "",
            "pos_profile": pos_profile or "All POS Profiles",
            "cashier": cashier or "All Cashiers",
            "payment_mode": payment_mode or "All Payment Modes",
            "search": search or "",
        },
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.pos_sales_print_format

    if not print_format:
        frappe.throw("Please set POS Sales Performance Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf = get_pdf(html)

    filename = "POS-Sales-Performance-{0}-to-{1}.pdf".format(
        context["filters"].get("date_from") or "from",
        context["filters"].get("date_to") or "to"
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"


def _build_pos_payment_breakdown(sales):
    payment_map = {}

    for row in sales:
        modes = str(row.get("payment_mode") or "Unknown").split(",")

        for mode_raw in modes:
            mode = mode_raw.strip() or "Unknown"
            payment_map[mode] = payment_map.get(mode, 0) + flt(row.get("net_amount"))

    return sorted(
        [{"mode": mode, "amount": amount} for mode, amount in payment_map.items()],
        key=lambda x: flt(x.get("amount")),
        reverse=True
    )


def _build_pos_cashier_performance(sales):
    cashier_map = {}

    for row in sales:
        cashier = row.get("cashier") or "Unknown"

        if cashier not in cashier_map:
            cashier_map[cashier] = {
                "cashier": cashier,
                "orders": 0,
                "sales": 0,
            }

        cashier_map[cashier]["orders"] += 1
        cashier_map[cashier]["sales"] += flt(row.get("net_amount"))

    return sorted(
        cashier_map.values(),
        key=lambda x: flt(x.get("sales")),
        reverse=True
    )
    

import frappe
from frappe.utils import now_datetime, format_datetime, cint
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def download_housekeeping_productivity_report(
    date_from=None,
    date_to=None,
    housekeeper=None,
    floor=None,
    status=None,
    search=None
):
    from rhohotel.rhocom_hotel.api.housekeeping_productivity_report import (
        get_housekeeping_productivity_report
    )

    result = get_housekeeping_productivity_report(
        date_from=date_from,
        date_to=date_to,
        housekeeper=housekeeper,
        floor=floor,
        status=status,
        search=search
    )

    rows = result.get("rows", [])

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    summary = result.get("summary", {})

    context = {
        "company": company,
        "rows": rows,
        "summary": {
            "rooms_assigned": summary.get("total_tasks", 0),
            "rooms_cleaned": summary.get("rooms_cleaned", 0),
            "rooms_inspected": summary.get("rooms_inspected", 0),
            "avg_cleaning_time": summary.get("avg_duration", 0),
            "guest_requests": summary.get("guest_requests", 0),
            "maintenance_issues": summary.get("issue_count", 0),
            "pending_tasks": summary.get("pending_tasks", 0),
        },
        "status_breakdown": _build_housekeeping_status_breakdown(rows),
        "housekeeper_performance": _build_housekeeper_performance(rows),
        "floor_performance": _build_floor_performance(rows),
        "inspector_summary": _build_inspector_summary(rows),
        "totals": {
            "duration": sum(cint(r.get("duration")) for r in rows),
            "guest_requests": sum(cint(r.get("guest_requests")) for r in rows),
        },
        "generated_at": result.get("generated_at") or format_datetime(
            now_datetime(),
            "dd-MM-yyyy HH:mm:ss"
        ),
        "filters": {
            "date_from": result.get("filters", {}).get("date_from") or date_from or "",
            "date_to": result.get("filters", {}).get("date_to") or date_to or "",
            "housekeeper": housekeeper or "All Housekeepers",
            "floor": floor or "All Floors",
            "status": status or "All Statuses",
            "search": search or "",
        },
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.housekeeping_productivity_print_format

    if not print_format:
        frappe.throw("Please set Housekeeping Productivity Report Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf = get_pdf(html)

    filename = "Housekeeping-Productivity-{0}-to-{1}.pdf".format(
        context["filters"].get("date_from") or "from",
        context["filters"].get("date_to") or "to"
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"


def _build_housekeeping_status_breakdown(rows):
    status_map = {}

    for row in rows:
        status = row.get("status") or "Unknown"
        status_map[status] = status_map.get(status, 0) + 1

    return sorted(
        [{"status": status, "count": count} for status, count in status_map.items()],
        key=lambda x: cint(x.get("count")),
        reverse=True
    )


def _is_housekeeping_done(status):
    return str(status or "").strip() in [
        "Cleaned",
        "Inspected",
        "Released",
        "Completed",
        "Done",
        "Finished",
        "Ready",
    ]


def _build_housekeeper_performance(rows):
    data = {}

    for row in rows:
        name = row.get("housekeeper") or "Unknown"

        if name not in data:
            data[name] = {
                "housekeeper": name,
                "assigned": 0,
                "cleaned": 0,
                "duration": 0,
                "duration_count": 0,
                "requests": 0,
            }

        data[name]["assigned"] += 1

        if _is_housekeeping_done(row.get("status")):
            data[name]["cleaned"] += 1

        if cint(row.get("duration")) > 0:
            data[name]["duration"] += cint(row.get("duration"))
            data[name]["duration_count"] += 1

        data[name]["requests"] += cint(row.get("guest_requests"))

    output = []

    for item in data.values():
        avg_time = (
            int(item["duration"] / item["duration_count"])
            if item["duration_count"] else 0
        )

        completion_rate = (
            (float(item["cleaned"]) / float(item["assigned"])) * 100
            if item["assigned"] else 0
        )

        speed_score = max(0, 100 - max(0, avg_time - 25) * 2) if avg_time else 0
        score = int(round((completion_rate * 0.7) + (speed_score * 0.3)))

        item["avg_time"] = avg_time
        item["score"] = score

        output.append(item)

    return sorted(output, key=lambda x: cint(x.get("score")), reverse=True)


def _build_floor_performance(rows):
    data = {}

    for row in rows:
        floor = row.get("floor") or "Unknown"

        if floor not in data:
            data[floor] = {
                "floor": floor,
                "assigned": 0,
                "cleaned": 0,
            }

        data[floor]["assigned"] += 1

        if _is_housekeeping_done(row.get("status")):
            data[floor]["cleaned"] += 1

    output = []

    for item in data.values():
        item["completion"] = (
            int(round((float(item["cleaned"]) / float(item["assigned"])) * 100))
            if item["assigned"] else 0
        )
        output.append(item)

    return sorted(output, key=lambda x: str(x.get("floor")))


def _build_inspector_summary(rows):
    data = {}

    for row in rows:
        inspector = row.get("inspector")
        if not inspector:
            continue

        if inspector not in data:
            data[inspector] = {
                "inspector": inspector,
                "inspected": 0,
                "released": 0,
                "rejected": 0,
            }

        if row.get("status") in ["Inspected", "Released", "Maintenance"]:
            data[inspector]["inspected"] += 1

        if row.get("status") == "Released":
            data[inspector]["released"] += 1

        if row.get("status") == "Maintenance":
            data[inspector]["rejected"] += 1

    return sorted(data.values(), key=lambda x: cint(x.get("inspected")), reverse=True)