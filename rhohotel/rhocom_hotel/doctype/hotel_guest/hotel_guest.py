
# Copyright (c) 2025, Rhocom and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from rhohotel.rhocom_hotel.utils.phone import validate_phone_number

class HotelGuest(Document):
    def validate(self):
        self.phone_number = validate_phone_number(
            self.phone_number,
            label="Phone Number",
            required=True,
        )
        self.contact_number = validate_phone_number(
            self.contact_number,
            label="Contact Person Number",
        )

    def before_save(self):
        if not self.customer:
            self.create_customer()

    def create_customer(self):
        if not frappe.db.exists("Customer", {"custom_guest_id": self.name}):
            customer = frappe.new_doc("Customer")
            customer.customer_name = self.hotel_guest_name
            # Set other customer fields as needed
            customer.custom_guest_id = self.name
            customer.insert()
            self.customer = customer.name
