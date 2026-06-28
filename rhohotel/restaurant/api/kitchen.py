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

    payload = _get_ticket_event_payload(ticket.name)
    for room in ("all", "website"):
        frappe.publish_realtime("rhohotel_kitchen_ticket_created", payload, room=room)

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

def _get_ticket_event_payload(ticket_name):
    ticket = frappe.get_doc("Kitchen Order Ticket", ticket_name)
    pos_profile = ""
    if ticket.pos_invoice:
        pos_profile = frappe.db.get_value("POS Invoice", ticket.pos_invoice, "pos_profile") or ""

    return {
        "id": ticket.name,
        "pos_invoice": ticket.pos_invoice,
        "table_or_room": ticket.table_or_room,
        "source": ticket.source,
        "chef_station": ticket.chef_station,
        "status": ticket.status,
        "notes": ticket.notes,
        "sent_at": cstr(ticket.sent_at),
        "pos_profile": pos_profile,
        "items": [
            {
                "item_code": row.item_code,
                "item_name": row.item_name,
                "qty": row.quantity,
                "notes": row.notes,
            }
            for row in ticket.items
        ],
    }


def _coerce_delay_minutes(value, fallback):
    return max(1, int(flt(value) or fallback))


def _mark_stale_tickets_delayed(pending_delay_minutes=25, preparing_delay_minutes=35):
    pending_delay_minutes = max(1, int(flt(pending_delay_minutes) or 25))
    preparing_delay_minutes = max(1, int(flt(preparing_delay_minutes) or 35))

    # Auto-transition stale tickets based on configured preparation thresholds.
    frappe.db.sql("""
        UPDATE `tabKitchen Order Ticket`
        SET status = 'Delayed'
        WHERE docstatus = 0
          AND status IN ('Pending', 'In Progress')
                    AND TIMESTAMPDIFF(
                                MINUTE,
                                CASE WHEN status = 'Pending' THEN sent_at ELSE modified END,
                                NOW()
                            ) >=
              CASE WHEN status = 'Pending' THEN %s ELSE %s END
    """, (pending_delay_minutes, preparing_delay_minutes))
    frappe.db.commit()


@frappe.whitelist()
def get_kitchen_tickets(search=None, station=None, source=None, status=None,
                        pending_delay_minutes=25, preparing_delay_minutes=35):
    """Return active Kitchen Order Tickets for the live board."""
    pending_delay_minutes = _coerce_delay_minutes(pending_delay_minutes, 25)
    preparing_delay_minutes = _coerce_delay_minutes(preparing_delay_minutes, 35)
    _mark_stale_tickets_delayed(pending_delay_minutes, preparing_delay_minutes)

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
            kt.modified,
            COALESCE(pi.pos_profile, '') AS pos_profile,
            GREATEST(0, TIMESTAMPDIFF(MINUTE, kt.sent_at, NOW())) AS age_minutes,
            GREATEST(
                0,
                TIMESTAMPDIFF(
                    MINUTE,
                    CASE
                        WHEN kt.status IN ('In Progress', 'Ready') THEN kt.modified
                        ELSE kt.sent_at
                    END,
                    NOW()
                )
            ) AS stage_age_minutes
        FROM `tabKitchen Order Ticket` kt
        LEFT JOIN `tabPOS Invoice` pi ON pi.name = kt.pos_invoice
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
        raw_stage_age = t.get("stage_age_minutes")
        stage_age = int(raw_stage_age if raw_stage_age is not None else age)
        h, m = divmod(age, 60)
        stage_h, stage_m = divmod(stage_age, 60)
        t["age"] = f"{h}h {m}m" if h else f"{m}m"
        t["mins"] = age
        t["stage_age"] = f"{stage_h}h {stage_m}m" if stage_h else f"{stage_m}m"
        t["stage_mins"] = stage_age

    return tickets


@frappe.whitelist()
def get_kitchen_stats(pending_delay_minutes=25, preparing_delay_minutes=35):
    """Return ticket counts per status for the stats bar."""
    pending_delay_minutes = _coerce_delay_minutes(pending_delay_minutes, 25)
    preparing_delay_minutes = _coerce_delay_minutes(preparing_delay_minutes, 35)
    _mark_stale_tickets_delayed(pending_delay_minutes, preparing_delay_minutes)

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


@frappe.whitelist()
def get_kitchen_pos_profiles():
    """Return distinct POS profiles currently referenced by active kitchen tickets."""
    rows = frappe.db.sql(
        """
        SELECT DISTINCT pi.pos_profile
        FROM `tabKitchen Order Ticket` kt
        INNER JOIN `tabPOS Invoice` pi ON pi.name = kt.pos_invoice
        WHERE kt.docstatus = 0
          AND kt.status != 'Served'
          AND pi.pos_profile IS NOT NULL
          AND pi.pos_profile != ''
        ORDER BY pi.pos_profile ASC
        """,
        as_dict=1,
    )
    return [r["pos_profile"] for r in rows]


@frappe.whitelist()
def get_kitchen_order_report(
    date_from=None,
    date_to=None,
    status=None,
    source=None,
    station=None,
    pos_profile=None,
    search=None,
    limit=500,
):
    """Return kitchen order report rows and summary metrics."""
    row_limit = max(1, min(int(flt(limit) or 500), 2000))

    conditions = ["kt.docstatus = 0"]
    args = []

    if date_from:
        conditions.append("DATE(kt.sent_at) >= %s")
        args.append(date_from)
    if date_to:
        conditions.append("DATE(kt.sent_at) <= %s")
        args.append(date_to)
    if status and status != "All":
        conditions.append("kt.status = %s")
        args.append(status)
    if source:
        conditions.append("kt.source = %s")
        args.append(source)
    if station:
        conditions.append("kt.chef_station = %s")
        args.append(station)
    if pos_profile:
        conditions.append("COALESCE(pi.pos_profile, '') = %s")
        args.append(pos_profile)
    if search:
        q = f"%{cstr(search).strip()}%"
        conditions.append(
            "(" 
            "kt.name LIKE %s OR "
            "kt.table_or_room LIKE %s OR "
            "kt.pos_invoice LIKE %s OR "
            "kt.notes LIKE %s"
            ")"
        )
        args.extend([q, q, q, q])

    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            kt.name AS ticket_name,
            kt.pos_invoice,
            COALESCE(pi.pos_profile, '') AS pos_profile,
            kt.table_or_room,
            kt.source,
            COALESCE(kt.chef_station, '') AS chef_station,
            kt.status,
            kt.notes,
            kt.sent_at,
            kt.modified,
            COALESCE(COUNT(kti.name), 0) AS item_count,
            COALESCE(SUM(kti.quantity), 0) AS total_qty,
            GREATEST(0, TIMESTAMPDIFF(MINUTE, kt.sent_at, NOW())) AS age_minutes,
            GREATEST(
                0,
                TIMESTAMPDIFF(
                    MINUTE,
                    CASE
                        WHEN kt.status IN ('In Progress', 'Ready', 'Delayed', 'Served') THEN kt.modified
                        ELSE kt.sent_at
                    END,
                    NOW()
                )
            ) AS stage_age_minutes
        FROM `tabKitchen Order Ticket` kt
        LEFT JOIN `tabPOS Invoice` pi ON pi.name = kt.pos_invoice
        LEFT JOIN `tabKitchen Order Ticket Item` kti ON kti.parent = kt.name
        WHERE {where}
        GROUP BY kt.name
        ORDER BY kt.sent_at DESC
        LIMIT {row_limit}
        """,
        tuple(args),
        as_dict=1,
    )

    status_counts = {
        "Pending": 0,
        "In Progress": 0,
        "Ready": 0,
        "Delayed": 0,
        "Served": 0,
    }
    total_items = 0
    total_stage_minutes = 0

    for row in rows:
        st = cstr(row.get("status"))
        if st in status_counts:
            status_counts[st] += 1
        total_items += int(flt(row.get("total_qty") or 0))
        total_stage_minutes += int(flt(row.get("stage_age_minutes") or 0))

    total_tickets = len(rows)
    avg_stage_minutes = (total_stage_minutes / total_tickets) if total_tickets else 0

    return {
        "summary": {
            "total_tickets": total_tickets,
            "pending_count": status_counts["Pending"],
            "in_progress_count": status_counts["In Progress"],
            "ready_count": status_counts["Ready"],
            "delayed_count": status_counts["Delayed"],
            "served_count": status_counts["Served"],
            "total_items": total_items,
            "avg_stage_minutes": round(avg_stage_minutes, 1),
        },
        "rows": rows,
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
