import frappe
from frappe import _
from frappe.utils import flt, cstr, now_datetime, nowdate, add_days, getdate
from frappe.utils.nestedset import get_descendants_of


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

    Priority:
    1. Profiles that explicitly list this user in their Users table.
    2. Profiles whose Users table is empty (available to everyone).

    This mirrors ERPNext behaviour where an unmapped profile is global.
    """
    user = user or frappe.session.user
    if not user or user == "Guest":
        return []

    # Explicitly mapped profiles (case-insensitive user match)
    explicit = frappe.db.sql(
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
    explicit_names = [r.get("name") for r in explicit if r.get("name")]

    if explicit_names:
        return explicit_names

    # Fallback: profiles with no user restrictions
    global_profiles = frappe.db.sql(
        """
        SELECT p.name
        FROM `tabPOS Profile` p
        WHERE p.disabled = 0
          AND NOT EXISTS (
              SELECT 1 FROM `tabPOS Profile User` pu2
              WHERE pu2.parent = p.name
          )
        ORDER BY p.modified DESC
        """,
        as_dict=1,
    )
    return [r.get("name") for r in global_profiles if r.get("name")]


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
        "default_profile": profiles[0] if profiles else None,
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
        pos_profile = mapped_profiles[0]

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
    """Return items available for POS billing.

    Fetches from ERPNext Item doctype. Falls back gracefully if no items
    are configured for POS.
    """
    conditions = ["i.disabled = 0", "i.is_sales_item = 1"]
    args = []

    pos_profile = _get_user_pos_profile()
    if not pos_profile:
        return []

    allowed_item_groups = _get_allowed_item_groups_for_profile(pos_profile)
    if not allowed_item_groups:
        return []

    placeholders = ", ".join(["%s"] * len(allowed_item_groups))
    conditions.append(f"i.item_group IN ({placeholders})")
    args.extend(allowed_item_groups)

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(i.item_name LIKE %s OR i.item_code LIKE %s OR i.item_group LIKE %s)")
        args.extend([q, q, q])

    if category and category != "All Items":
        conditions.append("i.item_group = %s")
        args.append(category)

    where = " AND ".join(conditions)

    # Filter stock by the POS profile's warehouse so the correct bin is used.
    pos_warehouse = frappe.db.get_value("POS Profile", pos_profile, "warehouse") or None
    warehouse_join = "AND b.warehouse = %s" if pos_warehouse else ""
    join_args = [pos_warehouse] if pos_warehouse else []

    items = frappe.db.sql(f"""
        SELECT
            i.name AS item_code,
            i.item_name AS name,
            i.item_group AS category,
            COALESCE(p.price_list_rate, i.standard_rate, 0) AS price,
            i.image,
            i.stock_uom AS uom,
            i.is_stock_item,
            COALESCE(SUM(b.actual_qty), 0) AS stock
        FROM `tabItem` i
        LEFT JOIN `tabItem Price` p ON p.item_code = i.name
            AND p.selling = 1
            AND (p.price_list = 'Standard Selling' OR p.price_list IS NULL)
        LEFT JOIN `tabBin` b ON b.item_code = i.name
            {warehouse_join}
        WHERE {where}
        GROUP BY i.name
        ORDER BY i.item_group, i.item_name
        LIMIT 100
    """, tuple(join_args + args), as_dict=1)

    return items


@frappe.whitelist()
def get_pos_item_categories():
    """Return distinct item groups that have active sales items."""
    pos_profile = _get_user_pos_profile()
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
    """Search active check-in guests, walk-in customer, and table/bar entries for Bill To."""
    results = []

    # Resolve the actual walk-in customer name that exists in the system
    _walk_in_customer = None
    for _candidate in ("Walk In", "Guest", "Walk-in Customer", "Walk In Customer", "POS Customer", "Cash Customer"):
        if frappe.db.exists("Customer", _candidate):
            _walk_in_customer = _candidate
            break
    walk_in_entry = {"id": _walk_in_customer or "Walk In", "name": "Walk In", "room": None, "type": "Walk In"}

    if query:
        q_raw = cstr(query).strip()
        q = f"%{q_raw}%"
        q_lower = q_raw.lower()

        # Walk-in appears when query matches "walk" or "walk in"
        if q_lower in "walk in" or "walk" in q_lower:
            results.append(walk_in_entry)

        # Active check-in guests
        checkins = frappe.db.sql("""
            SELECT name AS id, guest AS name, room_number AS room, 'Direct Guest' AS type
            FROM `tabHotel Room Check In`
            WHERE status = 'Checked In' AND docstatus = 1
              AND (guest LIKE %s OR room_number LIKE %s)
            ORDER BY guest
            LIMIT 10
        """, (q, q), as_dict=1)
        results.extend(checkins)

        # Tables / bars from POS (just return generic label matches)
        table_names = ["Table 01", "Table 02", "Table 03", "Table 04", "Table 05",
                       "Bar 01", "Bar 02", "Bar 03"]
        for t in table_names:
            if q_lower in t.lower():
                typ = "Table" if t.startswith("Table") else "Bar"
                results.append({"id": t, "name": t, "room": None, "type": typ})
    else:
        # Walk-in always first in default results
        results.append(walk_in_entry)
        # Return first 5 active guests
        checkins = frappe.db.sql("""
            SELECT name AS id, guest AS name, room_number AS room, 'Direct Guest' AS type
            FROM `tabHotel Room Check In`
            WHERE status = 'Checked In' AND docstatus = 1
            ORDER BY guest
            LIMIT 5
        """, as_dict=1)
        results.extend(checkins)

    return results


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
                        service_charge=0, kitchen_note=None, pos_profile=None, discount_amount=0):
    """Create and submit a POS Invoice for non-room-posting settlements."""
    import json

    try:
        items = json.loads(items) if isinstance(items, str) else items
        if not items:
            frappe.throw(_("No items in cart"))

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
        if mode_of_payment not in allowed_modes:
            mode_of_payment = allowed_modes[0]

        customer = _resolve_pos_customer(customer, profile_doc=profile_doc, allow_guest_fallback=True)

        if not customer:
            frappe.throw(_("Set a valid default customer on POS Profile {0}. Optionally configure POS Settings.customer if available in your ERPNext version.").format(pos_profile))

        pi = frappe.new_doc("POS Invoice")
        pi.customer = customer
        pi.company = company
        pi.posting_date = nowdate()
        pi.pos_profile = pos_profile

        if _has_pos_opening_entry_on_invoice():
            pi.pos_opening_entry = pos_opening_entry.get("name")

        if kitchen_note:
            pi.remarks = kitchen_note

        for it in items:
            pi.append("items", {
                "item_code": it.get("item_code") or it.get("id"),
                "qty": flt(it.get("qty", 1)),
                "rate": flt(it.get("price", 0)),
            })

        _items_total = flt(sum(flt(i.get("price", 0)) * flt(i.get("qty", 1)) for i in items))
        pi.discount_amount = flt(discount_amount)
        pi.append("payments", {
            "mode_of_payment": mode_of_payment,
            "amount": max(0, _items_total - flt(discount_amount)),
        })

        pi.flags.ignore_permissions = True
        pi.set_missing_values()
        pi.insert()
        pi.submit()
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

    return {"pos_invoice": pi.name, "grand_total": flt(pi.grand_total)}


# ─────────────────────────────────────────────────────────────────────────────
# Post to Room
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def post_bill_to_room(items, check_in, service_charge=0, discount_amount=0, narration=None, kitchen_note=None, pos_profile=None):
    """Create a Sales Invoice linked to a Hotel Room Check In folio, then immediately
    create and consolidate a POS Invoice against the open shift so the transaction
    appears in shift reports without waiting for the end-of-shift consolidation job."""
    import json

    items = json.loads(items) if isinstance(items, str) else items
    if not items:
        frappe.throw(_("No items in cart"))

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

    # Discount
    disc = flt(discount_amount)
    if disc > 0:
        si.discount_amount = disc
        si.apply_discount_on = "Grand Total"

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

                items_total = flt(sum(
                    flt(it.get("price", 0)) * flt(it.get("qty", 1)) for it in items
                )) + flt(service_charge)
                net_amount = max(0.0, items_total - flt(discount_amount))

                if disc > 0:
                    pi.discount_amount = disc
                    pi.apply_discount_on = "Grand Total"

                pi.append("payments", {
                    "mode_of_payment": mode_of_payment,
                    "amount": net_amount,
                })

                pi.flags.ignore_permissions = True
                pi.set_missing_values()
                pi.insert()
                pi.submit()

                # Mark as immediately consolidated — the room folio Sales Invoice
                # serves as the consolidated invoice; no end-of-shift re-processing needed.
                frappe.db.set_value("POS Invoice", pi.name, "consolidated_invoice", si.name)
                frappe.db.commit()
                pos_invoice_name = pi.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Post to Room POS Invoice consolidation failed")
        # Non-fatal: the room folio Sales Invoice was already committed; continue.

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

    # When re-holding a resumed order, delete the previous draft to avoid duplicates
    if existing_draft and frappe.db.exists("POS Invoice", existing_draft):
        try:
            old_pi = frappe.get_doc("POS Invoice", existing_draft)
            if old_pi.docstatus == 0:
                old_pi.flags.ignore_permissions = True
                old_pi.delete()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Failed to delete old draft on re-hold")

    company = frappe.db.get_single_value("Global Defaults", "default_company") or ""

    if not pos_profile:
        pos_profile = _get_user_pos_profile()
    if not pos_profile:
        frappe.throw(_("No POS Profile is mapped to your user."))

    profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
    customer = _resolve_pos_customer(customer, profile_doc=profile_doc, allow_guest_fallback=True)
    if not customer:
        frappe.throw(_("Set a valid default customer on POS Profile {0}. Optionally configure POS Settings.customer if available in your ERPNext version.").format(pos_profile))

    pi = frappe.new_doc("POS Invoice")
    pi.customer = customer
    pi.company = company
    pi.posting_date = nowdate()
    pi.pos_profile = pos_profile
    if kitchen_note:
        pi.remarks = kitchen_note

    for it in items:
        pi.append("items", {
            "item_code": it.get("item_code") or it.get("id"),
            "qty": flt(it.get("qty", 1)),
            "rate": flt(it.get("price", 0)),
        })

    # Keep one payment row to satisfy POS validations while still saving as draft.
    _draft_total = flt(sum(flt(i.get("price", 0)) * flt(i.get("qty", 1)) for i in items))
    pi.discount_amount = flt(discount_amount)
    pi.append("payments", {
        "mode_of_payment": "Cash",
        "amount": max(0, _draft_total - flt(discount_amount)),
    })

    try:
        pi.flags.ignore_permissions = True
        pi.set_missing_values()
        pi.insert()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS draft invoice creation failed")
        frappe.throw(_("Failed to save draft order. Please check POS profile and opening entry."))

    return {
        "pos_invoice": pi.name,
        "grand_total": flt(pi.grand_total),
        "status": "Draft",
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
        conditions.append("(pi.name LIKE %s OR pi.customer LIKE %s)")
        args.extend([q, q])

    if cashier:
        conditions.append("pi.owner = %s")
        args.append(cashier)

    where = " AND ".join(conditions)

    drafts = frappe.db.sql(f"""
        SELECT
            pi.name AS invoice,
            pi.customer,
            pi.pos_profile,
            pi.grand_total AS amount,
            pi.posting_date,
            pi.owner AS cashier,
            pi.remarks AS note,
            TIMESTAMPDIFF(MINUTE, pi.creation, NOW()) AS age_minutes,
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
        age = int(d.get("age_minutes") or 0)
        h, m = divmod(age, 60)
        d["age"] = f"{h}h {m}m" if h else f"{m}m"
        d["service_point"] = d.get("pos_profile") or "—"

    return drafts


@frappe.whitelist()
def get_draft_pos_stats():
    """Return stat card values for the Draft Orders modal."""
    total = frappe.db.count("POS Invoice", {"docstatus": 0})
    total_value = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabPOS Invoice` WHERE docstatus = 0
    """)[0][0] or 0
    oldest = frappe.db.sql("""
        SELECT TIMESTAMPDIFF(MINUTE, MIN(creation), NOW())
        FROM `tabPOS Invoice` WHERE docstatus = 0
    """)[0][0] or 0

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
        if status == "Posted":
            conditions.append("pi.docstatus = 0")
        elif status == "Paid":
            conditions.append("pi.docstatus = 1")
        elif status == "Void":
            conditions.append("pi.docstatus = 2")

    where = " AND ".join(conditions)

    invoices = frappe.db.sql(f"""
        SELECT
            pi.name AS invoice_no,
            pi.customer,
            pi.grand_total,
            pi.posting_date,
            pi.owner AS cashier,
            pi.pos_profile AS terminal,
            pi.docstatus,
            CASE pi.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Paid'
                WHEN 2 THEN 'Void'
            END AS status
        FROM `tabPOS Invoice` pi
        WHERE {where}
        ORDER BY pi.creation DESC
        LIMIT %s OFFSET %s
    """, tuple(args) + (int(page_length), int(start)), as_dict=1)

    return invoices


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
        entry_start = getdate(entry_doc.period_start_date)
        gross = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabPOS Invoice`
            WHERE pos_profile = %s
              AND owner = %s
              AND posting_date >= %s
              AND docstatus = 1
        """, (entry_doc.pos_profile, entry_doc.user, entry_start))[0][0] or 0

        open_drafts = frappe.db.count("POS Invoice", {
            "pos_profile": entry_doc.pos_profile,
            "owner": entry_doc.user,
            "posting_date": [">=", entry_start],
            "docstatus": 0,
        })

        # Fallback grouping by profile + user + opening date when no explicit shift link exists.
        tender = frappe.db.sql("""
            SELECT
                pip.mode_of_payment AS payment_type,
                COALESCE(SUM(pip.amount), 0) AS system_amount
            FROM `tabPOS Invoice` pi
            JOIN `tabSales Invoice Payment` pip ON pip.parent = pi.name
            WHERE pi.pos_profile = %s
              AND pi.owner = %s
              AND pi.posting_date >= %s
              AND pi.docstatus = 1
            GROUP BY pip.mode_of_payment
        """, (entry_doc.pos_profile, entry_doc.user, entry_start), as_dict=1)

    for t in tender:
        t["editable"] = t["payment_type"] == "Cash"
        t["counted"] = t["system_amount"]
        t["diff"] = 0

    # Additional stats for the Shift Close summary panel
    if _has_pos_opening_entry_on_invoice():
        bills_processed = frappe.db.count("POS Invoice", {"pos_opening_entry": pos_opening_entry, "docstatus": 1})
        voided_count = frappe.db.count("POS Invoice", {"pos_opening_entry": pos_opening_entry, "docstatus": 2})
    else:
        entry_start = getdate(entry_doc.period_start_date)
        bills_processed = frappe.db.count("POS Invoice", {
            "pos_profile": entry_doc.pos_profile, "owner": entry_doc.user,
            "posting_date": [">=", entry_start], "docstatus": 1,
        })
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
        "net_collections": flt(gross),
        "open_drafts": int(open_drafts),
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
def close_pos_shift(pos_opening_entry, tender_rows=None, closing_note=None):
    """Create a POS Closing Entry to close the active shift."""
    import json

    tender_rows = json.loads(tender_rows) if isinstance(tender_rows, str) else (tender_rows or [])

    if not frappe.db.exists("POS Opening Entry", pos_opening_entry):
        frappe.throw(_("POS Opening Entry {0} not found").format(pos_opening_entry))

    entry_doc = frappe.get_doc("POS Opening Entry", pos_opening_entry)

    closing = frappe.new_doc("POS Closing Entry")
    closing.pos_opening_entry = pos_opening_entry
    closing.pos_profile = entry_doc.pos_profile
    closing.user = entry_doc.user
    closing.company = entry_doc.company
    closing.period_start_date = entry_doc.period_start_date
    closing.period_end_date = now_datetime()
    closing.posting_date = nowdate()
    if closing_note:
        closing.notes = closing_note

    # Payment reconciliation
    for row in tender_rows:
        counted = flt(row.get("counted", row.get("system_amount", 0)))
        system = flt(row.get("system_amount", 0))
        closing.append("payment_reconciliation", {
            "mode_of_payment": row.get("payment_type"),
            "opening_amount": system,
            "expected_amount": system,
            "closing_amount": counted,
            "difference": counted - system,
        })

    try:
        closing.flags.ignore_permissions = True
        closing.set_missing_values()
        closing.insert()
        closing.submit()

        # Update the opening entry status
        frappe.db.set_value("POS Opening Entry", pos_opening_entry, "status", "Closed")
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS Shift close failed")
        frappe.throw(_("Failed to close POS shift. Please check configuration."))

    return {"closing_entry": closing.name}


# ─────────────────────────────────────────────────────────────────────────────
# Staff Roster (uses Employee Checkin / Shift Assignment from HRMS)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pos_staff_roster(outlet=None, shift=None, role=None, search=None):
    """Return POS staff shift assignments for the current week."""
    today = getdate(nowdate())
    week_start = today - __import__('datetime').timedelta(days=today.weekday())
    week_end = week_start + __import__('datetime').timedelta(days=6)

    conditions = ["sa.status = 'Active'"]
    args = []

    if shift:
        conditions.append("sa.shift_type = %s")
        args.append(shift)

    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append("(e.employee_name LIKE %s OR e.name LIKE %s)")
        args.extend([q, q])

    where = " AND ".join(conditions)

    staff = frappe.db.sql(f"""
        SELECT
            e.name AS employee,
            e.employee_name,
            e.designation AS role,
            e.department AS outlet,
            sa.shift_type AS shift,
            sa.start_date,
            sa.end_date
        FROM `tabShift Assignment` sa
        JOIN `tabEmployee` e ON e.name = sa.employee
        WHERE {where}
          AND sa.start_date <= %s AND (sa.end_date IS NULL OR sa.end_date >= %s)
        ORDER BY e.employee_name
        LIMIT 100
    """, tuple(args) + (cstr(week_end), cstr(week_start)), as_dict=1)

    if outlet:
        staff = [s for s in staff if outlet.lower() in (s.get("outlet") or "").lower()]

    return staff


@frappe.whitelist()
def get_pos_staff_roster_stats():
    """Return stat cards for the Staff Roster page."""
    today = getdate(nowdate())
    week_start = today - __import__('datetime').timedelta(days=today.weekday())
    week_end = week_start + __import__('datetime').timedelta(days=6)

    total = frappe.db.sql("""
        SELECT COUNT(DISTINCT employee) FROM `tabShift Assignment`
        WHERE status = 'Active'
          AND start_date <= %s AND (end_date IS NULL OR end_date >= %s)
    """, (cstr(week_end), cstr(week_start)))[0][0] or 0

    return {
        "scheduled_staff": int(total),
        "morning_coverage": 100,
        "evening_coverage": 83,
        "staff_off": 0,
    }


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
        "customer": pi.customer or "",
        "items": items,
        "remarks": pi.remarks or "",
        "discount_amount": flt(pi.discount_amount or 0),
    }


@frappe.whitelist()
def delete_pos_draft_invoice(invoice_name):
    """Cancel and delete a draft POS Invoice."""
    if not frappe.db.exists("POS Invoice", invoice_name):
        frappe.throw(_("Invoice {0} not found").format(invoice_name))

    pi = frappe.get_doc("POS Invoice", invoice_name)
    if pi.docstatus != 0:
        frappe.throw(_("Only draft invoices can be deleted."))

    try:
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
    """Return open table orders — draft POS Invoices whose customer is a table or bar name."""
    drafts = frappe.db.sql("""
        SELECT
            pi.name AS invoice,
            pi.customer,
            pi.grand_total AS bill,
            pi.owner AS cashier,
            pi.remarks AS notes,
            TIMESTAMPDIFF(MINUTE, pi.creation, NOW()) AS age_minutes,
            DATE_FORMAT(pi.creation, '%%h:%%i %%p') AS open_time,
            COUNT(pit.name) AS item_count
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabPOS Invoice Item` pit ON pit.parent = pi.name
        WHERE pi.docstatus = 0
          AND (
            pi.customer LIKE 'Table %%'
            OR pi.customer LIKE 'Bar %%'
            OR pi.customer LIKE 'Pool%%'
          )
        GROUP BY pi.name
        ORDER BY pi.creation DESC
        LIMIT 50
    """, as_dict=1)

    result = []
    for idx, d in enumerate(drafts):
        items = frappe.db.sql("""
            SELECT item_code, item_name AS name, qty,
                   rate AS price, (qty * rate) AS amount
            FROM `tabPOS Invoice Item`
            WHERE parent = %s
        """, d["invoice"], as_dict=1)
        age = int(d.get("age_minutes") or 0)
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
                COUNT(DISTINCT CASE WHEN pi.docstatus = 0 THEN pi.name END) AS open_drafts
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
                COUNT(DISTINCT CASE WHEN pi.docstatus = 0 THEN pi.name END) AS open_drafts
            FROM `tabPOS Opening Entry` poe
            LEFT JOIN `tabUser` u ON u.name = poe.user
            LEFT JOIN `tabPOS Invoice` pi
                ON pi.pos_profile = poe.pos_profile
                AND pi.owner = poe.user
                AND pi.posting_date >= DATE(poe.period_start_date)
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

    return rows
