import frappe
from frappe.utils import flt, now_datetime, get_first_day, get_last_day, nowdate


@frappe.whitelist()
def get_amenity_items():
    """Return active ERPNext Items in the Hall Amenities item group."""
    return frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE disabled = 0
          AND item_group = 'Hall Amenities'
        ORDER BY item_name ASC
    """, as_dict=True)


@frappe.whitelist()
def create_hall_amenity_item(item_name):
    if not item_name:
        frappe.throw("Amenity Name is required")

    item_name = item_name.strip()

    if not frappe.db.exists("Item Group", "Hall Amenities"):
        frappe.throw("Item Group 'Hall Amenities' does not exist. Please create it first.")

    if frappe.db.exists("Item", item_name):
        frappe.throw(
            "An Item with this name already exists. Duplicate Item names/codes are not allowed. "
            "Please check the Item list. If you want to use it as a Hall Amenity, confirm that it is under the 'Hall Amenities' item group."
        )
            

        return {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "exists": True
        }

    doc = frappe.new_doc("Item")
    doc.item_code = item_name
    doc.item_name = item_name
    doc.item_group = "Hall Amenities"
    doc.stock_uom = "Nos"
    doc.is_stock_item = 0
    doc.include_item_in_manufacturing = 0
    doc.insert(ignore_permissions=True)

    return {
        "item_code": doc.item_code,
        "item_name": doc.item_name,
        "exists": False
    }

@frappe.whitelist()
def update_hall(name, data):
    if isinstance(data, str):
        import json
        data = json.loads(data)

    doc = frappe.get_doc("Hall", name)

    doc.hall_name = data.get("hall_name")
    doc.hall_type = data.get("hall_type")
    doc.capacity = int(data.get("capacity") or 0)
    doc.rate = flt(data.get("rate") or 0)

    doc.has_projector_av = 1 if data.get("has_projector_av") else 0
    doc.has_sound_system = 1 if data.get("has_sound_system") else 0
    doc.has_air_conditioning = 1 if data.get("has_air_conditioning") else 0
    doc.has_stage = 1 if data.get("has_stage") else 0
    doc.has_restroom_access = 1 if data.get("has_restroom_access") else 0
    doc.has_parking_access = 1 if data.get("has_parking_access") else 0
    doc.has_kitchen_support = 1 if data.get("has_kitchen_support") else 0
    doc.has_private_entrance = 1 if data.get("has_private_entrance") else 0

    doc.availability_status = data.get("availability_status") or "Available"
    doc.unavailable_reason = data.get("unavailable_reason") or ""

    if doc.availability_status == "Available":
        doc.unavailable_reason = ""

    doc.set("table_tdts", [])
    for row in data.get("amenities", []):
        if row.get("item") or row.get("amenity_name"):
            doc.append("table_tdts", {
                "item": row.get("item", ""),
                "amenity_name": row.get("amenity_name", ""),
            })

    doc.save(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist()
def get_hall_list():
    halls = frappe.db.get_all(
        "Hall",
        fields=[
            "name", "hall_name", "hall_type", "capacity", "rate", "item_name",
            "availability_status", "unavailable_reason"
        ],
        order_by="hall_name asc",
    )

    now = now_datetime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

    for hall in halls:
        active = frappe.db.get_value(
            "Hall Booking",
            {
                "hall": hall.name,
                "docstatus": 1,
                "start_datetime": ["<=", now],
                "end_datetime": [">=", now],
            },
            ["name", "customer_name", "event_type", "start_datetime", "end_datetime"],
            as_dict=True,
        )

        hall["active_booking"] = active

        if hall.get("availability_status") == "Unavailable":
            hall["current_status"] = "Unavailable"
        elif active:
            hall["current_status"] = "Booked"
        else:
            hall["current_status"] = "Available"

        hall["bookings_today"] = frappe.db.count(
            "Hall Booking",
            {
                "hall": hall.name,
                "docstatus": 1,
                "start_datetime": ["<=", today_end],
                "end_datetime": [">=", today_start],
            },
        )

    return halls


@frappe.whitelist()
def get_hall(name):
    hall = frappe.get_doc("Hall", name)
    data = hall.as_dict()

    now = now_datetime()
    month_start = get_first_day(nowdate())
    month_end = get_last_day(nowdate())

    data["availability_status"] = hall.availability_status or "Available"
    data["unavailable_reason"] = hall.unavailable_reason or ""

    data["amenities"] = [
        {"item": row.item, "amenity_name": row.amenity_name}
        for row in hall.get("table_tdts", [])
    ]

    active = frappe.db.get_value(
        "Hall Booking",
        {
            "hall": name,
            "docstatus": 1,
            "start_datetime": ["<=", now],
            "end_datetime": [">=", now],
        },
        ["name", "customer_name", "event_type", "start_datetime", "end_datetime"],
        as_dict=True,
    )

    data["active_booking"] = active

    if data["availability_status"] == "Unavailable":
        data["current_status"] = "Unavailable"
    elif active:
        data["current_status"] = "Booked"
    else:
        data["current_status"] = "Available"

    upcoming = frappe.db.get_all(
        "Hall Booking",
        filters={
            "hall": name,
            "docstatus": 1,
            "start_datetime": [">", now],
        },
        fields=["name", "customer_name", "event_type", "start_datetime", "end_datetime", "net_total"],
        order_by="start_datetime asc",
        limit=10,
    )

    data["upcoming_bookings"] = upcoming
    data["upcoming_count"] = len(upcoming)

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
    if isinstance(data, str):
        import json
        data = json.loads(data)

    doc = frappe.new_doc("Hall")

    doc.hall_name = data.get("hall_name")
    doc.hall_type = data.get("hall_type")
    doc.capacity = int(data.get("capacity") or 0)
    doc.rate = flt(data.get("rate") or 0)

    doc.availability_status = data.get("availability_status") or "Available"
    doc.unavailable_reason = data.get("unavailable_reason") or ""

    if doc.availability_status == "Available":
        doc.unavailable_reason = ""

    doc.has_projector_av = 1 if data.get("has_projector_av") else 0
    doc.has_sound_system = 1 if data.get("has_sound_system") else 0
    doc.has_air_conditioning = 1 if data.get("has_air_conditioning") else 0
    doc.has_stage = 1 if data.get("has_stage") else 0
    doc.has_restroom_access = 1 if data.get("has_restroom_access") else 0
    doc.has_parking_access = 1 if data.get("has_parking_access") else 0
    doc.has_kitchen_support = 1 if data.get("has_kitchen_support") else 0
    doc.has_private_entrance = 1 if data.get("has_private_entrance") else 0

    for row in data.get("amenities", []):
        if row.get("item") or row.get("amenity_name"):
            doc.append("table_tdts", {
                "item": row.get("item", ""),
                "amenity_name": row.get("amenity_name", ""),
            })

    doc.insert(ignore_permissions=True)
    return {"name": doc.name}

@frappe.whitelist()
def update_hall_availability(hall_name, availability_status, unavailable_reason=None):
    if not hall_name:
        frappe.throw("Hall is required.")

    if availability_status not in ["Available", "Unavailable"]:
        frappe.throw("Invalid availability status.")

    hall = frappe.get_doc("Hall", hall_name)

    hall.availability_status = availability_status

    if availability_status == "Unavailable":
        hall.unavailable_reason = unavailable_reason or ""
    else:
        hall.unavailable_reason = ""

    hall.save(ignore_permissions=True)

    return {
        "name": hall.name,
        "availability_status": hall.availability_status,
        "unavailable_reason": hall.unavailable_reason,
    }
    
    
@frappe.whitelist()
def get_hall_types():
    """Return all Hall Type records for the Hall Type dropdown."""
    return frappe.db.get_all(
        "Hall Type",
        fields=["name", "hall_type_name"],
        order_by="hall_type_name asc"
    )


@frappe.whitelist()
def create_hall_type(hall_type_name):
    """Create a new Hall Type record."""
    if not hall_type_name:
        frappe.throw("Hall Type Name is required")

    hall_type_name = hall_type_name.strip()

    if frappe.db.exists("Hall Type", hall_type_name):
        return {
            "name": hall_type_name,
            "hall_type_name": hall_type_name,
            "exists": True
        }

    doc = frappe.new_doc("Hall Type")
    doc.hall_type_name = hall_type_name
    doc.insert(ignore_permissions=True)

    return {
        "name": doc.name,
        "hall_type_name": doc.hall_type_name,
        "exists": False
    }
