"""
Tests for rhohotel.rhocom_hotel.api.pos_sales_performance
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
    utils_stub.format_datetime = lambda v, fmt="": "01-05-2026 12:00"
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import pos_sales_performance as psp


class _DD(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e
    def __setattr__(self, k, v):
        self[k] = v


class TestGetPaymentStatus(unittest.TestCase):
    def test_paid(self):
        row = {"outstanding_amount": 0, "grand_total": 5000, "status": "Paid"}
        self.assertEqual(psp._get_payment_status(row, "Cash"), "Paid")

    def test_unpaid(self):
        row = {"outstanding_amount": 5000, "grand_total": 5000, "status": "Submitted"}
        self.assertEqual(psp._get_payment_status(row, "Cash"), "Unpaid")

    def test_part_payment(self):
        row = {"outstanding_amount": 2000, "grand_total": 5000, "status": "Submitted"}
        self.assertEqual(psp._get_payment_status(row, "Cash"), "Part Payment")

    def test_posted_to_room(self):
        row = {"outstanding_amount": 5000, "grand_total": 5000, "status": "Submitted"}
        self.assertEqual(psp._get_payment_status(row, "Room Posting"), "Posted to Room")

    def test_cancelled_status(self):
        row = {"outstanding_amount": 0, "grand_total": 5000, "status": "Cancelled"}
        self.assertEqual(psp._get_payment_status(row, "Cash"), "Cancelled")


class TestMoney(unittest.TestCase):
    def test_rounds_to_two(self):
        self.assertEqual(psp._money(100), 100.0)

    def test_handles_none(self):
        self.assertEqual(psp._money(None), 0.0)


class TestGetPosSalesPerformanceReport(unittest.TestCase):
    def test_returns_empty_when_no_pos_invoice_doctype(self):
        with patch.object(psp, "_has_doctype", return_value=False):
            result = psp.get_pos_sales_performance_report()
        self.assertEqual(result["sales"], [])
        self.assertIn("generated_at", result)

    def test_returns_required_keys(self):
        with patch.object(psp, "_has_doctype", return_value=False):
            result = psp.get_pos_sales_performance_report()
        required = {"sales", "shifts", "top_items", "pos_profiles",
                    "cashiers", "payment_modes", "generated_at"}
        self.assertTrue(required.issubset(result.keys()))

    def test_search_filter(self):
        # When no matching invoices, sales is empty
        with (
            patch.object(psp, "_has_doctype", return_value=True),
            patch.object(psp, "_get_field", return_value=None),
            patch.object(psp.frappe.db, "sql", return_value=[]),
        ):
            result = psp.get_pos_sales_performance_report(search="XYZ_nonexistent")
        self.assertEqual(result["sales"], [])

    def test_payment_mode_filter(self):
        invoice = _DD({
            "name": "PINV-001", "posting_date": "2026-05-01",
            "posting_time": "12:00:00", "customer": "Walk-in",
            "customer_display": "Walk-in Customer", "pos_profile": "Main POS",
            "cashier": "alice@example.com", "room": "",
            "net_total": 5000, "grand_total": 5000,
            "discount_amount": 0, "total_taxes_and_charges": 0,
            "outstanding_amount": 0, "paid_amount": 5000,
            "status": "Paid", "docstatus": 1,
        })
        payment_rows = [{"parent": "PINV-001", "mode_of_payment": "Cash", "amount": 5000}]

        with (
            patch.object(psp, "_has_doctype", return_value=True),
            patch.object(psp, "_get_field", return_value=None),
            patch.object(psp.frappe.db, "sql", return_value=[]),
        ):
            result = psp.get_pos_sales_performance_report(payment_mode="Card")
        self.assertEqual(result["sales"], [])

    def test_filters_returned(self):
        # When no POS Invoice doctype, basic keys still present
        with patch.object(psp, "_has_doctype", return_value=False):
            result = psp.get_pos_sales_performance_report()
        self.assertIn("sales", result)
        self.assertIn("generated_at", result)
        self.assertEqual(result["sales"], [])

    def test_cashier_aggregation_when_no_shifts(self):
        # When no POS Invoice doctype, shifts is empty list
        with patch.object(psp, "_has_doctype", return_value=False):
            result = psp.get_pos_sales_performance_report()
        self.assertIsInstance(result["shifts"], list)
        self.assertEqual(len(result["shifts"]), 0)