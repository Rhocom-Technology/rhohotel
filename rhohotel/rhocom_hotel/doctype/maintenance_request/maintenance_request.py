import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class MaintenanceRequest(Document):

    def validate(self):
        self._validate_location()
        # self._validate_no_duplicate_pending()
        self._validate_dates()
        self._check_approval_permission()

    def on_update(self):
        self._stamp_approval()
        self._handle_rejection()
        self._auto_create_task()
        self._update_room_flag()

    def before_delete(self):
        self._cancel_linked_task()

    def _validate_location(self):
        if self.location_type == "Room" and not self.room:
            frappe.throw("Please select a Room.", title="Room Required")

        if self.location_type == "Asset Location" and not self.asset_location:
            frappe.throw("Please select an Asset Location.", title="Asset Location Required")

        if self.location_type == "Other Location" and not self.location:
            frappe.throw("Please enter a Location.", title="Location Required")

        if self.location_type == "Room":
            self.asset_location = None
            self.location = None

        elif self.location_type == "Asset Location":
            self.room = None
            self.location = None

        elif self.location_type == "Other Location":
            self.room = None
            self.asset_location = None

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

        elif self.location_type == "Asset Location" and self.asset_location:
            filters["asset_location"] = self.asset_location

        elif self.location_type == "Other Location" and self.location:
            filters["location"] = self.location

        else:
            return

        existing = frappe.db.exists(filters)

        if existing:
            frappe.throw(
                "An open Maintenance Request already exists for this location and issue type ({0}).".format(existing),
                title="Duplicate Request"
            )

    def _validate_dates(self):
        if self.reported_at and get_datetime(self.reported_at) > now_datetime():
            frappe.throw("Reported At cannot be in the future.")

    def _check_approval_permission(self):
        if self.has_value_changed("approved") and self.approved in ("Approved", "Rejected"):
            allowed_roles = set(["Facilities Manager", "Facility Manager"])
            user_roles = set(frappe.get_roles(frappe.session.user))

            if not allowed_roles.intersection(user_roles):
                frappe.throw(
                    "Only a Facilities Manager can approve or reject this request.",
                    title="Permission Denied"
                )

            if self.approved == "Approved" and not self.assigned_technician:
                frappe.throw(
                    "Please assign a technician before approving this request.",
                    title="Technician Required"
                )

            if self.approved == "Approved" and not self.witness_employee:
                frappe.throw(
                    "Please select a Supervisor / Witness before approving this request.",
                    title="Witness Required"
                )

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

        task_location = self._get_task_location()

        task = frappe.new_doc("Maintenance Task")

        task.maintenance_request = self.name
        task.task_type = "Corrective"
        task.status = "Open"

        task.priority = self.priority
        task.assigned_technician = self.assigned_technician
        task.supervisor = self.witness_employee

        task.reported_by = self.reported_by
        task.requesting_department = self.requesting_department
        task.witness_department = self.witness_department
        task.issue_type = self.issue_type
        task.request_location_type = self.location_type
        task.location = task_location
        task.reported_at = self.reported_at
        task.asset = self.asset

        task.task_description = frappe.utils.strip_html_tags(
            self.issue_description or ""
        )

        task.insert(ignore_permissions=True)
        frappe.db.commit()

        self.db_set("task", task.name)
        self.db_set("status", "In Progress")

        frappe.msgprint(
            "Maintenance Task <b>{0}</b> created automatically.".format(task.name),
            indicator="green",
            alert=True
        )

    def _get_task_location(self):
        if self.location_type == "Room":
            return frappe.db.get_value("Hotel Room", self.room, "room_number") or self.room

        if self.location_type == "Asset Location":
            return self.asset_location

        return self.location or "See Maintenance Request"

    def _update_room_flag(self):
        if self.location_type != "Room" or not self.room:
            return

        active_statuses = set(["Approved", "In Progress"])
        flag = 1 if self.status in active_statuses else 0

        frappe.db.set_value("Hotel Room", self.room, "maintenance_flag", flag)
        frappe.db.commit()

    def _cancel_linked_task(self):
        if not self.task:
            return

        try:
            task = frappe.get_doc("Maintenance Task", self.task)

            if task.docstatus == 0:
                task.delete()
            elif task.docstatus == 1:
                task.cancel()

            frappe.db.set_value("Maintenance Request", self.name, "task", None)
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(str(e), "Maintenance Request — Task Cleanup")