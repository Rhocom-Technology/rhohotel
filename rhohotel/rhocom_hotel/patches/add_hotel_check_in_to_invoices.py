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

    # Sales Invoice — invoice source field (Restaurant / Laundry / Bar / etc.)
    if not frappe.db.exists(
        "Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_invoice_source"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "custom_invoice_source",
                "label": "Invoice Source",
                "fieldtype": "Data",
                "insert_after": "custom_hotel_room_check_in",
                "in_list_view": 0,
                "in_standard_filter": 1,
            }
        ).insert(ignore_permissions=True)

    # POS Closing Entry — difference status + reviewer note
    if not frappe.db.exists(
        "Custom Field", {"dt": "POS Closing Entry", "fieldname": "custom_difference_status"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "POS Closing Entry",
                "fieldname": "custom_difference_status",
                "label": "Difference Status",
                "fieldtype": "Select",
                "options": "\nPending Review\nUnder Review\nResolved\nEscalated",
                "insert_after": "amended_from",
                "in_list_view": 0,
                "in_standard_filter": 1,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists(
        "Custom Field", {"dt": "POS Closing Entry", "fieldname": "custom_difference_note"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "POS Closing Entry",
                "fieldname": "custom_difference_note",
                "label": "Difference Review Note",
                "fieldtype": "Small Text",
                "insert_after": "custom_difference_status",
                "in_list_view": 0,
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
