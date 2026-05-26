# # your_app/patches/add_maintenance_item_permissions.py

# import frappe


# def execute():
#     add_perm("Item")
#     add_perm("Warehouse")
#     add_perm("UOM")
#     add_perm("Bin")


# def add_perm(doctype):
#     role = "Maintenance Technician"

#     exists = frappe.db.exists(
#         "Custom DocPerm",
#         {
#             "parent": doctype,
#             "role": role
#         }
#     )

#     if exists:
#         return

#     perm = frappe.get_doc({
#         "doctype": "Custom DocPerm",
#         "parent": doctype,
#         "parenttype": "DocType",
#         "parentfield": "permissions",
#         "role": role,
#         "read": 1,
#         "select": 1
#     })

#     if doctype == "Bin":
#         perm.read = 1
#         perm.select = 0

#     perm.insert(ignore_permissions=True)

#     frappe.db.commit()


import frappe


ROLES = [
    "Maintenance Technician",
    "Employee"
]


def execute():
    for role in ROLES:
        ensure_role(role)

        add_perm("Item", role)
        add_perm("Warehouse", role)
        add_perm("UOM", role)
        add_perm("Bin", role)


def ensure_role(role):
    if frappe.db.exists("Role", role):
        return

    frappe.get_doc({
        "doctype": "Role",
        "role_name": role,
        "desk_access": 1
    }).insert(ignore_permissions=True)


def add_perm(doctype, role):
    exists = frappe.db.exists(
        "Custom DocPerm",
        {
            "parent": doctype,
            "role": role
        }
    )

    if exists:
        return

    perm = frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": doctype,
        "parenttype": "DocType",
        "parentfield": "permissions",
        "role": role,
        "read": 1,
        "select": 1
    })

    if doctype == "Bin":
        perm.select = 0

    perm.insert(ignore_permissions=True)