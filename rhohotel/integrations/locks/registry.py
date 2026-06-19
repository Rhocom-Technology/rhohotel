# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
Provider registry / factory.

Usage:
    from rhohotel.integrations.locks.registry import get_provider
    provider = get_provider("mock")           # by provider_code
    # or
    provider = get_provider_for_room("101")   # resolves mapping → provider
"""

from __future__ import annotations

import importlib
from typing import Optional

import frappe
from frappe import _

from rhohotel.integrations.locks.base import (
    LockProvider,
    LockProviderMappingError,
    LockProviderError,
)


def get_provider(provider_code: str) -> LockProvider:
    """
    Load, instantiate, and return a LockProvider for the given provider_code.

    Raises:
        LockProviderError: If the provider does not exist, is disabled, or
                           the class cannot be imported.
    """
    provider_doc = frappe.db.get_value(
        "Lock Provider",
        {"provider_code": provider_code},
        [
            "name", "provider_code", "provider_label", "is_enabled",
            "environment", "provider_class_path", "timeout_seconds",
            "retry_count", "connection_config",
        ],
        as_dict=True,
    )
    if not provider_doc:
        raise LockProviderError(
            _("Lock Provider '{0}' not found.").format(provider_code)
        )
    if not provider_doc.get("is_enabled"):
        raise LockProviderError(
            _("Lock Provider '{0}' is disabled.").format(provider_code)
        )

    class_path: str = provider_doc.get("provider_class_path") or ""
    if not class_path or "." not in class_path:
        raise LockProviderError(
            _("Lock Provider '{0}' has an invalid class path: '{1}'.").format(
                provider_code, class_path
            )
        )

    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        klass = getattr(module, class_name)
    except (ImportError, AttributeError) as exc:
        raise LockProviderError(
            _("Could not load provider class '{0}': {1}").format(class_path, exc)
        ) from exc

    if not (isinstance(klass, type) and issubclass(klass, LockProvider)):
        raise LockProviderError(
            _("'{0}' is not a subclass of LockProvider.").format(class_path)
        )

    # Pass a lightweight namespace object so providers can access config fields
    # without requiring a full Frappe document load (faster and avoids DB hit).
    class _ProviderConfig:
        pass

    cfg = _ProviderConfig()
    for k, v in provider_doc.items():
        setattr(cfg, k, v)

    return klass(cfg)


def get_default_provider() -> LockProvider:
    """
    Return the default lock provider.

    Resolution order:
    1. Lock Provider with is_default=1
    2. Hotel Settings.default_lock_provider
    3. Any single enabled provider

    Raises LockProviderError if nothing is configured.
    """
    # 1. Explicit default flag on provider record
    default_code = frappe.db.get_value(
        "Lock Provider", {"is_default": 1, "is_enabled": 1}, "provider_code"
    )
    if default_code:
        return get_provider(default_code)

    # 2. Hotel Settings default
    settings_code = frappe.db.get_single_value("Hotel Settings", "default_lock_provider")
    if settings_code:
        return get_provider(settings_code)

    # 3. Any single enabled provider
    all_codes = frappe.db.get_all(
        "Lock Provider", {"is_enabled": 1}, pluck="provider_code", limit=2
    )
    if len(all_codes) == 1:
        return get_provider(all_codes[0])

    raise LockProviderError(
        _(
            "No default lock provider is configured. Set a default in Hotel Settings "
            "or mark one Lock Provider as default."
        )
    )


def get_room_mapping(room_number: str, provider_code: Optional[str] = None):
    """
    Return the enabled Room Lock Mapping for *room_number*.

    If *provider_code* is given, filter by provider. Otherwise return the
    first enabled mapping.

    Returns:
        dict with room, provider, external_lock_id, lock_alias fields.

    Raises:
        LockProviderMappingError: if no enabled mapping exists.
    """
    filters: dict = {"room": room_number, "is_enabled": 1}
    if provider_code:
        filters["provider"] = provider_code

    mapping = frappe.db.get_value(
        "Room Lock Mapping",
        filters,
        [
            "name", "room", "provider", "external_lock_id", "lock_alias",
            "last_sync_status", "last_sync_time",
        ],
        as_dict=True,
    )
    if not mapping:
        raise LockProviderMappingError(
            _(
                "No active Room Lock Mapping found for room '{0}'. "
                "Please configure a mapping in the Room Lock Mapping list."
            ).format(room_number)
        )
    return mapping


def get_provider_for_room(room_number: str) -> tuple[LockProvider, dict]:
    """
    Resolve the provider and mapping for a room in a single call.

    Returns:
        (provider, mapping_dict)

    Raises:
        LockProviderMappingError: if no enabled mapping.
        LockProviderError: if the mapped provider is unavailable.
    """
    mapping = get_room_mapping(room_number)
    provider = get_provider(mapping["provider"])
    return provider, mapping
