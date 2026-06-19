# Adding a New Smart Lock Provider

This guide walks through every step needed to add a new hardware or cloud lock
provider to the Rhocom Hotel PMS lock integration framework.

---

## Architecture overview

```
PMS workflows (check-in / checkout / stay adjustment / room transfer)
        │
        ▼
  service.py  ←─ the only layer that should be called by Frappe code
        │
        ▼
  registry.py ←─ resolves provider_code → LockProvider instance
        │         resolves room_number   → Room Lock Mapping + LockProvider
        ▼
  YourProvider  ←─ subclass of LockProvider (base.py)
        │
        ▼
  Vendor API / SDK
```

All providers share the same contract defined in
`rhohotel/integrations/locks/base.py`. The service layer never imports a
provider directly — it always goes through the registry using a `provider_code`
string stored in the database.

---

## Step 1 — Write the provider class

Create a new file inside `rhohotel/integrations/locks/`:

```
rhohotel/integrations/locks/acme_provider.py
```

### Minimal skeleton

```python
from __future__ import annotations

import json
from typing import Any, Optional

from rhohotel.integrations.locks.base import (
    KeyContext,
    LockProvider,
    LockProviderAuthError,
    LockProviderRequestError,
    LockProviderUnavailableError,
    ProviderResult,
)

# Lazy Frappe import so the module can be imported in unit tests without a
# running Frappe context.
try:
    from frappe import _
except ImportError:
    def _(s: str, *args, **kwargs) -> str:  # type: ignore[misc]
        return s


class AcmeLockProvider(LockProvider):
    """
    ACME Smart Lock Cloud API provider.

    Provider Code: acme
    Class Path:    rhohotel.integrations.locks.acme_provider.AcmeLockProvider

    connection_config JSON keys:
        base_url (str): Override the default API endpoint.
        timeout  (int): Per-request timeout in seconds.
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

        self._base_url: str = (
            self._config.get("base_url") or "https://api.acmelocks.example.com"
        ).rstrip("/")

    # ------------------------------------------------------------------
    # Credential helper — keep secrets server-side only
    # ------------------------------------------------------------------

    def _get_api_key(self) -> str:
        """
        Read the API key from Frappe secure storage.
        Never log or return this value to the browser.
        """
        import frappe

        api_key = frappe.utils.password.get_decrypted_password(
            "ACME Lock Settings",   # DocType name
            "ACME Lock Settings",   # Document name (singleton)
            "api_key",              # Password field name
        ) or ""
        if not api_key:
            raise LockProviderAuthError(
                _("ACME Lock API key is not configured in ACME Lock Settings.")
            )
        return api_key

    # ------------------------------------------------------------------
    # LockProvider implementation
    # ------------------------------------------------------------------

    def issue_key(self, context: KeyContext) -> ProviderResult:
        # TODO: call ACME API to create a key / access credential
        raise NotImplementedError

    def reissue_key(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        # Cancel old key then issue a new one (or use a native reissue endpoint)
        raise NotImplementedError

    def update_key_validity(
        self,
        context: KeyContext,
        existing_key_id: str,
    ) -> ProviderResult:
        # Update valid_until on an existing key without changing the key ID
        raise NotImplementedError

    def cancel_key(
        self,
        key_id: str,
        room_mapping: Any,
        context: Optional[KeyContext] = None,
    ) -> ProviderResult:
        # Revoke the key in the ACME system
        raise NotImplementedError

    def transfer_key(
        self,
        context: KeyContext,
        old_room_mapping: Any,
        new_room_mapping: Any,
        existing_key_id: str,
    ) -> ProviderResult:
        # Default: cancel old + issue new.  Override if ACME has a native transfer.
        self.cancel_key(
            key_id=existing_key_id,
            room_mapping=old_room_mapping,
            context=context,
        )
        return self.issue_key(context)

    def get_lock_status(self, room_mapping: Any) -> ProviderResult:
        # Query battery level, online/offline, etc.
        raise NotImplementedError

    def health_check(self) -> ProviderResult:
        # Ping the API and verify credentials are valid
        raise NotImplementedError
```

### Rules every provider must follow

| Rule | Why |
|------|-----|
| Never import `frappe` at module level | Allows unit tests to import the class without a running Frappe instance |
| Never log or return credentials | OWASP A02 — credentials must stay server-side |
| Always call `self._redact(payload)` before storing `raw_response` | Strips tokens/secrets from audit logs automatically |
| Return `ProviderResult(success=False, error="…")` for expected failures (bad request, not found) | Lets the service layer record `Failed` log entries without a crash |
| Raise `LockProviderUnavailableError` for network / timeout errors | Triggers retry logic in the service layer |
| Raise `LockProviderAuthError` for invalid credentials | Separates credential issues from logic errors in the operation log |

### Using `_redact` before storing responses

```python
raw = {"keyId": "ABC123", "access_token": "SENSITIVE", "lockId": "L1"}
return ProviderResult(
    success=True,
    external_key_id=raw["keyId"],
    raw_response=self._redact(raw),          # strips access_token → "***"
)
```

To redact provider-specific additional keys pass them as a second argument:

```python
self._redact(raw, keys=("cardSecret", "pinCode"))
```

---

## Step 2 — Create a credential settings DocType (if needed)

If the provider has secrets (API keys, client secrets, etc.) create a singleton
**DocType** to store them securely using Frappe's encrypted Password field type.

Example structure for `ACME Lock Settings`:

| Field | Type | Notes |
|-------|------|-------|
| `api_key` | Password | Encrypted at rest by Frappe |
| `environment` | Select | Dev / Production |
| `base_url` | Data | Optional override |

Read the secret in your provider with:

```python
import frappe

api_key = frappe.utils.password.get_decrypted_password(
    "ACME Lock Settings", "ACME Lock Settings", "api_key"
)
```

> **Never** read secrets from `connection_config` — that field is visible in the
> UI to Hotel Managers.  `connection_config` is for non-sensitive configuration
> (base URL, timeout, environment flags).

Alternatively, store secrets in `site_config.json` and read them with:

```python
import frappe
api_key = frappe.conf.get("acme_api_key", "")
```

---

## Step 3 — Register the provider in Frappe

1. Open **Lock Provider** list in the Frappe desk (Rhocom Hotel module).
2. Create a new record:

| Field | Value |
|-------|-------|
| Provider Code | `acme` — lowercase, no spaces, unique |
| Provider Label | `ACME Smart Locks` |
| Is Enabled | ✓ |
| Is Default | Only if this should be the site-wide default |
| Environment | `Production` or `Dev` |
| Provider Class Path | `rhohotel.integrations.locks.acme_provider.AcmeLockProvider` |
| Timeout (seconds) | `30` (recommended) |
| Retry Count | `2` |
| Connection Config | `{"base_url": "https://api.acmelocks.example.com"}` |

3. Save.

---

## Step 4 — Map rooms to ACME locks

For each hotel room that has an ACME lock, create a **Room Lock Mapping** record:

| Field | Value |
|-------|-------|
| Room | `101` (Link to Hotel Room) |
| Provider | `acme` |
| Is Enabled | ✓ |
| External Lock ID | The lock's ID in the ACME system (e.g. `LOCK-00234`) |
| Lock Alias | Optional human-readable name |

The `External Lock ID` is passed to the provider as `context.external_lock_id`
on every operation — **always use this value to identify the lock**, never
derive it from the room number.

---

## Step 5 — Write tests

Create `rhohotel/tests/test_acme_provider.py`. Use the Mock provider's test
structure as a template (`rhohotel/tests/test_lock_integration.py`).

Key points:

- Import the provider **without** Frappe by using `MagicMock` for `provider_doc`:

```python
from unittest.mock import MagicMock, patch
import json

def _make_doc(config=None):
    doc = MagicMock()
    doc.connection_config = json.dumps(config or {})
    doc.provider_code = "acme"
    doc.timeout_seconds = 10
    doc.retry_count = 1
    return doc
```

- Mock HTTP calls with `unittest.mock.patch` on `requests.request`.
- Test the failure path by making the mock raise `requests.exceptions.ConnectionError`.
- Verify `raw_response` never contains sensitive strings.

---

## Step 6 — Run a health check

Once the provider is registered and credentials are configured, run a health
check from the Frappe console to verify connectivity:

```python
bench --site rhotel console

from rhohotel.integrations.locks.service import provider_health_check
result = provider_health_check("acme")
print(result)
```

Or call the whitelisted API from the browser (requires Hotel Manager role):

```
POST /api/method/rhohotel.rhocom_hotel.api.lock_api.provider_health_check
     {"provider_code": "acme"}
```

---

## Reference: `KeyContext` fields

| Field | Type | Description |
|-------|------|-------------|
| `check_in_name` | `str` | Frappe name of the `Hotel Room Check In` document |
| `room_number` | `str` | Hotel room number (for display/logging only) |
| `external_lock_id` | `str` | Lock's ID in the provider system (from Room Lock Mapping) |
| `guest_name` | `str` | Full guest name (for card label / audit trail) |
| `valid_from` | `str` | ISO datetime — key becomes valid from this time |
| `valid_until` | `str` | ISO datetime — key expires at this time |
| `canonical_reservation` | `str \| None` | Frappe name of the linked `Hotel Reservation` |
| `extra` | `dict` | Provider-specific extras injected by the service layer |

## Reference: `ProviderResult` fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | `True` if the operation completed successfully |
| `external_key_id` | `str \| None` | Key/card ID in the provider system; **required** on issue/reissue |
| `provider_request_id` | `str \| None` | Provider-side transaction or request ID (for support tickets) |
| `raw_response` | `dict \| None` | Redacted full response stored in the operation log |
| `error` | `str \| None` | Human-readable error message when `success=False` |
| `provider_data` | `dict` | Structured extra data (battery level, card UID, etc.) |

## Reference: exception types

| Exception | When to raise |
|-----------|--------------|
| `LockProviderAuthError` | Invalid or missing credentials |
| `LockProviderMappingError` | Room is not mapped (raised by registry, not providers) |
| `LockProviderRequestError` | API rejected the request (bad parameters, business rule) |
| `LockProviderUnavailableError` | Network error, timeout, unexpected HTTP error |

---

## Existing providers for reference

| Provider | Code | Class Path | Notes |
|----------|------|------------|-------|
| Mock | `mock` | `rhohotel.integrations.locks.mock_provider.MockLockProvider` | Testing/demo only |
| TT Hotel / TTLock | `tt_hotel` | `rhohotel.integrations.locks.tt_hotel_provider.TTHotelProvider` | OAuth2; EU endpoint |
