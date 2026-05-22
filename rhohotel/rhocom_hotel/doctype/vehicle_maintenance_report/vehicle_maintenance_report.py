import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime
from frappe import _


ALLOWED_FWO_STATES = [
    "Pending Facility Supervisor Approval",
    "In Progress",
    "Completed"
]


class VehicleMaintenanceReport(Document):

    def before_insert(self):
        if not self.report_date:
            self.report_date = nowdate()

    def validate(self):
        self.validate_facility_work_order()
        self.fetch_work_order_details()

    def before_submit(self):
        self.validate_fleet_supervisor()
        self.validate_required_submit_fields()
        self.set_verification_details()

    def validate_facility_work_order(self):
        if not self.facility_work_order:
            frappe.throw(_("Facility Work Order is required."))

        if not frappe.db.exists("Facility Work Order", self.facility_work_order):
            frappe.throw(_("Invalid Facility Work Order."))

        work_order = frappe.get_doc("Facility Work Order", self.facility_work_order)

        if work_order.workflow_state not in ALLOWED_FWO_STATES:
            frappe.throw(
                _("Vehicle Maintenance Report can only be created for Facility Work Orders in: {0}").format(
                    ", ".join(ALLOWED_FWO_STATES)
                )
            )

    def fetch_work_order_details(self):
        work_order = frappe.get_doc("Facility Work Order", self.facility_work_order)

        self.vehicle_asset = work_order.asset

        if not self.driver and work_order.contact_person:
            self.driver = work_order.contact_person

        if not self.issue_description and work_order.description_of_problem:
            self.issue_description = work_order.description_of_problem

    def validate_fleet_supervisor(self):
        if "Fleet Supervisor" not in frappe.get_roles(frappe.session.user):
            frappe.throw(_("Only a user with Fleet Supervisor role can submit Vehicle Maintenance Report."))

    def validate_required_submit_fields(self):
        missing = []

        if not self.facility_work_order:
            missing.append("Facility Work Order")
        if not self.vehicle_asset:
            missing.append("Vehicle / Asset")
        if not self.plate_registration_number:
            missing.append("Plate / Registration Number")
        if not self.driver:
            missing.append("Driver")
        if not self.current_mileage:
            missing.append("Current Mileage")
        if not self.issue_description:
            missing.append("Issue Description")
        if not self.inspection_result:
            missing.append("Inspection Result")
        if not self.work_done:
            missing.append("Work Done")
        if not self.fleet_supervisor_confirmed:
            missing.append("Fleet Supervisor Confirmation")

        if missing:
            frappe.throw(
                _("Please fill the following before submitting:<br><br>")
                + "<br>".join(["• {0}".format(m) for m in missing])
            )

    def set_verification_details(self):
        if not self.fleet_supervisor_verified_by:
            self.fleet_supervisor_verified_by = frappe.session.user
            self.fleet_supervisor_verified_on = now_datetime()


@frappe.whitelist()
def make_vehicle_maintenance_report(facility_work_order):
    if not facility_work_order:
        frappe.throw(_("Facility Work Order is required."))

    work_order = frappe.get_doc("Facility Work Order", facility_work_order)

    if work_order.workflow_state not in ALLOWED_FWO_STATES:
        frappe.throw(
            _("Vehicle Maintenance Report can only be created for Facility Work Orders in: {0}").format(
                ", ".join(ALLOWED_FWO_STATES)
            )
        )

    existing = frappe.db.exists(
        "Vehicle Maintenance Report",
        {
            "facility_work_order": facility_work_order,
            "docstatus": ["!=", 2]
        }
    )

    if existing:
        return existing

    doc = frappe.new_doc("Vehicle Maintenance Report")
    doc.facility_work_order = work_order.name
    doc.vehicle_asset = work_order.asset
    doc.driver = work_order.contact_person
    doc.issue_description = work_order.description_of_problem

    doc.insert(ignore_permissions=False)

    return doc.name