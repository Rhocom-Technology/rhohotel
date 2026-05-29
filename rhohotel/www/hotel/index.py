import frappe


def get_context(context):
    path = frappe.local.request.path.strip("/")

    if path == "hotel":
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect

    if path.startswith("hotel/"):
        new_path = "/" + path.replace("hotel/", "", 1)
        frappe.local.flags.redirect_location = new_path
        raise frappe.Redirect

    frappe.local.flags.redirect_location = "/"
    raise frappe.Redirect