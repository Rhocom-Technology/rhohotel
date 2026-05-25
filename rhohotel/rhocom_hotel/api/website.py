import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def submit_contact_message(full_name=None, email=None, phone=None, enquiry_type=None, message=None):
    if not full_name:
        frappe.throw(_("Full name is required"))

    if not email:
        frappe.throw(_("Email address is required"))

    if not message:
        frappe.throw(_("Message is required"))

    contact_message = frappe.get_doc({
        "doctype": "Hotel Contact Message",
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "enquiry_type": enquiry_type or "General",
        "message": message,
        "status": "New",
    })

    contact_message.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "Your message has been sent successfully.",
        "name": contact_message.name,
    }