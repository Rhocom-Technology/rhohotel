# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
IPTV Integration API
====================
Exposes hotel data and room-service ordering to in-room IPTV systems.

All endpoints are Frappe whitelisted methods reachable at:
    /api/method/rhohotel.rhocom_hotel.api.iptv.<method_name>

Authentication
--------------
Every request must include the header:
    X-IPTV-API-Key: <configured_key>

The key is configured in Hotel Settings → IPTV Integration → IPTV API Key.

Response envelope
-----------------
Success:  {"success": true,  "data": {...}}
Failure:  {"success": false, "error": "Readable message"}
"""

import frappe
from frappe import _
from frappe.utils import flt, cstr, now_datetime

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_RESTAURANT_ITEM_GROUPS = frozenset({
    "food", "drinks", "drink", "beverage", "beverages",
    "kitchen", "bar", "restaurant", "snacks", "meals",
})
_LAUNDRY_ITEM_GROUPS = frozenset({"laundry", "laundry services"})


def _success(data):
    """Return a standardised success envelope."""
    return {"success": True, "data": data}


def _error(message):
    """Return a standardised error envelope (never exposes stack traces)."""
    return {"success": False, "error": message}


def _get_request_data():
    """
    Parse request body from either JSON body or form-data.
    Returns an empty dict on failure so callers never see an exception here.
    """
    try:
        if frappe.request and frappe.request.data:
            import json as _json
            return _json.loads(frappe.request.data) or {}
    except Exception:
        pass
    return frappe.local.form_dict or {}


# Maximum accepted lengths for user-supplied string inputs.
_MAX_ROOM_NUMBER_LEN = 20
_MAX_SPECIAL_REQUEST_LEN = 500
_MAX_ORDER_ITEMS = 30


def _validate_iptv_api_key():
    """
    Validate the X-IPTV-API-Key header against the value stored in
    Hotel Settings.  Returns True when valid, False otherwise.

    Design decisions
    ----------------
    * The key is stored as a Password field in Hotel Settings — it is
      never returned through normal get_doc responses.
    * We retrieve it with get_decrypted_password() which bypasses masking.
    * Comparison uses hmac.compare_digest to resist timing attacks.
    * frappe.request is guarded for None so this function is safe in
      non-HTTP contexts (e.g., unit tests).
    """
    import hmac

    try:
        # Issue 9 fix: guard against frappe.request being None
        if not frappe.request:
            return False

        incoming = (
            frappe.request.headers.get("X-IPTV-API-Key")
            or frappe.request.headers.get("x-iptv-api-key")
            or ""
        )
        if not incoming:
            return False

        # Issue 10 fix: log decryption failure explicitly instead of silently
        # falling back to comparing plaintext against the encrypted blob.
        stored = ""
        try:
            stored = frappe.utils.password.get_decrypted_password(
                "Hotel Settings", "Hotel Settings", "iptv_api_key"
            ) or ""
        except Exception:
            frappe.log_error(
                "IPTV API key decryption failed. "
                "Verify that Hotel Settings → IPTV API Key is set correctly.",
                "IPTV Auth",
            )
            return False

        if not stored:
            frappe.log_error(
                "IPTV API key is not configured in Hotel Settings.",
                "IPTV Auth",
            )
            return False

        return hmac.compare_digest(cstr(incoming), cstr(stored))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "IPTV Auth Error")
        return False


def _get_active_booking_by_room(room_number):
    """
    Return the active Hotel Room Check In document for the given room number.

    An active stay is defined as status = 'Checked In'.
    Hotel Room.name is used as the room identifier (matches room_number field
    on Hotel Room Check In which is a Link to Hotel Room).

    Returns the document dict or None.
    """
    if not room_number:
        return None

    try:
        result = frappe.db.sql(
            """
            SELECT
                ci.name,
                ci.guest,
                ci.room_number,
                ci.room_type,
                ci.check_in_datetime,
                ci.expected_check_out_datetime,
                ci.canonical_reservation,
                ci.total_charges,
                ci.total_outstanding_amount
            FROM `tabHotel Room Check In` ci
            WHERE ci.room_number = %(room)s
              AND ci.status = 'Checked In'
              AND ci.docstatus = 1
            ORDER BY ci.check_in_datetime DESC
            LIMIT 1
            """,
            {"room": room_number},
            as_dict=True,
        )
        return result[0] if result else None
    except Exception:
        frappe.log_error(frappe.get_traceback(), "IPTV: _get_active_booking_by_room")
        return None


def _get_guest_name(guest_name_field):
    """
    Resolve the display name for a Hotel Guest record.
    Returns only the guest name — no sensitive fields (ID, phone, email, etc.).
    """
    if not guest_name_field:
        return None
    try:
        return (
            frappe.db.get_value("Hotel Guest", guest_name_field, "hotel_guest_name")
            or cstr(guest_name_field)
        )
    except Exception:
        return cstr(guest_name_field)


def _get_room_type_name(room_type_field):
    """
    Return the display name for a Hotel Room Type record.

    Hotel Room Type uses the field 'room_type' (Data) for its display name,
    not 'room_type_name'.  The document name (name) is the same as the type
    identifier, so cstr(room_type_field) is a safe fallback.
    """
    if not room_type_field:
        return None
    try:
        # Issue 1 fix: correct field is 'room_type', not 'room_type_name'
        return (
            frappe.db.get_value("Hotel Room Type", room_type_field, "room_type")
            or cstr(room_type_field)
        )
    except Exception:
        return cstr(room_type_field)


def _classify_invoice(invoice_name):
    """
    Classify a Sales Invoice as 'accommodation', 'restaurant', 'laundry', or 'other'
    by inspecting its line items' item groups.

    Returns one of: 'accommodation', 'restaurant', 'laundry', 'other'.
    """
    try:
        rows = frappe.db.sql(
            """
            SELECT LOWER(COALESCE(i.item_group, '')) AS item_group
            FROM `tabSales Invoice Item` sii
            LEFT JOIN `tabItem` i ON i.name = sii.item_code
            WHERE sii.parent = %(inv)s
            """,
            {"inv": invoice_name},
            as_dict=True,
        )
        groups = {r.item_group for r in rows if r.item_group}
        if not groups:
            # No item lines → treat as accommodation (e.g. room rate invoice)
            return "accommodation"
        if groups & _LAUNDRY_ITEM_GROUPS:
            return "laundry"
        if groups & _RESTAURANT_ITEM_GROUPS:
            return "restaurant"
        # Check remarks on the invoice itself for room-related keywords
        remarks = (
            frappe.db.get_value("Sales Invoice", invoice_name, "remarks") or ""
        ).lower()
        if any(
            kw in remarks
            for kw in ("room rate", "accommodation", "room charge", "stay", "night audit")
        ):
            return "accommodation"
        return "other"
    except Exception:
        return "other"


def _get_guest_folio_summary(active_booking):
    """
    Build a folio summary dict for the given active check-in row.

    Reads linked invoices from hotel_room_check_in_invoice child table,
    classifies each by item group, and sums by category.

    Falls back to the denormalised total_charges / total_outstanding_amount
    fields on the check-in if no invoices are found.
    """
    checkin_name = active_booking.get("name")
    try:
        invoices = frappe.db.sql(
            """
            SELECT
                inv.invoice,
                COALESCE(si.grand_total, 0)          AS grand_total,
                COALESCE(si.outstanding_amount, 0)   AS outstanding_amount,
                COALESCE(si.docstatus, 0)            AS docstatus
            FROM `tabHotel Room Check In Invoice` inv
            LEFT JOIN `tabSales Invoice` si ON si.name = inv.invoice
            WHERE inv.parent = %(ci)s
              AND COALESCE(si.docstatus, 0) = 1
            """,
            {"ci": checkin_name},
            as_dict=True,
        ) or []
    except Exception:
        frappe.log_error(frappe.get_traceback(), "IPTV: folio invoice query")
        invoices = []

    totals = {
        "accommodation": 0.0,
        "restaurant": 0.0,
        "laundry": 0.0,
        "other": 0.0,
        "total_grand": 0.0,
        "total_outstanding": 0.0,
    }

    if invoices:
        for row in invoices:
            category = _classify_invoice(row.invoice)
            amount = flt(row.grand_total)
            totals[category] += amount
            totals["total_grand"] += amount
            totals["total_outstanding"] += flt(row.outstanding_amount)
    else:
        # No submitted invoices yet — use the check-in summary fields
        acc = flt(active_booking.get("total_charges"))
        outstanding = flt(active_booking.get("total_outstanding_amount"))
        totals["accommodation"] = acc
        totals["total_grand"] = acc
        totals["total_outstanding"] = outstanding

    total_charges = flt(totals["total_grand"])
    total_outstanding = flt(totals["total_outstanding"])
    total_paid = max(0.0, total_charges - total_outstanding)

    currency = frappe.db.get_default("currency") or "NGN"

    return {
        "currency": currency,
        "accommodation_charges": flt(totals["accommodation"], 2),
        "restaurant_charges": flt(totals["restaurant"], 2),
        "laundry_charges": flt(totals["laundry"], 2),
        "other_charges": flt(totals["other"], 2),
        "total_charges": flt(total_charges, 2),
        "total_paid": flt(total_paid, 2),
        "outstanding_balance": flt(total_outstanding, 2),
    }


def _get_menu_items(category=None):
    """
    Return available Menu Items grouped by their item_group (category).

    The Menu Item DocType stores rate directly.  Category is derived from
    the linked ERPNext Item's item_group, which is the cleanest grouping
    available without adding new fields.

    Issue 4 fix: replaced f-string SQL interpolation with two separate
    fully-parameterized queries to eliminate the SQL injection risk pattern.

    Issue 7 fix: added `mi.item_code IS NOT NULL AND i.name IS NOT NULL`
    so Menu Items with no linked ERPNext Item are excluded.  Previously,
    the COALESCE(i.disabled, 0) = 0 condition was TRUE when i was NULL
    (COALESCE(NULL, 0) = 0), so orphaned Menu Items always appeared.
    """
    try:
        if category:
            rows = frappe.db.sql(
                """
                SELECT
                    mi.name            AS item_code,
                    mi.item_name       AS item_name,
                    mi.description     AS description,
                    mi.rate            AS price,
                    mi.image           AS image,
                    i.item_group       AS category
                FROM `tabMenu Item` mi
                INNER JOIN `tabItem` i ON i.name = mi.item_code
                WHERE mi.item_code IS NOT NULL
                  AND i.disabled = 0
                  AND LOWER(i.item_group) = LOWER(%(category)s)
                ORDER BY mi.item_name
                """,
                {"category": category},
                as_dict=True,
            ) or []
        else:
            rows = frappe.db.sql(
                """
                SELECT
                    mi.name            AS item_code,
                    mi.item_name       AS item_name,
                    mi.description     AS description,
                    mi.rate            AS price,
                    mi.image           AS image,
                    i.item_group       AS category
                FROM `tabMenu Item` mi
                INNER JOIN `tabItem` i ON i.name = mi.item_code
                WHERE mi.item_code IS NOT NULL
                  AND i.disabled = 0
                ORDER BY i.item_group, mi.item_name
                """,
                as_dict=True,
            ) or []
    except Exception:
        frappe.log_error(frappe.get_traceback(), "IPTV: _get_menu_items")
        return []

    # Group by category
    grouped = {}
    for row in rows:
        cat = row.get("category") or "General"
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "item_code": cstr(row.get("item_code")),
            "item_name": cstr(row.get("item_name")),
            "description": cstr(row.get("description") or ""),
            "price": flt(row.get("price"), 2),
            "available": True,
            "image": cstr(row.get("image") or ""),
        })

    return [{"category": cat, "items": items} for cat, items in grouped.items()]


# ---------------------------------------------------------------------------
# Public whitelisted endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_guest_by_room():
    """
    Endpoint 1 — Retrieve guest information by room number.

    URL: /api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_by_room
    Auth: X-IPTV-API-Key header required.

    Input (JSON body or form data):
        { "room_number": "101" }

    Returns guest name, dates, room details.
    No sensitive PII (ID, phone, email, address, passport) is returned.
    """
    if not _validate_iptv_api_key():
        return _error("Unauthorized")

    data = _get_request_data()
    room_number = cstr(data.get("room_number") or "").strip()

    if not room_number:
        return _error("room_number is required")
    if len(room_number) > _MAX_ROOM_NUMBER_LEN:
        return _error("room_number is too long")

    active = _get_active_booking_by_room(room_number)
    if not active:
        return _error("No active guest found for this room")

    guest_name = _get_guest_name(active.get("guest"))
    room_type = _get_room_type_name(active.get("room_type"))

    check_in_dt = active.get("check_in_datetime")
    check_out_dt = active.get("expected_check_out_datetime")

    # Issue 3 fix: frappe.db.sql may return datetime strings, not datetime
    # objects, depending on the MySQL driver version.  Use getdate() which
    # handles both safely.
    from frappe.utils import get_datetime as _get_dt

    def _safe_date_str(val):
        if not val:
            return None
        try:
            return str(_get_dt(val).date())
        except Exception:
            return cstr(val)[:10]  # best-effort: take first 10 chars (YYYY-MM-DD)

    return _success({
        "guest_name": guest_name or "—",
        "check_in_date": _safe_date_str(check_in_dt),
        "check_out_date": _safe_date_str(check_out_dt),
        "room_number": cstr(room_number),
        "room_type": room_type or cstr(active.get("room_type")),
        "booking_id": cstr(active.get("canonical_reservation") or active.get("name")),
    })


@frappe.whitelist(allow_guest=True)
def get_guest_folio():
    """
    Endpoint 2 — Retrieve the current bill/folio for a guest by room number.

    URL: /api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_folio
    Auth: X-IPTV-API-Key header required.

    Input:
        { "room_number": "101" }

    Returns categorised charges and outstanding balance.
    Cancelled invoices are excluded (docstatus = 1 only).
    """
    if not _validate_iptv_api_key():
        return _error("Unauthorized")

    data = _get_request_data()
    room_number = cstr(data.get("room_number") or "").strip()

    if not room_number:
        return _error("room_number is required")
    if len(room_number) > _MAX_ROOM_NUMBER_LEN:
        return _error("room_number is too long")

    active = _get_active_booking_by_room(room_number)
    if not active:
        return _error("No active guest found for this room")

    guest_name = _get_guest_name(active.get("guest"))
    folio = _get_guest_folio_summary(active)

    return _success({
        "guest_name": guest_name or "—",
        "room_number": cstr(room_number),
        **folio,
    })


@frappe.whitelist(allow_guest=True)
def place_room_service_order():
    """
    Endpoint 3 — Place a room service order from the IPTV system.

    URL: /api/method/rhohotel.rhocom_hotel.api.iptv.place_room_service_order
    Auth: X-IPTV-API-Key header required.
    Method: POST only (GET is rejected to prevent accidental ordering).

    Input:
        {
            "room_number": "101",
            "items": [
                {"item_code": "MENU-ITEM-00001", "qty": 2, "notes": "No pepper"},
                {"item_code": "MENU-ITEM-00002", "qty": 1}
            ],
            "special_request": "Please deliver quickly"
        }

    Notes:
    - item_code must be a valid Menu Item document name.
    - Rates are fetched server-side from Menu Item; IPTV-supplied rates are ignored.
    - The order is linked to the active Hotel Room Check In and Hotel Guest.
    - order_type is set to "Room Service".
    - special_request is stored as a document comment (Menu Item has no notes field).
    - The Restaurant Order is created in status "Confirmed".
    """
    # Reject GET requests — ordering must be explicit POST
    if frappe.request and frappe.request.method == "GET":
        return _error("This endpoint requires POST")

    if not _validate_iptv_api_key():
        return _error("Unauthorized")

    data = _get_request_data()
    room_number = cstr(data.get("room_number") or "").strip()
    items_raw = data.get("items") or []
    # Issue 5 fix: strip HTML from special_request to prevent stored XSS
    # when comments are rendered in Frappe's desk UI.
    from frappe.utils import strip_html_tags
    special_request = strip_html_tags(cstr(data.get("special_request") or "")).strip()

    # --- Input validation ---
    # Issue 8 fix: enforce max input lengths
    if not room_number:
        return _error("room_number is required")
    if len(room_number) > _MAX_ROOM_NUMBER_LEN:
        return _error("room_number is too long")

    # Issue 6 fix: check type before emptiness so a non-list value
    # (e.g. a JSON object) is rejected before the truthiness check.
    if not isinstance(items_raw, list):
        return _error("items must be a list")

    if not items_raw:
        return _error("items list is required and cannot be empty")

    # Issue 8 fix: cap number of items to prevent abuse
    if len(items_raw) > _MAX_ORDER_ITEMS:
        return _error(f"Order cannot exceed {_MAX_ORDER_ITEMS} items")

    # --- Validate active guest ---
    active = _get_active_booking_by_room(room_number)
    if not active:
        return _error("No active guest found for this room")

    guest_link = active.get("guest")
    checkin_name = active.get("name")
    # customer lives on Hotel Guest, not on Hotel Room Check In.
    # Fetch it here so Restaurant Order can be linked to the ERPNext Customer.
    customer_link = (
        frappe.db.get_value("Hotel Guest", guest_link, "customer")
        if guest_link else None
    ) or None
    guest_name = _get_guest_name(guest_link)

    # --- Validate and resolve items from Menu Item DocType ---
    order_items = []
    for idx, itm in enumerate(items_raw):
        item_code = cstr(itm.get("item_code") or "").strip()
        try:
            qty = flt(itm.get("qty") or itm.get("quantity") or 0)
        except (TypeError, ValueError):
            return _error(f"Invalid qty for item at position {idx + 1}")

        if not item_code:
            return _error(f"item_code is required for item at position {idx + 1}")

        if qty <= 0:
            return _error(f"qty must be greater than 0 for item '{item_code}'")

        # Fetch rate server-side — never trust the IPTV-supplied price
        # Assumption: item_code is the Menu Item document name
        menu_item = frappe.db.get_value(
            "Menu Item",
            item_code,
            ["name", "item_name", "rate"],
            as_dict=True,
        )
        if not menu_item:
            return _error(f"Menu item '{item_code}' not found or unavailable")

        item_name = menu_item.get("name") if isinstance(menu_item, dict) else menu_item.name
        item_rate = flt(menu_item.get("rate") if isinstance(menu_item, dict) else menu_item.rate)

        order_items.append({
            "item": item_name,
            "quantity": qty,
            "rate": item_rate,
            "amount": flt(qty * item_rate),
        })

    # --- Create Restaurant Order inside a savepoint for atomicity ---
    try:
        order = frappe.new_doc("Restaurant Order")
        order.order_type = "Room Service"
        order.hotel_guest = guest_link or None
        order.room_checkin = checkin_name
        order.customer = customer_link
        order.status = "Confirmed"

        for itm in order_items:
            order.append("items", {
                "item": itm["item"],
                "quantity": itm["quantity"],
                "rate": itm["rate"],
                "amount": itm["amount"],
            })

        # calculate_total runs in before_save of RestaurantOrder
        order.insert(ignore_permissions=True)

        # Store special_request as a comment so no DocType changes are needed.
        # The value has already been HTML-stripped above (issue 5).
        # Cap length here too in case strip_html_tags expanded the string.
        if special_request:
            safe_request = special_request[:_MAX_SPECIAL_REQUEST_LEN]
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "Restaurant Order",
                "reference_name": order.name,
                "content": f"[IPTV Special Request] {safe_request}",
            }).insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "IPTV: place_room_service_order")
        return _error("Failed to create order. Please try again.")

    created_at = cstr(order.creation or now_datetime())

    return _success({
        "order_id": cstr(order.name),
        "status": cstr(order.status),
        "room_number": cstr(room_number),
        "guest_name": guest_name or "—",
        "total_amount": flt(order.total_amount, 2),
        "created_at": cstr(created_at),
    })


@frappe.whitelist(allow_guest=True)
def get_room_service_menu():
    """
    Endpoint 4 — Retrieve available room service menu categories and items.

    URL: /api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu
    Auth: X-IPTV-API-Key header required.

    Optional input:
        { "category": "Food" }   — filter by category (item_group); omit for all.

    Items are sourced from the Menu Item DocType.
    Category is derived from the linked ERPNext Item's item_group.
    Only items whose linked Item is enabled (disabled = 0) are returned.
    """
    if not _validate_iptv_api_key():
        return _error("Unauthorized")

    data = _get_request_data()
    category_filter = cstr(data.get("category") or "").strip() or None

    categories = _get_menu_items(category=category_filter)
    currency = frappe.db.get_default("currency") or "NGN"

    return _success({
        "currency": currency,
        "categories": categories,
    })


def _get_restaurant_menus(menu_name=None, location=None):
    """
    Return Restaurant Menu records with their items.

    Data model
    ----------
    Restaurant Menu  1──* Restaurant Menu Item ──> Menu Item ──> Item

    Rate precedence (per item):
      1. Restaurant Menu Item.rate  (location/menu-specific override; used when > 0)
      2. Menu Item.rate             (global base rate fallback)

    Filters
    -------
    menu_name : exact match on Restaurant Menu.menu_name (case-sensitive)
    location  : exact match on Restaurant Menu.restaurant_location (case-insensitive)

    Only items whose linked ERPNext Item is enabled (disabled = 0) are included.
    Items where Menu Item has no linked ERPNext Item are excluded.
    """
    try:
        # Build the WHERE clause using only parameterised conditions so no
        # user-supplied string is ever interpolated into the SQL text.
        conditions = ["COALESCE(i.disabled, 0) = 0", "mi.item_code IS NOT NULL"]
        params: dict = {}

        if menu_name:
            conditions.append("rm.menu_name = %(menu_name)s")
            params["menu_name"] = menu_name

        if location:
            conditions.append("LOWER(rm.restaurant_location) = LOWER(%(location)s)")
            params["location"] = location

        where_clause = " AND ".join(conditions)

        rows = frappe.db.sql(
            f"""
            SELECT
                rm.name                                    AS menu_id,
                rm.menu_name                               AS menu_name,
                rm.restaurant_location                     AS location,
                mi.name                                    AS item_code,
                mi.item_name                               AS item_name,
                mi.description                             AS description,
                mi.image                                   AS image,
                COALESCE(i.item_group, 'General')          AS category,
                CASE
                    WHEN rmi.rate > 0 THEN rmi.rate
                    ELSE mi.rate
                END                                        AS price
            FROM `tabRestaurant Menu` rm
            INNER JOIN `tabRestaurant Menu Item` rmi ON rmi.parent = rm.name
            INNER JOIN `tabMenu Item` mi             ON mi.name    = rmi.menu_item
            INNER JOIN `tabItem` i                   ON i.name     = mi.item_code
            WHERE {where_clause}
            ORDER BY rm.menu_name, i.item_group, mi.item_name
            """,
            params,
            as_dict=True,
        ) or []
    except Exception:
        frappe.log_error(frappe.get_traceback(), "IPTV: _get_restaurant_menus")
        return []

    # Group rows → menus → items
    menus: dict = {}
    for row in rows:
        mid = cstr(row.get("menu_id"))
        if mid not in menus:
            menus[mid] = {
                "menu_name": cstr(row.get("menu_name")),
                "location": cstr(row.get("location") or ""),
                "items": [],
            }
        menus[mid]["items"].append({
            "item_code": cstr(row.get("item_code")),
            "item_name": cstr(row.get("item_name")),
            "description": cstr(row.get("description") or ""),
            "category": cstr(row.get("category") or "General"),
            "price": flt(row.get("price"), 2),
            "available": True,
            "image": cstr(row.get("image") or ""),
        })

    return list(menus.values())


@frappe.whitelist(allow_guest=True)
def get_restaurant_menu():
    """
    Endpoint 5 — Retrieve restaurant menus with items.

    URL: /api/method/rhohotel.rhocom_hotel.api.iptv.get_restaurant_menu
    Auth: X-IPTV-API-Key header required.
    HTTP methods: GET, POST.

    Optional input (all filters may be combined or omitted):
        {
            "menu_name": "Breakfast Menu",
            "location":  "Main Restaurant"
        }

    Behaviour
    ---------
    - Returns all Restaurant Menu records when no filters are supplied.
    - Filters by exact menu_name when provided.
    - Filters by location (case-insensitive) when provided.
    - Each item shows the menu-specific rate override when set (> 0),
      otherwise falls back to the global Menu Item rate.
    - Only items whose linked ERPNext Item is enabled are returned.
    - Items with no linked ERPNext Item are excluded.

    Difference from get_room_service_menu
    --------------------------------------
    get_room_service_menu reads directly from Menu Item and groups by
    item_group.  This endpoint reads from the Restaurant Menu DocType,
    which lets the hotel maintain separate named menus per location
    (e.g. "Pool Bar Menu", "Breakfast Menu") with location-specific prices.
    """
    if not _validate_iptv_api_key():
        return _error("Unauthorized")

    data = _get_request_data()
    menu_name = cstr(data.get("menu_name") or "").strip() or None
    location   = cstr(data.get("location")  or "").strip() or None

    # Enforce reasonable length limits on filter strings
    if menu_name and len(menu_name) > 140:
        return _error("menu_name filter is too long")
    if location and len(location) > 140:
        return _error("location filter is too long")

    menus = _get_restaurant_menus(menu_name=menu_name, location=location)
    currency = frappe.db.get_default("currency") or "NGN"

    return _success({
        "currency": currency,
        "menus": menus,
    })
