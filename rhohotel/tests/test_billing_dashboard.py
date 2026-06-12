import datetime
import sys
import types
import unittest
from unittest.mock import patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
    frappe_stub.db = types.SimpleNamespace()
    sys.modules["frappe"] = frappe_stub

if "frappe.utils" not in sys.modules:
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.flt = lambda value=0, *_, **__: float(value or 0)
    utils_stub.getdate = lambda value=None: value if isinstance(value, datetime.date) else datetime.date.fromisoformat(str(value))
    utils_stub.nowdate = lambda: "2026-06-12"
    utils_stub.add_days = lambda value, days: value + datetime.timedelta(days=days)
    sys.modules["frappe.utils"] = utils_stub


from rhohotel.rhocom_hotel.api import billing_dashboard as bd


class FakeDB:
    def __init__(self):
        self.queries = []

    def sql(self, query, values=None, as_dict=False):
        self.queries.append((query, values, as_dict))

        if "FROM `tabPayment Ledger Entry`" in query and "AND party IN %(c)s" in query:
            return [types.SimpleNamespace(invoiced=0, collected=0, outstanding=0)]
        if "FROM `tabPayment Ledger Entry`" in query and "AND party NOT IN %(c)s" in query:
            return [types.SimpleNamespace(invoiced=0, collected=0, outstanding=0)]
        if "FROM `tabPayment Ledger Entry`" in query:
            return [types.SimpleNamespace(total_invoiced=1000, total_collected=250, total_outstanding=750)]
        if "status = 'Overdue'" in query:
            return [types.SimpleNamespace(overdue=500)]
        if "ABS(SUM(outstanding_amount)) AS amount" in query:
            return [types.SimpleNamespace(cnt=0, amount=0)]
        if "COUNT(*) AS invoices_in_range" in query:
            return [types.SimpleNamespace(invoices_in_range=2, invoiced_in_range=700, outstanding_in_range=450)]
        if "FROM `tabPayment Entry`" in query:
            return [types.SimpleNamespace(cnt=0)]

        raise AssertionError(f"Unexpected SQL: {query}")

    def exists(self, *args, **kwargs):
        return False


class TestBillingDashboardStats(unittest.TestCase):
    def test_overdue_matches_sales_invoice_overdue_filter(self):
        fake_db = FakeDB()

        with patch.object(bd.frappe, "db", fake_db):
            stats = bd._build_stats(
                datetime.date(2026, 6, 5),
                datetime.date(2026, 6, 12),
                datetime.date(2026, 6, 12),
                [],
            )

        overdue_query = next(query for query, _values, _as_dict in fake_db.queries if "status = 'Overdue'" in query)

        self.assertIn("SUM(outstanding_amount)", overdue_query)
        self.assertIn("status = 'Overdue'", overdue_query)
        self.assertEqual(stats["total_overdue"], 500)
        self.assertEqual(stats["total_current"], 250)

    def test_invoices_in_period_excludes_zero_value_invoices(self):
        fake_db = FakeDB()

        with patch.object(bd.frappe, "db", fake_db):
            stats = bd._build_stats(
                datetime.date(2026, 6, 5),
                datetime.date(2026, 6, 12),
                datetime.date(2026, 6, 12),
                [],
            )

        period_query = next(query for query, _values, _as_dict in fake_db.queries if "COUNT(*) AS invoices_in_range" in query)

        self.assertIn("grand_total > 0", period_query)
        self.assertEqual(stats["invoices_in_range"], 2)
        self.assertEqual(stats["invoiced_in_range"], 700)

    def test_invoice_register_row_preserves_credit_note_balance(self):
        row = types.SimpleNamespace(
            name="ACC-SINV-RET-0001",
            customer="CUST-001",
            customer_name="Guest One",
            room_number="",
            invoice_source="",
            item_groups="",
            posting_date=datetime.date(2026, 6, 10),
            due_date=datetime.date(2026, 6, 10),
            grand_total=-120,
            outstanding_amount=-120,
            is_return=1,
            status="Return",
        )

        result = bd._invoice_register_row(row)

        self.assertEqual(result["type"], "Credit Note")
        self.assertEqual(result["status"], "Credit Note")
        self.assertEqual(result["amount"], -120)
        self.assertEqual(result["balance"], -120)

    def test_invoice_status_keeps_settled_credit_note_paid(self):
        self.assertEqual(bd._invoice_status("Paid", 0, None, -120, is_return=True), "Paid")


if __name__ == "__main__":
    unittest.main()
