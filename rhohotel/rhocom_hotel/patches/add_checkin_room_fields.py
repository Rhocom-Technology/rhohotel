import frappe

def execute():
    """Add new fields to Hotel Room Check In doctype"""
    # Add fields for enhanced check-in process
    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "vehicle_number"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room Check In",
            "fieldname": "vehicle_number",
            "label": "Vehicle Number",
            "fieldtype": "Data",
            "insert_after": "contact_number"
        }).insert()

    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "special_requests"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room Check In",
            "fieldname": "special_requests",
            "label": "Special Requests",
            "fieldtype": "Text",
            "insert_after": "vehicle_number"
        }).insert()

    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "key_card_number"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room Check In",
            "fieldname": "key_card_number",
            "label": "Key Card Number",
            "fieldtype": "Data",
            "insert_after": "room"
        }).insert()

    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room Check In", "fieldname": "room_preferences"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room Check In",
            "fieldname": "room_preferences",
            "label": "Room Preferences",
            "fieldtype": "Text",
            "insert_after": "special_requests"
        }).insert()

    # Add new status field to Hotel Room
    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "operational_status"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room",
            "fieldname": "operational_status",
            "label": "Operational Status",
            "fieldtype": "Select",
            "options": "Operational\nUnder Maintenance\nOut of Service",
            "default": "Operational",
            "insert_after": "status"
        }).insert()

    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "housekeeping_status"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room",
            "fieldname": "housekeeping_status",
            "label": "Housekeeping Status",
            "fieldtype": "Select",
            "options": "Clean\nDirty\nInspected\nIn Progress",
            "default": "Clean",
            "insert_after": "operational_status"
        }).insert()

    if not frappe.db.exists("Custom Field", {"dt": "Hotel Room", "fieldname": "current_key_card"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Hotel Room",
            "fieldname": "current_key_card",
            "label": "Current Key Card",
            "fieldtype": "Data",
            "insert_after": "housekeeping_status"
        }).insert()

    # Create Hotel Room Maintenance Request doctype if it doesn't exist
    if not frappe.db.exists("DocType", "Hotel Room Maintenance Request"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Hotel Room Maintenance Request",
            "module": "Rhocom Hotel",
            "custom": 1,
            "fields": [
                {
                    "fieldname": "room",
                    "fieldtype": "Link",
                    "label": "Room",
                    "options": "Hotel Room",
                    "reqd": 1
                },
                {
                    "fieldname": "issue_type",
                    "fieldtype": "Select",
                    "label": "Issue Type",
                    "options": "Maintenance\nCleaning\nInspection\nOther",
                    "reqd": 1
                },
                {
                    "fieldname": "description",
                    "fieldtype": "Text Editor",
                    "label": "Description",
                    "reqd": 1
                },
                {
                    "fieldname": "priority",
                    "fieldtype": "Select",
                    "label": "Priority",
                    "options": "Low\nMedium\nHigh\nUrgent",
                    "reqd": 1
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "label": "Status",
                    "options": "Open\nIn Progress\nCompleted\nCancelled",
                    "default": "Open",
                    "reqd": 1
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                },
                {
                    "role": "Hotel Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1
                },
                {
                    "role": "Maintenance User",
                    "read": 1,
                    "write": 1,
                    "create": 1
                }
            ]
        }).insert()

    # Add Hotel Room Check In link field to Sales Invoice
    if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_hotel_room_check_in"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "custom_hotel_room_check_in",
            "label": "Hotel Room Check In",
            "fieldtype": "Link",
            "options": "Hotel Room Check In",
            "insert_after": "customer",
            "in_list_view": 0,
            "in_standard_filter": 1,
            "search_index": 1,
        }).insert(ignore_permissions=True)

    # Add Hotel Room Check In link field to Payment Entry
    if not frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "custom_hotel_room_check_in"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Payment Entry",
            "fieldname": "custom_hotel_room_check_in",
            "label": "Hotel Room Check In",
            "fieldtype": "Link",
            "options": "Hotel Room Check In",
            "insert_after": "party",
            "in_standard_filter": 1,
            "search_index": 1,
        }).insert(ignore_permissions=True)

    frappe.db.commit()