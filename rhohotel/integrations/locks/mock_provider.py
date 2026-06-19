# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt
"""
Mock Lock Provider — deterministic simulation for testing and demos.

Does not make any network calls.  All operations succeed by default.
Use MOCK_FORCE_FAIL environment variable or set force_fail=1 in
connection_config JSON to simulate failures.

Provider Code: mock
Class Path:    rhohotel.integrations.locks.mock_provider.MockLockProvider
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

from rhohotel.integrations.locks.base import (
    KeyContext,
    LockProvider,
    ProviderResult,
)


class MockLockProvider(LockProvider):
    """
    Simulates a smart-lock provider for local development and automated tests.

    Configuration (via connection_config JSON):
        force_fail (bool): Return failure for all operations.
        fail_operations (list[str]): Fail only listed operation types,
            e.g. ["issue_key", "cancel_key"].

    Example connection_config:
        {"force_fail": false, "fail_operations": []}
    """

    def __init__(self, provider_doc: Any) -> None:
        super().__init__(provider_doc)
        config_str = getattr(provider_doc, "connection_config", None) or "{}"
        try:
            self._config: dict = json.loads(config_str) if isinstance(config_str, str) else dict(config_str)
        except (json.JSONDecodeError, TypeError):
            self._config = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _should_fail(self, operation: str) -> bool:
        if os.environ.get("MOCK_LOCK_FORCE_FAIL", "").lower() in ("1", "true", "yes"):
            return True
        if self._config.get("force_fail"):
            return True
        fail_ops = self._config.get("fail_operations") or []
        return operation in fail_ops

    @staticmethod
    def _mock_key_id(context: KeyContext) -> str:
        """Generate a deterministic mock key ID from context."""
        raw = f"{context.check_in_name}:{context.external_lock_id}:{context.valid_from}"
        return "MOCK-" + hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    @staticmethod
    def _mock_response(operation: str, **kwargs) -> dict:
        return {"mock": True, "operation": operation, **kwargs}

    # ------------------------------------------------------------------
    # LockProvider implementation
    # ------------------------------------------------------------------

    def issue_key(self, context: KeyContext) -> ProviderResult:
        if self._should_fail("issue_key"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("issue_key", reason="forced_failure"),
                error="Mock provider: forced failure on issue_key.",
            )
        key_id = self._mock_key_id(context)
        return ProviderResult(
            success=True,
            external_key_id=key_id,
            provider_request_id=f"MOCK-REQ-ISSUE-{key_id}",
            raw_response=self._mock_response(
                "issue_key",
                key_id=key_id,
                lock_id=context.external_lock_id,
                guest=context.guest_name,
                valid_from=context.valid_from,
                valid_until=context.valid_until,
            ),
            provider_data={"status": "issued"},
        )

    def reissue_key(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        if self._should_fail("reissue_key"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("reissue_key", reason="forced_failure"),
                error="Mock provider: forced failure on reissue_key.",
            )
        new_key_id = self._mock_key_id(context) + "-R"
        return ProviderResult(
            success=True,
            external_key_id=new_key_id,
            provider_request_id=f"MOCK-REQ-REISSUE-{new_key_id}",
            raw_response=self._mock_response(
                "reissue_key",
                old_key_id=existing_key_id,
                new_key_id=new_key_id,
                lock_id=context.external_lock_id,
            ),
            provider_data={"status": "reissued"},
        )

    def update_key_validity(self, context: KeyContext, existing_key_id: str) -> ProviderResult:
        if self._should_fail("update_key_validity"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("update_key_validity", reason="forced_failure"),
                error="Mock provider: forced failure on update_key_validity.",
            )
        return ProviderResult(
            success=True,
            external_key_id=existing_key_id,
            provider_request_id=f"MOCK-REQ-UPDATE-{existing_key_id}",
            raw_response=self._mock_response(
                "update_key_validity",
                key_id=existing_key_id,
                new_valid_until=context.valid_until,
            ),
            provider_data={"status": "updated"},
        )

    def cancel_key(
        self,
        key_id: str,
        room_mapping: Any,
        context: Optional[KeyContext] = None,
    ) -> ProviderResult:
        if self._should_fail("cancel_key"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("cancel_key", reason="forced_failure"),
                error="Mock provider: forced failure on cancel_key.",
            )
        lock_id = room_mapping.get("external_lock_id") if isinstance(room_mapping, dict) else getattr(room_mapping, "external_lock_id", "")
        return ProviderResult(
            success=True,
            external_key_id=key_id,
            provider_request_id=f"MOCK-REQ-CANCEL-{key_id}",
            raw_response=self._mock_response(
                "cancel_key",
                key_id=key_id,
                lock_id=lock_id,
            ),
            provider_data={"status": "cancelled"},
        )

    def transfer_key(
        self,
        context: KeyContext,
        old_room_mapping: Any,
        new_room_mapping: Any,
        existing_key_id: str,
    ) -> ProviderResult:
        if self._should_fail("transfer_key"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("transfer_key", reason="forced_failure"),
                error="Mock provider: forced failure on transfer_key.",
            )
        new_key_id = self._mock_key_id(context) + "-T"
        old_lock = old_room_mapping.get("external_lock_id") if isinstance(old_room_mapping, dict) else getattr(old_room_mapping, "external_lock_id", "")
        new_lock = new_room_mapping.get("external_lock_id") if isinstance(new_room_mapping, dict) else getattr(new_room_mapping, "external_lock_id", "")
        return ProviderResult(
            success=True,
            external_key_id=new_key_id,
            provider_request_id=f"MOCK-REQ-TRANSFER-{new_key_id}",
            raw_response=self._mock_response(
                "transfer_key",
                old_lock=old_lock,
                new_lock=new_lock,
                old_key_id=existing_key_id,
                new_key_id=new_key_id,
            ),
            provider_data={"status": "transferred"},
        )

    def get_lock_status(self, room_mapping: Any) -> ProviderResult:
        if self._should_fail("get_lock_status"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("get_lock_status", reason="forced_failure"),
                error="Mock provider: forced failure on get_lock_status.",
            )
        lock_id = room_mapping.get("external_lock_id") if isinstance(room_mapping, dict) else getattr(room_mapping, "external_lock_id", "")
        return ProviderResult(
            success=True,
            raw_response=self._mock_response(
                "get_lock_status",
                lock_id=lock_id,
                online=True,
                battery_level=85,
            ),
            provider_data={"online": True, "battery_level": 85, "locked": True},
        )

    def health_check(self) -> ProviderResult:
        if self._should_fail("health_check"):
            return ProviderResult(
                success=False,
                raw_response=self._mock_response("health_check", reason="forced_failure"),
                error="Mock provider: forced failure on health_check.",
            )
        return ProviderResult(
            success=True,
            raw_response=self._mock_response("health_check", status="ok"),
            provider_data={"status": "ok", "provider": "mock"},
        )
