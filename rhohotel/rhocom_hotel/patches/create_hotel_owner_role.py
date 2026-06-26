import frappe


def execute():
	if frappe.db.exists("Role", "Hotel Owner"):
		return

	role = frappe.new_doc("Role")
	role.role_name = "Hotel Owner"
	role.desk_access = 1
	role.insert(ignore_permissions=True)
