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
        "shiftTypeCounts": []
    }


@frappe.whitelist()
def get_departments():
    company = _get_default_company()
    if not company:
        return []

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


@frappe.whitelist()
def get_shift_stats(department=None, week_start=None, shift_type=None):
    company = _get_default_company()

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

    published_rows = frappe.db.sql("""
        select
            sa.shift_type,
            count(*) as total
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
        group by sa.shift_type
        order by sa.shift_type asc
    """.format(
        department_condition=department_condition,
        shift_condition=shift_condition
    ), filters, as_dict=True)

    published_week_row = frappe.db.sql("""
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

    unpublished_row = frappe.db.sql("""
        select count(*) as total
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

    staff_scheduled = 0
    shift_type_counts = []

    for row in published_rows:
        count = row.total or 0
        staff_scheduled += count

        shift_type_counts.append({
            "shift_type": row.shift_type or "Unknown",
            "count": count
        })

    return {
        "publishedThisWeek": published_week_row[0].total if published_week_row else 0,
        "staffScheduled": staff_scheduled,
        "unpublished": unpublished_row[0].total if unpublished_row else 0,
        "shiftTypeCounts": shift_type_counts
    }


@frappe.whitelist()
def get_shift_calendar(department=None, week_start=None, shift_type=None):
    company = _get_default_company()

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

    context = {
        "company": company,
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
    }

    settings = frappe.get_single("Hotel Settings")
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
    frappe.local.response.type = "download"