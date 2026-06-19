# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
Lock provider contract.

All smart-lock integrations must subclass LockProvider and implement every
abstract method.  The service layer is vendor-neutral and only ever calls
methods defined here.

KeyContext — information the service passes to the provider for every operation.
ProviderResult — standardised response object every provider method must return.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------

@dataclass
class KeyContext:
    """All the PMS context a provider needs to perform a key operation."""
    check_in_name: str
    room_number: str
    external_lock_id: str          # From Room Lock Mapping — never inferred from room number
    guest_name: str
    valid_from: str                # ISO datetime string
    valid_until: str               # ISO datetime string
    canonical_reservation: Optional[str] = None
    extra: dict = field(default_factory=dict)   # Provider-specific extras if needed


@dataclass
class ProviderResult:
    """Normalised result returned by every provider method."""
    success: bool
    external_key_id: Optional[str] = None     # Key/card ID in the provider system
    provider_request_id: Optional[str] = None  # Provider-side request/transaction ID
    raw_response: Optional[dict] = None        # Full (possibly redacted) provider response
    error: Optional[str] = None               # Human-readable error if success=False
    provider_data: dict = field(default_factory=dict)  # Any extra structured data


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LockProviderError(Exception):
    """Base exception for all provider errors."""


class LockProviderAuthError(LockProviderError):
    """Provider authentication / credential failure."""


class LockProviderMappingError(LockProviderError):
    """Room is not mapped to a lock, or the mapping is disabled."""


class LockProviderRequestError(LockProviderError):
    """Provider rejected the request (invalid parameters, business rule violation)."""


class LockProviderUnavailableError(LockProviderError):
    """Provider API is unreachable or returned an unexpected error."""


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class LockProvider(ABC):
    """
    Abstract base class for all lock providers.

    Constructor receives the Frappe `Lock Provider` document so each provider
    can read its own connection_config and any credentials it stores in
    its own settings.  The base class does not read passwords or secrets —
    each concrete provider is responsible for retrieving its own credentials
    through secure Frappe get_password() calls.
    """

    def __init__(self, provider_doc: Any) -> None:
        """
        Args:
            provider_doc: A Frappe `Lock Provider` document (or dict-like).
        """
        self.provider_doc = provider_doc
        self.provider_code: str = getattr(provider_doc, "provider_code", "") or ""
        self.timeout: int = int(getattr(provider_doc, "timeout_seconds", 30) or 30)
        self.retry_count: int = int(getattr(provider_doc, "retry_count", 2) or 2)

    # ------------------------------------------------------------------
    # Core key operations — every provider must implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def issue_key(self, context: KeyContext) -> ProviderResult:
        """
        Issue a new key for the guest described in *context*.

        The provider should use context.external_lock_id to identify the lock.
        On success, ProviderResult.external_key_id must contain the provider key ID.
        """

    @abstractmethod
    def reissue_key(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        """
        Reissue a key (replace existing one with a new key/card for the same stay).

        Behaviour:
        - Cancel the existing key in the provider system.
        - Issue a fresh key with the same validity window.
        - Return the new key ID in ProviderResult.external_key_id.
        """

    @abstractmethod
    def update_key_validity(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        """
        Update the valid_until time of an existing key without reissuing it.

        Used when a stay is extended or reduced.
        """

    @abstractmethod
    def cancel_key(
        self,
        key_id: str,
        room_mapping: Any,
        context: Optional[KeyContext] = None,
    ) -> ProviderResult:
        """
        Cancel/invalidate a key in the provider system.

        Args:
            key_id: The external_key_id to cancel.
            room_mapping: The Room Lock Mapping document (provides external_lock_id).
            context: Optional stay context for providers that need it.
        """

    @abstractmethod
    def transfer_key(
        self,
        context: KeyContext,
        old_room_mapping: Any,
        new_room_mapping: Any,
        existing_key_id: str,
    ) -> ProviderResult:
        """
        Transfer a key from one room to another (room transfer mid-stay).

        Default implementation: cancel old key + issue new key.
        Override if the provider has a native transfer operation.
        """

    # ------------------------------------------------------------------
    # Status / diagnostics
    # ------------------------------------------------------------------

    @abstractmethod
    def get_lock_status(self, room_mapping: Any) -> ProviderResult:
        """Return current status of the physical lock (battery, online/offline, etc.)."""

    @abstractmethod
    def health_check(self) -> ProviderResult:
        """
        Validate that the provider API is reachable and credentials are valid.

        Returns ProviderResult(success=True) if healthy.
        """

    # ------------------------------------------------------------------
    # Helpers available to all providers
    # ------------------------------------------------------------------

    def _redact(self, payload: dict, keys: tuple[str, ...] = ()) -> dict:
        """
        Return a copy of *payload* with sensitive keys replaced by '***'.

        The base set of keys that are always redacted is extended by
        any provider-specific *keys* passed in.
        """
        always_redact = {
            "password", "secret", "token", "access_token", "refresh_token",
            "api_key", "apikey", "api_secret", "client_secret", "cardSecret",
            "card_secret", "key_secret", "passCode",
        }
        redact_set = always_redact | set(keys)

        def _walk(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    k: "***" if k.lower() in redact_set else _walk(v)
                    for k, v in obj.items()
                }
            if isinstance(obj, list):
                return [_walk(item) for item in obj]
            return obj

        return _walk(payload)
