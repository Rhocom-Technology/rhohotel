import frappe
from frappe import _


def is_leaf_customer_group(customer_group):
    """Return True when the Customer Group exists and is not a parent group."""
    customer_group = (customer_group or "").strip()
    if not customer_group:
        return False

    if not frappe.db.exists("Customer Group", customer_group):
        return False

    return not bool(frappe.db.get_value("Customer Group", customer_group, "is_group"))


def get_leaf_customer_group(preferred=None):
    """
    Resolve a valid non-group Customer Group for generated hotel customers.

    ERPNext rejects parent groups such as "All Customer Groups" on Customer
    records, so defaults must be checked before use.
    """
    candidates = [preferred]

    get_default = getattr(frappe.db, "get_default", None)
    if callable(get_default):
        candidates.append(get_default("customer_group"))

    try:
        selling_settings = frappe.get_cached_doc("Selling Settings")
        candidates.append(getattr(selling_settings, "customer_group", None))
    except Exception:
        pass

    candidates.append("Individual")

    seen = set()
    for candidate in candidates:
        candidate = (candidate or "").strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if is_leaf_customer_group(candidate):
            return candidate

    try:
        customer_group = frappe.db.get_value(
            "Customer Group",
            {"is_group": 0},
            "name",
            order_by="lft asc",
        )
    except TypeError:
        customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")

    if customer_group:
        return customer_group

    frappe.throw(_("Please create a non-group Customer Group before creating hotel customers."))
