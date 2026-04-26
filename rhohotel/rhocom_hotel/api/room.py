import frappe
from frappe.utils import today


@frappe.whitelist()
def get_room_inventory():
    """Return all rooms with occupancy status and current guest info for the room list page."""
    rooms = frappe.db.sql("""
        SELECT
            r.name,
            r.room_number,
            r.room_type,
            r.floor,
            r.status,
            r.operational_status,
            r.maintenance_flag,
            r.current_check_in,
            r.current_guest,
            ci.guest AS guest_name
        FROM `tabHotel Room` r
        LEFT JOIN `tabHotel Room Check In` ci
            ON ci.name = r.current_check_in AND ci.docstatus = 1
        ORDER BY r.room_number ASC
    """, as_dict=True)

    today_date = today()

    # Build a simple rate cache by room_type to avoid repeated DB hits
    rate_cache = {}

    result = []
    for r in rooms:
        room_type = r.get("room_type") or ""

        if room_type and room_type not in rate_cache:
            rate_cache[room_type] = frappe.db.get_value(
                "Hotel Room Tariff",
                {"room_type": room_type, "is_active": 1},
                "rate_amount"
            ) or 0

        rate = rate_cache.get(room_type, 0)

        # Determine occupancy label
        if r.get("operational_status") != "In Service" or r.get("maintenance_flag"):
            occupancy = "Unavailable"
        elif r.get("status") == "Occupied" or r.get("current_check_in"):
            occupancy = "Occupied"
        else:
            occupancy = "Vacant"

        result.append({
            "no": r.get("room_number") or r.get("name"),
            "type": room_type,
            "floor": r.get("floor") or "",
            "rate": rate,
            "occupancy": occupancy,
            "guest": r.get("guest_name") or r.get("current_guest") or "",
        })

    # Pull room types and floors from their doctypes
    room_types = frappe.db.get_all(
        "Hotel Room Type",
        filters={"is_active": 1},
        fields=["name", "room_type"],
        order_by="room_type asc",
    )

    floors = frappe.db.get_all(
        "Hotel Floor",
        fields=["name", "floor_name", "alias"],
        order_by="name asc",
    )

    return {
        "rooms": result,
        "room_types": [rt.get("room_type") or rt.get("name") for rt in room_types],
        "floors": [f.get("name") for f in floors],
    }
