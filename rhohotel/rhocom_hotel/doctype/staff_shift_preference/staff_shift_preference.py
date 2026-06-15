import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, now_datetime


class StaffShiftPreference(Document):
    def validate(self):
        self.set_employee_details()
        self.set_week_end()
        self.validate_week()
        self.validate_submitted_lock()
        self.validate_no_shift_assignment()
        self.validate_duplicate_employee_week()

    def before_save(self):
        if self.status == "Submitted" and not self.submitted_on:
            self.submitted_on = now_datetime()

    def set_employee_details(self):
        if not self.employee:
            return

        emp = frappe.db.get_value(
            "Employee",
            self.employee,
            ["employee_name", "user_id", "company", "department"],
            as_dict=True
        )

        if not emp:
            frappe.throw("Invalid Employee.")

        self.employee_name = emp.employee_name
        self.user = emp.user_id
        self.company = emp.company
        self.department = emp.department

    def set_week_end(self):
        if self.week_start:
            self.week_end = add_days(getdate(self.week_start), 6)

    def validate_week(self):
        if not self.week_start:
            frappe.throw("Week Start is required.")

        week_start = getdate(self.week_start)

        if week_start.weekday() != 0:
            frappe.throw("Week Start must be a Monday.")

    def validate_submitted_lock(self):
        if self.is_new():
            return

        old_status = frappe.db.get_value(self.doctype, self.name, "status")

        if old_status == "Submitted":
            frappe.throw("This preference has already been submitted and cannot be changed.")

    def validate_no_shift_assignment(self):
        if not self.company or not self.department or not self.week_start or not self.week_end:
            return

        exists = frappe.db.sql("""
            select sa.name
            from `tabShift Assignment` sa
            inner join `tabEmployee` emp on emp.name = sa.employee
            where
                sa.docstatus = 1
                and emp.company = %(company)s
                and emp.department = %(department)s
                and sa.start_date <= %(week_end)s
                and ifnull(sa.end_date, sa.start_date) >= %(week_start)s
            limit 1
        """, {
            "company": self.company,
            "department": self.department,
            "week_start": self.week_start,
            "week_end": self.week_end
        }, as_dict=True)

        if exists:
            frappe.throw("Preference cannot be submitted or edited because shift assignment already exists for this department/week.")

    def validate_duplicate_employee_week(self):
        duplicate = frappe.db.exists(
            "Staff Shift Preference",
            {
                "employee": self.employee,
                "week_start": self.week_start,
                "name": ["!=", self.name]
            }
        )

        if duplicate:
            frappe.throw("A shift preference already exists for this employee and week.")