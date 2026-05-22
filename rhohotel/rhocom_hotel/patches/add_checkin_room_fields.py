# import frappe

# def execute():
#     """Add new fields to Hotel Room Check In doctype"""
#     # Add fields for enhanced check-in process
#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "vehicle_number"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room Check In",
#             "fieldname": "vehicle_number",
#             "label": "Vehicle Number",
#             "fieldtype": "Data",
#             "insert_after": "contact_number"
#         }).insert()

#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "special_requests"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room Check In",
#             "fieldname": "special_requests",
#             "label": "Special Requests",
#             "fieldtype": "Text",
#             "insert_after": "vehicle_number"
#         }).insert()

#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "key_card_number"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room Check In",
#             "fieldname": "key_card_number",
#             "label": "Key Card Number",
#             "fieldtype": "Data",
#             "insert_after": "room"
#         }).insert()

#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "room_preferences"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room Check In",
#             "fieldname": "room_preferences",
#             "label": "Room Preferences",
#             "fieldtype": "Text",
#             "insert_after": "special_requests"
#         }).insert()

#     # Add new status field to Hotel Room
#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "operational_status"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room",
#             "fieldname": "operational_status",
#             "label": "Operational Status",
#             "fieldtype": "Select",
#             "options": "Operational\nUnder Maintenance\nOut of Service",
#             "default": "Operational",
#             "insert_after": "status"
#         }).insert()

#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "housekeeping_status"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room",
#             "fieldname": "housekeeping_status",
#             "label": "Housekeeping Status",
#             "fieldtype": "Select",
#             "options": "Clean\nDirty\nInspected\nIn Progress",
#             "default": "Clean",
#             "insert_after": "operational_status"
#         }).insert()

#     if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "current_key_card"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Hotel Room",
#             "fieldname": "current_key_card",
#             "label": "Current Key Card",
#             "fieldtype": "Data",
#             "insert_after": "housekeeping_status"
#         }).insert()

#     # Create Hotel Room Maintenance Request doctype if it doesn't exist
#     if not frappe.db.exists("DocType", "Hotel Room Maintenance Request"):
#         frappe.get_doc({
#             "doctype": "DocType",
#             "name": "Hotel Room Maintenance Request",
#             "module": "Rhocom Hotel",
#             "custom": 1,
#             "fields": [
#                 {
#                     "fieldname": "room",
#                     "fieldtype": "Link",
#                     "label": "Room",
#                     "options": "Hotel Room",
#                     "reqd": 1
#                 },
#                 {
#                     "fieldname": "issue_type",
#                     "fieldtype": "Select",
#                     "label": "Issue Type",
#                     "options": "Maintenance\nCleaning\nInspection\nOther",
#                     "reqd": 1
#                 },
#                 {
#                     "fieldname": "description",
#                     "fieldtype": "Text Editor",
#                     "label": "Description",
#                     "reqd": 1
#                 },
#                 {
#                     "fieldname": "priority",
#                     "fieldtype": "Select",
#                     "label": "Priority",
#                     "options": "Low\nMedium\nHigh\nUrgent",
#                     "reqd": 1
#                 },
#                 {
#                     "fieldname": "status",
#                     "fieldtype": "Select",
#                     "label": "Status",
#                     "options": "Open\nIn Progress\nCompleted\nCancelled",
#                     "default": "Open",
#                     "reqd": 1
#                 }
#             ],
#             "permissions": [
#                 {
#                     "role": "System Manager",
#                     "read": 1,
#                     "write": 1,
#                     "create": 1,
#                     "delete": 1
#                 },
#                 {
#                     "role": "Hotel Manager",
#                     "read": 1,
#                     "write": 1,
#                     "create": 1
#                 },
#                 {
#                     "role": "Maintenance User",
#                     "read": 1,
#                     "write": 1,
#                     "create": 1
#                 }
#             ]
#         }).insert()

#     # Add Hotel Room Check In link field to Sales Invoice
#     if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_hotel_room_check_in"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Sales Invoice",
#             "fieldname": "custom_hotel_room_check_in",
#             "label": "Hotel Room Check In",
#             "fieldtype": "Link",
#             "options": "Hotel Room Check In",
#             "insert_after": "customer",
#             "in_list_view": 0,
#             "in_standard_filter": 1,
#             "search_index": 1,
#         }).insert(ignore_permissions=True)

#     # Add Hotel Room Check In link field to Payment Entry
#     if not frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "custom_hotel_room_check_in"}):
#         frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": "Payment Entry",
#             "fieldname": "custom_hotel_room_check_in",
#             "label": "Hotel Room Check In",
#             "fieldtype": "Link",
#             "options": "Hotel Room Check In",
#             "insert_after": "party",
#             "in_standard_filter": 1,
#             "search_index": 1,
#         }).insert(ignore_permissions=True)

#     frappe.db.commit()


import frappe


def execute():
    """Add new fields to Hotel Room Check In doctype"""

    def safe_insert_custom_field(dt, fieldname, label, fieldtype, insert_after, **kwargs):
        """Insert custom field only if it doesn't exist as custom or standard field."""
        # Check custom field
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            print(f"Custom field already exists: {fieldname} on {dt}")
            return
        # Check standard field
        if frappe.db.exists("DocField", {"parent": dt, "fieldname": fieldname}):
            print(f"Standard field already exists: {fieldname} on {dt}")
            return
        try:
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": dt,
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype,
                "insert_after": insert_after,
                **kwargs
            }).insert(ignore_permissions=True)
            print(f"Created: {fieldname} on {dt}")
        except Exception as e:
            print(f"Skipped {fieldname} on {dt}: {e}")

    # ── Hotel Room Check In fields ────────────────────────────────────────────
    safe_insert_custom_field("Hotel Room Check In", "vehicle_number",
        "Vehicle Number", "Data", "contact_number")

    safe_insert_custom_field("Hotel Room Check In", "special_requests",
        "Special Requests", "Text", "vehicle_number")

    safe_insert_custom_field("Hotel Room Check In", "key_card_number",
        "Key Card Number", "Data", "room")

    safe_insert_custom_field("Hotel Room Check In", "room_preferences",
        "Room Preferences", "Text", "special_requests")

    # ── Hotel Room fields ─────────────────────────────────────────────────────
    safe_insert_custom_field("Hotel Room", "operational_status",
        "Operational Status", "Select", "status",
        options="Operational\nUnder Maintenance\nOut of Service",
        default="Operational")

    safe_insert_custom_field("Hotel Room", "housekeeping_status",
        "Housekeeping Status", "Select", "operational_status",
        options="Clean\nDirty\nInspected\nIn Progress",
        default="Clean")

    safe_insert_custom_field("Hotel Room", "current_key_card",
        "Current Key Card", "Data", "housekeeping_status")

    # ── Hotel Room Maintenance Request doctype ────────────────────────────────
    if not frappe.db.exists("DocType", "Hotel Room Maintenance Request"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Hotel Room Maintenance Request",
            "module": "Rhocom Hotel",
            "custom": 1,
            "fields": [
                {"fieldname": "room",        "fieldtype": "Link",        "label": "Room",        "options": "Hotel Room", "reqd": 1},
                {"fieldname": "issue_type",  "fieldtype": "Select",      "label": "Issue Type",  "options": "Maintenance\nCleaning\nInspection\nOther", "reqd": 1},
                {"fieldname": "description", "fieldtype": "Text Editor", "label": "Description", "reqd": 1},
                {"fieldname": "priority",    "fieldtype": "Select",      "label": "Priority",    "options": "Low\nMedium\nHigh\nUrgent", "reqd": 1},
                {"fieldname": "status",      "fieldtype": "Select",      "label": "Status",      "options": "Open\nIn Progress\nCompleted\nCancelled", "default": "Open", "reqd": 1}
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
                {"role": "Hotel Manager",  "read": 1, "write": 1, "create": 1},
                {"role": "Maintenance User","read": 1, "write": 1, "create": 1}
            ]
        }).insert(ignore_permissions=True)
        print("Created: Hotel Room Maintenance Request doctype")

    # ── Sales Invoice — Hotel Room Check In link ──────────────────────────────
    safe_insert_custom_field("Sales Invoice", "custom_hotel_room_check_in",
        "Hotel Room Check In", "Link", "customer",
        options="Hotel Room Check In",
        in_list_view=0, in_standard_filter=1, search_index=1)

    # ── Payment Entry — Hotel Room Check In link ──────────────────────────────
    safe_insert_custom_field("Payment Entry", "custom_hotel_room_check_in",
        "Hotel Room Check In", "Link", "party",
        options="Hotel Room Check In",
        in_standard_filter=1, search_index=1)

    frappe.db.commit()
    print("add_checkin_room_fields complete")