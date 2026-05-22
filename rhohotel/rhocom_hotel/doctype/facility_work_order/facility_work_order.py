import frappe
from frappe.utils import now_datetime
from frappe import _


class FacilityWorkOrder(frappe.model.document.Document):

    def before_insert(self):
        if not self.date_reported:
            self.date_reported = now_datetime()
        if not self.workflow_state:
            self.workflow_state = "Draft"

    def validate(self):
        self._validate_location()

    def on_update(self):
        self._handle_workflow_transitions()

    # ── Location ─────────────────────────────────────────────────────────────

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

    # ── Workflow transition hooks ─────────────────────────────────────────────

    def _handle_workflow_transitions(self):
        state = self.workflow_state

        if state == "Pending Requesting Officer Approval":
            self._stamp_submitted()

        elif state == "Pending Department Head Signature":
            self._validate_request_fields()
            self._validate_supervisor_fields()
            self._stamp_completed()

        elif state == "Closed":
            self._check_linked_documents()
            self._stamp_closed()

    # ── Field validation ──────────────────────────────────────────────────────

    def _validate_request_fields(self):
        """
        Validates all request fields before sending to Department Head.
        Ensures nothing was missed before final sign-off.
        """
        missing = []

        if not self.requesting_department:
            missing.append("Requesting Department")
        if not self.contact_person:
            missing.append("Contact Person")
        if not self.date_reported:
            missing.append("Date Reported")
        if not self.category:
            missing.append("Category")
        if not self.description_of_problem or self.description_of_problem.strip() in ("", "<p><br></p>", "<p></p>"):
            missing.append("Description of Problem")

        if self.location_type == "Room" and not self.room:
            missing.append("Room")
        elif self.location_type == "Asset Location" and not self.asset_location:
            missing.append("Asset Location")
        elif self.location_type == "Other Location" and not self.location_description:
            missing.append("Location Description")

        if missing:
            frappe.throw(
                _("The following request fields must be filled before sending for signature:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )

    def _validate_supervisor_fields(self):
        """
        Validates that Facilities Supervisor has filled all required fields
        before sending to Department Head.
        """
        missing = []

        if not self.inspection_findings:
            missing.append("Inspection Findings")
        if not self.assigned_technician:
            missing.append("Technician Assigned")
        if not self.action_taken:
            missing.append("Action Taken")

        if missing:
            frappe.throw(
                _("The following fields must be filled before sending for signature:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )

    # ── Audit stamps ──────────────────────────────────────────────────────────

    def _stamp_submitted(self):
        if not self.submitted_by:
            self.db_set("submitted_by", frappe.session.user)
            self.db_set("submitted_on", now_datetime())

    def _stamp_completed(self):
        if not self.completion_date:
            self.db_set("completion_date", now_datetime())

    def _stamp_closed(self):
        if not self.closed_by:
            self.db_set("closed_by", frappe.session.user)
            self.db_set("closed_on", now_datetime())

    # ── Linked document gate ──────────────────────────────────────────────────

    def _check_linked_documents(self):
        """
        Runs on Close transition.
        Checks all linked sub-documents that exist for this Work Order.
        Only documents that actually exist are checked.
        Sub-doctypes are commented out until they are built.
        """
        sub_doctypes = [
            ("Machine Access Log", "facility_work_order"),
            ("Removed Parts Register", "facility_work_order"),
            ("Asset Repair", "rh_facility_work_order"),
            # ("Maintenance Material Request", "facility_work_order"),
            # ("Material Issue Slip", "facility_work_order"),
        ]

        errors = []
        for dt, link_field in sub_doctypes:
            if not frappe.db.exists("DocType", dt):
                continue

            incomplete = frappe.get_all(
                dt,
                filters={
                    link_field: self.name,
                    "docstatus": ["!=", 1]
                },
                fields=["name", "docstatus"]
            )

            for doc in incomplete:
                status = "Draft" if doc.docstatus == 0 else "Cancelled"
                errors.append(
                    f"{dt} <b>{doc.name}</b> is not submitted "
                    f"(current status: {status})"
                )

        if errors:
            frappe.throw(
                _("Cannot close this Work Order. "
                  "The following linked documents must be Closed first:<br><br>")
                + "<br>".join(errors)
            )