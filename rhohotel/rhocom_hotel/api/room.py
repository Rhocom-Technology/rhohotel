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


@frappe.whitelist()
def get_room_detail(room_id):
    """Return full details for a single room, including current guest and audit trail."""
    if not room_id:
        frappe.throw("room_id is required")

    # Accept either doc name or room_number
    if frappe.db.exists("Hotel Room", room_id):
        doc_name = room_id
    else:
        doc_name = frappe.db.get_value("Hotel Room", {"room_number": room_id}, "name")
        if not doc_name:
            frappe.throw(f"Room '{room_id}' not found", frappe.DoesNotExistError)

    room = frappe.get_doc("Hotel Room", doc_name)

    # Rate from active tariff, fall back to room's base_rate
    rate = 0
    if room.room_type:
        tariff_rows = frappe.get_all(
            "Hotel Room Tariff",
            filters={"room_type": room.room_type, "is_active": 1},
            fields=["rate_amount"],
            limit=1,
        )
        rate = tariff_rows[0].rate_amount if tariff_rows else 0
    rate = rate or room.base_rate or 0

    # Determine occupancy label
    if room.operational_status != "In Service" or room.maintenance_flag:
        occupancy = "Unavailable"
    elif room.status == "Occupied" or room.current_check_in:
        occupancy = "Occupied"
    else:
        occupancy = "Vacant"

    # Current guest display name — Hotel Guest uses hotel_guest_name as title field
    guest_name = ""
    if room.current_guest:
        guest_name = (
            frappe.db.get_value("Hotel Guest", room.current_guest, "hotel_guest_name")
            or room.current_guest
        )

    # Amenities list
    amenities = [row.amenity for row in (room.amenities or []) if row.amenity]

    # Audit trail from Frappe Version log (wrapped defensively)
    audit = []
    try:
        versions = frappe.db.sql("""
            SELECT
                DATE_FORMAT(creation, '%%d %%b %%Y • %%h:%%i %%p') AS time,
                owner
            FROM `tabVersion`
            WHERE ref_doctype = 'Hotel Room' AND docname = %s
            ORDER BY creation DESC
            LIMIT 10
        """, [doc_name], as_dict=True)
        audit = [{"time": v.get("time"), "action": f"Modified by {v.get('owner')}"} for v in versions]
    except Exception:
        pass

    if not audit:
        creation_str = frappe.utils.get_datetime(room.creation).strftime("%d %b %Y • %I:%M %p") if room.creation else ""
        audit = [{"time": creation_str, "action": f"Room record created by {room.owner}"}]

    return {
        "name": room.name,
        "room_number": room.room_number or room.name,
        "room_type": room.room_type or "",
        "floor": room.floor or "",
        "bed_type": room.bed_type or "",
        "capacity": room.capacity or "",
        "status": room.status or "",
        "operational_status": room.operational_status or "",
        "occupancy": occupancy,
        "housekeeping_status": room.housekeeping_status or "",
        "maintenance_flag": bool(room.maintenance_flag),
        "require_inspection": bool(room.require_inspection),
        "keycard_enabled": bool(room.keycard_enabled),
        "rate": rate,
        "rate_plan": room.rate_plan or "",
        "description": room.description or "",
        "operational_notes": room.operational_notes or "",
        "current_check_in": room.current_check_in or "",
        "current_guest": room.current_guest or "",
        "guest_name": guest_name,
        "amenities": amenities,
        "audit": audit,
    }
