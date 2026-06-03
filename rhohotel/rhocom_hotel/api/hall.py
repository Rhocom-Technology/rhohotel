import frappe
from frappe.utils import flt, now_datetime, get_first_day, get_last_day, nowdate



@frappe.whitelist()
def get_all_items():
    """Return active ERPNext Items in the Hall item group for the Hall form dropdowns."""
    return frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE disabled = 0
          AND item_group = 'Hall'
        ORDER BY item_name ASC
    """, as_dict=True)


@frappe.whitelist()
def get_amenity_items():
    """Return all active ERPNext Items for the Amenities table — no item group filter."""
    return frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE disabled = 0
        ORDER BY item_name ASC
    """, as_dict=True)


@frappe.whitelist()
def search_items(query=""):
    """Search ERPNext Items by name or code — used by the Hall form item pickers."""
    if not query:
        return []

    like = f"%{query}%"
    rows = frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE disabled = 0
          AND (item_name LIKE %(like)s OR item_code LIKE %(like)s)
        ORDER BY item_name ASC
        LIMIT 20
    """, {"like": like}, as_dict=True)
    return rows

@frappe.whitelist()
def update_hall(name, data):
    """Update an existing Hall document from the Vue edit form."""
    if isinstance(data, str):
        import json
        data = json.loads(data)

    doc = frappe.get_doc("Hall", name)
    doc.hall_name     = data.get("hall_name")
    doc.hall_type     = data.get("hall_type", "Conference")
    doc.capacity      = int(data.get("capacity") or 0)
    doc.rate_per_hour = flt(data.get("rate_per_hour") or 0)
    doc.item_name     = data.get("item_name") or None

    # Replace child table rows
    doc.set("table_tdts", [])
    for row in data.get("amenities", []):
        if row.get("item") or row.get("amenity_name"):
            doc.append("table_tdts", {
                "item":         row.get("item", ""),
                "amenity_name": row.get("amenity_name", ""),
            })

    doc.save(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist()
def get_hall_list():
    """
    Returns all halls with live availability derived from Hall Booking
    start_datetime / end_datetime — no status field needed on the doctype.
    """
    halls = frappe.db.get_all(
        "Hall",
        fields=["name", "hall_name", "hall_type", "capacity", "rate_per_hour", "item_name"],
        order_by="hall_name asc",
    )

    now  = now_datetime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end   = now.replace(hour=23, minute=59, second=59, microsecond=0)

    for hall in halls:
        # Active booking right now
        active = frappe.db.get_value(
            "Hall Booking",
            {
                "hall": hall.name,
                "docstatus": 1,
                "start_datetime": ["<=", now],
                "end_datetime":   [">=", now],
            },
            ["name", "customer_name", "event_type", "start_datetime", "end_datetime"],
            as_dict=True,
        )
        hall["active_booking"]  = active
        hall["current_status"]  = "Booked" if active else "Available"

        # Count bookings today
        hall["bookings_today"] = frappe.db.count(
            "Hall Booking",
            {
                "hall": hall.name,
                "docstatus": 1,
                "start_datetime": ["<=", today_end],
                "end_datetime":   [">=", today_start],
            },
        )

    return halls


@frappe.whitelist()
def get_hall(name):
    """
    Returns full hall record with amenities, active booking,
    upcoming bookings, and this-month booking count.
    """
    hall = frappe.get_doc("Hall", name)
    data = hall.as_dict()

    now        = now_datetime()
    month_start = get_first_day(nowdate())
    month_end   = get_last_day(nowdate())

    # Amenities from child table
    data["amenities"] = [
        {"item": row.item, "amenity_name": row.amenity_name}
        for row in hall.get("table_tdts", [])
    ]

    # Active booking right now
    active = frappe.db.get_value(
        "Hall Booking",
        {
            "hall": name,
            "docstatus": 1,
            "start_datetime": ["<=", now],
            "end_datetime":   [">=", now],
        },
        ["name", "customer_name", "event_type", "start_datetime", "end_datetime"],
        as_dict=True,
    )
    data["active_booking"] = active

    # Upcoming bookings (future, submitted)
    upcoming = frappe.db.get_all(
        "Hall Booking",
        filters={
            "hall": name,
            "docstatus": 1,
            "start_datetime": [">", now],
        },
        fields=["name", "customer_name", "event_type",
                "start_datetime", "end_datetime", "net_total"],
        order_by="start_datetime asc",
        limit=10,
    )
    data["upcoming_bookings"] = upcoming
    data["upcoming_count"]    = len(upcoming)

    # Bookings this month
    data["bookings_this_month"] = frappe.db.count(
        "Hall Booking",
        {
            "hall": name,
            "docstatus": 1,
            "start_datetime": ["between", [month_start, month_end]],
        },
    )

    return data


@frappe.whitelist()
def create_hall(data):
    """Create a new Hall document from the Vue form payload."""
    if isinstance(data, str):
        import json
        data = json.loads(data)

    doc = frappe.new_doc("Hall")
    doc.hall_name    = data.get("hall_name")
    doc.hall_type    = data.get("hall_type", "Conference")
    doc.capacity     = int(data.get("capacity") or 0)
    doc.rate_per_hour = flt(data.get("rate_per_hour") or 0)
    doc.item_name    = data.get("item_name") or None

    for row in data.get("amenities", []):
        if row.get("item") or row.get("amenity_name"):
            doc.append("table_tdts", {
                "item":         row.get("item", ""),
                "amenity_name": row.get("amenity_name", ""),
            })

    doc.insert(ignore_permissions=True)
    return {"name": doc.name}