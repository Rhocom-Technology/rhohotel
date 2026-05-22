import frappe
from frappe import _


class RemovedPartsRegister(frappe.model.document.Document):

    def before_insert(self):
        self._validate_work_order_state()
        self._prefill_from_sources()

    def validate(self):
        self._validate_asset_consistency()

    def before_submit(self):
        self._validate_all_fields()
        self._validate_confirmations()

    # ── Pre-fill ──────────────────────────────────────────────────────────────

    def _prefill_from_sources(self):
        """
        Pre-fill asset and technician.
        Priority: Machine Access Log → Facility Work Order
        """
        if not self.asset:
            # Try MAL first
            if self.machine_access_log:
                mal_asset = frappe.db.get_value(
                    "Machine Access Log", self.machine_access_log, "asset"
                )
                if mal_asset:
                    self.asset = mal_asset

            # Fall back to WO
            if not self.asset and self.facility_work_order:
                wo_asset = frappe.db.get_value(
                    "Facility Work Order", self.facility_work_order, "asset"
                )
                if wo_asset:
                    self.asset = wo_asset

        # Pre-fill technician from WO
        if not self.technician and self.facility_work_order:
            wo_tech = frappe.db.get_value(
                "Facility Work Order", self.facility_work_order, "assigned_technician"
            )
            if wo_tech:
                self.technician = wo_tech

    # ── Asset consistency ─────────────────────────────────────────────────────

    def _validate_asset_consistency(self):
        """
        If a Machine Access Log is linked, its asset must match
        the asset on this register and on the Work Order.
        """
        if not self.machine_access_log:
            return

        mal_asset = frappe.db.get_value(
            "Machine Access Log", self.machine_access_log, "asset"
        )

        if mal_asset and self.asset and mal_asset != self.asset:
            frappe.throw(
                _("Asset <b>{0}</b> does not match the Machine Access Log asset <b>{1}</b>."
                  ).format(self.asset, mal_asset)
            )

        # Also check MAL belongs to same WO
        if self.facility_work_order:
            mal_wo = frappe.db.get_value(
                "Machine Access Log", self.machine_access_log, "facility_work_order"
            )
            if mal_wo and mal_wo != self.facility_work_order:
                frappe.throw(
                    _("Machine Access Log <b>{0}</b> does not belong to "
                      "Work Order <b>{1}</b>.").format(
                        self.machine_access_log, self.facility_work_order
                    )
                )

    # ── Work Order state check ────────────────────────────────────────────────

    def _validate_work_order_state(self):
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
                _("Removed Parts Register can only be created after the Facility "
                  "Work Order has been approved by the Facilities Supervisor.<br><br>"
                  "Current Work Order state: <b>{0}</b>").format(wo_state)
            )

    # ── Full field validation before submit ───────────────────────────────────

    def _validate_all_fields(self):
        missing = []

        if not self.facility_work_order:
            missing.append("Facility Work Order")
        if not self.date:
            missing.append("Date")
        if not self.part_removed:
            missing.append("Part Removed")
        if not self.condition:
            missing.append("Condition")
        if not self.reason_for_removal:
            missing.append("Reason for Removal")
        if not self.warehouse:
            missing.append("Returned to Warehouse")
        if not self.technician:
            missing.append("Technician")
        if not self.storekeeper:
            missing.append("Storekeeper")

        if missing:
            frappe.throw(
                _("The following fields must be filled before submitting:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )

    # ── Confirmation check ────────────────────────────────────────────────────

    def _validate_confirmations(self):
        missing = []
        if not self.technician_confirmed:
            missing.append("Technician Confirmation")
        if not self.storekeeper_confirmed:
            missing.append("Storekeeper Confirmation")

        if missing:
            frappe.throw(
                _("The following confirmations are required before submitting:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )