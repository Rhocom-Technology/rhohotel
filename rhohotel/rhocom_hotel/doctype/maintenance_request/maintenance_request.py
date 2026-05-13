from erpnext.buying.report import subcontracted_raw_materials_to_be_transferred
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class MaintenanceRequest(Document):

    # ── Lifecycle hooks ────────────────────────────────────────────────────────

    def validate(self):
        self._validate_location()
        self._validate_no_duplicate_pending()
        self._validate_dates()
        self._check_approval_permission()

    def on_update(self):
        self._stamp_approval()
        self._handle_rejection()
        self._auto_create_task()
        self._update_room_flag()

    def before_delete(self):
        self._cancel_linked_task()

    # ── Validate ───────────────────────────────────────────────────────────────

    def _validate_location(self):
        if self.location_type == "Room" and not self.room:
            frappe.throw(
                "Please select a Room.",
                title="Room Required"
            )
        if self.location_type == "Other Location" and not self.location:
            frappe.throw(
                "Please enter a Location (e.g. Laundry, Gym, Kitchen).",
                title="Location Required"
            )
        if self.location_type == "Room":
            self.location = None
        elif self.location_type == "Other Location":
            self.room = None

    def _validate_no_duplicate_pending(self):
        filters = {
            "doctype": "Maintenance Request",
            "issue_type": self.issue_type,
            "location_type": self.location_type,
            "status": ["in", ["Pending", "Approved", "In Progress"]],
            "name": ["!=", self.name]
        }
        if self.location_type == "Room" and self.room:
            filters["room"] = self.room
        elif self.location_type == "Other Location" and self.location:
            filters["location"] = self.location
        else:
            return

        existing = frappe.db.exists(filters)
        if existing:
            frappe.throw(
                f"An open Maintenance Request already exists for this "
                f"location and issue type ({existing}).",
                title="Duplicate Request"
            )

    def _validate_dates(self):
        if self.reported_at:
            if get_datetime(self.reported_at) > now_datetime():
                frappe.throw("Reported At cannot be in the future.")

    def _check_approval_permission(self):
        if (
            self.has_value_changed("approved")
            and self.approved in ("Approved", "Rejected")
        ):
            allowed_roles = {"Hotel Manager", "System Manager"}
            user_roles = set(frappe.get_roles(frappe.session.user))
            if not allowed_roles.intersection(user_roles):
                frappe.throw(
                    "Only a Hotel Manager or System Manager can approve "
                    "or reject this request.",
                    title="Permission Denied"
                )

            # Must assign technician before approving
            if self.approved == "Approved" and not self.assigned_technician:
                frappe.throw(
                    "Please assign a technician before approving this request.",
                    title="Technician Required"
                )

    # ── On update ──────────────────────────────────────────────────────────────

    def _stamp_approval(self):
        if self.approved == "Approved" and not self.approved_on:
            self.db_set("approved_by", frappe.session.user)
            self.db_set("approved_on", now_datetime())
            self.db_set("status", "Approved")

    def _handle_rejection(self):
        if self.approved == "Rejected":
            if self.status != "Cancelled":
                self.db_set("status", "Cancelled")
                self._cancel_linked_task()
                self._update_room_flag()
                frappe.msgprint(
                    "This Maintenance Request has been rejected and cancelled.",
                    indicator="red",
                    title="Request Rejected"
                )

    def _auto_create_task(self):
        if self.approved != "Approved":
            return
        if self.task:
            return
        if not self.assigned_technician:
            return

        existing = frappe.db.get_value(
            "Maintenance Task",
            {
                "maintenance_request": self.name,
                "docstatus": ["!=", 2]
            },
            "name"
        )
        if existing:
            self.db_set("task", existing)
            self.db_set("status", "In Progress")
            return

        if self.location_type == "Room":
            task_location = (
                frappe.db.get_value(
                    "Hotel Room", self.room, "room_number"
                ) or self.room
            )
        else:
            task_location = self.location or "See Maintenance Request"

        task = frappe.new_doc("Maintenance Task")
        task.maintenance_request = self.name
        task.task_type = "Corrective"
        task.priority = self.priority
        task.status = "Open"
        task.assigned_technician = self.assigned_technician
        task.location = task_location
        task.task_description = frappe.utils.strip_html_tags(
            self.issue_description or ""
        )
        task.insert(ignore_permissions=True)
        frappe.db.commit()

        self.db_set("task", task.name)
        self.db_set("status", "In Progress")

        frappe.msgprint(
            f"Maintenance Task <b>{task.name}</b> created automatically.",
            indicator="green",
            alert=True
        )

    def _update_room_flag(self):
        if self.location_type != "Room" or not self.room:
            return
        active_statuses = {"Approved", "In Progress"}
        flag = 1 if self.status in active_statuses else 0
        frappe.db.set_value(
            "Hotel Room", self.room, "maintenance_flag", flag
        )
        frappe.db.commit()

    # ── Before delete ──────────────────────────────────────────────────────────

    def _cancel_linked_task(self):
        if not self.task:
            return
        try:
            task = frappe.get_doc("Maintenance Task", self.task)
            if task.docstatus == 0:
                task.delete()
            elif task.docstatus == 1:
                task.cancel()
            frappe.db.set_value(
                "Maintenance Request", self.name, "task", None
            )
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(
                str(e),
                "Maintenance Request — Task Cleanup"
            )