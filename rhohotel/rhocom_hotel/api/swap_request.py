import frappe
from frappe import _
from frappe.utils import cstr, getdate, now_datetime

from rhohotel.rhocom_hotel.api.weekly_shift_generator import (
    _get_overlapping_assignment,
    _apply_draft_assignments,
    _format_shift_time,
    _get_default_company,
)

MANAGER_ROLES = ("System Manager", "Hotel Manager", "Front Desk Manager", "Sales Manager", "Housekeeping Manager", "Maintenance Manager", "Facility Manager")
SWAP_REQUEST_DOCTYPE = "Shift Swap Request"


def _require_logged_in():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in."), frappe.PermissionError)


def _is_manager():
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles(frappe.session.user))
    return bool(roles.intersection(MANAGER_ROLES))


def _is_super_manager():
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles(frappe.session.user))
    return bool(roles.intersection({"System Manager", "Hotel Manager"}))


def _require_manager():
    _require_logged_in()

    if not _is_manager():
        frappe.throw(
            _("Only Hotel Manager or Front Desk Manager can manage shift swap requests."),
            frappe.PermissionError,
        )


def _get_logged_in_employee():
    _require_logged_in()

    employee = frappe.db.get_value(
        "Employee",
        {
            "user_id": frappe.session.user,
            "status": "Active",
        },
        ["name", "employee_name", "designation", "department", "company"],
        as_dict=True,
    )

    if not employee:
        frappe.throw(_("No active Employee record is linked to your user account."))

    if not employee.department:
        frappe.throw(_("Your Employee record has no department."))

    return employee


def _get_employee(employee):
    employee = cstr(employee).strip()

    if not employee:
        frappe.throw(_("Employee is required."))

    row = frappe.db.get_value(
        "Employee",
        employee,
        ["name", "employee_name", "designation", "department", "company", "status"],
        as_dict=True,
    )

    if not row:
        frappe.throw(_("Employee {0} was not found.").format(employee))

    return row


def _cell_from_assignment(row):
    if not row:
        return {
            "value": "OFF",
            "status": "Off",
            "shift_type": None,
        }

    if row.status == "Inactive":
        return {
            "value": "Leave",
            "status": "Leave",
            "shift_type": row.shift_type,
        }

    return {
        "value": row.shift_type,
        "status": "Active",
        "shift_type": row.shift_type,
    }


def _get_shift_time(shift_type):
    if not shift_type:
        return ""

    st = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["start_time", "end_time"],
        as_dict=True,
    )

    if not st:
        return ""

    return _format_shift_time(st.start_time, st.end_time)


def _get_employee_shift(employee, date):
    employee_doc = _get_employee(employee)
    date = getdate(date)

    existing = _get_overlapping_assignment(employee, date)
    cell = _cell_from_assignment(existing)

    return {
        "employee": employee_doc.name,
        "employee_name": employee_doc.employee_name,
        "designation": employee_doc.designation,
        "department": employee_doc.department,
        "date": cstr(date),
        "value": cell["value"],
        "status": cell["status"],
        "shift_type": cell["shift_type"],
        "time": _get_shift_time(cell["shift_type"]),
        "locked": bool(existing and existing.docstatus == 1),
    }


def _build_checks(department, date, requesting_employee, target_employee):
    department = cstr(department or "").strip()
    date = getdate(date)

    requesting = _get_employee(requesting_employee)
    target = _get_employee(target_employee)

    errors = []
    checks = []

    if date < getdate():
        errors.append(_("You cannot request a shift swap for a past date."))
        checks.append({
            "level": "warning",
            "title": "Past Date Selected",
            "detail": "Choose today or a future date for the swap.",
        })

    if requesting.name == target.name:
        errors.append(_("Requesting Employee and Target Employee cannot be the same."))
        checks.append({
            "level": "warning",
            "title": "Same Employee Selected",
            "detail": "Select a different target employee.",
        })

    if requesting.status != "Active":
        errors.append(_("{0} is not active.").format(requesting.employee_name))
        checks.append({
            "level": "warning",
            "title": "Requester Not Active",
            "detail": "{0} is not an active employee.".format(requesting.employee_name),
        })

    if target.status != "Active":
        errors.append(_("{0} is not active.").format(target.employee_name))
        checks.append({
            "level": "warning",
            "title": "Target Not Active",
            "detail": "{0} is not an active employee.".format(target.employee_name),
        })

    if requesting.department != department:
        errors.append(_("Requesting Employee must belong to the selected department."))
        checks.append({
            "level": "warning",
            "title": "Requester Department Conflict",
            "detail": "{0} belongs to {1}.".format(
                requesting.employee_name,
                requesting.department,
            ),
        })

    if target.department != department:
        errors.append(_("Target Employee must belong to the same department."))
        checks.append({
            "level": "warning",
            "title": "Target Department Conflict",
            "detail": "{0} belongs to {1}.".format(
                target.employee_name,
                target.department,
            ),
        })

    shift_a = _get_employee_shift(requesting.name, date)
    shift_b = _get_employee_shift(target.name, date)

    if shift_a.get("value") == shift_b.get("value"):
        errors.append(_("Both employees already have the same shift on this date."))
        checks.append({
            "level": "warning",
            "title": "Same Shift Conflict",
            "detail": "Both employees have {0} on {1}.".format(
                shift_a.get("value"),
                cstr(date),
            ),
        })
    else:
        checks.append({
            "level": "success",
            "title": "Different Shifts Found",
            "detail": "{0} has {1}, while {2} has {3}.".format(
                requesting.employee_name,
                shift_a.get("value"),
                target.employee_name,
                shift_b.get("value"),
            ),
        })

    if shift_a.get("status") == "Leave":
        errors.append(_("{0} is on leave on this date.").format(requesting.employee_name))
        checks.append({
            "level": "warning",
            "title": "Requester On Leave",
            "detail": "{0} is on leave.".format(requesting.employee_name),
        })

    if shift_b.get("status") == "Leave":
        errors.append(_("{0} is on leave on this date.").format(target.employee_name))
        checks.append({
            "level": "warning",
            "title": "Target On Leave",
            "detail": "{0} is on leave.".format(target.employee_name),
        })

    if not errors:
        checks.append({
            "level": "success",
            "title": "Both Staff Available",
            "detail": "No leave or blocking conflict found.",
        })

        checks.append({
            "level": "success",
            "title": "No Overlap Conflict",
            "detail": "Swap can be safely applied for the selected date.",
        })

    return {
        "ok": not bool(errors),
        "errors": errors,
        "checks": checks,
        "department": department,
        "date": cstr(date),
        "requesting_employee": shift_a,
        "target_employee": shift_b,
    }


def _serialize_request(doc):
    return {
        "name": doc.name,
        "request_id": doc.name,
        "department": doc.department,
        "date": cstr(doc.swap_date),
        "requesting_employee": doc.requesting_employee,
        "requesting_employee_name": doc.requesting_employee_name,
        "requesting_shift": doc.requesting_shift,
        "requesting_shift_time": doc.requesting_shift_time,
        "target_employee": doc.target_employee,
        "target_employee_name": doc.target_employee_name,
        "target_shift": doc.target_shift,
        "target_shift_time": doc.target_shift_time,
        "request_reason": doc.request_reason,
        "manager_note": doc.manager_note,
        "status": doc.status,
        "check_status": doc.check_status,
        "submitted_by": doc.submitted_by,
        "submitted_on": cstr(doc.submitted_on),
        "approved_by": doc.approved_by,
        "approved_on": cstr(doc.approved_on) if doc.approved_on else "",
        "rejected_by": doc.rejected_by,
        "rejected_on": cstr(doc.rejected_on) if doc.rejected_on else "",
    }


@frappe.whitelist()
def get_my_swap_context():
    _require_logged_in()

    is_manager = _is_manager()

    employee = frappe.db.get_value(
        "Employee",
        {
            "user_id": frappe.session.user,
            "status": "Active",
        },
        ["name", "employee_name", "designation", "department", "company"],
        as_dict=True,
    )

    if not employee:
        if is_manager:
            return {
                "employee": "",
                "employee_name": frappe.session.user,
                "designation": "",
                "department": "",
                "company": "",
                "is_manager": True,
                "has_employee": False,
            }

        frappe.throw(_("No active Employee record is linked to your user account."))

    return {
        "employee": employee.name,
        "employee_name": employee.employee_name,
        "designation": employee.designation,
        "department": employee.department,
        "company": employee.company,
        "is_manager": is_manager,
        "has_employee": True,
    }


@frappe.whitelist()
def get_department_employees(department=None, exclude_employee=None, search=None):
    _require_logged_in()

    current_employee = _get_logged_in_employee()

    department = cstr(department or current_employee.department).strip()
    exclude_employee = cstr(exclude_employee or current_employee.name).strip()
    search = cstr(search or "").strip()

    conditions = [
        "status = 'Active'",
        "department = %(department)s",
    ]

    values = {
        "department": department,
    }

    if exclude_employee:
        conditions.append("name != %(exclude_employee)s")
        values["exclude_employee"] = exclude_employee

    if search:
        conditions.append(
            "(employee_name LIKE %(search)s OR name LIKE %(search)s OR designation LIKE %(search)s)"
        )
        values["search"] = "%{0}%".format(search)

    return frappe.db.sql(
        """
        SELECT
            name AS employee,
            employee_name,
            designation,
            department
        FROM `tabEmployee`
        WHERE {conditions}
        ORDER BY employee_name ASC
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )


@frappe.whitelist()
def get_employee_shift(employee=None, date=None):
    _require_logged_in()

    if not employee:
        employee = _get_logged_in_employee().name

    return _get_employee_shift(employee, date)


@frappe.whitelist()
def check_swap_availability(date, target_employee):
    current_employee = _get_logged_in_employee()

    return _build_checks(
        department=current_employee.department,
        date=date,
        requesting_employee=current_employee.name,
        target_employee=target_employee,
    )


@frappe.whitelist()
def create_swap_request(date, target_employee, request_reason):
    current_employee = _get_logged_in_employee()

    department = current_employee.department
    requesting_employee = current_employee.name
    target_employee = cstr(target_employee or "").strip()
    date = getdate(date)
    request_reason = cstr(request_reason or "").strip()

    if not target_employee:
        frappe.throw(_("Target Employee is required."))

    if not request_reason:
        frappe.throw(_("Request Reason is required."))

    check = _build_checks(
        department=department,
        date=date,
        requesting_employee=requesting_employee,
        target_employee=target_employee,
    )

    if not check.get("ok"):
        frappe.throw(
            _("Swap request cannot be created: {0}").format(
                "; ".join(check.get("errors") or [])
            )
        )

    requesting_shift = check.get("requesting_employee")
    target_shift = check.get("target_employee")

    doc = frappe.new_doc(SWAP_REQUEST_DOCTYPE)
    doc.department = department
    doc.swap_date = date

    doc.requesting_employee = requesting_shift.get("employee")
    doc.requesting_employee_name = requesting_shift.get("employee_name")
    doc.requesting_shift = requesting_shift.get("value")
    doc.requesting_shift_time = requesting_shift.get("time")

    doc.target_employee = target_shift.get("employee")
    doc.target_employee_name = target_shift.get("employee_name")
    doc.target_shift = target_shift.get("value")
    doc.target_shift_time = target_shift.get("time")

    doc.request_reason = request_reason
    doc.status = "Pending"
    doc.check_status = "Clear"
    doc.submitted_by = frappe.session.user
    doc.submitted_on = now_datetime()

    doc.insert(ignore_permissions=True)

    return {
        "ok": True,
        "message": _("Swap request created."),
        "request": _serialize_request(doc),
        "checks": check.get("checks"),
    }



@frappe.whitelist()
def get_swap_requests(department=None, date=None, status=None, search=None, limit_start=0, limit_page_length=25):
    _require_logged_in()

    conditions = []
    values = {}

    # Non-managers are ALWAYS restricted to requests where they are either
    # the requesting or target employee, regardless of what department/date/
    # status/search filters the client sends. This is enforced server-side
    # so it can't be bypassed by calling the API directly with different
    # parameters.
    if not _is_manager():
        current_employee = _get_logged_in_employee()
        conditions.append(
            """(
                requesting_employee = %(current_employee)s
                OR target_employee = %(current_employee)s
            )"""
        )
        values["current_employee"] = current_employee.name

        # Department/status/search filters are only meaningful for managers
        # browsing everyone's requests -- a non-manager's own requests are
        # already a small, fixed set, so don't let stray filter values (e.g.
        # a stale department selection) accidentally hide their own data.
        department = None
        status = None
        search = None
        date = None
    else:
        department = cstr(department or "").strip()
        status = cstr(status or "").strip()
        search = cstr(search or "").strip()

        # Restrict department managers to their own department unless they are
        # System Manager or Hotel Manager (who can see all departments).
        if not _is_super_manager():
            mgr_employee = _get_logged_in_employee()
            if mgr_employee and mgr_employee.department:
                department = mgr_employee.department

    if department and department != "All Departments":
        conditions.append("department = %(department)s")
        values["department"] = department

    if date:
        conditions.append("swap_date = %(swap_date)s")
        values["swap_date"] = getdate(date)

    if status and status != "All Statuses":
        conditions.append("status = %(status)s")
        values["status"] = status

    if search:
        conditions.append(
            """(
                name LIKE %(search)s
                OR requesting_employee_name LIKE %(search)s
                OR target_employee_name LIKE %(search)s
                OR requesting_employee LIKE %(search)s
                OR target_employee LIKE %(search)s
            )"""
        )
        values["search"] = "%{0}%".format(search)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    limit_start = int(limit_start or 0)
    limit_page_length = int(limit_page_length or 25)

    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabShift Swap Request`
        {where}
        ORDER BY creation DESC
        LIMIT %(limit_start)s, %(limit_page_length)s
        """.format(where=where),
        dict(values, limit_start=limit_start, limit_page_length=limit_page_length),
        as_dict=True,
    )

    total = frappe.db.sql(
        """
        SELECT COUNT(*) AS total
        FROM `tabShift Swap Request`
        {where}
        """.format(where=where),
        values,
        as_dict=True,
    )[0].total

    return {
        "rows": [_serialize_request(frappe.get_doc(SWAP_REQUEST_DOCTYPE, row.name)) for row in rows],
        "total": total,
        "limit_start": limit_start,
        "limit_page_length": limit_page_length,
    }
    
    
@frappe.whitelist()
def get_swap_request(name):
    _require_logged_in()

    doc = frappe.get_doc(SWAP_REQUEST_DOCTYPE, name)

    if not _is_manager():
        current_employee = _get_logged_in_employee()

        if doc.requesting_employee != current_employee.name and doc.target_employee != current_employee.name:
            frappe.throw(_("You can only view swap requests involving you."), frappe.PermissionError)

    data = _serialize_request(doc)

    check = _build_checks(
        department=doc.department,
        date=doc.swap_date,
        requesting_employee=doc.requesting_employee,
        target_employee=doc.target_employee,
    )

    data["checks"] = check.get("checks")
    data["availability_check"] = check

    return data   


@frappe.whitelist()
def approve_swap_request(name, manager_note=None):
    _require_manager()

    doc = frappe.get_doc(SWAP_REQUEST_DOCTYPE, name)

    # Department managers can only approve requests in their own department.
    # System/Hotel managers can approve across all departments.
    if not _is_super_manager():
        mgr_employee = _get_logged_in_employee()
        if (mgr_employee.department or "") != (doc.department or ""):
            frappe.throw(
                _("You can only approve swap requests in your department ({0}).").format(
                    mgr_employee.department
                ),
                frappe.PermissionError,
            )

    # Idempotent approve: if already approved, return success payload instead
    # of raising an error when users click approve again.
    if doc.status == "Approved":
        return {
            "ok": True,
            "message": _("Swap request is already approved."),
            "request": _serialize_request(doc),
        }

    if doc.status != "Pending":
        frappe.throw(_("Only pending swap requests can be approved."))

    check = _build_checks(
        department=doc.department,
        date=doc.swap_date,
        requesting_employee=doc.requesting_employee,
        target_employee=doc.target_employee,
    )

    if not check.get("ok"):
        doc.check_status = "Conflict"
        doc.save(ignore_permissions=True)

        frappe.throw(
            _("Swap cannot be approved: {0}").format(
                "; ".join(check.get("errors") or [])
            )
        )

    requesting_shift = check.get("requesting_employee")
    target_shift = check.get("target_employee")

    assignments = {
        doc.requesting_employee: {
            cstr(getdate(doc.swap_date)): target_shift.get("value"),
        },
        doc.target_employee: {
            cstr(getdate(doc.swap_date)): requesting_shift.get("value"),
        },
    }

    result = _apply_draft_assignments(
        department=None,
        week_start=getdate(doc.swap_date),
        assignments=assignments,
        publish=True,
        allowed_dates={cstr(getdate(doc.swap_date))},
    )

    doc.status = "Approved"
    doc.check_status = "Clear"
    doc.manager_note = cstr(manager_note or "").strip()
    doc.approved_by = frappe.session.user
    doc.approved_on = now_datetime()
    doc.save(ignore_permissions=True)

    return {
        "ok": True,
        "message": _("Swap request approved and applied."),
        "warnings": result.get("warnings", []),
        "request": _serialize_request(doc),
        "before": {
            "requesting_employee": requesting_shift,
            "target_employee": target_shift,
        },
        "after": {
            "requesting_employee": _get_employee_shift(doc.requesting_employee, doc.swap_date),
            "target_employee": _get_employee_shift(doc.target_employee, doc.swap_date),
        },
    }


@frappe.whitelist()
def reject_swap_request(name, manager_note=None):
    _require_manager()

    doc = frappe.get_doc(SWAP_REQUEST_DOCTYPE, name)

    if not _is_super_manager():
        mgr_employee = _get_logged_in_employee()
        if (mgr_employee.department or "") != (doc.department or ""):
            frappe.throw(
                _("You can only reject swap requests in your department ({0}).").format(
                    mgr_employee.department
                ),
                frappe.PermissionError,
            )

    if doc.status == "Rejected":
        return {
            "ok": True,
            "message": _("Swap request is already rejected."),
            "request": _serialize_request(doc),
        }

    if doc.status != "Pending":
        frappe.throw(_("Only pending swap requests can be rejected."))

    doc.status = "Rejected"
    doc.manager_note = cstr(manager_note or "").strip()
    doc.rejected_by = frappe.session.user
    doc.rejected_on = now_datetime()
    doc.save(ignore_permissions=True)

    return {
        "ok": True,
        "message": _("Swap request rejected."),
        "request": _serialize_request(doc),
    }


@frappe.whitelist()
def get_swap_request_stats(department=None, date=None):
    _require_manager()

    conditions = []
    values = {}

    department = cstr(department or "").strip()

    if not _is_super_manager():
        mgr_employee = _get_logged_in_employee()
        department = mgr_employee.department or ""

    if department and department != "All Departments":
        conditions.append("department = %(department)s")
        values["department"] = department

    if date:
        conditions.append("swap_date = %(swap_date)s")
        values["swap_date"] = getdate(date)

    base = ""
    if conditions:
        base = " AND " + " AND ".join(conditions)

    def count_status(status):
        return frappe.db.sql(
            """
            SELECT COUNT(*) AS total
            FROM `tabShift Swap Request`
            WHERE status = %(status)s {base}
            """.format(base=base),
            dict(values, status=status),
            as_dict=True,
        )[0].total

    conflict_alerts = frappe.db.sql(
        """
        SELECT COUNT(*) AS total
        FROM `tabShift Swap Request`
        WHERE check_status = 'Conflict' {base}
        """.format(base=base),
        values,
        as_dict=True,
    )[0].total

    return {
        "pendingReview": count_status("Pending"),
        "approvedThisWeek": count_status("Approved"),
        "conflictAlerts": conflict_alerts,
        "rejectedCancelled": count_status("Rejected") + count_status("Cancelled"),
    }
    
    
@frappe.whitelist()
def get_departments():
    _require_manager()

    if not _is_super_manager():
        mgr_employee = _get_logged_in_employee()
        return [mgr_employee.department] if mgr_employee.department else []

    default_company = _get_default_company()

    rows = frappe.db.sql(
        """
        SELECT DISTINCT department
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND department IS NOT NULL
          AND department != ''
          AND (%(company)s = '' OR company = %(company)s)
        ORDER BY department ASC
        """,
        {"company": default_company or ""},
        as_dict=True,
    )

    return [row.department for row in rows]