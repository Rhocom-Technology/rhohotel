import frappe
from frappe.utils import now_datetime
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import AssetMaintenance


class CustomAssetMaintenance(AssetMaintenance):

    def validate(self):
        self._set_reported_by_default()
        self._check_approval_permission()
        # Call parent validate but skip the assign_to check
        # by patching the tasks temporarily
        self._validate_dates_only()

    def before_submit(self):
        if self.get("rh_approved") != "Approved":
            frappe.throw(
                "This Asset Maintenance must be approved by a Hotel Manager "
                "before it can be submitted. Current approval status: "
                f"{self.get('rh_approved') or 'Pending'}",
                title="Approval Required"
            )
        if not self.get("rh_reported_by"):
            frappe.throw(
                "Please fill in who reported this before submitting.",
                title="Reported By Required"
            )
        if not self.get("rh_assigned_technician"):
            frappe.throw(
                "Please assign a technician before submitting.",
                title="Technician Required"
            )

    def on_update(self):
        """Stamp approval details. Auto-cancel if rejected."""
        if self.get("rh_approved") == "Approved" and not self.get("rh_approved_on"):
            self.db_set("rh_approved_by", frappe.session.user)
            self.db_set("rh_approved_on", now_datetime())
        elif self.get("rh_approved") == "Rejected":
            self._handle_rejection()

        # Skip ERPNext's on_update entirely — it calls assign_tasks()
        # which requires task.assign_to. We use rh_assigned_technician
        # instead, so the parent logic is not needed.

    # ── Private helpers ────────────────────────────────────────────────────────

    def _validate_dates_only(self):
        """
        Run only the date validation from the parent class,
        skipping the assign_to required check since we use
        rh_assigned_technician instead.
        """
        from frappe import throw
        from frappe.utils import getdate, nowdate

        for task in self.get("asset_maintenance_tasks"):
            if task.end_date and (getdate(task.start_date) >= getdate(task.end_date)):
                throw(
                    f"Start date should be less than end date for task {task.maintenance_task}"
                )
            if getdate(task.next_due_date) < getdate(nowdate()):
                task.maintenance_status = "Overdue"

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
                    "Only a Hotel Manager or System Manager can approve this.",
                    title="Permission Denied"
                )

    def _handle_rejection(self):
        """
        When rh_approved is set to Rejected:
        - Block if already submitted
        - Set docstatus to 2 (cancelled) so it does not appear in open counts
        """
        if self.docstatus == 1:
            frappe.throw(
                "Cannot reject a submitted Asset Maintenance. "
                "Cancel it through the normal ERPNext process.",
                title="Invalid Operation"
            )

        if self.docstatus == 0:
            frappe.db.set_value("Asset Maintenance", self.name, "docstatus", 2)
            frappe.db.commit()
            frappe.msgprint(
                "This Asset Maintenance has been rejected and cancelled automatically.",
                indicator="red",
                title="Maintenance Rejected"
            )