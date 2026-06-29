"""
Tests for rhohotel.rhocom_hotel.api.corporate_account_statement
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
    frappe_stub.get_doc = lambda *a, **k: None
    frappe_stub.new_doc = lambda *a, **k: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    frappe_stub.log_error = lambda *a, **k: None
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.session = types.SimpleNamespace(user="Administrator")
    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *a, **k: [],
        count=lambda *a, **k: 0,
        get_value=lambda *a, **k: None,
        set_value=lambda *a, **k: None,
        exists=lambda *a, **k: True,
        has_column=lambda *a, **k: True,
        commit=lambda: None,
        rollback=lambda: None,
    )
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.getdate = lambda v: v
    utils_stub.add_days = lambda d, n: d
    utils_stub.flt = lambda v, p=2: float(v or 0)
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import corporate_account_statement as cas


class DotDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e
    def __setattr__(self, key, value):
        self[key] = value


class TestPaginate(unittest.TestCase):
    def test_returns_correct_slice(self):
        data = list(range(10))
        result = cas._paginate(data, page=2, page_size=3)
        self.assertEqual(result["rows"], [3, 4, 5])
        self.assertEqual(result["total"], 10)
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["total_pages"], 4)

    def test_page_minimum_is_one(self):
        data = [1, 2, 3]
        result = cas._paginate(data, page=0, page_size=2)
        self.assertEqual(result["page"], 1)

    def test_empty_data_returns_total_pages_one(self):
        result = cas._paginate([], page=1, page_size=10)
        self.assertEqual(result["total_pages"], 1)
        self.assertEqual(result["total"], 0)

    def test_invalid_page_defaults(self):
        result = cas._paginate([1, 2], page="bad", page_size="bad")
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 10)

    def test_page_beyond_total_clamped(self):
        data = [1, 2, 3]
        result = cas._paginate(data, page=99, page_size=10)
        self.assertEqual(result["page"], 1)


class TestGetCustomerDisplay(unittest.TestCase):
    def test_returns_unknown_for_empty(self):
        self.assertEqual(cas._get_customer_display(""), "Unknown")
        self.assertEqual(cas._get_customer_display(None), "Unknown")

    def test_returns_customer_name_when_found(self):
        with (
            patch.object(cas, "_has_doctype", return_value=True),
            patch.object(cas.frappe.db, "exists", return_value=True),
            patch.object(cas.frappe.db, "get_value", return_value="Acme Corp"),
        ):
            result = cas._get_customer_display("CUST-001")
        self.assertEqual(result, "Acme Corp")

    def test_falls_back_to_customer_id(self):
        with (
            patch.object(cas, "_has_doctype", return_value=True),
            patch.object(cas.frappe.db, "exists", return_value=True),
            patch.object(cas.frappe.db, "get_value", return_value=None),
        ):
            result = cas._get_customer_display("CUST-001")
        self.assertEqual(result, "CUST-001")


class TestGetCorporateCustomers(unittest.TestCase):
    def test_returns_empty_when_no_hotel_guest_doctype(self):
        with patch.object(cas, "_has_doctype", return_value=False):
            result = cas._get_corporate_customers()
        self.assertEqual(result, [])

    def test_returns_empty_when_fields_missing(self):
        with (
            patch.object(cas, "_has_doctype", return_value=True),
            patch.object(cas, "_get_field", return_value=None),
        ):
            result = cas._get_corporate_customers()
        self.assertEqual(result, [])

    def test_returns_customer_list(self):
        rows = [DotDict(customer="CUST-001"), DotDict(customer="CUST-002")]
        with (
            patch.object(cas, "_has_doctype", return_value=True),
            patch.object(cas, "_get_field", return_value="guest_type"),
            patch.object(cas.frappe.db, "sql", return_value=rows),
        ):
            result = cas._get_corporate_customers()
        self.assertEqual(result, ["CUST-001", "CUST-002"])


class TestGetCorporateAccountStatement(unittest.TestCase):
    def test_returns_empty_when_no_corporate_customers(self):
        with patch.object(cas, "_get_corporate_customers", return_value=[]):
            result = cas.get_corporate_account_statement()
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["customers"], [])
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["customer_count"], 0)

    def test_response_has_required_keys(self):
        with patch.object(cas, "_get_corporate_customers", return_value=[]):
            result = cas.get_corporate_account_statement()
        required = {"rows", "customers", "account_summary", "summary",
                    "account_summary_total", "account_summary_page",
                    "account_summary_page_size", "account_summary_total_pages"}
        self.assertTrue(required.issubset(result.keys()))

    def test_summary_keys_present(self):
        with patch.object(cas, "_get_corporate_customers", return_value=[]):
            result = cas.get_corporate_account_statement()
        summary_keys = {"opening_balance", "total_debit", "total_credit",
                        "closing_balance", "transaction_count", "customer_count"}
        self.assertTrue(summary_keys.issubset(result["summary"].keys()))

    def test_transaction_type_filter_applied(self):
        customers = ["CUST-001"]
        ple_row = DotDict(
            name="PLE-001", creation="2026-05-01 10:00:00",
            posting_date="2026-05-01", party="CUST-001",
            voucher_type="Sales Invoice", voucher_no="SINV-001",
            against_voucher_type=None, against_voucher_no=None,
            amount=1000, remarks=""
        )
        with (
            patch.object(cas, "_get_corporate_customers", return_value=customers),
            patch.object(cas, "_get_corporate_ple_rows", return_value=[ple_row]),
            patch.object(cas, "_get_voucher_meta_for_corporate_ledger", return_value={"sales_invoice": {}, "payment_entry": {}, "journal_entry": {}}),
            patch.object(cas, "_get_customer_name_map", return_value={"CUST-001": "Acme Corp"}),
            patch.object(cas, "_get_corporate_opening_balance", return_value=0),
            patch.object(cas, "_get_customers", return_value=[]),
        ):
            result = cas.get_corporate_account_statement(transaction_type="Payment Entry")
        # Sales Invoice row should be filtered out
        self.assertEqual(result["rows"], [])

    def test_debit_positive_credit_negative_amount(self):
        customers = ["CUST-001"]
        ple_row = DotDict(
            name="PLE-001", creation="2026-05-01 10:00:00",
            posting_date="2026-05-01", party="CUST-001",
            voucher_type="Sales Invoice", voucher_no="SINV-001",
            against_voucher_type=None, against_voucher_no=None,
            amount=500, remarks=""
        )
        with (
            patch.object(cas, "_get_corporate_customers", return_value=customers),
            patch.object(cas, "_get_corporate_ple_rows", return_value=[ple_row]),
            patch.object(cas, "_get_voucher_meta_for_corporate_ledger", return_value={"sales_invoice": {}, "payment_entry": {}, "journal_entry": {}}),
            patch.object(cas, "_get_customer_name_map", return_value={"CUST-001": "Acme Corp"}),
            patch.object(cas, "_get_corporate_opening_balance", return_value=0),
            patch.object(cas, "_get_customers", return_value=[]),
        ):
            result = cas.get_corporate_account_statement()
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["rows"][0]["debit"], 500)
        self.assertEqual(result["rows"][0]["credit"], 0)


class TestCorporateTransactionType(unittest.TestCase):
    def test_sales_invoice_positive(self):
        ple = DotDict(voucher_type="Sales Invoice", voucher_no="SINV-001", amount=100, remarks="")
        meta = {"sales_invoice": {"SINV-001": {"is_return": 0}}, "payment_entry": {}, "journal_entry": {}}
        self.assertEqual(cas._corporate_transaction_type(ple, meta), "Sales Invoice")

    def test_sales_invoice_return(self):
        ple = DotDict(voucher_type="Sales Invoice", voucher_no="SINV-001", amount=-100, remarks="")
        meta = {"sales_invoice": {"SINV-001": {"is_return": 1}}, "payment_entry": {}, "journal_entry": {}}
        self.assertEqual(cas._corporate_transaction_type(ple, meta), "Credit Note")

    def test_payment_entry(self):
        ple = DotDict(voucher_type="Payment Entry", voucher_no="PE-001", amount=-100, remarks="")
        meta = {"sales_invoice": {}, "payment_entry": {}, "journal_entry": {}}
        self.assertEqual(cas._corporate_transaction_type(ple, meta), "Payment Entry")

    def test_journal_entry_bill_transfer(self):
        ple = DotDict(voucher_type="Journal Entry", voucher_no="JE-001", amount=100, remarks="bill transfer")
        meta = {"sales_invoice": {}, "payment_entry": {}, "journal_entry": {"JE-001": {"remarks": ""}}}
        self.assertEqual(cas._corporate_transaction_type(ple, meta), "Bill Transfer")


if __name__ == "__main__":
    unittest.main()