# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
TT Hotel / TTLock Cloud Open API provider.

Implements the LockProvider contract for the TTLock Cloud Open API v3.

Provider Code:  tt_hotel
Class Path:     rhohotel.integrations.locks.tt_hotel_provider.TTHotelProvider

Credential storage:
    Credentials are read from the "TT Hotel Settings" singleton DocType
    (client_id Data field, client_secret Password field).  This DocType is
    accessible only to System Manager — credentials are NEVER returned to
    the browser.

TTLock API reference: https://open.ttlock.com/developer/guide
EU endpoint: https://euapi.ttlock.com
US endpoint: https://api.ttlock.com

Notes:
  • All POST requests use application/x-www-form-urlencoded (not JSON).
  • Timestamps are milliseconds since Unix epoch.
  • lockId and keyId are integers.
  • errcode == 0 means success; any other value is an error.
  • Two key types are supported:
      eKey    — mobile-app e-key sent to guest's phone via TTLock app
      IC Card — physical RFID card programmed via a card encoder device
"""

from __future__ import annotations

import calendar
import json
import time as _time
from typing import Any, Optional

from rhohotel.integrations.locks.base import (
    KeyContext,
    LockProvider,
    LockProviderAuthError,
    LockProviderRequestError,
    LockProviderUnavailableError,
    ProviderResult,
)

# Lazy Frappe import so the module can be loaded in unit tests without a
# running Frappe context.
try:
    from frappe import _
except ImportError:
    def _(s: str, *args, **kwargs) -> str:  # type: ignore[misc]
        return s

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EU_BASE = "https://euapi.ttlock.com"
_US_BASE = "https://api.ttlock.com"

# TTLock error codes that indicate the key/card does not exist on the lock side.
# We treat these as "already gone" and return success for cancel operations.
_KEY_NOT_FOUND_ERRCODES = {10007, 10009, 10010, 30007}

# Maximum key name length accepted by TTLock
_MAX_KEY_NAME = 32


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class TTHotelProvider(LockProvider):
    """
    TTLock Cloud Open API lock provider.

    Reads all configuration from the "TT Hotel Settings" singleton DocType.

    connection_config JSON keys (Lock Provider record — non-secret):
        base_url  (str): Override the API endpoint.  Default: EU endpoint.
        key_type  (str): "eKey" or "IC Card".  Overrides TT Hotel Settings.
    """

    def __init__(self, provider_doc: Any) -> None:
        super().__init__(provider_doc)
        config_str = getattr(provider_doc, "connection_config", None) or "{}"
        try:
            self._config: dict = (
                json.loads(config_str) if isinstance(config_str, str) else dict(config_str)
            )
        except (json.JSONDecodeError, TypeError):
            self._config = {}

        # _base_url and _key_type are finalised lazily in _load_settings()
        # because they may depend on TT Hotel Settings which needs a DB call.
        self._base_url: Optional[str] = self._config.get("base_url")
        self._key_type: Optional[str] = self._config.get("key_type")
        self._settings_loaded: bool = False

        # OAuth2 token cache
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Settings / credential helpers
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        """Load TT Hotel Settings from DB (once per provider instance)."""
        if self._settings_loaded:
            return
        import frappe

        doc = frappe.get_cached_doc("TT Hotel Settings")
        if not self._base_url:
            self._base_url = (doc.base_url or _EU_BASE).rstrip("/")
        else:
            self._base_url = self._base_url.rstrip("/")
        if not self._key_type:
            self._key_type = doc.key_type or "eKey"
        self._settings_loaded = True

    def _get_credentials(self) -> tuple[str, str]:
        """
        Return (client_id, client_secret) from TT Hotel Settings.

        Raises LockProviderAuthError if not configured.
        Credentials are NEVER logged or returned to the browser.
        """
        import frappe
        from frappe.utils.password import get_decrypted_password

        client_id = frappe.db.get_single_value("TT Hotel Settings", "client_id") or ""
        client_secret = (
            get_decrypted_password("TT Hotel Settings", "TT Hotel Settings", "client_secret")
            or ""
        )
        if not client_id or not client_secret:
            raise LockProviderAuthError(
                _(
                    "TTLock credentials are not configured. "
                    "Go to TT Hotel Settings and enter your Client ID and Client Secret."
                )
            )
        return client_id, client_secret

    def _get_lock_id_is_int(self) -> bool:
        """Whether lockId / keyId should be cast to int."""
        import frappe
        return bool(frappe.db.get_single_value("TT Hotel Settings", "lock_id_is_integer") or 1)

    def _coerce_id(self, value: str) -> Any:
        """Return value as int if lock_id_is_integer is set, else str."""
        try:
            return int(value) if self._get_lock_id_is_int() else str(value)
        except (TypeError, ValueError):
            return str(value)

    def _key_name(self, context: KeyContext) -> str:
        """Build the key name shown in the TTLock app."""
        import frappe
        prefix = frappe.db.get_single_value("TT Hotel Settings", "default_key_name_prefix") or "Guest"
        raw = f"{prefix} {context.guest_name}"
        return raw[:_MAX_KEY_NAME]

    # ------------------------------------------------------------------
    # OAuth2 access token
    # ------------------------------------------------------------------

    def _get_access_token(self) -> str:
        """
        Return a cached access token, refreshing it 30 seconds before expiry.

        TTLock OAuth2 flow:
            POST /oauth2/token  (application/x-www-form-urlencoded)
            Body: clientId=…&clientSecret=…&grant_type=client_credentials
        """
        if self._token and _time.monotonic() < self._token_expiry - 30:
            return self._token

        self._load_settings()
        client_id, client_secret = self._get_credentials()

        url = f"{self._base_url}/oauth2/token"
        data = {
            "clientId": client_id,
            "clientSecret": client_secret,
            "grant_type": "client_credentials",
        }
        resp = self._post(url, data, _skip_auth=True)

        access_token: str = resp.get("access_token") or ""
        expires_in = int(resp.get("expires_in") or 7200)
        if not access_token:
            raise LockProviderAuthError(
                _("TTLock did not return an access_token — check credentials in TT Hotel Settings.")
            )
        self._token = access_token
        self._token_expiry = _time.monotonic() + expires_in
        return self._token

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _common_params(self) -> dict:
        """Parameters included in every authenticated request."""
        client_id, _ = self._get_credentials()
        return {
            "clientId": client_id,
            "accessToken": self._get_access_token(),
            "date": _now_ms(),
        }

    def _post(self, url: str, data: dict, _skip_auth: bool = False) -> dict:
        """
        POST with application/x-www-form-urlencoded body.
        TTLock requires form-encoded POST for all mutation endpoints.
        """
        try:
            import requests as _req
        except ImportError as exc:
            raise LockProviderUnavailableError("requests library not available") from exc

        try:
            resp = _req.post(url, data=data, timeout=self.timeout)
            resp.raise_for_status()
        except _req.exceptions.Timeout as exc:
            raise LockProviderUnavailableError(
                _("TTLock API timed out ({0}s).").format(self.timeout)
            ) from exc
        except _req.exceptions.ConnectionError as exc:
            raise LockProviderUnavailableError(
                _("Cannot reach TTLock API: {0}").format(str(exc))
            ) from exc
        except _req.exceptions.HTTPError as exc:
            raise LockProviderUnavailableError(
                _("TTLock API HTTP error: {0}").format(str(exc))
            ) from exc

        return self._parse(resp)

    def _get(self, url: str, params: dict) -> dict:
        """GET with query parameters."""
        try:
            import requests as _req
        except ImportError as exc:
            raise LockProviderUnavailableError("requests library not available") from exc

        try:
            resp = _req.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except _req.exceptions.Timeout as exc:
            raise LockProviderUnavailableError(
                _("TTLock API timed out ({0}s).").format(self.timeout)
            ) from exc
        except _req.exceptions.ConnectionError as exc:
            raise LockProviderUnavailableError(
                _("Cannot reach TTLock API: {0}").format(str(exc))
            ) from exc
        except _req.exceptions.HTTPError as exc:
            raise LockProviderUnavailableError(
                _("TTLock API HTTP error: {0}").format(str(exc))
            ) from exc

        return self._parse(resp)

    def _parse(self, resp: Any) -> dict:
        """Parse response JSON and raise on TTLock-level errors."""
        try:
            data = resp.json()
        except ValueError as exc:
            raise LockProviderUnavailableError(
                _("TTLock API returned non-JSON response.")
            ) from exc

        err_code = data.get("errcode") or data.get("errCode")
        if err_code is not None and int(err_code) != 0:
            errmsg_raw = data.get("errmsg") or data.get("errMsg") or "Unknown error"
            if isinstance(errmsg_raw, list):
                errmsg = ", ".join(str(m) for m in errmsg_raw) or "Unknown error"
            else:
                errmsg = str(errmsg_raw)
            raise LockProviderRequestError(
                _("TTLock error {0}: {1}").format(err_code, errmsg)
            )
        return data

    # ------------------------------------------------------------------
    # LockProvider implementation
    # ------------------------------------------------------------------

    def issue_key(self, context: KeyContext) -> ProviderResult:
        """
        Issue a key for the guest.

        eKey flow  → POST /v3/ekey/add
        IC Card    → POST /v3/ic/add  (requires a card encoder on-site)

        Returns ProviderResult with external_key_id set to the TTLock keyId/icCardId.
        """
        self._load_settings()
        if self._key_type == "IC Card":
            return self._issue_ic_card(context)
        return self._issue_ekey(context)

    def _issue_ekey(self, context: KeyContext) -> ProviderResult:
        """POST /v3/ekey/add — mobile app e-key."""
        url = f"{self._base_url}/v3/ekey/add"
        data = {
            **self._common_params(),
            "lockId": self._coerce_id(context.external_lock_id),
            "keyName": self._key_name(context),
            "startDate": _iso_to_ms(context.valid_from),
            "endDate": _iso_to_ms(context.valid_until),
        }
        raw = self._post(url, data)
        key_id = str(raw.get("keyId") or "")
        if not key_id:
            return ProviderResult(
                success=False,
                raw_response=self._redact(raw),
                error=_("TTLock did not return a keyId for the eKey."),
            )
        return ProviderResult(
            success=True,
            external_key_id=key_id,
            provider_request_id=str(raw.get("requestId") or ""),
            raw_response=self._redact(raw),
            provider_data={"key_type": "eKey", "key_id": key_id},
        )

    def _issue_ic_card(self, context: KeyContext) -> ProviderResult:
        """
        POST /v3/ic/add — physical RFID card.

        Requires the card's UID (cardNumber) which must be read beforehand
        by a card reader (USB RFID reader at the front desk, or a TTLock
        card encoder on-site) and passed as context.extra["card_number"].
        """
        card_number = str(context.extra.get("card_number") or "").strip()
        if not card_number:
            raise LockProviderRequestError(
                _(
                    "IC Card issuance requires the card UID. "
                    "Scan the card with the card reader then enter the number in the Issue Key form."
                )
            )
        url = f"{self._base_url}/v3/ic/add"
        data = {
            **self._common_params(),
            "lockId": self._coerce_id(context.external_lock_id),
            "cardNumber": card_number,
            "keyName": self._key_name(context),
            "startDate": _iso_to_ms(context.valid_from),
            "endDate": _iso_to_ms(context.valid_until),
        }
        raw = self._post(url, data)
        card_id = str(raw.get("icCardId") or raw.get("keyId") or "")
        if not card_id:
            return ProviderResult(
                success=False,
                raw_response=self._redact(raw),
                error=_("TTLock did not return an icCardId for the IC Card."),
            )
        return ProviderResult(
            success=True,
            external_key_id=card_id,
            provider_request_id=str(raw.get("requestId") or ""),
            raw_response=self._redact(raw),
            provider_data={
                "key_type": "IC Card",
                "ic_card_id": card_id,
                "card_number": raw.get("cardNumber") or "",
            },
        )

    def reissue_key(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        """Delete the existing key then issue a new one."""
        cancel = self._delete_key(existing_key_id, context.external_lock_id)
        if not cancel.success:
            return cancel
        return self.issue_key(context)

    def update_key_validity(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        """
        Update the validity window of an existing key without reissuing it.

        eKey   → POST /v3/ekey/changePeriod
        IC Card → POST /v3/ic/changePeriod
        """
        self._load_settings()
        if self._key_type == "IC Card":
            return self._change_ic_period(context, existing_key_id)
        return self._change_ekey_period(context, existing_key_id)

    def _change_ekey_period(self, context: KeyContext, key_id: str) -> ProviderResult:
        url = f"{self._base_url}/v3/ekey/changePeriod"
        data = {
            **self._common_params(),
            "lockId": self._coerce_id(context.external_lock_id),
            "keyId": self._coerce_id(key_id),
            "startDate": _iso_to_ms(context.valid_from),
            "endDate": _iso_to_ms(context.valid_until),
        }
        raw = self._post(url, data)
        return ProviderResult(
            success=True,
            external_key_id=key_id,
            provider_request_id=str(raw.get("requestId") or ""),
            raw_response=self._redact(raw),
            provider_data={"updated": True, "key_type": "eKey"},
        )

    def _change_ic_period(self, context: KeyContext, card_id: str) -> ProviderResult:
        url = f"{self._base_url}/v3/ic/changePeriod"
        data = {
            **self._common_params(),
            "lockId": self._coerce_id(context.external_lock_id),
            "icCardId": self._coerce_id(card_id),
            "startDate": _iso_to_ms(context.valid_from),
            "endDate": _iso_to_ms(context.valid_until),
        }
        raw = self._post(url, data)
        return ProviderResult(
            success=True,
            external_key_id=card_id,
            provider_request_id=str(raw.get("requestId") or ""),
            raw_response=self._redact(raw),
            provider_data={"updated": True, "key_type": "IC Card"},
        )

    def cancel_key(
        self,
        key_id: str,
        room_mapping: Any,
        context: Optional[KeyContext] = None,
    ) -> ProviderResult:
        lock_id = (
            room_mapping.get("external_lock_id")
            if isinstance(room_mapping, dict)
            else getattr(room_mapping, "external_lock_id", "")
        )
        return self._delete_key(key_id, lock_id)

    def transfer_key(
        self,
        context: KeyContext,
        old_room_mapping: Any,
        new_room_mapping: Any,
        existing_key_id: str,
    ) -> ProviderResult:
        """Cancel old-room key then issue a new key for the new room."""
        old_lock_id = (
            old_room_mapping.get("external_lock_id")
            if isinstance(old_room_mapping, dict)
            else getattr(old_room_mapping, "external_lock_id", "")
        )
        cancel = self._delete_key(existing_key_id, old_lock_id)
        if not cancel.success:
            return cancel
        return self.issue_key(context)

    def get_lock_status(self, room_mapping: Any) -> ProviderResult:
        """
        Query lock detail and open state.

        GET /v3/lock/detail        — battery, firmware, lock name
        GET /v3/lock/queryOpenState — 0=locked, 1=unlocked, 2=unknown
        """
        self._load_settings()
        lock_id = (
            room_mapping.get("external_lock_id")
            if isinstance(room_mapping, dict)
            else getattr(room_mapping, "external_lock_id", "")
        )
        base_params = {
            **self._common_params(),
            "lockId": self._coerce_id(lock_id),
        }

        detail: dict = {}
        open_state: dict = {}
        errors: list[str] = []

        try:
            detail = self._get(f"{self._base_url}/v3/lock/detail", base_params)
        except LockProviderRequestError as exc:
            errors.append(f"detail: {exc}")

        try:
            # Refresh date/token for second call
            base_params["date"] = _now_ms()
            base_params["accessToken"] = self._get_access_token()
            open_state = self._get(f"{self._base_url}/v3/lock/queryOpenState", base_params)
        except LockProviderRequestError as exc:
            errors.append(f"open_state: {exc}")

        state = open_state.get("state")  # 0=locked, 1=unlocked, 2=unknown
        battery = detail.get("electricQuantity")  # 0–100

        return ProviderResult(
            success=True,
            raw_response=self._redact({**detail, "open_state": open_state}),
            provider_data={
                "locked": state == 0,
                "open_state": state,
                "battery_level": battery,
                "lock_name": detail.get("lockName"),
                "firmware_version": detail.get("firmwareRevision"),
                "errors": errors or None,
            },
        )

    def health_check(self) -> ProviderResult:
        """Verify API reachability by obtaining an access token."""
        try:
            self._load_settings()
            token = self._get_access_token()
            return ProviderResult(
                success=bool(token),
                raw_response={"status": "ok", "token_obtained": True},
                provider_data={"status": "ok", "base_url": self._base_url},
            )
        except LockProviderAuthError as exc:
            return ProviderResult(
                success=False,
                error=str(exc),
                provider_data={"status": "auth_error"},
            )
        except LockProviderUnavailableError as exc:
            return ProviderResult(
                success=False,
                error=str(exc),
                provider_data={"status": "unavailable"},
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _delete_key(self, key_id: str, lock_id: str) -> ProviderResult:
        """
        Delete/cancel a key.

        eKey   → POST /v3/ekey/delete
        IC Card → POST /v3/ic/delete

        Both endpoints accept the same parameters.  If the key no longer
        exists on the lock (already deleted), we treat that as success.
        """
        self._load_settings()
        endpoint = (
            "/v3/ic/delete" if self._key_type == "IC Card" else "/v3/ekey/delete"
        )
        id_field = "icCardId" if self._key_type == "IC Card" else "keyId"

        url = f"{self._base_url}{endpoint}"
        data = {
            **self._common_params(),
            "lockId": self._coerce_id(lock_id),
            id_field: self._coerce_id(key_id),
        }

        try:
            raw = self._post(url, data)
        except LockProviderRequestError as exc:
            # Treat "key not found" error codes as already-cancelled
            msg = str(exc)
            for code in _KEY_NOT_FOUND_ERRCODES:
                if str(code) in msg:
                    return ProviderResult(
                        success=True,
                        external_key_id=key_id,
                        raw_response={"note": "key not found on lock — treated as cancelled"},
                        provider_data={"deleted": True, "was_missing": True},
                    )
            return ProviderResult(
                success=False,
                external_key_id=key_id,
                error=str(exc),
                provider_data={"deleted": False},
            )

        return ProviderResult(
            success=True,
            external_key_id=key_id,
            provider_request_id=str(raw.get("requestId") or ""),
            raw_response=self._redact(raw),
            provider_data={"deleted": True},
        )


# ---------------------------------------------------------------------------
# Datetime / timestamp utilities
# ---------------------------------------------------------------------------

def _iso_to_ms(dt_str: str) -> int:
    """Convert an ISO datetime string to milliseconds since Unix epoch."""
    try:
        from frappe.utils import get_datetime
        dt = get_datetime(dt_str)
    except ImportError:
        from datetime import datetime
        dt = datetime.fromisoformat(str(dt_str).replace("T", " ").split(".")[0])
    return int(calendar.timegm(dt.timetuple()) * 1000)


def _now_ms() -> int:
    """Current time in milliseconds since Unix epoch."""
    return int(_time.time() * 1000)

