import datetime
import sys
import types
import unittest
from unittest.mock import patch


if "frappe" not in sys.modules:
	frappe_stub = types.ModuleType("frappe")
	frappe_stub._ = lambda text: text
	frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
	frappe_stub.PermissionError = PermissionError
	frappe_stub.session = types.SimpleNamespace(user="owner@example.com")
	frappe_stub.db = types.SimpleNamespace()
	sys.modules["frappe"] = frappe_stub

frappe_stub = sys.modules["frappe"]
frappe_stub._ = getattr(frappe_stub, "_", lambda text: text)
frappe_stub.whitelist = getattr(frappe_stub, "whitelist", lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0])
frappe_stub.PermissionError = getattr(frappe_stub, "PermissionError", PermissionError)
frappe_stub.session = getattr(frappe_stub, "session", types.SimpleNamespace(user="owner@example.com"))
frappe_stub.get_roles = getattr(frappe_stub, "get_roles", lambda user=None: [])
frappe_stub.throw = getattr(frappe_stub, "throw", lambda message, exc=None: (_ for _ in ()).throw(exc(message) if exc else Exception(message)))
frappe_stub.get_all = getattr(frappe_stub, "get_all", lambda *args, **kwargs: [])

if "frappe.utils" not in sys.modules:
	utils_stub = types.ModuleType("frappe.utils")
	utils_stub.flt = lambda value=0, *_, **__: float(value or 0)
	utils_stub.getdate = lambda value=None: value if isinstance(value, datetime.date) else datetime.date.fromisoformat(str(value))
	utils_stub.nowdate = lambda: "2026-06-24"
	utils_stub.add_days = lambda value, days: value + datetime.timedelta(days=days)
	sys.modules["frappe.utils"] = utils_stub

utils_stub = sys.modules["frappe.utils"]
utils_stub.flt = getattr(utils_stub, "flt", lambda value=0, *_, **__: float(value or 0))
utils_stub.getdate = getattr(utils_stub, "getdate", lambda value=None: value if isinstance(value, datetime.date) else datetime.date.fromisoformat(str(value)))
utils_stub.nowdate = getattr(utils_stub, "nowdate", lambda: "2026-06-24")
utils_stub.today = getattr(utils_stub, "today", lambda: "2026-06-24")
utils_stub.add_days = getattr(utils_stub, "add_days", lambda value, days: value + datetime.timedelta(days=days))
utils_stub.now_datetime = getattr(utils_stub, "now_datetime", lambda: datetime.datetime(2026, 6, 24, 12, 0, 0))
utils_stub.add_to_date = getattr(utils_stub, "add_to_date", lambda value, **kwargs: value)
utils_stub.cstr = getattr(utils_stub, "cstr", lambda value: "" if value is None else str(value))
utils_stub.cint = getattr(utils_stub, "cint", lambda value=0, *_, **__: int(value or 0))


from rhohotel.rhocom_hotel.api import owner_dashboard as od


class FakeDB:
	def __init__(self, tables=None):
		self.tables = set(tables or [])
		self.queries = []
		self.counts = {}

	def table_exists(self, doctype):
		return doctype in self.tables

	def has_column(self, doctype, fieldname):
		return fieldname in {
			("Sales Invoice", "custom_invoice_source"),
			("Sales Invoice", "custom_hotel_room_check_in"),
			("Hotel Room", "housekeeping_status"),
			("Hotel Room Check In", "total_outstanding_amount"),
			("Housekeeping Task", "status"),
			("Housekeeping Task", "creation"),
			("Maintenance Task", "status"),
			("Maintenance Task", "creation"),
			("Hall Booking", "customer_name"),
			("Hall Booking", "hall"),
			("Hall Booking", "event_type"),
			("Hall Booking", "event_status"),
			("Hall Booking", "payment_status"),
			("Hall Booking", "net_total"),
			("Hall Booking", "total_amount"),
		}

	def count(self, doctype, filters=None):
		return self.counts.get((doctype, tuple(sorted((filters or {}).items()))), 0)

	def sql(self, query, values=None, as_dict=False):
		self.queries.append((query, values, as_dict))
		if "FROM `tabPayment Ledger Entry`" in query and "posting_date BETWEEN" not in query:
			return [types.SimpleNamespace(total_invoiced=1000, total_collected=400, total_outstanding=600)]
		if "FROM `tabPayment Ledger Entry`" in query and "posting_date BETWEEN" in query:
			return [types.SimpleNamespace(period_invoiced=300, period_collected=125, period_outstanding=175)]
		if "SUM(outstanding_amount) AS total_overdue" in query:
			return [types.SimpleNamespace(total_overdue=225)]
		if "ABS(SUM(outstanding_amount)) AS amount" in query:
			return [types.SimpleNamespace(cnt=2, amount=50)]
		if "FROM `tabPayment Entry`" in query and "SUM(unallocated_amount)" in query:
			return [types.SimpleNamespace(cnt=3, amount=75)]
		if "FROM `tabGL Entry`" in query:
			return [
				types.SimpleNamespace(root_type="Income", account="Room Revenue", income_amount=1200, expense_amount=-1200),
				types.SimpleNamespace(root_type="Income", account="Restaurant Revenue", income_amount=300, expense_amount=-300),
				types.SimpleNamespace(root_type="Expense", account="Staff Salary", income_amount=-350, expense_amount=350),
				types.SimpleNamespace(root_type="Expense", account="Utilities - Power", income_amount=-125, expense_amount=125),
			]
		if "FROM `tabPayment Entry`" in query and "GROUP BY payment_type" in query:
			return [
				types.SimpleNamespace(payment_type="Receive", mode_of_payment="Cash", amount=650, entry_count=4),
				types.SimpleNamespace(payment_type="Receive", mode_of_payment="Bank", amount=400, entry_count=2),
				types.SimpleNamespace(payment_type="Pay", mode_of_payment="Bank", amount=225, entry_count=1),
			]
		if "FROM `tabSales Invoice`" in query and "GROUP BY category" in query:
			return [
				types.SimpleNamespace(category="Rooms", amount=700, invoice_count=7),
				types.SimpleNamespace(category="POS", amount=200, invoice_count=4),
			]
		if "FROM `tabHotel Room`" in query and "GROUP BY status" in query:
			return [
				types.SimpleNamespace(status="Occupied", cnt=4),
				types.SimpleNamespace(status="Vacant", cnt=6),
				types.SimpleNamespace(status="Maintenance", cnt=1),
			]
		if "FROM `tabHotel Room`" in query and "housekeeping_status = 'Dirty'" in query:
			return [types.SimpleNamespace(cnt=2)]
		if "COUNT(*) AS room_nights" in query:
			return [types.SimpleNamespace(room_nights=8)]
		if "FROM `tabPOS Invoice`" in query and "posting_date AS revenue_date" in query:
			return [types.SimpleNamespace(revenue_date=datetime.date(2026, 6, 24), revenue=120, source="POS")]
		if "FROM `tabPOS Invoice`" in query and "SUM(grand_total) AS amount" in query and "GROUP BY" not in query:
			return [types.SimpleNamespace(amount=200)]
		if "FROM `tabPOS Closing Entry`" in query:
			return [types.SimpleNamespace(amount=15)]
		if "FROM `tabPOS Invoice`" in query and "GROUP BY pos_profile" in query:
			return [types.SimpleNamespace(outlet="Restaurant", amount=200)]
		if "FROM `tabHotel Reservation`" in query and "GROUP BY channel" in query:
			return [types.SimpleNamespace(channel="OTA", bookings=3, room_nights=6, gross_revenue=900, commission=90)]
		if "FROM `tabHotel Reservation`" in query and "from_date AS revenue_date" in query:
			return [types.SimpleNamespace(revenue_date=datetime.date(2026, 6, 24), revenue=500, source="Reservations")]
		if "FROM `tabHotel Reservation`" in query:
			return [types.SimpleNamespace(cnt=5)]
		if "FROM `tabHotel Room Check In`" in query and "GROUP BY room_type" in query:
			return [types.SimpleNamespace(room_type="Deluxe", stays=2, room_nights=4, revenue=600)]
		if "FROM `tabHotel Room Check In`" in query:
			return [types.SimpleNamespace(cnt=2)]
		if "FROM `tabHotel Guest`" in query:
			return [types.SimpleNamespace(customer="CORP-1")]
		if "FROM `tabSales Invoice`" in query and "GROUP BY customer" in query:
			return [types.SimpleNamespace(customer="CORP-1", invoice_count=2, outstanding=500, overdue=300, oldest_due_date=datetime.date(2026, 6, 1))]
		if "FROM `tabHousekeeping Task`" in query:
			return [types.SimpleNamespace(cnt=6)]
		if "FROM `tabMaintenance Task`" in query:
			return [types.SimpleNamespace(cnt=1)]
		if "FROM `tabHall Booking`" in query and "GROUP BY event_status" in query:
			return [
				types.SimpleNamespace(event_status="Scheduled", cnt=2, amount=800, unpaid_amount=300),
				types.SimpleNamespace(event_status="Completed", cnt=1, amount=400, unpaid_amount=0),
			]
		if "FROM `tabHall Booking`" in query and "ORDER BY start_datetime ASC" in query:
			return [types.SimpleNamespace(name="HB-1", customer_name="CORP-1", hall="Main Hall", event_type="Meeting", start_datetime=datetime.datetime(2026, 6, 24, 10, 0), event_status="Scheduled", payment_status="Partly Paid", amount=800)]
		if "FROM `tabHall Booking`" in query and "DATE(start_datetime) AS revenue_date" in query:
			return [types.SimpleNamespace(revenue_date=datetime.date(2026, 6, 24), revenue=300, source="Halls")]
		if "FROM `tabHall Booking`" in query:
			return [types.SimpleNamespace(cnt=3)]
		if "GROUP BY posting_date" in query:
			return [types.SimpleNamespace(posting_date=datetime.date(2026, 6, 24), revenue=900, outstanding=100)]
		raise AssertionError(f"Unexpected SQL: {query}")


class TestOwnerDashboard(unittest.TestCase):
	def test_permission_guard_allows_owner_role(self):
		with patch.object(od.frappe, "get_roles", return_value=["Hotel Owner"]):
			od._require_owner_access()

	def test_permission_guard_rejects_non_owner(self):
		with (
			patch.object(od.frappe, "get_roles", return_value=["Hotel Receptionist"]),
			patch.object(od.frappe, "throw", side_effect=PermissionError("blocked")),
		):
			with self.assertRaises(PermissionError):
				od._require_owner_access()

	def test_finance_uses_ple_and_date_filters(self):
		fake_db = FakeDB({"Payment Ledger Entry", "Sales Invoice", "Payment Entry"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_finance(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(result["total_invoiced"], 1000)
		self.assertEqual(result["total_collected"], 400)
		self.assertEqual(result["collection_rate"], 40.0)
		self.assertEqual(result["period_invoiced"], 300)
		self.assertEqual(result["total_overdue"], 225)
		period_query = next(query for query, _values, _as_dict in fake_db.queries if "period_invoiced" in query)
		self.assertIn("posting_date BETWEEN", period_query)

	def test_empty_tables_return_zero_sections(self):
		fake_db = FakeDB(set())
		with patch.object(od.frappe, "db", fake_db):
			finance = od._build_finance(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))
			cash = od._build_cash_control(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))
			profitability = od._build_profitability(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))
			cashflow = od._build_cashflow(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(finance["total_invoiced"], 0)
		self.assertEqual(cash["pos_sales"], 0)
		self.assertEqual(cash["open_drafts"], 0)
		self.assertEqual(profitability["net_profit"], 0)
		self.assertEqual(cashflow["net_cashflow"], 0)

	def test_profitability_uses_gl_income_and_expense_accounts(self):
		fake_db = FakeDB({"GL Entry", "Account"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_profitability(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(result["accounting_revenue"], 1500)
		self.assertEqual(result["operating_expenses"], 475)
		self.assertEqual(result["net_profit"], 1025)
		self.assertEqual(result["profit_margin"], 68.3)
		self.assertEqual(result["cost_signals"]["payroll"], 350)
		self.assertEqual(result["cost_signals"]["utilities"], 125)

	def test_cashflow_groups_payment_modes(self):
		fake_db = FakeDB({"Payment Entry"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_cashflow(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(result["cash_in"], 1050)
		self.assertEqual(result["cash_out"], 225)
		self.assertEqual(result["net_cashflow"], 825)
		bank = next(row for row in result["payment_modes"] if row["mode"] == "Bank")
		self.assertEqual(bank["net"], 175)

	def test_historical_occupancy_does_not_show_current_room_status(self):
		fake_db = FakeDB({"Hotel Room", "Hotel Room Check In"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_occupancy(datetime.date(2025, 1, 1), datetime.date(2025, 12, 31), {"period_invoiced": 0})

		self.assertEqual(result["total_rooms"], 11)
		self.assertEqual(result["occupied"], 0)
		self.assertEqual(result["vacant"], 0)
		self.assertEqual(result["maintenance"], 0)

	def test_hall_bookings_aggregate_period_events(self):
		fake_db = FakeDB({"Hall Booking"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_hall_bookings(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(result["total_bookings"], 3)
		self.assertEqual(result["scheduled"], 2)
		self.assertEqual(result["completed"], 1)
		self.assertEqual(result["revenue"], 1200)
		self.assertEqual(result["unpaid_amount"], 300)
		self.assertEqual(result["events"][0]["hall"], "Main Hall")

	def test_trends_fall_back_to_operational_revenue_sources(self):
		fake_db = FakeDB({"Hotel Reservation", "POS Invoice", "Hall Booking"})
		with patch.object(od.frappe, "db", fake_db):
			result = od._build_trends(datetime.date(2026, 6, 18), datetime.date(2026, 6, 24))

		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["revenue"], 920)
		self.assertIn("Halls", result[0]["source"])


if __name__ == "__main__":
	unittest.main()
