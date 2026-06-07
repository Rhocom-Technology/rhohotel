import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

frappe_stub = sys.modules.get("frappe")
if frappe_stub is None:
	frappe_stub = types.ModuleType("frappe")
	sys.modules["frappe"] = frappe_stub

def _default_throw(message):
	raise RuntimeError(message)

def _whitelist(*args, **kwargs):
	def _decorator(fn):
		return fn

	return _decorator

if not hasattr(frappe_stub, "_"):
	frappe_stub._ = lambda text: text
if not hasattr(frappe_stub, "throw"):
	frappe_stub.throw = _default_throw
if not hasattr(frappe_stub, "get_all"):
	frappe_stub.get_all = lambda *args, **kwargs: []
if not hasattr(frappe_stub, "db"):
	frappe_stub.db = types.SimpleNamespace()
if not hasattr(frappe_stub.db, "sql"):
	frappe_stub.db.sql = lambda *args, **kwargs: []
if not hasattr(frappe_stub.db, "get_value"):
	frappe_stub.db.get_value = lambda *args, **kwargs: None
if not hasattr(frappe_stub.db, "get_single_value"):
	frappe_stub.db.get_single_value = lambda *args, **kwargs: None
if not hasattr(frappe_stub, "whitelist"):
	frappe_stub.whitelist = _whitelist

utils_stub = sys.modules.get("frappe.utils")
if utils_stub is None:
	utils_stub = types.ModuleType("frappe.utils")
	sys.modules["frappe.utils"] = utils_stub

def _get_datetime(value):
	if isinstance(value, datetime):
		return value
	if isinstance(value, str):
		# supports both YYYY-MM-DD and YYYY-MM-DD HH:MM:SS
		try:
			return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
		except ValueError:
			return datetime.strptime(value, "%Y-%m-%d")
	return datetime.combine(value, datetime.min.time())

def _getdate(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, str):
		return datetime.strptime(value, "%Y-%m-%d").date()
	return value

if not hasattr(utils_stub, "get_datetime"):
	utils_stub.get_datetime = _get_datetime
if not hasattr(utils_stub, "getdate"):
	utils_stub.getdate = _getdate
if not hasattr(utils_stub, "date_diff"):
	utils_stub.date_diff = lambda a, b: (a - b).days

sys.modules["frappe"] = frappe_stub

from rhohotel.rhocom_hotel.utils import room_availability as ra


class DotDict(dict):
	"""Simple dict with attribute access to mimic frappe._dict in tests."""

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc

	def __setattr__(self, key, value):
		self[key] = value


class TestRoomAvailability(unittest.TestCase):
	def test_assert_room_available_throws_when_checkin_conflicts(self):
		with (
			patch.object(
				ra,
				"check_checkin_conflict",
				return_value=DotDict(
					name="CHK-011",
					check_in_datetime="2026-04-10 12:00:00",
					expected_check_out_datetime="2026-04-12 12:00:00",
				),
			),
			patch.object(ra.frappe, "throw", side_effect=RuntimeError("checkin conflict")) as throw_mock,
		):
			with self.assertRaises(RuntimeError):
				ra.assert_room_available("R-101", "2026-04-10", "2026-04-12")

		self.assertTrue(throw_mock.called)

	def test_get_available_rooms_filters_and_excludes_unavailable(self):
		rooms = [
			DotDict(name="R-101", room_type="Deluxe", floor="1", capacity=2),
			DotDict(name="R-102", room_type="Deluxe", floor="1", capacity=2),
		]

		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))

		captured = {"filters": None}

		def fake_get_all(doctype, filters, fields):
			captured["filters"] = filters
			return rooms

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", side_effect=fake_get_all),
			patch.object(ra.frappe.db, "sql", return_value=[]),
			patch.object(ra, "date_diff", return_value=2),
		):
			available = ra.get_available_rooms(
				"2026-04-10",
				"2026-04-12",
				room_type="Deluxe",
				require_vacant=True,
			)

		self.assertEqual(captured["filters"]["room_type"], "Deluxe")
		self.assertEqual(captured["filters"]["status"], "Vacant")
		self.assertEqual(len(available), 2)
		self.assertEqual(available[0]["rate_per_night"], 50000)
		self.assertEqual(available[0]["total_amount"], 100000)

	def test_canonical_reservation_conflict_ignores_consumed_room_rows(self):
		with patch.object(ra.frappe.db, "sql", return_value=[]) as sql_mock:
			conflict = ra.check_canonical_reservation_conflict(
				"R-104",
				"2026-04-10",
				"2026-04-12",
			)

		self.assertIsNone(conflict)
		query = sql_mock.call_args.args[0]
		self.assertIn("COALESCE(rr.check_in_reference, '') = ''", query)
		self.assertIn("COALESCE(rr.status, 'Reserved') NOT IN", query)
		self.assertIn("'Checked In', 'Checked Out', 'Cancelled'", query)

	def test_get_available_rooms_allows_transferred_out_reservation_room(self):
		rooms = [
			DotDict(name="R-104", room_type="Deluxe", floor="1", capacity=2),
			DotDict(name="R-105", room_type="Deluxe", floor="1", capacity=2),
		]
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))
		sql_queries = []

		def fake_sql(query, params=None, as_dict=False):
			sql_queries.append(query)
			if "FROM `tabHotel Room Check In`" in query and "expected_check_out_datetime >" in query:
				return [DotDict(room_number="R-105")]
			if "FROM `tabHotel Reservation Room`" in query:
				self.assertIn("COALESCE(rr.check_in_reference, '') = ''", query)
				self.assertIn("COALESCE(rr.status, 'Reserved') NOT IN", query)
				return []
			return []

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", return_value=rooms),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
			patch.object(ra, "date_diff", return_value=2),
		):
			available = ra.get_available_rooms(
				"2026-04-10",
				"2026-04-12",
				require_vacant=True,
			)

		self.assertEqual([room.name for room in available], ["R-104"])
		self.assertTrue(any("FROM `tabHotel Reservation Room`" in q for q in sql_queries))

	def test_get_available_rooms_does_not_treat_current_occupancy_as_future_block(self):
		rooms = [
			DotDict(name="R-101", room_type="Deluxe", floor="1", capacity=2),
			DotDict(name="R-102", room_type="Deluxe", floor="1", capacity=2),
		]
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))
		sql_queries = []

		def fake_sql(query, params=None, as_dict=False):
			sql_queries.append(query)
			if "expected_check_out_datetime <=" in query:
				return [DotDict(room_number="R-101")]
			return []

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", return_value=rooms),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
			patch.object(ra, "date_diff", return_value=2),
		):
			available = ra.get_available_rooms("2099-07-01", "2099-07-03")

		self.assertEqual([room.name for room in available], ["R-101", "R-102"])
		self.assertFalse(any("expected_check_out_datetime <=" in q for q in sql_queries))

	def test_get_available_rooms_blocks_overdue_checkin_for_current_arrival(self):
		today = datetime.now().strftime("%Y-%m-%d")
		tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
		rooms = [
			DotDict(name="R-101", room_type="Deluxe", floor="1", capacity=2),
			DotDict(name="R-102", room_type="Deluxe", floor="1", capacity=2),
		]
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))

		def fake_sql(query, params=None, as_dict=False):
			if "expected_check_out_datetime <=" in query:
				return [DotDict(room_number="R-101")]
			return []

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", return_value=rooms),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
			patch.object(ra, "date_diff", return_value=1),
		):
			available = ra.get_available_rooms(today, tomorrow)

		self.assertEqual([room.name for room in available], ["R-102"])

	def test_check_checkin_conflict_does_not_treat_overdue_stay_as_future_block(self):
		with patch.object(ra.frappe, "get_all", return_value=[]) as get_all_mock:
			conflict = ra.check_checkin_conflict("R-101", "2099-07-01", "2099-07-03")

		self.assertIsNone(conflict)
		self.assertEqual(get_all_mock.call_count, 1)

	def test_get_available_rooms_throws_for_invalid_date_range(self):
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))
		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "throw", side_effect=ValueError("bad range")),
		):
			with self.assertRaises(ValueError):
				ra.get_available_rooms("2026-04-12", "2026-04-12")

	def test_assert_room_available_occupied_room_blocks_current_arrival(self):
		with (
			patch.object(ra, "check_checkin_conflict", return_value=None),
			patch.object(ra, "check_canonical_reservation_conflict", return_value=None),
			patch.object(ra.frappe.db, "get_value", return_value="Occupied"),
			patch.object(ra.frappe, "throw", side_effect=RuntimeError("occupied now")),
		):
			with self.assertRaises(RuntimeError):
				ra.assert_room_available("R-101", datetime.now(), datetime.now())

	def test_assert_room_available_occupied_room_allows_future_arrival(self):
		throw_mock = Mock()
		with (
			patch.object(ra, "check_checkin_conflict", return_value=None),
			patch.object(ra, "check_canonical_reservation_conflict", return_value=None),
			patch.object(ra.frappe.db, "get_value", return_value="Occupied"),
			patch.object(ra.frappe, "throw", throw_mock),
		):
			ra.assert_room_available("R-101", "2099-01-01", "2099-01-02")

		throw_mock.assert_not_called()


if __name__ == "__main__":
	unittest.main()
