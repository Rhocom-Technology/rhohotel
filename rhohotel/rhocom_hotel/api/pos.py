import re
import frappe
from frappe import _
from frappe.utils import flt, cstr, now_datetime, nowdate, add_days, getdate, time_diff_in_seconds
from frappe.utils.nestedset import get_descendants_of
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability

_TABLE_NAME_RE = re.compile(r'^(Table|Bar|Pool)\s*\S', re.IGNORECASE)


def _extract_table_display_name(customer):
    """If customer looks like a table/bar/pool name, return it as a display name.
    The caller should use Walk-In as the actual ERPNext customer and override
    pi.customer_name = the returned value AFTER set_missing_values()."""
    name = cstr(customer).strip()
    return name if (name and _TABLE_NAME_RE.match(name)) else None


def _get_user_pos_profile(user=None):
    """Return the active POS Profile mapped to the current user.

    No fallback is applied: users without mapping get no POS profile.
    """
    user = user or frappe.session.user

    if not user or user == "Guest":
        return None

    mapped_profile = frappe.db.sql(
        """
        SELECT p.name
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` pu ON pu.parent = p.name
        WHERE p.disabled = 0
            AND (
                LOWER(pu.user) = LOWER(%s)
                OR LOWER(SUBSTRING_INDEX(pu.user, '@', 1)) = LOWER(SUBSTRING_INDEX(%s, '@', 1))
            )
        ORDER BY p.modified DESC
        LIMIT 1
        """,
        (user, user),
    )

    if mapped_profile:
        return mapped_profile[0][0]

    return None


def _get_allowed_item_groups_for_profile(pos_profile):
    """Return configured POS profile item groups + descendants."""
    if not pos_profile:
        return []

    profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
    groups = []
    for row in profile_doc.get("item_groups") or []:
        if not row.item_group:
            continue
        groups.append(row.item_group)
        groups.extend(get_descendants_of("Item Group", row.item_group))

    return list(set(groups))


def _get_user_pos_profiles(user=None):
    """Return active POS Profiles accessible to the given user.

    Only profiles that explicitly list the user are returned. A cashier must be
    intentionally mapped to one or more POS Profiles before opening a shift.
    """
    user = user or frappe.session.user
    if not user or user == "Guest":
        return []

    rows = frappe.db.sql(
        """
        SELECT DISTINCT p.name
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` pu ON pu.parent = p.name
        WHERE p.disabled = 0
          AND (
                LOWER(pu.user) = LOWER(%s)
                OR LOWER(SUBSTRING_INDEX(pu.user, '@', 1)) = LOWER(SUBSTRING_INDEX(%s, '@', 1))
          )
        ORDER BY p.modified DESC
        """,
        (user, user),
        as_dict=1,
    )
    return [r.get("name") for r in rows if r.get("name")]


def _get_open_pos_entry(user, pos_profile=None):
    """Return an open POS Opening Entry for user, preferring the given profile.

    If no open entry exists for the preferred profile, falls back to any open
    entry for the same user.
    """
    if not user or user == "Guest":
        return None

    if pos_profile:
        preferred = frappe.db.get_value(
            "POS Opening Entry",
            {
                "user": user,
                "pos_profile": pos_profile,
                "status": "Open",
                "docstatus": 1,
            },
            ["name", "pos_profile"],
            as_dict=True,
        )
        if preferred:
            return preferred

    fallback = frappe.db.get_value(
        "POS Opening Entry",
        {
            "user": user,
            "status": "Open",
            "docstatus": 1,
        },
        ["name", "pos_profile"],
        as_dict=True,
        order_by="modified desc",
    )
    return fallback


def _has_pos_opening_entry_on_invoice():
    """Return True when POS Invoice has the pos_opening_entry column."""
    return bool(frappe.db.has_column("POS Invoice", "pos_opening_entry"))


def _pos_invoice_shift_time_condition(alias="pi"):
    return f"TIMESTAMP({alias}.posting_date, COALESCE({alias}.posting_time, '00:00:00')) >= %s"


def _get_shift_open_table_count(entry_doc, pos_opening_entry=None):
    table_condition = """
        (customer_name LIKE 'Table %%'
         OR customer_name LIKE 'Bar %%'
         OR customer_name LIKE 'Pool%%')
    """
    if _has_pos_opening_entry_on_invoice() and pos_opening_entry:
        return frappe.db.sql("""
            SELECT COUNT(*)
            FROM `tabPOS Invoice`
            WHERE pos_opening_entry = %s
              AND docstatus = 0
              AND {table_condition}
        """.format(table_condition=table_condition), pos_opening_entry)[0][0] or 0

    time_condition = _pos_invoice_shift_time_condition("pi")
    return frappe.db.sql("""
        SELECT COUNT(*)
        FROM `tabPOS Invoice` pi
        WHERE pi.pos_profile = %s
          AND pi.owner = %s
          AND {time_condition}
          AND pi.docstatus = 0
          AND {table_condition}
    """.format(
        time_condition=time_condition,
        table_condition=table_condition,
    ), (entry_doc.pos_profile, entry_doc.user, entry_doc.period_start_date))[0][0] or 0


def _get_room_posting_mop(profile_doc, fallback_modes):
    """Return the best Mode of Payment to use for a room-posting POS Invoice.

    Room postings are charged to the room folio (Sales Invoice), not collected
    as cash.  Using a non-cash MOP prevents the shift report from counting
    these charges as cash received.

    Priority:
    1. A mode listed in the POS profile whose name contains 'room', 'folio',
       or 'credit' (case-insensitive).
    2. A system-wide Mode of Payment whose name starts with 'Room'.
    3. First allowed mode from the POS profile (legacy fallback).
    """
    room_keywords = ["room", "folio", "credit"]
    for row in (profile_doc.get("payments") or []):
        mop = (row.mode_of_payment or "").lower()
        if any(kw in mop for kw in room_keywords):
            return row.mode_of_payment

    system_mop = frappe.db.get_value(
        "Mode of Payment",
        {"name": ["like", "Room%"], "enabled": 1},
        "name",
    )
    if system_mop:
        return system_mop

    return fallback_modes[0] if fallback_modes else "Cash"


def _resolve_pos_payment_mode(method, profile_doc, allowed_modes, allow_fallback=False):
    method = cstr(method or "").strip()
    allowed_modes = [mode for mode in (allowed_modes or []) if mode]

    if not allowed_modes:
        frappe.throw(_("POS Profile {0} has no payment modes configured.").format(profile_doc.name))

    if method in allowed_modes:
        return method

    method_lower = method.lower()
    for mode in allowed_modes:
        if cstr(mode).strip().lower() == method_lower:
            return mode

    if method_lower == "pos":
        pos_keywords = ("pos", "card", "debit", "terminal")
        excluded_keywords = ("room", "folio")
        for mode in allowed_modes:
            mode_lower = cstr(mode).lower()
            if any(keyword in mode_lower for keyword in excluded_keywords):
                continue
            if any(keyword in mode_lower for keyword in pos_keywords) or "credit card" in mode_lower:
                return mode

    if method_lower == "cash":
        for mode in allowed_modes:
            if "cash" in cstr(mode).lower():
                return mode

    if method_lower == "post to room":
        return _get_room_posting_mop(profile_doc, allowed_modes)

    if allow_fallback:
        return allowed_modes[0]

    frappe.throw(
        _("Mode of Payment {0} is not configured for POS Profile {1}.").format(
            method or _("Unknown"), profile_doc.name
        )
    )


def _resolve_pos_customer(explicit_customer=None, profile_doc=None, allow_guest_fallback=False):
    """Resolve POS customer safely across ERPNext schema variants."""
    customer = explicit_customer
    if customer and frappe.db.exists("Customer", customer):
        return customer

    if profile_doc:
        profile_customer = cstr(profile_doc.get("customer") or "").strip()
        if profile_customer and frappe.db.exists("Customer", profile_customer):
            return profile_customer

    try:
        if frappe.db.has_column("POS Settings", "customer"):
            settings_customer = cstr(frappe.db.get_single_value("POS Settings", "customer") or "").strip()
            if settings_customer and frappe.db.exists("Customer", settings_customer):
                return settings_customer
    except Exception:
        pass  # POS Settings table absent in this ERPNext version — skip silently.

    if allow_guest_fallback:
        for walk_in in ("Guest", "Walk-in Customer", "Walk In Customer", "POS Customer", "Cash Customer"):
            if frappe.db.exists("Customer", walk_in):
                return walk_in

    return None


def _get_complimentary_discount(complimentary_name, bill_total, manual_discount=0):
    if not complimentary_name:
        return 0
    from rhohotel.rhocom_hotel.api.complimentary import get_complimentary_pos_discount

    return flt(get_complimentary_pos_discount(
        complimentary_name,
        bill_total,
        manual_discount=manual_discount,
        department="Restaurant",
    ))


def _redeem_complimentary(complimentary_name, pos_invoice_name, bill_total, manual_discount=0):
    if not complimentary_name:
        return None
    from rhohotel.rhocom_hotel.api.complimentary import redeem_complimentary_for_pos

    return redeem_complimentary_for_pos(
        complimentary_name,
        pos_invoice_name,
        bill_total,
        manual_discount=manual_discount,
        department="Restaurant",
    )


def _get_sent_to_kitchen_map(pos_invoice):
    """Return total kitchen-sent quantities by item code for a POS Invoice."""
    if not pos_invoice:
        return {}

    rows = frappe.db.sql(
        """
        SELECT
            kti.item_code,
            SUM(kti.quantity) AS total_qty
        FROM `tabKitchen Order Ticket` kt
        INNER JOIN `tabKitchen Order Ticket Item` kti ON kti.parent = kt.name
        WHERE kt.pos_invoice = %s
          AND kt.docstatus = 0
        GROUP BY kti.item_code
        """,
        (pos_invoice,),
        as_dict=1,
    )
    return {
        cstr(row.get("item_code")): flt(row.get("total_qty"))
        for row in rows
        if row.get("item_code")
    }


def _age_minutes_from(creation):
    """Return elapsed minutes using Frappe datetime parsing across versions."""
    if not creation:
        return 0
    return max(0, int((time_diff_in_seconds(now_datetime(), creation) or 0) / 60))


def _get_open_table_draft(table_name, exclude_invoice=None):
    """Return the draft POS Invoice currently occupying a service table."""
    table_name = _extract_table_display_name(table_name)
    if not table_name:
        return None

    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabPOS Invoice`
        WHERE docstatus = 0
          AND LOWER(TRIM(customer_name)) = LOWER(%s)
        ORDER BY creation DESC
        LIMIT 5
        """,
        (table_name,),
        as_dict=1,
    )
    for row in rows:
        if row.name != exclude_invoice:
            return row.name
    return None


def _ensure_table_not_occupied(table_display_name, existing_draft=None):
    """Prevent a second draft sale from being created for an occupied table."""
    if not table_display_name:
        return
    occupied = _get_open_table_draft(table_display_name, exclude_invoice=existing_draft)
    if occupied:
        frappe.throw(_("{0} already has a held sale. Resume it from Open Tables instead of creating a new sale.").format(table_display_name))


def _sync_draft_payment_row(pi):
    """Keep a single draft payment row in step with draft items/discount."""
    draft_total = flt(sum(flt(row.rate) * flt(row.qty) for row in (pi.get("items") or [])))
    payment_mode = None
    if pi.get("payments"):
        payment_mode = pi.payments[0].mode_of_payment
    payment_mode = payment_mode or "Cash"
    pi.set("payments", [])
    pi.append("payments", {
        "mode_of_payment": payment_mode,
        "amount": max(0, draft_total - flt(pi.discount_amount)),
    })


def _get_kitchen_ticket_statuses(pos_invoice):
    if not pos_invoice:
        return []
    rows = frappe.get_all(
        "Kitchen Order Ticket",
        filters={"pos_invoice": pos_invoice, "docstatus": 0},
        fields=["name", "status"],
    )
    return [r.status for r in rows]


@frappe.whitelist()
def get_pos_opening_profiles():
    """Return opening-entry modal setup data for current POS user."""
    user = frappe.session.user
    open_entry = _get_open_pos_entry(user)
    profiles = _get_user_pos_profiles(user)

    profile_rows = []
    for profile_name in profiles:
        try:
            profile_doc = frappe.get_doc("POS Profile", profile_name)
            payments = [
                row.mode_of_payment
                for row in (profile_doc.get("payments") or [])
                if row.mode_of_payment
            ]
            profile_rows.append(
                {
                    "name": profile_name,
                    "company": profile_doc.company,
                    "payments": payments,
                }
            )
        except Exception:
            # If a profile doc can't be loaded, still include its name
            profile_rows.append({"name": profile_name, "company": "", "payments": []})

    return {
        "current_user": user,
        "has_open_shift": bool(open_entry),
        "open_pos_opening_entry": open_entry.get("name") if open_entry else None,
        "open_pos_profile": open_entry.get("pos_profile") if open_entry else None,
        "profiles": profile_rows,
        "default_profile": None,
    }


@frappe.whitelist()
def create_pos_opening_entry(pos_profile=None, opening_cash=0):
    """Create and submit POS Opening Entry for current user."""
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw(_("Please login to open a POS shift."))

    existing = _get_open_pos_entry(user, pos_profile)
    if existing:
        return {
            "pos_opening_entry": existing.get("name"),
            "pos_profile": existing.get("pos_profile"),
            "already_open": True,
        }

    mapped_profiles = _get_user_pos_profiles(user)
    if not mapped_profiles:
        frappe.throw(_("No POS Profile is mapped to your user."))

    if not pos_profile:
        frappe.throw(_("Select a POS Profile before opening a shift."))

    if pos_profile not in mapped_profiles:
        frappe.throw(_("POS Profile {0} is not mapped to your user.").format(pos_profile))

    profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
    opening = frappe.new_doc("POS Opening Entry")
    opening.company = profile_doc.company or frappe.db.get_single_value("Global Defaults", "default_company")
    opening.user = user
    opening.pos_profile = pos_profile
    opening.period_start_date = now_datetime()

    payment_modes = [row.mode_of_payment for row in (profile_doc.get("payments") or []) if row.mode_of_payment]
    if not payment_modes:
        frappe.throw(_("POS Profile {0} has no payment modes configured.").format(pos_profile))

    cash_opening = flt(opening_cash)
    for mode in payment_modes:
        opening.append(
            "balance_details",
            {
                "mode_of_payment": mode,
                "opening_amount": cash_opening if mode == "Cash" else 0,
            },
        )

    try:
        opening.flags.ignore_permissions = True
        opening.insert()
        opening.submit()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS Opening Entry creation failed")
        frappe.throw(_("Failed to open POS shift. Please check POS profile setup."))

    return {
        "pos_opening_entry": opening.name,
        "pos_profile": pos_profile,
        "already_open": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Menu Items
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_menu_items(search=None, category=None):
    conditions = ["i.disabled = 0", "i.is_sales_item = 1"]
    args = []

    # Prefer the profile from the user's currently open shift so that a user
    # mapped to multiple terminals (e.g. Restaurant AND Laundry) gets the items
    # for the terminal they actually opened, not whichever profile was last modified.
    open_entry = _get_open_pos_entry(frappe.session.user)
    pos_profile = (open_entry or {}).get("pos_profile") or _get_user_pos_profile()
    if not pos_profile:
        return []

    profile = frappe.get_cached_doc("POS Profile", pos_profile)
    pos_warehouse = profile.warehouse
    price_list = profile.selling_price_list or "Standard Selling"

    allowed_item_groups = _get_allowed_item_groups_for_profile(pos_profile)
    if not allowed_item_groups:
        return []

    placeholders = ", ".join(["%s"] * len(allowed_item_groups))
    conditions.append("i.item_group IN ({0})".format(placeholders))
    args.extend(allowed_item_groups)

    if search:
        q = "%{0}%".format(frappe.utils.cstr(search).strip())
        conditions.append("(i.item_name LIKE %s OR i.item_code LIKE %s OR i.item_group LIKE %s)")
        args.extend([q, q, q])

    if category and category != "All Items":
        conditions.append("i.item_group = %s")
        args.append(category)

    where = " AND ".join(conditions)

    items = frappe.db.sql("""
        SELECT
            i.name AS item_code,
            i.item_name AS name,
            i.item_group AS category,
            COALESCE(ip.price_list_rate, i.standard_rate, 0) AS price,
            i.image,
            i.stock_uom AS uom,
            i.is_stock_item
        FROM `tabItem` i
        LEFT JOIN (
            SELECT
                item_code,
                MAX(price_list_rate) AS price_list_rate
            FROM `tabItem Price`
            WHERE selling = 1
              AND price_list = %s
            GROUP BY item_code
        ) ip ON ip.item_code = i.name
        WHERE {where}
        ORDER BY i.item_group, i.item_name
        LIMIT 500
    """.format(where=where), tuple([price_list] + args), as_dict=True)

    for item in items:
        if item.get("is_stock_item") and pos_warehouse:
            available_qty, is_stock_item, _ = get_stock_availability(
                item.get("item_code"),
                pos_warehouse
            )
            item["stock"] = available_qty
            item["actual_qty"] = available_qty
            item["available_qty"] = available_qty
        else:
            item["stock"] = 0
            item["actual_qty"] = 0
            item["available_qty"] = 0

    return items



@frappe.whitelist()
def get_pos_item_categories():
    """Return distinct item groups that have active sales items."""
    # Same profile resolution as get_pos_menu_items: prefer the open shift profile.
    open_entry = _get_open_pos_entry(frappe.session.user)
    pos_profile = (open_entry or {}).get("pos_profile") or _get_user_pos_profile()
    if not pos_profile:
        return []

    allowed_item_groups = _get_allowed_item_groups_for_profile(pos_profile)
    if not allowed_item_groups:
        return []

    where_parts = ["disabled = 0", "is_sales_item = 1", "item_group IS NOT NULL"]
    args = []

    placeholders = ", ".join(["%s"] * len(allowed_item_groups))
    where_parts.append(f"item_group IN ({placeholders})")
    args.extend(allowed_item_groups)

    where_clause = " AND ".join(where_parts)
    groups = frappe.db.sql(
        f"""
        SELECT DISTINCT item_group AS name
        FROM `tabItem`
        WHERE {where_clause}
        ORDER BY item_group
        """,
        tuple(args),
        as_dict=1,
    )
    return [g["name"] for g in groups]


# ─────────────────────────────────────────────────────────────────────────────
# Bill-To Search (guests + tables)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def search_pos_bill_to(query=""):
    from frappe.utils import cstr

    query = cstr(query or "").strip()
    like_query = "%{0}%".format(query)

    filters = ["c.disabled = 0"]
    args = []

    if query:
        filters.append("""
            (
                c.name LIKE %s
                OR c.customer_name LIKE %s
                OR IFNULL(c.email_id, '') LIKE %s
                OR IFNULL(c.mobile_no, '') LIKE %s
            )
        """)
        args.extend([like_query, like_query, like_query, like_query])

    customers = frappe.db.sql("""
        SELECT
            c.name AS id,
            c.name AS customer,
            COALESCE(NULLIF(c.customer_name, ''), c.name) AS name,
            c.email_id,
            c.mobile_no
        FROM `tabCustomer` c
        WHERE {filters}
        ORDER BY c.customer_name
        LIMIT 5
    """.format(filters=" AND ".join(filters)), tuple(args), as_dict=True)

    customer_names = [c.customer for c in customers]

    checkin_match_parts = []
    checkin_args = []

    if query:
        checkin_match_parts.append("""
            (
                ci.name LIKE %s
                OR ci.room_number LIKE %s
                OR ci.guest LIKE %s
                OR IFNULL(hg.hotel_guest_name, '') LIKE %s
                OR IFNULL(hg.phone_number, '') LIKE %s
                OR IFNULL(hg.email, '') LIKE %s
                OR IFNULL(hg.customer, '') LIKE %s
            )
        """)
        checkin_args.extend([like_query] * 7)

    if customer_names:
        placeholders = ", ".join(["%s"] * len(customer_names))
        checkin_match_parts.append(f"IFNULL(hg.customer, '') IN ({placeholders})")
        checkin_args.extend(customer_names)
        checkin_match_parts.append(f"ci.guest IN ({placeholders})")
        checkin_args.extend(customer_names)

    checkins = []
    if checkin_match_parts:
        checkins = frappe.db.sql("""
            SELECT
                ci.name AS check_in,
                ci.guest AS guest,
                ci.room_number AS room,
                r.room_type,
                COALESCE(NULLIF(hg.customer, ''), ci.guest) AS customer,
                COALESCE(NULLIF(hg.hotel_guest_name, ''), ci.guest) AS name,
                hg.email AS email_id,
                hg.phone_number AS mobile_no,
                ci.reservation_source AS payment_type
            FROM `tabHotel Room Check In` ci
            LEFT JOIN `tabHotel Guest` hg ON hg.name = ci.guest
            LEFT JOIN `tabHotel Room` r ON r.room_number = ci.room_number
            WHERE ci.status = 'Checked In'
              AND ci.docstatus = 1
              AND ({matches})
            ORDER BY ci.modified DESC
            LIMIT 10
        """.format(matches=" OR ".join(checkin_match_parts)), tuple(checkin_args), as_dict=True)

    results = []

    seen_customers = set()
    seen_checkins = set()
    seen_active_tables = set()

    for ci in checkins:
        if ci.check_in in seen_checkins:
            continue
        seen_checkins.add(ci.check_in)
        if ci.customer:
            seen_customers.add(ci.customer)

        results.append({
            "id": ci.check_in,
            "check_in": ci.check_in,
            "customer": ci.customer,
            "guest": ci.guest,
            "name": ci.name,
            "room": ci.room,
            "room_type": ci.room_type,
            "email": ci.email_id,
            "phone": ci.mobile_no,
            "type": "Checked In",
            "payment_type": ci.payment_type,
        })

    for c in customers:
        if c.customer in seen_customers:
            continue

        active_table_invoice = _get_open_table_draft(c.name)
        active_table_bill = 0
        if active_table_invoice:
            seen_active_tables.add(active_table_invoice)
            active_table_bill = frappe.db.get_value("POS Invoice", active_table_invoice, "grand_total") or 0

        results.append({
            "id": c.customer,
            "customer": c.customer,
            "name": c.name,
            "room": None,
            "email": c.email_id,
            "phone": c.mobile_no,
            "type": "Active Table" if active_table_invoice else "Customer",
            "active_table_invoice": active_table_invoice,
            "active_table_bill": flt(active_table_bill),
        })

    if query and _extract_table_display_name(query):
        open_tables = frappe.db.sql("""
            SELECT
                pi.name AS invoice,
                pi.customer_name AS table_name,
                pi.grand_total AS bill
            FROM `tabPOS Invoice` pi
            WHERE pi.docstatus = 0
              AND (
                pi.customer_name LIKE 'Table %%'
                OR pi.customer_name LIKE 'Bar %%'
                OR pi.customer_name LIKE 'Pool%%'
              )
              AND pi.customer_name LIKE %s
            ORDER BY pi.modified DESC
            LIMIT 5
        """, (like_query,), as_dict=1)

        for table in open_tables:
            if table.invoice in seen_active_tables:
                continue
            results.append({
                "id": table.invoice,
                "customer": table.table_name,
                "name": table.table_name,
                "room": None,
                "email": None,
                "phone": None,
                "type": "Active Table",
                "active_table_invoice": table.invoice,
                "active_table_bill": flt(table.bill),
            })

    return results[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Occupied Rooms (for Post to Room)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_occupied_rooms_for_pos(search=None):
    """Return rooms with active check-ins for the Post to Room feature."""
    conditions = ["ci.status = 'Checked In'", "ci.docstatus = 1"]
    args = []

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(ci.room_number LIKE %s OR ci.guest LIKE %s OR ci.name LIKE %s)")
        args.extend([q, q, q])

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT
            ci.name AS check_in,
            ci.room_number AS room,
            r.room_type AS type,
            ci.guest,
            COALESCE(ci.total_outstanding_amount, 0) AS balance,
            ci.reservation_source AS payment_type
        FROM `tabHotel Room Check In` ci
        LEFT JOIN `tabHotel Room` r ON r.room_number = ci.room_number
        WHERE {where}
        ORDER BY ci.room_number
        LIMIT 100
    """, tuple(args), as_dict=1)

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Create POS Invoice (Cash / Card / POS terminal payments)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_pos_invoice(items, mode_of_payment="Cash", customer=None,
                        service_charge=0, kitchen_note=None, pos_profile=None, discount_amount=0,
                        existing_draft=None, complimentary_name=None):
    """Create and submit a POS Invoice for non-room-posting settlements."""
    import json

    try:
        items = json.loads(items) if isinstance(items, str) else items
        if not items:
            frappe.throw(_("No items in cart"))

        table_display_name = _extract_table_display_name(customer)
        _ensure_table_not_occupied(table_display_name, existing_draft=existing_draft)

        company = frappe.db.get_single_value("Global Defaults", "default_company") or ""

        # Resolve POS profile from current user to match opening-entry/profile validations
        if not pos_profile:
            pos_profile = _get_user_pos_profile()
        if not pos_profile:
            frappe.throw(_("No POS Profile is mapped to your user."))

        pos_opening_entry = _get_open_pos_entry(frappe.session.user, pos_profile)
        if not pos_opening_entry:
            frappe.throw(_("No open POS Opening Entry found for your user. Please open a shift before charging."))

        # Always align profile to the currently open shift to satisfy POS invoice validation.
        pos_profile = pos_opening_entry.get("pos_profile") or pos_profile

        # Ensure mode of payment is valid for the resolved POS profile.
        profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
        allowed_modes = [row.mode_of_payment for row in (profile_doc.get("payments") or []) if row.mode_of_payment]
        if not allowed_modes:
            frappe.throw(_("POS Profile {0} has no payment modes configured.").format(pos_profile))
        mode_of_payment = _resolve_pos_payment_mode(mode_of_payment, profile_doc, allowed_modes)

        if table_display_name:
            customer = None  # force walk-in resolution

        customer = _resolve_pos_customer(customer, profile_doc=profile_doc, allow_guest_fallback=True)

        if not customer:
            frappe.throw(_("Set a valid default customer on POS Profile {0}. Optionally configure POS Settings.customer if available in your ERPNext version.").format(pos_profile))

        updating_existing_draft = False
        if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
            pi = frappe.get_doc("POS Invoice", existing_draft)
            if pi.docstatus != 0:
                frappe.throw(_("Only draft POS Invoices can be completed from a held sale."))
            updating_existing_draft = True
            pi.set("items", [])
            pi.set("payments", [])
        else:
            pi = frappe.new_doc("POS Invoice")

        pi.customer = customer
        pi.company = company
        pi.posting_date = nowdate()
        pi.pos_profile = pos_profile
        pi.remarks = kitchen_note or ""

        if _has_pos_opening_entry_on_invoice():
            pi.pos_opening_entry = pos_opening_entry.get("name")

        for it in items:
            pi.append("items", {
                "item_code": it.get("item_code") or it.get("id"),
                "qty": flt(it.get("qty", 1)),
                "rate": flt(it.get("price", 0)),
            })

        _items_total = flt(sum(flt(i.get("price", 0)) * flt(i.get("qty", 1)) for i in items)) + flt(service_charge)
        manual_discount = flt(discount_amount)
        complimentary_discount = _get_complimentary_discount(complimentary_name, _items_total, manual_discount)
        total_discount = min(_items_total, manual_discount + complimentary_discount)
        pi.discount_amount = total_discount
        if total_discount > 0:
            pi.apply_discount_on = "Grand Total"
        pi.append("payments", {
            "mode_of_payment": mode_of_payment,
            "amount": max(0, _items_total - total_discount),
        })

        pi.flags.ignore_permissions = True
        pi.set_missing_values()
        if updating_existing_draft:
            pi.save()
        else:
            pi.insert()
        pi.submit()
        # Override customer_name AFTER submit: ERPNext's validate() inside insert/submit
        # calls set_missing_values() again which resets customer_name to the linked
        # Customer's name (e.g. "Walk In"). frappe.db.set_value bypasses validation.
        if table_display_name:
            frappe.db.set_value("POS Invoice", pi.name, "customer_name",
                                table_display_name, update_modified=False)
        complimentary = _redeem_complimentary(complimentary_name, pi.name, _items_total, manual_discount)
        frappe.db.commit()
    except Exception as e:
        safe_items = []
        for it in (items or []):
            safe_items.append({
                "item_code": it.get("item_code") or it.get("id"),
                "qty": flt(it.get("qty", 1)),
                "rate": flt(it.get("price", 0)),
            })

        context = {
            "user": frappe.session.user,
            "pos_profile": pos_profile,
            "mode_of_payment": mode_of_payment,
            "customer": customer,
            "service_charge": flt(service_charge),
            "item_count": len(safe_items),
            "items": safe_items,
            "error": cstr(e),
            "error_type": type(e).__name__,
        }
        frappe.log_error(
            f"{frappe.get_traceback()}\n\nContext:\n{frappe.as_json(context)}",
            "POS create_pos_invoice failed",
        )
        if isinstance(e, frappe.ValidationError):
            raise
        frappe.throw(_("Failed to create POS Invoice: {0}").format(cstr(e)))

    return {"pos_invoice": pi.name, "grand_total": flt(pi.grand_total), "complimentary": complimentary}


# ─────────────────────────────────────────────────────────────────────────────
# Post to Room
# ─────────────────────────────────────────────────────────────────────────────

def _derive_invoice_source(pos_profile_name):
    """Map a POS Profile name to a human-readable invoice source label."""
    name = (pos_profile_name or "").lower()
    if "laundry" in name:
        return "Laundry"
    if "bar" in name:
        return "Bar"
    if "mini" in name or "mart" in name:
        return "Mini-Mart"
    if "room service" in name or "room_service" in name:
        return "Room Service"
    if "spa" in name:
        return "Spa"
    return "Restaurant"


@frappe.whitelist()
def post_bill_to_room(items, check_in, service_charge=0, discount_amount=0, narration=None, kitchen_note=None, pos_profile=None, existing_draft=None, complimentary_name=None):
    """Create a Sales Invoice linked to a Hotel Room Check In folio, then immediately
    create and consolidate a POS Invoice against the open shift so the transaction
    appears in shift reports without waiting for the end-of-shift consolidation job."""
    import json

    items = json.loads(items) if isinstance(items, str) else items
    if not items:
        frappe.throw(_("No items in cart"))

    existing_draft_doc = None
    if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
        existing_draft_doc = frappe.get_doc("POS Invoice", existing_draft)
        if existing_draft_doc.docstatus != 0:
            frappe.throw(_("Only draft POS Invoices can be completed from a held sale."))

    if not frappe.db.exists("Hotel Room Check In", check_in):
        frappe.throw(_("Check-in {0} not found").format(check_in))

    ci = frappe.get_doc("Hotel Room Check In", check_in)
    if ci.status != "Checked In":
        frappe.throw(_("Check-in {0} is not active").format(check_in))

    company = frappe.db.get_single_value("Global Defaults", "default_company") or ""

    # Resolve customer via billing routing engine if canonical reservation is linked
    customer = None
    canonical_res_name = getattr(ci, "canonical_reservation", None)

    if canonical_res_name and frappe.db.exists("Hotel Reservation", canonical_res_name):
        try:
            from rhohotel.rhocom_hotel.utils.billing_routing import resolve_payer
            # Determine charge category from items (use first item's group or default)
            charge_category = "Restaurant"  # POS bills are typically F&B
            payer_info = resolve_payer(canonical_res_name, charge_category=charge_category)
            payer_type = payer_info.get("payer_type", "Guest")
            if payer_type != "Internal (Cost Centre)":
                customer = payer_info.get("customer")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Billing routing failed in post_bill_to_room")

    # Fallback: resolve from guest record
    if not customer:
        if ci.guest:
            try:
                guest_doc = frappe.get_doc("Hotel Guest", ci.guest)
                customer = guest_doc.customer
            except Exception:
                pass
    if not customer:
        customer = ci.guest or "Guest"

    si = frappe.new_doc("Sales Invoice")
    si.customer = customer
    si.company = company
    si.posting_date = nowdate()
    si.custom_hotel_room_check_in = check_in

    remarks_parts = []
    if kitchen_note:
        remarks_parts.append(kitchen_note)
    if narration:
        remarks_parts.append(narration)
    if remarks_parts:
        si.remarks = " | ".join(remarks_parts)

    for it in items:
        si.append("items", {
            "item_code": it.get("item_code") or it.get("id"),
            "qty": flt(it.get("qty", 1)),
            "rate": flt(it.get("price", 0)),
        })

    # Service charge
    svc = flt(service_charge)
    if svc > 0:
        svc_item = frappe.db.get_value("Item", {"item_name": ["like", "%service charge%"]}, "name")
        if svc_item:
            si.append("items", {"item_code": svc_item, "qty": 1, "rate": svc})

    items_total = flt(sum(
        flt(it.get("price", 0)) * flt(it.get("qty", 1)) for it in items
    )) + flt(service_charge)
    manual_discount = flt(discount_amount)
    complimentary_discount = _get_complimentary_discount(complimentary_name, items_total, manual_discount)

    # Discount
    disc = min(items_total, manual_discount + complimentary_discount)
    if disc > 0:
        si.discount_amount = disc
        si.apply_discount_on = "Grand Total"

    _source = _derive_invoice_source(pos_profile)
    if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
        si.custom_invoice_source = _source

    try:
        si.flags.ignore_permissions = True
        si.set_missing_values()
        si.insert()
        si.submit()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Post to Room invoice creation failed")
        frappe.throw(_("Failed to post bill to room. Check item/customer configuration."))

    # ── Immediately create & consolidate a POS Invoice for shift tracking ──
    pos_invoice_name = None
    try:
        resolved_pos_profile = pos_profile or _get_user_pos_profile()
        if resolved_pos_profile:
            pos_opening_entry = _get_open_pos_entry(frappe.session.user, resolved_pos_profile)
            if pos_opening_entry:
                resolved_pos_profile = pos_opening_entry.get("pos_profile") or resolved_pos_profile
                profile_doc = frappe.get_cached_doc("POS Profile", resolved_pos_profile)
                allowed_modes = [
                    row.mode_of_payment
                    for row in (profile_doc.get("payments") or [])
                    if row.mode_of_payment
                ]
                # Use a room-posting MOP so the POS shift does not count this
                # as cash collected — the charge lives on the room folio.
                mode_of_payment = _get_room_posting_mop(profile_doc, allowed_modes)

                updating_existing_draft = False
                if existing_draft_doc:
                    pi = existing_draft_doc
                    updating_existing_draft = True
                    pi.set("items", [])
                    pi.set("payments", [])
                else:
                    pi = frappe.new_doc("POS Invoice")

                pi.customer = _resolve_pos_customer(
                    customer, profile_doc=profile_doc, allow_guest_fallback=True
                )
                pi.company = company
                pi.posting_date = nowdate()
                pi.pos_profile = resolved_pos_profile
                pi.custom_hotel_room_check_in = check_in

                if _has_pos_opening_entry_on_invoice():
                    pi.pos_opening_entry = pos_opening_entry.get("name")

                if si.remarks:
                    pi.remarks = si.remarks

                for it in items:
                    pi.append("items", {
                        "item_code": it.get("item_code") or it.get("id"),
                        "qty": flt(it.get("qty", 1)),
                        "rate": flt(it.get("price", 0)),
                    })

                net_amount = max(0.0, items_total - disc)

                if disc > 0:
                    pi.discount_amount = disc
                    pi.apply_discount_on = "Grand Total"

                pi.append("payments", {
                    "mode_of_payment": mode_of_payment,
                    "amount": net_amount,
                })

                pi.flags.ignore_permissions = True
                pi.set_missing_values()
                if updating_existing_draft:
                    pi.save()
                else:
                    pi.insert()
                pi.submit()

                # Mark as immediately consolidated — the room folio Sales Invoice
                # serves as the consolidated invoice; no end-of-shift re-processing needed.
                frappe.db.set_value("POS Invoice", pi.name, "consolidated_invoice", si.name)
                _redeem_complimentary(complimentary_name, pi.name, items_total, manual_discount)
                frappe.db.commit()
                pos_invoice_name = pi.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Post to Room POS Invoice consolidation failed")
        # Non-fatal: the room folio Sales Invoice was already committed; continue.

    if complimentary_name and not pos_invoice_name:
        _redeem_complimentary(
            complimentary_name,
            _("Sales Invoice {0}").format(si.name),
            items_total,
            manual_discount,
        )
        frappe.db.commit()

    return {
        "sales_invoice": si.name,
        "pos_invoice": pos_invoice_name,
        "grand_total": flt(si.grand_total),
        "check_in": check_in,
        "room": ci.room_number,
    }


@frappe.whitelist()
def save_pos_draft_invoice(items, customer=None, service_charge=0, kitchen_note=None, pos_profile=None, discount_amount=0, existing_draft=None):
    """Create a draft POS Invoice for suspended/held sales."""
    import json

    items = json.loads(items) if isinstance(items, str) else items
    if not items:
        frappe.throw(_("No items in cart"))

    # Preserve table/bar/pool name as customer_name display field (needed early for merge logic)
    table_display_name = _extract_table_display_name(customer)

    items_to_save = list(items)
    _ensure_table_not_occupied(table_display_name, existing_draft=existing_draft)

    company = frappe.db.get_single_value("Global Defaults", "default_company") or ""

    if not pos_profile:
        pos_profile = _get_user_pos_profile()
    if not pos_profile:
        frappe.throw(_("No POS Profile is mapped to your user."))

    profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)

    if table_display_name:
        customer = None  # force walk-in resolution

    customer = _resolve_pos_customer(customer, profile_doc=profile_doc, allow_guest_fallback=True)
    if not customer:
        frappe.throw(_("Set a valid default customer on POS Profile {0}. Optionally configure POS Settings.customer if available in your ERPNext version.").format(pos_profile))

    updating_existing = False
    if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
        pi = frappe.get_doc("POS Invoice", existing_draft)
        if pi.docstatus != 0:
            frappe.throw(_("Only draft POS Invoices can be updated."))
        updating_existing = True
        pi.set("items", [])
        pi.set("payments", [])
    else:
        pi = frappe.new_doc("POS Invoice")

    pi.customer = customer
    pi.company = company
    pi.posting_date = nowdate()
    pi.pos_profile = pos_profile
    pi.remarks = kitchen_note or ""

    for it in items_to_save:
        pi.append("items", {
            "item_code": it.get("item_code") or it.get("id"),
            "qty": flt(it.get("qty", 1)),
            "rate": flt(it.get("price", 0)),
        })

    # Keep one payment row to satisfy POS validations while still saving as draft.
    _draft_total = flt(sum(flt(i.get("price", 0)) * flt(i.get("qty", 1)) for i in items_to_save))
    pi.discount_amount = flt(discount_amount)
    pi.append("payments", {
        "mode_of_payment": "Cash",
        "amount": max(0, _draft_total - flt(discount_amount)),
    })

    try:
        pi.flags.ignore_permissions = True
        pi.set_missing_values()
        if updating_existing:
            pi.save()
        else:
            pi.insert()
        # Override customer_name AFTER insert: ERPNext's validate() inside insert
        # calls set_missing_values() again which resets customer_name to the linked
        # Customer's name (e.g. "Walk In"). frappe.db.set_value bypasses validation.
        if table_display_name:
            frappe.db.set_value("POS Invoice", pi.name, "customer_name",
                                table_display_name, update_modified=False)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS draft invoice creation failed")
        frappe.throw(_("Failed to save draft order. Please check POS profile and opening entry."))

    return {
        "pos_invoice": pi.name,
        "grand_total": flt(pi.grand_total),
        "status": "Draft",
    }


@frappe.whitelist()
def transfer_pos_table_draft(invoice_name, target_table):
    """Move a draft table order to an empty table/service point."""
    target_table = cstr(target_table).strip()
    if not target_table or not _extract_table_display_name(target_table):
        frappe.throw(_("Enter a valid table, bar, or pool service point."))

    if not frappe.db.exists("POS Invoice", invoice_name):
        frappe.throw(_("Invoice {0} not found").format(invoice_name))

    occupied = _get_open_table_draft(target_table, exclude_invoice=invoice_name)
    if occupied:
        frappe.throw(_("{0} already has an active bill. Use Merge instead of Transfer.").format(target_table))

    pi = frappe.get_doc("POS Invoice", invoice_name)
    if pi.docstatus != 0:
        frappe.throw(_("Only draft table bills can be transferred."))

    try:
        pi.flags.ignore_permissions = True
        pi.save()
        frappe.db.set_value("POS Invoice", pi.name, "customer_name", target_table, update_modified=False)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS table transfer failed")
        frappe.throw(_("Failed to transfer table bill."))

    return {"pos_invoice": pi.name, "target_table": target_table}


@frappe.whitelist()
def merge_pos_table_drafts(source_invoice, target_invoice):
    """Merge one open table draft into another and delete the source draft."""
    if source_invoice == target_invoice:
        frappe.throw(_("Select two different table bills to merge."))

    if not frappe.db.exists("POS Invoice", source_invoice):
        frappe.throw(_("Source invoice {0} not found").format(source_invoice))
    if not frappe.db.exists("POS Invoice", target_invoice):
        frappe.throw(_("Target invoice {0} not found").format(target_invoice))

    source = frappe.get_doc("POS Invoice", source_invoice)
    target = frappe.get_doc("POS Invoice", target_invoice)
    if source.docstatus != 0 or target.docstatus != 0:
        frappe.throw(_("Only draft table bills can be merged."))

    target_table = _extract_table_display_name(target.customer_name or "")
    if not target_table:
        frappe.throw(_("Target invoice is not an open table bill."))

    merged = {}
    for row in target.items:
        merged[row.item_code] = {
            "item_code": row.item_code,
            "qty": flt(row.qty),
            "rate": flt(row.rate),
        }

    for row in source.items:
        if row.item_code in merged:
            merged[row.item_code]["qty"] += flt(row.qty)
        else:
            merged[row.item_code] = {
                "item_code": row.item_code,
                "qty": flt(row.qty),
                "rate": flt(row.rate),
            }

    target.set("items", [])
    for row in merged.values():
        target.append("items", row)

    notes = [cstr(target.remarks or "").strip(), cstr(source.remarks or "").strip()]
    target.remarks = " | ".join([n for n in notes if n])
    target.discount_amount = flt(target.discount_amount) + flt(source.discount_amount)
    _sync_draft_payment_row(target)

    try:
        target.flags.ignore_permissions = True
        source.flags.ignore_permissions = True
        target.save()
        frappe.db.set_value("POS Invoice", target.name, "customer_name", target_table, update_modified=False)
        frappe.db.set_value(
            "Kitchen Order Ticket",
            {"pos_invoice": source.name, "docstatus": 0},
            {"pos_invoice": target.name, "table_or_room": target_table},
            update_modified=False,
        )
        source.delete()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS table merge failed")
        frappe.throw(_("Failed to merge table bills."))

    return {
        "merged_into": target.name,
        "deleted_invoice": source.name,
        "target_table": target_table,
        "grand_total": flt(target.grand_total),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Draft POS Invoices
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_draft_pos_invoices(search=None, service_point=None, cashier=None):
    """Return draft (docstatus=0) POS invoices for the Draft Orders modal."""
    conditions = ["pi.docstatus = 0"]
    args = []

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(pi.name LIKE %s OR pi.customer LIKE %s OR pi.customer_name LIKE %s)")
        args.extend([q, q, q])

    if not cashier or cashier == "__current_user":
        cashier = frappe.session.user

    if cashier:
        conditions.append("pi.owner = %s")
        args.append(cashier)

    where = " AND ".join(conditions)

    drafts = frappe.db.sql(f"""
        SELECT
            pi.name AS invoice,
            COALESCE(NULLIF(pi.customer_name, ''), pi.customer) AS customer,
            pi.pos_profile,
            pi.grand_total AS amount,
            pi.posting_date,
            pi.creation,
            pi.owner AS cashier,
            pi.remarks AS note,
            COUNT(pit.name) AS item_count
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabPOS Invoice Item` pit ON pit.parent = pi.name
        WHERE {where}
        GROUP BY pi.name
        ORDER BY pi.creation DESC
        LIMIT 50
    """, tuple(args), as_dict=1)

    # Fetch items for each draft
    for d in drafts:
        d["items"] = frappe.db.sql("""
            SELECT item_name AS name, qty
            FROM `tabPOS Invoice Item`
            WHERE parent = %s
        """, d["invoice"], as_dict=1)
        kitchen_statuses = _get_kitchen_ticket_statuses(d["invoice"])
        blocking_statuses = [s for s in kitchen_statuses if s and s != "Pending"]
        d["kitchen_statuses"] = kitchen_statuses
        d["can_delete"] = not blocking_statuses
        d["delete_block_reason"] = (
            _("Kitchen has already started preparing this order.") if blocking_statuses else ""
        )
        age = _age_minutes_from(d.get("creation"))
        d["age_minutes"] = age
        h, m = divmod(age, 60)
        d["age"] = f"{h}h {m}m" if h else f"{m}m"
        d["service_point"] = d.get("pos_profile") or "—"

    return drafts


@frappe.whitelist()
def get_draft_pos_stats(cashier=None):
    """Return stat card values for the Draft Orders modal."""
    filters = {"docstatus": 0}
    if not cashier or cashier == "__current_user":
        cashier = frappe.session.user
    if cashier:
        filters["owner"] = cashier

    total = frappe.db.count("POS Invoice", filters)

    conditions = ["docstatus = 0"]
    args = []
    if cashier:
        conditions.append("owner = %s")
        args.append(cashier)
    where = " AND ".join(conditions)

    total_value = frappe.db.sql(f"""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabPOS Invoice` WHERE {where}
    """, tuple(args))[0][0] or 0
    oldest_creation = frappe.db.sql(f"""
        SELECT MIN(creation)
        FROM `tabPOS Invoice` WHERE {where}
    """, tuple(args))[0][0]
    oldest = _age_minutes_from(oldest_creation)

    return {
        "total_drafts": total,
        "total_value": flt(total_value),
        "oldest_minutes": int(oldest),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POS Invoice List
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_invoices(search=None, outlet=None, method=None, status=None,
                     page_length=50, start=0):
    """Return paginated POS invoices with optional filters."""
    conditions = ["pi.docstatus >= 0"]
    args = []

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(pi.name LIKE %s OR pi.customer LIKE %s)")
        args.extend([q, q])

    if status:
        if status in ("Draft", "Posted"):
            conditions.append("pi.docstatus = 0")
        elif status == "Paid":
            conditions.append("pi.docstatus = 1")
        elif status == "Void":
            conditions.append("pi.docstatus = 2")

    if outlet:
        conditions.append("pi.pos_profile = %s")
        args.append(cstr(outlet).strip())

    where = " AND ".join(conditions)

    invoices = frappe.db.sql(f"""
        SELECT
            pi.name AS invoice_no,
            COALESCE(NULLIF(pi.customer_name, ''), pi.customer) AS customer,
            pi.grand_total,
            pi.posting_date,
            pi.owner AS cashier,
            pi.pos_profile AS terminal,
            pi.docstatus,
            pi.status AS invoice_status,
            GROUP_CONCAT(DISTINCT pip.mode_of_payment ORDER BY pip.mode_of_payment SEPARATOR ', ') AS payment_method,
            CASE
                WHEN pi.docstatus = 0 THEN 'Draft'
                WHEN pi.docstatus = 2 THEN 'Void'
                WHEN pi.status = 'Consolidated' THEN 'Consolidated'
                ELSE 'Paid'
            END AS status
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabSales Invoice Payment` pip ON pip.parent = pi.name
        WHERE {where}
        GROUP BY pi.name
        {"HAVING payment_method LIKE %s" if method else ""}
        ORDER BY pi.creation DESC
        LIMIT %s OFFSET %s
    """, tuple(args) + ((f"%{cstr(method).strip()}%",) if method else tuple()) + (int(page_length), int(start)), as_dict=1)

    return invoices


@frappe.whitelist()
def cancel_pos_invoice(invoice_name, reason=None):
    """Cancel a submitted POS Invoice from the manager invoice list."""
    if not frappe.db.exists("POS Invoice", invoice_name):
        frappe.throw(_("Invoice {0} not found").format(invoice_name))

    allowed_roles = {
        "System Manager",
        "Accounts Manager",
        "POS Manager",
        "Restaurant Manager",
        "Hotel Manager",
        "Front Desk Manager",
    }
    user_roles = set(frappe.get_roles(frappe.session.user))
    has_cancel_permission = frappe.has_permission("POS Invoice", "cancel", invoice_name)
    if not (allowed_roles & user_roles or has_cancel_permission):
        frappe.throw(_("You do not have permission to cancel POS invoices."))

    pi = frappe.get_doc("POS Invoice", invoice_name)
    if pi.docstatus != 1:
        frappe.throw(_("Only submitted POS invoices can be cancelled."))

    try:
        linked_sales_invoice = cstr(pi.get("consolidated_invoice") or "")

        # For consolidated invoices the linked Sales Invoice is locked by a
        # POS Closing Entry and cannot be cancelled directly.  Instead we
        # clear the in-memory field so ERPNext's before_cancel check is
        # bypassed, cancel the POS Invoice (which reverses its own GL
        # entries), and leave a comment on the Sales Invoice for accounting.
        if linked_sales_invoice and frappe.db.exists("Sales Invoice", linked_sales_invoice):
            si_docstatus = frappe.db.get_value("Sales Invoice", linked_sales_invoice, "docstatus")
            if si_docstatus == 1:
                # Note on the Sales Invoice so accounting knows to reconcile.
                si = frappe.get_doc("Sales Invoice", linked_sales_invoice)
                note = _("POS Invoice {0} was cancelled from the POS manager interface. "
                         "This Sales Invoice may need manual adjustment.").format(invoice_name)
                if reason:
                    note += " " + _("Reason: {0}").format(cstr(reason))
                si.add_comment("Comment", note)
                # Clear in-memory only — bypasses before_cancel closing-entry check.
                pi.consolidated_invoice = None

        if reason:
            pi.add_comment("Comment", _("Cancelled from POS manager: {0}").format(cstr(reason)))
        pi.flags.ignore_permissions = True
        # ERPNext's POS Invoice.on_cancel() sets ignore_linked_doctypes to
        # ["Payment Ledger Entry", "Serial and Batch Bundle"], which is called
        # by Frappe BEFORE check_no_back_links_exist() inside _cancel().
        # We monkey-patch on_cancel on the instance so our extra doctype
        # ("POS Invoice Merge Log") is appended after the original runs.
        _orig_on_cancel = pi.on_cancel
        def _patched_on_cancel():
            _orig_on_cancel()
            # ERPNext sets ignore_linked_doctypes to ["Payment Ledger Entry",
            # "Serial and Batch Bundle"] inside on_cancel.  Append the extra
            # doctypes that reference POS Invoice via static or dynamic links:
            #   - POS Invoice Reference (child of both Merge Log and Closing Entry)
            #   - Sales Invoice Item    (consolidated SI items reference back to POS Invoice)
            #   - Kitchen Order Ticket  (pos_invoice field)
            # Also include the parent types reported in error messages (line 314 check):
            #   - POS Invoice Merge Log / POS Closing Entry / Sales Invoice
            extra = [
                "POS Invoice Reference",
                "POS Invoice Merge Log",
                "POS Closing Entry",
                "Sales Invoice Item",
                "Sales Invoice",
                "Kitchen Order Ticket",
            ]
            ignored = list(getattr(pi, "ignore_linked_doctypes", None) or [])
            for e in extra:
                if e not in ignored:
                    ignored.append(e)
            pi.ignore_linked_doctypes = ignored
        pi.on_cancel = _patched_on_cancel
        pi.cancel()
        frappe.db.commit()
    except frappe.ValidationError as exc:
        frappe.db.rollback()
        message = cstr(exc) or _("POS invoice could not be cancelled because Frappe validation blocked it.")
        frappe.throw(_("Failed to cancel POS invoice {0}: {1}").format(invoice_name, message))
    except Exception as exc:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "POS invoice cancellation failed")
        frappe.throw(_("Failed to cancel POS invoice: {0}").format(cstr(exc)))

    return {"invoice": invoice_name, "cancelled": invoice_name}


@frappe.whitelist()
def get_pos_invoice_stats():
    """Return stat card data for the POS Invoice List page."""
    today = nowdate()

    today_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPOS Invoice`
        WHERE posting_date = %s AND docstatus = 1
    """, today)[0][0] or 0

    today_value = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabPOS Invoice`
        WHERE posting_date = %s AND docstatus = 1
    """, today)[0][0] or 0

    room_posted = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSales Invoice`
        WHERE custom_hotel_room_check_in IS NOT NULL
          AND custom_hotel_room_check_in != ''
          AND posting_date = %s AND docstatus = 1
    """, today)[0][0] or 0

    voided = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPOS Invoice`
        WHERE docstatus = 2 AND posting_date = %s
    """, today)[0][0] or 0

    return {
        "today_count": int(today_count),
        "today_value": flt(today_value),
        "room_posted": int(room_posted),
        "voided": int(voided),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POS Manager Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_closed_shifts(page_length=20, start=0, date_from=None, date_to=None,
                      terminal=None, cashier=None, has_attachment=None):
    """Return recent POS Closing Entries with optional filters and attachment info."""
    conditions = ["ce.docstatus = 1"]
    args = []

    if date_from:
        conditions.append("ce.posting_date >= %s")
        args.append(cstr(date_from).strip())
    if date_to:
        conditions.append("ce.posting_date <= %s")
        args.append(cstr(date_to).strip())
    if terminal:
        conditions.append("ce.pos_profile = %s")
        args.append(cstr(terminal).strip())
    if cashier:
        conditions.append("ce.user = %s")
        args.append(cstr(cashier).strip())
    if has_attachment:
        conditions.append("f.name IS NOT NULL")

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT
            ce.name,
            ce.posting_date,
            ce.pos_profile,
            ce.user,
            ce.period_start_date,
            ce.period_end_date,
            ce.grand_total,
            ce.net_total,
            f.file_name,
            f.file_url
        FROM `tabPOS Closing Entry` ce
        LEFT JOIN `tabFile` f
            ON f.attached_to_doctype = 'POS Closing Entry'
            AND f.attached_to_name = ce.name
        WHERE {where}
        ORDER BY ce.creation DESC
        LIMIT %s OFFSET %s
    """, tuple(args) + (int(page_length), int(start)), as_dict=1)

    # Also return filter options (distinct terminals + cashiers) for dropdowns
    terminals = frappe.db.sql("""
        SELECT DISTINCT pos_profile FROM `tabPOS Closing Entry`
        WHERE docstatus = 1 AND pos_profile IS NOT NULL
        ORDER BY pos_profile
    """, as_list=1)

    cashiers = frappe.db.sql("""
        SELECT DISTINCT user FROM `tabPOS Closing Entry`
        WHERE docstatus = 1 AND user IS NOT NULL
        ORDER BY user
    """, as_list=1)

    return {
        "rows": rows,
        "terminals": [r[0] for r in terminals],
        "cashiers": [r[0] for r in cashiers],
    }


@frappe.whitelist()
def get_closed_shift_detail(closing_entry):
    """Return full detail for one POS Closing Entry (header + payments + attachment)."""
    if not frappe.db.exists("POS Closing Entry", closing_entry):
        frappe.throw(_("Closing Entry {0} not found").format(closing_entry))

    ce = frappe.db.get_value(
        "POS Closing Entry", closing_entry,
        ["name", "posting_date", "pos_profile", "user",
         "period_start_date", "period_end_date",
         "grand_total", "net_total"],
        as_dict=1,
    )

    payments = frappe.db.sql("""
        SELECT mode_of_payment, opening_amount, expected_amount, closing_amount, difference
        FROM `tabPOS Closing Entry Detail`
        WHERE parent = %s
        ORDER BY idx
    """, closing_entry, as_dict=1)

    bills = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPOS Invoice`
        WHERE pos_profile = %s AND owner = %s AND docstatus = 1
          AND posting_date = %s
    """, (ce.pos_profile, ce.user, ce.posting_date))[0][0] or 0

    voids = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPOS Invoice`
        WHERE pos_profile = %s AND owner = %s AND docstatus = 2
          AND posting_date = %s
    """, (ce.pos_profile, ce.user, ce.posting_date))[0][0] or 0

    attachment = frappe.db.get_value(
        "File",
        {"attached_to_doctype": "POS Closing Entry", "attached_to_name": closing_entry},
        ["file_name", "file_url"],
        as_dict=1,
    )

    return {
        **ce,
        "bills_processed": bills,
        "voided_count": voids,
        "payments": payments,
        "attachment": attachment or None,
    }


@frappe.whitelist()
def get_shift_difference_log(page_length=50, start=0, date_from=None, date_to=None,
                              terminal=None, status=None):
    """Return POS Closing Entries that have at least one payment difference != 0."""
    conditions = ["ce.docstatus = 1"]
    args = []

    if date_from:
        conditions.append("ce.posting_date >= %s")
        args.append(cstr(date_from).strip())
    if date_to:
        conditions.append("ce.posting_date <= %s")
        args.append(cstr(date_to).strip())
    if terminal:
        conditions.append("ce.pos_profile = %s")
        args.append(cstr(terminal).strip())
    if status:
        conditions.append("COALESCE(ce.custom_difference_status, 'Pending Review') = %s")
        args.append(cstr(status).strip())

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT
            ce.name,
            ce.posting_date,
            ce.pos_profile,
            ce.user,
            ce.period_start_date,
            ce.period_end_date,
            COALESCE(ce.custom_difference_status, 'Pending Review') AS status,
            ce.custom_difference_note AS note,
            SUM(ABS(d.difference)) AS total_difference,
            GROUP_CONCAT(
                CONCAT(d.mode_of_payment, ': ', d.difference)
                ORDER BY d.idx SEPARATOR ' | '
            ) AS difference_breakdown
        FROM `tabPOS Closing Entry` ce
        INNER JOIN `tabPOS Closing Entry Detail` d ON d.parent = ce.name
        WHERE {where}
        GROUP BY ce.name
        HAVING SUM(ABS(d.difference)) > 0
        ORDER BY ce.creation DESC
        LIMIT %s OFFSET %s
    """, tuple(args) + (int(page_length), int(start)), as_dict=1)

    terminals = frappe.db.sql("""
        SELECT DISTINCT pos_profile FROM `tabPOS Closing Entry`
        WHERE docstatus = 1 AND pos_profile IS NOT NULL
        ORDER BY pos_profile
    """, as_list=1)

    # Summary counts
    summary = frappe.db.sql("""
        SELECT
            COUNT(DISTINCT ce.name) AS total_cases,
            SUM(ABS(d.difference)) AS total_amount,
            COUNT(DISTINCT CASE WHEN COALESCE(ce.custom_difference_status,'Pending Review') IN ('Pending Review','Under Review') THEN ce.name END) AS pending_count,
            COUNT(DISTINCT CASE WHEN COALESCE(ce.custom_difference_status,'') = 'Resolved' THEN ce.name END) AS resolved_count,
            COUNT(DISTINCT CASE WHEN COALESCE(ce.custom_difference_status,'') = 'Escalated' THEN ce.name END) AS escalated_count
        FROM `tabPOS Closing Entry` ce
        INNER JOIN `tabPOS Closing Entry Detail` d ON d.parent = ce.name
        WHERE ce.docstatus = 1
        HAVING SUM(ABS(d.difference)) > 0
    """, as_dict=1)

    return {
        "rows": rows,
        "terminals": [r[0] for r in terminals],
        "summary": summary[0] if summary else {},
    }


@frappe.whitelist()
def update_shift_difference_status(closing_entry, status, note=None):
    """Update the difference review status and optional note on a POS Closing Entry."""
    allowed_roles = {"POS Manager", "Accounts Manager", "System Manager"}
    if not (set(frappe.get_roles()) & allowed_roles):
        frappe.throw(_("You do not have permission to update difference status."), frappe.PermissionError)

    if not frappe.db.exists("POS Closing Entry", closing_entry):
        frappe.throw(_("Closing Entry {0} not found").format(closing_entry))

    valid_statuses = {"Pending Review", "Under Review", "Resolved", "Escalated"}
    if cstr(status) not in valid_statuses:
        frappe.throw(_("Invalid status: {0}").format(status))

    updates = {"custom_difference_status": cstr(status)}
    if note is not None:
        updates["custom_difference_note"] = cstr(note)

    frappe.db.set_value("POS Closing Entry", closing_entry, updates)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def get_pos_dashboard_stats():
    """Return live stats for the POS Manager Dashboard."""
    today = nowdate()

    gross_sales = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabPOS Invoice`
        WHERE posting_date = %s AND docstatus = 1
    """, today)[0][0] or 0

    open_drafts = frappe.db.count("POS Invoice", {"docstatus": 0})

    shift_differences = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabPOS Closing Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today)[0][0] or 0

    # Active terminals — open POS Opening Entries
    if _has_pos_opening_entry_on_invoice():
        terminals_raw = frappe.db.sql("""
            SELECT
                poe.name,
                poe.pos_profile AS terminal_name,
                poe.user AS cashier,
                poe.period_start_date AS shift_date,
                COUNT(pi.name) AS bills,
                COALESCE(SUM(pi.grand_total), 0) AS sales
            FROM `tabPOS Opening Entry` poe
            LEFT JOIN `tabPOS Invoice` pi ON pi.pos_opening_entry = poe.name AND pi.docstatus = 1
            WHERE poe.status = 'Open' AND poe.docstatus = 1
            GROUP BY poe.name
            ORDER BY poe.creation DESC
            LIMIT 10
        """, as_dict=1)
    else:
        # Fallback for schemas where POS Invoice has no pos_opening_entry link.
        terminals_raw = frappe.db.sql("""
            SELECT
                poe.name,
                poe.pos_profile AS terminal_name,
                poe.user AS cashier,
                poe.period_start_date AS shift_date,
                COUNT(CASE WHEN pi.docstatus = 1 THEN pi.name END) AS bills,
                COALESCE(SUM(CASE WHEN pi.docstatus = 1 THEN pi.grand_total ELSE 0 END), 0) AS sales
            FROM `tabPOS Opening Entry` poe
            LEFT JOIN `tabPOS Invoice` pi
                ON pi.pos_profile = poe.pos_profile
                AND pi.owner = poe.user
                AND pi.posting_date >= DATE(poe.period_start_date)
            WHERE poe.status = 'Open' AND poe.docstatus = 1
            GROUP BY poe.name
            ORDER BY poe.creation DESC
            LIMIT 10
        """, as_dict=1)

    # Revenue by outlet (pos_profile groups by profile name = outlet)
    outlet_revenue = frappe.db.sql("""
        SELECT
            COALESCE(pos_profile, 'Unknown') AS outlet,
            COALESCE(SUM(grand_total), 0) AS amount
        FROM `tabPOS Invoice`
        WHERE posting_date = %s AND docstatus = 1
        GROUP BY pos_profile
        ORDER BY amount DESC
    """, today, as_dict=1)

    total_revenue = sum(flt(o["amount"]) for o in outlet_revenue) or 1
    for o in outlet_revenue:
        o["pct"] = round(flt(o["amount"]) / total_revenue * 100)

    return {
        "gross_sales": flt(gross_sales),
        "open_drafts": int(open_drafts),
        "shift_differences": flt(shift_differences),
        "terminals": terminals_raw,
        "outlet_revenue": outlet_revenue,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Shift Close
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_shift_stats(pos_opening_entry=None):
    """Return stats for the Shift Close page.

    If pos_opening_entry is provided, scope to that opening entry.
    Otherwise return the current user's open entry.
    """
    user = frappe.session.user

    if not pos_opening_entry:
        # Keep shift detection consistent with the POS opening/profile APIs.
        entry = _get_open_pos_entry(user)
        pos_opening_entry = entry.get("name") if entry else None

    if not pos_opening_entry:
        # No open shift for this user
        return {
            "has_open_shift": False,
            "gross_sales": 0,
            "net_collections": 0,
            "open_drafts": 0,
            "difference": 0,
            "cashier": frappe.db.get_value("User", user, "full_name") or user,
            "pos_profile": "",
            "shift_date": nowdate(),
            "opening_time": "",
            "tender_breakdown": [],
        }

    entry_doc = frappe.get_doc("POS Opening Entry", pos_opening_entry)

    if _has_pos_opening_entry_on_invoice():
        gross = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabPOS Invoice`
            WHERE pos_opening_entry = %s AND docstatus = 1
        """, pos_opening_entry)[0][0] or 0

        open_drafts = frappe.db.count("POS Invoice", {
            "pos_opening_entry": pos_opening_entry, "docstatus": 0
        })

        # Tender breakdown by payment mode
        tender = frappe.db.sql("""
            SELECT
                pip.mode_of_payment AS payment_type,
                COALESCE(SUM(pip.amount), 0) AS system_amount
            FROM `tabPOS Invoice` pi
            JOIN `tabSales Invoice Payment` pip ON pip.parent = pi.name
            WHERE pi.pos_opening_entry = %s AND pi.docstatus = 1
            GROUP BY pip.mode_of_payment
        """, pos_opening_entry, as_dict=1)
    else:
        entry_start = entry_doc.period_start_date
        time_condition = _pos_invoice_shift_time_condition("pi")
        gross = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabPOS Invoice` pi
            WHERE pi.pos_profile = %s
              AND pi.owner = %s
              AND {time_condition}
              AND docstatus = 1
        """.format(time_condition=time_condition), (entry_doc.pos_profile, entry_doc.user, entry_start))[0][0] or 0

        open_drafts = frappe.db.sql("""
            SELECT COUNT(*)
            FROM `tabPOS Invoice` pi
            WHERE pi.pos_profile = %s
              AND pi.owner = %s
              AND {time_condition}
              AND pi.docstatus = 0
        """.format(time_condition=time_condition), (entry_doc.pos_profile, entry_doc.user, entry_start))[0][0] or 0

        # Fallback grouping by profile + user + opening date when no explicit shift link exists.
        tender = frappe.db.sql("""
            SELECT
                pip.mode_of_payment AS payment_type,
                COALESCE(SUM(pip.amount), 0) AS system_amount
            FROM `tabPOS Invoice` pi
            JOIN `tabSales Invoice Payment` pip ON pip.parent = pi.name
            WHERE pi.pos_profile = %s
              AND pi.owner = %s
              AND {time_condition}
              AND pi.docstatus = 1
            GROUP BY pip.mode_of_payment
        """.format(time_condition=time_condition), (entry_doc.pos_profile, entry_doc.user, entry_start), as_dict=1)

    opening_by_mop = {
        row.mode_of_payment: flt(row.opening_amount)
        for row in (entry_doc.get("balance_details") or [])
        if row.mode_of_payment
    }

    for t in tender:
        opening_amount = flt(opening_by_mop.get(t["payment_type"]))
        collection_amount = flt(t["system_amount"])
        expected_amount = opening_amount + collection_amount
        t["collection_amount"] = collection_amount
        t["opening_amount"] = opening_amount
        t["expected_amount"] = expected_amount
        t["system_amount"] = expected_amount
        t["editable"] = t["payment_type"] == "Cash"
        t["counted"] = expected_amount
        t["diff"] = 0

    for mop, opening_amount in opening_by_mop.items():
        if any(t["payment_type"] == mop for t in tender):
            continue
        tender.append({
            "payment_type": mop,
            "collection_amount": 0,
            "opening_amount": flt(opening_amount),
            "expected_amount": flt(opening_amount),
            "system_amount": flt(opening_amount),
            "editable": mop.lower() == "cash",
            "counted": flt(opening_amount),
            "diff": 0,
        })

    net_collections = sum(flt(t.get("collection_amount")) for t in tender)

    # Additional stats for the Shift Close summary panel
    if _has_pos_opening_entry_on_invoice():
        bills_processed = frappe.db.count("POS Invoice", {"pos_opening_entry": pos_opening_entry, "docstatus": 1})
        voided_count = frappe.db.count("POS Invoice", {"pos_opening_entry": pos_opening_entry, "docstatus": 2})
    else:
        entry_start = entry_doc.period_start_date
        time_condition = _pos_invoice_shift_time_condition("pi")
        bills_processed = frappe.db.sql("""
            SELECT COUNT(*)
            FROM `tabPOS Invoice` pi
            WHERE pi.pos_profile = %s
              AND pi.owner = %s
              AND {time_condition}
              AND pi.docstatus = 1
        """.format(time_condition=time_condition), (entry_doc.pos_profile, entry_doc.user, entry_start))[0][0] or 0
        voided_count = 0

    opening_cash = 0
    for row in entry_doc.get("balance_details") or []:
        if (row.mode_of_payment or "").lower() == "cash":
            opening_cash = flt(row.opening_amount)
            break

    return {
        "has_open_shift": True,
        "pos_opening_entry": pos_opening_entry,
        "gross_sales": flt(gross),
                "net_collections": flt(net_collections),
        "open_drafts": int(open_drafts),
                "open_tables": int(_get_shift_open_table_count(entry_doc, pos_opening_entry)),
        "difference": 0,
        "cashier": frappe.db.get_value("User", entry_doc.user, "full_name") or entry_doc.user,
        "pos_profile": entry_doc.pos_profile,
        "shift_date": cstr(entry_doc.period_start_date),
        "opening_time": cstr(entry_doc.period_start_date),
        "tender_breakdown": tender,
        "bills_processed": int(bills_processed),
        "voided_count": int(voided_count),
        "opening_cash": flt(opening_cash),
    }


@frappe.whitelist()
def close_pos_shift(pos_opening_entry, tender_rows=None, closing_note=None, attachment_url=None):
    """Create a POS Closing Entry to close the active shift."""
    import json
    from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import (
        make_closing_entry_from_opening,
    )

    tender_rows = json.loads(tender_rows) if isinstance(tender_rows, str) else (tender_rows or [])

    if not frappe.db.exists("POS Opening Entry", pos_opening_entry):
        frappe.throw(_("POS Opening Entry {0} not found").format(pos_opening_entry))

    entry_doc = frappe.get_doc("POS Opening Entry", pos_opening_entry)

    try:
        # Use ERPNext's official helper to build the closing entry doc.
        # It calls get_pos_invoices() internally to populate pos_transactions,
        # payment_reconciliation and taxes.
        closing = make_closing_entry_from_opening(entry_doc)

        closing.flags.ignore_permissions = True
        closing.flags.ignore_mandatory = True

        # Apply counted (physical cash) amounts from the cashier's tender input.
        # Merge into auto-populated rows first, then add any remaining rows.
        if tender_rows:
            tender_map = {
                r.get("payment_type"): flt(r.get("counted", r.get("system_amount", 0)))
                for r in tender_rows if r.get("payment_type")
            }
            existing_mops = set()
            for row in (closing.get("payment_reconciliation") or []):
                existing_mops.add(row.mode_of_payment)
                if row.mode_of_payment in tender_map:
                    row.closing_amount = tender_map[row.mode_of_payment]
                    row.difference = row.closing_amount - flt(row.expected_amount or 0)

            # Add rows not already present from auto-population
            for r in tender_rows:
                mop = r.get("payment_type")
                if mop and mop not in existing_mops:
                    system = flt(r.get("system_amount", 0))
                    counted = flt(r.get("counted", system))
                    closing.append("payment_reconciliation", {
                        "mode_of_payment": mop,
                        "opening_amount": flt(r.get("opening_amount", 0)),
                        "expected_amount": system,
                        "closing_amount": counted,
                        "difference": counted - system,
                    })

        # Set closing note in whichever field the installed ERPNext version uses
        if closing_note:
            _meta_fields = {f.fieldname for f in frappe.get_meta("POS Closing Entry").fields}
            if "notes" in _meta_fields:
                closing.notes = closing_note
            elif "remarks" in _meta_fields:
                closing.remarks = closing_note

        closing.insert()
        closing.submit()

        # Attach uploaded file to the closing entry if provided
        if attachment_url:
            frappe.db.set_value(
                "File",
                {"file_url": cstr(attachment_url)},
                {
                    "attached_to_doctype": "POS Closing Entry",
                    "attached_to_name": closing.name,
                    "attached_to_field": None,
                },
            )

        frappe.db.commit()

    except frappe.ValidationError:
        # Re-raise as-is so the frontend shows the real ERPNext validation message
        frappe.log_error(frappe.get_traceback(), "POS Closing Entry ValidationError")
        raise
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS Shift close failed")
        frappe.throw(_("Failed to close POS shift. Please check configuration."))

    return {"closing_entry": closing.name}


# ─────────────────────────────────────────────────────────────────────────────
# Staff Roster (uses Employee Checkin / Shift Assignment from HRMS)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_staff_roster(outlet=None, shift=None, role=None, search=None, week_start=None, week_end=None):
    """Return POS staff shift assignments for the requested week."""
    week_start_dt, week_end_dt = _pos_roster_week_range(week_start, week_end)

    conditions = ["sa.status = 'Active'"]
    args = []

    if outlet:
        conditions.append("e.department LIKE %s")
        args.append(f"%{cstr(outlet).strip()}%")

    if shift:
        conditions.append("sa.shift_type = %s")
        args.append(cstr(shift).strip())

    if role:
        conditions.append("e.designation LIKE %s")
        args.append(f"%{cstr(role).strip()}%")

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(e.employee_name LIKE %s OR e.name LIKE %s OR e.department LIKE %s OR e.designation LIKE %s OR sa.shift_type LIKE %s)")
        args.extend([q, q, q, q, q])

    where = " AND ".join(conditions)

    staff = frappe.db.sql(f"""
        SELECT
            e.name AS employee,
            e.employee_name,
            e.designation AS role,
            e.department AS outlet,
            sa.shift_type AS shift,
            sa.start_date,
            sa.end_date,
            sa.status
        FROM `tabShift Assignment` sa
        JOIN `tabEmployee` e ON e.name = sa.employee
        WHERE {where}
          AND e.status = 'Active'
          AND sa.start_date <= %s
          AND (sa.end_date IS NULL OR sa.end_date >= %s)
        ORDER BY e.employee_name, sa.start_date, sa.shift_type
        LIMIT 500
    """, tuple(args) + (cstr(week_end_dt), cstr(week_start_dt)), as_dict=1)

    return [_pos_roster_row(row, week_start_dt, week_end_dt) for row in staff]


@frappe.whitelist()
def get_pos_staff_roster_stats(week_start=None, week_end=None, outlet=None, shift=None, role=None, search=None):
    """Return real stat cards for the Staff Roster page."""
    rows = get_pos_staff_roster(
        outlet=outlet,
        shift=shift,
        role=role,
        search=search,
        week_start=week_start,
        week_end=week_end,
    )
    week_start_dt, week_end_dt = _pos_roster_week_range(week_start, week_end)
    staff = {row.get("employee") for row in rows if row.get("employee")}
    outlets = {row.get("outlet") for row in rows if row.get("outlet")}
    shifts = {row.get("shift") for row in rows if row.get("shift")}

    morning_days = _covered_week_days(rows, week_start_dt, week_end_dt, "morning")
    evening_days = _covered_week_days(rows, week_start_dt, week_end_dt, "evening")
    leave_count = _pos_roster_leave_count(week_start_dt, week_end_dt, staff)

    return {
        "scheduled_staff": len(staff),
        "scheduled": len(staff),
        "outlet_count": len(outlets),
        "shift_count": len(shifts),
        "morning_coverage": _coverage_percent(morning_days),
        "evening_coverage": _coverage_percent(evening_days),
        "staff_off": leave_count,
        "on_leave": leave_count,
    }


@frappe.whitelist()
def get_pos_staff_roster_options():
    """Return dynamic filter options for the POS staff roster."""
    employees = frappe.db.sql("""
        SELECT
            name,
            employee_name,
            department,
            designation,
            company
        FROM `tabEmployee`
        WHERE status = 'Active'
        ORDER BY employee_name, name
    """, as_dict=1)
    outlets = frappe.db.sql("""
        SELECT DISTINCT department AS value
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND IFNULL(department, '') != ''
        ORDER BY department
    """, as_dict=1)
    shifts = frappe.db.sql("""
        SELECT name AS value
        FROM `tabShift Type`
        ORDER BY name
    """, as_dict=1)
    roles = frappe.db.sql("""
        SELECT DISTINCT designation AS value
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND IFNULL(designation, '') != ''
        ORDER BY designation
    """, as_dict=1)
    return {
        "employees": [{
            "employee": row.name,
            "employee_name": row.employee_name or row.name,
            "department": row.department or "",
            "designation": row.designation or "",
            "company": row.company or "",
        } for row in employees],
        "outlets": [row.value for row in outlets if row.value],
        "shifts": [row.value for row in shifts if row.value],
        "roles": [row.value for row in roles if row.value],
    }


@frappe.whitelist()
def create_pos_staff_roster(employee, shift_type, start_date, end_date=None, status="Active"):
    """Create a submitted HRMS Shift Assignment from the frontdesk roster page."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to create a shift plan."))

    employee = cstr(employee).strip()
    shift_type = cstr(shift_type).strip()
    status = cstr(status or "Active").strip()
    start = getdate(start_date) if start_date else None
    end = getdate(end_date) if end_date else None

    if not employee:
        frappe.throw(_("Employee is required."))
    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee {0} was not found.").format(employee))
    if not shift_type:
        frappe.throw(_("Shift Type is required."))
    if not frappe.db.exists("Shift Type", shift_type):
        frappe.throw(_("Shift Type {0} was not found.").format(shift_type))
    if not start:
        frappe.throw(_("Start Date is required."))
    if end and end < start:
        frappe.throw(_("End Date cannot be before Start Date."))
    if status not in ("Active", "Inactive"):
        frappe.throw(_("Status must be Active or Inactive."))

    employee_doc = frappe.db.get_value(
        "Employee",
        employee,
        ["employee_name", "company", "department"],
        as_dict=1,
    )
    if not employee_doc:
        frappe.throw(_("Employee {0} was not found.").format(employee))

    doc = frappe.get_doc({
        "doctype": "Shift Assignment",
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "company": employee_doc.company,
        "department": employee_doc.department,
        "shift_type": shift_type,
        "start_date": start,
        "end_date": end,
        "status": status,
    })
    doc.insert(ignore_permissions=True)
    doc.flags.ignore_permissions = True
    doc.submit()

    return {
        "name": doc.name,
        "employee": doc.employee,
        "employee_name": doc.employee_name,
        "shift": doc.shift_type,
        "start_date": cstr(doc.start_date),
        "end_date": cstr(doc.end_date or ""),
        "status": doc.status,
    }


def _pos_roster_week_range(week_start=None, week_end=None):
    if week_start:
        start = getdate(week_start)
    else:
        today = getdate(nowdate())
        start = add_days(today, -today.weekday())

    end = getdate(week_end) if week_end else add_days(start, 6)
    if end < start:
        frappe.throw(_("Week end cannot be before week start."))
    return start, end


def _pos_roster_row(row, week_start, week_end):
    start = max(getdate(row.start_date), week_start) if row.start_date else week_start
    end = min(getdate(row.end_date), week_end) if row.end_date else week_end
    return {
        "employee": row.employee,
        "employee_name": row.employee_name or row.employee,
        "role": row.role or "Unassigned",
        "designation": row.role or "Unassigned",
        "outlet": row.outlet or "Unassigned",
        "department": row.outlet or "Unassigned",
        "shift": row.shift or "Unassigned",
        "start_date": cstr(start),
        "end_date": cstr(end),
        "off_day": "—",
        "status": row.status or "Scheduled",
    }


def _covered_week_days(rows, week_start, week_end, shift_keyword):
    covered = set()
    keyword = cstr(shift_keyword).lower()
    for row in rows:
        if keyword not in cstr(row.get("shift")).lower():
            continue
        start = getdate(row.get("start_date"))
        end = getdate(row.get("end_date"))
        current = max(start, week_start)
        last = min(end, week_end)
        while current <= last:
            covered.add(cstr(current))
            current = add_days(current, 1)
    return covered


def _coverage_percent(days):
    return round((len(days) / 7) * 100) if days else 0


def _pos_roster_leave_count(week_start, week_end, scheduled_staff):
    if not frappe.db.table_exists("Leave Application"):
        return 0

    values = [cstr(week_end), cstr(week_start)]
    employee_filter = ""
    if scheduled_staff:
        employee_filter = "AND employee IN %(employees)s"
        values = {"week_end": cstr(week_end), "week_start": cstr(week_start), "employees": tuple(scheduled_staff)}
        params = values
    else:
        params = tuple(values)

    query = f"""
        SELECT COUNT(DISTINCT employee) AS cnt
        FROM `tabLeave Application`
        WHERE docstatus < 2
          AND status IN ('Approved', 'Open')
          AND from_date <= %(week_end)s
          AND to_date >= %(week_start)s
          {employee_filter}
    """ if scheduled_staff else """
        SELECT COUNT(DISTINCT employee) AS cnt
        FROM `tabLeave Application`
        WHERE docstatus < 2
          AND status IN ('Approved', 'Open')
          AND from_date <= %s
          AND to_date >= %s
    """
    result = frappe.db.sql(query, params, as_dict=1)
    return int(result[0].cnt or 0) if result else 0


# ─────────────────────────────────────────────────────────────────────────────
# Draft Invoice: Detail (resume) + Delete
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_draft_invoice_detail(invoice_name):
    """Return full item details for a draft POS Invoice so the cashier can resume it."""
    if not frappe.db.exists("POS Invoice", invoice_name):
        frappe.throw(_("Invoice {0} not found").format(invoice_name))

    pi = frappe.get_doc("POS Invoice", invoice_name)
    if pi.docstatus != 0:
        frappe.throw(_("Only draft invoices can be resumed."))

    items = []
    for row in pi.items:
        item_group = frappe.db.get_value("Item", row.item_code, "item_group") or ""
        image = frappe.db.get_value("Item", row.item_code, "image") or ""
        items.append({
            "item_code": row.item_code,
            "name": row.item_name,
            "qty": flt(row.qty),
            "price": flt(row.rate),
            "category": item_group,
            "image": image,
            "stock": 999,
        })

    return {
        "invoice": pi.name,
        "customer": pi.customer_name or pi.customer or "",
        "items": items,
        "remarks": pi.remarks or "",
        "discount_amount": flt(pi.discount_amount or 0),
        "sent_to_kitchen": _get_sent_to_kitchen_map(pi.name),
    }


@frappe.whitelist()
def delete_pos_draft_invoice(invoice_name):
    """Cancel and delete a draft POS Invoice."""
    if not frappe.db.exists("POS Invoice", invoice_name):
        frappe.throw(_("Invoice {0} not found").format(invoice_name))

    pi = frappe.get_doc("POS Invoice", invoice_name)
    if pi.docstatus != 0:
        frappe.throw(_("Only draft invoices can be deleted."))

    kitchen_tickets = frappe.get_all(
        "Kitchen Order Ticket",
        filters={"pos_invoice": invoice_name, "docstatus": 0},
        fields=["name", "status"],
    )
    started = [t for t in kitchen_tickets if t.status != "Pending"]
    if started:
        frappe.throw(_("Cannot delete this draft because kitchen preparation has already started."))

    try:
        for ticket in kitchen_tickets:
            if ticket.status == "Pending":
                kt = frappe.get_doc("Kitchen Order Ticket", ticket.name)
                kt.flags.ignore_permissions = True
                kt.delete()
        pi.flags.ignore_permissions = True
        pi.delete()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS draft invoice deletion failed")
        frappe.throw(_("Failed to delete invoice {0}.").format(invoice_name))

    return {"deleted": invoice_name}


# ─────────────────────────────────────────────────────────────────────────────
# Active POS Terminals (for manager Close Terminal modal)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_open_pos_tables():
    """Return open table orders — draft POS Invoices whose customer_name is a table or bar name."""
    drafts = frappe.db.sql("""
        SELECT
            pi.name AS invoice,
            pi.customer_name AS customer,
            pi.grand_total AS bill,
            pi.owner AS cashier,
            pi.remarks AS notes,
            pi.creation,
            DATE_FORMAT(pi.creation, '%%h:%%i %%p') AS open_time,
            COUNT(pit.name) AS item_count
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabPOS Invoice Item` pit ON pit.parent = pi.name
        WHERE pi.docstatus = 0
          AND (
            pi.customer_name LIKE 'Table %%'
            OR pi.customer_name LIKE 'Bar %%'
            OR pi.customer_name LIKE 'Pool%%'
          )
        GROUP BY pi.name
        ORDER BY pi.creation DESC
        LIMIT 50
    """, as_dict=1)

    result = []
    for idx, d in enumerate(drafts):
        items = frappe.db.sql("""
            SELECT pit.item_code, pit.item_name AS name, pit.qty,
                   pit.rate AS price, (pit.qty * pit.rate) AS amount,
                   i.item_group AS category
            FROM `tabPOS Invoice Item` pit
            LEFT JOIN `tabItem` i ON i.name = pit.item_code
            WHERE pit.parent = %s
        """, d["invoice"], as_dict=1)
        age = _age_minutes_from(d.get("creation"))
        h, m = divmod(age, 60)
        customer = d["customer"] or ""
        area = (
            "Bar Lounge" if customer.upper().startswith("BAR")
            else "Poolside" if customer.upper().startswith("POOL")
            else "Restaurant"
        )
        result.append({
            "id": idx + 1,
            "invoice": d["invoice"],
            "name": customer,
            "cashier": d["cashier"],
            "bill": float(d["bill"] or 0),
            "age": f"{h}h {m}m" if h else f"{m}m",
            "age_minutes": age,
            "items": [dict(i) for i in items],
            "sent_to_kitchen": _get_sent_to_kitchen_map(d["invoice"]),
            "status": "Ordering",
            "area": area,
            "waiter": d["cashier"],
            "guests": 0,
            "openTime": d["open_time"] or "",
            "notes": d["notes"] or "",
        })

    return result


@frappe.whitelist()
def get_open_pos_terminals():
    """Return active POS Opening Entries with live stats for the Close Terminal modal."""
    if _has_pos_opening_entry_on_invoice():
        rows = frappe.db.sql(
            """
            SELECT
                poe.name AS opening_entry,
                poe.pos_profile AS terminal_name,
                poe.user,
                poe.period_start_date AS shift_start,
                poe.company,
                COALESCE(u.full_name, poe.user) AS cashier,
                COUNT(DISTINCT CASE WHEN pi.docstatus = 1 THEN pi.name END) AS bill_count,
                COALESCE(SUM(CASE WHEN pi.docstatus = 1 THEN pi.grand_total ELSE 0 END), 0) AS gross_sales,
                COUNT(DISTINCT CASE WHEN pi.docstatus = 0 THEN pi.name END) AS open_drafts,
                COUNT(DISTINCT CASE
                    WHEN pi.docstatus = 0
                     AND (pi.customer_name LIKE 'Table %%'
                          OR pi.customer_name LIKE 'Bar %%'
                          OR pi.customer_name LIKE 'Pool%%')
                    THEN pi.name END) AS open_tables
            FROM `tabPOS Opening Entry` poe
            LEFT JOIN `tabUser` u ON u.name = poe.user
            LEFT JOIN `tabPOS Invoice` pi ON pi.pos_opening_entry = poe.name
            WHERE poe.status = 'Open' AND poe.docstatus = 1
            GROUP BY poe.name
            ORDER BY poe.creation DESC
            LIMIT 20
            """,
            as_dict=1,
        )
    else:
        rows = frappe.db.sql(
            """
            SELECT
                poe.name AS opening_entry,
                poe.pos_profile AS terminal_name,
                poe.user,
                poe.period_start_date AS shift_start,
                poe.company,
                COALESCE(u.full_name, poe.user) AS cashier,
                COUNT(DISTINCT CASE WHEN pi.docstatus = 1 THEN pi.name END) AS bill_count,
                COALESCE(SUM(CASE WHEN pi.docstatus = 1 THEN pi.grand_total ELSE 0 END), 0) AS gross_sales,
                COUNT(DISTINCT CASE WHEN pi.docstatus = 0 THEN pi.name END) AS open_drafts,
                COUNT(DISTINCT CASE
                    WHEN pi.docstatus = 0
                     AND (pi.customer_name LIKE 'Table %%'
                          OR pi.customer_name LIKE 'Bar %%'
                          OR pi.customer_name LIKE 'Pool%%')
                    THEN pi.name END) AS open_tables
            FROM `tabPOS Opening Entry` poe
            LEFT JOIN `tabUser` u ON u.name = poe.user
            LEFT JOIN `tabPOS Invoice` pi
                ON pi.pos_profile = poe.pos_profile
                AND pi.owner = poe.user
                AND TIMESTAMP(pi.posting_date, COALESCE(pi.posting_time, '00:00:00')) >= poe.period_start_date
            WHERE poe.status = 'Open' AND poe.docstatus = 1
            GROUP BY poe.name
            ORDER BY poe.creation DESC
            LIMIT 20
            """,
            as_dict=1,
        )

    for r in rows:
        r["gross_sales"] = flt(r["gross_sales"])
        r["bill_count"] = int(r["bill_count"])
        r["open_drafts"] = int(r["open_drafts"])
        r["open_tables"] = int(r.get("open_tables") or 0)

    return rows



@frappe.whitelist()
def create_split_pos_invoice(items, portions, customer=None, service_charge=0,
                             kitchen_note=None, pos_profile=None, discount_amount=0,
                             existing_draft=None, complimentary_name=None):
    import json

    items = json.loads(items) if isinstance(items, str) else items
    portions = json.loads(portions) if isinstance(portions, str) else portions

    if not items:
        frappe.throw(_("No items in cart"))

    draft_table_display_name = None
    if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
        draft_table_display_name = _extract_table_display_name(
            frappe.db.get_value("POS Invoice", existing_draft, "customer_name")
        )

    if not pos_profile:
        pos_profile = _get_user_pos_profile()

    if not pos_profile:
        frappe.throw(_("No POS Profile is mapped to your user."))

    pos_opening_entry = _get_open_pos_entry(frappe.session.user, pos_profile)
    if not pos_opening_entry:
        frappe.throw(_("No open POS Opening Entry found for your user. Please open a shift before charging."))

    pos_profile = pos_opening_entry.get("pos_profile") or pos_profile
    profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)

    allowed_modes = [
        row.mode_of_payment
        for row in (profile_doc.get("payments") or [])
        if row.mode_of_payment
    ]

    if not allowed_modes:
        frappe.throw(_("POS Profile {0} has no payment modes configured.").format(pos_profile))

    company = profile_doc.company or frappe.db.get_single_value("Global Defaults", "default_company") or ""

    customer = _resolve_pos_customer(customer, profile_doc=profile_doc, allow_guest_fallback=True)

    if not customer:
        frappe.throw(_("Set a valid default customer on POS Profile {0}.").format(pos_profile))

    items_total = flt(sum(
        flt(i.get("price", 0)) * flt(i.get("qty", 1))
        for i in items
    )) + flt(service_charge)

    manual_discount = flt(discount_amount)
    complimentary_discount = _get_complimentary_discount(complimentary_name, items_total, manual_discount)
    total_discount = min(items_total, manual_discount + complimentary_discount)
    net_total = max(0, items_total - total_discount)

    if not portions:
        if net_total > 0:
            frappe.throw(_("No split portions found"))
        portions = [{"amount": 0, "paymentType": "Cash"}]

    portions_total = flt(sum(flt(p.get("amount", 0)) for p in portions), 2)

    if flt(portions_total, 2) != flt(net_total, 2):
        frappe.throw(_("Split total must equal invoice total."))

    room_sales_invoices = []

    def create_room_split_invoice(portion):
        check_in = portion.get("checkIn")
        amount = flt(portion.get("amount", 0))
        if not check_in or amount <= 0:
            return None

        if not frappe.db.exists("Hotel Room Check In", check_in):
            frappe.throw(_("Check-in {0} not found").format(check_in))

        ci = frappe.get_doc("Hotel Room Check In", check_in)
        if ci.status != "Checked In":
            frappe.throw(_("Check-in {0} is not active").format(check_in))

        room_customer = None
        if ci.guest:
            try:
                guest_doc = frappe.get_doc("Hotel Guest", ci.guest)
                room_customer = guest_doc.customer
            except Exception:
                room_customer = None
        room_customer = room_customer or ci.guest or customer

        ratio = amount / net_total if net_total else 0
        si = frappe.new_doc("Sales Invoice")
        si.customer = room_customer
        si.company = company
        si.posting_date = nowdate()
        si.custom_hotel_room_check_in = check_in
        if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
            si.custom_invoice_source = _derive_invoice_source(pos_profile)
        if kitchen_note:
            si.remarks = kitchen_note

        for it in items:
            si.append("items", {
                "item_code": it.get("item_code") or it.get("id"),
                "qty": flt(it.get("qty", 1)),
                "rate": flt(it.get("price", 0)) * ratio,
            })

        si.flags.ignore_permissions = True
        si.set_missing_values()
        si.insert()
        si.submit()
        return {
            "sales_invoice": si.name,
            "check_in": check_in,
            "room": ci.room_number,
            "amount": amount,
        }

    updating_existing_draft = False
    if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
        pi = frappe.get_doc("POS Invoice", existing_draft)
        if pi.docstatus != 0:
            frappe.throw(_("Only draft POS Invoices can be completed from a held sale."))
        updating_existing_draft = True
        pi.set("items", [])
        pi.set("payments", [])
    else:
        pi = frappe.new_doc("POS Invoice")

    pi.customer = customer
    pi.company = company
    pi.posting_date = nowdate()
    pi.pos_profile = pos_profile
    pi.remarks = kitchen_note or ""

    if _has_pos_opening_entry_on_invoice():
        pi.pos_opening_entry = pos_opening_entry.get("name")

    room_check_in = None

    for p in portions:
        if cstr(p.get("paymentType")) == "Post to Room" and p.get("checkIn"):
            room_check_in = p.get("checkIn")
            break

    if room_check_in and frappe.db.has_column("POS Invoice", "custom_hotel_room_check_in"):
        pi.custom_hotel_room_check_in = room_check_in

    for it in items:
        pi.append("items", {
            "item_code": it.get("item_code") or it.get("id"),
            "qty": flt(it.get("qty", 1)),
            "rate": flt(it.get("price", 0)),
        })

    if total_discount > 0:
        pi.discount_amount = total_discount
        pi.apply_discount_on = "Grand Total"

    for p in portions:
        amount = flt(p.get("amount", 0))
        if amount <= 0:
            continue

        pi.append("payments", {
            "mode_of_payment": _resolve_pos_payment_mode(p.get("paymentType"), profile_doc, allowed_modes),
            "amount": amount,
        })

    if not pi.get("payments"):
        pi.append("payments", {
            "mode_of_payment": _resolve_pos_payment_mode("Cash", profile_doc, allowed_modes),
            "amount": 0,
        })

    pi.flags.ignore_permissions = True
    pi.set_missing_values()
    if updating_existing_draft:
        pi.save()
    else:
        pi.insert()
    pi.submit()
    if draft_table_display_name:
        frappe.db.set_value("POS Invoice", pi.name, "customer_name",
                            draft_table_display_name, update_modified=False)
    complimentary = _redeem_complimentary(complimentary_name, pi.name, items_total, manual_discount)
    for p in portions:
        if cstr(p.get("paymentType")) == "Post to Room":
            room_invoice = create_room_split_invoice(p)
            if room_invoice:
                room_sales_invoices.append(room_invoice)
    frappe.db.commit()

    return {
        "pos_invoice": pi.name,
        "grand_total": flt(pi.grand_total),
        "split": True,
        "complimentary": complimentary,
        "room_sales_invoices": room_sales_invoices,
    }
