import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime, now_datetime
from frappe import _


class VehicleRequestForm(Document):

    def before_insert(self):
        if not self.request_date:
            self.request_date = nowdate()
        if not self.request_time:
            self.request_time = nowtime()
        if not self.workflow_state:
            self.workflow_state = "Draft"

    def validate(self):
        self.validate_vehicle()
        self.fetch_vehicle_details()

    def on_update(self):
        self.stamp_workflow_actions()

    def validate_vehicle(self):
        if not self.hotel_vehicle:
            frappe.throw(_("Vehicle is required."))

        vehicle = frappe.get_doc("Hotel Vehicle", self.hotel_vehicle)

        if vehicle.status in ["Disposed", "Out of Service"]:
            frappe.throw(_("Vehicle {0} is not available. Current status: {1}").format(
                vehicle.name, vehicle.status
            ))

    def fetch_vehicle_details(self):
        if not self.hotel_vehicle:
            return

        vehicle = frappe.get_doc("Hotel Vehicle", self.hotel_vehicle)

        self.registration_number = vehicle.plate_number
        self.make_model = " ".join(filter(None, [vehicle.make, vehicle.model]))
        self.vehicle_asset = vehicle.asset

    def stamp_workflow_actions(self):
        if self.workflow_state == "Pending HOD Approval":
            if not self.submitted_by:
                self.db_set("submitted_by", frappe.session.user)
                self.db_set("submitted_on", now_datetime())

        elif self.workflow_state == "Pending HR Authorization":
            if not self.hod_approved_by:
                self.db_set("hod_approved_by", frappe.session.user)
                self.db_set("hod_approved_on", now_datetime())

        elif self.workflow_state == "Approved":
            if not self.hr_authorized_by:
                self.db_set("hr_authorized_by", frappe.session.user)
                self.db_set("hr_authorized_on", now_datetime())

        elif self.workflow_state == "Vehicle Out":
            if not self.vehicle_released_by:
                self.db_set("vehicle_released_by", frappe.session.user)
                self.db_set("vehicle_released_on", now_datetime())

        elif self.workflow_state == "Completed":
            if not self.vehicle_returned_by:
                self.db_set("vehicle_returned_by", frappe.session.user)
                self.db_set("vehicle_returned_on", now_datetime())