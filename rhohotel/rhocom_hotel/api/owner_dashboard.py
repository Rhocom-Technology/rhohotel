import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate


EXECUTIVE_ROLES = {"Hotel Owner", "Hotel Manager", "System Manager"}


@frappe.whitelist()
def get_owner_dashboard_data(from_date=None, to_date=None):
	"""Return the finance-first executive dashboard payload."""
	_require_owner_access()

	today = getdate(nowdate())
	to_dt = getdate(to_date) if to_date else today
	from_dt = getdate(from_date) if from_date else add_days(to_dt, -7)
	if to_dt < from_dt:
		frappe.throw(_("To Date cannot be before From Date."))

	errors = []
	finance = _safe_section("finance", lambda: _build_finance(from_dt, to_dt), _empty_finance(), errors)
	profitability = _safe_section("profitability", lambda: _build_profitability(from_dt, to_dt), _empty_profitability(), errors)
	cashflow = _safe_section("cashflow", lambda: _build_cashflow(from_dt, to_dt), _empty_cashflow(), errors)
	occupancy = _safe_section("occupancy", lambda: _build_occupancy(from_dt, to_dt, finance), _empty_occupancy(), errors)
	cash_control = _safe_section("cash_control", lambda: _build_cash_control(from_dt, to_dt), _empty_cash_control(), errors)
	operations = _safe_section("operations", lambda: _build_operations(from_dt, to_dt), _empty_operations(), errors)
	revenue_mix = _safe_section("revenue_mix", lambda: _build_revenue_mix(from_dt, to_dt), [], errors)
	channel_performance = _safe_section("channel_performance", lambda: _build_channel_performance(from_dt, to_dt), [], errors)
	room_type_performance = _safe_section("room_type_performance", lambda: _build_room_type_performance(from_dt, to_dt), [], errors)
	hall_bookings = _safe_section("hall_bookings", lambda: _build_hall_bookings(from_dt, to_dt), _empty_hall_bookings(), errors)
	corporate_risk = _safe_section("corporate_risk", lambda: _build_corporate_risk(from_dt, to_dt), [], errors)
	trends = _safe_section("trends", lambda: _build_trends(from_dt, to_dt), [], errors)
	watchlist = _safe_section("watchlist", lambda: _build_watchlist(finance, profitability, cashflow, occupancy, cash_control, operations, corporate_risk, from_dt, to_dt), [_watch("Dashboard partially loaded", len(errors), "Medium", "Some optional sections could not be loaded.", "/reports")], errors)

	return {
		"filters": {"from_date": str(from_dt), "to_date": str(to_dt)},
		"finance": finance,
		"profitability": profitability,
		"cashflow": cashflow,
		"revenue_mix": revenue_mix,
		"channel_performance": channel_performance,
		"room_type_performance": room_type_performance,
		"hall_bookings": hall_bookings,
		"corporate_risk": corporate_risk,
		"occupancy": occupancy,
		"cash_control": cash_control,
		"operations": operations,
		"trends": trends,
		"watchlist": watchlist,
		"section_errors": errors,
	}



def _safe_section(section, builder, fallback, errors):
	try:
		return builder()
	except Exception as exc:
		message = str(exc)[:180]
		errors.append({"section": section, "error": message})
		try:
			frappe.log_error(f"{section}: {message}", "Owner Dashboard Section Failed")
		except Exception:
			pass
		return fallback


def _empty_finance():
	return {
		"total_invoiced": 0,
		"total_collected": 0,
		"total_outstanding": 0,
		"total_overdue": 0,
		"collection_rate": 0,
		"period_invoiced": 0,
		"period_collected": 0,
		"period_outstanding": 0,
		"unallocated_payments_count": 0,
		"unallocated_payments_amount": 0,
		"credit_notes_count": 0,
		"credit_notes_amount": 0,
	}


def _empty_cashflow():
	return {"cash_in": 0, "cash_out": 0, "net_cashflow": 0, "payment_modes": []}


def _empty_occupancy():
	return {
		"total_rooms": 0,
		"occupied": 0,
		"vacant": 0,
		"reserved": 0,
		"dirty": 0,
		"maintenance": 0,
		"room_nights": 0,
		"occupancy_rate": 0,
		"adr": 0,
		"revpar": 0,
		"room_revenue": 0,
	}


def _empty_cash_control():
	return {
		"pos_sales": 0,
		"open_drafts": 0,
		"active_terminals": 0,
		"shift_differences": 0,
		"outlets": [],
	}


def _empty_operations():
	return {
		"arrivals": 0,
		"departures": 0,
		"overdue_checkouts": 0,
		"unpaid_folios": 0,
		"housekeeping_attention": 0,
		"maintenance_attention": 0,
		"hall_events": 0,
	}

def _require_owner_access():
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(EXECUTIVE_ROLES):
		frappe.throw(
			_("Only Hotel Owners and Hotel Managers can view the owner dashboard."),
			frappe.PermissionError,
		)


def _has_table(doctype):
	try:
		if hasattr(frappe.db, "table_exists"):
			return bool(frappe.db.table_exists(doctype))
	except Exception:
		pass
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		return True


def _has_column(doctype, fieldname):
	try:
		return bool(frappe.db.has_column(doctype, fieldname))
	except Exception:
		return False


def _first(rows):
	return rows[0] if rows else {}


def _get(row, key, default=0):
	if isinstance(row, dict):
		return row.get(key, default)
	return getattr(row, key, default)


def _round(value):
	return round(flt(value), 2)


def _pct(part, total):
	return round((flt(part) / flt(total) * 100) if flt(total) else 0, 1)


def _build_finance(from_dt, to_dt):
	if not _has_table("Payment Ledger Entry"):
		return {
			"total_invoiced": 0,
			"total_collected": 0,
			"total_outstanding": 0,
			"total_overdue": 0,
			"collection_rate": 0,
			"period_invoiced": 0,
			"period_collected": 0,
			"period_outstanding": 0,
			"unallocated_payments_count": 0,
			"unallocated_payments_amount": 0,
			"credit_notes_count": 0,
			"credit_notes_amount": 0,
		}

	lifetime = _first(frappe.db.sql(
		"""
		SELECT
			SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_invoiced,
			SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS total_collected,
			SUM(amount) AS total_outstanding
		FROM `tabPayment Ledger Entry`
		WHERE docstatus = 1
		  AND account_type = 'Receivable'
		  AND party_type = 'Customer'
		  AND delinked = 0
		  AND posting_date <= %(to_dt)s
		""",
		{"to_dt": str(to_dt)},
		as_dict=True,
	))
	period = _first(frappe.db.sql(
		"""
		SELECT
			SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS period_invoiced,
			SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS period_collected,
			SUM(amount) AS period_outstanding
		FROM `tabPayment Ledger Entry`
		WHERE docstatus = 1
		  AND account_type = 'Receivable'
		  AND party_type = 'Customer'
		  AND delinked = 0
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	))

	total_outstanding = flt(_get(lifetime, "total_outstanding"))
	total_collected = flt(_get(lifetime, "total_collected"))
	total_invoiced = flt(_get(lifetime, "total_invoiced"))

	overdue = 0
	credit_count = credit_amount = 0
	if _has_table("Sales Invoice"):
		overdue = flt(_get(_first(frappe.db.sql(
			"""
			SELECT SUM(outstanding_amount) AS total_overdue
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			  AND is_return = 0
			  AND outstanding_amount > 0
			  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			  AND due_date < %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "total_overdue"))
		credit = _first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt, ABS(SUM(outstanding_amount)) AS amount
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			  AND is_return = 1
			  AND outstanding_amount != 0
			  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		))
		credit_count = int(_get(credit, "cnt", 0) or 0)
		credit_amount = flt(_get(credit, "amount", 0))

	unallocated_count = unallocated_amount = 0
	if _has_table("Payment Entry"):
		unallocated = _first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt, SUM(unallocated_amount) AS amount
			FROM `tabPayment Entry`
			WHERE docstatus = 1
			  AND payment_type = 'Receive'
			  AND party_type = 'Customer'
			  AND IFNULL(party, '') != ''
			  AND unallocated_amount > 0
			  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		))
		unallocated_count = int(_get(unallocated, "cnt", 0) or 0)
		unallocated_amount = flt(_get(unallocated, "amount", 0))

	return {
		"total_invoiced": _round(total_invoiced),
		"total_collected": _round(total_collected),
		"total_outstanding": _round(total_outstanding),
		"total_overdue": _round(overdue),
		"collection_rate": _pct(total_collected, total_invoiced),
		"period_invoiced": _round(_get(period, "period_invoiced")),
		"period_collected": _round(_get(period, "period_collected")),
		"period_outstanding": _round(_get(period, "period_outstanding")),
		"unallocated_payments_count": unallocated_count,
		"unallocated_payments_amount": _round(unallocated_amount),
		"credit_notes_count": credit_count,
		"credit_notes_amount": _round(credit_amount),
	}


def _build_revenue_mix(from_dt, to_dt):
	if not _has_table("Sales Invoice"):
		return []

	source_expr = (
		"COALESCE(NULLIF(custom_invoice_source, ''), 'Other')"
		if _has_column("Sales Invoice", "custom_invoice_source")
		else "'Other'"
	)
	checkin_expr = "custom_hotel_room_check_in" if _has_column("Sales Invoice", "custom_hotel_room_check_in") else "NULL"
	rows = frappe.db.sql(
		f"""
		SELECT
			CASE
				WHEN {checkin_expr} IS NOT NULL AND {checkin_expr} != '' THEN 'Rooms'
				WHEN LOWER({source_expr}) LIKE '%%room%%' THEN 'Rooms'
				WHEN LOWER({source_expr}) LIKE '%%hall%%' THEN 'Halls'
				WHEN LOWER({source_expr}) LIKE '%%pos%%'
				  OR LOWER({source_expr}) LIKE '%%restaurant%%'
				  OR LOWER({source_expr}) LIKE '%%bar%%'
				  OR LOWER({source_expr}) LIKE '%%food%%'
				  OR LOWER({source_expr}) LIKE '%%beverage%%' THEN 'POS'
				ELSE 'Other'
			END AS category,
			SUM(grand_total) AS amount,
			COUNT(*) AS invoice_count
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		  AND is_return = 0
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY category
		ORDER BY amount DESC
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)
	total = sum(flt(_get(row, "amount")) for row in rows)
	return [
		{
			"category": _get(row, "category", "Other"),
			"amount": _round(_get(row, "amount")),
			"invoice_count": int(_get(row, "invoice_count", 0) or 0),
			"share": _pct(_get(row, "amount"), total),
		}
		for row in rows
	]



def _build_profitability(from_dt, to_dt):
	if not (_has_table("GL Entry") and _has_table("Account")):
		return _empty_profitability()

	rows = frappe.db.sql(
		"""
		SELECT
			acc.root_type,
			gle.account,
			SUM(gle.credit - gle.debit) AS income_amount,
			SUM(gle.debit - gle.credit) AS expense_amount
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0
		  AND gle.posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		  AND acc.root_type IN ('Income', 'Expense')
		GROUP BY acc.root_type, gle.account
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)

	revenue = expenses = 0
	income_accounts = []
	expense_accounts = []
	cost_signals = {
		"payroll": 0,
		"maintenance": 0,
		"housekeeping": 0,
		"fnb_cost": 0,
		"utilities": 0,
	}

	for row in rows:
		root_type = _get(row, "root_type", "")
		account = _get(row, "account", "Unknown")
		if root_type == "Income":
			amount = flt(_get(row, "income_amount"))
			if amount:
				revenue += amount
				income_accounts.append({"account": account, "amount": _round(amount)})
			continue

		if root_type == "Expense":
			amount = flt(_get(row, "expense_amount"))
			if amount:
				expenses += amount
				expense_accounts.append({"account": account, "amount": _round(amount)})
				_bucket_cost_signal(cost_signals, account, amount)

	net_profit = revenue - expenses
	return {
		"accounting_revenue": _round(revenue),
		"operating_expenses": _round(expenses),
		"net_profit": _round(net_profit),
		"profit_margin": _pct(net_profit, revenue),
		"income_accounts": sorted(income_accounts, key=lambda row: row["amount"], reverse=True)[:6],
		"expense_accounts": sorted(expense_accounts, key=lambda row: row["amount"], reverse=True)[:8],
		"cost_signals": {key: _round(value) for key, value in cost_signals.items()},
		"basis": "GL Entry income and expense accounts posted in the selected period.",
	}


def _empty_profitability():
	return {
		"accounting_revenue": 0,
		"operating_expenses": 0,
		"net_profit": 0,
		"profit_margin": 0,
		"income_accounts": [],
		"expense_accounts": [],
		"cost_signals": {
			"payroll": 0,
			"maintenance": 0,
			"housekeeping": 0,
			"fnb_cost": 0,
			"utilities": 0,
		},
		"basis": "No GL Entry or Account table was available for profitability.",
	}


def _bucket_cost_signal(cost_signals, account, amount):
	name = str(account or "").lower()
	if any(token in name for token in ("salary", "wage", "payroll", "staff", "labour", "labor")):
		cost_signals["payroll"] += flt(amount)
	if any(token in name for token in ("maintenance", "repair", "spare", "part")):
		cost_signals["maintenance"] += flt(amount)
	if any(token in name for token in ("housekeeping", "laundry", "cleaning", "linen", "amenity")):
		cost_signals["housekeeping"] += flt(amount)
	if any(token in name for token in ("food", "beverage", "restaurant", "kitchen", "cogs", "cost of goods")):
		cost_signals["fnb_cost"] += flt(amount)
	if any(token in name for token in ("utility", "utilities", "power", "electric", "water", "diesel", "gas")):
		cost_signals["utilities"] += flt(amount)


def _build_cashflow(from_dt, to_dt):
	if not _has_table("Payment Entry"):
		return {"cash_in": 0, "cash_out": 0, "net_cashflow": 0, "payment_modes": []}

	rows = frappe.db.sql(
		"""
		SELECT
			payment_type,
			COALESCE(NULLIF(mode_of_payment, ''), 'Unspecified') AS mode_of_payment,
			SUM(paid_amount) AS amount,
			COUNT(*) AS entry_count
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY payment_type, mode_of_payment
		ORDER BY amount DESC
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)

	cash_in = cash_out = 0
	modes = {}
	for row in rows:
		mode = _get(row, "mode_of_payment", "Unspecified")
		amount = flt(_get(row, "amount"))
		entry_count = int(_get(row, "entry_count", 0) or 0)
		if mode not in modes:
			modes[mode] = {"mode": mode, "received": 0, "paid": 0, "net": 0, "entry_count": 0}
		modes[mode]["entry_count"] += entry_count
		if _get(row, "payment_type") == "Receive":
			cash_in += amount
			modes[mode]["received"] += amount
		elif _get(row, "payment_type") == "Pay":
			cash_out += amount
			modes[mode]["paid"] += amount

	payment_modes = []
	for row in modes.values():
		row["net"] = row["received"] - row["paid"]
		payment_modes.append({
			"mode": row["mode"],
			"received": _round(row["received"]),
			"paid": _round(row["paid"]),
			"net": _round(row["net"]),
			"entry_count": row["entry_count"],
		})

	return {
		"cash_in": _round(cash_in),
		"cash_out": _round(cash_out),
		"net_cashflow": _round(cash_in - cash_out),
		"payment_modes": sorted(payment_modes, key=lambda row: abs(row["net"]), reverse=True)[:8],
	}


def _build_channel_performance(from_dt, to_dt):
	if not _has_table("Hotel Reservation"):
		return []

	rows = frappe.db.sql(
		"""
		SELECT
			COALESCE(NULLIF(source_channel, ''), NULLIF(reservation_type, ''), 'Unknown') AS channel,
			COUNT(*) AS bookings,
			SUM(number_of_nights) AS room_nights,
			SUM(COALESCE(net_total, total_amount, 0)) AS gross_revenue,
			SUM(COALESCE(ota_commission_amount, 0)) AS commission
		FROM `tabHotel Reservation`
		WHERE docstatus != 2
		  AND from_date BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY channel
		ORDER BY gross_revenue DESC
		LIMIT 8
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)
	return [
		{
			"channel": _get(row, "channel", "Unknown"),
			"bookings": int(_get(row, "bookings", 0) or 0),
			"room_nights": int(_get(row, "room_nights", 0) or 0),
			"gross_revenue": _round(_get(row, "gross_revenue")),
			"commission": _round(_get(row, "commission")),
			"net_revenue": _round(flt(_get(row, "gross_revenue")) - flt(_get(row, "commission"))),
		}
		for row in rows
	]


def _build_room_type_performance(from_dt, to_dt):
	if not _has_table("Hotel Room Check In"):
		return []

	rows = frappe.db.sql(
		"""
		SELECT
			COALESCE(NULLIF(room_type, ''), 'Unknown') AS room_type,
			COUNT(*) AS stays,
			SUM(number_of_nights) AS room_nights,
			SUM(COALESCE(rate_amount, 0) * COALESCE(NULLIF(number_of_nights, 0), 1)) AS revenue
		FROM `tabHotel Room Check In`
		WHERE docstatus = 1
		  AND DATE(check_in_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY room_type
		ORDER BY revenue DESC
		LIMIT 8
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)
	return [
		{
			"room_type": _get(row, "room_type", "Unknown"),
			"stays": int(_get(row, "stays", 0) or 0),
			"room_nights": int(_get(row, "room_nights", 0) or 0),
			"revenue": _round(_get(row, "revenue")),
			"adr": _round(flt(_get(row, "revenue")) / flt(_get(row, "room_nights"))) if flt(_get(row, "room_nights")) else 0,
		}
		for row in rows
	]




def _build_hall_bookings(from_dt, to_dt):
	if not _has_table("Hall Booking"):
		return _empty_hall_bookings()

	amount_expr = _hall_booking_amount_expr()
	status_expr = "COALESCE(NULLIF(event_status, ''), 'Scheduled')" if _has_column("Hall Booking", "event_status") else "'Scheduled'"
	payment_expr = "IFNULL(payment_status, '')" if _has_column("Hall Booking", "payment_status") else "''"
	status_select = "event_status" if _has_column("Hall Booking", "event_status") else "'Scheduled'"
	payment_select = "payment_status" if _has_column("Hall Booking", "payment_status") else "''"
	customer_select = "customer_name" if _has_column("Hall Booking", "customer_name") else "''"
	hall_select = "hall" if _has_column("Hall Booking", "hall") else "''"
	event_type_select = "event_type" if _has_column("Hall Booking", "event_type") else "''"

	status_rows = frappe.db.sql(
		f"""
		SELECT
			{status_expr} AS event_status,
			COUNT(*) AS cnt,
			SUM({amount_expr}) AS amount,
			SUM(CASE WHEN {payment_expr} NOT IN ('Paid', 'Fully Paid') THEN {amount_expr} ELSE 0 END) AS unpaid_amount
		FROM `tabHall Booking`
		WHERE docstatus = 1
		  AND DATE(start_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY event_status
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)

	summary = {
		"total_bookings": 0,
		"scheduled": 0,
		"completed": 0,
		"cancelled": 0,
		"no_show": 0,
		"revenue": 0,
		"unpaid_amount": 0,
	}
	for row in status_rows:
		status = str(_get(row, "event_status", "Scheduled") or "Scheduled").lower().replace(" ", "_")
		count = int(_get(row, "cnt", 0) or 0)
		summary["total_bookings"] += count
		if status in summary:
			summary[status] += count
		summary["revenue"] += flt(_get(row, "amount"))
		summary["unpaid_amount"] += flt(_get(row, "unpaid_amount"))

	events = frappe.db.sql(
		f"""
		SELECT
			name,
			{customer_select} AS customer_name,
			{hall_select} AS hall,
			{event_type_select} AS event_type,
			start_datetime,
			{status_select} AS event_status,
			{payment_select} AS payment_status,
			{amount_expr} AS amount
		FROM `tabHall Booking`
		WHERE docstatus = 1
		  AND DATE(start_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
		ORDER BY start_datetime ASC
		LIMIT 8
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)

	return {
		"total_bookings": summary["total_bookings"],
		"scheduled": summary["scheduled"],
		"completed": summary["completed"],
		"cancelled": summary["cancelled"],
		"no_show": summary["no_show"],
		"revenue": _round(summary["revenue"]),
		"unpaid_amount": _round(summary["unpaid_amount"]),
		"events": [
			{
				"name": _get(row, "name", ""),
				"customer_name": _get(row, "customer_name", ""),
				"hall": _get(row, "hall", ""),
				"event_type": _get(row, "event_type", ""),
				"start_datetime": str(_get(row, "start_datetime", "") or ""),
				"event_status": _get(row, "event_status", "Scheduled"),
				"payment_status": _get(row, "payment_status", ""),
				"amount": _round(_get(row, "amount")),
			}
			for row in events
		],
	}


def _empty_hall_bookings():
	return {
		"total_bookings": 0,
		"scheduled": 0,
		"completed": 0,
		"cancelled": 0,
		"no_show": 0,
		"revenue": 0,
		"unpaid_amount": 0,
		"events": [],
	}


def _hall_booking_amount_expr():
	if _has_column("Hall Booking", "net_total") and _has_column("Hall Booking", "total_amount"):
		return "COALESCE(net_total, total_amount, 0)"
	if _has_column("Hall Booking", "net_total"):
		return "COALESCE(net_total, 0)"
	if _has_column("Hall Booking", "total_amount"):
		return "COALESCE(total_amount, 0)"
	return "0"

def _build_corporate_risk(from_dt, to_dt):
	if not (_has_table("Hotel Guest") and _has_table("Sales Invoice")):
		return []

	customers = [
		_get(row, "customer")
		for row in frappe.db.sql(
			"""
			SELECT DISTINCT customer
			FROM `tabHotel Guest`
			WHERE guest_type = 'Corporate'
			  AND IFNULL(customer, '') != ''
			""",
			as_dict=True,
		)
		if _get(row, "customer")
	]
	if not customers:
		return []

	rows = frappe.db.sql(
		"""
		SELECT
			customer,
			COUNT(*) AS invoice_count,
			SUM(outstanding_amount) AS outstanding,
			SUM(CASE WHEN due_date < %(to_dt)s THEN outstanding_amount ELSE 0 END) AS overdue,
			MIN(due_date) AS oldest_due_date
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		  AND is_return = 0
		  AND outstanding_amount > 0
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		  AND customer IN %(customers)s
		GROUP BY customer
		ORDER BY overdue DESC, outstanding DESC
		LIMIT 8
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt), "customers": tuple(customers)},
		as_dict=True,
	)
	return [
		{
			"customer": _get(row, "customer", "Unknown"),
			"invoice_count": int(_get(row, "invoice_count", 0) or 0),
			"outstanding": _round(_get(row, "outstanding")),
			"overdue": _round(_get(row, "overdue")),
			"oldest_due_date": str(_get(row, "oldest_due_date", "") or ""),
		}
		for row in rows
	]

def _build_occupancy(from_dt, to_dt, finance):
	total_rooms = occupied = vacant = reserved_today = dirty = maintenance = 0
	shows_current_snapshot = getdate(from_dt) <= getdate(nowdate()) <= getdate(to_dt)
	if _has_table("Hotel Room"):
		status_rows = frappe.db.sql(
			"""
			SELECT status, COUNT(*) AS cnt
			FROM `tabHotel Room`
			GROUP BY status
			""",
			as_dict=True,
		)
		for row in status_rows:
			status = str(_get(row, "status", "") or "").lower()
			count = int(_get(row, "cnt", 0) or 0)
			total_rooms += count
			if not shows_current_snapshot:
				continue
			if status == "occupied":
				occupied += count
			elif status == "vacant":
				vacant += count
			elif status == "reserved":
				reserved_today += count
			elif status == "maintenance":
				maintenance += count

		if shows_current_snapshot and _has_column("Hotel Room", "housekeeping_status"):
			dirty = int(_get(_first(frappe.db.sql(
				"""
				SELECT COUNT(*) AS cnt
				FROM `tabHotel Room`
				WHERE housekeeping_status = 'Dirty'
				""",
				as_dict=True,
			)), "cnt", 0) or 0)

	room_revenue = flt(next((row.get("amount") for row in _build_revenue_mix(from_dt, to_dt) if row.get("category") == "Rooms"), 0))
	room_nights = 0
	if _has_table("Hotel Room Check In"):
		room_nights = flt(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS room_nights
			FROM `tabHotel Room Check In`
			WHERE docstatus = 1
			  AND DATE(expected_check_out_datetime) >= %(from_dt)s
			  AND DATE(check_in_datetime) <= %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "room_nights", 0))

	period_days = max(1, (getdate(to_dt) - getdate(from_dt)).days + 1)
	available_room_nights = max(0, total_rooms * period_days)
	occupancy_rate = _pct(room_nights, available_room_nights)
	adr = _round(room_revenue / room_nights) if room_nights else 0
	revpar = _round(room_revenue / available_room_nights) if available_room_nights else 0

	return {
		"total_rooms": int(total_rooms),
		"occupied": int(occupied),
		"vacant": int(vacant),
		"reserved": int(reserved_today),
		"dirty": int(dirty),
		"maintenance": int(maintenance),
		"room_nights": int(room_nights),
		"occupancy_rate": occupancy_rate,
		"adr": adr,
		"revpar": revpar,
		"room_revenue": _round(room_revenue or finance.get("period_invoiced", 0)),
	}


def _build_cash_control(from_dt, to_dt):
	if not _has_table("POS Invoice"):
		return {
			"pos_sales": 0,
			"open_drafts": 0,
			"active_terminals": 0,
			"shift_differences": 0,
			"outlets": [],
		}

	pos_sales = _get(_first(frappe.db.sql(
		"""
		SELECT SUM(grand_total) AS amount
		FROM `tabPOS Invoice`
		WHERE docstatus = 1
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)), "amount", 0)
	open_drafts = frappe.db.count("POS Invoice", {"docstatus": 0})
	active_terminals = 0
	if _has_table("POS Opening Entry"):
		active_terminals = frappe.db.count("POS Opening Entry", {"docstatus": 1, "status": "Open"})

	shift_differences = 0
	if _has_table("POS Closing Entry") and _has_table("POS Closing Entry Detail"):
		shift_differences = _get(_first(frappe.db.sql(
			"""
			SELECT SUM(ABS(d.difference)) AS amount
			FROM `tabPOS Closing Entry` ce
			INNER JOIN `tabPOS Closing Entry Detail` d ON d.parent = ce.name
			WHERE ce.docstatus = 1
			  AND ce.posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "amount", 0)

	outlet_rows = frappe.db.sql(
		"""
		SELECT COALESCE(pos_profile, 'Unknown') AS outlet, SUM(grand_total) AS amount
		FROM `tabPOS Invoice`
		WHERE docstatus = 1
		  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
		GROUP BY pos_profile
		ORDER BY amount DESC
		LIMIT 5
		""",
		{"from_dt": str(from_dt), "to_dt": str(to_dt)},
		as_dict=True,
	)
	total = sum(flt(_get(row, "amount")) for row in outlet_rows)
	return {
		"pos_sales": _round(pos_sales),
		"open_drafts": int(open_drafts or 0),
		"active_terminals": int(active_terminals or 0),
		"shift_differences": _round(shift_differences),
		"outlets": [
			{"name": _get(row, "outlet", "Unknown"), "amount": _round(_get(row, "amount")), "share": _pct(_get(row, "amount"), total)}
			for row in outlet_rows
		],
	}


def _build_operations(from_dt, to_dt):
	arrivals = departures = overdue_checkouts = unpaid_folios = 0
	if _has_table("Hotel Reservation"):
		arrivals = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabHotel Reservation`
			WHERE docstatus != 2
			  AND reservation_status IN ('Confirmed', 'Reserved', 'Hold')
			  AND from_date BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)
	if _has_table("Hotel Room Check In"):
		departures = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabHotel Room Check In`
			WHERE docstatus = 1
			  AND DATE(expected_check_out_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)
		overdue_checkouts = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabHotel Room Check In`
			WHERE docstatus = 1
			  AND status = 'Checked In'
			  AND DATE(expected_check_out_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
			  AND expected_check_out_datetime < NOW()
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)
		if _has_column("Hotel Room Check In", "total_outstanding_amount"):
			unpaid_folios = int(_get(_first(frappe.db.sql(
				"""
				SELECT COUNT(*) AS cnt
				FROM `tabHotel Room Check In`
				WHERE docstatus = 1
				  AND status = 'Checked In'
				  AND total_outstanding_amount > 0
				  AND DATE(check_in_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
				""",
				{"from_dt": str(from_dt), "to_dt": str(to_dt)},
				as_dict=True,
			)), "cnt", 0) or 0)

	housekeeping_attention = 0
	if _has_table("Housekeeping Task") and _has_column("Housekeeping Task", "status") and _has_column("Housekeeping Task", "creation"):
		housekeeping_attention = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabHousekeeping Task`
			WHERE status IN ('Pending', 'Assigned', 'In Progress', 'On Hold')
			  AND DATE(creation) BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)

	maintenance_attention = 0
	if _has_table("Maintenance Task") and _has_column("Maintenance Task", "status") and _has_column("Maintenance Task", "creation"):
		maintenance_attention = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabMaintenance Task`
			WHERE status NOT IN ('Done', 'Cancelled')
			  AND DATE(creation) BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)

	hall_pending = 0
	if _has_table("Hall Booking"):
		hall_pending = int(_get(_first(frappe.db.sql(
			"""
			SELECT COUNT(*) AS cnt
			FROM `tabHall Booking`
			WHERE docstatus = 1
			  AND start_datetime BETWEEN %(from_dt)s AND %(to_dt)s
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)), "cnt", 0) or 0)

	return {
		"arrivals": arrivals,
		"departures": departures,
		"overdue_checkouts": overdue_checkouts,
		"unpaid_folios": unpaid_folios,
		"housekeeping_attention": housekeeping_attention,
		"maintenance_attention": maintenance_attention,
		"hall_events": hall_pending,
	}


def _build_trends(from_dt, to_dt):
	rows = []
	if _has_table("Sales Invoice"):
		rows = frappe.db.sql(
			"""
			SELECT posting_date, SUM(grand_total) AS revenue, SUM(outstanding_amount) AS outstanding
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			  AND is_return = 0
			  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			GROUP BY posting_date
			ORDER BY posting_date ASC
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		)
	if rows:
		return [
			{
				"date": str(_get(row, "posting_date", "")),
				"revenue": _round(_get(row, "revenue")),
				"outstanding": _round(_get(row, "outstanding")),
				"source": "Invoices",
			}
			for row in rows
		]

	fallback_rows = []
	if _has_table("Hotel Reservation"):
		fallback_rows.extend(frappe.db.sql(
			"""
			SELECT from_date AS revenue_date, SUM(COALESCE(net_total, total_amount, 0)) AS revenue, 'Reservations' AS source
			FROM `tabHotel Reservation`
			WHERE docstatus != 2
			  AND from_date BETWEEN %(from_dt)s AND %(to_dt)s
			GROUP BY from_date
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		))
	if _has_table("POS Invoice"):
		fallback_rows.extend(frappe.db.sql(
			"""
			SELECT posting_date AS revenue_date, SUM(grand_total) AS revenue, 'POS' AS source
			FROM `tabPOS Invoice`
			WHERE docstatus = 1
			  AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
			GROUP BY posting_date
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		))
	if _has_table("Hall Booking"):
		hall_amount_expr = _hall_booking_amount_expr()
		fallback_rows.extend(frappe.db.sql(
			f"""
			SELECT DATE(start_datetime) AS revenue_date, SUM({hall_amount_expr}) AS revenue, 'Halls' AS source
			FROM `tabHall Booking`
			WHERE docstatus = 1
			  AND DATE(start_datetime) BETWEEN %(from_dt)s AND %(to_dt)s
			GROUP BY DATE(start_datetime)
			""",
			{"from_dt": str(from_dt), "to_dt": str(to_dt)},
			as_dict=True,
		))

	by_date = {}
	for row in fallback_rows:
		date = str(_get(row, "revenue_date", ""))
		if not date:
			continue
		if date not in by_date:
			by_date[date] = {"date": date, "revenue": 0, "outstanding": 0, "sources": set()}
		by_date[date]["revenue"] += flt(_get(row, "revenue"))
		by_date[date]["sources"].add(_get(row, "source", "Other"))

	return [
		{
			"date": date,
			"revenue": _round(row["revenue"]),
			"outstanding": 0,
			"source": ", ".join(sorted(row["sources"])),
		}
		for date, row in sorted(by_date.items())
	]


def _build_watchlist(finance, profitability, cashflow, occupancy, cash_control, operations, corporate_risk, from_dt, to_dt):
	items = []
	shows_current_snapshot = getdate(from_dt) <= getdate(nowdate()) <= getdate(to_dt)
	if profitability.get("net_profit", 0) < 0:
		items.append(_watch("Period operating loss", abs(profitability["net_profit"]), "High", "Review expense accounts and revenue leakage for this period.", "/reports", "money"))
	elif profitability.get("accounting_revenue", 0) > 0 and profitability.get("profit_margin", 0) < 15:
		items.append(_watch("Low profit margin", profitability["profit_margin"], "Medium", "Margin is below the owner attention threshold.", "/reports", "percent"))
	if cashflow.get("net_cashflow", 0) < 0:
		items.append(_watch("Negative net cashflow", abs(cashflow["net_cashflow"]), "High", "Payments out are higher than receipts in this period.", "/billing", "money"))
	if finance.get("total_overdue", 0) > 0:
		items.append(_watch("Overdue receivables", finance["total_overdue"], "High", "Collect or follow up overdue customer balances.", "/billing", "money"))
	corporate_overdue = sum(flt(row.get("overdue", 0)) for row in corporate_risk)
	if corporate_overdue > 0:
		items.append(_watch("Corporate overdue exposure", corporate_overdue, "High", "Corporate accounts have unpaid overdue invoices.", "/billing", "money"))
	if operations.get("unpaid_folios", 0) > 0:
		items.append(_watch("Unsettled in-house folios", operations["unpaid_folios"], "High", "Resolve guest balances before departure.", "/room-view"))
	if finance.get("unallocated_payments_count", 0) > 0:
		items.append(_watch("Unallocated receipts", finance["unallocated_payments_count"], "Medium", "Allocate customer payments to invoices.", "/billing/reconcile"))
	if shows_current_snapshot and cash_control.get("open_drafts", 0) > 0:
		items.append(_watch("Open POS drafts", cash_control["open_drafts"], "Medium", "Review held POS invoices and close stale drafts.", "/pos/manager-dashboard"))
	if cash_control.get("shift_differences", 0) > 0:
		items.append(_watch("POS shift differences", cash_control["shift_differences"], "High", "Review cash and card differences from POS closing.", "/pos/shift-difference-log", "money"))
	if shows_current_snapshot and occupancy.get("dirty", 0) > 0:
		items.append(_watch("Dirty rooms", occupancy["dirty"], "Medium", "Clean rooms to restore sellable inventory.", "/housekeeping/dashboard"))
	if shows_current_snapshot and occupancy.get("maintenance", 0) > 0:
		items.append(_watch("Rooms in maintenance", occupancy["maintenance"], "Medium", "Review rooms blocked from sale.", "/maintenance/dashboard"))
	if not items:
		items.append(_watch("No executive risks", 0, "Good", "No major finance or operational risk flags in this dashboard.", "/billing"))
	return items[:8]


def _watch(title, value, severity, detail, route, value_type="count"):
	return {
		"title": title,
		"value": value,
		"value_type": value_type,
		"severity": severity,
		"detail": detail,
		"route": route,
	}
