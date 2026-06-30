"""
Tests for rhohotel.rhocom_hotel.api.corporate_billing_statement
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
    frappe_stub.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
    frappe_stub.get_all = lambda *a, **k: []
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
    utils_stub.date_diff = lambda a, b: 0
    utils_stub.flt = lambda v, p=2: float(v or 0)
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import corporate_billing_statement as cbs


class TestAgingBucket(unittest.TestCase):
    def test_current(self):
        self.assertEqual(cbs._aging_bucket(0), "Current")
        self.assertEqual(cbs._aging_bucket(-5), "Current")

    def test_1_to_30(self):
        self.assertEqual(cbs._aging_bucket(1), "1-30")
        self.assertEqual(cbs._aging_bucket(30), "1-30")

    def test_31_to_60(self):
        self.assertEqual(cbs._aging_bucket(31), "31-60")
        self.assertEqual(cbs._aging_bucket(60), "31-60")

    def test_61_to_90(self):
        self.assertEqual(cbs._aging_bucket(61), "61-90")
        self.assertEqual(cbs._aging_bucket(90), "61-90")

    def test_over_90(self):
        self.assertEqual(cbs._aging_bucket(91), "90+")
        self.assertEqual(cbs._aging_bucket(200), "90+")


class TestBillingStatus(unittest.TestCase):
    def test_paid_when_outstanding_zero(self):
        self.assertEqual(cbs._billing_status(0, "2026-01-01"), "Paid")

    def test_overdue_when_past_due_date(self):
        result = cbs._billing_status(100, "2025-01-01", as_of_date="2026-05-01")
        self.assertEqual(result, "Overdue")

    def test_unpaid_when_future_due_date(self):
        result = cbs._billing_status(100, "2099-12-31", as_of_date="2026-05-01")
        self.assertEqual(result, "Unpaid")

    def test_unpaid_when_no_due_date(self):
        result = cbs._billing_status(100, None, as_of_date="2026-05-01")
        self.assertEqual(result, "Unpaid")


class TestGetCorporateBillingStatement(unittest.TestCase):
    def test_returns_empty_when_no_sales_invoice_doctype(self):
        with patch.object(cbs, "_has_doctype", return_value=False):
            result = cbs.get_corporate_billing_statement()
        self.assertEqual(result["rows"], [])
        self.assertIn("summary", result)

    def test_returns_empty_when_no_corporate_customers(self):
        with (
            patch.object(cbs, "_has_doctype", return_value=True),
            patch.object(cbs, "_get_corporate_customers", return_value=[]),
        ):
            result = cbs.get_corporate_billing_statement()
        self.assertEqual(result["rows"], [])

    def test_response_has_required_keys(self):
        with patch.object(cbs, "_has_doctype", return_value=False):
            result = cbs.get_corporate_billing_statement()
        required = {
            "rows", "companies", "company_summary", "company_summary_total",
            "company_summary_page", "company_summary_page_size",
            "company_summary_total_pages", "aging_breakdown",
            "aging_breakdown_total", "aging_breakdown_page",
            "aging_breakdown_page_size", "aging_breakdown_total_pages", "summary"
        }
        self.assertTrue(required.issubset(result.keys()))

    def test_summary_keys_present(self):
        with patch.object(cbs, "_has_doctype", return_value=False):
            result = cbs.get_corporate_billing_statement()
        summary_keys = {
            "total_billing", "total_paid", "outstanding",
            "overdue", "invoice_count", "company_count"
        }
        self.assertTrue(summary_keys.issubset(result["summary"].keys()))

    def test_status_filter_applied(self):
        customers = ["CUST-001"]
        voucher_row = {
            "customer": "CUST-001",
            "invoice": "SINV-001",
            "posting_date": "2026-05-01",
            "billed_amount": 1000,
            "paid_amount": 0,
            "outstanding_amount": 1000,
            "customer_name": "Acme Corp",
            "due_date": "2025-01-01",
            "reference": "",
            "is_return": 0,
        }
        with (
            patch.object(cbs, "_has_doctype", return_value=True),
            patch.object(cbs, "_get_corporate_customers", return_value=customers),
            patch.object(cbs, "_get_customer_name_map", return_value={"CUST-001": "Acme Corp"}),
            patch.object(cbs.frappe.db, "sql", return_value=[voucher_row]),
        ):
            result_paid = cbs.get_corporate_billing_statement(status="Paid")
        self.assertEqual(result_paid["rows"], [])

    def test_company_summary_min_outstanding_filter(self):
        customers = ["CUST-001"]
        voucher_row = {
            "customer": "CUST-001",
            "invoice": "SINV-001",
            "posting_date": "2026-05-01",
            "billed_amount": 500,
            "paid_amount": 500,
            "outstanding_amount": 0,
            "customer_name": "Acme Corp",
            "due_date": "2099-12-31",
            "reference": "",
            "is_return": 0,
        }
        with (
            patch.object(cbs, "_has_doctype", return_value=True),
            patch.object(cbs, "_get_corporate_customers", return_value=customers),
            patch.object(cbs, "_get_customer_name_map", return_value={"CUST-001": "Acme Corp"}),
            patch.object(cbs.frappe.db, "sql", return_value=[voucher_row]),
            patch(
                "rhohotel.rhocom_hotel.api.corporate_billing_statement.nowdate",
                return_value="2026-05-01",
            ),
            patch(
                "rhohotel.rhocom_hotel.api.corporate_billing_statement.add_days",
                return_value="2026-04-01",
            ),
        ):
            result = cbs.get_corporate_billing_statement(company_summary_min_outstanding=100)
        self.assertEqual(result["company_summary"], [])


if __name__ == "__main__":
    unittest.main()