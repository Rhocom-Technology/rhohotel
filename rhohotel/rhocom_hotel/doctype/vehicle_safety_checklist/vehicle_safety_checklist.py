import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime
from frappe import _


STANDARD_INSPECTION_ITEMS = [
    "Engine oil level",
    "Brake fluid level",
    "Brake pads / braking response",
    "Steering system / steering oil",
    "Coolant level",
    "Tire condition & inflation",
    "Headlights, brake lights & indicators",
    "Windshield & wipers",
    "Horn & mirrors",
    "Exterior body condition",
    "Interior condition & cleanliness",
    "Vehicle hygiene status",
    "General engine sound (idle & rev)"
]


class VehicleSafetyChecklist(Document):

    def before_insert(self):
        if not self.date_of_inspection:
            self.date_of_inspection = nowdate()

        self.populate_standard_items()

    def validate(self):
        self.validate_required_fields()
        self.set_vehicle_details()

    def before_submit(self):
        self.validate_fleet_supervisor()
        self.validate_submit_fields()
        self.set_confirmation_details()

    def populate_standard_items(self):
        if self.inspection_items:
            return

        for item in STANDARD_INSPECTION_ITEMS:
            self.append("inspection_items", {
                "inspection_item": item,
                "status": "OK"
            })

    def validate_required_fields(self):
        if not self.hotel_vehicle:
            frappe.throw(_("Vehicle is required."))

        if not self.driver:
            frappe.throw(_("Driver is required."))

    def set_vehicle_details(self):
        if not self.hotel_vehicle:
            return

        vehicle = frappe.get_doc("Hotel Vehicle", self.hotel_vehicle)

        self.registration_number = vehicle.plate_number
        self.make_model = " ".join(filter(None, [vehicle.make, vehicle.model]))
        self.vehicle_asset = vehicle.asset

    def validate_fleet_supervisor(self):
        if "Fleet Supervisor" not in frappe.get_roles(frappe.session.user):
            frappe.throw(_("Only Fleet Supervisor can submit Vehicle Safety Checklist."))

    def validate_submit_fields(self):
        missing = []

        if not self.hotel_vehicle:
            missing.append("Vehicle")
        if not self.registration_number:
            missing.append("Registration Number")
        if not self.driver:
            missing.append("Driver")
        if not self.date_of_inspection:
            missing.append("Date of Inspection")
        if not self.current_odometer_reading_km:
            missing.append("Current Odometer Reading (KM)")
        if not self.safety_declaration:
            missing.append("Safety Declaration")
        if not self.fleet_supervisor_confirmed:
            missing.append("Fleet Supervisor Confirmed")
        if not self.inspection_items:
            missing.append("Inspection Items")

        if missing:
            frappe.throw(
                _("Please fill the following before submitting:<br><br>")
                + "<br>".join(["• {0}".format(m) for m in missing])
            )

        fault_items = [
            row.inspection_item for row in self.inspection_items
            if row.status == "Fault"
        ]

        if fault_items and self.safety_declaration == "Safe":
            frappe.throw(
                _("Safety Declaration cannot be Safe because these items have faults:<br><br>")
                + "<br>".join(["• {0}".format(item) for item in fault_items])
            )

    def set_confirmation_details(self):
        if not self.fleet_supervisor_verified_by:
            self.fleet_supervisor_verified_by = frappe.session.user
            self.fleet_supervisor_verified_on = now_datetime()


@frappe.whitelist()
def reset_standard_items(name):
    doc = frappe.get_doc("Vehicle Safety Checklist", name)

    if doc.docstatus != 0:
        frappe.throw(_("Can only reset inspection items while document is Draft."))

    doc.set("inspection_items", [])

    for item in STANDARD_INSPECTION_ITEMS:
        doc.append("inspection_items", {
            "inspection_item": item,
            "status": "OK"
        })

    doc.save(ignore_permissions=False)
    frappe.db.commit()

    return doc.name