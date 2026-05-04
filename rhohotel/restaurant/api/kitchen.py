import frappe
from frappe import _
from frappe.utils import flt, cstr, now_datetime
from frappe.utils.nestedset import get_descendants_of


# ─────────────────────────────────────────────────────────────────────────────
# Kitchen Item Groups
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_kitchen_item_groups():
    """Return all item groups (including descendants) configured as kitchen items."""
    raw = frappe.db.get_single_value("Restaurant Settings", "kitchen_item_groups") or "[]"
    try:
        base_groups = frappe.parse_json(raw) or []
    except Exception:
        base_groups = []

    if not base_groups:
        return []

    result = set(base_groups)
    for g in list(base_groups):
        try:
            result.update(get_descendants_of("Item Group", g))
        except Exception:
            pass

    return sorted(result)


# ─────────────────────────────────────────────────────────────────────────────
# Send to Kitchen
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def send_to_kitchen(items, pos_invoice=None, kitchen_note=None, table_or_room=None, source=None):
    """Create a Kitchen Order Ticket for the given items.

    ``items`` is a JSON array of:
        {item_code, item_name, qty, notes}

    Returns the created ticket name and a list of sent item_codes so the
    frontend can mark those cart rows as sent.
    """
    import json

    items = json.loads(items) if isinstance(items, str) else items
    if not items:
        frappe.throw(_("No items to send to kitchen"))

    sent_qty_by_code = {}
    if pos_invoice:
        sent_rows = frappe.db.sql(
            """
            SELECT
                kti.item_code,
                SUM(kti.quantity) AS sent_qty
            FROM `tabKitchen Order Ticket` kt
            INNER JOIN `tabKitchen Order Ticket Item` kti ON kti.parent = kt.name
            WHERE kt.pos_invoice = %s
              AND kt.docstatus = 0
            GROUP BY kti.item_code
            """,
            (pos_invoice,),
            as_dict=1,
        )
        sent_qty_by_code = {
            cstr(r.get("item_code")): flt(r.get("sent_qty")) for r in sent_rows if r.get("item_code")
        }

    normalized_items = []
    for it in items:
        item_code = cstr(it.get("item_code") or it.get("id"))
        requested_qty = flt(it.get("qty", 1))
        already_sent = flt(sent_qty_by_code.get(item_code))
        qty_to_send = requested_qty - already_sent

        if qty_to_send <= 0:
            continue

        normalized_items.append(
            {
                "item_code": item_code,
                "item_name": cstr(it.get("item_name") or it.get("name")),
                "quantity": qty_to_send,
                "notes": cstr(it.get("notes") or ""),
            }
        )

    if not normalized_items:
        return {
            "ticket": None,
            "item_codes": [],
            "item_count": 0,
            "skipped": True,
            "message": _("All kitchen items were already sent for this order."),
        }

    ticket = frappe.new_doc("Kitchen Order Ticket")
    ticket.pos_invoice = pos_invoice or None
    ticket.table_or_room = table_or_room or ""
    ticket.source = source or "Restaurant Dining"
    ticket.status = "Pending"
    ticket.notes = kitchen_note or ""
    ticket.sent_at = now_datetime()

    for row in normalized_items:
        ticket.append("items", row)

    ticket.flags.ignore_mandatory = True
    ticket.flags.ignore_permissions = True
    ticket.insert()
    frappe.db.commit()

    return {
        "ticket": ticket.name,
        "item_codes": [row["item_code"] for row in normalized_items],
        "item_count": len(normalized_items),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sent Items Query (for POS cart state restoration)
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sent_to_kitchen_items(pos_invoice):
    """Return item_codes and total quantities already sent to kitchen
    for the given POS Invoice (across all its tickets)."""
    if not pos_invoice:
        return []

    rows = frappe.db.sql(
        """
        SELECT
            kti.item_code,
            kti.item_name,
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
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Kitchen Board
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_kitchen_tickets(search=None, station=None, source=None, status=None):
    """Return active Kitchen Order Tickets for the live board."""
    conditions = ["kt.docstatus = 0", "kt.status != 'Served'"]
    args = []

    if status and status != "All":
        conditions.append("kt.status = %s")
        args.append(status)
    if source:
        conditions.append("kt.source = %s")
        args.append(source)
    if station:
        conditions.append("kt.chef_station = %s")
        args.append(station)
    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append(
            "(kt.name LIKE %s OR kt.table_or_room LIKE %s OR kt.pos_invoice LIKE %s)"
        )
        args.extend([q, q, q])

    where = " AND ".join(conditions)

    tickets = frappe.db.sql(
        f"""
        SELECT
            kt.name AS id,
            kt.pos_invoice,
            kt.table_or_room,
            kt.source,
            kt.chef_station,
            kt.status,
            kt.notes,
            kt.sent_at,
            TIMESTAMPDIFF(MINUTE, kt.sent_at, NOW()) AS age_minutes
        FROM `tabKitchen Order Ticket` kt
        WHERE {where}
        ORDER BY kt.sent_at ASC
        LIMIT 150
        """,
        tuple(args),
        as_dict=1,
    )

    for t in tickets:
        t["items"] = frappe.db.sql(
            """
            SELECT item_code, item_name, quantity AS qty, notes
            FROM `tabKitchen Order Ticket Item`
            WHERE parent = %s
            """,
            t["id"],
            as_dict=1,
        )
        age = int(t.get("age_minutes") or 0)
        h, m = divmod(age, 60)
        t["age"] = f"{h}h {m}m" if h else f"{m}m"
        t["mins"] = age

    return tickets


@frappe.whitelist()
def get_kitchen_stats():
    """Return ticket counts per status for the stats bar."""
    rows = frappe.db.sql(
        """
        SELECT status, COUNT(*) AS count
        FROM `tabKitchen Order Ticket`
        WHERE docstatus = 0
        GROUP BY status
        """,
        as_dict=1,
    )
    stats = {r["status"]: r["count"] for r in rows}
    return {
        "new": stats.get("Pending", 0),
        "preparing": stats.get("In Progress", 0),
        "ready": stats.get("Ready", 0),
        "delayed": stats.get("Delayed", 0),
        "served": stats.get("Served", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Status Updates
# ─────────────────────────────────────────────────────────────────────────────

_VALID_STATUSES = {"Pending", "In Progress", "Ready", "Delayed", "Served"}


@frappe.whitelist()
def update_ticket_status(ticket_name, status):
    """Update the status of a Kitchen Order Ticket."""
    if status not in _VALID_STATUSES:
        frappe.throw(_("Invalid status: {0}").format(status))
    if not frappe.db.exists("Kitchen Order Ticket", ticket_name):
        frappe.throw(_("Ticket {0} not found").format(ticket_name))

    frappe.db.set_value("Kitchen Order Ticket", ticket_name, "status", status)
    frappe.db.commit()
    return {"ticket": ticket_name, "status": status}
