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
	frappe_stub.db = types.SimpleNamespace(
		sql=lambda *args, **kwargs: [],
		get_value=lambda *args, **kwargs: None,
	)
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
