# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
Whitelisted lock API surface for the Vue front desk UI.

All provider calls are server-side.  Credentials, raw tokens, and sensitive
card data are never returned to the browser.
"""

from __future__ import annotations

from typing import Optional

import frappe
from frappe import _


_ALLOWED_ROLES = frozenset(
    ["System Manager", "Hotel Manager", "Front Desk Manager", "Hotel Receptionist"]
)
_MANAGER_ROLES = frozenset(["System Manager", "Hotel Manager"])


def _check_role(roles=None):
    allowed = roles or _ALLOWED_ROLES
    if not (allowed & set(frappe.get_roles(frappe.session.user))):
        frappe.throw(_("You do not have permission to perform this operation."), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Context / metadata
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_lock_context(check_in_name: str) -> dict:
    """
    Return lock status summary for the active check-in panel.

    Response fields (sanitised — no secrets):
        enabled:       bool
        has_mapping:   bool
        provider:      str | None
        active_key:    dict | None  (name, valid_from, valid_until, status)
        recent_logs:   list[dict]   (last 5 operation logs)
    """
    _check_role()

    enabled = bool(frappe.db.get_single_value("Hotel Settings", "enable_lock_integration"))
    if not enabled:
        return {"enabled": False, "has_mapping": False, "provider": None, "active_key": None, "recent_logs": []}

    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        frappe.throw(_("Check-in not found: {0}").format(check_in_name))

    room_number = frappe.db.get_value("Hotel Room Check In", check_in_name, "room_number")

    # Mapping
    mapping = frappe.db.get_value(
        "Room Lock Mapping",
        {"room": room_number, "is_enabled": 1},
        ["name", "provider", "external_lock_id", "lock_alias", "last_sync_status"],
        as_dict=True,
    )
    has_mapping = bool(mapping)
    provider_label = None
    if mapping:
        provider_label = frappe.db.get_value("Lock Provider", mapping["provider"], "provider_label")

    # Active key
    active_key = frappe.db.get_value(
        "Guest Key",
        {"check_in": check_in_name, "status": "Active"},
        ["name", "valid_from", "valid_until", "status", "issued_at", "issued_by"],
        as_dict=True,
        order_by="issued_at desc",
    )

    # Whether this provider/config requires a physical card UID input
    requires_card_number = False
    # Whether this provider requires a guest email for key delivery (Salto mobile)
    requires_guest_email = False

    if mapping:
        prov = mapping.get("provider") or ""
        if prov == "tt_hotel":
            try:
                key_type = frappe.db.get_single_value("TT Hotel Settings", "key_type") or "eKey"
                requires_card_number = key_type == "IC Card"
            except Exception:
                pass
        elif prov == "salto":
            try:
                key_type = frappe.db.get_single_value("Salto Settings", "key_type") or "code"
                requires_guest_email = key_type == "mobile"
            except Exception:
                pass

    # Recent logs (last 5)
    recent_logs = frappe.db.get_all(
        "Lock Operation Log",
        {"check_in": check_in_name},
        ["name", "operation_type", "status", "request_datetime", "error_message", "duration_ms"],
        order_by="request_datetime desc",
        limit=5,
    )

    return {
        "enabled": True,
        "has_mapping": has_mapping,
        "provider": provider_label,
        "requires_card_number": requires_card_number,
        "requires_guest_email": requires_guest_email,
        "active_key": active_key,
        "recent_logs": recent_logs,
    }


# ---------------------------------------------------------------------------
# Key operations
# ---------------------------------------------------------------------------

@frappe.whitelist()
def issue_key(check_in_name: str, card_number: Optional[str] = None, guest_email: Optional[str] = None) -> dict:
    """Issue a new key for an active check-in."""
    _check_role()
    from rhohotel.integrations.locks.service import issue_guest_key
    result = issue_guest_key(
        check_in_name,
        requested_by=frappe.session.user,
        card_number=card_number or None,
        guest_email=guest_email or None,
    )
    return _sanitise(result)


@frappe.whitelist()
def reissue_key(guest_key_name: str, card_number: Optional[str] = None, guest_email: Optional[str] = None) -> dict:
    """Reissue (replace) a key for an active check-in."""
    _check_role()
    from rhohotel.integrations.locks.service import reissue_guest_key
    result = reissue_guest_key(
        guest_key_name,
        requested_by=frappe.session.user,
        card_number=card_number or None,
        guest_email=guest_email or None,
    )
    return _sanitise(result)


@frappe.whitelist()
def update_key(guest_key_name: str, new_valid_until: str) -> dict:
    """Update the validity window of an existing key."""
    _check_role()
    from rhohotel.integrations.locks.service import update_guest_key_validity
    result = update_guest_key_validity(
        guest_key_name, new_valid_until=new_valid_until, requested_by=frappe.session.user
    )
    return _sanitise(result)


@frappe.whitelist()
def cancel_key(guest_key_name: str) -> dict:
    """Cancel a single guest key."""
    _check_role()
    from rhohotel.integrations.locks.service import cancel_guest_key
    result = cancel_guest_key(guest_key_name, requested_by=frappe.session.user)
    return _sanitise(result)


@frappe.whitelist()
def cancel_keys_for_check_in(check_in_name: str) -> dict:
    """Cancel all active keys for a check-in (called at checkout)."""
    _check_role()
    from rhohotel.integrations.locks.service import cancel_keys_for_check_in as _cancel
    result = _cancel(check_in_name, requested_by=frappe.session.user)
    return result


@frappe.whitelist()
def get_operation_logs(check_in_name: str, limit: int = 20) -> list:
    """Return operation log entries for a check-in (read-only, no sensitive data)."""
    _check_role()
    return frappe.db.get_all(
        "Lock Operation Log",
        {"check_in": check_in_name},
        [
            "name", "operation_type", "status", "provider", "room",
            "requested_by", "request_datetime", "duration_ms", "error_message",
            "provider_request_id", "retry_count",
        ],
        order_by="request_datetime desc",
        limit=int(limit),
    )


# ---------------------------------------------------------------------------
# Diagnostics (managers only)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def provider_health_check(provider_code: str) -> dict:
    """Run a connectivity/credential health check for a provider."""
    _check_role(roles=_MANAGER_ROLES)
    from rhohotel.integrations.locks.service import provider_health_check as _check
    return _check(provider_code)


@frappe.whitelist()
def get_lock_status(check_in_name: str) -> dict:
    """Query the physical lock status for a room (managers only)."""
    _check_role(roles=_MANAGER_ROLES)
    from rhohotel.integrations.locks.service import get_lock_status as _status
    return _status(check_in_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitise(result: dict) -> dict:
    """Strip any fields that should not be returned to the browser."""
    safe_keys = {"success", "guest_key", "log", "error", "updated", "cancelled", "failed", "errors", "pin_code"}
    return {k: v for k, v in (result or {}).items() if k in safe_keys}
