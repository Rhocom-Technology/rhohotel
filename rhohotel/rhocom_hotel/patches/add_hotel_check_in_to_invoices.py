import frappe


def execute():
    """Add Hotel Room Check In link field to Sales Invoice and Payment Entry."""

    # Sales Invoice
    if not frappe.db.exists(
        "Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_hotel_room_check_in"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "custom_hotel_room_check_in",
                "label": "Hotel Room Check In",
                "fieldtype": "Link",
                "options": "Hotel Room Check In",
                "insert_after": "customer",
                "in_standard_filter": 1,
                "search_index": 1,
            }
        ).insert(ignore_permissions=True)

    # Payment Entry
    if not frappe.db.exists(
        "Custom Field", {"dt": "Payment Entry", "fieldname": "custom_hotel_room_check_in"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Payment Entry",
                "fieldname": "custom_hotel_room_check_in",
                "label": "Hotel Room Check In",
                "fieldtype": "Link",
                "options": "Hotel Room Check In",
                "insert_after": "party",
                "in_standard_filter": 1,
                "search_index": 1,
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
