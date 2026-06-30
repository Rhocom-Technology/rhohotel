"""
Tests for rhohotel.rhocom_hotel.api.night_audit_summary_report
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
    utils_stub.flt = lambda v, p=2: float(v or 0)
    utils_stub.cint = lambda v: int(v or 0)
    utils_stub.cstr = lambda v: str(v or "")
    utils_stub.get_datetime = lambda v: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import night_audit_summary_report as nar


class TestIsRoomRevenueSource(unittest.TestCase):
    def test_room_source(self):
        self.assertTrue(nar._is_room_revenue_source("room charge"))
        self.assertTrue(nar._is_room_revenue_source("accommodation"))
        self.assertTrue(nar._is_room_revenue_source("Night Audit"))

    def test_empty_is_room(self):
        self.assertTrue(nar._is_room_revenue_source(""))
        self.assertTrue(nar._is_room_revenue_source(None))

    def test_non_room_source(self):
        self.assertFalse(nar._is_room_revenue_source("restaurant"))
        self.assertFalse(nar._is_room_revenue_source("POS Sale"))


class TestIsFnbRevenueSource(unittest.TestCase):
    def test_fnb(self):
        self.assertTrue(nar._is_fnb_revenue_source("restaurant order"))
        self.assertTrue(nar._is_fnb_revenue_source("bar tab"))
        self.assertTrue(nar._is_fnb_revenue_source("POS"))

    def test_non_fnb(self):
        self.assertFalse(nar._is_fnb_revenue_source("room charge"))
        self.assertFalse(nar._is_fnb_revenue_source(""))


class TestGetNightAuditSummaryReport(unittest.TestCase):
    def test_returns_required_keys(self):
        with (
            patch.object(nar, "_get_sales_invoice_rows", return_value=[]),
            patch.object(nar, "_get_pos_invoice_rows", return_value=[]),
            patch.object(nar, "_get_payment_entry_rows", return_value=[]),
            patch.object(nar, "_get_room_stats", return_value={
                "total_rooms": 0, "occupied_rooms": 0,
                "vacant_rooms": 0, "occupancy_percent": 0
            }),
            patch.object(nar, "_get_arrival_departure_counts", return_value={
                "arrivals": 0, "departures": 0, "stayovers": 0
            }),
            patch.object(nar, "_get_pos_profiles", return_value=[]),
        ):
            result = nar.get_night_audit_summary_report()
        required = {"rows", "payment_breakdown", "revenue_breakdown",
                    "exceptions", "pos_profiles", "summary"}
        self.assertTrue(required.issubset(result.keys()))

    def test_summary_keys_present(self):
        with (
            patch.object(nar, "_get_sales_invoice_rows", return_value=[]),
            patch.object(nar, "_get_pos_invoice_rows", return_value=[]),
            patch.object(nar, "_get_payment_entry_rows", return_value=[]),
            patch.object(nar, "_get_room_stats", return_value={
                "total_rooms": 10, "occupied_rooms": 5,
                "vacant_rooms": 5, "occupancy_percent": 50.0
            }),
            patch.object(nar, "_get_arrival_departure_counts", return_value={
                "arrivals": 2, "departures": 1, "stayovers": 3
            }),
            patch.object(nar, "_get_pos_profiles", return_value=[]),
        ):
            result = nar.get_night_audit_summary_report()
        summary_keys = {
            "audit_date", "room_revenue", "pos_revenue", "other_revenue",
            "total_revenue", "total_tax", "total_discount", "total_paid",
            "total_outstanding", "transaction_count", "pe_count",
            "exceptions_count", "total_rooms", "occupied_rooms",
            "arrivals", "departures", "stayovers"
        }
        self.assertTrue(summary_keys.issubset(result["summary"].keys()))

    def test_revenue_type_filter(self):
        invoice_row = {
            "date": "2026-05-01", "transaction_type": "POS Revenue",
            "reference": "SINV-001", "guest": "John",
            "room": "", "reservation": "", "pos_profile": "",
            "payment_mode": "Cash", "net_amount": 5000, "tax": 0,
            "discount": 0, "gross_amount": 5000, "paid_amount": 5000,
            "outstanding_amount": 0, "status": "Paid"
        }
        with (
            patch.object(nar, "_get_sales_invoice_rows", return_value=[invoice_row]),
            patch.object(nar, "_get_pos_invoice_rows", return_value=[]),
            patch.object(nar, "_get_payment_entry_rows", return_value=[]),
            patch.object(nar, "_get_room_stats", return_value={
                "total_rooms": 0, "occupied_rooms": 0, "vacant_rooms": 0, "occupancy_percent": 0
            }),
            patch.object(nar, "_get_arrival_departure_counts", return_value={
                "arrivals": 0, "departures": 0, "stayovers": 0
            }),
            patch.object(nar, "_get_pos_profiles", return_value=[]),
        ):
            result = nar.get_night_audit_summary_report()
        self.assertEqual(result["summary"]["pos_revenue"], 5000.0)
        self.assertEqual(result["summary"]["room_revenue"], 0.0)

    def test_exceptions_generated_for_outstanding(self):
        invoice_row = {
            "date": "2026-05-01", "transaction_type": "Room Revenue",
            "reference": "SINV-001", "guest": "John",
            "room": "CI-001", "reservation": "", "pos_profile": "",
            "payment_mode": "", "net_amount": 5000, "tax": 0,
            "discount": 0, "gross_amount": 5000, "paid_amount": 0,
            "outstanding_amount": 5000, "status": "Unpaid"
        }
        with (
            patch.object(nar, "_get_sales_invoice_rows", return_value=[invoice_row]),
            patch.object(nar, "_get_pos_invoice_rows", return_value=[]),
            patch.object(nar, "_get_payment_entry_rows", return_value=[]),
            patch.object(nar, "_get_room_stats", return_value={
                "total_rooms": 0, "occupied_rooms": 0, "vacant_rooms": 0, "occupancy_percent": 0
            }),
            patch.object(nar, "_get_arrival_departure_counts", return_value={
                "arrivals": 0, "departures": 0, "stayovers": 0
            }),
            patch.object(nar, "_get_pos_profiles", return_value=[]),
        ):
            result = nar.get_night_audit_summary_report()
        self.assertEqual(result["summary"]["exceptions_count"], 1)
        self.assertEqual(result["exceptions"][0]["type"], "Outstanding Balance")


if __name__ == "__main__":
    unittest.main()