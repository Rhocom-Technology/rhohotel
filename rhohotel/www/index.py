import frappe
from frappe import _


def get_context(context):
    page = frappe.form_dict.get("page") or "home"

    hotel = get_hotel_profile()
    if not hotel:
        frappe.throw(_("Hotel Profile not found"))

    template_code = get_template_code(hotel.active_template)

    optional_pages = {
        "dining": "enable_dining",
        "spa": "enable_spa",
        "gym": "enable_gym",
        "events": "enable_events",
    }

    if page in optional_pages and not hotel.get(optional_pages[page]):
        frappe.throw(_("Page not found"), frappe.DoesNotExistError)

    page_map = {
        "home": "home",
        "rooms": "rooms",
        "experiences": "experiences",
        "booking": "booking",
        "contact": "contact",
        "dining": "dining",
        "spa": "spa",
        "gym": "gym",
        "events": "events",
    }

    if page not in page_map:
        frappe.throw(_("Page not found"), frappe.DoesNotExistError)

    context.hotel = hotel
    context.current_page = page
    context.rooms = get_rooms()
    context.home_rooms = get_home_rooms()
    context.page_media = get_page_media()
    context.body_template = (
        f"rhocom_hotel/templates/hotel_templates/{template_code}/pages/{page_map[page]}.html"
    )

    return context


def get_hotel_profile():
    hotel = frappe.get_single("Hotel Profile")

    if not hotel or not hotel.published:
        return None

    return hotel

def get_template_code(template_name):
    if not template_name:
        return "template_two"

    return frappe.db.get_value("Hotel Template", template_name, "template_code") or "template_two"


def get_rooms():
    try:
        meta = frappe.get_meta("Hotel Room Type")

        filters = {}

        if meta.has_field("show_on_website"):
            filters["show_on_website"] = 1

        order_by = "creation desc"

        if meta.has_field("sort_order"):
            order_by = "sort_order asc"

        room_names = frappe.get_all(
            "Hotel Room Type",
            filters=filters,
            pluck="name",
            order_by=order_by,
        )

        # Fallback for testing:
        # if show_on_website exists but no room is checked,
        # still show all room types so the website does not look empty.
        if not room_names:
            room_names = frappe.get_all(
                "Hotel Room Type",
                pluck="name",
                order_by="creation desc",
            )

        rooms = []

        for name in room_names:
            doc = frappe.get_doc("Hotel Room Type", name)
            room = doc.as_dict()

            room["display_name"] = (
                room.get("room_type")
                or room.get("room_name")
                or room.get("title")
                or room.get("name")
            )

            room_slug = room.get("slug") or frappe.scrub(room["display_name"])
            room["display_slug"] = room_slug
            room["modal_id"] = f"roomModal-{frappe.scrub(room_slug)}"

            # Default fallback image in case the room has no uploaded image.
            room["display_image"] = "/assets/rhohotel/hotel_templates/template_two/files/room-1.jpg"
            room["display_images"] = []

            # Correct child table:
            # Parent fieldname: hotel_room_images
            # Child DocType: Hotel Room Images
            # Image fieldname inside child row: image
            if room.get("hotel_room_images"):
                room["display_images"] = [
                    row.get("image")
                    for row in room.get("hotel_room_images")
                    if row.get("image")
                ]

                if room["display_images"]:
                    room["display_image"] = room["display_images"][0]

            room["display_price"] = (
                room.get("price")
                or room.get("rate")
                or room.get("room_rate")
                or room.get("base_price")
                or room.get("standard_rate")
                or room.get("amount")
                or room.get("default_price")
                or 0
            )

            rooms.append(room)

        return rooms

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Hotel Website Room Fetch Error")
        return []


def get_home_rooms():
    try:
        meta = frappe.get_meta("Hotel Room Type")

        filters = {}

        if meta.has_field("show_on_home"):
            filters["show_on_home"] = 1

        order_by = "creation desc"

        if meta.has_field("sort_order"):
            order_by = "sort_order asc"

        room_names = frappe.get_all(
            "Hotel Room Type",
            filters=filters,
            pluck="name",
            order_by=order_by,
        )

        home_rooms = []

        for name in room_names:
            doc = frappe.get_doc("Hotel Room Type", name)
            room = doc.as_dict()

            room["display_name"] = (
                room.get("room_type")
                or room.get("room_name")
                or room.get("title")
                or room.get("name")
            )

            room["display_image"] = "/assets/rhohotel/hotel_templates/template_two/files/room-1.jpg"
            room["display_images"] = []

            if room.get("hotel_room_images"):
                room["display_images"] = [
                    row.get("image")
                    for row in room.get("hotel_room_images")
                    if row.get("image")
                ]

                if room["display_images"]:
                    room["display_image"] = room["display_images"][0]

            home_rooms.append(room)

        return home_rooms

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Hotel Website Home Room Fetch Error")
        return []
    
def get_page_media():
    try:
        records = frappe.get_all(
            "Hotel Page Media",
            filters={"is_active": 1},
            fields=["name", "page"],
            order_by="creation asc",
        )

        media = {}

        for record in records:
            if not record.page:
                continue

            page_key = frappe.scrub(record.page)

            if page_key not in media:
                media[page_key] = {}

            doc = frappe.get_doc("Hotel Page Media", record.name)

            for row in doc.get("images") or []:
                if not row.image_type or not row.image:
                    continue

                image_type_key = frappe.scrub(row.image_type)

                if image_type_key not in media[page_key]:
                    media[page_key][image_type_key] = []

                media[page_key][image_type_key].append({
                    "image": row.image,
                    "alt_text": row.alt_text or "",
                    "sort_order": row.sort_order or 0,
                })

            for image_type_key in media[page_key]:
                media[page_key][image_type_key] = sorted(
                    media[page_key][image_type_key],
                    key=lambda item: item.get("sort_order", 0)
                )

        return media

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Hotel Page Media Fetch Error")
        return {}