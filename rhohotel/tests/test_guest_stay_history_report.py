"""
Tests for rhohotel.rhocom_hotel.api.guest_stay_history_report
"""
import sys
import types
import unittest
from unittest.mock import patch

if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")
    frappe_stub._ = lambda t: t
    frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
    frappe_stub.throw = lambda m, *a, **k: (_ for _ in ()).throw(RuntimeError(m))
    frappe_stub.log_error = lambda *a, **k: None
    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *a, **k: [],
        count=lambda *a, **k: 0,
        get_value=lambda *a, **k: None,
        exists=lambda *a, **k: True,
        has_column=lambda *a, **k: True,
        commit=lambda: None,
    )
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.getdate = lambda v: v
    utils_stub.add_days = lambda d, n: d
    utils_stub.flt = lambda v, p=2: float(v or 0)
    utils_stub.cint = lambda v: int(v or 0)
    utils_stub.get_datetime = lambda v=None: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    utils_stub.format_datetime = lambda v, fmt="": "01-05-2026"
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import guest_stay_history_report as gsh


class DotDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e
    def __setattr__(self, key, value):
        self[key] = value


class TestGetPaymentStatus(unittest.TestCase):
    def test_settled(self):
        self.assertEqual(gsh._get_payment_status(1000, 0), "Settled")

    def test_outstanding(self):
        self.assertEqual(gsh._get_payment_status(0, 0), "Outstanding")

    def test_part_paid(self):
        self.assertEqual(gsh._get_payment_status(1000, 500), "Part Paid")

    def test_outstanding_with_balance(self):
        self.assertEqual(gsh._get_payment_status(1000, 1000), "Outstanding")

    def test_corporate_credit(self):
        self.assertEqual(gsh._get_payment_status(1000, 500, corporate_check_in="CI-001"), "Corporate Credit")


class TestGetGuestType(unittest.TestCase):
    def _row(self, **kwargs):
        base = {
            "corporate_check_in": None,
            "guest_type": None,
            "loyalty_tier": None,
            "number_of_nights": 1,
        }
        base.update(kwargs)
        return DotDict(base)

    def test_corporate(self):
        row = self._row(corporate_check_in="CI-001")
        self.assertEqual(gsh._get_guest_type(row, 1), "Corporate")

    def test_vip(self):
        row = self._row(loyalty_tier="VIP")
        self.assertEqual(gsh._get_guest_type(row, 1), "VIP")

    def test_long_stay(self):
        row = self._row(number_of_nights=7)
        self.assertEqual(gsh._get_guest_type(row, 1), "Long Stay")

    def test_repeat(self):
        row = self._row(number_of_nights=1)
        self.assertEqual(gsh._get_guest_type(row, 3), "Repeat")

    def test_new(self):
        row = self._row(number_of_nights=1)
        self.assertEqual(gsh._get_guest_type(row, 1), "New")


class TestGetSource(unittest.TestCase):
    def _row(self, **kwargs):
        return DotDict(kwargs)

    def test_corporate_from_checkin(self):
        row = self._row(corporate_check_in="CI-001", reservation_source=None,
                        market_place=None, guest_market_place=None, guest_type=None)
        self.assertEqual(gsh._get_source(row), "Corporate")

    def test_walk_in(self):
        row = self._row(corporate_check_in=None, reservation_source="Walk In",
                        market_place=None, guest_market_place=None, guest_type=None)
        self.assertEqual(gsh._get_source(row), "Walk-in")

    def test_direct_fallback(self):
        row = self._row(corporate_check_in=None, reservation_source=None,
                        market_place=None, guest_market_place=None, guest_type=None)
        self.assertEqual(gsh._get_source(row), "Direct")

    def test_source_from_reservation(self):
        row = self._row(corporate_check_in=None, reservation_source="Booking.com",
                        market_place=None, guest_market_place=None, guest_type=None)
        self.assertEqual(gsh._get_source(row), "Booking.com")


class TestGetGuestStayHistory(unittest.TestCase):
    def test_returns_required_keys(self):
        with (
            patch.object(gsh.frappe.db, "sql", return_value=[]),
            patch.object(gsh, "_get_invoice_totals", return_value={}),
        ):
            result = gsh.get_guest_stay_history()
        required = {"rows", "stats", "totals", "room_types", "sources", "generated_at", "filters"}
        self.assertTrue(required.issubset(result.keys()))

    def test_stats_keys_present(self):
        with (
            patch.object(gsh.frappe.db, "sql", return_value=[]),
            patch.object(gsh, "_get_invoice_totals", return_value={}),
        ):
            result = gsh.get_guest_stay_history()
        stats_keys = {"totalStays", "uniqueGuests", "repeatGuests", "repeatRatio",
                      "roomNights", "totalRevenue", "avgStay"}
        self.assertTrue(stats_keys.issubset(result["stats"].keys()))

    def test_guest_type_filter(self):
        row = DotDict(
            name="CI-001", guest="G-001", room_number="101", room_type="Deluxe",
            check_in_datetime="2026-05-01 14:00:00", expected_check_out_datetime="2026-05-03 12:00:00",
            actual_check_out_datetime=None, number_of_nights=2, rate_amount=5000,
            discount=0, total_charges=10000, total_outstanding_amount=0,
            reservation_source=None, corporate_check_in=None, housekeeping_notes=None,
            checkin_status="Checked Out", hotel_guest_name="John Doe", phone_number="",
            contact_number="", guest_type=None, guest_market_place=None,
            preference=None, notes=None, loyalty_tier=None
        )
        with (
            patch.object(gsh.frappe.db, "sql", side_effect=[
                [row],   # main checkins query
                [],      # stay_count query
                [],      # last_visit query
            ]),
            patch.object(gsh, "_get_invoice_totals", return_value={"CI-001": {"amount": 10000, "outstanding": 0, "paid_amount": 10000}}),
        ):
            result = gsh.get_guest_stay_history(guest_type="Corporate")
        # New guest should be filtered out
        self.assertEqual(result["rows"], [])

    def test_search_filter(self):
        with (
            patch.object(gsh.frappe.db, "sql", return_value=[]),
            patch.object(gsh, "_get_invoice_totals", return_value={}),
        ):
            result = gsh.get_guest_stay_history(search="nonexistent")
        self.assertEqual(result["rows"], [])

    def test_empty_stats_when_no_rows(self):
        with (
            patch.object(gsh.frappe.db, "sql", return_value=[]),
            patch.object(gsh, "_get_invoice_totals", return_value={}),
        ):
            result = gsh.get_guest_stay_history()
        self.assertEqual(result["stats"]["totalStays"], 0)
        self.assertEqual(result["stats"]["repeatRatio"], "0%")


if __name__ == "__main__":
    unittest.main()