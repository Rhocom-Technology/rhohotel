import frappe
import json
from frappe.utils import nowdate, now_datetime, flt


@frappe.whitelist()
def get_complimentary_dashboard():
    """Stats for the complimentary dashboard page."""
    today = nowdate()

    issued_today = frappe.db.count("Hotel Complimentary", {"issue_date": today})
    pending_approval = frappe.db.count("Hotel Complimentary", {"status": "Pending"})
    consumed_today = frappe.db.count("Hotel Complimentary", {"status": "Consumed", "issue_date": today})
    active_count = frappe.db.count(
        "Hotel Complimentary",
        {"status": ["in", ["Approved", "In Progress"]]}
    )
    expired_unused = frappe.db.count("Hotel Complimentary", {"status": "Expired"})

    # Budget impact: sum of value for today's records
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(value), 0) as total
        FROM `tabHotel Complimentary`
        WHERE issue_date = %s
    """, (today,), as_dict=1)
    budget_impact_today = flt(result[0].total) if result else 0.0

    return {
        "issued_today": issued_today,
        "pending_approval": pending_approval,
        "consumed_today": consumed_today,
        "active_count": active_count,
        "expired_unused": expired_unused,
        "budget_impact_today": budget_impact_today,
    }


@frappe.whitelist()
def get_complimentary_list(
    search=None,
    filter_type=None,
    filter_status=None,
    filter_approver=None,
    page=1,
    page_size=25
):
    """Paginated complimentary list with optional filters."""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = {}
    if filter_type:
        filters["complimentary_type"] = filter_type
    if filter_status:
        filters["status"] = filter_status
    if filter_approver:
        filters["approval_level"] = filter_approver

    fields = [
        "name", "guest", "room", "complimentary_type", "department",
        "value", "status", "approval_level", "issue_date", "expiry_date",
        "source_category", "note", "reason"
    ]

    if search:
        q = f"%{search}%"
        records = frappe.db.sql("""
            SELECT name, guest, room, complimentary_type, department,
                   value, status, approval_level, issue_date, expiry_date,
                   source_category, note, reason
            FROM `tabHotel Complimentary`
            WHERE (name LIKE %(q)s OR guest LIKE %(q)s OR room LIKE %(q)s
                   OR complimentary_type LIKE %(q)s OR approval_level LIKE %(q)s)
            ORDER BY issue_date DESC, modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"q": q, "limit": page_size, "offset": (page - 1) * page_size}, as_dict=1)

        count_result = frappe.db.sql("""
            SELECT COUNT(name) as cnt
            FROM `tabHotel Complimentary`
            WHERE (name LIKE %(q)s OR guest LIKE %(q)s OR room LIKE %(q)s
                   OR complimentary_type LIKE %(q)s OR approval_level LIKE %(q)s)
        """, {"q": q}, as_dict=1)
        total = count_result[0].cnt if count_result else 0
    else:
        records = frappe.get_all(
            "Hotel Complimentary",
            filters=filters,
            fields=fields,
            order_by="issue_date desc, modified desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size,
        )
        total = frappe.db.count("Hotel Complimentary", filters)

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_complimentary(complimentary_name):
    """Full detail of a single complimentary record."""
    if not frappe.db.exists("Hotel Complimentary", complimentary_name):
        frappe.throw(
            f"Complimentary record '{complimentary_name}' not found",
            frappe.DoesNotExistError
        )

    doc = frappe.get_doc("Hotel Complimentary", complimentary_name)

    # Fetch change log for audit trail
    audit_trail = []
    try:
        logs = frappe.get_all(
            "Version",
            filters={"ref_doctype": "Hotel Complimentary", "docname": complimentary_name},
            fields=["creation", "owner", "data"],
            order_by="creation asc",
            limit_page_length=20,
        )
        for log in logs:
            try:
                data = json.loads(log.data) if isinstance(log.data, str) else log.data
                changed = data.get("changed", [])
                if changed:
                    changes = "; ".join(
                        f"{c[0]}: {c[1]} → {c[2]}"
                        for c in changed
                        if len(c) >= 3
                    )
                    audit_trail.append({
                        "time": str(log.creation),
                        "action": f"Changed by {log.owner}: {changes}",
                    })
            except Exception:
                audit_trail.append({
                    "time": str(log.creation),
                    "action": f"Updated by {log.owner}",
                })
    except Exception:
        pass

    # Creation entry
    audit_trail.insert(0, {
        "time": str(doc.creation),
        "action": f"Created by {doc.owner}",
    })

    if doc.approved_on:
        audit_trail.append({
            "time": str(doc.approved_on),
            "action": f"Approved by {doc.approved_by or 'Manager'}",
        })
    if doc.consumed_on:
        audit_trail.append({
            "time": str(doc.consumed_on),
            "action": "Marked as consumed",
        })

    return {
        "name": doc.name,
        "guest": doc.guest,
        "room": doc.room,
        "reservation": doc.reservation,
        "complimentary_type": doc.complimentary_type,
        "department": doc.department,
        "value": doc.value,
        "quantity": doc.quantity,
        "issue_date": str(doc.issue_date) if doc.issue_date else None,
        "expiry_date": str(doc.expiry_date) if doc.expiry_date else None,
        "reason": doc.reason,
        "redemption_rule": doc.redemption_rule,
        "note": doc.note,
        "status": doc.status,
        "approval_level": doc.approval_level,
        "source_category": doc.source_category,
        "issued_by": doc.issued_by,
        "approved_by": doc.approved_by,
        "approved_on": str(doc.approved_on) if doc.approved_on else None,
        "consumption_reference": doc.consumption_reference,
        "consumed_on": str(doc.consumed_on) if doc.consumed_on else None,
        "audit_trail": audit_trail,
    }


@frappe.whitelist()
def create_complimentary(complimentary_data):
    """Create a new Hotel Complimentary record."""
    if isinstance(complimentary_data, str):
        complimentary_data = json.loads(complimentary_data)

    try:
        doc = frappe.new_doc("Hotel Complimentary")
        doc.guest = complimentary_data.get("guest", "")
        doc.room = complimentary_data.get("room", "")
        doc.reservation = complimentary_data.get("reservation") or None
        doc.complimentary_type = complimentary_data.get("complimentary_type", "")
        doc.department = complimentary_data.get("department", "")
        doc.value = flt(complimentary_data.get("value") or 0)
        doc.quantity = complimentary_data.get("quantity") or "1"
        doc.issue_date = complimentary_data.get("issue_date") or nowdate()
        doc.expiry_date = complimentary_data.get("expiry_date") or None
        doc.reason = complimentary_data.get("reason") or ""
        doc.redemption_rule = complimentary_data.get("redemption_rule") or ""
        doc.note = complimentary_data.get("note") or ""
        doc.approval_level = complimentary_data.get("approval_level", "General Manager")
        doc.source_category = complimentary_data.get("source_category") or ""
        doc.status = "Pending"
        doc.issued_by = frappe.session.user

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "complimentary_name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def approve_complimentary(complimentary_name):
    """Approve a pending complimentary record."""
    try:
        doc = frappe.get_doc("Hotel Complimentary", complimentary_name)

        if doc.status not in ("Pending", "In Progress"):
            return {"success": False, "error": f"Cannot approve a record with status '{doc.status}'"}

        doc.status = "Approved"
        doc.approved_by = frappe.session.user
        doc.approved_on = now_datetime()
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "approve_complimentary error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def mark_consumed(complimentary_name, consumption_reference=None):
    """Mark a complimentary record as consumed."""
    try:
        doc = frappe.get_doc("Hotel Complimentary", complimentary_name)

        if doc.status == "Consumed":
            return {"success": False, "error": "Record is already consumed"}
        if doc.status in ("Cancelled", "Expired"):
            return {"success": False, "error": f"Cannot consume a record with status '{doc.status}'"}

        doc.status = "Consumed"
        doc.consumed_on = now_datetime()
        if consumption_reference:
            doc.consumption_reference = consumption_reference
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "mark_consumed error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_complimentary(complimentary_name):
    """Cancel a complimentary record."""
    try:
        doc = frappe.get_doc("Hotel Complimentary", complimentary_name)

        if doc.status == "Consumed":
            return {"success": False, "error": "Cannot cancel a consumed record"}
        if doc.status == "Cancelled":
            return {"success": False, "error": "Record is already cancelled"}

        doc.status = "Cancelled"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_complimentary error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_active_checkins():
    """Return currently checked-in guests and their rooms for the complimentary form."""
    try:
        rows = frappe.db.sql("""
            SELECT ci.name as check_in, ci.guest, ci.room_number
            FROM `tabHotel Room Check In` ci
            WHERE ci.status = 'Checked In'
              AND ci.docstatus = 1
            ORDER BY ci.room_number ASC
        """, as_dict=True)

        checkins = []
        for r in rows:
            guest_display = r.guest or ""
            if guest_display:
                guest_display = (
                    frappe.db.get_value("Hotel Guest", r.guest, "hotel_guest_name")
                    or r.guest
                )
            checkins.append({
                "check_in": r.check_in,
                "guest": guest_display,
                "room_number": r.room_number or "",
            })

        return {"checkins": checkins}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_active_checkins error")
        return {"checkins": []}
