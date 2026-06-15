import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, getdate, now_datetime

from rhohotel.rhocom_hotel.api.weekly_shift_generator import (
    _get_overlapping_assignment,
    _format_shift_time,
)


class ShiftSwapRequest(Document):
    def validate(self):
        self.validate_required_fields()
        self.validate_same_department()
        self.validate_different_employees()
        self.set_shift_details()
        self.validate_different_shifts()

    def before_insert(self):
        if not self.status:
            self.status = "Pending"

        if not self.check_status:
            self.check_status = "Review"

        if not self.submitted_by:
            self.submitted_by = frappe.session.user

        if not self.submitted_on:
            self.submitted_on = now_datetime()

    def validate_required_fields(self):
        if not self.department:
            frappe.throw(_("Department is required."))

        if not self.swap_date:
            frappe.throw(_("Swap Date is required."))

        if not self.requesting_employee:
            frappe.throw(_("Requesting Employee is required."))

        if not self.target_employee:
            frappe.throw(_("Target Employee is required."))

        if not cstr(self.request_reason).strip():
            frappe.throw(_("Request Reason is required."))

    def validate_different_employees(self):
        if self.requesting_employee == self.target_employee:
            frappe.throw(_("Requesting Employee and Target Employee cannot be the same."))

    def validate_same_department(self):
        requesting_department = frappe.db.get_value(
            "Employee",
            self.requesting_employee,
            "department",
        )

        target_department = frappe.db.get_value(
            "Employee",
            self.target_employee,
            "department",
        )

        if requesting_department != self.department:
            frappe.throw(_("Requesting Employee must be in the selected department."))

        if target_department != self.department:
            frappe.throw(_("Target Employee must be in the selected department."))

    def validate_different_shifts(self):
        if self.requesting_shift == self.target_shift:
            self.check_status = "Conflict"
            frappe.throw(_("Both employees already have the same shift on this date."))

        self.check_status = "Clear"

    def set_shift_details(self):
        requesting_shift = get_employee_shift_for_date(
            self.requesting_employee,
            self.swap_date,
        )

        target_shift = get_employee_shift_for_date(
            self.target_employee,
            self.swap_date,
        )

        self.requesting_employee_name = requesting_shift.get("employee_name")
        self.requesting_shift = requesting_shift.get("value")
        self.requesting_shift_time = requesting_shift.get("time")

        self.target_employee_name = target_shift.get("employee_name")
        self.target_shift = target_shift.get("value")
        self.target_shift_time = target_shift.get("time")


def get_employee_shift_for_date(employee, date):
    date = getdate(date)

    employee_doc = frappe.db.get_value(
        "Employee",
        employee,
        ["name", "employee_name"],
        as_dict=1,
    )

    if not employee_doc:
        frappe.throw(_("Employee {0} was not found.").format(employee))

    existing = _get_overlapping_assignment(employee, date)

    if not existing:
        return {
            "employee": employee,
            "employee_name": employee_doc.employee_name,
            "date": cstr(date),
            "value": "OFF",
            "status": "Off",
            "shift_type": None,
            "time": "",
            "locked": False,
        }

    if existing.status == "Inactive":
        value = "Leave"
        status = "Leave"
    else:
        value = existing.shift_type
        status = "Active"

    time = ""
    if existing.shift_type:
        shift_type = frappe.db.get_value(
            "Shift Type",
            existing.shift_type,
            ["start_time", "end_time"],
            as_dict=1,
        )

        if shift_type:
            time = _format_shift_time(
                shift_type.start_time,
                shift_type.end_time,
            )

    return {
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "date": cstr(date),
        "value": value,
        "status": status,
        "shift_type": existing.shift_type,
        "time": time,
        "locked": bool(existing.docstatus == 1),
    }