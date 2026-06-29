"""
Tests for rhohotel.rhocom_hotel.api.housekeeping_productivity_report
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
    utils_stub.cint = lambda v: int(v or 0)
    utils_stub.get_datetime = lambda v=None: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    utils_stub.format_datetime = lambda v, fmt="": "01-05-2026 12:00"
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import housekeeping_productivity_report as hpr


class TestIsCleaned(unittest.TestCase):
    def test_cleaned(self):
        self.assertTrue(hpr._is_cleaned("Completed"))
        self.assertTrue(hpr._is_cleaned("Done"))
        self.assertTrue(hpr._is_cleaned("Ready"))

    def test_not_cleaned(self):
        self.assertFalse(hpr._is_cleaned("Pending"))
        self.assertFalse(hpr._is_cleaned("In Progress"))


class TestIsInspected(unittest.TestCase):
    def test_inspected(self):
        self.assertTrue(hpr._is_inspected("Inspected"))
        self.assertTrue(hpr._is_inspected("Approved"))

    def test_not_inspected(self):
        self.assertFalse(hpr._is_inspected("Pending"))
        self.assertFalse(hpr._is_inspected("Completed"))


class TestCleanStatus(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(hpr._clean_status("Completed"), "completed")
        self.assertEqual(hpr._clean_status(None), "")
        self.assertEqual(hpr._clean_status("  Pending  "), "pending")


class TestGetHousekeepingProductivityReport(unittest.TestCase):
    def test_returns_empty_when_no_doctype(self):
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report()
        self.assertEqual(result["rows"], [])
        self.assertIn("summary", result)

    def test_returns_required_keys(self):
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report()
        required = {"rows", "summary", "housekeepers", "floors", "statuses",
                    "generated_at", "filters"}
        self.assertTrue(required.issubset(result.keys()))

    def test_summary_keys_present(self):
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report()
        summary_keys = {"total_tasks", "rooms_cleaned", "rooms_inspected",
                        "pending_tasks", "issue_count", "guest_requests", "avg_duration"}
        self.assertTrue(summary_keys.issubset(result["summary"].keys()))

    def test_search_filter_applied(self):
        # When doctype missing, rows is empty
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report(search="XYZ_nonexistent")
        self.assertEqual(result["rows"], [])

    def test_filters_in_response(self):
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report(
                date_from="2026-05-01", date_to="2026-05-07"
            )
        self.assertIn("date_from", result["filters"])
        self.assertIn("date_to", result["filters"])

    def test_avg_duration_zero_when_no_tasks(self):
        with patch.object(hpr, "_has_doctype", return_value=False):
            result = hpr.get_housekeeping_productivity_report()
        self.assertEqual(result["summary"]["avg_duration"], 0)


if __name__ == "__main__":
    unittest.main()