import frappe
from frappe.utils import nowdate, add_days, getdate, get_datetime, flt, cint, format_datetime


def _has_doctype(doctype):
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		return False


def _has_column(doctype, column):
	try:
		return bool(frappe.db.has_column(doctype, column))
	except Exception:
		return False


def _get_field(doctype, candidates):
	for field in candidates:
		if _has_column(doctype, field):
			return field
	return None


def _date_or_default(value, default_value):
	try:
		return getdate(value) if value else getdate(default_value)
	except Exception:
		return getdate(default_value)


def _dt(value):
	if not value:
		return ""
	try:
		return format_datetime(value, "dd-MM-yyyy HH:mm")
	except Exception:
		return str(value)


def _money(value):
	return flt(value or 0, 2)


def _get_payment_status(row, payment_mode):
	outstanding = flt(row.get("outstanding_amount") or 0)
	grand_total = flt(row.get("grand_total") or 0)
	status = row.get("status") or ""

	if status in ("Return", "Cancelled", "Draft"):
		return status

	if payment_mode == "Room Posting":
		return "Posted to Room"

	if grand_total <= 0:
		return "Paid"

	if outstanding <= 0:
		return "Paid"

	if outstanding < grand_total:
		return "Part Payment"

	return "Unpaid"


@frappe.whitelist()
def get_pos_sales_performance_report(
	date_from=None,
	date_to=None,
	pos_profile=None,
	cashier=None,
	payment_mode=None,
	search=None,
):
	date_from = _date_or_default(date_from, add_days(nowdate(), -7))
	date_to = _date_or_default(date_to, nowdate())

	if not _has_doctype("POS Invoice"):
		return {
			"sales": [],
			"shifts": [],
			"top_items": [],
			"pos_profiles": [],
			"cashiers": [],
			"payment_modes": [],
			"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
		}

	room_field = _get_field("POS Invoice", [
		"custom_room_number",
		"room_number",
		"room",
		"custom_room",
		"hotel_room",
		"custom_hotel_room",
		"custom_hotel_room_check_in",
	])

	cashier_field = _get_field("POS Invoice", [
		"cashier",
		"custom_cashier",
		"user",
		"owner",
	])

	customer_name_field = _get_field("POS Invoice", [
		"customer_name",
		"customer",
	])

	select_parts = [
		"name",
		"posting_date",
		"posting_time",
		"customer",
		"`{0}` AS customer_display".format(customer_name_field) if customer_name_field else "customer AS customer_display",
		"pos_profile",
		"`{0}` AS cashier".format(cashier_field) if cashier_field else "owner AS cashier",
		"`{0}` AS room".format(room_field) if room_field else "'' AS room",
		"net_total",
		"grand_total",
		"discount_amount",
		"total_taxes_and_charges",
		"outstanding_amount",
		"paid_amount",
		"status",
		"docstatus",
	]

	conditions = [
		"docstatus = 1",
		"posting_date BETWEEN %s AND %s",
	]

	values = [date_from, date_to]

	if pos_profile:
		conditions.append("pos_profile = %s")
		values.append(pos_profile)

	if cashier and cashier_field:
		conditions.append("`{0}` = %s".format(cashier_field))
		values.append(cashier)

	sql = """
		SELECT {fields}
		FROM `tabPOS Invoice`
		WHERE {conditions}
		ORDER BY posting_date DESC, posting_time DESC, creation DESC
	""".format(
		fields=", ".join(select_parts),
		conditions=" AND ".join(conditions),
	)

	invoices = frappe.db.sql(sql, tuple(values), as_dict=True)

	invoice_names = [d.name for d in invoices]
	payments_by_invoice = {}
	items_by_invoice = {}

	if invoice_names and _has_doctype("POS Invoice Payment"):
		placeholders = ", ".join(["%s"] * len(invoice_names))
		payment_rows = frappe.db.sql(
			"""
			SELECT parent, mode_of_payment, amount
			FROM `tabPOS Invoice Payment`
			WHERE parent IN ({0})
			""".format(placeholders),
			tuple(invoice_names),
			as_dict=True,
		)

		for row in payment_rows:
			payments_by_invoice.setdefault(row.parent, [])
			payments_by_invoice[row.parent].append({
				"mode": row.mode_of_payment or "Unknown",
				"amount": flt(row.amount or 0),
			})

	if invoice_names and _has_doctype("POS Invoice Item"):
		placeholders = ", ".join(["%s"] * len(invoice_names))
		item_rows = frappe.db.sql(
			"""
			SELECT
				parent,
				item_code,
				item_name,
				item_group,
				qty,
				net_amount,
				amount
			FROM `tabPOS Invoice Item`
			WHERE parent IN ({0})
			""".format(placeholders),
			tuple(invoice_names),
			as_dict=True,
		)

		for row in item_rows:
			items_by_invoice.setdefault(row.parent, [])
			items_by_invoice[row.parent].append(row)

	sales = []

	for inv in invoices:
		payments = payments_by_invoice.get(inv.name, [])
		payment_modes = [p.get("mode") for p in payments if p.get("mode")]

		if not payment_modes:
			payment_modes = ["Room Posting"] if flt(inv.outstanding_amount or 0) > 0 else ["Unknown"]

		main_payment_mode = ", ".join(payment_modes)

		if payment_mode:
			if payment_mode not in payment_modes and payment_mode != main_payment_mode:
				continue

		status = _get_payment_status(inv, main_payment_mode)

		row = {
			"invoice": inv.name,
			"date": _dt(str(inv.posting_date) + " " + str(inv.posting_time or "00:00:00")),
			"customer": inv.customer_display or inv.customer or "Walk-in Customer",
			"room": inv.room or "",
			"cashier": inv.cashier or inv.owner or "Unknown",
			"pos_profile": inv.pos_profile or "—",
			"payment_mode": main_payment_mode,
			"gross_amount": _money(inv.net_total or inv.grand_total),
			"discount": _money(inv.discount_amount),
			"tax": _money(inv.total_taxes_and_charges),
			"net_amount": _money(inv.grand_total),
			"outstanding": _money(inv.outstanding_amount),
			"paid_amount": _money(inv.paid_amount),
			"status": status,
		}

		sales.append(row)

	if search:
		q = str(search).lower().strip()
		sales = [
			row for row in sales
			if q in str(row.get("invoice") or "").lower()
			or q in str(row.get("customer") or "").lower()
			or q in str(row.get("room") or "").lower()
			or q in str(row.get("cashier") or "").lower()
			or q in str(row.get("pos_profile") or "").lower()
			or q in str(row.get("payment_mode") or "").lower()
			or q in str(row.get("status") or "").lower()
		]

	allowed_invoice_names = set([row["invoice"] for row in sales])

	item_map = {}
	for invoice_name, invoice_items in items_by_invoice.items():
		if invoice_name not in allowed_invoice_names:
			continue

		for item in invoice_items:
			key = item.item_code or item.item_name or "Unknown Item"

			if key not in item_map:
				item_map[key] = {
					"item_code": item.item_code or key,
					"item_name": item.item_name or key,
					"category": item.item_group or "Uncategorized",
					"qty": 0,
					"revenue": 0,
				}

			item_map[key]["qty"] += flt(item.qty or 0)
			item_map[key]["revenue"] += flt(item.net_amount or item.amount or 0)

	top_items = sorted(
		item_map.values(),
		key=lambda d: flt(d.get("revenue")),
		reverse=True
	)[:10]

	shifts = []

	if _has_doctype("POS Opening Shift"):
		shift_cashier_field = _get_field("POS Opening Shift", ["user", "cashier", "owner"])
		opening_field = _get_field("POS Opening Shift", ["period_start_date", "opening_time", "creation"])
		closing_field = _get_field("POS Opening Shift", ["period_end_date", "closing_time", "modified"])

		shift_select = [
			"name",
			"pos_profile" if _has_column("POS Opening Shift", "pos_profile") else "'' AS pos_profile",
			"`{0}` AS cashier".format(shift_cashier_field) if shift_cashier_field else "owner AS cashier",
			"`{0}` AS opening_time".format(opening_field) if opening_field else "creation AS opening_time",
			"`{0}` AS closing_time".format(closing_field) if closing_field else "modified AS closing_time",
		]

		shift_conditions = ["docstatus != 2"]
		shift_values = []

		if opening_field:
			shift_conditions.append("DATE(`{0}`) BETWEEN %s AND %s".format(opening_field))
			shift_values.extend([date_from, date_to])

		if pos_profile and _has_column("POS Opening Shift", "pos_profile"):
			shift_conditions.append("pos_profile = %s")
			shift_values.append(pos_profile)

		if cashier and shift_cashier_field:
			shift_conditions.append("`{0}` = %s".format(shift_cashier_field))
			shift_values.append(cashier)

		shift_rows = frappe.db.sql(
			"""
			SELECT {fields}
			FROM `tabPOS Opening Shift`
			WHERE {conditions}
			ORDER BY modified DESC
			""".format(
				fields=", ".join(shift_select),
				conditions=" AND ".join(shift_conditions),
			),
			tuple(shift_values),
			as_dict=True,
		)

		for shift in shift_rows:
			shift_sales = [
				row for row in sales
				if (not shift.pos_profile or row.get("pos_profile") == shift.pos_profile)
				and (not shift.cashier or row.get("cashier") == shift.cashier)
			]

			shifts.append({
				"name": shift.name,
				"cashier": shift.cashier or "Unknown",
				"opening_time": _dt(shift.opening_time),
				"closing_time": _dt(shift.closing_time) if shift.closing_time else "",
				"orders": len(shift_sales),
				"sales": _money(sum(flt(row.get("net_amount")) for row in shift_sales)),
				"variance": 0,
			})

	if not shifts:
		cashier_map = {}
		for row in sales:
			key = row.get("cashier") or "Unknown"

			if key not in cashier_map:
				cashier_map[key] = {
					"name": "AUTO-" + key,
					"cashier": key,
					"opening_time": "",
					"closing_time": "",
					"orders": 0,
					"sales": 0,
					"variance": 0,
				}

			cashier_map[key]["orders"] += 1
			cashier_map[key]["sales"] += flt(row.get("net_amount"))

		shifts = list(cashier_map.values())

	pos_profiles = sorted(list(set([row["pos_profile"] for row in sales if row.get("pos_profile") and row.get("pos_profile") != "—"])))
	cashiers = sorted(list(set([row["cashier"] for row in sales if row.get("cashier")])))
	payment_modes = sorted(list(set([mode.strip() for row in sales for mode in str(row.get("payment_mode") or "").split(",") if mode.strip()])))

	return {
		"sales": sales,
		"shifts": shifts,
		"top_items": top_items,
		"pos_profiles": pos_profiles,
		"cashiers": cashiers,
		"payment_modes": payment_modes,
		"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
		"filters": {
			"date_from": str(date_from),
			"date_to": str(date_to),
		},
	}