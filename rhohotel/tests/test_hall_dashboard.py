"""
Tests for rhohotel.rhocom_hotel.api.hall_dashboard
"""
import sys
import types
import datetime
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
        get_all=lambda *a, **k: [],
        exists=lambda *a, **k: True,
        has_column=lambda *a, **k: True,
        commit=lambda: None,
    )
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.flt = lambda v, p=2: float(v or 0)

    def _getdate(v=None):
        if v is None:
            return datetime.date(2026, 5, 1)
        if isinstance(v, datetime.date):
            return v
        return datetime.date(2026, 5, 1)

    utils_stub.getdate = _getdate
    utils_stub.add_days = lambda d, n: d
    utils_stub.date_diff = lambda a, b: 0
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import hall_dashboard as hd


class _DD(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e
    def __setattr__(self, k, v):
        self[k] = v


class TestGetStatusLabel(unittest.TestCase):
    def test_draft(self):
        self.assertEqual(hd.get_status_label(0), "Draft")

    def test_confirmed(self):
        self.assertEqual(hd.get_status_label(1), "Confirmed")

    def test_cancelled(self):
        self.assertEqual(hd.get_status_label(2), "Cancelled")

    def test_unknown(self):
        self.assertEqual(hd.get_status_label(99), "Unknown")


class TestGetPeriodDays(unittest.TestCase):
    def test_minimum_one(self):
        same = datetime.date(2026, 5, 1)
        with patch.object(hd, "date_diff", return_value=0):
            result = hd.get_period_days(same, same)
        self.assertEqual(result, 1)

    def test_multiple_days(self):
        start = datetime.date(2026, 5, 1)
        end = datetime.date(2026, 5, 7)
        with patch.object(hd, "date_diff", return_value=6):
            result = hd.get_period_days(start, end)
        self.assertEqual(result, 7)


class TestGetOverlapDays(unittest.TestCase):
    def test_no_overlap_returns_zero(self):
        # booking May 10-15, period May 1-5: no overlap
        result = hd.get_overlap_days(
            datetime.date(2026, 5, 10), datetime.date(2026, 5, 15),
            datetime.date(2026, 5, 1), datetime.date(2026, 5, 5),
        )
        self.assertEqual(result, 0)


class TestBuildStats(unittest.TestCase):
    def test_returns_required_keys(self):
        result = hd.build_stats([], [],
                                datetime.date(2026, 5, 1),
                                datetime.date(2026, 5, 31))
        required = {"total_bookings", "today", "today_start_date",
                    "today_end_date", "pending_payment", "utilization"}
        self.assertTrue(required.issubset(result.keys()))

    def test_total_bookings_count(self):
        # build_stats counts all bookings regardless of status
        bookings = [_DD({"docstatus": 1, "payment_status": "Paid", "net_total": 5000,
             "start_datetime": "2026-05-01 00:00:00",
             "end_datetime": "2026-05-03 00:00:00"})]
        result = hd.build_stats(bookings, [],
                                datetime.date(2026, 5, 1),
                                datetime.date(2026, 5, 31))
        self.assertEqual(result["total_bookings"], 1)


class TestBuildPaymentSummary(unittest.TestCase):
    def test_paid_and_pending(self):
        bookings = [
            _DD({"payment_status": "Paid", "net_total": 10000}),
            _DD({"payment_status": "Unpaid", "net_total": 5000}),
        ]
        result = hd.build_payment_summary(bookings)
        self.assertEqual(result["paid_today"], 10000)
        self.assertEqual(result["pending"], 5000)


class TestBuildBookingStatus(unittest.TestCase):
    def test_counts_by_docstatus(self):
        bookings = [
            _DD({"docstatus": 1, "payment_status": "Paid"}),
            _DD({"docstatus": 1, "payment_status": "Unpaid"}),
        ]
        result = hd.build_booking_status(bookings)
        self.assertEqual(result["confirmed"], 2)
        self.assertEqual(result["paid"], 1)


class TestGetDashboardData(unittest.TestCase):
    def test_returns_required_keys(self):
        with (
            patch.object(hd, "get_bookings", return_value=[]),
            patch.object(hd.frappe.db, "get_all", return_value=[]),
        ):
            result = hd.get_dashboard_data()
        required = {"filters", "halls", "stats", "payment", "alerts",
                    "booking_status", "revenue_trend", "occupancy", "upcoming_events"}
        self.assertTrue(required.issubset(result.keys()))


if __name__ == "__main__":
    unittest.main()