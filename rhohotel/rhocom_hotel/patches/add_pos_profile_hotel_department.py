import frappe


def execute():
    """Add hotel_department Select field to POS Profile for complimentary voucher routing."""
    if not frappe.db.exists(
        "Custom Field", {"dt": "POS Profile", "fieldname": "hotel_department"}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "POS Profile",
                "fieldname": "hotel_department",
                "label": "Hotel Department",
                "fieldtype": "Select",
                "options": "\nRestaurant\nLaundry\nFront Desk\nHousekeeping\nGM Office\nOperations",
                "insert_after": "name",
                "description": "Maps this POS terminal to a hotel department for complimentary voucher redemption.",
            }
        ).insert(ignore_permissions=True)
