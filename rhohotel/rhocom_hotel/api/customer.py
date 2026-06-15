import frappe

@frappe.whitelist(allow_guest=True)
def get_or_create_customer(name, email=None, phone=None):

    customer = frappe.db.get_value(
        "Customer",
        {"customer_name": name},
        "name"
    )

    if customer:
        return customer

    doc = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": name,
        "customer_type": "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "email_id": email or "",
        "mobile_no": phone or ""
    })

    doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return doc.name