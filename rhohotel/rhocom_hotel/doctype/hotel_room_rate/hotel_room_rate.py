# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HotelRoomRate(Document):
	def validate(self):
		self._validate_unique_rate_code_room_type()

	def _validate_unique_rate_code_room_type(self):
		"""Ensure the rate_code + room_type combination is unique."""
		if frappe.db.exists(
			"Hotel Room Rate",
			{"rate_code": self.rate_code, "room_type": self.room_type, "name": ["!=", self.name]},
		):
			frappe.throw(
				frappe._("A rate with code <b>{0}</b> already exists for room type <b>{1}</b>.").format(
					self.rate_code, self.room_type
				)
			)
