import frappe
from frappe.model.naming import make_autoname


@frappe.whitelist(allow_guest=True)
def submit_contact_message(full_name=None, email=None, phone=None, enquiry_type=None, message=None):
    if not full_name:
        return {"success": False, "message": "Full name is required."}

    if not email:
        return {"success": False, "message": "Email address is required."}

    if not message:
        return {"success": False, "message": "Message is required."}

    doc = frappe.new_doc("Hotel Contact Message")
    doc.name = make_autoname("HCM-.#####")
    doc.full_name = full_name
    doc.email = email
    doc.phone = phone
    doc.enquiry_type = enquiry_type
    doc.message = message
    doc.status = "New"

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "Message sent successfully."
    }

@frappe.whitelist(allow_guest=True)
def submit_event_booking(
    hall=None,
    guest_name=None,
    guest_email=None,
    guest_phone=None,
    event_type=None,
    event_date=None,
    start_time=None,
    end_time=None,
    estimated_guest=None,
    noted=None,
):
    if not guest_name:
        return {"success": False, "message": "Guest name is required."}

    if not guest_email:
        return {"success": False, "message": "Guest email is required."}

    if not hall:
        return {"success": False, "message": "Please select an event hall."}

    if not event_type:
        return {"success": False, "message": "Please select an event type."}

    if not event_date:
        return {"success": False, "message": "Event date is required."}

    doc = frappe.new_doc("Hotel Event Booking")
    doc.hall = hall
    doc.guest_name = guest_name
    doc.guest_email = guest_email
    doc.guest_phone = guest_phone
    doc.event_type = event_type
    doc.event_date = event_date
    doc.start_time = start_time
    doc.end_time = end_time
    doc.estimated_guest = estimated_guest
    doc.noted = noted
    doc.status = "Pending"
    doc.payment_status = "Unpaid"

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "Event booking enquiry submitted successfully.",
        "booking": doc.name,
    }