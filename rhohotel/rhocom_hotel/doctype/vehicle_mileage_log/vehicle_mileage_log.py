import frappe
from frappe import _
from frappe.model.document import Document


class VehicleMileageLog(Document):

    def validate(self):
        self._set_vehicle_details()
        self._calculate_km()

    def before_submit(self):
        self._validate_submit_fields()
        self._validate_supervisor_role()

    # ─────────────────────────────────────────────────────────────
    # Load vehicle details from Hotel Vehicle
    # ─────────────────────────────────────────────────────────────

    def _set_vehicle_details(self):
        if not self.hotel_vehicle:
            return

        vehicle = frappe.get_doc("Hotel Vehicle", self.hotel_vehicle)

        self.plate_number = vehicle.plate_number
        self.asset = vehicle.asset

    # ─────────────────────────────────────────────────────────────
    # Auto-calculate KM
    # ─────────────────────────────────────────────────────────────

    def _calculate_km(self):

        if self.odometer_stop and self.odometer_start:

            if self.odometer_stop < self.odometer_start:
                frappe.throw(
                    _("Odometer Stop (<b>{0}</b>) cannot be less than "
                      "Odometer Start (<b>{1}</b>).").format(
                        self.odometer_stop,
                        self.odometer_start
                    )
                )

            self.km_this_trip = (
                self.odometer_stop - self.odometer_start
            )

        else:
            self.km_this_trip = 0

    # ─────────────────────────────────────────────────────────────
    # Submit validations
    # ─────────────────────────────────────────────────────────────

    def _validate_submit_fields(self):

        missing = []

        if not self.hotel_vehicle:
            missing.append("Vehicle")

        if not self.plate_number:
            missing.append("Plate / Registration Number")

        if not self.driver:
            missing.append("Driver")

        if not self.date:
            missing.append("Date")

        if not self.destination:
            missing.append("Destination")

        if not self.odometer_start:
            missing.append("Odometer Start")

        if not self.odometer_stop:
            missing.append("Odometer Stop")

        if not self.supervisor:
            missing.append("Supervisor Name")

        if missing:
            frappe.throw(
                _("The following fields must be filled before submitting:<br><br>")
                + "<br>".join(f"• {m}" for m in missing)
            )

    # ─────────────────────────────────────────────────────────────
    # Role validation
    # ─────────────────────────────────────────────────────────────

    def _validate_supervisor_role(self):

        allowed_roles = {
            "Fleet Supervisor",
            "Hotel Manager",
            "System Manager"
        }

        user_roles = set(
            frappe.get_roles(frappe.session.user)
        )

        if not allowed_roles.intersection(user_roles):
            frappe.throw(
                _("Only a Fleet Supervisor can submit a Vehicle Mileage Log."),
                title="Permission Denied"
            )