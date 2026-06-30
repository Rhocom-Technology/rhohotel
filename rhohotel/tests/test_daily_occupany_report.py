"""
Tests for rhohotel.rhocom_hotel.api.daily_occupany_report
"""
import sys
import types
import unittest
from unittest.mock import patch, MagicMock

if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")
    frappe_stub._ = lambda t: t
    frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
    frappe_stub.throw = lambda m, *a, **k: (_ for _ in ()).throw(RuntimeError(m))
    frappe_stub.log_error = lambda *a, **k: None
    frappe_stub.get_traceback = lambda: ""
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
    utils_stub.format_datetime = lambda v, fmt="": str(v)
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import daily_occupany_report as dor


class TestGetPaymentStatus(unittest.TestCase):
    def test_paid(self):
        self.assertEqual(dor._get_payment_status(1000, 1000, 0), "Paid")

    def test_part_payment(self):
        self.assertEqual(dor._get_payment_status(1000, 500, 500), "Part Payment")

    def test_unpaid(self):
        self.assertEqual(dor._get_payment_status(1000, 0, 1000), "Unpaid")

    def test_empty_amount(self):
        self.assertEqual(dor._get_payment_status(0, 0, 0), "")


class TestGetRoomStatus(unittest.TestCase):
    def test_occupied_when_checkin(self):
        import datetime
        future = datetime.datetime(2099, 1, 1)
        checkin = {"expected_check_out_datetime": future}
        compare_dt = datetime.datetime(2026, 5, 1)
        result = dor._get_room_status("Vacant", "Clean", checkin, compare_dt)
        self.assertEqual(result, "Occupied")

    def test_overdue_checkout(self):
        import datetime
        past_checkout = datetime.datetime(2020, 1, 1)
        compare_after_checkout = datetime.datetime(2026, 5, 1)
        # Stub out get_datetime to return the actual value passed in (not a fixed value)
        with patch.object(dor, "get_datetime", side_effect=lambda v: v):
            checkin = {"expected_check_out_datetime": past_checkout}
            result = dor._get_room_status("Occupied", "Clean", checkin, compare_after_checkout)
        self.assertEqual(result, "Overdue Check-Out")

    def test_maintenance(self):
        result = dor._get_room_status("Maintenance", "Clean", None)
        self.assertEqual(result, "Maintenance")

    def test_vacant_dirty(self):
        result = dor._get_room_status("Vacant", "Dirty", None)
        self.assertEqual(result, "Vacant Dirty")

    def test_vacant_clean(self):
        result = dor._get_room_status("Vacant", "Clean", None)
        self.assertEqual(result, "Vacant Clean")


class TestMoney(unittest.TestCase):
    def test_rounds_to_two_decimals(self):
        self.assertEqual(dor._money(100), 100.0)

    def test_handles_none(self):
        self.assertEqual(dor._money(None), 0.0)

    def test_handles_zero(self):
        self.assertEqual(dor._money(0), 0.0)


class TestGetDailyOccupancyReport(unittest.TestCase):
    def test_returns_required_keys(self):
        with (
            patch.object(dor.frappe.db, "sql", return_value=[]),
            patch.object(dor.frappe.db, "count", return_value=0),
            patch.object(dor, "_get_invoice_totals", return_value={}),
            patch.object(dor, "_has_doctype", return_value=False),
            patch.object(dor, "_has_column", return_value=False),
        ):
            result = dor.get_daily_occupancy_report()
        required = {"rows", "stats", "totals", "rooms", "floors", "generated_at", "filters"}
        self.assertTrue(required.issubset(result.keys()))

    def test_stats_keys_present(self):
        with (
            patch.object(dor.frappe.db, "sql", return_value=[]),
            patch.object(dor.frappe.db, "count", return_value=0),
            patch.object(dor, "_get_invoice_totals", return_value={}),
            patch.object(dor, "_has_doctype", return_value=False),
            patch.object(dor, "_has_column", return_value=False),
        ):
            result = dor.get_daily_occupancy_report()
        stats_keys = {
            "occupancyRate", "totalRooms", "occupiedRooms", "vacantRooms",
            "arrivals", "departures", "outstanding", "overdueCheckOut",
            "roomRevenue", "posRevenue", "totalCollected", "totalRevenue"
        }
        self.assertTrue(stats_keys.issubset(result["stats"].keys()))

    def test_filters_returned_in_response(self):
        with (
            patch.object(dor.frappe.db, "sql", return_value=[]),
            patch.object(dor.frappe.db, "count", return_value=0),
            patch.object(dor, "_get_invoice_totals", return_value={}),
            patch.object(dor, "_has_doctype", return_value=False),
            patch.object(dor, "_has_column", return_value=False),
        ):
            result = dor.get_daily_occupancy_report(date_from="2026-05-01", date_to="2026-05-01")
        self.assertIn("date_from", result["filters"])
        self.assertIn("date_to", result["filters"])

    def test_totals_keys_present(self):
        with (
            patch.object(dor.frappe.db, "sql", return_value=[]),
            patch.object(dor.frappe.db, "count", return_value=0),
            patch.object(dor, "_get_invoice_totals", return_value={}),
            patch.object(dor, "_has_doctype", return_value=False),
            patch.object(dor, "_has_column", return_value=False),
        ):
            result = dor.get_daily_occupancy_report()
        totals_keys = {"nights", "discount", "amount", "paid_amount", "outstanding"}
        self.assertTrue(totals_keys.issubset(result["totals"].keys()))


if __name__ == "__main__":
    unittest.main()