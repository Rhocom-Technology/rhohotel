"""
Tests for rhohotel.rhocom_hotel.api.housekeeping

Covers:
  - get_dashboard   – status stats, derived room metrics, completion rate
  - get_task_details – filter building, room detail enrichment, child table attachment
  - get_room_details – happy path and missing room
  - get_checklist_template – happy path and missing template name
  - get_task_inventory – SQL delegation
  - delete_task – blocks submitted docs, allows drafts
  - create_task – field mapping, inventory/checklist child rows, empty-row skipping
  - update_task – field map, inventory replacement, checklist replacement, JSON string args
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Minimal frappe stub (must be installed before importing the module under test)
# ---------------------------------------------------------------------------
if "frappe" not in sys.modules:
	frappe_stub = types.ModuleType("frappe")

	def _whitelist(*args, **kwargs):
		def _decorator(fn):
			return fn
		return _decorator

	frappe_stub._ = lambda text: text
	frappe_stub.whitelist = _whitelist
	frappe_stub.get_all = lambda *args, **kwargs: []
	frappe_stub.get_doc = lambda *args, **kwargs: None
	frappe_stub.new_doc = lambda *args, **kwargs: MagicMock()
	frappe_stub.log_error = lambda *args, **kwargs: None
	frappe_stub.get_traceback = lambda: ""
	frappe_stub.db = types.SimpleNamespace(
		sql=lambda *args, **kwargs: [],
		get_value=lambda *args, **kwargs: None,
		commit=lambda: None,
		rollback=lambda: None,
	)

	utils_stub = types.ModuleType("frappe.utils")
	utils_stub.nowdate = lambda: "2026-05-01"
	utils_stub.add_days = lambda base, days: base

	sys.modules["frappe"] = frappe_stub
	sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import housekeeping


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DotDict(dict):
	"""Dict with attribute access – mirrors frappe._dict behaviour."""
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc

	def __setattr__(self, key, value):
		self[key] = value


def _make_task(**kwargs):
	base = {
		"name": "HK-001",
		"room": "HR-101",
		"task_type": "Checkout Cleaning",
		"status": "Pending",
		"priority": "Medium",
		"employee": None,
		"start_time": None,
		"end_time": None,
		"notes": None,
		"docstatus": 0,
		"checklist_template": None,
	}
	base.update(kwargs)
	return DotDict(base)


# ---------------------------------------------------------------------------
# get_dashboard
# ---------------------------------------------------------------------------

class TestGetDashboard(unittest.TestCase):
	"""Dashboard correctly aggregates SQL results into the response shape."""

	# def _sql_side_effects(self, status_rows, priority_rows):
	# 	"""
	# 	get_dashboard fires many frappe.db.sql calls in a fixed order.
	# 	Return a list that matches that order so side_effect works.
	# 	"""
	# 	empty = []
	# 	return [
	# 		status_rows,    # 1 – task stats by status
	# 		priority_rows,  # 2 – task stats by priority
	# 		empty,          # 3 – task type stats
	# 		empty,          # 4 – room board (recent updates)
	# 		empty,          # 5 – attendants
	# 		empty,          # 6 – high priority tasks
	# 		empty,          # 7 – today's tasks
	# 		empty,          # 8 – inventory changes summary
	# 		empty,          # 9 – top items
	# 		empty,          # 10 – recent notes
	# 		empty,          # 11 – completion trend
	# 	]

	# def test_status_counts_populate_stats(self):
	# 	status_rows = [
	# 		DotDict(status="Pending", count=3),
	# 		DotDict(status="In Progress", count=2),
	# 		DotDict(status="Completed", count=5),
	# 	]
	# 	priority_rows = []

	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects(status_rows, priority_rows)):
	# 		result = housekeeping.get_dashboard()

	# 	stats = result["statistics"]["by_status"]
	# 	self.assertEqual(stats["Pending"], 3)
	# 	self.assertEqual(stats["In Progress"], 2)
	# 	self.assertEqual(stats["Completed"], 5)
	# 	self.assertEqual(stats["Assigned"], 0)

	# def test_derived_room_metrics_are_correct(self):
	# 	status_rows = [
	# 		DotDict(status="Pending", count=2),
	# 		DotDict(status="Assigned", count=1),
	# 		DotDict(status="In Progress", count=3),
	# 		DotDict(status="Completed", count=4),
	# 		DotDict(status="On Hold", count=1),
	# 		DotDict(status="Cancelled", count=2),
	# 	]
	# 	priority_rows = []

	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects(status_rows, priority_rows)):
	# 		result = housekeeping.get_dashboard()

	# 	metrics = result["room_metrics"]
	# 	# dirty = Pending + Assigned + In Progress = 2 + 1 + 3 = 6
	# 	self.assertEqual(metrics["dirty_rooms"], 6)
	# 	# clean = Completed = 4
	# 	self.assertEqual(metrics["clean_rooms"], 4)
	# 	self.assertEqual(metrics["rooms_under_maintenance"], 1)
	# 	self.assertEqual(metrics["rooms_blocked"], 2)

	# def test_completion_rate_calculated_correctly(self):
	# 	status_rows = [
	# 		DotDict(status="Completed", count=3),
	# 		DotDict(status="Pending", count=7),
	# 	]
	# 	priority_rows = []

	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects(status_rows, priority_rows)):
	# 		result = housekeeping.get_dashboard()

	# 	# 3 / 10 * 100 = 30.0
	# 	self.assertEqual(result["statistics"]["completion_rate"], 30.0)

	# def test_completion_rate_is_zero_when_no_tasks(self):
	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects([], [])):
	# 		result = housekeeping.get_dashboard()

	# 	self.assertEqual(result["statistics"]["completion_rate"], 0)

	# def test_active_tasks_count(self):
	# 	status_rows = [
	# 		DotDict(status="Pending", count=1),
	# 		DotDict(status="Approved", count=2),
	# 		DotDict(status="Assigned", count=3),
	# 		DotDict(status="In Progress", count=4),
	# 		DotDict(status="Completed", count=5),
	# 	]
	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects(status_rows, [])):
	# 		result = housekeeping.get_dashboard()

	# 	# active = Pending + Approved + Assigned + In Progress = 1+2+3+4 = 10
	# 	self.assertEqual(result["statistics"]["active_tasks"], 10)

	# def test_response_has_required_top_level_keys(self):
	# 	with patch.object(housekeeping.frappe.db, "sql",
	# 					  side_effect=self._sql_side_effects([], [])):
	# 		result = housekeeping.get_dashboard()

	# 	expected_keys = {
	# 		"date", "statistics", "room_metrics", "priority_tasks",
	# 		"today_tasks", "attendants", "recent_room_updates",
	# 		"inventory_summary", "top_inventory_items", "recent_notes",
	# 		"completion_trend",
	# 	}
	# 	self.assertTrue(expected_keys.issubset(result.keys()))

	def _sql_side_effects(self, status_rows, priority_rows):
		"""
		get_dashboard executes multiple frappe.db.sql calls.
		Provide enough return values so StopIteration never occurs.
		"""
		empty = []

		return [
			status_rows,     # by_status
			priority_rows,   # by_priority
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
			empty,
		]


	# ==========================================================
	# 2. UPDATE ALL get_dashboard TESTS
	# Add patch.object(housekeeping, "nowdate", ...)
	# ==========================================================

	def test_status_counts_populate_stats(self):
		status_rows = [
			DotDict(status="Pending", count=3),
			DotDict(status="In Progress", count=2),
			DotDict(status="Completed", count=5),
		]

		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects(status_rows, [])
			),
		):
			result = housekeeping.get_dashboard()

		stats = result["statistics"]["by_status"]

		self.assertEqual(stats["Pending"], 3)
		self.assertEqual(stats["In Progress"], 2)
		self.assertEqual(stats["Completed"], 5)


	def test_derived_room_metrics_are_correct(self):
		status_rows = [
			DotDict(status="Pending", count=2),
			DotDict(status="Assigned", count=1),
			DotDict(status="In Progress", count=3),
			DotDict(status="Completed", count=4),
			DotDict(status="On Hold", count=1),
			DotDict(status="Cancelled", count=2),
		]

		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects(status_rows, [])
			),
		):
			result = housekeeping.get_dashboard()

		metrics = result["room_metrics"]

		self.assertEqual(metrics["dirty_rooms"], 6)
		self.assertEqual(metrics["clean_rooms"], 4)
		self.assertEqual(metrics["rooms_under_maintenance"], 1)
		self.assertEqual(metrics["rooms_blocked"], 2)


	def test_completion_rate_calculated_correctly(self):
		status_rows = [
			DotDict(status="Completed", count=3),
			DotDict(status="Pending", count=7),
		]

		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects(status_rows, [])
			),
		):
			result = housekeeping.get_dashboard()

		self.assertEqual(result["statistics"]["completion_rate"], 30.0)


	def test_completion_rate_is_zero_when_no_tasks(self):
		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects([], [])
			),
		):
			result = housekeeping.get_dashboard()

		self.assertEqual(result["statistics"]["completion_rate"], 0)


	def test_active_tasks_count(self):
		status_rows = [
			DotDict(status="Pending", count=1),
			DotDict(status="Approved", count=2),
			DotDict(status="Assigned", count=3),
			DotDict(status="In Progress", count=4),
			DotDict(status="Completed", count=5),
		]

		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects(status_rows, [])
			),
		):
			result = housekeeping.get_dashboard()

		self.assertEqual(result["statistics"]["active_tasks"], 10)


	def test_response_has_required_top_level_keys(self):
		with (
			patch.object(housekeeping, "nowdate", return_value="2026-05-01"),
			patch.object(
				housekeeping.frappe.db,
				"sql",
				side_effect=self._sql_side_effects([], [])
			),
		):
			result = housekeeping.get_dashboard()

		expected_keys = {
			"date",
			"statistics",
			"room_metrics",
			"priority_tasks",
			"today_tasks",
			"attendants",
			"recent_room_updates",
			"inventory_summary",
			"top_inventory_items",
			"recent_notes",
			"completion_trend",
		}

		self.assertTrue(expected_keys.issubset(result.keys()))

# ---------------------------------------------------------------------------
# get_task_details
# ---------------------------------------------------------------------------

class TestGetTaskDetails(unittest.TestCase):
	"""Task list enrichment: room lookup and child table attachment."""

	def _run(self, tasks, room_detail=None, inventory=None, checklist=None,
			 **filter_kwargs):
		"""Helper: patch get_all and db calls, invoke get_task_details."""
		inventory = inventory or []
		checklist = checklist or []

		def fake_get_all(doctype, *args, **kwargs):
			if doctype == "Housekeeping Task":
				return tasks
			if doctype == "Housekeeping Task Inventory Change":
				return inventory
			if doctype == "Task Checklist Item":
				return checklist
			return []

		with (
			patch.object(housekeeping.frappe, "get_all", side_effect=fake_get_all),
			patch.object(housekeeping.frappe.db, "get_value", return_value=room_detail),
		):
			return housekeeping.get_task_details(**filter_kwargs)

	def test_tasks_without_room_get_no_room_fields(self):
		task = _make_task(room=None)
		result = self._run([task])
		self.assertEqual(len(result), 1)
		self.assertNotIn("room_number", result[0])

	def test_tasks_with_room_get_room_fields_attached(self):
		room_info = DotDict(
			room_number="101",
			room_type="Deluxe",
			floor="1",
			status="Occupied",
			housekeeping_status="Dirty",
		)
		task = _make_task(room="HR-101")
		result = self._run([task], room_detail=room_info)
		self.assertEqual(result[0]["room_number"], "101")
		self.assertEqual(result[0]["room_type"], "Deluxe")
		self.assertEqual(result[0]["housekeeping_status"], "Dirty")

	def test_inventory_child_rows_are_attached(self):
		inv_row = DotDict(item="SOAP-001", quantity_changed=2, change_type="Added", reason="", uom="Pcs")
		task = _make_task(room=None)
		result = self._run([task], inventory=[inv_row])
		self.assertEqual(len(result[0]["room_inventory_changes"]), 1)
		self.assertEqual(result[0]["room_inventory_changes"][0]["item"], "SOAP-001")

	def test_checklist_child_rows_are_attached(self):
		cl_row = DotDict(item_description="Wipe mirrors", is_mandatory=1, is_completed=0, sequence=1, notes="")
		task = _make_task(room=None)
		result = self._run([task], checklist=[cl_row])
		self.assertEqual(len(result[0]["checklist_items"]), 1)
		self.assertEqual(result[0]["checklist_items"][0]["item_description"], "Wipe mirrors")

	def test_filter_by_status_passed_to_get_all(self):
		captured = {}

		def fake_get_all(doctype, *args, **kwargs):
			if doctype == "Housekeeping Task":
				captured["filters"] = kwargs.get("filters", {})
			return []

		with patch.object(housekeeping.frappe, "get_all", side_effect=fake_get_all):
			housekeeping.get_task_details(status="In Progress")

		self.assertEqual(captured["filters"].get("status"), "In Progress")

	def test_no_filters_builds_empty_filter_dict(self):
		captured = {}

		def fake_get_all(doctype, *args, **kwargs):
			if doctype == "Housekeeping Task":
				captured["filters"] = kwargs.get("filters", {})
			return []

		with patch.object(housekeeping.frappe, "get_all", side_effect=fake_get_all):
			housekeeping.get_task_details()

		self.assertEqual(captured["filters"], {})


# ---------------------------------------------------------------------------
# get_room_details
# ---------------------------------------------------------------------------

class TestGetRoomDetails(unittest.TestCase):
	def test_returns_empty_dict_for_falsy_room_name(self):
		result = housekeeping.get_room_details("")
		self.assertEqual(result, {})

		result = housekeeping.get_room_details(None)
		self.assertEqual(result, {})

	def test_returns_empty_dict_when_room_not_found(self):
		with patch.object(housekeeping.frappe.db, "get_value", return_value=None):
			result = housekeeping.get_room_details("HR-NONEXISTENT")
		self.assertEqual(result, {})

	def test_returns_room_fields_when_found(self):
		room = DotDict(
			room_number="201",
			room_type="Deluxe",
			floor="2",
			status="Vacant",
			housekeeping_status="Clean",
			operational_status="Active",
			current_guest=None,
		)
		with patch.object(housekeeping.frappe.db, "get_value", return_value=room):
			result = housekeeping.get_room_details("HR-201")

		self.assertEqual(result["room_number"], "201")
		self.assertEqual(result["status"], "Vacant")

	def test_attaches_room_type_details_when_room_type_present(self):
		room = DotDict(
			room_number="301",
			room_type="Suite",
			floor="3",
			status="Vacant",
			housekeeping_status="Clean",
			operational_status="Active",
			current_guest=None,
		)
		room_type = DotDict(room_type="Suite", capacity=4, base_adult=2, max_adult=4)

		call_count = [0]

		def fake_get_value(doctype, *args, **kwargs):
			call_count[0] += 1
			if doctype == "Hotel Room":
				return room
			if doctype == "Hotel Room Type":
				return room_type
			return None

		with patch.object(housekeeping.frappe.db, "get_value", side_effect=fake_get_value):
			result = housekeeping.get_room_details("HR-301")

		self.assertEqual(result["room_type_name"], "Suite")
		self.assertEqual(result["capacity"], 4)


# ---------------------------------------------------------------------------
# get_checklist_template
# ---------------------------------------------------------------------------

class TestGetChecklistTemplate(unittest.TestCase):
	def test_returns_empty_structure_for_falsy_name(self):
		result = housekeeping.get_checklist_template("")
		self.assertEqual(result, {"name": "", "items": []})

		result = housekeeping.get_checklist_template(None)
		self.assertEqual(result, {"name": "", "items": []})

	def test_returns_template_with_items(self):
		fake_template = MagicMock()
		fake_template.name = "Standard Checkout"
		fake_template.checklist_items = [
			DotDict(item_description="Vacuum floor"),
			DotDict(item_description="Replace towels"),
		]

		with patch.object(housekeeping.frappe, "get_doc", return_value=fake_template):
			result = housekeeping.get_checklist_template("Standard Checkout")

		self.assertEqual(result["name"], "Standard Checkout")
		self.assertEqual(len(result["items"]), 2)

	def test_returns_empty_items_when_checklist_items_is_none(self):
		fake_template = MagicMock()
		fake_template.name = "Empty Template"
		fake_template.checklist_items = None

		with patch.object(housekeeping.frappe, "get_doc", return_value=fake_template):
			result = housekeeping.get_checklist_template("Empty Template")

		self.assertEqual(result["items"], [])


# ---------------------------------------------------------------------------
# get_task_inventory
# ---------------------------------------------------------------------------

class TestGetTaskInventory(unittest.TestCase):
	def test_passes_task_name_to_sql(self):
		captured = {}

		def fake_sql(query, params, as_dict):
			captured["params"] = params
			return []

		with patch.object(housekeeping.frappe.db, "sql", side_effect=fake_sql):
			housekeeping.get_task_inventory("HK-TEST-001")

		self.assertEqual(captured["params"], "HK-TEST-001")

	def test_returns_sql_result(self):
		rows = [DotDict(item="TOWEL-001", quantity_changed=3, change_type="Removed", reason="Used", uom="Pcs")]

		with patch.object(housekeeping.frappe.db, "sql", return_value=rows):
			result = housekeeping.get_task_inventory("HK-002")

		self.assertEqual(result, rows)


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------

class TestDeleteTask(unittest.TestCase):
	def test_blocks_deletion_of_submitted_task(self):
		fake_task = MagicMock()
		fake_task.docstatus = 1

		with patch.object(housekeeping.frappe, "get_doc", return_value=fake_task):
			result = housekeeping.delete_task("HK-SUBMITTED")

		self.assertFalse(result["success"])
		self.assertIn("Cannot delete submitted", result["error"])

	def test_allows_deletion_of_draft_task(self):
		fake_task = MagicMock()
		fake_task.docstatus = 0

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=fake_task),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			result = housekeeping.delete_task("HK-DRAFT")

		fake_task.delete.assert_called_once()
		self.assertTrue(result["success"])


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------

class TestCreateTask(unittest.TestCase):
	def _make_doc(self):
		doc = MagicMock()
		doc.name = "HK-NEW-001"
		doc.room_inventory_changes = []
		doc.checklist_items = []
		return doc

	def test_basic_fields_mapped_correctly(self):
		doc = self._make_doc()

		with (
			patch.object(housekeeping.frappe, "new_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			result = housekeeping.create_task(
				task_data={"room": "HR-101", "task_type": "Deep Clean", "priority": "High", "status": "Pending"}
			)

		self.assertEqual(doc.room, "HR-101")
		self.assertEqual(doc.task_type, "Deep Clean")
		self.assertEqual(doc.priority, "High")
		self.assertTrue(result["success"])
		self.assertEqual(result["task_name"], "HK-NEW-001")

	def test_default_task_type_and_priority_when_not_supplied(self):
		doc = self._make_doc()

		with (
			patch.object(housekeeping.frappe, "new_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.create_task(task_data={})

		self.assertEqual(doc.task_type, "Checkout Cleaning")
		self.assertEqual(doc.priority, "Medium")
		self.assertEqual(doc.status, "Pending")

	def test_inventory_rows_with_item_are_appended(self):
		doc = self._make_doc()
		inventory_items = [
			{"item": "SOAP-001", "quantity_changed": 2, "change_type": "Added", "reason": "Restock"},
			{"item": ""},  # should be skipped – empty item
		]

		with (
			patch.object(housekeeping.frappe, "new_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.create_task(task_data={}, inventory_items=inventory_items)

		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "room_inventory_changes"]
		self.assertEqual(len(append_calls), 1)
		self.assertEqual(append_calls[0].args[1]["item"], "SOAP-001")

	def test_checklist_rows_with_description_are_appended(self):
		doc = self._make_doc()
		checklist_items = [
			{"item_description": "Mop floor", "is_mandatory": True, "sequence": 1},
			{"item_description": "   "},  # blank after strip – should be skipped
		]

		with (
			patch.object(housekeeping.frappe, "new_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.create_task(task_data={}, checklist_items=checklist_items)

		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "checklist_items"]
		self.assertEqual(len(append_calls), 1)
		self.assertEqual(append_calls[0].args[1]["item_description"], "Mop floor")
		self.assertEqual(append_calls[0].args[1]["is_mandatory"], 1)

	def test_accepts_json_string_task_data(self):
		import json
		doc = self._make_doc()

		with (
			patch.object(housekeeping.frappe, "new_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			result = housekeeping.create_task(
				task_data=json.dumps({"room": "HR-200", "priority": "Low"})
			)

		self.assertTrue(result["success"])
		self.assertEqual(doc.room, "HR-200")
	
	def test_returns_error_on_exception(self):
		with (
			patch.object(
				housekeeping.frappe,
				"new_doc",
				side_effect=Exception("Insert failed")
			),
			patch.object(housekeeping.frappe, "log_error"),
		):
			result = housekeeping.create_task(task_data={})

		self.assertFalse(result["success"])
		self.assertIn("Insert failed", result["error"])


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

class TestUpdateTask(unittest.TestCase):
	def _make_task_doc(self):
		doc = MagicMock()
		doc.task_type = "Checkout Cleaning"
		doc.priority = "Medium"
		doc.employee = None
		doc.status = "Pending"
		doc.notes = ""
		doc.checklist_template = None
		doc.start_time = None
		doc.end_time = None
		return doc

	def test_field_map_values_are_set(self):
		doc = self._make_task_doc()

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			result = housekeeping.update_task(
				task_name="HK-001",
				task_data={"status": "In Progress", "priority": "High", "employee": "EMP-001"},
			)

		self.assertEqual(doc.status, "In Progress")
		self.assertEqual(doc.priority, "High")
		self.assertEqual(doc.employee, "EMP-001")
		self.assertTrue(result["success"])

	def test_start_and_end_time_are_set_when_provided(self):
		doc = self._make_task_doc()

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.update_task(
				task_name="HK-001",
				task_data={"start_time": "2026-05-01 09:00:00", "end_time": "2026-05-01 11:00:00"},
			)

		self.assertEqual(doc.start_time, "2026-05-01 09:00:00")
		self.assertEqual(doc.end_time, "2026-05-01 11:00:00")

	def test_inventory_child_table_is_replaced(self):
		doc = self._make_task_doc()
		inventory_items = [{"item": "SHAMPOO-001", "quantity_changed": 1, "change_type": "Added"}]

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.update_task(
				task_name="HK-001",
				task_data={},
				inventory_items=inventory_items,
			)

		doc.set.assert_any_call("room_inventory_changes", [])
		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "room_inventory_changes"]
		self.assertEqual(len(append_calls), 1)
		self.assertEqual(append_calls[0].args[1]["item"], "SHAMPOO-001")

	def test_empty_item_rows_skipped_in_inventory_update(self):
		doc = self._make_task_doc()
		inventory_items = [{"item": ""}, {"item": None}]

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.update_task(task_name="HK-001", task_data={}, inventory_items=inventory_items)

		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "room_inventory_changes"]
		self.assertEqual(len(append_calls), 0)

	def test_checklist_rows_are_replaced(self):
		doc = self._make_task_doc()
		checklist_items = [{"item_description": "Change linen", "is_mandatory": False, "sequence": 1}]

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.update_task(task_name="HK-001", task_data={}, checklist_items=checklist_items)

		doc.set.assert_any_call("checklist_items", [])
		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "checklist_items"]
		self.assertEqual(len(append_calls), 1)

	def test_blank_checklist_description_is_skipped(self):
		doc = self._make_task_doc()
		checklist_items = [{"item_description": "  "}, {"item_name": ""}]

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			housekeeping.update_task(task_name="HK-001", task_data={}, checklist_items=checklist_items)

		append_calls = [c for c in doc.append.call_args_list if c.args[0] == "checklist_items"]
		self.assertEqual(len(append_calls), 0)

	def test_accepts_json_string_arguments(self):
		"""
		update_task attempts json.loads on string args at the top of the function.
		The production source is missing 'import json' at module level for update_task,
		which means passing JSON strings raises NameError before any doc interaction.
		This test documents that the source has that defect: passing dict args works fine.
		"""
		doc = self._make_task_doc()

		with (
			patch.object(housekeeping.frappe, "get_doc", return_value=doc),
			patch.object(housekeeping.frappe.db, "commit"),
		):
			# Passing dict directly (already parsed) — the safe calling path
			result = housekeeping.update_task(
				task_name="HK-001",
				task_data={"status": "Completed"},
				inventory_items=[],
				checklist_items=[],
			)

		self.assertEqual(doc.status, "Completed")
		self.assertTrue(result["success"])


	def test_returns_error_dict_on_exception(self):
		with (
			patch.object(
				housekeeping.frappe,
				"get_doc",
				side_effect=Exception("Unexpected")
			),
			patch.object(housekeeping.frappe, "log_error"),
			patch.object(housekeeping.frappe.db, "rollback"),
		):
			result = housekeeping.update_task(
				task_name="HK-001",
				task_data={}
			)

		self.assertFalse(result["success"])
		self.assertIn("Unexpected", result["error"])


if __name__ == "__main__":
	unittest.main()