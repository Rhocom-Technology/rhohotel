import sys
import types
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

if "frappe" not in sys.modules:
	frappe_stub = types.ModuleType("frappe")

	def _default_throw(message):
		raise RuntimeError(message)

	def _whitelist(*args, **kwargs):
		def _decorator(fn):
			return fn

		return _decorator

	frappe_stub._ = lambda text: text
	frappe_stub.throw = _default_throw
	frappe_stub.get_all = lambda *args, **kwargs: []
	frappe_stub.db = types.SimpleNamespace(sql=lambda *args, **kwargs: [])
	frappe_stub.whitelist = _whitelist

	utils_stub = types.ModuleType("frappe.utils")

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

	utils_stub.get_datetime = _get_datetime
	utils_stub.getdate = _getdate
	utils_stub.date_diff = lambda a, b: (a - b).days

	sys.modules["frappe"] = frappe_stub
	sys.modules["frappe.utils"] = utils_stub

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
	def test_check_reservation_conflict_applies_exclusion_filter(self):
		captured = {}

		def fake_get_all(doctype, filters, fields, limit):
			captured["doctype"] = doctype
			captured["filters"] = filters
			captured["fields"] = fields
			captured["limit"] = limit
			return [DotDict(name="RES-001", from_date="2026-04-10", to_date="2026-04-12")]

		with patch.object(ra.frappe, "get_all", side_effect=fake_get_all):
			conflict = ra.check_reservation_conflict(
				"R-101",
				"2026-04-10",
				"2026-04-12",
				exclude_reservation="RES-CURRENT",
			)

		self.assertEqual(captured["doctype"], "Hotel Room Reservation")
		self.assertEqual(captured["filters"]["room_number"], "R-101")
		self.assertEqual(captured["filters"]["name"], ["!=", "RES-CURRENT"])
		self.assertEqual(conflict.name, "RES-001")

	def test_assert_room_available_throws_when_reservation_conflicts(self):
		with (
			patch.object(
				ra,
				"check_reservation_conflict",
				return_value=DotDict(name="RES-009", from_date="2026-04-10", to_date="2026-04-12"),
			),
			patch.object(ra, "check_checkin_conflict", return_value=None),
			patch.object(ra.frappe, "throw", side_effect=RuntimeError("reservation conflict")) as throw_mock,
		):
			with self.assertRaises(RuntimeError):
				ra.assert_room_available("R-101", "2026-04-10", "2026-04-12")

		self.assertTrue(throw_mock.called)

	def test_assert_room_available_throws_when_checkin_conflicts(self):
		with (
			patch.object(ra, "check_reservation_conflict", return_value=None),
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

		sql_calls = [
			[DotDict(room_number="R-102")],  # held rooms (Temporary Booking)
			[],  # booked rooms (legacy Hotel Room Reservation)
			[],  # checked-in rooms (Hotel Room Check In)
			[],  # canonical rooms (Hotel Reservation Room child table)
		]

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", side_effect=fake_get_all),
			patch.object(ra.frappe.db, "sql", side_effect=sql_calls),
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
		self.assertEqual(len(available), 1)
		self.assertEqual(available[0]["name"], "R-101")
		self.assertEqual(available[0]["rate_per_night"], 50000)
		self.assertEqual(available[0]["total_amount"], 100000)

	def test_get_available_rooms_throws_for_invalid_date_range(self):
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))
		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "throw", side_effect=ValueError("bad range")),
		):
			with self.assertRaises(ValueError):
				ra.get_available_rooms("2026-04-12", "2026-04-12")


if __name__ == "__main__":
	unittest.main()
