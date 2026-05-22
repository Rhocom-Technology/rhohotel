import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime
from frappe import _


ALLOWED_FWO_STATES = [
    "Pending Facility Supervisor Approval"
]


class EquipmentRepairAuthorization(Document):

    def before_insert(self):
        if not self.authorization_date:
            self.authorization_date = nowdate()

    def validate(self):
        self.validate_facility_work_order()
        self.fetch_work_order_details()

    def on_update(self):
        if self.workflow_state == "Pending Approval":
            self.validate_required_fields()
            self.stamp_recommended()

        elif self.workflow_state == "Approved":
            self.validate_required_fields()
            self.stamp_approved()

        elif self.workflow_state == "Rejected":
            self.stamp_rejected()

    def validate_facility_work_order(self):
        if not self.facility_work_order:
            frappe.throw(_("Facility Work Order is required."))

        work_order = frappe.get_doc("Facility Work Order", self.facility_work_order)

        if work_order.workflow_state not in ALLOWED_FWO_STATES:
            frappe.throw(
                _("Equipment Repair Authorization can only be created for Facility Work Orders in: {0}").format(
                    ", ".join(ALLOWED_FWO_STATES)
                )
            )

    def fetch_work_order_details(self):
        work_order = frappe.get_doc("Facility Work Order", self.facility_work_order)

        if not self.asset and work_order.asset:
            self.asset = work_order.asset

        if self.asset:
            self.asset_id = self.asset

        if not self.repair_description and work_order.description_of_problem:
            self.repair_description = work_order.description_of_problem

        if not self.reason_for_repair and work_order.inspection_findings:
            self.reason_for_repair = work_order.inspection_findings

    def validate_required_fields(self):
        missing = []

        if not self.facility_work_order:
            missing.append("Facility Work Order")
        if not self.asset:
            missing.append("Machine / Asset")
        if not self.asset_id:
            missing.append("Asset ID")
        if not self.repair_description:
            missing.append("Repair Description")
        if not self.estimated_cost:
            missing.append("Estimated Cost")
        if not self.reason_for_repair:
            missing.append("Reason for Repair")
        if not self.approval_level_required:
            missing.append("Approval Level Required")
        if not self.authorization_date:
            missing.append("Date")

        if missing:
            frappe.throw(
                _("Please fill the following fields:<br><br>")
                + "<br>".join(["• {0}".format(m) for m in missing])
            )

    def stamp_recommended(self):
        if not self.recommended_by:
            self.db_set("recommended_by", frappe.session.user)
            self.db_set("recommended_on", now_datetime())

    def stamp_approved(self):
        if not self.approved_by:
            self.db_set("approved_by", frappe.session.user)
            self.db_set("approved_on", now_datetime())

    def stamp_rejected(self):
        if not self.rejected_by:
            self.db_set("rejected_by", frappe.session.user)
            self.db_set("rejected_on", now_datetime())


@frappe.whitelist()
def make_equipment_repair_authorization(facility_work_order):
    work_order = frappe.get_doc("Facility Work Order", facility_work_order)

    existing = frappe.db.exists(
        "Equipment Repair Authorization",
        {
            "facility_work_order": facility_work_order,
            "workflow_state": ["!=", "Rejected"]
        }
    )

    if existing:
        return existing

    doc = frappe.new_doc("Equipment Repair Authorization")
    doc.facility_work_order = work_order.name
    doc.asset = work_order.asset
    doc.asset_id = work_order.asset
    doc.repair_description = work_order.description_of_problem
    doc.reason_for_repair = work_order.inspection_findings

    doc.insert(ignore_permissions=False)

    return doc.name