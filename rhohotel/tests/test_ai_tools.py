import sys
import types
import unittest
from unittest.mock import patch


if "frappe" not in sys.modules:
	frappe_stub = types.ModuleType("frappe")
	frappe_stub.get_all = lambda *args, **kwargs: []
	frappe_stub.log_error = lambda *args, **kwargs: None
	frappe_stub.db = types.SimpleNamespace(sql=lambda *args, **kwargs: [])
	sys.modules["frappe"] = frappe_stub

if "frappe.utils" not in sys.modules:
	utils_stub = types.ModuleType("frappe.utils")
	utils_stub.today = lambda: "2026-06-30"
	utils_stub.getdate = lambda value=None: value
	utils_stub.flt = lambda value=0, *_, **__: float(value or 0)
	sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import ai_tools


class DotDict(dict):
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc


class TestAIRoomStatusTools(unittest.TestCase):
	def test_occupancy_summary_uses_hotel_room_status_fields(self):
		rooms = [
			DotDict(name="101", status="Occupied", operational_status="In Service", maintenance_flag=0),
			DotDict(name="102", status="Vacant", operational_status="In Service", maintenance_flag=0),
			DotDict(name="103", status="Maintenance", operational_status="In Service", maintenance_flag=0),
			DotDict(name="104", status="Vacant", operational_status="Out of Service", maintenance_flag=0),
			DotDict(name="105", status="Occupied", operational_status="In Service", maintenance_flag=1),
		]

		with patch.object(ai_tools.frappe, "get_all", return_value=rooms) as get_all:
			result = ai_tools.get_occupancy_summary()

		self.assertEqual(result["total_rooms"], 5)
		self.assertEqual(result["occupied"], 1)
		self.assertEqual(result["vacant"], 1)
		self.assertEqual(result["maintenance"], 3)
		self.assertEqual(result["occupancy_pct"], 20.0)
		self.assertNotIn("occupancy_status", get_all.call_args.kwargs["fields"])

	def test_maintenance_blocked_rooms_includes_flags_and_out_of_service(self):
		rooms = [
			DotDict(name="101", status="Vacant", operational_status="In Service", maintenance_flag=0),
			DotDict(name="102", status="Maintenance", operational_status="In Service", maintenance_flag=0),
			DotDict(name="103", status="Vacant", operational_status="Blocked", maintenance_flag=0),
			DotDict(name="104", status="Occupied", operational_status="In Service", maintenance_flag=1),
		]

		with patch.object(ai_tools.frappe, "get_all", return_value=rooms):
			result = ai_tools.get_maintenance_blocked_rooms()

		self.assertEqual(result["count"], 3)
		self.assertEqual(
			{room["name"] for room in result["maintenance_blocked_rooms"]},
			{"102", "103", "104"},
		)


if __name__ == "__main__":
	unittest.main()
