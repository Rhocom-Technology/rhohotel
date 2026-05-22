# import frappe


# def execute():
#     fields = [
#         {
#             "fieldname": "rh_location_section",
#             "fieldtype": "Section Break",
#             "label": "Hotel Details",
#             "insert_after": "naming_series"
#         },
#         {
#             "fieldname": "rh_location_type",
#             "fieldtype": "Select",
#             "label": "Location Type",
#             "options": "Room\nAsset Location",
#             "default": "Room",
#             "insert_after": "rh_location_section"
#         },
#         {
#             "fieldname": "rh_hotel_room",
#             "fieldtype": "Link",
#             "label": "Hotel Room",
#             "options": "Hotel Room",
#             "insert_after": "rh_location_type",
#             "depends_on": "eval:doc.rh_location_type === 'Room'",
#             "mandatory_depends_on": "eval:doc.rh_location_type === 'Room'"
#         },
#         {
#             "fieldname": "rh_asset_location",
#             "fieldtype": "Link",
#             "label": "Asset Location",
#             "options": "Location",
#             "insert_after": "rh_hotel_room",
#             "depends_on": "eval:doc.rh_location_type === 'Asset Location'",
#             "mandatory_depends_on": "eval:doc.rh_location_type === 'Asset Location'"
#         },
#         {
#             "fieldname": "rh_column_break",
#             "fieldtype": "Column Break",
#             "insert_after": "rh_asset_location"
#         },
#         {
#             "fieldname": "rh_reported_by",
#             "fieldtype": "Link",
#             "label": "Reported By",
#             "options": "Employee",
#             "insert_after": "rh_column_break",
#             "fetch_if_empty": 1
#         },
#         {
#             "fieldname": "rh_priority",
#             "fieldtype": "Select",
#             "label": "Priority",
#             "options": "Low\nMedium\nHigh\nCritical",
#             "default": "Medium",
#             "insert_after": "rh_reported_by",
#             "in_list_view": 1,
#             "in_standard_filter": 1
#         },
#         {
#             "fieldname": "rh_assigned_technician",
#             "fieldtype": "Link",
#             "label": "Assigned Technician",
#             "options": "Maintenance Technician",
#             "insert_after": "rh_reported_by",
#             "in_list_view": 1,
#             "in_standard_filter": 1,
#             "depends_on": "",        # explicitly clear it
#             "mandatory_depends_on": "",  # explicitly clear this too
#         },
#         {
#             "fieldname": "rh_issue_type",
#             "fieldtype": "Select",
#             "label": "Issue Type",
#             "options": "\nPlumbing\nElectrical\nHVAC\nFurniture\nAppliance\nElectronics\nStructural\nOther",
#             "insert_after": "rh_priority",
#             "in_list_view": 1,
#             "in_standard_filter": 1
#         },
#         {
#             "fieldname": "rh_approval_section",
#             "fieldtype": "Section Break",
#             "label": "Hotel Approval",
#             "insert_after": "rh_issue_type"
#         },
#         {
#             "fieldname": "rh_approved",
#             "fieldtype": "Select",
#             "label": "Approval Status",
#             "options": "Pending\nApproved\nRejected",
#             "default": "Pending",
#             "insert_after": "rh_approval_section",
#             "in_list_view": 1,
#             "in_standard_filter": 1,
#             "permlevel": 1
#         },
#         {
#             "fieldname": "rh_approved_by",
#             "fieldtype": "Link",
#             "label": "Approved By",
#             "options": "User",
#             "read_only": 1,
#             "insert_after": "rh_approved",
#             "permlevel": 1
#         },
#         {
#             "fieldname": "rh_approved_on",
#             "fieldtype": "Datetime",
#             "label": "Approved On",
#             "read_only": 1,
#             "insert_after": "rh_approved_by",
#             "permlevel": 1
#         },
#     ]

#     for f in fields:
#         if frappe.db.exists(
#             "Custom Field",
#             {"dt": "Asset Repair", "fieldname": f["fieldname"]}
#         ):
#             cf = frappe.get_doc(
#                 "Custom Field",
#                 {"dt": "Asset Repair", "fieldname": f["fieldname"]}
#             )
#             cf.update(f)
#             cf.save()
#         else:
#             cf = frappe.new_doc("Custom Field")
#             cf.dt = "Asset Repair"
#             cf.update(f)
#             cf.insert()

#     # ── Grant permlevel 1 read/write to Hotel Manager and System Manager ──
#     roles_needing_level1 = ["Hotel Manager", "System Manager"]

#     for role in roles_needing_level1:
#         exists = frappe.db.exists(
#             "DocPerm",
#             {"parent": "Asset Repair", "role": role, "permlevel": 1}
#         )
#         if not exists:
#             frappe.get_doc({
#                 "doctype": "DocPerm",
#                 "parent": "Asset Repair",
#                 "parenttype": "DocType",
#                 "parentfield": "permissions",
#                 "role": role,
#                 "permlevel": 1,
#                 "read": 1,
#                 "write": 1,
#             }).insert(ignore_permissions=True)

#     frappe.db.commit()




import frappe


def execute():
    fields = [
        # ── Facility Work Order — after company ───────────────────────────────
        {
            "fieldname": "rh_facility_work_order",
            "fieldtype": "Link",
            "label": "Facility Work Order",
            "options": "Facility Work Order",
            "insert_after": "company",
            "reqd": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
        },
        # ── Material Request — after WO ───────────────────────────────────────
        {
            "fieldname": "rh_material_request",
            "fieldtype": "Link",
            "label": "Material Request",
            "options": "Material Request",
            "insert_after": "rh_facility_work_order",
            "description": "Approved material request for this repair — items will be loaded from here",
        },
        # ── Approval section — 2 columns ──────────────────────────────────────
        {
            "fieldname": "rh_approval_section",
            "fieldtype": "Section Break",
            "label": "Hotel Approval",
            "insert_after": "rh_material_request"
        },
        {
            "fieldname": "rh_approved",
            "fieldtype": "Select",
            "label": "Approval Status",
            "options": "Pending\nApproved\nRejected",
            "default": "Pending",
            "insert_after": "rh_approval_section",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "permlevel": 1
        },
        {
            "fieldname": "rh_approved_by",
            "fieldtype": "Link",
            "label": "Approved By",
            "options": "User",
            "read_only": 1,
            "insert_after": "rh_approved",
            "permlevel": 1
        },
        {
            "fieldname": "rh_column_break_approval",
            "fieldtype": "Column Break",
            "insert_after": "rh_approved_by",
        },
        {
            "fieldname": "rh_approved_on",
            "fieldtype": "Datetime",
            "label": "Approved On",
            "read_only": 1,
            "insert_after": "rh_column_break_approval",
            "permlevel": 1
        },
        # ── Vendor / External Repair section ──────────────────────────────────
        {
            "fieldname": "rh_vendor_section",
            "fieldtype": "Section Break",
            "label": "Vendor / External Repair",
            "insert_after": "rh_approved_on",
            "collapsible": 0,
        },
        {
            "fieldname": "rh_vendor_technician",
            "fieldtype": "Link",
            "label": "Technician",
            "options": "Maintenance Technician",
            "insert_after": "rh_vendor_section",
                "in_list_view": 1,
            "in_standard_filter": 1,
        },
        {
            "fieldname": "rh_maintenance_representative",
            "fieldtype": "Link",
            "label": "Maintenance Representative",
            "options": "Employee",
            "insert_after": "rh_vendor_technician",
                "description": "Hotel staff present during the repair",
        },
        {
            "fieldname": "rh_column_break_vendor",
            "fieldtype": "Column Break",
            "insert_after": "rh_maintenance_representative",
        },
        {
            "fieldname": "rh_functional_test_result",
            "fieldtype": "Select",
            "label": "Functional Test Result",
            "options": "\nPassed\nFailed\nNot Tested",
            "insert_after": "rh_column_break_vendor",
                "in_standard_filter": 1,
        },
        {
            "fieldname": "rh_supplier_quotation",
            "fieldtype": "Link",
            "label": "Supplier Quotation",
            "options": "Supplier Quotation",
            "insert_after": "rh_functional_test_result",
            "description": "Quotation received from vendor before the repair",
        },
    ]

    for f in fields:
        if frappe.db.exists("Custom Field", {"dt": "Asset Repair", "fieldname": f["fieldname"]}):
            cf = frappe.get_doc("Custom Field", {"dt": "Asset Repair", "fieldname": f["fieldname"]})
            cf.update(f)
            cf.save(ignore_permissions=True)
            print(f"Updated: {f['fieldname']}")
        else:
            cf = frappe.new_doc("Custom Field")
            cf.dt = "Asset Repair"
            cf.update(f)
            cf.insert(ignore_permissions=True)
            print(f"Created: {f['fieldname']}")

    # ── Remove redundant fields ───────────────────────────────────────────────
    remove_fields = [
        "rh_location_section", "rh_location_type", "rh_hotel_room",
        "rh_asset_location", "rh_location_description", "rh_column_break",
        "rh_reported_by", "rh_priority", "rh_issue_type", "rh_assigned_technician",
    ]

    for fieldname in remove_fields:
        cf_name = frappe.db.get_value(
            "Custom Field", {"dt": "Asset Repair", "fieldname": fieldname}, "name"
        )
        if cf_name:
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)
            print(f"Deleted: {fieldname}")

    # ── Grant permlevel 1 to Hotel Manager and System Manager ─────────────────
    for role in ["Hotel Manager", "System Manager"]:
        if not frappe.db.exists("DocPerm", {"parent": "Asset Repair", "role": role, "permlevel": 1}):
            frappe.get_doc({
                "doctype": "DocPerm",
                "parent": "Asset Repair",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "permlevel": 1,
                "read": 1,
                "write": 1,
            }).insert(ignore_permissions=True)
            print(f"Granted permlevel 1 to {role}")

    frappe.db.commit()
    print("create_asset_repair_custom_fields complete")
