# # Copyright (c) 2025, Rhocom Technology Ltd and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class Hall(Document):
# 	pass

# 	def validate(self):
# 		# Create Item for the Hall if not exists
# 		if not frappe.db.exists("Item", self.hall_name):
# 			item = frappe.get_doc({
# 				"doctype": "Item",
# 				"item_name": self.hall_name,
# 				"item_code": self.hall_name,
# 				"item_group": "Hall",
# 				"stock_uom": "Nos"
# 			})
# 			item.insert(ignore_permissions=True)
# 			self.item_name = item.name

# 	def onsave(self):
# 		# Create Item for the Hall if not exists
# 		if not frappe.db.exists("Item", self.item_name):
# 			item = frappe.get_doc({
# 				"doctype": "Item",
# 				"item_name": self.item_name,
# 				"item_code": self.item_name,
# 				"item_group": "Hall",
# 				"stock_uom": "Nos"
# 			})
# 			item.insert(ignore_permissions=True)
# 			self.item_name = item.name
# 			self.save(ignore_permissions=True)



# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Hall(Document):
	def validate(self):
		self.create_item_if_not_exists()

	def create_item_if_not_exists(self):
		if not self.hall_name:
			return

		if not frappe.db.exists("Item Group", "Hall"):
			frappe.throw("Item Group 'Hall' does not exist. Please create it first.")

		item_code = self.item_name or self.hall_name

		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_name": self.hall_name,
				"item_code": item_code,
				"item_group": "Hall",
				"stock_uom": "Nos",
				"is_stock_item": 0
			})
			item.insert(ignore_permissions=True)
			self.item_name = item.name