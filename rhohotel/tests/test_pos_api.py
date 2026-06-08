import sys
import types
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch


frappe_stub = sys.modules.get("frappe")
if frappe_stub is None:
	frappe_stub = types.ModuleType("frappe")
	sys.modules["frappe"] = frappe_stub


class ValidationError(Exception):
	pass


def _default_throw(message):
	raise RuntimeError(message)


def _whitelist(*args, **kwargs):
	if args and callable(args[0]):
		return args[0]

	def _decorator(fn):
		return fn

	return _decorator


if not hasattr(frappe_stub, "_"):
	frappe_stub._ = lambda text: text
if not hasattr(frappe_stub, "throw"):
	frappe_stub.throw = _default_throw
if not hasattr(frappe_stub, "whitelist"):
	frappe_stub.whitelist = _whitelist
if not hasattr(frappe_stub, "ValidationError"):
	frappe_stub.ValidationError = ValidationError
if not hasattr(frappe_stub, "get_traceback"):
	frappe_stub.get_traceback = lambda: ""
if not hasattr(frappe_stub, "log_error"):
	frappe_stub.log_error = lambda *args, **kwargs: None
if not hasattr(frappe_stub, "as_json"):
	frappe_stub.as_json = lambda value: str(value)
if not hasattr(frappe_stub, "session"):
	frappe_stub.session = types.SimpleNamespace(user="test@example.com")
if not hasattr(frappe_stub, "db"):
	frappe_stub.db = types.SimpleNamespace()

for method_name, default in {
	"sql": lambda *args, **kwargs: [],
	"exists": lambda *args, **kwargs: False,
	"get_value": lambda *args, **kwargs: None,
	"get_single_value": lambda *args, **kwargs: None,
	"has_column": lambda *args, **kwargs: False,
	"count": lambda *args, **kwargs: 0,
	"set_value": lambda *args, **kwargs: None,
	"commit": lambda *args, **kwargs: None,
}.items():
	if not hasattr(frappe_stub.db, method_name):
		setattr(frappe_stub.db, method_name, default)

if not hasattr(frappe_stub, "get_doc"):
	frappe_stub.get_doc = lambda *args, **kwargs: None
if not hasattr(frappe_stub, "get_cached_doc"):
	frappe_stub.get_cached_doc = lambda *args, **kwargs: None
if not hasattr(frappe_stub, "new_doc"):
	frappe_stub.new_doc = lambda *args, **kwargs: None
if not hasattr(frappe_stub, "get_meta"):
	frappe_stub.get_meta = lambda *args, **kwargs: types.SimpleNamespace(fields=[])

utils_stub = sys.modules.get("frappe.utils")
if utils_stub is None:
	utils_stub = types.ModuleType("frappe.utils")
	sys.modules["frappe.utils"] = utils_stub


def _flt(value, precision=None):
	result = float(value or 0)
	return round(result, precision) if precision is not None else result


def _getdate(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return datetime.strptime(str(value), "%Y-%m-%d").date()


utils_stub.flt = getattr(utils_stub, "flt", _flt)
utils_stub.cstr = getattr(utils_stub, "cstr", lambda value="": "" if value is None else str(value))
utils_stub.now_datetime = getattr(utils_stub, "now_datetime", lambda: datetime(2026, 6, 8, 9, 30, 0))
utils_stub.nowdate = getattr(utils_stub, "nowdate", lambda: "2026-06-08")
utils_stub.add_days = getattr(utils_stub, "add_days", lambda value, days: _getdate(value) + timedelta(days=days))
utils_stub.getdate = getattr(utils_stub, "getdate", _getdate)

nestedset_stub = types.ModuleType("frappe.utils.nestedset")
nestedset_stub.get_descendants_of = lambda doctype, name: []
sys.modules.setdefault("frappe.utils.nestedset", nestedset_stub)

erpnext_pos_stub = types.ModuleType("erpnext.accounts.doctype.pos_invoice.pos_invoice")
erpnext_pos_stub.get_stock_availability = lambda *args, **kwargs: (0, False, None)
sys.modules.setdefault("erpnext", types.ModuleType("erpnext"))
sys.modules.setdefault("erpnext.accounts", types.ModuleType("erpnext.accounts"))
sys.modules.setdefault("erpnext.accounts.doctype", types.ModuleType("erpnext.accounts.doctype"))
sys.modules.setdefault("erpnext.accounts.doctype.pos_invoice", types.ModuleType("erpnext.accounts.doctype.pos_invoice"))
sys.modules.setdefault("erpnext.accounts.doctype.pos_invoice.pos_invoice", erpnext_pos_stub)


from rhohotel.rhocom_hotel.api import pos as pos_api
from rhohotel.restaurant.api import kitchen as kitchen_api


class DotDict(dict):
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc

	def __setattr__(self, key, value):
		self[key] = value


class FakeDoc:
	def __init__(self, name="DOC-0001", docstatus=0, **values):
		self.name = name
		self.docstatus = docstatus
		self.flags = types.SimpleNamespace()
		self.items = []
		self.payments = []
		self.deleted = False
		self.inserted = False
		self.submitted = False
		self.grand_total = values.pop("grand_total", 0)
		for key, value in values.items():
			setattr(self, key, value)

	def append(self, table, row):
		getattr(self, table).append(DotDict(row))

	def get(self, key, default=None):
		return getattr(self, key, default)

	def set_missing_values(self):
		self.grand_total = sum(float(row.get("rate", 0)) * float(row.get("qty", 1)) for row in self.items)

	def insert(self):
		self.inserted = True
		return self

	def submit(self):
		self.submitted = True
		return self

	def delete(self):
		self.deleted = True


class TestPOSHelpers(unittest.TestCase):
	def test_extract_table_display_name_recognizes_service_points(self):
		self.assertEqual(pos_api._extract_table_display_name("Table 01"), "Table 01")
		self.assertEqual(pos_api._extract_table_display_name("bar counter"), "bar counter")
		self.assertEqual(pos_api._extract_table_display_name("Pool 2"), "Pool 2")
		self.assertIsNone(pos_api._extract_table_display_name("Regular Guest"))

	def test_room_posting_mode_prefers_room_or_credit_payment(self):
		profile = DotDict(payments=[
			DotDict(mode_of_payment="Cash"),
			DotDict(mode_of_payment="Card POS"),
			DotDict(mode_of_payment="Room Charge"),
		])

		with patch.object(pos_api.frappe.db, "get_value", return_value="Room System") as get_value:
			mode = pos_api._get_room_posting_mop(profile, ["Cash", "Card POS"])

		self.assertEqual(mode, "Room Charge")
		get_value.assert_not_called()

	def test_room_posting_mode_falls_back_to_system_room_mode_then_profile_mode(self):
		profile = DotDict(payments=[DotDict(mode_of_payment="Cash"), DotDict(mode_of_payment="Card")])

		with patch.object(pos_api.frappe.db, "get_value", return_value="Room System"):
			self.assertEqual(pos_api._get_room_posting_mop(profile, ["Cash", "Card"]), "Room System")

		with patch.object(pos_api.frappe.db, "get_value", return_value=None):
			self.assertEqual(pos_api._get_room_posting_mop(profile, ["Cash", "Card"]), "Cash")

	def test_resolve_pos_customer_uses_explicit_profile_settings_and_guest_fallback(self):
		profile = DotDict(customer="Profile Customer")

		def fake_exists(doctype, name):
			return doctype == "Customer" and name in {"Explicit Customer", "Profile Customer", "Settings Customer", "Walk-in Customer"}

		with (
			patch.object(pos_api.frappe.db, "exists", side_effect=fake_exists),
			patch.object(pos_api.frappe.db, "has_column", return_value=True),
			patch.object(pos_api.frappe.db, "get_single_value", return_value="Settings Customer"),
		):
			self.assertEqual(pos_api._resolve_pos_customer("Explicit Customer", profile), "Explicit Customer")
			self.assertEqual(pos_api._resolve_pos_customer("Missing", profile), "Profile Customer")
			self.assertEqual(pos_api._resolve_pos_customer("Missing", DotDict(customer="")), "Settings Customer")
			self.assertEqual(pos_api._resolve_pos_customer("Missing", DotDict(customer=""), True), "Settings Customer")

		with (
			patch.object(pos_api.frappe.db, "exists", side_effect=lambda doctype, name: doctype == "Customer" and name == "Walk-in Customer"),
			patch.object(pos_api.frappe.db, "has_column", return_value=False),
		):
			self.assertEqual(pos_api._resolve_pos_customer(None, DotDict(customer=""), True), "Walk-in Customer")


class TestPOSProfileAndShiftAPI(unittest.TestCase):
	def test_user_pos_profiles_prefers_explicit_profiles_over_global_profiles(self):
		def fake_sql(query, params=None, as_dict=False):
			if "INNER JOIN `tabPOS Profile User`" in query:
				return [DotDict(name="Restaurant POS"), DotDict(name="Bar POS")]
			return [DotDict(name="Global POS")]

		with patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql):
			self.assertEqual(pos_api._get_user_pos_profiles("cashier@example.com"), ["Restaurant POS", "Bar POS"])

	def test_user_pos_profiles_uses_global_profiles_when_user_has_no_mapping(self):
		def fake_sql(query, params=None, as_dict=False):
			if "INNER JOIN `tabPOS Profile User`" in query:
				return []
			return [DotDict(name="Global POS")]

		with patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql):
			self.assertEqual(pos_api._get_user_pos_profiles("cashier@example.com"), ["Global POS"])

	def test_open_pos_entry_prefers_requested_profile_then_falls_back_to_any_open_shift(self):
		calls = []

		def fake_get_value(doctype, filters, fields=None, as_dict=False, order_by=None):
			calls.append(filters)
			if filters.get("pos_profile") == "Restaurant POS":
				return None
			return DotDict(name="OPEN-ANY", pos_profile="Bar POS")

		with patch.object(pos_api.frappe.db, "get_value", side_effect=fake_get_value):
			entry = pos_api._get_open_pos_entry("cashier@example.com", "Restaurant POS")

		self.assertEqual(entry.name, "OPEN-ANY")
		self.assertEqual(calls[0]["pos_profile"], "Restaurant POS")
		self.assertNotIn("pos_profile", calls[1])

	def test_get_pos_opening_profiles_returns_open_shift_and_profile_rows(self):
		profile_doc = DotDict(company="Rho Hotel", payments=[DotDict(mode_of_payment="Cash"), DotDict(mode_of_payment="Card")])

		with (
			patch.object(pos_api.frappe, "session", types.SimpleNamespace(user="cashier@example.com")),
			patch.object(pos_api, "_get_open_pos_entry", return_value=DotDict(name="OPEN-1", pos_profile="Restaurant POS")),
			patch.object(pos_api, "_get_user_pos_profiles", return_value=["Restaurant POS"]),
			patch.object(pos_api.frappe, "get_doc", return_value=profile_doc),
		):
			result = pos_api.get_pos_opening_profiles()

		self.assertTrue(result["has_open_shift"])
		self.assertEqual(result["open_pos_opening_entry"], "OPEN-1")
		self.assertEqual(result["default_profile"], "Restaurant POS")
		self.assertEqual(result["profiles"][0]["payments"], ["Cash", "Card"])

	def test_get_pos_shift_stats_returns_empty_state_when_no_open_shift(self):
		with (
			patch.object(pos_api.frappe, "session", types.SimpleNamespace(user="cashier@example.com")),
			patch.object(pos_api, "_get_open_pos_entry", return_value=None),
			patch.object(pos_api.frappe.db, "get_value", return_value="Cashier User"),
		):
			result = pos_api.get_pos_shift_stats()

		self.assertFalse(result["has_open_shift"])
		self.assertEqual(result["gross_sales"], 0)
		self.assertEqual(result["cashier"], "Cashier User")

	def test_get_pos_shift_stats_scopes_by_opening_entry_when_schema_has_link(self):
		entry_doc = FakeDoc(
			name="OPEN-1",
			pos_profile="Restaurant POS",
			user="cashier@example.com",
			period_start_date="2026-06-08 09:00:00",
		)
		entry_doc.balance_details = [DotDict(mode_of_payment="Cash", opening_amount=2500)]

		def fake_sql(query, params=None, as_dict=False):
			if "SUM(grand_total)" in query:
				return [(12000,)]
			if "JOIN `tabSales Invoice Payment`" in query:
				return [DotDict(payment_type="Cash", system_amount=8000), DotDict(payment_type="Card", system_amount=4000)]
			if "customer_name LIKE 'Table" in query:
				return [(2,)]
			return [(0,)]

		def fake_count(doctype, filters):
			if filters.get("docstatus") == 0:
				return 3
			if filters.get("docstatus") == 1:
				return 7
			if filters.get("docstatus") == 2:
				return 1
			return 0

		with (
			patch.object(pos_api, "_has_pos_opening_entry_on_invoice", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=entry_doc),
			patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql),
			patch.object(pos_api.frappe.db, "count", side_effect=fake_count),
			patch.object(pos_api.frappe.db, "get_value", return_value="Cashier User"),
		):
			result = pos_api.get_pos_shift_stats("OPEN-1")

		self.assertTrue(result["has_open_shift"])
		self.assertEqual(result["gross_sales"], 12000)
		self.assertEqual(result["open_drafts"], 3)
		self.assertEqual(result["open_tables"], 2)
		self.assertEqual(result["bills_processed"], 7)
		self.assertEqual(result["voided_count"], 1)
		self.assertEqual(result["opening_cash"], 2500)
		self.assertTrue(result["tender_breakdown"][0]["editable"])
		self.assertFalse(result["tender_breakdown"][1]["editable"])


class TestPOSReadAPIs(unittest.TestCase):
	def test_search_pos_bill_to_returns_checked_in_guest_with_room_and_checkin_id(self):
		customer_row = DotDict(
			id="CUST-001",
			customer="CUST-001",
			name="Ada Lovelace",
			email_id="ada@example.com",
			mobile_no="0801",
		)
		checkin_row = DotDict(
			check_in="CHK-001",
			guest="HG-001",
			room="204",
			room_type="Deluxe",
			customer="CUST-001",
			name="Ada Lovelace",
			email_id="ada@example.com",
			mobile_no="0801",
			payment_type="Direct Guest",
		)

		def fake_sql(query, params=None, as_dict=False):
			if "FROM `tabCustomer`" in query:
				return [customer_row]
			if "FROM `tabHotel Room Check In` ci" in query:
				self.assertIn("LEFT JOIN `tabHotel Guest` hg", query)
				self.assertIn("ci.room_number LIKE %s", query)
				return [checkin_row]
			return []

		with patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql):
			result = pos_api.search_pos_bill_to("Ada")

		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["id"], "CHK-001")
		self.assertEqual(result[0]["check_in"], "CHK-001")
		self.assertEqual(result[0]["customer"], "CUST-001")
		self.assertEqual(result[0]["name"], "Ada Lovelace")
		self.assertEqual(result[0]["room"], "204")
		self.assertEqual(result[0]["room_type"], "Deluxe")
		self.assertEqual(result[0]["type"], "Checked In")

	def test_get_draft_pos_invoices_returns_items_age_and_service_point(self):
		draft_row = DotDict(
			invoice="POS-DRAFT-1",
			customer="Table 01",
			pos_profile="Restaurant POS",
			amount=1750,
			posting_date="2026-06-08",
			cashier="cashier@example.com",
			note="No pepper",
			age_minutes=95,
			item_count=2,
		)

		def fake_sql(query, params=None, as_dict=False):
			if "LEFT JOIN `tabPOS Invoice Item`" in query:
				return [draft_row]
			if "FROM `tabPOS Invoice Item`" in query:
				return [DotDict(name="Rice", qty=1), DotDict(name="Water", qty=2)]
			return []

		with patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql) as sql_mock:
			result = pos_api.get_draft_pos_invoices(search="Table", cashier="cashier@example.com")

		self.assertEqual(result[0]["invoice"], "POS-DRAFT-1")
		self.assertEqual(result[0]["items"][0].name, "Rice")
		self.assertEqual(result[0]["age"], "1h 35m")
		self.assertEqual(result[0]["service_point"], "Restaurant POS")
		self.assertIn("pi.owner = %s", sql_mock.call_args_list[0].args[0])

	def test_get_draft_pos_stats_aggregates_count_value_and_age(self):
		def fake_sql(query, params=None, as_dict=False):
			if "SUM(grand_total)" in query:
				return [(4500,)]
			if "TIMESTAMPDIFF" in query:
				return [(42,)]
			return [(0,)]

		with (
			patch.object(pos_api.frappe.db, "count", return_value=5),
			patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql),
		):
			result = pos_api.get_draft_pos_stats()

		self.assertEqual(result, {"total_drafts": 5, "total_value": 4500.0, "oldest_minutes": 42})

	def test_get_pos_invoices_applies_status_search_and_pagination(self):
		invoice = DotDict(invoice_no="POS-0001", customer="Walk In", grand_total=2000, status="Paid")

		with patch.object(pos_api.frappe.db, "sql", return_value=[invoice]) as sql_mock:
			result = pos_api.get_pos_invoices(search="Walk", status="Paid", page_length=10, start=20)

		query = sql_mock.call_args.args[0]
		params = sql_mock.call_args.args[1]
		self.assertEqual(result, [invoice])
		self.assertIn("pi.docstatus = 1", query)
		self.assertEqual(params[-2:], (10, 20))

	def test_get_pos_dashboard_stats_returns_live_totals_and_percentages(self):
		def fake_sql(query, params=None, as_dict=False):
			if "SUM(grand_total)" in query and "FROM `tabPOS Invoice`" in query and not as_dict:
				return [(30000,)]
			if "FROM `tabPOS Closing Entry`" in query:
				return [(250,)]
			if "FROM `tabPOS Opening Entry`" in query:
				return [DotDict(name="OPEN-1", terminal_name="Restaurant POS", cashier="Cashier", bills=4, sales=18000)]
			if "GROUP BY pos_profile" in query:
				return [DotDict(outlet="Restaurant POS", amount=20000), DotDict(outlet="Bar POS", amount=10000)]
			return [(0,)]

		with (
			patch.object(pos_api, "_has_pos_opening_entry_on_invoice", return_value=True),
			patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql),
			patch.object(pos_api.frappe.db, "count", return_value=6),
		):
			result = pos_api.get_pos_dashboard_stats()

		self.assertEqual(result["gross_sales"], 30000)
		self.assertEqual(result["open_drafts"], 6)
		self.assertEqual(result["shift_differences"], 250)
		self.assertEqual(result["outlet_revenue"][0]["pct"], 67)
		self.assertEqual(result["outlet_revenue"][1]["pct"], 33)

	def test_get_open_pos_tables_formats_area_age_and_items(self):
		rows = [
			DotDict(invoice="POS-TABLE-1", customer="Table 01", bill=1200, cashier="Ann", notes="Starter", age_minutes=15, open_time="09:15 AM"),
			DotDict(invoice="POS-BAR-1", customer="Bar 02", bill=800, cashier="Ben", notes="", age_minutes=125, open_time="08:00 AM"),
		]

		def fake_sql(query, params=None, as_dict=False):
			if "LEFT JOIN `tabPOS Invoice Item`" in query:
				return rows
			return [DotDict(item_code="ITEM-1", name="Rice", qty=1, price=1200, amount=1200)]

		with patch.object(pos_api.frappe.db, "sql", side_effect=fake_sql):
			result = pos_api.get_open_pos_tables()

		self.assertEqual(result[0]["area"], "Restaurant")
		self.assertEqual(result[0]["age"], "15m")
		self.assertEqual(result[1]["area"], "Bar Lounge")
		self.assertEqual(result[1]["age"], "2h 5m")
		self.assertEqual(result[0]["items"][0]["item_code"], "ITEM-1")

	def test_get_open_pos_terminals_normalizes_numeric_fields(self):
		terminal = DotDict(opening_entry="OPEN-1", terminal_name="Restaurant POS", gross_sales="15000", bill_count="5", open_drafts="2")

		with (
			patch.object(pos_api, "_has_pos_opening_entry_on_invoice", return_value=True),
			patch.object(pos_api.frappe.db, "sql", return_value=[terminal]),
		):
			result = pos_api.get_open_pos_terminals()

		self.assertEqual(result[0]["gross_sales"], 15000)
		self.assertEqual(result[0]["bill_count"], 5)
		self.assertEqual(result[0]["open_drafts"], 2)


class TestPOSDraftActions(unittest.TestCase):
	def test_get_pos_draft_invoice_detail_maps_items_for_resume(self):
		invoice = FakeDoc(name="POS-DRAFT-1", docstatus=0, customer_name="Table 01", customer="Walk In", remarks="No pepper", discount_amount=250)
		invoice.items = [DotDict(item_code="ITEM-1", item_name="Rice", qty=2, rate=1500)]

		def fake_get_value(doctype, name, fieldname):
			if fieldname == "item_group":
				return "Food"
			if fieldname == "image":
				return "/files/rice.png"
			return None

		with (
			patch.object(pos_api.frappe.db, "exists", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=invoice),
			patch.object(pos_api.frappe.db, "get_value", side_effect=fake_get_value),
		):
			result = pos_api.get_pos_draft_invoice_detail("POS-DRAFT-1")

		self.assertEqual(result["customer"], "Table 01")
		self.assertEqual(result["discount_amount"], 250)
		self.assertEqual(result["items"][0]["category"], "Food")
		self.assertEqual(result["items"][0]["price"], 1500)

	def test_get_pos_draft_invoice_detail_rejects_submitted_invoice(self):
		invoice = FakeDoc(name="POS-0001", docstatus=1)

		with (
			patch.object(pos_api.frappe.db, "exists", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=invoice),
			patch.object(pos_api.frappe, "throw", side_effect=RuntimeError("Only draft invoices can be resumed.")),
		):
			with self.assertRaises(RuntimeError):
				pos_api.get_pos_draft_invoice_detail("POS-0001")

	def test_delete_pos_draft_invoice_deletes_only_draft_invoice(self):
		invoice = FakeDoc(name="POS-DRAFT-1", docstatus=0)

		with (
			patch.object(pos_api.frappe.db, "exists", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=invoice),
			patch.object(pos_api.frappe.db, "commit") as commit_mock,
		):
			result = pos_api.delete_pos_draft_invoice("POS-DRAFT-1")

		self.assertEqual(result, {"deleted": "POS-DRAFT-1"})
		self.assertTrue(invoice.deleted)
		commit_mock.assert_called_once()


class TestPostToRoomFlow(unittest.TestCase):
	def test_post_bill_to_room_creates_room_folio_and_consolidated_pos_invoice(self):
		sales_invoice = FakeDoc(name="SI-ROOM-1")
		pos_invoice = FakeDoc(name="POS-ROOM-1")
		check_in = FakeDoc(
			name="CHK-1",
			status="Checked In",
			room_number="101",
			guest="HG-1",
			canonical_reservation=None,
		)
		guest = FakeDoc(name="HG-1", customer="Guest Customer")
		profile = DotDict(
			company="Rho Hotel",
			payments=[DotDict(mode_of_payment="Cash"), DotDict(mode_of_payment="Room Charge")],
		)
		items = [{"item_code": "ITEM-1", "qty": 2, "price": 1500}]
		set_value_calls = []

		def fake_exists(doctype, name):
			if doctype == "Hotel Room Check In" and name == "CHK-1":
				return True
			return False

		def fake_get_doc(doctype, name):
			if doctype == "Hotel Room Check In" and name == "CHK-1":
				return check_in
			if doctype == "Hotel Guest" and name == "HG-1":
				return guest
			raise AssertionError(f"Unexpected get_doc({doctype!r}, {name!r})")

		with (
			patch.object(pos_api.frappe.db, "exists", side_effect=fake_exists),
			patch.object(pos_api.frappe, "get_doc", side_effect=fake_get_doc),
			patch.object(pos_api.frappe, "new_doc", side_effect=[sales_invoice, pos_invoice]),
			patch.object(pos_api.frappe.db, "get_single_value", return_value="Rho Hotel"),
			patch.object(pos_api.frappe.db, "get_value", return_value=None),
			patch.object(pos_api.frappe.db, "set_value", side_effect=lambda *args, **kwargs: set_value_calls.append((args, kwargs))),
			patch.object(pos_api.frappe.db, "commit") as commit_mock,
			patch.object(pos_api, "_get_user_pos_profile", return_value="Restaurant POS"),
			patch.object(pos_api, "_get_open_pos_entry", return_value=DotDict(name="OPEN-1", pos_profile="Restaurant POS")),
			patch.object(pos_api.frappe, "get_cached_doc", return_value=profile),
			patch.object(pos_api, "_resolve_pos_customer", return_value="Guest Customer"),
			patch.object(pos_api, "_has_pos_opening_entry_on_invoice", return_value=True),
			patch.object(pos_api, "_get_complimentary_discount", return_value=0),
			patch.object(pos_api, "_redeem_complimentary", return_value=None),
		):
			result = pos_api.post_bill_to_room(
				items,
				"CHK-1",
				narration="Room service dinner",
				kitchen_note="No onions",
			)

		self.assertEqual(result["sales_invoice"], "SI-ROOM-1")
		self.assertEqual(result["pos_invoice"], "POS-ROOM-1")
		self.assertEqual(result["room"], "101")
		self.assertEqual(sales_invoice.custom_hotel_room_check_in, "CHK-1")
		self.assertEqual(sales_invoice.customer, "Guest Customer")
		self.assertEqual(sales_invoice.remarks, "No onions | Room service dinner")
		self.assertTrue(sales_invoice.submitted)
		self.assertEqual(pos_invoice.custom_hotel_room_check_in, "CHK-1")
		self.assertEqual(pos_invoice.pos_opening_entry, "OPEN-1")
		self.assertEqual(pos_invoice.payments[0].mode_of_payment, "Room Charge")
		self.assertEqual(pos_invoice.payments[0].amount, 3000)
		self.assertTrue(pos_invoice.submitted)
		self.assertIn((('POS Invoice', 'POS-ROOM-1', 'consolidated_invoice', 'SI-ROOM-1'), {}), set_value_calls)
		self.assertEqual(commit_mock.call_count, 2)

	def test_post_bill_to_room_rejects_inactive_checkin(self):
		check_in = FakeDoc(name="CHK-OUT", status="Checked Out", room_number="101", guest="HG-1")

		with (
			patch.object(pos_api.frappe.db, "exists", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=check_in),
			patch.object(pos_api.frappe, "throw", side_effect=RuntimeError("Check-in CHK-OUT is not active")),
		):
			with self.assertRaises(RuntimeError):
				pos_api.post_bill_to_room([{"item_code": "ITEM-1", "qty": 1, "price": 1000}], "CHK-OUT")


class TestKitchenSendFlow(unittest.TestCase):
	def test_send_to_kitchen_creates_ticket_for_unsent_quantities(self):
		ticket = FakeDoc(name="KOT-1")
		items = [
			{"item_code": "ITEM-1", "item_name": "Rice", "qty": 3},
			{"item_code": "ITEM-2", "item_name": "Soup", "qty": 1, "notes": "Extra hot"},
		]

		with (
			patch.object(kitchen_api.frappe.db, "sql", return_value=[DotDict(item_code="ITEM-1", sent_qty=1)]),
			patch.object(kitchen_api.frappe, "new_doc", return_value=ticket),
			patch.object(kitchen_api.frappe.db, "commit") as commit_mock,
		):
			result = kitchen_api.send_to_kitchen(
				items,
				pos_invoice="POS-1",
				table_or_room="Table 01",
				source="Restaurant Dining",
				kitchen_note="Serve starters first",
			)

		self.assertEqual(result, {"ticket": "KOT-1", "item_codes": ["ITEM-1", "ITEM-2"], "item_count": 2})
		self.assertEqual(ticket.pos_invoice, "POS-1")
		self.assertEqual(ticket.table_or_room, "Table 01")
		self.assertEqual(ticket.source, "Restaurant Dining")
		self.assertEqual(ticket.status, "Pending")
		self.assertEqual(ticket.notes, "Serve starters first")
		self.assertEqual(ticket.items[0].quantity, 2)
		self.assertEqual(ticket.items[1].quantity, 1)
		self.assertTrue(ticket.inserted)
		commit_mock.assert_called_once()

	def test_send_to_kitchen_skips_when_all_items_already_sent(self):
		items = [{"item_code": "ITEM-1", "item_name": "Rice", "qty": 2}]

		with (
			patch.object(kitchen_api.frappe.db, "sql", return_value=[DotDict(item_code="ITEM-1", sent_qty=2)]),
			patch.object(kitchen_api.frappe, "new_doc") as new_doc_mock,
		):
			result = kitchen_api.send_to_kitchen(items, pos_invoice="POS-1")

		self.assertTrue(result["skipped"])
		self.assertEqual(result["item_count"], 0)
		new_doc_mock.assert_not_called()


class TestPOSShiftClosing(unittest.TestCase):
	def test_close_pos_shift_applies_counted_tenders_note_and_submits_closing_entry(self):
		opening = FakeDoc(name="OPEN-1")
		closing = FakeDoc(name="CLOSE-1")
		closing.payment_reconciliation = [
			DotDict(mode_of_payment="Cash", expected_amount=1000, closing_amount=0, difference=0)
		]

		closing_module = types.ModuleType("erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry")
		closing_module.make_closing_entry_from_opening = Mock(return_value=closing)

		with (
			patch.dict(
				sys.modules,
				{
					"erpnext.accounts.doctype.pos_closing_entry": types.ModuleType("erpnext.accounts.doctype.pos_closing_entry"),
					"erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry": closing_module,
				},
			),
			patch.object(pos_api.frappe.db, "exists", return_value=True),
			patch.object(pos_api.frappe, "get_doc", return_value=opening),
			patch.object(
				pos_api.frappe,
				"get_meta",
				return_value=types.SimpleNamespace(fields=[types.SimpleNamespace(fieldname="notes")]),
			),
			patch.object(pos_api.frappe.db, "commit") as commit_mock,
		):
			result = pos_api.close_pos_shift(
				"OPEN-1",
				tender_rows=[
					{"payment_type": "Cash", "system_amount": 1000, "counted": 900},
					{"payment_type": "Card", "system_amount": 500, "counted": 500},
				],
				closing_note="End of shift balanced except cash shortage",
			)

		self.assertEqual(result, {"closing_entry": "CLOSE-1"})
		closing_module.make_closing_entry_from_opening.assert_called_once_with(opening)
		self.assertTrue(closing.flags.ignore_permissions)
		self.assertTrue(closing.flags.ignore_mandatory)
		self.assertEqual(closing.payment_reconciliation[0].closing_amount, 900)
		self.assertEqual(closing.payment_reconciliation[0].difference, -100)
		self.assertEqual(closing.payment_reconciliation[1].mode_of_payment, "Card")
		self.assertEqual(closing.payment_reconciliation[1].closing_amount, 500)
		self.assertEqual(closing.notes, "End of shift balanced except cash shortage")
		self.assertTrue(closing.inserted)
		self.assertTrue(closing.submitted)
		commit_mock.assert_called_once()

	def test_close_pos_shift_rejects_missing_opening_entry(self):
		closing_module = types.ModuleType("erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry")
		closing_module.make_closing_entry_from_opening = Mock()

		with (
			patch.dict(
				sys.modules,
				{
					"erpnext.accounts.doctype.pos_closing_entry": types.ModuleType("erpnext.accounts.doctype.pos_closing_entry"),
					"erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry": closing_module,
				},
			),
			patch.object(pos_api.frappe.db, "exists", return_value=False),
			patch.object(pos_api.frappe, "throw", side_effect=RuntimeError("POS Opening Entry MISSING not found")),
		):
			with self.assertRaises(RuntimeError):
				pos_api.close_pos_shift("MISSING")

		closing_module.make_closing_entry_from_opening.assert_not_called()


class TestPOSSplitInvoice(unittest.TestCase):
	def test_create_split_pos_invoice_creates_submitted_invoice_with_resolved_payment_modes(self):
		created_invoice = FakeDoc(name="POS-SPLIT-1")
		profile = DotDict(
			company="Rho Hotel",
			customer="Walk-in Customer",
			payments=[
				DotDict(mode_of_payment="Cash"),
				DotDict(mode_of_payment="Card POS"),
				DotDict(mode_of_payment="Room Charge"),
			],
		)
		items = [{"item_code": "ITEM-1", "qty": 2, "price": 1000}]
		portions = [
			{"paymentType": "POS", "amount": 1200},
			{"paymentType": "Post to Room", "amount": 800, "checkIn": "CHK-1"},
		]

		with (
			patch.object(pos_api.frappe, "session", types.SimpleNamespace(user="cashier@example.com")),
			patch.object(pos_api, "_get_user_pos_profile", return_value="Restaurant POS"),
			patch.object(pos_api, "_get_open_pos_entry", return_value=DotDict(name="OPEN-1", pos_profile="Restaurant POS")),
			patch.object(pos_api.frappe, "get_cached_doc", return_value=profile),
			patch.object(pos_api, "_resolve_pos_customer", return_value="Walk-in Customer"),
			patch.object(pos_api, "_has_pos_opening_entry_on_invoice", return_value=True),
			patch.object(pos_api, "_get_complimentary_discount", return_value=0),
			patch.object(pos_api, "_redeem_complimentary", return_value=None),
			patch.object(pos_api.frappe.db, "has_column", return_value=True),
			patch.object(pos_api.frappe.db, "exists", return_value=False),
			patch.object(pos_api.frappe.db, "commit") as commit_mock,
			patch.object(pos_api.frappe, "new_doc", return_value=created_invoice),
		):
			result = pos_api.create_split_pos_invoice(items, portions)

		self.assertEqual(result["pos_invoice"], "POS-SPLIT-1")
		self.assertTrue(result["split"])
		self.assertTrue(created_invoice.inserted)
		self.assertTrue(created_invoice.submitted)
		self.assertEqual(created_invoice.pos_opening_entry, "OPEN-1")
		self.assertEqual(created_invoice.custom_hotel_room_check_in, "CHK-1")
		self.assertEqual([p.mode_of_payment for p in created_invoice.payments], ["Card POS", "Room Charge"])
		self.assertEqual([p.amount for p in created_invoice.payments], [1200, 800])
		commit_mock.assert_called_once()

	def test_create_split_pos_invoice_requires_portions_to_match_invoice_total(self):
		profile = DotDict(company="Rho Hotel", customer="Walk-in Customer", payments=[DotDict(mode_of_payment="Cash")])

		with (
			patch.object(pos_api.frappe, "session", types.SimpleNamespace(user="cashier@example.com")),
			patch.object(pos_api, "_get_user_pos_profile", return_value="Restaurant POS"),
			patch.object(pos_api, "_get_open_pos_entry", return_value=DotDict(name="OPEN-1", pos_profile="Restaurant POS")),
			patch.object(pos_api.frappe, "get_cached_doc", return_value=profile),
			patch.object(pos_api, "_resolve_pos_customer", return_value="Walk-in Customer"),
			patch.object(pos_api, "_get_complimentary_discount", return_value=0),
			patch.object(pos_api.frappe, "throw", side_effect=RuntimeError("Split total must equal invoice total.")),
		):
			with self.assertRaises(RuntimeError):
				pos_api.create_split_pos_invoice(
					[{"item_code": "ITEM-1", "qty": 1, "price": 1000}],
					[{"paymentType": "Cash", "amount": 900}],
				)


if __name__ == "__main__":
	unittest.main()