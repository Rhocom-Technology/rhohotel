"""
Tests for rhohotel.rhocom_hotel.api.guest_ledger_report
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
    utils_stub.get_datetime = lambda v=None: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    utils_stub.format_datetime = lambda v, fmt="": "01-05-2026 12:00"
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import guest_ledger_report as glr


class DotDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e
    def __setattr__(self, key, value):
        self[key] = value


class TestResolveTransactionType(unittest.TestCase):
    def test_sales_invoice_positive(self):
        ple = DotDict(voucher_type="Sales Invoice", amount=100, remarks="")
        meta = DotDict()
        si = DotDict(is_return=0)
        self.assertEqual(glr._resolve_transaction_type(ple, meta, si), "Sales Invoice")

    def test_credit_note_return(self):
        ple = DotDict(voucher_type="Sales Invoice", amount=100, remarks="")
        meta = DotDict()
        si = DotDict(is_return=1)
        self.assertEqual(glr._resolve_transaction_type(ple, meta, si), "Credit Note")

    def test_credit_note_negative_amount(self):
        ple = DotDict(voucher_type="Sales Invoice", amount=-100, remarks="")
        meta = DotDict()
        si = DotDict(is_return=0)
        self.assertEqual(glr._resolve_transaction_type(ple, meta, si), "Credit Note")

    def test_payment_entry(self):
        ple = DotDict(voucher_type="Payment Entry", amount=-200, remarks="")
        meta = DotDict(remarks="")
        si = DotDict()
        self.assertEqual(glr._resolve_transaction_type(ple, meta, si), "Payment Entry")

    def test_payment_refund(self):
        ple = DotDict(voucher_type="Payment Entry", amount=200, remarks="")
        meta = DotDict(remarks="")
        si = DotDict()
        self.assertEqual(glr._resolve_transaction_type(ple, meta, si), "Payment Refund")

    def test_bill_transfer_in(self):
        ple = DotDict(voucher_type="Journal Entry", amount=100, remarks="bill transfer done")
        meta = DotDict(remarks="")
        si = DotDict()
        result = glr._resolve_transaction_type(ple, meta, si)
        self.assertEqual(result, "Bill Transfer In")

    def test_bill_transfer_out(self):
        ple = DotDict(voucher_type="Journal Entry", amount=-100, remarks="bill transfer done")
        meta = DotDict(remarks="")
        si = DotDict()
        result = glr._resolve_transaction_type(ple, meta, si)
        self.assertEqual(result, "Bill Transfer Out")


class TestRowMatchesSearch(unittest.TestCase):
    def test_matches_guest_name(self):
        row = {"guest_name": "John Doe", "date": "2026-05-01", "guest": "G-001",
               "customer": "C-001", "check_in": "", "room_number": "101",
               "transaction_type": "Invoice", "voucher_no": "SINV-001",
               "remarks": "", "checkin_status": "", "room_type": ""}
        self.assertTrue(glr._row_matches_search(row, "John"))

    def test_no_match(self):
        row = {"guest_name": "John Doe", "date": "2026-05-01", "guest": "G-001",
               "customer": "C-001", "check_in": "", "room_number": "101",
               "transaction_type": "Invoice", "voucher_no": "SINV-001",
               "remarks": "", "checkin_status": "", "room_type": ""}
        self.assertFalse(glr._row_matches_search(row, "XYZ"))

    def test_empty_search_always_matches(self):
        self.assertTrue(glr._row_matches_search({}, ""))
        self.assertTrue(glr._row_matches_search({}, None))


class TestFilterRows(unittest.TestCase):
    def test_checkin_status_filter(self):
        rows = [
            {"checkin_status": "Checked In", "room_type": "Deluxe"},
            {"checkin_status": "Checked Out", "room_type": "Deluxe"},
        ]
        result = glr._filter_rows(rows, checkin_status="Checked In")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["checkin_status"], "Checked In")

    def test_room_type_filter(self):
        rows = [
            {"checkin_status": "Checked In", "room_type": "Deluxe"},
            {"checkin_status": "Checked In", "room_type": "Standard"},
        ]
        result = glr._filter_rows(rows, room_type="Standard")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["room_type"], "Standard")


class TestGetGuestLedgerReport(unittest.TestCase):
    def test_returns_empty_when_no_customers(self):
        with patch.object(glr, "_get_guest_profiles", return_value=[]):
            result = glr.get_guest_ledger_report()
        self.assertEqual(result["rows"], [])
        self.assertIn("summary", result)

    def test_response_has_required_keys(self):
        with patch.object(glr, "_get_guest_profiles", return_value=[]):
            result = glr.get_guest_ledger_report()
        required = {
            "summary", "rows", "room_types", "checkin_statuses",
            "guest_options", "transaction_types", "generated_at", "filters"
        }
        self.assertTrue(required.issubset(result.keys()))

    def test_summary_keys_present(self):
        with patch.object(glr, "_get_guest_profiles", return_value=[]):
            result = glr.get_guest_ledger_report()
        summary_keys = {
            "opening_balance", "total_debit", "total_credit",
            "closing_balance", "transaction_count", "guest_count"
        }
        self.assertTrue(summary_keys.issubset(result["summary"].keys()))

    def test_returns_empty_when_no_ple_rows(self):
        guest_profiles = [DotDict(guest="G-001", guest_name="John", customer="CUST-001",
                                  phone_number="", contact_number="")]
        with (
            patch.object(glr, "_get_guest_profiles", return_value=guest_profiles),
            patch.object(glr, "_get_checkins_for_customers", return_value=[]),
            patch.object(glr, "_get_payment_ledger_rows", return_value=[]),
        ):
            result = glr.get_guest_ledger_report()
        self.assertEqual(result["rows"], [])

    def test_transaction_type_filter(self):
        guest_profiles = [DotDict(guest="G-001", guest_name="John", customer="CUST-001",
                                  phone_number="", contact_number="")]
        ple_row = DotDict(
            name="PLE-001", creation="2026-05-01 10:00:00",
            posting_date="2026-05-01", party="CUST-001",
            voucher_type="Payment Entry", voucher_no="PE-001",
            against_voucher_type=None, against_voucher_no=None,
            amount=-500, remarks=""
        )
        with (
            patch.object(glr, "_get_guest_profiles", return_value=guest_profiles),
            patch.object(glr, "_get_checkins_for_customers", return_value=[]),
            patch.object(glr, "_get_payment_ledger_rows", return_value=[ple_row]),
            patch.object(glr, "_get_voucher_meta", return_value={"sales_invoice": {}, "payment_entry": {}, "journal_entry": {}}),
        ):
            result = glr.get_guest_ledger_report(transaction_type="Sales Invoice")
        self.assertEqual(result["rows"], [])


if __name__ == "__main__":
    unittest.main()