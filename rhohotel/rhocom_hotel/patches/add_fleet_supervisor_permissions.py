# # import frappe


# # def execute():
# #     ensure_custom_role()
# #     ensure_custom_doctype_permission()
# #     ensure_standard_doctype_permissions()
# #     frappe.clear_cache()


# # def ensure_custom_role():
# #     if not frappe.db.exists("Role", "Fleet Supervisor"):
# #         role = frappe.get_doc({
# #             "doctype": "Role",
# #             "role_name": "Fleet Supervisor",
# #             "desk_access": 1
# #         })
# #         role.insert(ignore_permissions=True)


# # def add_custom_docperm(doctype, role, perms):
# #     if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
# #         docperm = frappe.get_doc("Custom DocPerm", {"parent": doctype, "role": role})
# #     else:
# #         docperm = frappe.new_doc("Custom DocPerm")
# #         docperm.parent = doctype
# #         docperm.parenttype = "DocType"
# #         docperm.parentfield = "permissions"
# #         docperm.role = role

# #     for key, value in perms.items():
# #         docperm.set(key, value)

# #     docperm.save(ignore_permissions=True)


# # def ensure_custom_doctype_permission():
# #     # Facility Work Order is your custom DocType.
# #     add_custom_docperm("Facility Work Order", "Fleet Supervisor", {
# #         "read": 1,
# #         "write": 0,
# #         "create": 0,
# #         "delete": 0,
# #         "submit": 0,
# #         "cancel": 0,
# #         "amend": 0,
# #         "report": 1,
# #         "export": 0,
# #         "print": 1,
# #         "email": 0,
# #         "share": 0,
# #         "select": 1
# #     })


# # def ensure_standard_doctype_permissions():
# #     # Needed because VMR links to these standard ERPNext/Frappe doctypes.
# #     for doctype in ["Supplier", "Asset", "Employee"]:
# #         add_custom_docperm(doctype, "Fleet Supervisor", {
# #             "read": 1,
# #             "write": 0,
# #             "create": 0,
# #             "delete": 0,
# #             "submit": 0,
# #             "cancel": 0,
# #             "amend": 0,
# #             "report": 1,
# #             "export": 0,
# #             "print": 1,
# #             "email": 0,
# #             "share": 0,
# #             "select": 1
# #         })




# import frappe


# def execute():
#     ensure_custom_roles()
#     ensure_custom_doctype_permission()
#     ensure_standard_doctype_permissions()
#     frappe.clear_cache()


# def ensure_custom_roles():
#     roles = [
#         "Fleet Supervisor",
#         "Facilities Manager"
#     ]

#     for role_name in roles:
#         if not frappe.db.exists("Role", role_name):
#             role = frappe.get_doc({
#                 "doctype": "Role",
#                 "role_name": role_name,
#                 "desk_access": 1
#             })
#             role.insert(ignore_permissions=True)


# def add_custom_docperm(doctype, role, perms):
#     if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
#         docperm = frappe.get_doc("Custom DocPerm", {"parent": doctype, "role": role})
#     else:
#         docperm = frappe.new_doc("Custom DocPerm")
#         docperm.parent = doctype
#         docperm.parenttype = "DocType"
#         docperm.parentfield = "permissions"
#         docperm.role = role

#     for key, value in perms.items():
#         docperm.set(key, value)

#     docperm.save(ignore_permissions=True)


# def read_only_perms():
#     return {
#         "read": 1,
#         "write": 0,
#         "create": 0,
#         "delete": 0,
#         "submit": 0,
#         "cancel": 0,
#         "amend": 0,
#         "report": 1,
#         "export": 0,
#         "print": 1,
#         "email": 0,
#         "share": 0,
#         "select": 1
#     }


# def facilities_manager_era_perms():
#     return {
#         "read": 1,
#         "write": 1,
#         "create": 0,
#         "delete": 0,
#         "submit": 0,
#         "cancel": 0,
#         "amend": 0,
#         "report": 1,
#         "export": 0,
#         "print": 1,
#         "email": 0,
#         "share": 0,
#         "select": 1
#     }


# # def ensure_custom_doctype_permission():
# #     add_custom_docperm("Facility Work Order", "Fleet Supervisor", read_only_perms())

# #     add_custom_docperm("Facility Work Order", "Facilities Manager", read_only_perms())

# #     add_custom_docperm(
# #         "Equipment Repair Authorization",
# #         "Facilities Manager",
# #         facilities_manager_era_perms()
# #     )


# def ensure_custom_doctype_permission():
#     add_custom_docperm("Facility Work Order", "Fleet Supervisor", read_only_perms())
#     add_custom_docperm("Facility Work Order", "Facilities Manager", read_only_perms())

#     add_custom_docperm(
#         "Equipment Repair Authorization",
#         "Facilities Manager",
#         facilities_manager_era_perms()
#     )

#     add_custom_docperm("Vehicle Maintenance Report", "Fleet Supervisor", {
#         "read": 1,
#         "write": 1,
#         "create": 1,
#         "delete": 0,
#         "submit": 1,
#         "cancel": 0,
#         "amend": 0,
#         "report": 1,
#         "export": 0,
#         "print": 1,
#         "email": 0,
#         "share": 0,
#         "select": 1
#     })

#     add_custom_docperm("Vehicle Safety Checklist", "Fleet Supervisor", {
#         "read": 1,
#         "write": 1,
#         "create": 1,
#         "delete": 0,
#         "submit": 1,
#         "cancel": 0,
#         "amend": 0,
#         "report": 1,
#         "export": 0,
#         "print": 1,
#         "email": 0,
#         "share": 0,
#         "select": 1
#     })

# # def ensure_standard_doctype_permissions():
# #     for role in ["Fleet Supervisor", "Facilities Manager"]:
# #         for doctype in ["Supplier", "Asset", "Employee"]:
# #             add_custom_docperm(doctype, role, read_only_perms())

# def ensure_standard_doctype_permissions():
#     reference_doctypes = [
#         "Supplier",
#         "Asset",
#         "Employee",
#         "Department",
#         "Location",
#         "Hotel Room"
#     ]

#     for role in ["Fleet Supervisor", "Facilities Manager"]:
#         for doctype in reference_doctypes:
#             if frappe.db.exists("DocType", doctype):
#                 add_custom_docperm(doctype, role, read_only_perms())