"""
Tests for rhohotel.rhocom_hotel.api.hall_booking
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
    frappe_stub.get_doc = lambda *a, **k: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    frappe_stub.new_doc = lambda *a, **k: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.session = types.SimpleNamespace(user="Administrator")
    frappe_stub.get_roles = lambda u: ["Administrator"]
    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *a, **k: [],
        count=lambda *a, **k: 0,
        get_value=lambda *a, **k: None,
        get_all=lambda *a, **k: [],
        exists=lambda *a, **k: False,
        has_column=lambda *a, **k: True,
        commit=lambda: None,
    )
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.flt = lambda v, p=2: float(v or 0)
    utils_stub.now_datetime = lambda: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    utils_stub.get_datetime = lambda v: __import__("datetime").datetime(2026, 5, 2, 12, 0)
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import hall_booking as hb

# When running under bench run-tests, the real frappe is loaded so frappe.throw
# raises frappe.exceptions.ValidationError instead of RuntimeError.
# We catch the common base Exception to handle both cases.
_THROW_EXC = Exception


def _make_booking_doc(**kwargs):
    doc = MagicMock()
    doc.docstatus = kwargs.get("docstatus", 1)
    doc.sales_invoice = kwargs.get("sales_invoice", None)
    doc.net_total = kwargs.get("net_total", 10000)
    doc.rate = kwargs.get("rate", 5000)
    doc.total_amount = kwargs.get("total_amount", 10000)
    doc.discount_type = kwargs.get("discount_type", "Fixed Amount")
    doc.discount_amount = kwargs.get("discount_amount", 0)
    doc.get = MagicMock(return_value=[])
    doc.as_dict = MagicMock(return_value={
        "name": kwargs.get("name", "HB-001"),
        "docstatus": doc.docstatus,
        "net_total": doc.net_total,
        "event_status": "Scheduled",
        "completed_by": None,
        "completed_on": None,
    })
    doc.name = kwargs.get("name", "HB-001")
    doc.hall = kwargs.get("hall", "HALL-001")
    doc.event_status = "Scheduled"
    doc.completed_by = None
    doc.completed_on = None
    return doc


class TestPaymentStatus(unittest.TestCase):
    def test_draft(self):
        doc = _make_booking_doc(docstatus=0)
        self.assertEqual(hb._payment_status(doc), "Draft")

    def test_no_invoice(self):
        doc = _make_booking_doc(docstatus=1, sales_invoice=None)
        self.assertEqual(hb._payment_status(doc), "No Invoice")

    def test_paid(self):
        doc = _make_booking_doc(docstatus=1, sales_invoice="SINV-001")
        inv = MagicMock()
        inv.docstatus = 1
        inv.outstanding_amount = 0.0
        inv.grand_total = 10000.0

        with patch.object(hb.frappe, "get_doc", return_value=inv):
            result = hb._payment_status(doc)
        self.assertEqual(result, "Paid")

    def test_partial(self):
        doc = _make_booking_doc(docstatus=1, sales_invoice="SINV-001")
        inv = MagicMock()
        inv.docstatus = 1
        inv.outstanding_amount = 3000.0
        inv.grand_total = 10000.0

        with patch.object(hb.frappe, "get_doc", return_value=inv):
            result = hb._payment_status(doc)
        self.assertEqual(result, "Partial")

    def test_unpaid(self):
        doc = _make_booking_doc(docstatus=1, sales_invoice="SINV-001")
        inv = MagicMock()
        inv.docstatus = 1
        inv.outstanding_amount = 10000.0
        inv.grand_total = 10000.0

        with patch.object(hb.frappe, "get_doc", return_value=inv):
            result = hb._payment_status(doc)
        self.assertEqual(result, "Unpaid")


class TestDocstatusLabel(unittest.TestCase):
    def test_draft(self):
        self.assertEqual(hb._docstatus_label(0), "Draft")

    def test_confirmed(self):
        self.assertEqual(hb._docstatus_label(1), "Confirmed")

    def test_cancelled(self):
        self.assertEqual(hb._docstatus_label(2), "Cancelled")

    def test_unknown(self):
        self.assertEqual(hb._docstatus_label(99), "Unknown")


class TestComputeFinancialSummary(unittest.TestCase):
    def test_fixed_discount(self):
        doc = MagicMock()
        doc.discount_type = "Fixed Amount"
        doc.discount_amount = 1000
        doc.total_amount = 10000
        doc.rate = 5000
        doc.get = MagicMock(return_value=[])

        with patch.object(hb, "_original_hall_gross", return_value=10000):
            result = hb._compute_financial_summary(doc)

        self.assertEqual(result["hall_gross_total"], 10000)
        self.assertEqual(result["hall_discount_value"], 1000)
        self.assertEqual(result["hall_net_total"], 9000)

    def test_percentage_discount(self):
        doc = MagicMock()
        doc.discount_type = "Percentage"
        doc.discount_amount = 10
        doc.total_amount = 10000
        doc.rate = 5000
        doc.get = MagicMock(return_value=[])

        with patch.object(hb, "_original_hall_gross", return_value=10000):
            result = hb._compute_financial_summary(doc)

        self.assertEqual(result["hall_discount_value"], 1000.0)
        self.assertEqual(result["hall_net_total"], 9000.0)


class TestGetHallRate(unittest.TestCase):
    def test_returns_zero_when_no_hall(self):
        self.assertEqual(hb.get_hall_rate(None), 0)
        self.assertEqual(hb.get_hall_rate(""), 0)

    def test_returns_rate(self):
        with patch.object(hb.frappe.db, "get_value", return_value=5000):
            result = hb.get_hall_rate("HALL-001")
        self.assertEqual(result, 5000)


class TestMarkEventStatus(unittest.TestCase):
    def test_throws_on_invalid_status(self):
        with self.assertRaises(_THROW_EXC):
            hb.mark_event_status("HB-001", "InvalidStatus")

    def test_throws_when_not_submitted(self):
        doc = _make_booking_doc(docstatus=0)
        with patch.object(hb.frappe, "get_doc", return_value=doc):
            with self.assertRaises(_THROW_EXC):
                hb.mark_event_status("HB-001", "Completed")

    def test_sets_no_show(self):
        doc = _make_booking_doc(docstatus=1)
        doc.flags = MagicMock()

        with patch.object(hb.frappe, "get_doc", return_value=doc):
            result = hb.mark_event_status("HB-001", "No Show")

        self.assertEqual(doc.event_status, "No Show")
        self.assertEqual(result["event_status"], "No Show")


class TestGetBookingList(unittest.TestCase):
    def test_returns_list_with_enriched_fields(self):
        bookings = [
            {"name": "HB-001", "customer_name": "Acme", "hall": "HALL-001",
             "event_type": "Conference", "start_datetime": "2026-05-01 09:00:00",
             "end_datetime": "2026-05-01 17:00:00", "total_days": 1,
             "net_total": 10000, "docstatus": 1, "sales_invoice": "SINV-001",
             "mobile_number": ""},
        ]
        with (
            patch.object(hb.frappe.db, "get_all", return_value=bookings),
            patch.object(hb, "_get_invoice_payment_status", return_value="Paid"),
            patch.object(hb.frappe.db, "get_value", return_value="Grand Hall"),
        ):
            result = hb.get_booking_list()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["payment_status"], "Paid")
        self.assertEqual(result[0]["status_label"], "Confirmed")
        self.assertEqual(result[0]["hall_name"], "Grand Hall")


if __name__ == "__main__":
    unittest.main()