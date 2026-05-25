import frappe


def execute():
    """Add custom_invoice_source field to Sales Invoice to reliably identify the charge origin."""

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
                "read_only": 1,
                "print_hide": 1,
                "no_copy": 1,
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
