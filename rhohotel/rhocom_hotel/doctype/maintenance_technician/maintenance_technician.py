import frappe
from frappe.model.document import Document


class MaintenanceTechnician(Document):

    def validate(self):
        self._validate_linkage()
        self._validate_contact()

    def before_save(self):
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
        if self.technician_type == "In-House" and self.employee:
            emp_status = frappe.db.get_value("Employee", self.employee, "status")
            if emp_status and emp_status != "Active" and self.availability == "Available":
                frappe.msgprint(
                    f"Note: Linked employee {self.employee} is no longer active. "
                    "Consider updating availability.",
                    indicator="yellow",
                    title="Employee Status Warning"
                )

    def _validate_linkage(self):
        if self.technician_type == "In-House":
            if self.supplier:
                frappe.throw(
                    "In-House technicians cannot be linked to a Supplier. "
                    "Clear the Supplier field or switch to Outsourced.",
                    title="Invalid Linkage"
                )
            if self.employee:
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
                existing = frappe.db.get_value(
                    "Maintenance Technician",
                    {"employee": self.employee, "name": ["!=", self.name or ""]},
                    "name"
                )
                if existing:
                    frappe.throw(
                        f"Employee '{self.employee}' is already linked to technician {existing}. "
                        "Each employee can only be linked to one technician record.",
                        title="Duplicate Employee Link"
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
        if self.email and "@" not in self.email:
            frappe.throw(
                f"'{self.email}' does not look like a valid email address.",
                title="Invalid Email"
            )
        if self.phone:
            existing_phone = frappe.db.get_value(
                "Maintenance Technician",
                {"phone": self.phone, "name": ["!=", self.name or ""]},
                "name"
            )
            if existing_phone:
                frappe.throw(
                    f"Phone number '{self.phone}' is already used by technician {existing_phone}.",
                    title="Duplicate Phone Number"
                )
        if self.email:
            existing_email = frappe.db.get_value(
                "Maintenance Technician",
                {"email": self.email, "name": ["!=", self.name or ""]},
                "name"
            )
            if existing_email:
                frappe.throw(
                    f"Email '{self.email}' is already used by technician {existing_email}.",
                    title="Duplicate Email"
                )