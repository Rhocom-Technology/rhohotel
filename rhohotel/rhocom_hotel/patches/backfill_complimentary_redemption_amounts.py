import frappe
from frappe.utils import flt


def execute():
    frappe.reload_doc("rhocom_hotel", "doctype", "hotel_complimentary")

    if not frappe.db.has_column("Hotel Complimentary", "redeemed_amount"):
        return
    if not frappe.db.has_column("Hotel Complimentary", "remaining_value"):
        return

    rows = frappe.get_all(
        "Hotel Complimentary",
        fields=["name", "value", "status", "redeemed_amount", "remaining_value"],
        limit_page_length=0,
    )
    for row in rows:
        value = flt(row.value)
        redeemed = flt(row.redeemed_amount)
        remaining = flt(row.remaining_value)

        if row.status == "Consumed":
            redeemed = value
            remaining = 0
        elif not redeemed and not remaining:
            remaining = value
        else:
            redeemed = min(max(redeemed, 0), value)
            remaining = max(value - redeemed, 0)

        frappe.db.set_value(
            "Hotel Complimentary",
            row.name,
            {
                "redeemed_amount": redeemed,
                "remaining_value": remaining,
            },
            update_modified=False,
        )
