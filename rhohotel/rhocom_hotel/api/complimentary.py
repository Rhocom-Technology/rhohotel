import frappe
import json
from frappe import _
from frappe.utils import nowdate, now_datetime, flt, getdate, cstr

DOCTYPE = "Hotel Complimentary"
MANAGER_ROLES = {"System Manager", "Hotel Manager"}
APPROVAL_ROLES = {
    "General Manager": {"System Manager", "Hotel Manager"},
    "Duty Manager": {"System Manager", "Hotel Manager", "Front Desk Manager"},
    "Front Desk Supervisor": {"System Manager", "Hotel Manager", "Front Desk Manager"},
    "Operations Lead": {"System Manager", "Hotel Manager", "Front Desk Manager"},
}
CONSUMPTION_ROLES = {
    "Restaurant": {"System Manager", "Hotel Manager", "Front Desk Manager", "Restaurant Manager","Sales User"},
    "Front Desk": {"System Manager", "Hotel Manager", "Front Desk Manager", "Hotel Receptionist", "Front Desk"},
    "Housekeeping": {"System Manager", "Hotel Manager", "Hotel Housekeeping", "Housekeeping Manager"},
    "Laundry": {"System Manager", "Hotel Manager", "Front Desk Manager", "Hotel Housekeeping", "Housekeeping Manager"},
    "GM Office": {"System Manager", "Hotel Manager"},
    "Operations": {"System Manager", "Hotel Manager", "Front Desk Manager"},
}
ALLOWED_FIELDS = {
    "guest", "room", "reservation", "check_in", "complimentary_type", "department",
    "value", "quantity", "issue_date", "expiry_date", "reason", "redemption_rule",
    "note", "approval_level", "source_category", "upgrade_room", "late_checkout_time",
}


def _payload(value):
    if isinstance(value, str):
        return json.loads(value or "{}")
    return value or {}


def _roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def _has_any(required_roles):
    return bool(_roles() & set(required_roles))


def _is_manager():
    return _has_any(MANAGER_ROLES)


def _is_owner(doc):
    return doc.owner == frappe.session.user or doc.issued_by == frappe.session.user


def _require_read(doc):
    if not frappe.has_permission(DOCTYPE, "read", doc=doc):
        frappe.throw(_("Not permitted to read this complimentary record."), frappe.PermissionError)


def _require_write(doc):
    if not frappe.has_permission(DOCTYPE, "write", doc=doc):
        frappe.throw(_("Not permitted to update this complimentary record."), frappe.PermissionError)


def _can_approve(doc):
    return _is_manager() or _has_any(APPROVAL_ROLES.get(doc.approval_level, set()))


def _can_consume(doc):
    return _is_manager() or _has_any(CONSUMPTION_ROLES.get(doc.department, set()))


def _normalize_status(value):
    value = (value or "").strip()
    return value if value in {"Draft", "Pending", "Approved", "In Progress", "Consumed", "Expired", "Cancelled"} else "Draft"


def _is_expired(doc):
    return bool(doc.expiry_date and getdate(doc.expiry_date) < getdate(nowdate()))


def _remaining_value(doc):
    value = flt(getattr(doc, "value", 0))
    remaining = getattr(doc, "remaining_value", None)
    if remaining is not None:
        return max(0, flt(remaining))
    return max(0, value - flt(getattr(doc, "redeemed_amount", 0)))


def _redemption_reference(transaction_reference, default_label=None):
    reference = cstr(transaction_reference).strip()
    if reference and " " not in reference:
        reference = _("POS Invoice {0}").format(reference)
    return reference or default_label or _("Voucher Redemption")


def redeem_complimentary_value(complimentary_name, applied_amount, transaction_reference, department=None):
    """Apply a fixed amount against a complimentary and keep any balance open."""
    if not complimentary_name:
        return {"applied_amount": 0, "remaining_value": 0}

    if not frappe.db.exists(DOCTYPE, complimentary_name):
        frappe.throw(_("Complimentary record {0} not found.").format(complimentary_name))

    doc = frappe.get_doc(DOCTYPE, complimentary_name)
    _validate_redeemable(doc, department=department or doc.department)

    applied_amount = flt(applied_amount)
    remaining_before = _remaining_value(doc)
    if applied_amount <= 0 or remaining_before <= 0:
        frappe.throw(_("Complimentary {0} cannot be applied.").format(doc.name))
    if applied_amount > remaining_before:
        applied_amount = remaining_before

    doc.redeemed_amount = min(flt(doc.value), flt(getattr(doc, "redeemed_amount", 0)) + applied_amount)
    doc.remaining_value = max(0, flt(doc.value) - flt(doc.redeemed_amount))
    doc.consumption_reference = _redemption_reference(transaction_reference)
    if doc.remaining_value <= 0:
        doc.status = "Consumed"
        doc.consumed_on = now_datetime()
    else:
        doc.status = "In Progress"
        doc.consumed_on = None
    doc.flags.ignore_permissions = True
    doc.save()

    return {
        "complimentary_name": doc.name,
        "applied_amount": applied_amount,
        "remaining_value": doc.remaining_value,
        "redeemed_amount": doc.redeemed_amount,
        "status": doc.status,
        "consumption_reference": doc.consumption_reference,
    }


def _validate_redeemable(doc, department=None):
    if doc.status not in {"Approved", "In Progress"}:
        frappe.throw(_("Complimentary {0} is not approved for redemption.").format(doc.name))
    if department and doc.department != department:
        frappe.throw(_("Complimentary {0} is for {1}, not {2}.").format(doc.name, doc.department, department))
    if _is_expired(doc):
        frappe.throw(_("Complimentary {0} has expired.").format(doc.name))
    if _remaining_value(doc) <= 0:
        frappe.throw(_("Complimentary {0} has no redeemable value.").format(doc.name))
    if not _can_consume(doc):
        frappe.throw(_("You do not have the role required to redeem this complimentary."), frappe.PermissionError)


def _check_in_reservation_fields():
    fields = ["guest", "room_number"]
    if frappe.db.has_column("Hotel Room Check In", "canonical_reservation"):
        fields.append("canonical_reservation")
    if frappe.db.has_column("Hotel Room Check In", "reservation"):
        fields.append("reservation")
    return fields


def _check_in_reservation_select():
    canonical = (
        "ci.canonical_reservation"
        if frappe.db.has_column("Hotel Room Check In", "canonical_reservation")
        else "NULL"
    )
    reservation = (
        "ci.reservation"
        if frappe.db.has_column("Hotel Room Check In", "reservation")
        else "NULL"
    )
    return canonical, reservation


def _set_doc_fields(doc, data):
    for field in ALLOWED_FIELDS:
        if field not in data:
            continue
        value = data.get(field)
        if field == "value":
            value = flt(value or 0)
        if field == "quantity":
            value = value or "1"
        if field in {"reservation", "check_in", "expiry_date", "upgrade_room", "late_checkout_time"}:
            value = value or None
        setattr(doc, field, value)

    if doc.check_in and frappe.db.exists("Hotel Room Check In", doc.check_in):
        check_in = frappe.db.get_value(
            "Hotel Room Check In",
            doc.check_in,
            _check_in_reservation_fields(),
            as_dict=True,
        )
        if check_in:
            if check_in.guest:
                doc.guest = frappe.db.get_value("Hotel Guest", check_in.guest, "hotel_guest_name") or check_in.guest
            if check_in.room_number:
                doc.room = check_in.room_number
            if not doc.reservation:
                doc.reservation = check_in.get("canonical_reservation") or check_in.get("reservation") or None


def _record_response(doc, audit_trail=None):
    return {
        "name": doc.name,
        "guest": doc.guest,
        "room": doc.room,
        "reservation": doc.reservation,
        "check_in": getattr(doc, "check_in", None),
        "complimentary_type": doc.complimentary_type,
        "department": doc.department,
        "value": doc.value,
        "redeemed_amount": flt(getattr(doc, "redeemed_amount", 0)),
        "remaining_value": _remaining_value(doc),
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
        "upgrade_room": getattr(doc, "upgrade_room", None),
        "late_checkout_time": str(getattr(doc, "late_checkout_time", None) or "") or None,
        "audit_trail": audit_trail or [],
    }


def _identity_conditions(check_in=None, room=None, guest=None):
    conditions = []
    params = {}
    if check_in:
        conditions.append("check_in = %(check_in)s")
        params["check_in"] = check_in
    if room:
        conditions.append("room = %(room)s")
        params["room"] = room
    if guest:
        conditions.append("guest LIKE %(guest)s")
        params["guest"] = f"%{guest}%"
    return conditions, params


def _unused_complimentary_rows(check_in=None, room=None, guest=None, department=None, complimentary_type=None, limit=20):
    expire_unused_complimentaries(commit=True)

    conditions = ["status IN ('Approved', 'In Progress')"]
    params = {}
    redeemed_expr = "COALESCE(redeemed_amount, 0)" if frappe.db.has_column(DOCTYPE, "redeemed_amount") else "0"
    remaining_expr = "COALESCE(remaining_value, value, 0)" if frappe.db.has_column(DOCTYPE, "remaining_value") else "COALESCE(value, 0)"

    identity_conditions, identity_params = _identity_conditions(check_in=check_in, room=room, guest=guest)
    params.update(identity_params)
    if identity_conditions:
        conditions.append("(" + " OR ".join(identity_conditions) + ")")

    if department:
        conditions.append("department = %(department)s")
        params["department"] = department
    if complimentary_type:
        conditions.append("complimentary_type = %(complimentary_type)s")
        params["complimentary_type"] = complimentary_type

    rows = frappe.db.sql(
        f"""
        SELECT
            name, guest, room, check_in, complimentary_type, department,
            value, {redeemed_expr} as redeemed_amount, {remaining_expr} as remaining_value,
            quantity, issue_date, expiry_date, reason, redemption_rule, status
        FROM `tabHotel Complimentary`
        WHERE {" AND ".join(conditions)}
        ORDER BY expiry_date IS NULL ASC, expiry_date ASC, modified DESC
        LIMIT %(limit)s
        """,
        {**params, "limit": int(limit or 20)},
        as_dict=True,
    )

    today = getdate(nowdate())
    return [
        r for r in rows
        if (not r.expiry_date or getdate(r.expiry_date) >= today) and flt(r.remaining_value) > 0
    ]


def _complimentary_summary(rows):
    items = []
    total_value = 0
    by_type = {}
    for r in rows:
        value = flt(r.value)
        remaining_value = flt(getattr(r, "remaining_value", value))
        redeemed_amount = flt(getattr(r, "redeemed_amount", 0))
        total_value += remaining_value
        by_type[r.complimentary_type] = by_type.get(r.complimentary_type, 0) + 1
        items.append({
            "name": r.name,
            "guest": r.guest,
            "room": r.room,
            "check_in": r.check_in,
            "complimentary_type": r.complimentary_type,
            "department": r.department,
            "value": value,
            "redeemed_amount": redeemed_amount,
            "remaining_value": remaining_value,
            "quantity": r.quantity,
            "issue_date": str(r.issue_date) if r.issue_date else None,
            "expiry_date": str(r.expiry_date) if r.expiry_date else None,
            "reason": r.reason,
            "redemption_rule": r.redemption_rule,
            "status": r.status,
        })
    return {
        "count": len(items),
        "total_value": total_value,
        "by_type": by_type,
        "items": items,
    }


@frappe.whitelist()
def get_complimentary_dashboard():
    """Stats for the complimentary dashboard page."""
    frappe.has_permission(DOCTYPE, "read", throw=True)
    today = nowdate()
    expire_unused_complimentaries(commit=True)

    issued_today = frappe.db.count(DOCTYPE, {"issue_date": today})
    draft_count = frappe.db.count(DOCTYPE, {"status": "Draft"})
    pending_approval = frappe.db.count(DOCTYPE, {"status": "Pending"})
    consumed_today = frappe.db.count(DOCTYPE, {"status": "Consumed", "issue_date": today})
    active_count = frappe.db.count(DOCTYPE, {"status": ["in", ["Approved", "In Progress"]]})
    expired_unused = frappe.db.count(DOCTYPE, {"status": "Expired"})

    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(value), 0) as total
        FROM `tabHotel Complimentary`
        WHERE issue_date = %s AND status != 'Cancelled'
        """,
        (today,),
        as_dict=1,
    )
    budget_impact_today = flt(result[0].total) if result else 0.0

    return {
        "issued_today": issued_today,
        "draft_count": draft_count,
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
    filter_department=None,
    page=1,
    page_size=25,
):
    """Paginated complimentary list with optional filters."""
    frappe.has_permission(DOCTYPE, "read", throw=True)
    try:
        page = max(1, int(page))
        page_size = min(100, max(1, int(page_size)))
    except (TypeError, ValueError):
        page, page_size = 1, 25

    conditions = ["1 = 1"]
    params = {"limit": page_size, "offset": (page - 1) * page_size}

    if filter_type:
        conditions.append("complimentary_type = %(filter_type)s")
        params["filter_type"] = filter_type
    if filter_status:
        conditions.append("status = %(filter_status)s")
        params["filter_status"] = filter_status
    if filter_approver:
        conditions.append("approval_level = %(filter_approver)s")
        params["filter_approver"] = filter_approver
    if filter_department:
        conditions.append("department = %(filter_department)s")
        params["filter_department"] = filter_department
    if search:
        params["q"] = f"%{search}%"
        conditions.append(
            """(name LIKE %(q)s OR guest LIKE %(q)s OR room LIKE %(q)s
                OR complimentary_type LIKE %(q)s OR approval_level LIKE %(q)s
                OR department LIKE %(q)s OR source_category LIKE %(q)s)"""
        )

    where_clause = " AND ".join(conditions)
    redeemed_expr = "COALESCE(redeemed_amount, 0) as redeemed_amount" if frappe.db.has_column(DOCTYPE, "redeemed_amount") else "0 as redeemed_amount"
    remaining_expr = "COALESCE(remaining_value, value, 0) as remaining_value" if frappe.db.has_column(DOCTYPE, "remaining_value") else "COALESCE(value, 0) as remaining_value"
    fields = """
        name, guest, room, check_in, complimentary_type, department,
        value, {redeemed_expr}, {remaining_expr}, status, approval_level, issue_date, expiry_date,
        source_category, note, reason
    """.format(redeemed_expr=redeemed_expr, remaining_expr=remaining_expr)

    records = frappe.db.sql(
        f"""
        SELECT {fields}
        FROM `tabHotel Complimentary`
        WHERE {where_clause}
        ORDER BY issue_date DESC, modified DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
        as_dict=1,
    )

    count_result = frappe.db.sql(
        f"""
        SELECT COUNT(name) as cnt
        FROM `tabHotel Complimentary`
        WHERE {where_clause}
        """,
        params,
        as_dict=1,
    )
    total = count_result[0].cnt if count_result else 0

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
    if not frappe.db.exists(DOCTYPE, complimentary_name):
        frappe.throw(f"Complimentary record '{complimentary_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc(DOCTYPE, complimentary_name)
    _require_read(doc)

    audit_trail = []
    try:
        logs = frappe.get_all(
            "Version",
            filters={"ref_doctype": DOCTYPE, "docname": complimentary_name},
            fields=["creation", "owner", "data"],
            order_by="creation asc",
            limit_page_length=30,
        )
        for log in logs:
            try:
                data = json.loads(log.data) if isinstance(log.data, str) else log.data
                changed = data.get("changed", [])
                if changed:
                    changes = "; ".join(
                        f"{c[0]}: {c[1]} -> {c[2]}" for c in changed if len(c) >= 3
                    )
                    audit_trail.append({"time": str(log.creation), "action": f"Changed by {log.owner}: {changes}"})
            except Exception:
                audit_trail.append({"time": str(log.creation), "action": f"Updated by {log.owner}"})
    except Exception:
        pass

    audit_trail.insert(0, {"time": str(doc.creation), "action": f"Created by {doc.owner}"})
    if doc.approved_on:
        audit_trail.append({"time": str(doc.approved_on), "action": f"Approved by {doc.approved_by or 'Manager'}"})
    if doc.consumed_on:
        audit_trail.append({"time": str(doc.consumed_on), "action": f"Marked as consumed: {doc.consumption_reference or 'No reference'}"})

    return _record_response(doc, audit_trail)


@frappe.whitelist()
def create_complimentary(complimentary_data, submit_for_approval=1):
    """Create a new Hotel Complimentary record as Draft or Pending."""
    data = _payload(complimentary_data)
    submit_for_approval = str(submit_for_approval) not in {"0", "false", "False", ""}

    try:
        frappe.has_permission(DOCTYPE, "create", throw=True)
        doc = frappe.new_doc(DOCTYPE)
        _set_doc_fields(doc, data)
        doc.status = "Pending" if submit_for_approval else "Draft"
        doc.issued_by = frappe.session.user
        doc.insert()
        frappe.db.commit()
        return {"success": True, "complimentary_name": doc.name, "status": doc.status}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_complimentary(complimentary_name, complimentary_data, submit_for_approval=0):
    """Update a Draft/Pending complimentary record and optionally submit it."""
    data = _payload(complimentary_data)
    submit_for_approval = str(submit_for_approval) not in {"0", "false", "False", ""}

    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status not in {"Draft", "Pending"}:
            return {"success": False, "error": f"Cannot edit a record with status '{doc.status}'."}
        if not (_is_owner(doc) or _is_manager()):
            frappe.throw(_("Only the issuer or a manager can update this record."), frappe.PermissionError)

        _set_doc_fields(doc, data)
        if submit_for_approval:
            doc.status = "Pending"
        doc.save()
        frappe.db.commit()
        return {"success": True, "status": doc.status}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_complimentary(complimentary_name):
    """Move a draft record into the approval queue."""
    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status != "Draft":
            return {"success": False, "error": f"Only Draft records can be submitted. Current status: {doc.status}"}
        if not (_is_owner(doc) or _is_manager()):
            frappe.throw(_("Only the issuer or a manager can submit this record."), frappe.PermissionError)
        doc.status = "Pending"
        doc.save()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def approve_complimentary(complimentary_name):
    """Approve a pending complimentary record.

    For Room Upgrade type: if upgrade_room and check_in are set, automatically
    transfers the guest to the new room, calculates the rate difference, creates
    a credit note to waive it, and marks the complimentary as Consumed.
    """
    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status != "Pending":
            return {"success": False, "error": f"Cannot approve a record with status '{doc.status}'."}
        if not _can_approve(doc):
            frappe.throw(_("You do not have the role required for this approval level."), frappe.PermissionError)

        doc.status = "Approved"
        doc.approved_by = frappe.session.user
        doc.approved_on = now_datetime()

        # ── Room Upgrade auto-execution ──────────────────────────────────────
        upgrade_room = getattr(doc, "upgrade_room", None)
        if doc.complimentary_type == "Room Upgrade" and upgrade_room and doc.check_in:
            return _execute_room_upgrade(doc)

        # ── Late Checkout auto-execution ──────────────────────────────────
        if doc.complimentary_type == "Late Checkout" and doc.check_in:
            if not getattr(doc, "late_checkout_time", None):
                return {"success": False, "error": _("Approved Checkout Time is required for Late Checkout vouchers.")}
            return _execute_late_checkout(doc)

        doc.save()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "approve_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


def _execute_room_upgrade(doc):
    """Transfer the guest to the upgrade room and waive the rate difference."""
    from rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in import (
        transfer_room,
        apply_discount,
    )

    check_in_name = doc.check_in
    upgrade_room = doc.upgrade_room

    # Capture old room BEFORE transfer
    old_room = frappe.db.get_value("Hotel Room Check In", check_in_name, "room_number") or ""

    # Step 1: transfer the guest — this creates a rate_invoice for the difference
    try:
        result = transfer_room(check_in_name, upgrade_room, note=f"Room Upgrade — {doc.name}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Room Upgrade transfer failed")
        frappe.db.rollback()
        return {
            "success": False,
            "error": _("Room transfer failed: {0}").format(str(e)),
        }

    rate_invoice = result.get("rate_invoice")

    # Step 2: waive the rate difference via a credit note (if an invoice was created)
    credit_note = None
    if rate_invoice:
        # Get the invoice total to waive
        invoice_total = flt(
            frappe.db.get_value("Sales Invoice", rate_invoice, "grand_total")
        )
        if invoice_total > 0:
            try:
                discount_result = apply_discount(
                    check_in_name,
                    invoice_total,
                    reason=_("Room Upgrade Waiver — Complimentary {0}").format(doc.name),
                    source_invoice=rate_invoice,
                )
                credit_note = discount_result.get("credit_note")
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Room Upgrade discount failed")
                # Transfer succeeded; note the failure but don't roll back
                frappe.log_error(
                    _("Rate invoice {0} was created but the waiver credit note failed: {1}").format(
                        rate_invoice, str(e)
                    ),
                    "Room Upgrade waiver incomplete",
                )

    # Step 3: mark the complimentary as Consumed
    rate_diff = flt(frappe.db.get_value("Sales Invoice", rate_invoice, "grand_total")) if rate_invoice else 0
    doc.value = rate_diff
    doc.redeemed_amount = rate_diff
    doc.remaining_value = 0
    doc.status = "Consumed"
    doc.consumed_on = now_datetime()
    doc.consumption_reference = credit_note or rate_invoice or _("Room transfer — no rate difference")
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    # Step 4: notify front desk in real-time
    try:
        frappe.publish_realtime(
            "rhohotel_room_upgrade",
            {
                "guest": doc.guest,
                "old_room": old_room,
                "new_room": upgrade_room,
                "complimentary": doc.name,
                "waiver": rate_diff,
            },
        )
    except Exception:
        pass  # non-critical: task queue will still surface this move

    return {
        "success": True,
        "room_upgraded": True,
        "new_room": upgrade_room,
        "rate_invoice": rate_invoice,
        "credit_note": credit_note,
        "value": rate_diff,
    }


def _execute_late_checkout(doc):
    """Set late_checkout=1 on the check-in and extend checkout time to the approved time."""
    from frappe.utils import get_datetime

    check_in_name = doc.check_in
    late_time = getattr(doc, "late_checkout_time", None)

    ci = frappe.get_doc("Hotel Room Check In", check_in_name)
    if ci.status != "Checked In":
        return {"success": False, "error": _("Guest is not currently checked in.")}

    current_checkout_dt = get_datetime(ci.expected_check_out_datetime)
    checkout_date = current_checkout_dt.date()

    if not late_time:
        return {"success": False, "error": _("Select an approved late checkout time.")}

    # late_checkout_time is stored as "HH:MM:SS" by Frappe
    time_str = str(late_time)[:5]  # "HH:MM"
    from datetime import datetime
    new_checkout_dt = datetime.strptime(f"{checkout_date} {time_str}", "%Y-%m-%d %H:%M")
    if new_checkout_dt <= current_checkout_dt:
        return {
            "success": False,
            "error": _("Late checkout time must be later than the current checkout time ({0}).").format(
                current_checkout_dt.strftime("%H:%M")
            ),
        }

    # Update the check-in with db_set to bypass submit restrictions
    frappe.db.set_value(
        "Hotel Room Check In",
        check_in_name,
        {
            "late_checkout": 1,
            "expected_check_out_datetime": new_checkout_dt,
        },
        update_modified=True,
    )

    # Mark complimentary as Consumed
    doc.status = "Consumed"
    doc.consumed_on = now_datetime()
    doc.consumption_reference = _("Late Checkout approved — checkout extended to {0}").format(
        new_checkout_dt.strftime("%H:%M")
    )
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    try:
        frappe.publish_realtime("rhohotel_front_desk_update")
    except Exception:
        pass

    return {
        "success": True,
        "late_checkout_applied": True,
        "new_checkout_time": new_checkout_dt.strftime("%H:%M"),
        "checkout_date": str(checkout_date),
        "guest": doc.guest,
    }


@frappe.whitelist()
def get_late_checkout_preview(check_in, late_checkout_time=None):
    """Return current checkout time and the new time if the voucher is approved."""
    try:
        from frappe.utils import get_datetime

        if not frappe.db.exists("Hotel Room Check In", check_in):
            return {"error": "Check-in not found"}

        ci = frappe.db.get_value(
            "Hotel Room Check In",
            check_in,
            ["expected_check_out_datetime", "status", "late_checkout"],
            as_dict=True,
        )
        if not ci or ci.status != "Checked In":
            return {"error": "Guest is not currently checked in"}
        if ci.late_checkout:
            return {"error": "Guest already has late checkout approved"}

        current_dt = get_datetime(ci.expected_check_out_datetime)
        result = {
            "current_checkout": ci.expected_check_out_datetime,
            "current_time": current_dt.strftime("%H:%M"),
            "checkout_date": str(current_dt.date()),
        }

        if late_checkout_time:
            from datetime import datetime
            time_str = str(late_checkout_time)[:5]
            new_dt = datetime.strptime(f"{current_dt.date()} {time_str}", "%Y-%m-%d %H:%M")
            result["new_checkout"] = str(new_dt)
            result["new_time"] = new_dt.strftime("%H:%M")
            result["is_extension"] = new_dt > current_dt

        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_late_checkout_preview error")
        return {"error": str(e)}


@frappe.whitelist()
def get_pending_room_moves():
    """Return today's Room Upgrade complimentaries not yet acknowledged by front desk."""
    frappe.has_permission(DOCTYPE, "read", throw=True)
    today = nowdate()
    records = frappe.get_all(
        DOCTYPE,
        filters={
            "complimentary_type": "Room Upgrade",
            "status": "Consumed",
            "consumed_on": [">=", today + " 00:00:00"],
        },
        fields=["name", "guest", "room", "upgrade_room", "consumed_on", "consumption_reference"],
        order_by="consumed_on desc",
        limit=20,
    )
    pending = [
        r for r in records
        if not frappe.cache().get_value(f"rhohotel:room_move_ack:{r.name}")
    ]
    return pending


@frappe.whitelist()
def acknowledge_room_move(complimentary_name):
    """Mark a room move task as seen/acknowledged by front desk (cached 24 h)."""
    if not frappe.db.exists(DOCTYPE, complimentary_name):
        frappe.throw(_("Complimentary {0} not found").format(complimentary_name))
    frappe.cache().set_value(
        f"rhohotel:room_move_ack:{complimentary_name}", 1, expires_in_sec=86400
    )
    return {"success": True}


@frappe.whitelist()
def mark_in_progress(complimentary_name):
    """Mark an approved complimentary as being prepared/served by the outlet."""
    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status != "Approved":
            return {"success": False, "error": f"Only Approved records can move in progress. Current status: {doc.status}"}
        if not _can_consume(doc):
            frappe.throw(_("You do not have the role required for this department."), frappe.PermissionError)
        doc.status = "In Progress"
        doc.save()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "mark_in_progress error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def mark_consumed(complimentary_name, consumption_reference=None):
    """Mark a complimentary record as consumed."""
    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status == "Consumed":
            return {"success": False, "error": "Record is already consumed"}
        if doc.status not in {"Approved", "In Progress"}:
            return {"success": False, "error": f"Cannot consume a record with status '{doc.status}'."}
        if not _can_consume(doc):
            frappe.throw(_("You do not have the role required to confirm consumption for this department."), frappe.PermissionError)
        if not (consumption_reference or "").strip():
            return {"success": False, "error": "Consumption reference is required."}

        doc.redeemed_amount = flt(doc.value)
        doc.remaining_value = 0
        doc.status = "Consumed"
        doc.consumed_on = now_datetime()
        doc.consumption_reference = consumption_reference.strip()
        doc.save()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "mark_consumed error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


def redeem_complimentary_for_pos(complimentary_name, transaction_reference, bill_total, manual_discount=0, department="Restaurant"):
    """Validate and redeem a complimentary voucher against a submitted POS transaction."""
    if not complimentary_name:
        return {"applied_amount": 0}

    if not frappe.db.exists(DOCTYPE, complimentary_name):
        frappe.throw(_("Complimentary record {0} not found.").format(complimentary_name))

    doc = frappe.get_doc(DOCTYPE, complimentary_name)
    _validate_redeemable(doc, department=department)

    remaining_total = max(0, flt(bill_total) - flt(manual_discount))
    applied_amount = min(_remaining_value(doc), remaining_total)
    if applied_amount <= 0:
        frappe.throw(_("Complimentary {0} cannot be applied to this bill.").format(doc.name))

    return redeem_complimentary_value(
        complimentary_name=doc.name,
        applied_amount=applied_amount,
        transaction_reference=_redemption_reference(transaction_reference, _("POS Invoice")),
        department=department,
    )


def get_complimentary_pos_discount(complimentary_name, bill_total, manual_discount=0, department="Restaurant"):
    """Return the amount a POS bill may discount for a complimentary voucher."""
    if not complimentary_name:
        return 0
    if not frappe.db.exists(DOCTYPE, complimentary_name):
        frappe.throw(_("Complimentary record {0} not found.").format(complimentary_name))
    doc = frappe.get_doc(DOCTYPE, complimentary_name)
    _validate_redeemable(doc, department=department)
    return min(_remaining_value(doc), max(0, flt(bill_total) - flt(manual_discount)))


@frappe.whitelist()
def get_redeemable_complimentaries(check_in=None, room=None, guest=None, department=None, complimentary_type=None):
    """Approved complimentary records that can be applied from POS or any department."""
    if department:
        if not _is_manager() and not _has_any(CONSUMPTION_ROLES.get(department, set())):
            frappe.throw(_("You do not have the role required to redeem complimentaries."), frappe.PermissionError)
    else:
        # When no department specified, check if user can consume in any department
        consumer_roles = set().union(*CONSUMPTION_ROLES.values())
        if not _is_manager() and not _has_any(consumer_roles):
            frappe.throw(_("You do not have the role required to redeem complimentaries."), frappe.PermissionError)

    rows = _unused_complimentary_rows(
        check_in=check_in,
        room=room,
        guest=guest,
        department=department,
        complimentary_type=complimentary_type,
        limit=20,
    )
    return _complimentary_summary(rows)["items"]


@frappe.whitelist()
def get_unused_complimentary_indicator(check_in=None, room=None, guest=None):
    """Small unread/unused complimentary summary for POS and front-desk cues."""
    can_read = frappe.has_permission(DOCTYPE, "read")
    consumer_roles = set().union(*CONSUMPTION_ROLES.values())
    if not (can_read or _is_manager() or _has_any(consumer_roles)):
        frappe.throw(_("Not permitted to view complimentary indicators."), frappe.PermissionError)
    rows = _unused_complimentary_rows(check_in=check_in, room=room, guest=guest, limit=10)
    return _complimentary_summary(rows)


@frappe.whitelist()
def cancel_complimentary(complimentary_name):
    """Cancel a complimentary record."""
    try:
        doc = frappe.get_doc(DOCTYPE, complimentary_name)
        _require_write(doc)
        if doc.status == "Consumed":
            return {"success": False, "error": "Cannot cancel a consumed record"}
        if doc.status == "Cancelled":
            return {"success": False, "error": "Record is already cancelled"}
        if not (_is_owner(doc) or _is_manager() or _can_approve(doc)):
            frappe.throw(_("Only the issuer, approver, or manager can cancel this record."), frappe.PermissionError)

        doc.status = "Cancelled"
        doc.save()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_complimentary error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_active_checkins():
    """Return currently checked-in guests and their rooms for the complimentary form."""
    try:
        frappe.has_permission(DOCTYPE, "create", throw=True)
        canonical_expr, reservation_expr = _check_in_reservation_select()
        rows = frappe.db.sql(
            f"""
            SELECT
                ci.name as check_in,
                ci.guest,
                ci.room_number,
                {canonical_expr} as canonical_reservation,
                {reservation_expr} as reservation
            FROM `tabHotel Room Check In` ci
            WHERE ci.status = 'Checked In'
              AND ci.docstatus = 1
            ORDER BY ci.room_number ASC
            """,
            as_dict=True,
        )

        checkins = []
        for r in rows:
            guest_display = r.guest or ""
            if guest_display:
                guest_display = frappe.db.get_value("Hotel Guest", r.guest, "hotel_guest_name") or r.guest
            checkins.append({
                "check_in": r.check_in,
                "guest": guest_display,
                "guest_id": r.guest,
                "room_number": r.room_number or "",
                "reservation": r.canonical_reservation or r.reservation or "",
            })

        return {"checkins": checkins}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_active_checkins error")
        return {"checkins": []}


@frappe.whitelist()
def get_room_upgrade_preview(check_in, upgrade_room):
    """Return the estimated rate difference and remaining nights for a Room Upgrade preview."""
    try:
        from frappe.utils.data import date_diff
        from rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in import get_room_rate

        if not frappe.db.exists("Hotel Room Check In", check_in):
            return {"error": "Check-in not found"}
        if not frappe.db.exists("Hotel Room", upgrade_room):
            return {"error": "Room not found"}

        ci = frappe.db.get_value(
            "Hotel Room Check In",
            check_in,
            ["room_number", "rate_amount", "check_in_datetime", "expected_check_out_datetime", "status"],
            as_dict=True,
        )
        if not ci or ci.status != "Checked In":
            return {"error": "Guest is not currently checked in"}
        if ci.room_number == upgrade_room:
            return {"error": "Guest is already in this room"}

        new_room = frappe.get_doc("Hotel Room", upgrade_room)
        if new_room.status != "Vacant":
            return {"error": f"Room {upgrade_room} is not vacant"}

        today = getdate(nowdate())
        expected_checkout = getdate(ci.expected_check_out_datetime)
        remaining_nights = max(date_diff(expected_checkout, today), 1)

        new_rate_data = get_room_rate(new_room.room_type, "", str(today))
        new_rate = flt(new_rate_data)
        old_rate = flt(ci.rate_amount)
        rate_diff_per_night = new_rate - old_rate
        total_waiver = rate_diff_per_night * remaining_nights

        return {
            "current_room": ci.room_number,
            "upgrade_room": upgrade_room,
            "upgrade_room_type": new_room.room_type,
            "old_rate": old_rate,
            "new_rate": new_rate,
            "rate_diff_per_night": rate_diff_per_night,
            "remaining_nights": remaining_nights,
            "total_waiver": total_waiver,
            "is_upgrade": rate_diff_per_night > 0,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_room_upgrade_preview error")
        return {"error": str(e)}


@frappe.whitelist()
def expire_unused_complimentaries(commit=True):
    """Expire approved/pending unused complimentary records past expiry_date."""
    today = getdate(nowdate())
    rows = frappe.get_all(
        DOCTYPE,
        filters={"status": ["in", ["Draft", "Pending", "Approved", "In Progress"]], "expiry_date": ["<", today]},
        fields=["name", "status"],
    )
    expired = []
    for row in rows:
        try:
            frappe.db.set_value(DOCTYPE, row.name, "status", "Expired", update_modified=True)
            expired.append(row.name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to expire complimentary {row.name}")
    if commit:
        frappe.db.commit()
    return {"expired": expired, "count": len(expired)}
