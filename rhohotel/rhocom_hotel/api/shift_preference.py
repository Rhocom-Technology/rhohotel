import frappe
from frappe.utils import getdate, add_days, now_datetime


def _week_start(value=None):
    d = getdate(value) if value else getdate()
    return add_days(d, -d.weekday())


def _week_end(week_start):
    return add_days(week_start, 6)


def _get_employee():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        ["name", "employee_name", "company", "department"],
        as_dict=True,
    )

    if not employee:
        frappe.throw("No active Employee record is linked to this user.")

    return employee


def _has_department_shift_assignment(company, department, week_start, week_end):
    return frappe.db.exists(
        "Shift Assignment",
        {
            "company": company,
            "department": department,
            "docstatus": 1,
            "start_date": ["<=", week_end],
            "end_date": [">=", week_start],
        },
    )


def _get_existing(employee, week_start):
    return frappe.db.get_value(
        "Staff Shift Preference",
        {
            "employee": employee,
            "week_start": week_start,
        },
        "name",
    )


@frappe.whitelist()
def get_shift_types():
    rows = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")
    return [r.name for r in rows]


@frappe.whitelist()
def get_my_preference(week_start=None):
    emp = _get_employee()
    week_start = _week_start(week_start)
    week_end = _week_end(week_start)

    locked_by_roster = _has_department_shift_assignment(
        emp.company,
        emp.department,
        week_start,
        week_end,
    )

    docname = _get_existing(emp.name, week_start)

    days = []
    for i in range(7):
        d = add_days(week_start, i)
        days.append({
            "date": str(d),
            "day": d.strftime("%A"),
        })

    if not docname:
        return {
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "company": emp.company,
            "department": emp.department,
            "week_start": str(week_start),
            "week_end": str(week_end),
            "status": "Not Started",
            "locked": bool(locked_by_roster),
            "lock_reason": "Shift assignment already exists for this department/week." if locked_by_roster else "",
            "days": days,
            "preferences": [],
        }

    doc = frappe.get_doc("Staff Shift Preference", docname)

    return {
        "name": doc.name,
        "employee": doc.employee,
        "employee_name": doc.employee_name,
        "company": doc.company,
        "department": doc.department,
        "week_start": str(doc.week_start),
        "week_end": str(doc.week_end),
        "status": doc.status,
        "locked": doc.status == "Submitted" or bool(locked_by_roster),
        "lock_reason": "Preference already submitted." if doc.status == "Submitted" else (
            "Shift assignment already exists for this department/week." if locked_by_roster else ""
        ),
        "days": days,
        "preferences": [
            {
                "date": str(row.date),
                "day": row.day,
                "preferred_shift": row.preferred_shift,
                "alternative_shift": row.alternative_shift,
                "availability": row.availability,
                "note": row.note,
            }
            for row in doc.preferences
        ],
    }


def _save_or_submit(week_start=None, preferences=None, submit=False):
    emp = _get_employee()
    week_start = _week_start(week_start)
    week_end = _week_end(week_start)

    if _has_department_shift_assignment(emp.company, emp.department, week_start, week_end):
        frappe.throw("Cannot submit preference. Shift assignment already exists for this department/week.")

    docname = _get_existing(emp.name, week_start)

    if docname:
        doc = frappe.get_doc("Staff Shift Preference", docname)

        if doc.status == "Submitted":
            frappe.throw("Preference already submitted. It cannot be changed.")
    else:
        doc = frappe.new_doc("Staff Shift Preference")
        doc.employee = emp.name
        doc.employee_name = emp.employee_name
        doc.user = frappe.session.user
        doc.company = emp.company
        doc.department = emp.department
        doc.week_start = week_start
        doc.week_end = week_end
        doc.status = "Draft"

    doc.preferences = []

    for row in preferences or []:
        doc.append("preferences", {
            "date": row.get("date"),
            "day": row.get("day"),
            "preferred_shift": row.get("preferred_shift"),
            "alternative_shift": row.get("alternative_shift"),
            "availability": row.get("availability") or "Available",
            "note": row.get("note"),
        })

    if submit:
        doc.status = "Submitted"
        doc.submitted_on = now_datetime()
    else:
        doc.status = "Draft"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name": doc.name,
        "status": doc.status,
    }


@frappe.whitelist()
def save_draft(week_start=None, preferences=None):
    if isinstance(preferences, str):
        preferences = frappe.parse_json(preferences)

    return _save_or_submit(
        week_start=week_start,
        preferences=preferences,
        submit=False,
    )


@frappe.whitelist()
def submit_preference(week_start=None, preferences=None):
    if isinstance(preferences, str):
        preferences = frappe.parse_json(preferences)

    return _save_or_submit(
        week_start=week_start,
        preferences=preferences,
        submit=True,
    )