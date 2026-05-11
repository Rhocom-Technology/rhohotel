import frappe
from frappe.utils import now_datetime
from erpnext.assets.doctype.asset_repair.asset_repair import AssetRepair


class CustomAssetRepair(AssetRepair):

    def validate(self):
        super().validate()
        self._set_reported_by_default()
        self._check_approval_permission()
        

    def before_submit(self):
        # 1. Must be approved before submission
        if self.get("rh_approved") != "Approved":
            frappe.throw(
                "This Asset Repair must be approved by a Hotel Manager "
                "before it can be submitted. Current approval status: "
                f"{self.get('rh_approved') or 'Pending'}",
                title="Approval Required"
            )

        # 2. Reported By must be filled
        if not self.get("rh_reported_by"):
            frappe.throw(
                "Please fill in who reported this repair before submitting.",
                title="Reported By Required"
            )

        # 3. If repair is completed, technician must be assigned
        if self.repair_status == "Completed" and not self.get("rh_assigned_technician"):
            frappe.throw(
                "Please assign a technician before submitting a completed repair.",
                title="Technician Required"
            )

        # 4. Run ERPNext's original before_submit
        super().before_submit()

    def on_update(self):
        """Stamp who approved and when. Auto-cancel if rejected."""
        if self.get("rh_approved") == "Approved" and not self.get("rh_approved_on"):
            self.db_set("rh_approved_by", frappe.session.user)
            self.db_set("rh_approved_on", now_datetime())

        elif self.get("rh_approved") == "Rejected":
            self._handle_rejection()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _set_reported_by_default(self):
        """Default rh_reported_by to the linked employee of the logged-in user."""
        if not self.get("rh_reported_by"):
            employee = frappe.db.get_value(
                "Employee",
                {"user_id": frappe.session.user},
                "name"
            )
            if employee:
                self.rh_reported_by = employee

    def _check_approval_permission(self):
        """Only Hotel Manager or System Manager can set rh_approved to Approved."""
        if (
            self.has_value_changed("rh_approved")
            and self.get("rh_approved") == "Approved"
        ):
            allowed_roles = {"Hotel Manager", "System Manager"}
            user_roles = set(frappe.get_roles(frappe.session.user))
            if not allowed_roles.intersection(user_roles):
                frappe.throw(
                    "Only a Hotel Manager or System Manager can approve this repair.",
                    title="Permission Denied"
                )

    def _handle_rejection(self):
        """
        When rh_approved is set to Rejected:
        - Block if already submitted (docstatus=1) — must use normal cancel flow
        - Set repair_status to Cancelled
        - Cancel the draft document (docstatus=2) so it does not appear in open counts
        """
        if self.docstatus == 1:
            frappe.throw(
                "Cannot reject a submitted Asset Repair. "
                "Cancel it through the normal ERPNext process.",
                title="Invalid Operation"
            )

        if self.repair_status != "Cancelled":
            self.db_set("repair_status", "Cancelled")

        if self.docstatus == 0:
            frappe.db.set_value("Asset Repair", self.name, "docstatus", 2)
            frappe.db.commit()
            frappe.msgprint(
                "This Asset Repair has been rejected and cancelled automatically.",
                indicator="red",
                title="Repair Rejected"
            )