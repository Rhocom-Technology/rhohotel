"""
Tests for rhohotel.rhocom_hotel.api.maintenance_request

Covers:
  - get_request_dashboard   – stat aggregation, correct key set
  - get_request_list        – filter building, pagination, display-name enrichment,
                              search path, location display logic
  - get_maintenance_request – happy path, not-found throw, linked task + technician name
  - create_maintenance_request – field mapping, default values, error path,
                                  JSON string arg, location_type routing
  - approve_request         – happy path, already-approved guard, missing technician
                              guard, missing witness guard, same-person guard, error path
  - reject_request          – happy path, already-rejected guard, error path
  - update_maintenance_request – field update, approved-guard, status-guard,
                                  JSON string arg, error path
  - complete_maintenance_request – idempotent on already-completed, sets status + date,
                                    error path
  - retry_task_creation     – not-approved guard, already-has-task guard, happy path,
                               missing technician guard, same-person guard
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Minimal frappe stub — installed before the module is imported
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
    frappe_stub.ValidationError = type("ValidationError", (Exception,), {})
    frappe_stub.get_all = lambda *args, **kwargs: []
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub.new_doc = lambda *args, **kwargs: MagicMock()
    frappe_stub.log_error = lambda *args, **kwargs: None
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.session = types.SimpleNamespace(user="Administrator")
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
    doc = MagicMock()
    for k, v in kwargs.items():
        setattr(doc, k, v)
    return doc


# ---------------------------------------------------------------------------
# get_request_dashboard
# ---------------------------------------------------------------------------

class TestGetRequestDashboard(unittest.TestCase):

    def test_returns_all_required_keys(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=0)]),
        ):
            result = mr.get_request_dashboard()

        required = {
            "pending", "completed", "cancelled", "total",
            "urgent_pending", "approved_pending", "resolved_this_week",
        }
        self.assertTrue(required.issubset(result.keys()))

    def test_resolved_this_week_from_sql(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=9)]),
        ):
            result = mr.get_request_dashboard()

        self.assertEqual(result["resolved_this_week"], 9)

    def test_resolved_this_week_defaults_to_zero_on_empty_sql(self):
        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "sql", return_value=[]),
        ):
            result = mr.get_request_dashboard()

        self.assertEqual(result["resolved_this_week"], 0)

    def test_counts_forwarded_correctly(self):
        counts = {"pending": 3, "completed": 7, "cancelled": 1,
                  "urgent": 2, "approved_pending": 4, "total": 0}

        def fake_count(doctype, filters=None):
            f = filters or {}
            if not f:
                return 11        # total (no filters)
            if f.get("status") == "Pending" and "priority" not in f and "approved" not in f:
                return counts["pending"]
            if f.get("status") == "Completed":
                return counts["completed"]
            if f.get("status") == "Cancelled":
                return counts["cancelled"]
            if f.get("priority"):
                return counts["urgent"]
            if f.get("approved") == "Approved":
                return counts["approved_pending"]
            return 0

        with (
            patch.object(mr, "get_first_day_of_week", return_value="2026-04-27"),
            patch.object(mr.frappe.db, "count", side_effect=fake_count),
            patch.object(mr.frappe.db, "sql", return_value=[DotDict(cnt=5)]),
        ):
            result = mr.get_request_dashboard()

        self.assertEqual(result["pending"], 3)
        self.assertEqual(result["completed"], 7)
        self.assertEqual(result["cancelled"], 1)
        self.assertEqual(result["total"], 11)


# ---------------------------------------------------------------------------
# get_request_list
# ---------------------------------------------------------------------------

class TestGetRequestList(unittest.TestCase):

    def _base_request(self, **kwargs):
        base = dict(
            name="MR-001", room="HR-101", location_type="Room",
            location=None, asset_location=None, asset="ASS-001",
            issue_type="Electrical", priority="High", status="Pending",
            reported_by="EMP-001", requesting_department=None,
            reported_at="2026-05-01", witness_employee=None,
            witness_department=None, approved="Pending",
            approved_by=None, approved_on=None,
            assigned_technician=None, task=None, completion_date=None,
        )
        base.update(kwargs)
        return DotDict(base)

    def test_filters_applied_from_parameters(self):
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

    def test_invalid_page_defaults_to_1(self):
        with (
            patch.object(mr.frappe, "get_all", return_value=[]),
            patch.object(mr.frappe.db, "count", return_value=0),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_request_list(page="bad", page_size="also-bad")

        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 25)

    def test_room_number_and_reporter_name_resolved(self):
        req = self._base_request()

        def fake_get_value(doctype, key, field, *args, **kwargs):
            if doctype == "Hotel Room":
                return "101"
            if doctype == "Employee":
                return "John Doe"
            return None

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_request_list()

        row = result["requests"][0]
        self.assertEqual(row["room_number"], "101")
        self.assertEqual(row["reported_by_name"], "John Doe")

    def test_location_display_for_room_type(self):
        req = self._base_request(location_type="Room", room="HR-101")

        def fake_get_value(doctype, key, field, *args, **kwargs):
            if doctype == "Hotel Room":
                return "101"
            return None

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_request_list()

        self.assertEqual(result["requests"][0]["location_display"], "101")

    def test_location_display_for_other_location(self):
        req = self._base_request(location_type="Other Location", room=None, location="Lobby")

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_request_list()

        self.assertEqual(result["requests"][0]["location_display"], "Lobby")

    def test_technician_name_resolved(self):
        req = self._base_request(assigned_technician="TECH-001")

        def fake_get_value(doctype, key, field, *args, **kwargs):
            if doctype == "Maintenance Technician":
                return "Ali Musa"
            return None

        with (
            patch.object(mr.frappe, "get_all", return_value=[req]),
            patch.object(mr.frappe.db, "count", return_value=1),
            patch.object(mr.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = mr.get_request_list()

        self.assertEqual(result["requests"][0]["technician_name"], "Ali Musa")

    def test_search_path_uses_sql(self):
        captured = {}

        def fake_sql(query, params, as_dict=False):
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
            name="MR-001", room="HR-101", location_type="Room",
            asset_location="", location="", asset="",
            issue_type="Plumbing", priority="Medium",
            status="Pending", reported_by="EMP-001",
            reported_at=None, completion_date=None,
            issue_description="Leaking pipe",
            approved="Pending", approved_by="", approved_on=None,
            assigned_technician="", witness_employee="",
            witness_department="", requesting_department="",
            task="", image_1="", image_2="", image_3="",
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
            "name", "location_type", "room", "room_number",
            "asset_location", "location", "issue_type", "priority", "status",
            "reported_by", "reported_by_name", "reported_at",
            "requesting_department", "witness_employee", "witness_employee_name",
            "witness_department", "approved", "approved_by", "approved_on",
            "assigned_technician", "technician_name",
            "task", "linked_task", "task_technician_name",
            "completion_date", "issue_description", "asset",
            "image_1", "image_2", "image_3",
        }
        self.assertTrue(required.issubset(result.keys()))

    def test_linked_task_resolved(self):
        doc = self._make_req_doc(task="MT-001")
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
        self.assertEqual(result["task_technician_name"], "Ali Musa")

    def test_no_linked_task_returns_none(self):
        doc = self._make_req_doc(task="")

        with (
            patch.object(mr.frappe.db, "exists", return_value=True),
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.get_maintenance_request("MR-001")

        self.assertIsNone(result["linked_task"])
        self.assertIsNone(result["task_technician_name"])


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
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.create_maintenance_request({
                "location_type": "Room",
                "room": "HR-101",
                "issue_type": "Electrical",
                "priority": "High",
                "reported_by": "EMP-001",
                "issue_description": "Faulty switch",
            })

        self.assertEqual(doc.room, "HR-101")
        self.assertEqual(doc.issue_type, "Electrical")
        self.assertEqual(doc.priority, "High")
        self.assertEqual(doc.status, "Pending")
        self.assertTrue(result["success"])
        self.assertEqual(result["request_name"], "MR-NEW-001")

    def test_default_priority_is_medium(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            mr.create_maintenance_request({})

        self.assertEqual(doc.priority, "Medium")
        self.assertEqual(doc.status, "Pending")

    def test_location_type_room_sets_room_clears_others(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            mr.create_maintenance_request({
                "location_type": "Room",
                "room": "HR-202",
                "asset_location": "should-be-ignored",
                "location": "should-be-ignored",
            })

        self.assertEqual(doc.room, "HR-202")
        self.assertIsNone(doc.asset_location)
        self.assertIsNone(doc.location)

    def test_location_type_asset_location_sets_asset_location(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            mr.create_maintenance_request({
                "location_type": "Asset Location",
                "asset_location": "Boiler Room",
            })

        self.assertIsNone(doc.room)
        self.assertEqual(doc.asset_location, "Boiler Room")

    def test_accepts_json_string(self):
        import json
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "new_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
            patch.object(mr.frappe.db, "get_value", return_value=None),
        ):
            result = mr.create_maintenance_request(
                json.dumps({"location_type": "Room", "room": "HR-200", "priority": "Low"})
            )

        self.assertEqual(doc.room, "HR-200")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "new_doc", side_effect=Exception("DB failure")),
            patch.object(mr.frappe, "log_error"),
            patch.object(mr.frappe.db, "rollback"),
        ):
            result = mr.create_maintenance_request({})

        self.assertFalse(result["success"])
        self.assertIn("DB failure", result["error"])


# ---------------------------------------------------------------------------
# approve_request
# ---------------------------------------------------------------------------

class TestApproveRequest(unittest.TestCase):

    def _make_doc(self, approved="Pending", assigned_technician="TECH-001",
                  witness_employee="EMP-002"):
        doc = MagicMock()
        doc.approved = approved
        doc.assigned_technician = assigned_technician
        doc.witness_employee = witness_employee
        return doc

    def test_happy_path_sets_approved_and_saves(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="EMP-999"),  # different employee
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.approve_request("MR-001")

        self.assertTrue(result["success"])
        self.assertEqual(doc.approved, "Approved")
        doc.save.assert_called_once()

    def test_blocks_when_already_approved(self):
        doc = self._make_doc(approved="Approved")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("already approved", result["error"])

    def test_blocks_when_no_technician(self):
        doc = self._make_doc(assigned_technician=None)

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("technician", result["error"].lower())

    def test_blocks_when_no_witness(self):
        doc = self._make_doc(witness_employee=None)

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Witness", result["error"])

    def test_blocks_when_technician_is_same_as_witness(self):
        doc = self._make_doc(assigned_technician="TECH-001", witness_employee="EMP-001")

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            # technician's employee == witness
            patch.object(mr.frappe.db, "get_value", return_value="EMP-001"),
        ):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("cannot", result["error"].lower())

    def test_assigns_technician_from_parameter(self):
        doc = self._make_doc(assigned_technician=None)

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="EMP-999"),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.approve_request("MR-001", assigned_technician="TECH-NEW")

        self.assertEqual(doc.assigned_technician, "TECH-NEW")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Permission denied")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.approve_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Permission denied", result["error"])


# ---------------------------------------------------------------------------
# reject_request
# ---------------------------------------------------------------------------

class TestRejectRequest(unittest.TestCase):

    def test_happy_path_sets_rejected(self):
        doc = MagicMock()
        doc.approved = "Pending"

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.reject_request("MR-001")

        self.assertTrue(result["success"])
        self.assertEqual(doc.approved, "Rejected")
        doc.save.assert_called_once()

    def test_blocks_when_already_rejected(self):
        doc = MagicMock()
        doc.approved = "Rejected"

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.reject_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("already rejected", result["error"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Crash")),
            patch.object(mr.frappe, "log_error"),
        ):
            result = mr.reject_request("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Crash", result["error"])


# ---------------------------------------------------------------------------
# update_maintenance_request
# ---------------------------------------------------------------------------

class TestUpdateMaintenanceRequest(unittest.TestCase):

    def _make_doc(self, approved="Pending", status="Pending"):
        doc = MagicMock()
        doc.approved = approved
        doc.status = status
        doc.room = "HR-101"
        doc.asset = None
        doc.issue_type = "Electrical"
        doc.priority = "Medium"
        doc.reported_by = "EMP-001"
        doc.issue_description = "Old description"
        doc.reported_at = None
        doc.location_type = "Room"
        doc.asset_location = None
        doc.location = None
        doc.witness_employee = None
        doc.image_1 = None
        doc.image_2 = None
        doc.image_3 = None
        return doc

    def test_blocks_update_when_approved(self):
        doc = self._make_doc(approved="Approved")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.update_maintenance_request("MR-001", {"issue_type": "Plumbing"})

        self.assertFalse(result["success"])
        self.assertIn("approved", result["error"].lower())

    def test_blocks_update_when_rejected(self):
        doc = self._make_doc(approved="Rejected")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.update_maintenance_request("MR-001", {"issue_type": "Plumbing"})

        self.assertFalse(result["success"])
        self.assertIn("approved", result["error"].lower())

    def test_blocks_update_when_status_not_pending(self):
        doc = self._make_doc(status="Completed")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.update_maintenance_request("MR-001", {"issue_type": "Plumbing"})

        self.assertFalse(result["success"])
        self.assertIn("Completed", result["error"])

    def test_editable_fields_are_updated(self):
        doc = self._make_doc()

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value=None),
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
            patch.object(mr.frappe.db, "get_value", return_value=None),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.update_maintenance_request("MR-001", json.dumps({"priority": "Low"}))

        self.assertEqual(doc.priority, "Low")
        self.assertTrue(result["success"])

    def test_returns_error_on_exception(self):
        with (
            patch.object(mr.frappe, "get_doc", side_effect=Exception("Lock error")),
            patch.object(mr.frappe, "log_error"),
            patch.object(mr.frappe.db, "rollback"),
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

    def test_sets_status_and_completion_date(self):
        doc = MagicMock()
        doc.status = "Pending"

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "commit"),
            patch.object(mr, "now_datetime", return_value="2026-05-01 15:00:00"),
        ):
            result = mr.complete_maintenance_request("MR-001")

        calls = [c[0] for c in doc.db_set.call_args_list]
        self.assertIn(("status", "Completed"), calls)
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
# retry_task_creation
# ---------------------------------------------------------------------------

class TestRetryTaskCreation(unittest.TestCase):

    def _make_doc(self, approved="Approved", task=None,
                  assigned_technician="TECH-001", witness_employee="EMP-002"):
        doc = MagicMock()
        doc.approved = approved
        doc.task = task
        doc.assigned_technician = assigned_technician
        doc.witness_employee = witness_employee
        return doc

    def test_blocks_when_not_approved(self):
        doc = self._make_doc(approved="Pending")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Approved", result["error"])

    def test_blocks_when_task_already_exists(self):
        doc = self._make_doc(task="MT-EXISTING")

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("already exists", result["error"])

    def test_blocks_when_no_technician(self):
        doc = self._make_doc(assigned_technician=None)

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("technician", result["error"].lower())

    def test_blocks_when_no_witness(self):
        doc = self._make_doc(witness_employee=None)

        with patch.object(mr.frappe, "get_doc", return_value=doc):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("Witness", result["error"])

    def test_blocks_when_technician_same_as_witness(self):
        doc = self._make_doc(assigned_technician="TECH-001", witness_employee="EMP-001")

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="EMP-001"),
        ):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("cannot", result["error"].lower())

    def test_happy_path_saves_and_returns_task(self):
        doc = self._make_doc()

        # After reload, task is set
        def fake_reload():
            doc.task = "MT-NEW"

        doc.reload = fake_reload

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="EMP-999"),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.retry_task_creation("MR-001")

        self.assertTrue(result["success"])
        self.assertEqual(result["task"], "MT-NEW")

    def test_returns_error_when_task_still_not_created(self):
        doc = self._make_doc()

        # reload does not set task
        doc.reload = lambda: None
        doc.task = None

        with (
            patch.object(mr.frappe, "get_doc", return_value=doc),
            patch.object(mr.frappe.db, "get_value", return_value="EMP-999"),
            patch.object(mr.frappe.db, "commit"),
        ):
            result = mr.retry_task_creation("MR-001")

        self.assertFalse(result["success"])
        self.assertIn("could not be created", result["error"].lower())


if __name__ == "__main__":
    unittest.main()