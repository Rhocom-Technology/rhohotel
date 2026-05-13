import frappe


def execute():
    fields = [
        {
            "fieldname": "rh_location_section",
            "fieldtype": "Section Break",
            "label": "Hotel Details",
            "insert_after": "naming_series"
        },
        {
            "fieldname": "rh_location_type",
            "fieldtype": "Select",
            "label": "Location Type",
            "options": "Room\nAsset Location",
            "default": "Room",
            "insert_after": "rh_location_section"
        },
        {
            "fieldname": "rh_hotel_room",
            "fieldtype": "Link",
            "label": "Hotel Room",
            "options": "Hotel Room",
            "insert_after": "rh_location_type",
            "depends_on": "eval:doc.rh_location_type === 'Room'",
            "mandatory_depends_on": "eval:doc.rh_location_type === 'Room'"
        },
        {
            "fieldname": "rh_asset_location",
            "fieldtype": "Link",
            "label": "Asset Location",
            "options": "Location",
            "insert_after": "rh_hotel_room",
            "depends_on": "eval:doc.rh_location_type === 'Asset Location'",
            "mandatory_depends_on": "eval:doc.rh_location_type === 'Asset Location'"
        },
        {
            "fieldname": "rh_column_break",
            "fieldtype": "Column Break",
            "insert_after": "rh_asset_location"
        },
        {
            "fieldname": "rh_reported_by",
            "fieldtype": "Link",
            "label": "Reported By",
            "options": "Employee",
            "insert_after": "rh_column_break",
            "fetch_if_empty": 1
        },
        {
            "fieldname": "rh_priority",
            "fieldtype": "Select",
            "label": "Priority",
            "options": "Low\nMedium\nHigh\nCritical",
            "default": "Medium",
            "insert_after": "rh_reported_by",
            "in_list_view": 1,
            "in_standard_filter": 1
        },
        {
            "fieldname": "rh_assigned_technician",
            "fieldtype": "Link",
            "label": "Assigned Technician",
            "options": "Maintenance Technician",
            "insert_after": "rh_reported_by",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "depends_on": "",        # explicitly clear it
            "mandatory_depends_on": "",  # explicitly clear this too
        },
        {
            "fieldname": "rh_issue_type",
            "fieldtype": "Select",
            "label": "Issue Type",
            "options": "\nPlumbing\nElectrical\nHVAC\nFurniture\nAppliance\nElectronics\nStructural\nOther",
            "insert_after": "rh_priority",
            "in_list_view": 1,
            "in_standard_filter": 1
        },
        {
            "fieldname": "rh_approval_section",
            "fieldtype": "Section Break",
            "label": "Hotel Approval",
            "insert_after": "rh_issue_type"
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
            "fieldname": "rh_approved_on",
            "fieldtype": "Datetime",
            "label": "Approved On",
            "read_only": 1,
            "insert_after": "rh_approved_by",
            "permlevel": 1
        },
    ]

    for f in fields:
        if frappe.db.exists(
            "Custom Field",
            {"dt": "Asset Repair", "fieldname": f["fieldname"]}
        ):
            cf = frappe.get_doc(
                "Custom Field",
                {"dt": "Asset Repair", "fieldname": f["fieldname"]}
            )
            cf.update(f)
            cf.save()
        else:
            cf = frappe.new_doc("Custom Field")
            cf.dt = "Asset Repair"
            cf.update(f)
            cf.insert()

    # ── Grant permlevel 1 read/write to Hotel Manager and System Manager ──
    roles_needing_level1 = ["Hotel Manager", "System Manager"]

    for role in roles_needing_level1:
        exists = frappe.db.exists(
            "DocPerm",
            {"parent": "Asset Repair", "role": role, "permlevel": 1}
        )
        if not exists:
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

    frappe.db.commit()
