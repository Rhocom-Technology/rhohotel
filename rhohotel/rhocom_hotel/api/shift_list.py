import frappe
from frappe.utils import now_datetime, format_datetime, getdate, add_days, formatdate
from frappe.utils.pdf import get_pdf


def _to_int(value, default_value):
    try:
        return int(value)
    except Exception:
        return default_value


def _get_default_company():
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
    )


def _get_week_start(value=None):
    date_value = getdate(value) if value else getdate()
    return add_days(date_value, -date_value.weekday())


def _get_shift_time(shift_type):
    if not shift_type:
        return ""

    values = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["start_time", "end_time"],
        as_dict=True
    )

    if not values:
        return ""

    start_time = values.get("start_time")
    end_time = values.get("end_time")

    if not start_time or not end_time:
        return ""

    return "{} - {}".format(start_time, end_time)


def _empty_stats():
    return {
        "publishedThisWeek": 0,
        "staffScheduled": 0,
        "unpublished": 0,
        "yourShiftsThisWeek": 0,
        "shiftTypeCounts": []
    }


def _can_view_all_departments():
    """Administrator and Hotel Manager can see/filter every department.
    Everyone else is restricted to their own department only."""
    user = frappe.session.user
    if user == "Administrator":
        return True
    roles = frappe.get_roles(user)
    return "Hotel Manager" in roles


def _get_user_department():
    """Resolve the current user's own department via their linked Employee
    record. Returns None if no Employee is linked or it has no department."""
    user = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    if not employee:
        return None
    return frappe.db.get_value("Employee", employee, "department")


def _resolve_department_filter(requested_department):
    """Server-side enforcement of the department restriction: restricted
    users always get their own department regardless of what's requested
    from the client, so this can't be bypassed by calling the API directly
    with a different department value."""
    if _can_view_all_departments():
        return requested_department

    own_department = _get_user_department()
    return own_department or "__NONE__"  # no department linked -> see nothing


@frappe.whitelist()
def get_departments():
    """Department dropdown options. Administrator/Hotel Manager get every
    department in the company; everyone else only gets their own (so the
    dropdown reflects what they're actually allowed to see)."""
    company = _get_default_company()
    if not company:
        return []

    if not _can_view_all_departments():
        own_department = _get_user_department()
        return [own_department] if own_department else []

    rows = frappe.db.sql("""
        select distinct emp.department
        from `tabEmployee` emp
        where
            emp.status = 'Active'
            and emp.company = %(company)s
            and emp.department is not null
            and emp.department != ''
        order by emp.department asc
    """, {"company": company}, as_dict=True)

    return [row.department for row in rows]


@frappe.whitelist()
def get_shift_types():
    rows = frappe.get_all(
        "Shift Type",
        fields=["name"],
        order_by="name asc"
    )
    return ["All Shifts"] + [row.name for row in rows]


@frappe.whitelist()
def get_shift_list(department=None, week_start=None, shift_type=None, page=1, page_size=15):
    company = _get_default_company()
    department = _resolve_department_filter(department)

    if not company:
        return {
            "records": [],
            "stats": _empty_stats(),
            "pagination": {
                "page": 1,
                "page_size": 15,
                "total": 0,
                "total_pages": 1
            }
        }

    page = _to_int(page, 1)
    page_size = _to_int(page_size, 15)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 15

    start = (page - 1) * page_size

    week_start_date = _get_week_start(week_start)
    week_end_date = add_days(week_start_date, 6)

    filters = {
        "company": company,
        "week_start": week_start_date,
        "week_end": week_end_date,
        "start": start,
        "page_size": page_size
    }

    department_condition = ""
    shift_condition = ""

    if department:
        department_condition = " and emp.department = %(department)s"
        filters["department"] = department

    if shift_type and shift_type != "All Shifts":
        shift_condition = " and sa.shift_type = %(shift_type)s"
        filters["shift_type"] = shift_type

    rows = frappe.db.sql("""
        select
            sa.name as id,
            sa.employee,
            emp.employee_name as staff,
            emp.designation,
            emp.department,
            sa.shift_type,
            sa.start_date,
            sa.end_date
        from `tabShift Assignment` sa
        inner join `tabEmployee` emp on emp.name = sa.employee
        where
            sa.docstatus = 1
            and emp.status = 'Active'
            and emp.company = %(company)s
            and sa.start_date <= %(week_end)s
            and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            {department_condition}
            {shift_condition}
        order by
            sa.start_date asc,
            sa.shift_type asc,
            emp.employee_name asc
        limit %(page_size)s offset %(start)s
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    total_row = frappe.db.sql("""
        select count(*) as total
        from `tabShift Assignment` sa
        inner join `tabEmployee` emp on emp.name = sa.employee
        where
            sa.docstatus = 1
            and emp.status = 'Active'
            and emp.company = %(company)s
            and sa.start_date <= %(week_end)s
            and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            {department_condition}
            {shift_condition}
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    total = total_row[0].total if total_row else 0

    records = []
    for row in rows:
        row_date = getdate(row.start_date)

        records.append({
            "id": row.id,
            "staff": row.staff or row.employee,
            "roleStation": "{} • {}".format(row.designation or "—", row.department or "—"),
            "day": row_date.strftime("%A"),
            "shift": row.shift_type or "—",
            "time": _get_shift_time(row.shift_type),
            "status": "Published"
        })

    total_pages = int((total + page_size - 1) / page_size) if total else 1

    return {
        "records": records,
        "stats": get_shift_stats(
            department=department,
            week_start=week_start_date,
            shift_type=shift_type
        ),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }


def _expand_to_week_days(rows, week_start_date, week_end_date):
    """Given Shift Assignment rows (each with start_date/end_date possibly
    spanning many days), expand each into one entry per day that actually
    falls within [week_start_date, week_end_date]. A single 7-day
    assignment becomes 7 entries here; a single 1-day assignment becomes 1.
    This is what 'Published Shifts This Week' / 'Shift Type Counts' /
    'Your Shifts This Week' are actually meant to count: shift-days
    occurring this week, not assignment records.
    """
    expanded = []
    for row in rows:
        start = getdate(row.start_date)
        end = getdate(row.end_date or row.start_date)
        day = max(start, week_start_date)
        last_day = min(end, week_end_date)
        while day <= last_day:
            expanded.append({
                "employee": row.employee,
                "shift_type": row.shift_type,
                "date": day,
            })
            day = add_days(day, 1)
    return expanded


@frappe.whitelist()
def get_shift_stats(department=None, week_start=None, shift_type=None):
    company = _get_default_company()
    department = _resolve_department_filter(department)

    if not company:
        return _empty_stats()

    week_start_date = _get_week_start(week_start)
    week_end_date = add_days(week_start_date, 6)

    filters = {
        "company": company,
        "week_start": week_start_date,
        "week_end": week_end_date
    }

    department_condition = ""
    shift_condition = ""

    if department:
        department_condition = " and emp.department = %(department)s"
        filters["department"] = department

    if shift_type and shift_type != "All Shifts":
        shift_condition = " and sa.shift_type = %(shift_type)s"
        filters["shift_type"] = shift_type

    # Fetch the raw overlapping rows once -- everything else is derived
    # from expanding these into individual shift-days in Python, since the
    # date-range schema makes day-level counting awkward to express purely
    # in SQL.
    published_assignment_rows = frappe.db.sql("""
        select sa.employee, sa.shift_type, sa.start_date, sa.end_date
        from `tabShift Assignment` sa
        inner join `tabEmployee` emp on emp.name = sa.employee
        where
            sa.docstatus = 1
            and emp.status = 'Active'
            and emp.company = %(company)s
            and sa.start_date <= %(week_end)s
            and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            {department_condition}
            {shift_condition}
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    unpublished_assignment_rows = frappe.db.sql("""
        select sa.employee, sa.shift_type, sa.start_date, sa.end_date
        from `tabShift Assignment` sa
        inner join `tabEmployee` emp on emp.name = sa.employee
        where
            sa.docstatus = 0
            and emp.status = 'Active'
            and emp.company = %(company)s
            and sa.start_date <= %(week_end)s
            and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            {department_condition}
            {shift_condition}
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    published_days = _expand_to_week_days(published_assignment_rows, week_start_date, week_end_date)
    unpublished_days = _expand_to_week_days(unpublished_assignment_rows, week_start_date, week_end_date)

    published_this_week = len(published_days)
    staff_scheduled = len(set(d["employee"] for d in published_days))

    shift_type_totals = {}
    for d in published_days:
        key = d["shift_type"] or "Unknown"
        shift_type_totals[key] = shift_type_totals.get(key, 0) + 1

    shift_type_counts = [
        {"shift_type": k, "count": v}
        for k, v in sorted(shift_type_totals.items())
    ]

    # "Your Shifts This Week" -- shift-days for the currently logged-in
    # user specifically, not all staff. Resolved via their linked Employee.
    current_employee = frappe.db.get_value(
        "Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
    )
    your_shifts_this_week = (
        sum(1 for d in published_days if d["employee"] == current_employee)
        if current_employee else 0
    )

    return {
        "publishedThisWeek": published_this_week,
        "staffScheduled": staff_scheduled,
        "unpublished": len(unpublished_days),
        "yourShiftsThisWeek": your_shifts_this_week,
        "shiftTypeCounts": shift_type_counts
    }


@frappe.whitelist()
def get_shift_calendar(department=None, week_start=None, shift_type=None):
    company = _get_default_company()
    department = _resolve_department_filter(department)

    if not company:
        return {
            "days": [],
            "staff": []
        }

    week_start_date = _get_week_start(week_start)
    week_end_date = add_days(week_start_date, 6)

    filters = {
        "company": company,
        "week_start": week_start_date,
        "week_end": week_end_date
    }

    department_condition = ""
    shift_condition = ""

    if department:
        department_condition = " and emp.department = %(department)s"
        filters["department"] = department

    if shift_type and shift_type != "All Shifts":
        shift_condition = " and sa.shift_type = %(shift_type)s"
        filters["shift_type"] = shift_type

    employees = frappe.db.sql("""
        select
            emp.name as employee,
            emp.employee_name,
            emp.designation,
            emp.department
        from `tabEmployee` emp
        where
            emp.status = 'Active'
            and emp.company = %(company)s
            {department_condition}
        order by emp.employee_name asc
    """.format(
        department_condition=department_condition
    ), filters, as_dict=True)

    assignments = frappe.db.sql("""
        select
            sa.name,
            sa.employee,
            sa.shift_type,
            sa.start_date,
            sa.end_date
        from `tabShift Assignment` sa
        inner join `tabEmployee` emp on emp.name = sa.employee
        where
            sa.docstatus = 1
            and emp.status = 'Active'
            and emp.company = %(company)s
            and sa.start_date <= %(week_end)s
            and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            {department_condition}
            {shift_condition}
        order by sa.start_date asc, sa.shift_type asc
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    days = []
    for index in range(7):
        current_date = add_days(week_start_date, index)
        days.append({
            "date": str(current_date),
            "label": current_date.strftime("%A"),
            "dateLabel": formatdate(current_date, "dd MMM")
        })

    staff_map = {}

    for emp in employees:
        staff_map[emp.employee] = {
            "id": emp.employee,
            "name": emp.employee_name or emp.employee,
            "role": emp.designation or "—",
            "department": emp.department or "",
            "shifts": {}
        }

    for assignment in assignments:
        if assignment.employee not in staff_map:
            continue

        assignment_start = getdate(assignment.start_date)
        assignment_end = getdate(assignment.end_date or assignment.start_date)

        for day in days:
            current_date = getdate(day["date"])

            if assignment_start <= current_date <= assignment_end:
                staff_map[assignment.employee]["shifts"][day["date"]] = {
                    "shift": assignment.shift_type,
                    "time": _get_shift_time(assignment.shift_type),
                    "status": "Published"
                }

    return {
        "days": days,
        "staff": list(staff_map.values())
    }


@frappe.whitelist()
def download_shift_list_report(
    department=None,
    week_start=None,
    shift_type=None
):
    from rhohotel.rhocom_hotel.api.shift_list import (
        get_shift_calendar,
        get_shift_stats,
        _get_week_start
    )

    department = _resolve_department_filter(department)

    calendar_result = get_shift_calendar(
        department=department,
        week_start=week_start,
        shift_type=shift_type
    )

    days = calendar_result.get("days", [])
    staff = calendar_result.get("staff", [])

    week_start_date = _get_week_start(week_start)
    week_end_date = add_days(week_start_date, 6)

    stats = get_shift_stats(
        department=department,
        week_start=week_start_date,
        shift_type=shift_type
    )

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or "Hotel"
    )

    from rhohotel.rhocom_hotel.api.reports import _logo_to_data_uri

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
            parts = [company_doc.get("address_line1") or "", company_doc.get("city") or "", company_doc.get("country") or ""]
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
        "days": days,
        "staff": staff,
        "stats": stats,
        "generated_at": format_datetime(now_datetime(), "dd-MM-yyyy HH:mm:ss"),
        "filters": {
            "department": department or "All Departments",
            "shift_type": shift_type or "All Shifts",
            "week_start": formatdate(week_start_date, "dd MMM yyyy"),
            "week_end": formatdate(week_end_date, "dd MMM yyyy"),
        },
        "shift_types": [r.name for r in frappe.get_all("Shift Type", fields=["name"], order_by="name asc")],
    }

    print_format = settings.shift_print_format

    if not print_format:
        frappe.throw("Please set Shift List Print Format in Hotel Settings.")

    html_template = frappe.db.get_value("Print Format", print_format, "html")

    if not html_template:
        frappe.throw("The selected Print Format has no HTML content.")

    html = frappe.render_template(html_template, context)

    pdf = get_pdf(html, {
        "orientation": "Landscape",
        "page-size": "A4",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "8mm",
        "margin-right": "8mm",
    })

    filename = "Shift-Calendar-{0}-to-{1}.pdf".format(
        str(week_start_date),
        str(week_end_date)
    )

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"