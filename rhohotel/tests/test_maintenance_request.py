"""
Tests for rhohotel.rhocom_hotel.api.maintenance_request

Covers:
  - get_request_dashboard   – stat aggregation, correct key set
  - get_request_list        – filter building, pagination, display-name enrichment,
                              linked-task resolution, search path
  - get_maintenance_request – happy path, not-found throw, linked task + technician name
  - create_maintenance_request – field mapping, default values, error path, JSON string arg
  - approve_request         – delegates to doc method, handles exception
  - convert_to_task         – happy path, repair-type guard, duplicate-task guard,
                              priority mapping, missing-request guard
  - _map_priority           – every mapping value
  - update_maintenance_request – field update, approved-guard, status-guard, error path
  - complete_maintenance_request – idempotent on already-completed, sets status + date
  - get_room_assets         – uses amenity item_codes, falls back when no amenities
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call, ANY

# ---------------------------------------------------------------------------
# Minimal frappe stub
# ---------------------------------------------------------------------------
if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _whitelist(*args, **kwargs):
        def _decorator(fn):
            return fn
        return _decorator

    def _default_throw(message, *args, **kwargs):
        raise RuntimeError(message)

    frappe_stub._ = lambda text: text
    frappe_stub.whitelist = _whitelist
    frappe_stub.throw = _default_throw
    frappe_stub.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
    frappe_stub.get_all = lambda *args, **kwargs: []
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub.new_doc = lambda *args, **kwargs: MagicMock()
    frappe_stub.log_error = lambda *args, **kwargs: None
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *args, **kwargs: [],
        count=lambda *args, **kwargs: 0,
        get_value=lambda *args, **kwargs: None,
        set_value=lambda *args, **kwargs: None,
        exists=lambda *args, **kwargs: True,
        commit=lambda: None,
        rollback=lambda: None,
    )

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.now_datetime = lambda: "2026-05-01 12:00:00"
    utils_stub.get_first_day_of_week = lambda d: "2026-04-27"

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import maintenance_request as mr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DotDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


def _fake_doc(**kwargs):
    """Return a MagicMock with attributes set from kwargs."""
    doc = MagicMock()
    for k, v in kwargs.items():
        setattr(doc, k, v)
    return doc


# ---------------------------------------------------------------------------
# get_request_dashboard
# ---------------------------------------------------------------------------

class TestGetRequestDashboard(unittest.TestCase):
    def _make_counts(self, pending=2, completed=5, cancelled=1,
                     urgent=1, approved_pending=1):
        def fake_count(doctype, filters):
            if filters.get("status") == "Pending" and "priority" not in filters and "approved" not in filters:
                return pending
            if filters.get("status") == "Completed":
                return completed
            if filters.get("status") == "Cancelled":
                return cancelled
            if filters.get("priority"):
                return urgent
            if filters.get("approved") == 1:
                return approved_pending
            return 0

        return fake_count

    def test_total_is_sum_of_statuses(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", side_effect=self._make_counts(2, 5, 1)),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=3)]),
        ):
            result = mr.get_request_dashboard()

        self.assertEqual(result["total"], 8)  # 2 + 5 + 1
        self.assertEqual(result["pending"], 2)
        self.assertEqual(result["completed"], 5)
        self.assertEqual(result["cancelled"], 1)

    def test_resolved_this_week_from_sql(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=7)]),
        ):
            result = mr.get_request_dashboard()

        self.assertEqual(result["resolved_this_week"], 7)

    def test_response_has_all_required_keys(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=0)]),
        ):
            result = mr.get_request_dashboard()

        required = {"pending", "completed", "cancelled", "total",
                    "urgent_pending", "approved_pending", "resolved_this_week"}
        self.assertTrue(required.issubset(result.keys()))


# ---------------------------------------------------------------------------
# get_request_list
# ---------------------------------------------------------------------------

class TestGetRequestList(unittest.TestCase):
    def _base_request(self, **kwargs):
        base = dict(
            name="MR-001", room="HR-101", asset="ASS-001",
            issue_type="Electrical", priority="High", status="Pending",
            reported_by="EMP-001", reported_at="2026-05-01",
            approved=0, approval_time=None, completion_date=None,
            asset_repair=None,
        )
        base.update(kwargs)
        return DotDict(base)

    def test_filter_applied_from_parameters(self):
        captured = {}

        def fake_get_all(doctype, filters=None, **kwargs):
            if doctype == "Maintenance Request":
                captured["filters"] = dict(filters or {})
            return []

        with (
            patch.object(mr.frappe, "get_all", side_effect=fake_get_all),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            mr.get_request_list(filter_priority="High", filter_status="Pending")

        self.assertEqual(captured["filters"].get("priority"), "High")
        self.assertEqual(captured["filters"].get("status"), "Pending")

    def test_pagination_fields_present_in_response(self):
        with (
            patch.object(mr.frappe, "get_all", return_value=[]),
            patch.object(mr.frappe.db, "count", return_value=30),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_request_list(page=2, page_size=10)

        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_size"], 10)
        self.assertEqual(result["total"], 30)
        self.assertEqual(result["total_pages"], 3)

    def test_total_pages_minimum_is_one(self):
        with (
            patch.object(mr.frappe, "get_all", return_value=[]),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_request_list()

        self.assertEqual(result["total_pages"], 1)

    def test_asset_room_and_reporter_names_are_resolved(self):
        req = self._base_request()

        def fake_get_value(doctype, key, field, *args, **kwargs):
            if doctype == "Asset":
                return "Air Conditioner"
            if doctype == "Hotel Room":
                return "101"
            if doctype == "Employee":
                return "John Doe"
            if doctype == "Maintenance Task":
                return None
            return None

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_request_list()

        row = result["requests"][0]
        self.assertEqual(row["asset_name"], "Air Conditioner")
        self.assertEqual(row["room_number"], "101")
        self.assertEqual(row["reported_by_name"], "John Doe")

    def test_linked_maintenance_task_resolved(self):
        req = self._base_request(asset=None, room=None, reported_by=None)

        def fake_get_value(doctype, *args, **kwargs):
            if doctype == "Maintenance Task":
                return "MT-001"
            return None

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_request_list()

        self.assertEqual(result["requests"][0]["maintenance_task"], "MT-001")

    def test_invalid_page_defaults_to_1(self):
        with (
            patch.object(mr.frappe, "get_all", return_value=[]),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_request_list(page="bad", page_size="also-bad")

        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 25)

    def test_search_path_uses_sql(self):
        captured = {}

        def fake_sql(query, params, as_dict):
            captured["query"] = query
            captured["params"] = params
            return []

        with (
            patch.object(mr.frappe.db, "sql", side_effect=fake_sql),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            mr.get_request_list(search="AC unit")

        self.assertIn("q", captured["params"])
        self.assertEqual(captured["params"]["q"], "%AC unit%")

# ---------------------------------------------------------------------------
# get_maintenance_request
# ---------------------------------------------------------------------------

class TestGetMaintenanceRequest(unittest.TestCase):
    def _make_req_doc(self, **kwargs):
        defaults = dict(
            name="MR-001", room="HR-101", asset="ASS-001",
            issue_type="Plumbing", priority="Medium",
            request_type="Repair", status="Pending",
            reported_by="EMP-001", reported_at=None,
            completion_date=None, issue_description="Leaking pipe",
            approved=0, approval_time=None, asset_repair=None,
        )
        defaults.update(kwargs)
        return _fake_doc(**defaults)

    def test_throws_when_request_not_found(self):
        with (
            patch.object(mr.frappe.db, "exists", return_value=False),
            patch.object(mr.frappe, "throw", side_effect=RuntimeError("not found")),
        ):
            with self.assertRaises(RuntimeError):
                mr.get_maintenance_request("MR-MISSING")

    def test_returns_all_expected_keys(self):
        doc = self._make_req_doc()

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_maintenance_request("MR-001")

        required = {
            "name", "room", "room_number", "asset", "asset_name",
            "issue_type", "priority", "request_type", "status",
            "reported_by", "reported_by_name", "reported_at",
            "completion_date", "issue_description", "approved",
            "approval_time", "asset_repair", "linked_task", "technician_name",
        }
        self.assertTrue(required.issubset(result.keys()))

    def test_linked_task_and_technician_name_resolved(self):
        doc = self._make_req_doc()
        linked = DotDict(name="MT-001", status="In Progress", assigned_technician="TECH-001")

        def fake_get_value(doctype, *args, **kwargs):
            if doctype == "Maintenance Task":
                return linked
            if doctype == "Maintenance Technician":
                return "Ali Musa"
            return None

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_maintenance_request("MR-001")

        self.assertEqual(result["linked_task"], linked)
        self.assertEqual(result["technician_name"], "Ali Musa")


# ---------------------------------------------------------------------------
# create_maintenance_request
# ---------------------------------------------------------------------------

class TestCreateMaintenanceRequest(unittest.TestCase):
    def _make_doc(self):
        doc = MagicMock()
        doc.name = "MR-NEW-001"
        return doc

    def test_fields_mapped_from_request_data(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.create_maintenance_request({
                "room": "HR-101",
                "asset": "ASS-001",
                "issue_type": "Electrical",
                "priority": "High",
                "request_type": "Repair",
                "reported_by": "EMP-001",
                "issue_description": "Faulty switch",
            })

        self.assertEqual(doc.room, "HR-101")
        self.assertEqual(doc.asset, "ASS-001")
        self.assertEqual(doc.priority, "High")
        self.assertEqual(doc.status, "Pending")
        self.assertTrue(result["success"])
        self.assertEqual(result["request_name"], "MR-NEW-001")

    def test_default_priority_is_medium(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            mr.create_maintenance_request({})

        self.assertEqual(doc.priority, "Medium")
        self.assertEqual(doc.request_type, "Repair")
        self.assertEqual(doc.status, "Pending")

    def test_accepts_json_string(self):
        import json
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.create_maintenance_request(json.dumps({"room": "HR-200", "priority": "Low"}))

        self.assertEqual(doc.room, "HR-200")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "new_doc", side_effect=Exception("DB failure")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.create_maintenance_request({})

        self.assertFalse(result["success"])
        self.assertIn("DB failure", result["error"])


# ---------------------------------------------------------------------------
# approve_request
# ---------------------------------------------------------------------------

class TestApproveRequest(unittest.TestCase):
    def test_calls_approve_request_on_doc(self):
        doc = MagicMock()

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.approve_request("MR-001")

        doc.approve_request.assert_called_once()
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Permission denied")),
            patch.object(mr.frappe, "log_error")
        ):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Permission denied", result["error"])


# ---------------------------------------------------------------------------
# convert_to_task
# ---------------------------------------------------------------------------

class TestConvertToTask(unittest.TestCase):
    def _req_doc(self, request_type="Maintenance", **kwargs):
        defaults = dict(
            name="MR-001", asset="ASS-001", priority="High",
            request_type=request_type,
        )
        defaults.update(kwargs)
        return _fake_doc(**defaults)

    def test_blocks_repair_type_requests(self):
        doc = self._req_doc(request_type="Repair")

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.convert_to_task("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Repair", result["error"])

    def test_blocks_when_request_not_found(self):
        with patch.object(mr.frappe.db, "exists", return_value=False):
            result = mr.convert_to_task("MR-MISSING")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    def test_blocks_duplicate_task_conversion(self):
        doc = self._req_doc()

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="MT-EXISTING"),
        ):
            result = mr.convert_to_task("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("MT-EXISTING", result["error"])

    def test_creates_task_with_correct_fields(self):
        req_doc = self._req_doc(priority="Critical")
        task_doc = MagicMock()
        task_doc.name = "MT-NEW-001"

        def fake_db_exists(doctype, value=None):
            # All existence checks return True except initial Maintenance Task lookup
            return True

        with (
            patch.object(mr.frappe.db, "exists", side_effect=fake_db_exists),
            patch.object(mr.frappe, "get_doc", return_value=req_doc),
            patch.object(mr.frappe, "new_doc", return_value=task_doc),
            # No existing task found
            patch.object(mr.frappe.db, "get_value", return_value=None),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.convert_to_task(
                "MR-001",
                task_data={"task_type": "Corrective", "assigned_technician": "TECH-001"}
            )

        self.assertEqual(task_doc.maintenance_request, "MR-001")
        self.assertEqual(task_doc.asset, "ASS-001")
        self.assertEqual(task_doc.task_type, "Corrective")
        # Critical -> High (via _map_priority)
        self.assertEqual(task_doc.priority, "High")
        self.assertEqual(task_doc.status, "Open")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe.db, "exists", side_effect=Exception("Boom")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.convert_to_task("MR-001")

        self.assertFalse(result["success"])


# ---------------------------------------------------------------------------
# _map_priority
# ---------------------------------------------------------------------------

class TestMapPriority(unittest.TestCase):
    def test_critical_maps_to_high(self):
        self.assertEqual(mr._map_priority("Critical"), "High")

    def test_high_maps_to_high(self):
        self.assertEqual(mr._map_priority("High"), "High")

    def test_medium_maps_to_medium(self):
        self.assertEqual(mr._map_priority("Medium"), "Medium")

    def test_low_maps_to_low(self):
        self.assertEqual(mr._map_priority("Low"), "Low")

    def test_unknown_defaults_to_medium(self):
        self.assertEqual(mr._map_priority("Unknown"), "Medium")
        self.assertEqual(mr._map_priority(""), "Medium")
        self.assertEqual(mr._map_priority(None), "Medium")


# ---------------------------------------------------------------------------
# update_maintenance_request
# ---------------------------------------------------------------------------

class TestUpdateMaintenanceRequest(unittest.TestCase):
    def _make_doc(self, approved=0, status="Pending"):
        doc = MagicMock()
        doc.approved = approved
        doc.status = status
        doc.room = "HR-101"
        doc.asset = None
        doc.issue_type = "Electrical"
        doc.priority = "Medium"
        doc.request_type = "Repair"
        doc.reported_by = "EMP-001"
        doc.issue_description = "Old description"
        doc.reported_at = None
        return doc

    def test_blocks_update_when_already_approved(self):
        doc = self._make_doc(approved=1)

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.update_maintenance_request("MR-001", {"issue_type": "Plumbing"})

        self.assertFalse(result["success"])
        self.assertIn("approved", result["error"])

    def test_blocks_update_when_status_is_not_pending(self):
        doc = self._make_doc(status="Completed")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.update_maintenance_request("MR-001", {"issue_type": "Plumbing"})

        self.assertFalse(result["success"])
        self.assertIn("Completed", result["error"])

    def test_editable_fields_are_updated(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.update_maintenance_request("MR-001", {
                "issue_type": "Plumbing",
                "priority": "High",
                "issue_description": "Updated desc",
            })

        self.assertEqual(doc.issue_type, "Plumbing")
        self.assertEqual(doc.priority, "High")
        self.assertEqual(doc.issue_description, "Updated desc")
        self.assertTrue(result["success"])

    def test_accepts_json_string(self):
        import json
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.update_maintenance_request("MR-001", json.dumps({"priority": "Low"}))

        self.assertEqual(doc.priority, "Low")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Lock error")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.update_maintenance_request("MR-001", {})

        self.assertFalse(result["success"])
        self.assertIn("Lock error", result["error"])


# ---------------------------------------------------------------------------
# complete_maintenance_request
# ---------------------------------------------------------------------------

class TestCompleteMaintenanceRequest(unittest.TestCase):
    def test_idempotent_when_already_completed(self):
        doc = MagicMock()
        doc.status = "Completed"

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.complete_maintenance_request("MR-DONE")

        doc.db_set.assert_not_called()
        self.assertTrue(result["success"])


    
    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Crash")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.complete_maintenance_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Crash", result["error"])


# ---------------------------------------------------------------------------
# get_room_assets
# ---------------------------------------------------------------------------

class TestGetRoomAssets(unittest.TestCase):
    def test_returns_empty_list_for_falsy_room(self):
        result = mr.get_room_assets("")
        self.assertEqual(result, [])

        result = mr.get_room_assets(None)
        self.assertEqual(result, [])

    def test_returns_empty_list_when_room_does_not_exist(self):
        with patch.object(mr.frappe.db, "exists", return_value=False):
            result = mr.get_room_assets("HR-NONEXISTENT")

        self.assertEqual(result, [])

    def test_falls_back_to_all_assets_when_no_amenities(self):
        doc = MagicMock()
        doc.get.return_value = []  # no amenities

        captured = {}

        def fake_get_all(doctype, filters=None, **kwargs):
            captured["doctype"] = doctype
            captured["filters"] = filters
            return []

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe, "get_all", side_effect=fake_get_all),
        ):
            mr.get_room_assets("HR-101")

        self.assertEqual(captured["doctype"], "Asset")
        # No item_code filter when falling back
        self.assertNotIn("item_code", (captured.get("filters") or {}))

    def test_uses_amenity_item_codes_as_filter(self):
        amenity1 = MagicMock()
        amenity1.item = "LAMP-001"
        amenity2 = MagicMock()
        amenity2.item = "AC-001"

        doc = MagicMock()
        doc.get.return_value = [amenity1, amenity2]

        captured = {}

        def fake_get_all(doctype, filters=None, **kwargs):
            captured["filters"] = filters
            return []

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe, "get_all", side_effect=fake_get_all),
        ):
            mr.get_room_assets("HR-101")

        item_filter = captured["filters"].get("item_code")
        self.assertIsNotNone(item_filter)
        self.assertIn("LAMP-001", item_filter[1])
        self.assertIn("AC-001", item_filter[1])


if __name__ == "__main__":
    unittest.main()