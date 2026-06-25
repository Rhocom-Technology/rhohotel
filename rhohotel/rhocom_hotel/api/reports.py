import frappe
from frappe.utils import now_datetime, format_datetime
from frappe.utils.pdf import get_pdf


def _logo_to_data_uri(logo_path):
    """
    Convert a Frappe file path like /files/logo.png to a base64 data URI
    so wkhtmltopdf doesn't need to make a network request to fetch it.
    Returns empty string if file not found or conversion fails.
    """
    if not logo_path:
        return ""
    try:
        import base64, mimetypes, os
        site_path = os.path.abspath(frappe.get_site_path())
        if logo_path.startswith("/files/"):
            abs_path = os.path.join(site_path, "public", logo_path.lstrip("/"))
        elif logo_path.startswith("/private/files/"):
            abs_path = os.path.join(site_path, logo_path.lstrip("/"))
        else:
            return logo_path
        if not os.path.exists(abs_path):
            return ""
        mime, _ = mimetypes.guess_type(abs_path)
        mime = mime or "image/png"
        with open(abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""

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

    # Pull hotel branding from Hotel Settings and Company record
    settings = frappe.get_single("Hotel Settings")

    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""

    # Try to enrich with company phone/email/website from Frappe Company doctype
    hotel_phone = ""
    hotel_email = ""
    hotel_website = ""
    try:
        company_doc = frappe.get_doc("Company", hotel_company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        hotel_website = company_doc.get("website") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company": hotel_company,
        "hotel_logo": hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone": hotel_phone,
        "hotel_email": hotel_email,
        "hotel_website": hotel_website,
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

@frappe.whitelist()
def download_reservation_confirmation(reservation_name=None):
    if not reservation_name:
        frappe.throw("Reservation name is required.")

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    rooms = []
    for room in (doc.rooms or []):
        rooms.append({
            "room_number":   room.room_number or "",
            "room_type":     room.room_type or "",
            "rate_per_night": flt(room.rate_per_night or 0),
            "room_total":    flt(room.room_total or 0),
            "occupant_name": room.occupant_name or "",
        })

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "reservation": {
            "name":                reservation_name,
            "reservation_status":  doc.reservation_status or "",
            "payment_status":      doc.payment_status or "",
            "reservation_type":    doc.reservation_type or "",
            "source_channel":      doc.source_channel or "",
            "primary_guest_name":  doc.primary_guest_name or "",
            "primary_guest_email": doc.primary_guest_email or "",
            "primary_guest_phone": doc.primary_guest_phone or "",
            "from_date":           str(doc.from_date or ""),
            "to_date":             str(doc.to_date or ""),
            "number_of_nights":    doc.number_of_nights or 0,
            "booking_notes":       doc.booking_notes or "",
            "subtotal":            flt(doc.subtotal or 0),
            "discount_amount":     flt(doc.discount_amount or 0),
            "total_amount":        flt(doc.total_amount or 0),
            "rooms":               rooms,
        },
        "generated_at": format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    settings = frappe.get_single("Hotel Settings")
    print_format = settings.reservation_print_format

    if not print_format:
        frappe.throw("Please set Reservation Confirmation Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Reservation-{reservation_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_guest_folio(checkin_name=None):
    if not checkin_name:
        frappe.throw("Check-in name is required.")

    from rhohotel.rhocom_hotel.api.checkin import get_checkin_detail

    data = get_checkin_detail(checkin_name)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    invoices = data.get("invoices") or []
    payments = data.get("payments") or []

    total_charges = sum(
        flt(inv.get("amount") or 0)
        for inv in invoices
        if not inv.get("is_return")
    )
    total_credits = sum(
        flt(inv.get("amount") or 0)
        for inv in invoices
        if inv.get("is_return")
    )
    total_paid = sum(
        flt(pmt.get("paid_amount") or 0)
        for pmt in payments
        if pmt.get("docstatus") == 1
    )
    total_outstanding = sum(
        flt(inv.get("outstanding_amount") or 0)
        for inv in invoices
        if not inv.get("is_return")
    )
    balance = total_outstanding - total_paid if total_outstanding else (total_charges - total_credits - total_paid)

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "checkin":       data,
        "invoices":      invoices,
        "payments":      payments,
        "total_charges": total_charges,
        "total_paid":    total_paid,
        "total_outstanding": total_outstanding,
        "balance":       balance,
        "generated_at":  format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.checkin_folio_print_format

    if not print_format:
        frappe.throw("Please set Guest Folio Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Guest-Folio-{checkin_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_corporate_bill(invoice_name=None):
    if not invoice_name:
        frappe.throw("Invoice name is required.")

    from rhohotel.rhocom_hotel.api.corporate_billing import get_corporate_bill_detail

    bill = get_corporate_bill_detail(invoice_name)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "bill":          bill,
        "generated_at":  format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.corporate_bill_print_format

    if not print_format:
        frappe.throw("Please set Corporate Bill Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Corporate-Bill-{invoice_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_room_record(room_id=None):
    if not room_id:
        frappe.throw("Room ID is required.")

    from rhohotel.rhocom_hotel.api.room import get_room_detail

    room = get_room_detail(room_id)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "room":          room,
        "generated_at":  format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.room_record_print_format

    if not print_format:
        frappe.throw("Please set Room Record Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    room_number = (room.get("room_number") or room_id).replace(" ", "-")
    frappe.local.response.filename    = f"Room-{room_number}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_complimentary_record(complimentary_name=None):
    if not complimentary_name:
        frappe.throw("Complimentary name is required.")

    from rhohotel.rhocom_hotel.api.complimentary import get_complimentary

    record = get_complimentary(complimentary_name)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "record":        record,
        "generated_at":  format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.complimentary_print_format

    if not print_format:
        frappe.throw("Please set Complimentary Record Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    guest_name = (record.get("guest") or "").strip().replace(" ", "-")
    frappe.local.response.filename    = f"Complimentary-{complimentary_name}-{guest_name}.pdf" if guest_name else f"Complimentary-{complimentary_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_maintenance_task(task_name=None):
    if not task_name:
        frappe.throw("Task name is required.")

    from rhohotel.rhocom_hotel.api.maintenance_task import get_maintenance_task

    task = get_maintenance_task(task_name)

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    # Convert request images to base64 to avoid wkhtmltopdf network errors
    for img_key in ("request_image_1", "request_image_2", "request_image_3"):
        if task.get(img_key):
            task[img_key] = _logo_to_data_uri(task[img_key]) or ""

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "task":          task,
        "generated_at":  format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.maintenance_task_print_format

    if not print_format:
        frappe.throw("Please set Maintenance Task Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Maintenance-Task-{task_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_guest_ledger_report(
    date_from=None,
    date_to=None,
    guest=None,
    checkin_status=None,
    room_type=None,
    transaction_type=None,
    search=None,
    include_corporate=0,
):
    from rhohotel.rhocom_hotel.api.guest_ledger_report import get_guest_ledger_report

    result = get_guest_ledger_report(
        date_from=date_from,
        date_to=date_to,
        guest=guest,
        checkin_status=checkin_status,
        room_type=room_type,
        transaction_type=transaction_type,
        search=search,
        include_corporate=include_corporate,
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    # Resolve guest name for display
    guest_label = guest or "All Guests"
    if guest:
        try:
            gname = frappe.db.get_value("Hotel Guest", guest, "guest_name")
            if gname:
                guest_label = gname
        except Exception:
            pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "rows":          result.get("rows", []),
        "summary":       result.get("summary", {}),
        "filters": {
            "date_from":        result.get("filters", {}).get("date_from") or date_from or "",
            "date_to":          result.get("filters", {}).get("date_to") or date_to or "",
            "guest":            guest_label,
            "checkin_status":   checkin_status or "All",
            "room_type":        room_type or "All Room Types",
            "transaction_type": transaction_type or "All Transactions",
        },
        "generated_at":  result.get("generated_at") or format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.guest_ledger_print_format

    if not print_format:
        frappe.throw("Please set Guest Ledger Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    filename = f"Guest-Ledger-{context['filters']['date_from']}-to-{context['filters']['date_to']}.pdf"
    frappe.local.response.filename    = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_kitchen_order_report(
    date_from=None,
    date_to=None,
    status=None,
    source=None,
    station=None,
    pos_profile=None,
    search=None,
    limit=500,
):
    from rhohotel.restaurant.api.kitchen import get_kitchen_order_report

    result = get_kitchen_order_report(
        date_from=date_from,
        date_to=date_to,
        status=status,
        source=source,
        station=station,
        pos_profile=pos_profile,
        search=search,
        limit=limit,
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "rows":          result.get("rows", []),
        "summary":       result.get("summary", {}),
        "filters": {
            "date_from":   date_from or "",
            "date_to":     date_to or "",
            "status":      status or "All",
            "source":      source or "All",
            "station":     station or "All",
            "pos_profile": pos_profile or "All",
        },
        "generated_at": format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.kitchen_order_print_format

    if not print_format:
        frappe.throw("Please set Kitchen Order Report Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")
    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Kitchen-Order-Report-{date_from}-to-{date_to}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"


@frappe.whitelist()
def download_complimentary_house_use_report(
    date_from=None,
    date_to=None,
    reservation_type=None,
    status=None,
    search=None,
):
    from rhohotel.rhocom_hotel.api.special_reservation_report import get_special_reservation_report

    result = get_special_reservation_report(
        date_from=date_from,
        date_to=date_to,
        reservation_type=reservation_type,
        status=status,
        search=search,
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    settings = frappe.get_single("Hotel Settings")
    hotel_logo    = _logo_to_data_uri(settings.get("hotel_logo") or "")
    hotel_tagline = settings.get("hotel_tagline") or ""
    hotel_address = settings.get("hotel_address") or ""
    hotel_phone   = ""
    hotel_email   = ""

    try:
        company_doc = frappe.get_doc("Company", company)
        hotel_phone = company_doc.get("phone_no") or ""
        hotel_email = company_doc.get("email") or ""
        if not hotel_address:
            parts = [
                company_doc.get("address_line1") or "",
                company_doc.get("address_line2") or "",
                company_doc.get("city") or "",
                company_doc.get("state") or "",
                company_doc.get("country") or "",
            ]
            hotel_address = ", ".join(p for p in parts if p)
    except Exception:
        pass

    context = {
        "company":       company,
        "hotel_logo":    hotel_logo,
        "hotel_tagline": hotel_tagline,
        "hotel_address": hotel_address,
        "hotel_phone":   hotel_phone,
        "hotel_email":   hotel_email,
        "rows":          result.get("rows", []),
        "summary":       result.get("summary", {}),
        "filters": {
            "date_from":        date_from or "",
            "date_to":          date_to or "",
            "reservation_type": reservation_type or "All Types",
            "status":           status or "All",
            "search":           search or "",
        },
        "generated_at": format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
    }

    print_format = settings.complimentary_house_use_print_format

    if not print_format:
        frappe.throw("Please set Complimentary & House Use Report Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")
    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)
    pdf  = get_pdf(html)

    frappe.local.response.filename    = f"Complimentary-House-Use-{date_from}-to-{date_to}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type        = "download"