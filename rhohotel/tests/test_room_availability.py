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


# ---------------------------------------------------------------------------
# Hotel-settings time boundary tests
# ---------------------------------------------------------------------------

def _make_hotel_settings(check_in_time="13:00:00", check_out_time="11:00:00"):
	"""Return a mock Hotel Settings singleton."""
	return types.SimpleNamespace(
		default_check_in_time=check_in_time,
		default_check_out_time=check_out_time,
	)


class TestHotelTimeBoundaries(unittest.TestCase):
	"""
	Verify that room availability uses the hotel's configured check-in /
	check-out times rather than the old hardcoded 12:00 noon boundary.

	Scenario that previously caused false conflicts
	------------------------------------------------
	Hotel settings:  check-in  13:00,  check-out  11:00.

	An existing guest checked in on June 11 and is expected to check out on
	June 12 at 11:00.  A new reservation also starts on June 12 (from_date
	= '2026-06-12').  The DB DATE value '2026-06-12' must be interpreted as
	2026-06-12 11:00:00 (checkout time) so that:

	    TIMESTAMP('2026-06-12', '11:00:00') > 2026-06-12 11:00:00  →  FALSE

	meaning the incoming reservation does NOT block the outgoing guest's room.
	"""

	def _patch_hotel_settings(self, check_in="13:00:00", check_out="11:00:00"):
		"""Return a context manager that patches _get_hotel_time_strings."""
		return patch.object(
			ra,
			"_get_hotel_time_strings",
			return_value=(check_in, check_out),
		)

	# ------------------------------------------------------------------
	# _normalize_checkin_dt / _normalize_checkout_dt
	# ------------------------------------------------------------------

	def test_normalize_checkin_dt_uses_hotel_checkin_time(self):
		with self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"):
			result = ra._normalize_checkin_dt("2026-06-12")
		self.assertEqual(result, datetime(2026, 6, 12, 13, 0, 0))

	def test_normalize_checkout_dt_uses_hotel_checkout_time(self):
		with self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"):
			result = ra._normalize_checkout_dt("2026-06-12")
		self.assertEqual(result, datetime(2026, 6, 12, 11, 0, 0))

	def test_normalize_checkin_dt_passes_through_full_datetime(self):
		"""Full datetime strings must not have their time overridden."""
		with self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"):
			result = ra._normalize_checkin_dt("2026-06-12 15:30:00")
		self.assertEqual(result, datetime(2026, 6, 12, 15, 30, 0))

	def test_normalize_checkout_dt_passes_through_full_datetime(self):
		with self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"):
			result = ra._normalize_checkout_dt("2026-06-12 09:00:00")
		self.assertEqual(result, datetime(2026, 6, 12, 9, 0, 0))

	# ------------------------------------------------------------------
	# _get_hotel_time_strings fallback
	# ------------------------------------------------------------------

	def test_get_hotel_time_strings_returns_settings_values(self):
		mock_settings = _make_hotel_settings("14:00:00", "10:00:00")
		with patch.object(ra.frappe, "get_single", return_value=mock_settings, create=True):
			ci, co = ra._get_hotel_time_strings()
		self.assertEqual(ci, "14:00:00")
		self.assertEqual(co, "10:00:00")

	def test_get_hotel_time_strings_pads_short_values(self):
		"""Values stored as HH:MM (no seconds) should be padded to HH:MM:SS."""
		mock_settings = _make_hotel_settings("13:00", "11:00")
		with patch.object(ra.frappe, "get_single", return_value=mock_settings, create=True):
			ci, co = ra._get_hotel_time_strings()
		self.assertEqual(ci, "13:00:00")
		self.assertEqual(co, "11:00:00")

	def test_get_hotel_time_strings_falls_back_on_exception(self):
		with patch.object(ra.frappe, "get_single", side_effect=Exception("no DB"), create=True):
			ci, co = ra._get_hotel_time_strings()
		self.assertEqual(ci, "13:00:00")
		self.assertEqual(co, "11:00:00")

	# ------------------------------------------------------------------
	# check_canonical_reservation_conflict uses parameterised times
	# ------------------------------------------------------------------

	def test_canonical_conflict_uses_hotel_times_in_sql(self):
		"""
		The SQL query must pass the hotel's actual check-in / check-out time
		strings as parameters, not the literal '12:00:00'.
		"""
		captured = {}

		def fake_sql(query, params, as_dict=False):
			captured["query"] = query
			captured["params"] = params
			return []

		with (
			self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
		):
			ra.check_canonical_reservation_conflict("R-101", "2026-06-11", "2026-06-12")

		query = captured["query"]
		params = captured["params"]

		# Time strings must be passed as query parameters
		self.assertIn("%s", query)
		self.assertIn("13:00:00", params)
		self.assertIn("11:00:00", params)
		# Must NOT contain the old hardcoded literal
		self.assertNotIn("'12:00:00'", query)

	def test_canonical_conflict_checkout_eq_next_checkin_no_conflict(self):
		"""
		A new reservation starting the same date an existing one ends must
		NOT be detected as a conflict.

		Existing reservation: from_date='2026-06-11', to_date='2026-06-12'
		  → interpreted as checkout 2026-06-12 11:00:00

		New booking check-in: '2026-06-12'
		  → interpreted as 2026-06-12 13:00:00

		Overlap condition:
		  TIMESTAMP(from_date, '13:00:00') < checkout_of_new  (2026-06-12 11:00)
		    → 2026-06-11 13:00 < 2026-06-12 11:00  ✓  (from_date side passes)
		  TIMESTAMP(to_date, '11:00:00') > checkin_of_new  (2026-06-12 13:00)
		    → 2026-06-12 11:00 > 2026-06-12 13:00  ✗  (no conflict)
		"""
		def fake_sql(query, params, as_dict=False):
			# Simulate real MariaDB evaluation of the TIMESTAMP conditions
			# by extracting the time strings from params and evaluating manually.
			# params order: (room_number, ci_time, check_out_str, co_time, check_in_str)
			_, ci_time, check_out_str, co_time, check_in_str = params[:5]

			from_date = "2026-06-11"
			to_date = "2026-06-12"

			def ts(date_str, time_str):
				return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

			existing_from = ts(from_date, ci_time)
			existing_to = ts(to_date, co_time)
			new_checkout = datetime.strptime(check_out_str, "%Y-%m-%d %H:%M:%S")
			new_checkin = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")

			overlaps = existing_from < new_checkout and existing_to > new_checkin
			if overlaps:
				return [DotDict(name="RES-001", from_date=from_date, to_date=to_date, primary_guest_name="Test")]
			return []

		with (
			self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
		):
			# Existing reservation ends June 12; new booking starts June 12 — no conflict.
			conflict = ra.check_canonical_reservation_conflict(
				"R-101",
				"2026-06-12",   # new check-in  → 2026-06-12 13:00
				"2026-06-13",   # new check-out → 2026-06-13 11:00
			)

		self.assertIsNone(conflict, "Same-day turnover should not be a conflict")

	def test_canonical_conflict_detected_when_dates_genuinely_overlap(self):
		"""Genuine overlapping dates must still be detected as a conflict."""
		def fake_sql(query, params, as_dict=False):
			_, ci_time, check_out_str, co_time, check_in_str = params[:5]
			from_date = "2026-06-10"
			to_date = "2026-06-14"

			def ts(date_str, time_str):
				return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

			existing_from = ts(from_date, ci_time)
			existing_to = ts(to_date, co_time)
			new_checkout = datetime.strptime(check_out_str, "%Y-%m-%d %H:%M:%S")
			new_checkin = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")

			if existing_from < new_checkout and existing_to > new_checkin:
				return [DotDict(name="RES-002", from_date=from_date, to_date=to_date, primary_guest_name="Guest")]
			return []

		with (
			self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
		):
			conflict = ra.check_canonical_reservation_conflict(
				"R-101",
				"2026-06-12",   # new check-in
				"2026-06-15",   # new check-out
			)

		self.assertIsNotNone(conflict, "Overlapping dates must still be detected")
		self.assertEqual(conflict.name, "RES-002")

	# ------------------------------------------------------------------
	# get_available_rooms passes hotel times to canonical SQL
	# ------------------------------------------------------------------

	def test_get_available_rooms_passes_hotel_times_to_canonical_sql(self):
		"""
		The canonical-reservation SQL in get_available_rooms must use the
		hotel's check-in / check-out time strings as parameters.
		"""
		rooms = [DotDict(name="R-101", room_type="Deluxe", floor="1", capacity=2)]
		faked_api = types.SimpleNamespace(get_room_rate=Mock(return_value=50000))
		canonical_params = {}

		def fake_sql(query, params=None, as_dict=False):
			if "tabHotel Reservation Room" in query:
				canonical_params["query"] = query
				canonical_params["params"] = params
			return []

		with (
			patch.dict(sys.modules, {"rhohotel.api": faked_api}),
			patch.object(ra.frappe, "get_all", return_value=rooms),
			patch.object(ra.frappe.db, "sql", side_effect=fake_sql),
			patch.object(ra, "date_diff", return_value=1),
			self._patch_hotel_settings(check_in="13:00:00", check_out="11:00:00"),
		):
			ra.get_available_rooms("2026-06-12", "2026-06-13")

		self.assertIn("query", canonical_params, "Canonical SQL was not called")
		self.assertNotIn("'12:00:00'", canonical_params["query"])
		self.assertIn("13:00:00", canonical_params["params"])
		self.assertIn("11:00:00", canonical_params["params"])


if __name__ == "__main__":
	unittest.main()
