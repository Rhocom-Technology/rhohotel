"""
Tests for the IPTV Integration API.
rhohotel/tests/test_iptv_api.py

These tests run without a live Frappe/database instance by stubbing the
frappe module — matching the pattern used in test_checkin_api.py and
test_guest_api.py.

Test coverage
-------------
Authentication
  - Missing API key -> Unauthorized
  - Wrong API key -> Unauthorized
  - Correct API key passes through
  - frappe.request is None -> Unauthorized (not a crash)
  - Decryption failure -> Unauthorized (not a crash)

get_guest_by_room
  - Missing room_number
  - Empty room_number
  - room_number too long (>20 chars)
  - No active guest found
  - Successful lookup with datetime objects
  - Successful lookup with string datetimes (DB string format)
  - Response contains no PII fields

get_guest_folio
  - Missing room_number
  - No active guest found
  - Successful folio retrieval

get_room_service_menu
  - Unauthorized when no key
  - All items returned
  - Filtered by category
  - Empty categories list on success

place_room_service_order
  - GET request rejected
  - Missing room_number
  - items is a dict (not a list) -> rejected before emptiness check
  - Empty items list
  - Too many items (>30)
  - Zero qty rejected
  - Invalid item_code rejected
  - No active guest rejected
  - special_request HTML is stripped
  - Successful order creation
"""

import sys
import types
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Frappe stub -- must be set up before importing the module under test
# ---------------------------------------------------------------------------
if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _whitelist(*args, **kwargs):
        def _decorator(fn):
            return fn
        return _decorator

    frappe_stub._ = lambda text: text
    frappe_stub.whitelist = _whitelist
    frappe_stub.throw = lambda msg, *a, **kw: (_ for _ in ()).throw(RuntimeError(msg))
    frappe_stub.log_error = lambda *a, **kw: None
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.request = MagicMock()
    frappe_stub.request.method = "POST"
    frappe_stub.request.data = b""
    frappe_stub.request.headers = {}
    frappe_stub.local = types.SimpleNamespace(form_dict={})
    frappe_stub.DoesNotExistError = RuntimeError
    frappe_stub.db = types.SimpleNamespace(
        get_value=lambda *a, **kw: None,
        get_single_value=lambda *a, **kw: None,
        get_default=lambda *a, **kw: "NGN",
        sql=lambda *a, **kw: [],
        exists=lambda *a, **kw: False,
        commit=lambda: None,
        rollback=lambda: None,
    )

    _fake_doc = types.SimpleNamespace(
        name="NEW-ORDER-001",
        status="Confirmed",
        total_amount=7000.0,
        creation="2026-06-17 12:00:00",
    )
    _fake_doc.append = lambda table, row: None
    _fake_doc.insert = lambda *a, **kw: None

    frappe_stub.new_doc = lambda *a, **kw: _fake_doc
    frappe_stub.get_doc = lambda *a, **kw: _fake_doc

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.flt = lambda v, p=None: round(float(v or 0), p) if p is not None else float(v or 0)
    utils_stub.cstr = lambda v: "" if v is None else str(v)
    utils_stub.now_datetime = lambda: datetime(2026, 6, 17, 12, 0, 0)
    utils_stub.get_datetime = lambda v: v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
    utils_stub.strip_html_tags = lambda v: v  # no-op by default; overridden in XSS test

    password_stub = types.ModuleType("frappe.utils.password")
    # Default: returns None -> auth fails unless patched per-test
    password_stub.get_decrypted_password = lambda *a, **kw: None

    # Connect module attributes so that frappe.utils.password works as an
    # attribute chain (not just sys.modules lookups).
    utils_stub.password = password_stub
    frappe_stub.utils = utils_stub

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub
    sys.modules["frappe.utils.password"] = password_stub
    sys.modules["frappe.model"] = types.ModuleType("frappe.model")
    document_stub = types.ModuleType("frappe.model.document")
    document_stub.Document = object
    sys.modules["frappe.model.document"] = document_stub

import frappe       # noqa: E402
import frappe.utils # noqa: E402

from rhohotel.rhocom_hotel.api import iptv as iptv_api  # noqa: E402


# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

VALID_KEY = "test-iptv-secret-key-abc123"

ACTIVE_BOOKING = {
    "name": "HRCI-0001",
    "guest": "GUEST-0001",
    "room_number": "101",
    "room_type": "DELUXE-01",
    "check_in_datetime": datetime(2026, 6, 15, 14, 0, 0),
    "expected_check_out_datetime": datetime(2026, 6, 20, 12, 0, 0),
    "canonical_reservation": "RES-0001",
    "total_charges": 150000.0,
    "total_outstanding_amount": 90000.0,
    "customer": "CUST-0001",
}

ACTIVE_BOOKING_STRING_DATES = {
    **ACTIVE_BOOKING,
    "check_in_datetime": "2026-06-15 14:00:00",
    "expected_check_out_datetime": "2026-06-20 12:00:00",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(headers=None, body=None, method="POST"):
    import json as _json
    req = frappe.request
    req.method = method
    req.headers = headers or {}
    req.data = _json.dumps(body or {}).encode() if body else b""
    frappe.local.form_dict = {}


def _auth_headers():
    return {"X-IPTV-API-Key": VALID_KEY}


def _patch_auth(valid=True):
    """
    Patch get_decrypted_password, which is what _validate_iptv_api_key
    now calls (after issue-10 fix removed the get_single_value fallback).
    """
    return_val = VALID_KEY if valid else None
    return patch.object(
        sys.modules["frappe.utils.password"],
        "get_decrypted_password",
        return_value=return_val,
    )


# ---------------------------------------------------------------------------
# Tests: Authentication
# ---------------------------------------------------------------------------

class TestIPTVAuth(unittest.TestCase):

    def test_missing_api_key_returns_unauthorized(self):
        _make_request(headers={}, body={"room_number": "101"})
        with _patch_auth(valid=True):
            result = iptv_api.get_guest_by_room()
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unauthorized")

    def test_wrong_api_key_returns_unauthorized(self):
        _make_request(headers={"X-IPTV-API-Key": "wrong-key"}, body={"room_number": "101"})
        with _patch_auth(valid=True):
            result = iptv_api.get_guest_by_room()
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unauthorized")

    def test_correct_api_key_passes_auth(self):
        _make_request(headers=_auth_headers(), body={"room_number": "101"})
        with _patch_auth(valid=True), \
             patch.object(iptv_api, "_get_active_booking_by_room", return_value=None):
            result = iptv_api.get_guest_by_room()
        self.assertFalse(result["success"])
        self.assertNotEqual(result["error"], "Unauthorized")

    def test_frappe_request_none_returns_unauthorized(self):
        """Issue 9: frappe.request being None must not crash."""
        original = frappe.request
        frappe.request = None
        try:
            with _patch_auth(valid=True):
                result = iptv_api.get_guest_by_room()
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "Unauthorized")
        finally:
            frappe.request = original

    def test_decryption_failure_returns_unauthorized(self):
        """Issue 10: decryption exception must return Unauthorized, not crash."""
        _make_request(headers=_auth_headers(), body={"room_number": "101"})
        with patch.object(
            sys.modules["frappe.utils.password"],
            "get_decrypted_password",
            side_effect=Exception("vault unavailable"),
        ):
            result = iptv_api.get_guest_by_room()
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unauthorized")


# ---------------------------------------------------------------------------
# Tests: get_guest_by_room
# ---------------------------------------------------------------------------

class TestGetGuestByRoom(unittest.TestCase):

    def _call(self, body, headers=None):
        _make_request(headers=headers or _auth_headers(), body=body)
        with _patch_auth(valid=True):
            return iptv_api.get_guest_by_room()

    def test_missing_room_number(self):
        result = self._call({})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is required")

    def test_empty_room_number(self):
        result = self._call({"room_number": ""})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is required")

    def test_room_number_too_long_rejected(self):
        """Issue 8: room_number > 20 chars is rejected."""
        result = self._call({"room_number": "A" * 21})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is too long")

    def test_no_active_guest(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=None):
            result = self._call({"room_number": "999"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No active guest found for this room")

    def test_successful_guest_lookup_with_datetime_objects(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(iptv_api, "_get_guest_name", return_value="John Smith"), \
             patch.object(iptv_api, "_get_room_type_name", return_value="Deluxe Room"):
            result = self._call({"room_number": "101"})
        self.assertTrue(result["success"])
        data = result["data"]
        self.assertEqual(data["guest_name"], "John Smith")
        self.assertEqual(data["check_in_date"], "2026-06-15")
        self.assertEqual(data["check_out_date"], "2026-06-20")
        self.assertEqual(data["booking_id"], "RES-0001")

    def test_successful_guest_lookup_with_string_datetimes(self):
        """Issue 3: DB may return strings instead of datetime objects."""
        with patch.object(iptv_api, "_get_active_booking_by_room",
                          return_value=ACTIVE_BOOKING_STRING_DATES), \
             patch.object(iptv_api, "_get_guest_name", return_value="Jane Doe"), \
             patch.object(iptv_api, "_get_room_type_name", return_value="Suite"):
            result = self._call({"room_number": "101"})
        self.assertTrue(result["success"])
        data = result["data"]
        self.assertEqual(data["check_in_date"], "2026-06-15")
        self.assertEqual(data["check_out_date"], "2026-06-20")

    def test_response_contains_no_pii(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(iptv_api, "_get_guest_name", return_value="Jane Doe"), \
             patch.object(iptv_api, "_get_room_type_name", return_value="Suite"):
            result = self._call({"room_number": "101"})
        data = result.get("data", {})
        for banned in ("phone", "email", "id_number", "passport", "address", "customer"):
            self.assertNotIn(
                banned, data, f"PII field '{banned}' must not appear in IPTV response"
            )


# ---------------------------------------------------------------------------
# Tests: get_guest_folio
# ---------------------------------------------------------------------------

class TestGetGuestFolio(unittest.TestCase):

    def _call(self, body):
        _make_request(headers=_auth_headers(), body=body)
        with _patch_auth(valid=True):
            return iptv_api.get_guest_folio()

    def test_missing_room_number(self):
        result = self._call({})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is required")

    def test_no_active_guest(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=None):
            result = self._call({"room_number": "101"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No active guest found for this room")

    def test_successful_folio_retrieval(self):
        folio = {
            "currency": "NGN",
            "accommodation_charges": 150000.0,
            "restaurant_charges": 25000.0,
            "laundry_charges": 0.0,
            "other_charges": 0.0,
            "total_charges": 175000.0,
            "total_paid": 85000.0,
            "outstanding_balance": 90000.0,
        }
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(iptv_api, "_get_guest_name", return_value="John Smith"), \
             patch.object(iptv_api, "_get_guest_folio_summary", return_value=folio):
            result = self._call({"room_number": "101"})
        self.assertTrue(result["success"])
        data = result["data"]
        self.assertEqual(data["currency"], "NGN")
        self.assertEqual(data["accommodation_charges"], 150000.0)
        self.assertEqual(data["outstanding_balance"], 90000.0)
        self.assertEqual(data["guest_name"], "John Smith")


# ---------------------------------------------------------------------------
# Tests: get_room_service_menu
# ---------------------------------------------------------------------------

class TestGetRoomServiceMenu(unittest.TestCase):

    def _call(self, body=None, method="GET"):
        _make_request(headers=_auth_headers(), body=body or {}, method=method)
        with _patch_auth(valid=True):
            return iptv_api.get_room_service_menu()

    def test_unauthorized_no_key(self):
        _make_request(headers={}, body={})
        with _patch_auth(valid=True):
            result = iptv_api.get_room_service_menu()
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unauthorized")

    def test_successful_menu_retrieval_all(self):
        fake_categories = [
            {
                "category": "Food",
                "items": [{"item_code": "MI-001", "item_name": "Jollof Rice",
                           "description": "", "price": 3000.0, "available": True, "image": ""}],
            }
        ]
        with patch.object(iptv_api, "_get_menu_items", return_value=fake_categories), \
             patch.object(frappe.db, "get_default", return_value="NGN"):
            result = self._call()
        self.assertTrue(result["success"])
        data = result["data"]
        self.assertEqual(data["currency"], "NGN")
        self.assertEqual(len(data["categories"]), 1)
        self.assertEqual(data["categories"][0]["category"], "Food")

    def test_successful_menu_retrieval_with_category_filter(self):
        with patch.object(iptv_api, "_get_menu_items", return_value=[]) as mock_get, \
             patch.object(frappe.db, "get_default", return_value="NGN"):
            result = self._call(body={"category": "Drinks"})
        mock_get.assert_called_once_with(category="Drinks")
        self.assertTrue(result["success"])

    def test_empty_menu_returns_success(self):
        with patch.object(iptv_api, "_get_menu_items", return_value=[]), \
             patch.object(frappe.db, "get_default", return_value="NGN"):
            result = self._call()
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["categories"], [])


# ---------------------------------------------------------------------------
# Tests: place_room_service_order
# ---------------------------------------------------------------------------

class TestPlaceRoomServiceOrder(unittest.TestCase):

    def _call(self, body, method="POST"):
        _make_request(headers=_auth_headers(), body=body, method=method)
        with _patch_auth(valid=True):
            return iptv_api.place_room_service_order()

    def test_get_request_rejected(self):
        result = self._call({}, method="GET")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "This endpoint requires POST")

    def test_missing_room_number(self):
        result = self._call({"items": [{"item_code": "MI-001", "qty": 1}]})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is required")

    def test_room_number_too_long_rejected(self):
        """Issue 8: room_number > 20 chars is rejected."""
        result = self._call({"room_number": "R" * 21, "items": [{"item_code": "MI", "qty": 1}]})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "room_number is too long")

    def test_items_as_dict_rejected_before_emptiness_check(self):
        """
        Issue 6: isinstance check must happen before 'not items_raw'.
        A non-empty dict is truthy, so it previously bypassed the empty check.
        """
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING):
            result = self._call(
                {"room_number": "101", "items": {"item_code": "MI-001", "qty": 1}}
            )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "items must be a list")

    def test_empty_items_list(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING):
            result = self._call({"room_number": "101", "items": []})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "items list is required and cannot be empty")

    def test_too_many_items_rejected(self):
        """Issue 8: more than _MAX_ORDER_ITEMS is rejected."""
        items = [
            {"item_code": f"MI-{i}", "qty": 1}
            for i in range(iptv_api._MAX_ORDER_ITEMS + 1)
        ]
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING):
            result = self._call({"room_number": "101", "items": items})
        self.assertFalse(result["success"])
        self.assertIn("exceed", result["error"])

    def test_zero_qty_rejected(self):
        fake_mi = {"name": "MENU-ITEM-00001", "item_name": "X", "rate": 100.0}
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(frappe.db, "get_value", return_value=fake_mi):
            result = self._call({
                "room_number": "101",
                "items": [{"item_code": "MENU-ITEM-00001", "qty": 0}],
            })
        self.assertFalse(result["success"])
        self.assertIn("qty must be greater than 0", result["error"])

    def test_invalid_item_code_rejected(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(frappe.db, "get_value", return_value=None):
            result = self._call({
                "room_number": "101",
                "items": [{"item_code": "DOES-NOT-EXIST", "qty": 1}],
            })
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    def test_no_active_guest_rejected(self):
        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=None):
            result = self._call({
                "room_number": "101",
                "items": [{"item_code": "MENU-ITEM-00001", "qty": 1}],
            })
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No active guest found for this room")

    def test_special_request_html_is_stripped(self):
        """Issue 5: HTML tags in special_request must be stripped before storage."""
        captured_comments = []

        def _capture_get_doc(payload, *a, **kw):
            if isinstance(payload, dict) and payload.get("doctype") == "Comment":
                captured_comments.append(payload.get("content", ""))
            return types.SimpleNamespace(insert=lambda *a, **kw: None)

        fake_order = types.SimpleNamespace(
            name="RES-ORD-XSS",
            status="Confirmed",
            total_amount=5000.0,
            creation="2026-06-17 12:00:00",
        )
        fake_order.append = lambda *a, **kw: None
        fake_order.insert = lambda *a, **kw: None

        def _fake_strip(val):
            import re
            return re.sub(r"<[^>]+>", "", val)

        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(iptv_api, "_get_guest_name", return_value="Guest"), \
             patch.object(frappe.db, "get_value",
                          return_value={"name": "MI-001", "item_name": "X", "rate": 100.0}), \
             patch("frappe.new_doc", return_value=fake_order), \
             patch("frappe.get_doc", side_effect=_capture_get_doc), \
             patch.object(frappe.db, "commit"), \
             patch.object(frappe.utils, "strip_html_tags", side_effect=_fake_strip):
            result = self._call({
                "room_number": "101",
                "items": [{"item_code": "MI-001", "qty": 1}],
                "special_request": '<script>alert("xss")</script>Please hurry',
            })

        self.assertTrue(result["success"])
        self.assertTrue(len(captured_comments) > 0, "Expected a comment to be created")
        stored = captured_comments[0]
        self.assertNotIn("<script>", stored)
        self.assertIn("Please hurry", stored)

    def test_successful_order_creation(self):
        fake_menu_item = {"name": "MENU-ITEM-00001", "item_name": "Chicken Sandwich", "rate": 5000.0}

        fake_order = types.SimpleNamespace(
            name="RES-ORD-00001",
            status="Confirmed",
            total_amount=10000.0,
            creation="2026-06-17 12:00:00",
        )
        rows_appended = []
        fake_order.append = lambda table, row: rows_appended.append(row)
        fake_order.insert = lambda *a, **kw: None

        with patch.object(iptv_api, "_get_active_booking_by_room", return_value=ACTIVE_BOOKING), \
             patch.object(iptv_api, "_get_guest_name", return_value="John Smith"), \
             patch.object(frappe.db, "get_value", return_value=fake_menu_item), \
             patch("frappe.new_doc", return_value=fake_order), \
             patch("frappe.get_doc",
                   return_value=types.SimpleNamespace(insert=lambda *a, **kw: None)), \
             patch.object(frappe.db, "commit", return_value=None):
            result = self._call({
                "room_number": "101",
                "items": [{"item_code": "MENU-ITEM-00001", "qty": 2}],
                "special_request": "Extra sauce",
            })

        self.assertTrue(result["success"], f"Expected success but got: {result}")
        data = result["data"]
        self.assertEqual(data["order_id"], "RES-ORD-00001")
        self.assertEqual(data["status"], "Confirmed")
        self.assertEqual(data["room_number"], "101")
        self.assertEqual(data["guest_name"], "John Smith")


if __name__ == "__main__":
    unittest.main()
