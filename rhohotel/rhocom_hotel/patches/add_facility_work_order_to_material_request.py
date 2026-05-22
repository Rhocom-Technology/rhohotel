import frappe


def execute():
    # Remove the section break if it was already created
    if frappe.db.exists("Custom Field", {
        "dt": "Material Request",
        "fieldname": "rh_facilities_section"
    }):
        frappe.delete_doc("Custom Field", frappe.db.get_value(
            "Custom Field", {"dt": "Material Request", "fieldname": "rh_facilities_section"}, "name"
        ), ignore_permissions=True)
        print("Removed section break")

    # Add just the link field after company
    if not frappe.db.exists("Custom Field", {
        "dt": "Material Request",
        "fieldname": "rh_facility_work_order"
    }):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Material Request",
            "fieldname": "rh_facility_work_order",
            "fieldtype": "Link",
            "label": "Facility Work Order",
            "options": "Facility Work Order",
            "insert_after": "company",
            "description": "Link to Facility Work Order (if applicable)",
        }).insert(ignore_permissions=True)
        print("Created: rh_facility_work_order")
    else:
        # Update insert_after to remove section dependency
        frappe.db.set_value(
            "Custom Field",
            {"dt": "Material Request", "fieldname": "rh_facility_work_order"},
            "insert_after", "company"
        )
        print("Updated: rh_facility_work_order insert_after → company")

    frappe.db.commit()
    print("Done")