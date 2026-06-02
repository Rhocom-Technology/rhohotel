import frappe


def execute():
    """Backfill reserved-room row status for rooms already linked to active check-ins."""
    if not frappe.db.has_column("Hotel Reservation Room", "status"):
        return

    set_clause = "rr.status = 'Checked In'"
    if frappe.db.has_column("Hotel Reservation Room", "check_in_time"):
        set_clause += ", rr.check_in_time = ci.check_in_datetime"

    frappe.db.sql(
        f"""
        UPDATE `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Room Check In` ci
            ON ci.name = rr.check_in_reference
        SET {set_clause}
        WHERE COALESCE(rr.check_in_reference, '') != ''
          AND ci.docstatus = 1
          AND ci.status = 'Checked In'
          AND COALESCE(rr.status, '') != 'Checked In'
        """
    )
    frappe.db.commit()
