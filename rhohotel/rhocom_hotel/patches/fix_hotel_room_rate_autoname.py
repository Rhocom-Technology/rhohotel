import frappe


def execute():
    """Fix invalid naming overrides that reference removed field `rate_type`."""

    desired_autoname = "format:{rate_code}-{room_type}"

    # Update DocType row directly.
    frappe.db.set_value("DocType", "Hotel Room Rate", "autoname", desired_autoname)
    frappe.db.set_value("DocType", "Hotel Room Rate", "naming_rule", None)

    # Remove stale property setters that forced invalid naming behavior.
    stale_setters = frappe.get_all(
        "Property Setter",
        filters={
            "doc_type": "Hotel Room Rate",
            "doctype_or_field": "DocType",
            "property": ["in", ["autoname", "naming_rule"]],
        },
        pluck="name",
    )

    for setter in stale_setters:
        frappe.delete_doc("Property Setter", setter, ignore_permissions=True, force=True)

    frappe.clear_cache(doctype="Hotel Room Rate")
    frappe.db.commit()
