"""Tests for the smart lock integration framework.

These tests use the Mock provider so no real lock hardware is required.
Run with:  bench run-tests --app rhohotel --module rhohotel.tests.test_lock_integration
"""

import json
import unittest
from unittest.mock import MagicMock, patch


# Helper: a minimal room_mapping dict
_ROOM_MAPPING = {"external_lock_id": "LOCK-101", "is_enabled": 1}


class TestMockProvider(unittest.TestCase):
    """Unit tests for the Mock provider in isolation."""

    def _make_provider(self, config=None):
        from rhohotel.integrations.locks.mock_provider import MockLockProvider

        # MockLockProvider reads connection_config from the doc via
        # getattr(provider_doc, "connection_config", ...) so we use a dict-like object.
        doc = MagicMock()
        doc.connection_config = json.dumps(config) if config else "{}"
        doc.provider_code = "mock"
        doc.timeout_seconds = 10
        doc.retry_count = 1
        return MockLockProvider(doc)

    def _make_ctx(self):
        from rhohotel.integrations.locks.base import KeyContext

        return KeyContext(
            check_in_name="CHK-TEST-001",
            room_number="101",
            external_lock_id="LOCK-101",
            guest_name="Alice Test",
            valid_from="2024-06-01 14:00:00",
            valid_until="2024-06-05 12:00:00",
            canonical_reservation=None,
        )

    def test_issue_key_success(self):
        provider = self._make_provider()
        ctx = self._make_ctx()
        result = provider.issue_key(ctx)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.external_key_id)
        self.assertIsNone(result.error)

    def test_issue_key_returns_deterministic_id(self):
        provider = self._make_provider()
        ctx = self._make_ctx()
        r1 = provider.issue_key(ctx)
        r2 = provider.issue_key(ctx)
        self.assertEqual(r1.external_key_id, r2.external_key_id)

    def test_reissue_key_success(self):
        provider = self._make_provider()
        ctx = self._make_ctx()
        issued = provider.issue_key(ctx)
        result = provider.reissue_key(ctx, existing_key_id=issued.external_key_id)
        self.assertTrue(result.success)
        # Reissued key ID should differ from original
        self.assertNotEqual(issued.external_key_id, result.external_key_id)

    def test_cancel_key_success(self):
        provider = self._make_provider()
        ctx = self._make_ctx()
        issued = provider.issue_key(ctx)
        result = provider.cancel_key(
            key_id=issued.external_key_id,
            room_mapping=_ROOM_MAPPING,
            context=ctx,
        )
        self.assertTrue(result.success)

    def test_force_fail_config_returns_failure(self):
        provider = self._make_provider({"force_fail": True})
        ctx = self._make_ctx()
        result = provider.issue_key(ctx)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    def test_fail_specific_operation(self):
        provider = self._make_provider({"fail_operations": ["issue_key"]})
        ctx = self._make_ctx()
        # issue_key should fail
        result = provider.issue_key(ctx)
        self.assertFalse(result.success)
        # cancel_key should still work
        result2 = provider.cancel_key(
            key_id="some-id",
            room_mapping=_ROOM_MAPPING,
            context=ctx,
        )
        self.assertTrue(result2.success)

    def test_update_key_validity(self):
        provider = self._make_provider()
        ctx = self._make_ctx()
        issued = provider.issue_key(ctx)
        result = provider.update_key_validity(
            ctx,
            existing_key_id=issued.external_key_id,
        )
        self.assertTrue(result.success)

    def test_health_check(self):
        provider = self._make_provider()
        result = provider.health_check()
        self.assertTrue(result.success)

    def test_get_lock_status(self):
        provider = self._make_provider()
        result = provider.get_lock_status(room_mapping=_ROOM_MAPPING)
        self.assertTrue(result.success)
        self.assertEqual(result.provider_data.get("online"), True)


class TestRedact(unittest.TestCase):
    """Unit tests for the _redact instance method via MockLockProvider."""

    def _make_provider(self):
        from rhohotel.integrations.locks.mock_provider import MockLockProvider

        doc = MagicMock()
        doc.connection_config = "{}"
        doc.provider_code = "mock"
        doc.timeout_seconds = 10
        doc.retry_count = 1
        return MockLockProvider(doc)

    def test_strips_sensitive_keys(self):
        provider = self._make_provider()
        payload = {"client_id": "abc", "client_secret": "secret", "token": "tok", "data": "ok"}
        redacted = provider._redact(payload)
        self.assertEqual(redacted["client_secret"], "***")
        self.assertEqual(redacted["token"], "***")
        self.assertEqual(redacted["data"], "ok")

    def test_preserves_non_sensitive_keys(self):
        provider = self._make_provider()
        payload = {"room": "101", "guest": "Alice", "lock_id": "LOCK-1"}
        redacted = provider._redact(payload)
        self.assertEqual(redacted["room"], "101")
        self.assertEqual(redacted["guest"], "Alice")


class TestRegistryUnit(unittest.TestCase):
    """Unit tests for registry helpers (no DB required)."""

    def test_get_provider_for_unknown_code_raises(self):
        from rhohotel.integrations.locks.registry import get_provider

        with self.assertRaises(Exception):
            get_provider("__nonexistent_provider__")

    def test_mapping_error_propagates(self):
        from rhohotel.integrations.locks.base import LockProviderMappingError
        from rhohotel.integrations.locks.registry import get_room_mapping

        try:
            get_room_mapping("__nonexistent_room__")
        except LockProviderMappingError:
            return  # Correct behaviour
        except RuntimeError:
            # frappe.db is a Werkzeug LocalProxy; not bound outside bench run-tests
            self.skipTest("Frappe DB context unavailable; run via bench run-tests")
        else:
            self.fail("Expected LockProviderMappingError was not raised")


class TestServicePermissions(unittest.TestCase):
    """Ensure service-layer permission checks work."""

    def test_assert_roles_blocks_unauthorized(self):
        from rhohotel.integrations.locks.service import _assert_roles

        with patch("frappe.get_roles", return_value=["Employee"]):
            with self.assertRaises(Exception):
                _assert_roles()

    def test_assert_roles_allows_hotel_receptionist(self):
        from rhohotel.integrations.locks.service import _assert_roles

        with patch("frappe.get_roles", return_value=["Hotel Receptionist"]), \
             patch("frappe.session", MagicMock(user="test@example.com")):
            _assert_roles()  # should not raise

    def test_assert_roles_allows_system_manager(self):
        from rhohotel.integrations.locks.service import _assert_roles

        with patch("frappe.get_roles", return_value=["System Manager"]), \
             patch("frappe.session", MagicMock(user="test@example.com")):
            _assert_roles()  # should not raise


class TestProviderBaseClass(unittest.TestCase):
    """Ensure the ABC cannot be instantiated directly."""

    def test_cannot_instantiate_base(self):
        from rhohotel.integrations.locks.base import LockProvider

        with self.assertRaises(TypeError):
            LockProvider({})


class TestKeyContextDefaults(unittest.TestCase):
    """KeyContext dataclass defaults."""

    def test_extra_defaults_to_empty_dict(self):
        from rhohotel.integrations.locks.base import KeyContext

        ctx = KeyContext(
            check_in_name="x",
            room_number="101",
            external_lock_id="L1",
            guest_name="Bob",
            valid_from="2024-01-01 14:00:00",
            valid_until="2024-01-03 12:00:00",
        )
        self.assertIsInstance(ctx.extra, dict)

    def test_canonical_reservation_optional(self):
        from rhohotel.integrations.locks.base import KeyContext

        ctx = KeyContext(
            check_in_name="x",
            room_number="101",
            external_lock_id="L1",
            guest_name="Bob",
            valid_from="2024-01-01 14:00:00",
            valid_until="2024-01-03 12:00:00",
        )
        self.assertIsNone(ctx.canonical_reservation)


class TestMockProviderTransfer(unittest.TestCase):
    """transfer_key combines cancel + issue."""

    def _make_provider(self):
        from rhohotel.integrations.locks.mock_provider import MockLockProvider

        doc = MagicMock()
        doc.connection_config = "{}"
        doc.provider_code = "mock"
        doc.timeout_seconds = 10
        doc.retry_count = 1
        return MockLockProvider(doc)

    def test_transfer_key_success(self):
        from rhohotel.integrations.locks.base import KeyContext

        provider = self._make_provider()
        old_ctx = KeyContext(
            check_in_name="CHK-T1",
            room_number="101",
            external_lock_id="LOCK-101",
            guest_name="Alice",
            valid_from="2024-06-01 14:00:00",
            valid_until="2024-06-05 12:00:00",
        )
        new_ctx = KeyContext(
            check_in_name="CHK-T1",
            room_number="202",
            external_lock_id="LOCK-202",
            guest_name="Alice",
            valid_from="2024-06-01 14:00:00",
            valid_until="2024-06-05 12:00:00",
        )
        issued = provider.issue_key(old_ctx)
        result = provider.transfer_key(
            context=new_ctx,
            old_room_mapping={"external_lock_id": "LOCK-101"},
            new_room_mapping={"external_lock_id": "LOCK-202"},
            existing_key_id=issued.external_key_id,
        )
        self.assertTrue(result.success)
        self.assertIsNotNone(result.external_key_id)

    def test_transfer_key_force_fail(self):
        from rhohotel.integrations.locks.base import KeyContext
        from rhohotel.integrations.locks.mock_provider import MockLockProvider

        doc = MagicMock()
        doc.connection_config = json.dumps({"fail_operations": ["transfer_key"]})
        doc.provider_code = "mock"
        doc.timeout_seconds = 10
        doc.retry_count = 1
        provider = MockLockProvider(doc)
        ctx = KeyContext(
            check_in_name="CHK-T2",
            room_number="202",
            external_lock_id="LOCK-202",
            guest_name="Bob",
            valid_from="2024-06-01 14:00:00",
            valid_until="2024-06-05 12:00:00",
        )
        result = provider.transfer_key(
            context=ctx,
            old_room_mapping={"external_lock_id": "LOCK-101"},
            new_room_mapping={"external_lock_id": "LOCK-202"},
            existing_key_id="OLD-KEY",
        )
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
