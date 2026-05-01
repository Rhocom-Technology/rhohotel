import frappe
from frappe.model.document import Document


class MaintenanceTechnician(Document):

    def validate(self):
        self._validate_linkage()
        self._validate_contact()

    def before_save(self):
        # Auto-fill name from linked employee/supplier if still blank
        if self.technician_type == "In-House" and self.employee:
            if not self.technician_name:
                self.technician_name = frappe.db.get_value(
                    "Employee", self.employee, "employee_name"
                ) or self.technician_name

        elif self.technician_type == "Outsourced" and self.supplier:
            if not self.technician_name:
                self.technician_name = frappe.db.get_value(
                    "Supplier", self.supplier, "supplier_name"
                ) or self.technician_name

    def on_update(self):
        # Keep availability in sync if linked employee is terminated
        if self.technician_type == "In-House" and self.employee:
            emp_status = frappe.db.get_value("Employee", self.employee, "status")
            if emp_status and emp_status != "Active" and self.availability == "Available":
                frappe.msgprint(
                    f"Note: Linked employee {self.employee} is no longer active. "
                    "Consider updating availability.",
                    indicator="yellow",
                    title="Employee Status Warning"
                )

    # ─── Private helpers ────────────────────────────────────────────────────────

    def _validate_linkage(self):
        """
        In-House technicians must not have a supplier link.
        Outsourced technicians must not have an employee link.
        """
        if self.technician_type == "In-House":
            if self.supplier:
                frappe.throw(
                    "In-House technicians cannot be linked to a Supplier. "
                    "Clear the Supplier field or switch to Outsourced.",
                    title="Invalid Linkage"
                )
            if self.employee:
                # Verify the employee exists and is active
                emp = frappe.db.get_value(
                    "Employee", self.employee, ["employee_name", "status"], as_dict=1
                )
                if not emp:
                    frappe.throw(
                        f"Employee '{self.employee}' does not exist.",
                        title="Invalid Employee"
                    )
                if emp.status != "Active":
                    frappe.msgprint(
                        f"Employee '{emp.employee_name}' has status '{emp.status}'. "
                        "Linking an inactive employee is allowed but may cause issues.",
                        indicator="yellow",
                        title="Inactive Employee"
                    )

        elif self.technician_type == "Outsourced":
            if self.employee:
                frappe.throw(
                    "Outsourced technicians cannot be linked to an Employee. "
                    "Clear the Employee field or switch to In-House.",
                    title="Invalid Linkage"
                )
            if self.supplier:
                if not frappe.db.exists("Supplier", self.supplier):
                    frappe.throw(
                        f"Supplier '{self.supplier}' does not exist.",
                        title="Invalid Supplier"
                    )

    def _validate_contact(self):
        """Basic email format check"""
        if self.email and "@" not in self.email:
            frappe.throw(
                f"'{self.email}' does not look like a valid email address.",
                title="Invalid Email"
            )