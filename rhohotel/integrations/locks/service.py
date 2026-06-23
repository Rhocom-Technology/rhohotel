# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
Lock service — orchestration layer.

This is the only module called from DocType hooks, API endpoints, and PMS
workflow integration points.  Callers must never call providers directly.

Design principles:
- PMS is always the source of truth.  Provider failures are logged and surfaced
  to staff but never roll back a successful PMS operation (checkout, stay
  adjustment, room transfer).
- Every provider call is wrapped in a Lock Operation Log entry that records
  the outcome, duration, and redacted payloads.
- Hotel Room Check In is the active stay anchor.  Reservation context is
  resolved through canonical_reservation when present.
- Credentials are never passed to or stored in this module.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime

from rhohotel.integrations.locks.base import (
    KeyContext,
    LockProviderError,
    LockProviderMappingError,
)
from rhohotel.integrations.locks.registry import get_provider_for_room


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_lock_enabled() -> bool:
    return bool(frappe.db.get_single_value("Hotel Settings", "enable_lock_integration"))


def _require_lock_enabled():
    if not _is_lock_enabled():
        frappe.throw(
            _("Smart Lock Integration is not enabled. Enable it in Hotel Settings → Smart Lock Integration.")
        )


def _get_setting(field: str, default=None):
    return frappe.db.get_single_value("Hotel Settings", field) or default


def _assert_roles():
    """Raise PermissionError if the current user has no lock operation role."""
    allowed = {
        "System Manager",
        "Hotel Manager",
        "Front Desk Manager",
        "Hotel Receptionist",
    }
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not (allowed & user_roles):
        frappe.throw(
            _("You do not have permission to perform lock operations."),
            frappe.PermissionError,
        )


def _build_key_context(check_in_doc, room_mapping: dict) -> KeyContext:
    """Build a KeyContext from a Hotel Room Check In document."""
    buffer_mins = int(_get_setting("lock_key_validity_buffer_minutes", 0) or 0)
    valid_until_dt = get_datetime(check_in_doc.expected_check_out_datetime)
    if buffer_mins > 0:
        from frappe.utils import add_to_date
        valid_until_dt = add_to_date(valid_until_dt, minutes=buffer_mins)

    guest_name = (
        frappe.db.get_value("Hotel Guest", check_in_doc.guest, "hotel_guest_name")
        or str(check_in_doc.guest or "")
    )

    return KeyContext(
        check_in_name=check_in_doc.name,
        room_number=check_in_doc.room_number,
        external_lock_id=room_mapping["external_lock_id"],
        guest_name=guest_name,
        valid_from=str(check_in_doc.check_in_datetime),
        valid_until=str(valid_until_dt),
        canonical_reservation=getattr(check_in_doc, "canonical_reservation", None),
    )


def _create_log(
    operation_type: str,
    provider_code: str,
    room: str,
    check_in: Optional[str] = None,
    reservation: Optional[str] = None,
    guest_key: Optional[str] = None,
    requested_by: Optional[str] = None,
) -> str:
    """Insert a Lock Operation Log in Pending state and return its name."""
    log = frappe.get_doc(
        {
            "doctype": "Lock Operation Log",
            "operation_type": operation_type,
            "status": "Pending",
            "provider": provider_code,
            "room": room,
            "check_in": check_in,
            "reservation": reservation,
            "guest_key": guest_key,
            "requested_by": requested_by or frappe.session.user,
            "request_datetime": now_datetime(),
            "duration_ms": 0,
            "retry_count": 0,
        }
    )
    log.insert(ignore_permissions=True)
    frappe.db.commit()
    return log.name


def _update_log(
    log_name: str,
    status: str,
    duration_ms: int = 0,
    provider_request_id: Optional[str] = None,
    request_payload: Optional[dict] = None,
    response_payload: Optional[dict] = None,
    error_message: Optional[str] = None,
    guest_key: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Update an existing Lock Operation Log with the operation result."""
    updates = {
        "status": status,
        "duration_ms": duration_ms,
    }
    if provider_request_id is not None:
        updates["provider_request_id"] = provider_request_id
    if request_payload is not None:
        updates["request_payload"] = json.dumps(request_payload, default=str)
    if response_payload is not None:
        updates["response_payload"] = json.dumps(response_payload, default=str)
    if error_message is not None:
        updates["error_message"] = str(error_message)[:2000]
    if guest_key is not None:
        updates["guest_key"] = guest_key
    if notes is not None:
        updates["notes"] = notes

    frappe.db.set_value("Lock Operation Log", log_name, updates, update_modified=False)
    frappe.db.commit()


def _upsert_guest_key(
    check_in_doc,
    provider_code: str,
    external_key_id: str,
    valid_from: str,
    valid_until: str,
    status: str = "Active",
    card_uid: Optional[str] = None,
    provider_payload: Optional[dict] = None,
    existing_key_name: Optional[str] = None,
) -> str:
    """Create or update a Guest Key record and return its name."""
    now = str(now_datetime())

    if existing_key_name and frappe.db.exists("Guest Key", existing_key_name):
        frappe.db.set_value(
            "Guest Key",
            existing_key_name,
            {
                "external_key_id": external_key_id,
                "status": status,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "last_updated_at": now,
                "last_provider_status": status,
                "provider_payload": json.dumps(provider_payload or {}, default=str),
            },
            update_modified=True,
        )
        frappe.db.commit()
        return existing_key_name

    gk = frappe.get_doc(
        {
            "doctype": "Guest Key",
            "check_in": check_in_doc.name,
            "canonical_reservation": getattr(check_in_doc, "canonical_reservation", None),
            "guest": check_in_doc.guest,
            "room": check_in_doc.room_number,
            "provider": provider_code,
            "external_key_id": external_key_id,
            "card_uid": card_uid,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "status": status,
            "issued_by": frappe.session.user,
            "issued_at": now,
            "last_updated_at": now,
            "last_provider_status": status,
            "provider_payload": json.dumps(provider_payload or {}, default=str),
        }
    )
    gk.insert(ignore_permissions=True)
    frappe.db.commit()
    return gk.name


def _get_active_key_for_check_in(check_in_name: str) -> Optional[dict]:
    """Return the most recent Active Guest Key for a check-in, or None."""
    return frappe.db.get_value(
        "Guest Key",
        {"check_in": check_in_name, "status": "Active"},
        ["name", "external_key_id", "provider", "room", "valid_from", "valid_until"],
        as_dict=True,
        order_by="issued_at desc",
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def issue_guest_key(
    check_in_name: str,
    requested_by: Optional[str] = None,
    card_number: Optional[str] = None,
    guest_email: Optional[str] = None,
) -> dict:
    """
    Issue a new key for an active check-in.

    Returns:
        {"success": bool, "guest_key": str|None, "log": str, "error": str|None}
    """
    _require_lock_enabled()
    _assert_roles()

    check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
    if check_in_doc.status != "Checked In":
        frappe.throw(
            _("Cannot issue a key for check-in {0} — status is '{1}'.").format(
                check_in_name, check_in_doc.status
            )
        )

    provider, mapping = get_provider_for_room(check_in_doc.room_number)
    context = _build_key_context(check_in_doc, mapping)
    if card_number:
        context.extra["card_number"] = str(card_number).strip()

    log_name = _create_log(
        provider_code=mapping["provider"],
        room=check_in_doc.room_number,
        check_in=check_in_name,
        reservation=context.canonical_reservation,
        requested_by=requested_by or frappe.session.user,
    )

    t0 = time.monotonic()
    try:
        result = provider.issue_key(context)
        duration = int((time.monotonic() - t0) * 1000)

        if result.success:
            gk_name = _upsert_guest_key(
                check_in_doc=check_in_doc,
                provider_code=mapping["provider"],
                external_key_id=result.external_key_id or "",
                valid_from=context.valid_from,
                valid_until=context.valid_until,
                status="Active",
                provider_payload=result.raw_response,
            )
            # Update compatibility fields on the check-in
            frappe.db.set_value(
                "Hotel Room Check In",
                check_in_name,
                "keycard_assigned",
                1,
                update_modified=False,
            )
            _update_log(
                log_name,
                status="Success",
                duration_ms=duration,
                provider_request_id=result.provider_request_id,
                response_payload=result.raw_response,
                guest_key=gk_name,
            )
            ret = {"success": True, "guest_key": gk_name, "log": log_name, "error": None}
            # Surface PIN code to the UI so front desk can relay it to the guest.
            # The code is only visible once at issuance time.
            if result.provider_data and result.provider_data.get("code"):
                ret["pin_code"] = str(result.provider_data["code"])
            return ret

        # Provider returned success=False (business rule rejection)
        _update_log(
            log_name,
            status="Failed",
            duration_ms=duration,
            response_payload=result.raw_response,
            error_message=result.error,
        )
        return {"success": False, "guest_key": None, "log": log_name, "error": result.error}

    except LockProviderMappingError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        return {"success": False, "guest_key": None, "log": log_name, "error": str(exc)}
    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"issue_guest_key: {check_in_name}")
        return {"success": False, "guest_key": None, "log": log_name, "error": str(exc)}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"issue_guest_key: {check_in_name}")
        return {"success": False, "guest_key": None, "log": log_name, "error": "Unexpected error issuing key."}


def reissue_guest_key(
    guest_key_name: str,
    requested_by: Optional[str] = None,
    card_number: Optional[str] = None,
    guest_email: Optional[str] = None,
) -> dict:
    """
    Reissue a key — cancel the existing one and issue a fresh card.

    Returns:
        {"success": bool, "guest_key": str|None, "log": str, "error": str|None}
    """
    _require_lock_enabled()
    _assert_roles()

    gk_doc = frappe.get_doc("Guest Key", guest_key_name)
    check_in_doc = frappe.get_doc("Hotel Room Check In", gk_doc.check_in)
    if check_in_doc.status != "Checked In":
        frappe.throw(_("Cannot reissue key — check-in is not active."))

    provider, mapping = get_provider_for_room(check_in_doc.room_number)
    context = _build_key_context(check_in_doc, mapping)
    if card_number:
        context.extra["card_number"] = str(card_number).strip()
    if guest_email:
        context.extra["guest_email"] = str(guest_email).strip()

    log_name = _create_log(
        operation_type="Reissue Key",
        provider_code=mapping["provider"],
        room=check_in_doc.room_number,
        check_in=gk_doc.check_in,
        reservation=context.canonical_reservation,
        guest_key=guest_key_name,
        requested_by=requested_by or frappe.session.user,
    )

    t0 = time.monotonic()
    try:
        result = provider.reissue_key(context, existing_key_id=gk_doc.external_key_id or "")
        duration = int((time.monotonic() - t0) * 1000)

        if result.success:
            # Mark old key as Reissued, create new key record
            frappe.db.set_value("Guest Key", guest_key_name, "status", "Reissued", update_modified=True)
            new_gk_name = _upsert_guest_key(
                check_in_doc=check_in_doc,
                provider_code=mapping["provider"],
                external_key_id=result.external_key_id or "",
                valid_from=context.valid_from,
                valid_until=context.valid_until,
                status="Active",
                provider_payload=result.raw_response,
            )
            _update_log(
                log_name,
                status="Success",
                duration_ms=duration,
                provider_request_id=result.provider_request_id,
                response_payload=result.raw_response,
                guest_key=new_gk_name,
            )
            ret = {"success": True, "guest_key": new_gk_name, "log": log_name, "error": None}
            if result.provider_data and result.provider_data.get("code"):
                ret["pin_code"] = str(result.provider_data["code"])
            return ret

        _update_log(log_name, status="Failed", duration_ms=duration,
                    response_payload=result.raw_response, error_message=result.error)
        return {"success": False, "guest_key": None, "log": log_name, "error": result.error}

    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"reissue_guest_key: {guest_key_name}")
        return {"success": False, "guest_key": None, "log": log_name, "error": str(exc)}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"reissue_guest_key: {guest_key_name}")
        return {"success": False, "guest_key": None, "log": log_name, "error": "Unexpected error reissuing key."}


def update_guest_key_validity(
    guest_key_name: str,
    new_valid_until: str,
    requested_by: Optional[str] = None,
) -> dict:
    """
    Update the valid_until time on an existing active key.

    Used after stay adjustment (extend or reduce).
    """
    _require_lock_enabled()
    _assert_roles()

    gk_doc = frappe.get_doc("Guest Key", guest_key_name)
    if gk_doc.status not in ("Active", "Draft"):
        frappe.throw(_("Key {0} is not active (status: {1}).").format(guest_key_name, gk_doc.status))

    check_in_doc = frappe.get_doc("Hotel Room Check In", gk_doc.check_in)
    provider, mapping = get_provider_for_room(check_in_doc.room_number)
    context = _build_key_context(check_in_doc, mapping)
    # Override valid_until with the explicit new value
    context.valid_until = str(new_valid_until)

    log_name = _create_log(
        operation_type="Update Validity",
        provider_code=mapping["provider"],
        room=check_in_doc.room_number,
        check_in=gk_doc.check_in,
        reservation=context.canonical_reservation,
        guest_key=guest_key_name,
        requested_by=requested_by or frappe.session.user,
    )

    t0 = time.monotonic()
    try:
        result = provider.update_key_validity(context, existing_key_id=gk_doc.external_key_id or "")
        duration = int((time.monotonic() - t0) * 1000)

        if result.success:
            frappe.db.set_value(
                "Guest Key",
                guest_key_name,
                {
                    "valid_until": new_valid_until,
                    "last_updated_at": str(now_datetime()),
                    "last_provider_status": "Active",
                    "provider_payload": json.dumps(result.raw_response or {}, default=str),
                },
                update_modified=True,
            )
            frappe.db.commit()
            _update_log(
                log_name,
                status="Success",
                duration_ms=duration,
                provider_request_id=result.provider_request_id,
                response_payload=result.raw_response,
            )
            return {"success": True, "guest_key": guest_key_name, "log": log_name, "error": None}

        _update_log(log_name, status="Failed", duration_ms=duration,
                    response_payload=result.raw_response, error_message=result.error)
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": result.error}

    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"update_guest_key_validity: {guest_key_name}")
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": str(exc)}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"update_guest_key_validity: {guest_key_name}")
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": "Unexpected error updating key."}


def cancel_guest_key(guest_key_name: str, requested_by: Optional[str] = None) -> dict:
    """Cancel a single guest key."""
    _require_lock_enabled()
    _assert_roles()

    gk_doc = frappe.get_doc("Guest Key", guest_key_name)
    if gk_doc.status == "Cancelled":
        return {"success": True, "guest_key": guest_key_name, "log": None, "error": None}

    check_in_doc = frappe.get_doc("Hotel Room Check In", gk_doc.check_in)

    try:
        provider, mapping = get_provider_for_room(check_in_doc.room_number)
    except LockProviderMappingError as exc:
        # Log failure but don't hard-block — mapping may have been removed
        frappe.log_error(str(exc), f"cancel_guest_key mapping error: {guest_key_name}")
        return {"success": False, "guest_key": guest_key_name, "log": None, "error": str(exc)}

    log_name = _create_log(
        operation_type="Cancel Key",
        provider_code=mapping["provider"],
        room=check_in_doc.room_number,
        check_in=gk_doc.check_in,
        reservation=getattr(check_in_doc, "canonical_reservation", None),
        guest_key=guest_key_name,
        requested_by=requested_by or frappe.session.user,
    )

    t0 = time.monotonic()
    try:
        result = provider.cancel_key(
            key_id=gk_doc.external_key_id or "",
            room_mapping=mapping,
        )
        duration = int((time.monotonic() - t0) * 1000)

        if result.success:
            now = str(now_datetime())
            frappe.db.set_value(
                "Guest Key",
                guest_key_name,
                {
                    "status": "Cancelled",
                    "cancelled_at": now,
                    "cancelled_by": frappe.session.user,
                    "last_provider_status": "Cancelled",
                    "provider_payload": json.dumps(result.raw_response or {}, default=str),
                },
                update_modified=True,
            )
            frappe.db.commit()
            _update_log(
                log_name,
                status="Success",
                duration_ms=duration,
                provider_request_id=result.provider_request_id,
                response_payload=result.raw_response,
            )
            return {"success": True, "guest_key": guest_key_name, "log": log_name, "error": None}

        _update_log(log_name, status="Failed", duration_ms=duration,
                    response_payload=result.raw_response, error_message=result.error)
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": result.error}

    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"cancel_guest_key: {guest_key_name}")
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": str(exc)}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"cancel_guest_key: {guest_key_name}")
        return {"success": False, "guest_key": guest_key_name, "log": log_name, "error": "Unexpected error cancelling key."}


def cancel_keys_for_check_in(check_in_name: str, requested_by: Optional[str] = None) -> dict:
    """
    Cancel all active keys for a check-in.

    Called during checkout.  Failures are logged but checkout is not blocked.

    Returns:
        {"cancelled": int, "failed": int, "logs": [str], "errors": [str]}
    """
    if not _is_lock_enabled():
        return {"cancelled": 0, "failed": 0, "logs": [], "errors": []}

    active_keys = frappe.db.get_all(
        "Guest Key",
        {"check_in": check_in_name, "status": ["in", ["Active", "Draft"]]},
        ["name"],
    )

    cancelled = 0
    failed = 0
    logs = []
    errors = []

    for key_row in active_keys:
        result = cancel_guest_key(key_row["name"], requested_by=requested_by)
        if result.get("log"):
            logs.append(result["log"])
        if result["success"]:
            cancelled += 1
        else:
            failed += 1
            if result.get("error"):
                errors.append(f"{key_row['name']}: {result['error']}")

    # Update keycard_assigned compatibility field
    if cancelled > 0 or failed == 0:
        frappe.db.set_value(
            "Hotel Room Check In",
            check_in_name,
            "keycard_assigned",
            0,
            update_modified=False,
        )
        frappe.db.commit()

    return {"cancelled": cancelled, "failed": failed, "logs": logs, "errors": errors}


def handle_room_transfer(
    check_in_name: str,
    old_room: str,
    new_room: str,
    requested_by: Optional[str] = None,
) -> dict:
    """
    Handle lock operations after an active-stay room transfer.

    Behaviour:
    1. Cancel active keys for the old room.
    2. Issue a new key for the new room.

    Called after transfer_room() has already updated the PMS.
    Returns a summary dict; failures are logged and returned but do not
    roll back the PMS room transfer.
    """
    if not _is_lock_enabled():
        return {"success": True, "cancelled": 0, "issued": False, "errors": []}
    if not bool(_get_setting("auto_handle_keys_on_room_transfer", 0)):
        return {"success": True, "cancelled": 0, "issued": False, "errors": []}

    errors = []

    # 1. Cancel keys for the old room
    old_keys = frappe.db.get_all(
        "Guest Key",
        {"check_in": check_in_name, "room": old_room, "status": ["in", ["Active", "Draft"]]},
        ["name"],
    )
    cancelled = 0
    for key_row in old_keys:
        res = cancel_guest_key(key_row["name"], requested_by=requested_by)
        if res["success"]:
            cancelled += 1
        else:
            errors.append(res.get("error") or "Cancel failed")

    # 2. Issue key for new room (check-in doc now has new room_number)
    check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
    issue_result = issue_guest_key(check_in_name, requested_by=requested_by)
    issued = issue_result["success"]
    if not issued:
        errors.append(issue_result.get("error") or "Issue failed")

    return {
        "success": len(errors) == 0,
        "cancelled": cancelled,
        "issued": issued,
        "errors": errors,
    }


def handle_stay_adjustment(
    check_in_name: str,
    new_checkout: str,
    requested_by: Optional[str] = None,
) -> dict:
    """
    Update key validity after a stay adjustment.

    Called after adjust_stay() has already updated the PMS.
    Returns a summary dict; failures are logged but do not roll back the adjustment.
    """
    if not _is_lock_enabled():
        return {"success": True, "updated": 0, "errors": []}
    if not bool(_get_setting("auto_update_keys_on_stay_adjustment", 0)):
        return {"success": True, "updated": 0, "errors": []}

    active_keys = frappe.db.get_all(
        "Guest Key",
        {"check_in": check_in_name, "status": "Active"},
        ["name"],
    )
    updated = 0
    errors = []
    for key_row in active_keys:
        res = update_guest_key_validity(
            key_row["name"], new_valid_until=new_checkout, requested_by=requested_by
        )
        if res["success"]:
            updated += 1
        else:
            errors.append(res.get("error") or "Update failed")

    return {"success": len(errors) == 0, "updated": updated, "errors": errors}


def get_lock_status(check_in_name: str) -> dict:
    """
    Return the current lock status for the room associated with a check-in.
    """
    _require_lock_enabled()
    _assert_roles()

    check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
    provider, mapping = get_provider_for_room(check_in_doc.room_number)

    log_name = _create_log(
        operation_type="Get Status",
        provider_code=mapping["provider"],
        room=check_in_doc.room_number,
        check_in=check_in_name,
    )

    t0 = time.monotonic()
    try:
        result = provider.get_lock_status(mapping)
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(
            log_name,
            status="Success" if result.success else "Failed",
            duration_ms=duration,
            response_payload=result.raw_response,
            error_message=result.error if not result.success else None,
        )
        return {
            "success": result.success,
            "status": result.provider_data,
            "error": result.error,
        }
    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        return {"success": False, "status": {}, "error": str(exc)}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"get_lock_status: {check_in_name}")
        return {"success": False, "status": {}, "error": "Unexpected error."}


def provider_health_check(provider_code: str) -> dict:
    """
    Run a health check against a specific provider.

    Restricted to Hotel Manager and System Manager.
    """
    manager_roles = {"System Manager", "Hotel Manager"}
    if not (manager_roles & set(frappe.get_roles(frappe.session.user))):
        frappe.throw(_("Only Hotel Managers and System Managers may run provider health checks."), frappe.PermissionError)

    from rhohotel.integrations.locks.registry import get_provider
    provider = get_provider(provider_code)

    log_name = _create_log(
        operation_type="Health Check",
        provider_code=provider_code,
        room="",
        requested_by=frappe.session.user,
    )
    t0 = time.monotonic()
    try:
        result = provider.health_check()
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(
            log_name,
            status="Success" if result.success else "Failed",
            duration_ms=duration,
            response_payload=result.raw_response,
            error_message=result.error if not result.success else None,
        )
        return {"success": result.success, "error": result.error, "data": result.provider_data}
    except LockProviderError as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        return {"success": False, "error": str(exc), "data": {}}
    except Exception as exc:
        duration = int((time.monotonic() - t0) * 1000)
        _update_log(log_name, status="Failed", duration_ms=duration, error_message=str(exc))
        frappe.log_error(frappe.get_traceback(), f"provider_health_check: {provider_code}")
        return {"success": False, "error": "Unexpected error.", "data": {}}
