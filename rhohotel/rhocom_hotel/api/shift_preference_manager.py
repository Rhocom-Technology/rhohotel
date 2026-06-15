import frappe
from frappe.utils import getdate, add_days, formatdate


def _get_default_company():
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
    )


def _get_week_start(value=None):
    d = getdate(value) if value else getdate()
    return add_days(d, -d.weekday())


def _get_week_end(week_start):
    return add_days(week_start, 6)


@frappe.whitelist()
def get_departments():
    company = _get_default_company()
    if not company:
        return []

    rows = frappe.db.sql("""
        select distinct department
        from `tabEmployee`
        where
            status = 'Active'
            and company = %(company)s
            and department is not null
            and department != ''
        order by department asc
    """, {"company": company}, as_dict=True)

    return [r.department for r in rows]


@frappe.whitelist()
def get_preference_review(department=None, week_start=None, submission_status="All Staff", search_text=None):
    company = _get_default_company()
    if not company:
        return {
            "days": [],
            "staff": [],
            "stats": {
                "departmentStaff": 0,
                "submittedPreferences": 0,
                "unavailableRequests": 0,
                "mostPreferredShift": "—",
                "mostPreferredPct": 0,
            }
        }

    week_start_date = _get_week_start(week_start)
    week_end_date = _get_week_end(week_start_date)

    filters = {
        "company": company,
        "week_start": week_start_date,
        "week_end": week_end_date,
    }

    dept_condition = ""
    search_condition = ""

    if department:
        dept_condition = " and emp.department = %(department)s"
        filters["department"] = department

    if search_text:
        search_condition = " and emp.employee_name like %(search_text)s"
        filters["search_text"] = "%{}%".format(search_text)

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
            {dept_condition}
            {search_condition}
        order by emp.employee_name asc
    """.format(
        dept_condition=dept_condition,
        search_condition=search_condition
    ), filters, as_dict=True)

    pref_rows = frappe.db.sql("""
        select
            pref.name,
            pref.employee,
            pref.status,
            pref.submitted_on
        from `tabStaff Shift Preference` pref
        inner join `tabEmployee` emp on emp.name = pref.employee
        where
            pref.company = %(company)s
            and pref.week_start = %(week_start)s
            and pref.week_end = %(week_end)s
            {dept_condition}
    """.format(
        dept_condition=dept_condition
    ), filters, as_dict=True)

    pref_by_employee = {}
    pref_names = []

    for pref in pref_rows:
        pref_by_employee[pref.employee] = pref
        pref_names.append(pref.name)

    detail_by_pref = {}

    if pref_names:
        details = frappe.db.sql("""
            select
                parent,
                date,
                day,
                preferred_shift,
                alternative_shift,
                availability,
                note
            from `tabStaff Shift Preference Detail`
            where parent in %(parents)s
            order by date asc
        """, {"parents": tuple(pref_names)}, as_dict=True)

        for row in details:
            detail_by_pref.setdefault(row.parent, []).append(row)

    days = []
    for i in range(7):
        d = add_days(week_start_date, i)
        days.append({
            "date": str(d),
            "label": d.strftime("%A"),
            "dateLabel": formatdate(d, "dd MMM"),
        })

    staff_list = []
    submitted_count = 0
    unavailable_requests = 0
    shift_counts = {}

    for emp in employees:
        pref = pref_by_employee.get(emp.employee)
        submitted = bool(pref and pref.status == "Submitted")

        if submission_status == "Submitted" and not submitted:
            continue

        if submission_status == "Pending" and submitted:
            continue

        shifts = {}
        availability = {}
        notes = {}

        if submitted:
            submitted_count += 1

            for row in detail_by_pref.get(pref.name, []):
                date_key = str(row.date)
                shift_label = row.preferred_shift or "No Preference"

                if row.availability == "Unavailable":
                    shift_label = "Unavailable"
                    unavailable_requests += 1

                shifts[date_key] = shift_label
                availability[date_key] = row.availability
                notes[date_key] = row.note or ""

                if row.preferred_shift:
                    shift_counts[row.preferred_shift] = shift_counts.get(row.preferred_shift, 0) + 1

        staff_list.append({
            "id": emp.employee,
            "name": emp.employee_name or emp.employee,
            "role": emp.designation or "—",
            "area": emp.department or "—",
            "submitted": submitted,
            "status": "Sent" if submitted else "Pending",
            "shifts": shifts,
            "availability": availability,
            "notes": notes,
        })

    most_shift = "—"
    most_pct = 0
    total_shift_votes = sum(shift_counts.values())

    if shift_counts:
        most_shift = max(shift_counts, key=shift_counts.get)
        if total_shift_votes:
            most_pct = int(round((shift_counts[most_shift] * 100.0) / total_shift_votes))

    return {
        "days": days,
        "staff": staff_list,
        "stats": {
            "departmentStaff": len(employees),
            "submittedPreferences": submitted_count,
            "unavailableRequests": unavailable_requests,
            "mostPreferredShift": most_shift,
            "mostPreferredPct": most_pct,
        }
    }