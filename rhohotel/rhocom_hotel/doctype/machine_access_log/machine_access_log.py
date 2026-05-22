import frappe
from frappe import _


class MachineAccessLog(frappe.model.document.Document):

    def before_insert(self):
        self._validate_work_order_state()
        self._prefill_from_work_order()

    def validate(self):
        self._validate_location()

    def before_submit(self):
        self._validate_confirmations()

    # ── Pre-fill from Work Order ──────────────────────────────────────────────

    def _prefill_from_work_order(self):
        """Auto-fill location and technician from the linked Facility Work Order."""
        if not self.facility_work_order:
            return

        wo = frappe.get_doc("Facility Work Order", self.facility_work_order)

        # Pre-fill asset if not already set
        if not self.asset and wo.asset:
            self.asset = wo.asset

        # Pre-fill technician if not already set
        if not self.technician and wo.assigned_technician:
            self.technician = wo.assigned_technician

        # Pre-fill location from WO
        if not self.location_type:
            self.location_type = wo.location_type or "Room"

        if wo.location_type == "Room" and wo.room and not self.room:
            self.room = wo.room

        elif wo.location_type == "Asset Location" and wo.asset_location and not self.asset_location:
            self.asset_location = wo.asset_location

        elif wo.location_type == "Other Location" and wo.location_description and not self.location_description:
            self.location_description = wo.location_description

    # ── Location ──────────────────────────────────────────────────────────────

    def _validate_location(self):
        if self.location_type == "Room":
            self.asset_location = None
            self.location_description = None
        elif self.location_type == "Asset Location":
            self.room = None
            self.location_description = None
        elif self.location_type == "Other Location":
            self.room = None
            self.asset_location = None

    # ── Work Order state check ────────────────────────────────────────────────

    def _validate_work_order_state(self):
        """
        Machine Access Log can only be created when the linked
        Facility Work Order is in Pending Facility Supervisor Approval or beyond.
        """
        if not self.facility_work_order:
            return

        allowed_states = [
            "Pending Facility Supervisor Approval",
            "Pending Department Head Signature",
            "Closed",
        ]

        wo_state = frappe.db.get_value(
            "Facility Work Order", self.facility_work_order, "workflow_state"
        )

        if wo_state not in allowed_states:
            frappe.throw(
                _("Machine Access Log can only be created after the Facility Work Order "
                  "has been approved by the Facilities Supervisor.<br><br>"
                  "Current Work Order state: <b>{0}</b>").format(wo_state)
            )

    # ── Submit validations ────────────────────────────────────────────────────

    def _validate_confirmations(self):
        """Both technician and witness must confirm before submission."""
        missing = []
        if not self.technician_confirmed:
            missing.append("Technician Confirmation")
        if not self.witness_confirmed:
            missing.append("Witness Confirmation")

        if missing:
            frappe.throw(
                _("The following confirmations are required before submitting:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )