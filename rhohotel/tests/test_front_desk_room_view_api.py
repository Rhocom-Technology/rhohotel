import json
import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch


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
	frappe_stub.db = types.SimpleNamespace(sql=lambda *args, **kwargs: [])

	utils_stub = types.ModuleType("frappe.utils")
	utils_stub.now_datetime = lambda: datetime(2026, 4, 25, 12, 0, 0)
	utils_stub.add_to_date = lambda value, **kwargs: value
	utils_stub.flt = lambda value: float(value or 0)
	utils_stub.cstr = lambda value: "" if value is None else str(value)

	sys.modules["frappe"] = frappe_stub
	sys.modules["frappe.utils"] = utils_stub


from rhohotel.rhocom_hotel.api import front_desk


class TestFrontDeskRoomViewApi(unittest.TestCase):
	def test_get_room_view_data_builds_stats_and_normalized_rows(self):
		now = datetime(2026, 4, 25, 12, 0, 0)
		rooms = [
			{
				"name": "HR-001",
				"room_number": "101",
				"room_type": "Deluxe",
				"floor": "1",
				"status": "occupied",
				"housekeeping_status": "dirty",
				"current_guest": "John Doe",
			},
			{
				"name": "HR-002",
				"room_number": "102",
				"room_type": "Deluxe",
				"floor": "1",
				"status": "vacant",
				"housekeeping_status": "Clean",
				"current_guest": None,
			},
			{
				"name": "HR-003",
				"room_number": "201",
				"room_type": "Suite",
				"floor": "2",
				"status": "Reserved",
				"housekeeping_status": "Inspected",
				"current_guest": None,
			},
		]
		checkins = [
			{
				"name": "CHK-001",
				"room_number": "101",
				"guest": "John Doe",
				"reservation_source": "Walk in",
				"expected_check_out_datetime": now - timedelta(hours=2),
				"total_outstanding_amount": 2500,
			}
		]

		with (
			patch.object(front_desk.frappe, "get_all", side_effect=[rooms, checkins]),
			patch.object(front_desk, "now_datetime", return_value=now),
		):
			result = front_desk.get_room_view_data()

		self.assertEqual(result["total_rooms"], 3)
		self.assertEqual(result["filtered_rooms"], 3)
		self.assertEqual(result["stats"]["occupied"], 1)
		self.assertEqual(result["stats"]["vacant"], 1)
		self.assertEqual(result["stats"]["reserved"], 1)
		self.assertEqual(result["stats"]["dirty"], 1)
		self.assertEqual(result["stats"]["overdue"], 1)
		self.assertEqual(result["stats"]["unpaid"], 1)
		self.assertEqual(result["stats"]["vip"], 1)

		first_room = result["rooms"][0]
		self.assertEqual(first_room["status"], "Occupied")
		self.assertEqual(first_room["housekeeping_status"], "Dirty")
		self.assertEqual(first_room["reservation_source"], "Walk in")
		self.assertEqual(first_room["current_guest"], "John Doe")
		self.assertTrue(first_room["overdue"])
		self.assertTrue(first_room["unpaid"])

	def test_get_room_view_data_applies_filters(self):
		now = datetime(2026, 4, 25, 12, 0, 0)
		rooms = [
			{
				"name": "HR-010",
				"room_number": "301",
				"room_type": "Standard",
				"floor": 3,
				"status": "Occupied",
				"housekeeping_status": "Dirty",
				"current_guest": "Alice",
			},
			{
				"name": "HR-011",
				"room_number": "302",
				"room_type": "Standard",
				"floor": 3,
				"status": "Occupied",
				"housekeeping_status": "Clean",
				"current_guest": "Bob",
			},
		]
		checkins = [
			{
				"name": "CHK-010",
				"room_number": "301",
				"expected_check_out_datetime": now - timedelta(hours=1),
				"total_outstanding_amount": 0,
			},
			{
				"name": "CHK-011",
				"room_number": "302",
				"expected_check_out_datetime": now + timedelta(hours=4),
				"total_outstanding_amount": 0,
			},
		]
		filters = json.dumps({"floor": "3", "only_overdue": True, "search": "301"})

		with (
			patch.object(front_desk.frappe, "get_all", side_effect=[rooms, checkins]),
			patch.object(front_desk, "now_datetime", return_value=now),
		):
			result = front_desk.get_room_view_data(filters=filters)

		self.assertEqual(result["total_rooms"], 2)
		self.assertEqual(result["filtered_rooms"], 1)
		self.assertEqual(result["rooms"][0]["room_number"], "301")


if __name__ == "__main__":
	unittest.main()
