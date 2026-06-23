import frappe
from frappe.utils import (
	nowdate,
	getdate,
	get_datetime,
	add_days,
	flt,
	cint,
	format_datetime,
)


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


def _money(value):
	return flt(value or 0, 2)


def _date_or_default(value, default_value):
	try:
		return getdate(value) if value else getdate(default_value)
	except Exception:
		return getdate(default_value)


def _dt_label(value):
	if not value:
		return ""
	try:
		return format_datetime(value, "dd-MM-yyyy HH:mm")
	except Exception:
		return str(value)


def _get_payment_status(amount, paid_amount, outstanding):
	amount = flt(amount or 0)
	paid_amount = flt(paid_amount or 0)
	outstanding = flt(outstanding or 0)

	if amount <= 0:
		return ""

	if outstanding <= 0 or paid_amount >= amount:
		return "Paid"

	if paid_amount > 0:
		return "Part Payment"

	return "Unpaid"


def _get_room_status(room_status, housekeeping_status, checkin, range_end_dt=None):
	if checkin:
		expected_checkout = checkin.get("expected_check_out_datetime")
		# A room is overdue if its expected checkout is before the END of the
		# selected date range. This makes the report consistent when run for a
		# historical period — rooms overdue in April show as overdue when you
		# query April, not just rooms that are overdue right now.
		compare_dt = range_end_dt if range_end_dt else get_datetime()
		if expected_checkout and get_datetime(expected_checkout) < compare_dt:
			return "Overdue Check-Out"
		return "Occupied"

	if room_status == "Maintenance":
		return "Maintenance"

	if room_status == "Occupied":
		return "Occupied"

	if housekeeping_status == "Dirty":
		return "Vacant Dirty"

	return "Vacant Clean"


def _get_invoice_totals(checkin_names):
	totals = {}

	if not checkin_names:
		return totals

	for name in checkin_names:
		totals[name] = {
			"amount": 0,
			"outstanding": 0,
			"paid_amount": 0,
		}

	placeholders = ", ".join(["%s"] * len(checkin_names))

	if _has_doctype("Sales Invoice") and _has_column("Sales Invoice", "custom_hotel_room_check_in"):
		rows = frappe.db.sql(
			"""
			SELECT
				custom_hotel_room_check_in AS checkin,
				SUM(grand_total) AS amount,
				SUM(outstanding_amount) AS outstanding
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			  AND custom_hotel_room_check_in IN ({0})
			GROUP BY custom_hotel_room_check_in
			""".format(placeholders),
			tuple(checkin_names),
			as_dict=True,
		)

		for row in rows:
			if row.checkin in totals:
				totals[row.checkin]["amount"] += flt(row.amount)
				totals[row.checkin]["outstanding"] += flt(row.outstanding)

	if _has_doctype("POS Invoice") and _has_column("POS Invoice", "custom_hotel_room_check_in"):
		rows = frappe.db.sql(
			"""
			SELECT
				custom_hotel_room_check_in AS checkin,
				SUM(grand_total) AS amount,
				SUM(outstanding_amount) AS outstanding
			FROM `tabPOS Invoice`
			WHERE docstatus = 1
			  AND custom_hotel_room_check_in IN ({0})
			GROUP BY custom_hotel_room_check_in
			""".format(placeholders),
			tuple(checkin_names),
			as_dict=True,
		)

		for row in rows:
			if row.checkin in totals:
				totals[row.checkin]["amount"] += flt(row.amount)
				totals[row.checkin]["outstanding"] += flt(row.outstanding)

	if _has_doctype("Payment Entry") and _has_column("Payment Entry", "custom_hotel_room_check_in"):
		rows = frappe.db.sql(
			"""
			SELECT
				custom_hotel_room_check_in AS checkin,
				SUM(paid_amount) AS paid_amount
			FROM `tabPayment Entry`
			WHERE docstatus = 1
			  AND payment_type = 'Receive'
			  AND custom_hotel_room_check_in IN ({0})
			GROUP BY custom_hotel_room_check_in
			""".format(placeholders),
			tuple(checkin_names),
			as_dict=True,
		)

		for row in rows:
			if row.checkin in totals:
				totals[row.checkin]["paid_amount"] += flt(row.paid_amount)

	for name in totals:
		amount = flt(totals[name]["amount"])
		outstanding = flt(totals[name]["outstanding"])
		paid_amount = flt(totals[name]["paid_amount"])

		if paid_amount <= 0 and amount > 0:
			paid_amount = amount - outstanding

		totals[name]["paid_amount"] = max(flt(paid_amount), 0)

	return totals


@frappe.whitelist()
def get_daily_occupancy_report(
	date_from=None,
	date_to=None,
	room=None,
	floor=None,
	status=None,
	payment=None,
	search=None,
	overdue_only=0,
):
	overdue_only = cint(overdue_only or 0)

	# Default: show today's snapshot when no date range is supplied.
	# When date_from is provided without date_to, make it a single-day view.
	date_from = _date_or_default(date_from, nowdate())
	date_to   = _date_or_default(date_to, date_from) if date_to else date_from

	from_dt = get_datetime(str(date_from) + " 00:00:00")
	to_dt   = get_datetime(str(date_to)   + " 23:59:59")

	# Use raw SQL for a full room inventory snapshot to avoid any implicit
	# list limits or permission-side truncation.
	rooms = frappe.db.sql(
		"""
		SELECT
			name,
			room_number,
			room_type,
			floor,
			status,
			housekeeping_status,
			base_rate,
			owner,
			creation
		FROM `tabHotel Room`
		ORDER BY room_number ASC
		""",
		as_dict=True,
	)

	# Fetch all check-ins that were active at any point within the date range.
	# "Active" means: checked in before end of range AND (expected or actual)
	# checkout falls after start of range AND status is Checked In.
	checkins = frappe.db.sql(
		"""
		SELECT
			ci.name,
			ci.room_number,
			ci.room_type,
			ci.guest,
			ci.check_in_datetime,
			ci.expected_check_out_datetime,
			ci.actual_check_out_datetime,
			ci.number_of_nights,
			ci.rate_amount,
			ci.discount,
			ci.total_charges,
			ci.total_outstanding_amount,
			ci.owner,
			ci.status,
			g.hotel_guest_name AS guest_name
		FROM `tabHotel Room Check In` ci
		LEFT JOIN `tabHotel Guest` g ON g.name = ci.guest
		WHERE ci.docstatus != 2
		  AND ci.status = 'Checked In'
		  AND ci.check_in_datetime <= %s
		  AND IFNULL(ci.actual_check_out_datetime, ci.expected_check_out_datetime) >= %s
		ORDER BY ci.check_in_datetime DESC
		""",
		(to_dt, from_dt),
		as_dict=True,
	)

	checkin_by_room = {}
	for ci in checkins:
		if ci.room_number and ci.room_number not in checkin_by_room:
			checkin_by_room[ci.room_number] = ci

	invoice_totals = _get_invoice_totals([ci.name for ci in checkins])

	rows = []
	for r in rooms:
		ci  = checkin_by_room.get(r.name) or checkin_by_room.get(r.room_number)
		inv = invoice_totals.get(ci.name, {}) if ci else {}

		amount      = _money(inv.get("amount")      or (ci.get("total_charges")           if ci else 0))
		outstanding = _money(inv.get("outstanding") or (ci.get("total_outstanding_amount") if ci else 0))
		paid_amount = _money(inv.get("paid_amount") or max(amount - outstanding, 0))

		# Pass to_dt so overdue is evaluated against the END of the selected
		# range, not against the current clock. This makes the report consistent:
		# if you run it for April, rooms that were overdue in April show as
		# overdue, not rooms that are overdue today.
		row_status     = _get_room_status(r.status, r.housekeeping_status, ci, to_dt)
		payment_status = _get_payment_status(amount, paid_amount, outstanding)

		row = {
			"checkin_id":    ci.name if ci else "",
			"room_number":   r.room_number or r.name,
			"room":          r.name,
			"room_type":     (ci.room_type if ci else r.room_type) or "",
			"floor":         r.floor or "",
			"status":        row_status,
			"guest":         (ci.guest_name or ci.guest) if ci else "",
			"guest_id":      ci.guest if ci else "",
			"checkin":       _dt_label(ci.check_in_datetime) if ci else "",
			"checkout":      _dt_label(ci.actual_check_out_datetime or ci.expected_check_out_datetime) if ci else "",
			"nights":        cint(ci.number_of_nights) if ci else 0,
			"rate":          _money((ci.rate_amount if ci else 0) or r.base_rate),
			"discount":      _money(ci.discount) if ci else 0,
			"amount":        amount,
			"paid_amount":   paid_amount,
			"outstanding":   outstanding,
			"payment_status": payment_status,
			"created_by":    ci.owner if ci else r.owner,
		}

		rows.append(row)

	# ── Summary cards — derived ONLY from checkin data for the date range ───────
	# We compute these separately from the table rows so that the Hotel Room
	# status fallback (used for the table) does not pollute the card numbers.
	# A room counts as "occupied" for the cards only if a matching checkin
	# exists in the date-range query — not because Hotel Room.status = Occupied.
	total_rooms          = len(rooms)
	checkin_room_numbers = set(ci.room_number for ci in checkins if ci.room_number)

	# Occupied: rooms that have an active checkin overlapping the date range
	all_occupied = len(checkin_room_numbers)

	# Vacant: all rooms that do NOT have an active checkin in the range
	all_vacant = total_rooms - all_occupied

	# Overdue: checkins whose expected checkout is before the end of the range
	all_overdue = len([
		ci for ci in checkins
		if ci.get("expected_check_out_datetime")
		and get_datetime(ci.get("expected_check_out_datetime")) < to_dt
	])

	# Outstanding: sum of unpaid balances for checkins in the date range
	checkin_names_in_range = [ci.name for ci in checkins]
	if checkin_names_in_range:
		inv_totals_for_range = _get_invoice_totals(checkin_names_in_range)
		all_outstanding = _money(sum(
			flt(v.get("outstanding")) for v in inv_totals_for_range.values()
		))
		# Fall back to check-in field if no invoices exist
		if all_outstanding == 0:
			all_outstanding = _money(sum(
				flt(ci.get("total_outstanding_amount")) for ci in checkins
			))
	else:
		all_outstanding = 0

	# ── Revenue breakdown for the date range ─────────────────────────────────
	# Room revenue: Sales Invoices linked to check-ins in the range
	room_revenue = 0
	pos_revenue  = 0
	total_collected = 0

	if checkin_names_in_range:
		placeholders = ", ".join(["%s"] * len(checkin_names_in_range))

		if _has_doctype("Sales Invoice") and _has_column("Sales Invoice", "custom_hotel_room_check_in"):
			si_rows = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(grand_total), 0) AS total
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				  AND custom_hotel_room_check_in IN ({0})
				""".format(placeholders),
				tuple(checkin_names_in_range),
				as_dict=True,
			)
			room_revenue = _money(si_rows[0].total if si_rows else 0)

		if _has_doctype("POS Invoice") and _has_column("POS Invoice", "custom_hotel_room_check_in"):
			pos_rows = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(grand_total), 0) AS total
				FROM `tabPOS Invoice`
				WHERE docstatus = 1
				  AND custom_hotel_room_check_in IN ({0})
				""".format(placeholders),
				tuple(checkin_names_in_range),
				as_dict=True,
			)
			pos_revenue = _money(pos_rows[0].total if pos_rows else 0)

		if _has_doctype("Payment Entry") and _has_column("Payment Entry", "custom_hotel_room_check_in"):
			pe_rows = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(paid_amount), 0) AS total
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND payment_type = 'Receive'
				  AND custom_hotel_room_check_in IN ({0})
				""".format(placeholders),
				tuple(checkin_names_in_range),
				as_dict=True,
			)
			total_collected = _money(pe_rows[0].total if pe_rows else 0)

	# Arrivals: check-ins that started within the date range
	arrivals = frappe.db.count(
		"Hotel Room Check In",
		{
			"docstatus": ["!=", 2],
			"status":    "Checked In",
			"check_in_datetime": ["between", [from_dt, to_dt]],
		},
	)

	# Departures: expected checkouts that fall within the date range
	departures = frappe.db.count(
		"Hotel Room Check In",
		{
			"docstatus": ["!=", 2],
			"status":    "Checked In",
			"expected_check_out_datetime": ["between", [from_dt, to_dt]],
		},
	)

	stats = {
		"occupancyRate":   round((all_occupied / total_rooms) * 100, 1) if total_rooms else 0,
		"totalRooms":      total_rooms,
		"occupiedRooms":   all_occupied,
		"vacantRooms":     all_vacant,
		"arrivals":        arrivals,
		"departures":      departures,
		"outstanding":     all_outstanding,
		"overdueCheckOut": all_overdue,
		"roomRevenue":     room_revenue,
		"posRevenue":      pos_revenue,
		"totalCollected":  total_collected,
		"totalRevenue":    _money(room_revenue + pos_revenue),
	}

	# ── Now apply user-driven filters to the table rows ───────────────────────
	if overdue_only:
		rows = [r for r in rows if r["status"] == "Overdue Check-Out"]

	if room:
		rows = [r for r in rows if str(r["room_number"]) == str(room) or str(r["room"]) == str(room)]

	if floor:
		# r["floor"] is the Hotel Floor document name (e.g. "1st Floor", "Ground", "2")
		# Compare directly — the dropdown now sends the real doc name from the API.
		rows = [r for r in rows if str(r.get("floor") or "") == str(floor)]

	if status:
		rows = [r for r in rows if r["status"] == status]

	if payment:
		rows = [r for r in rows if r["payment_status"] == payment]

	if search:
		q = str(search).lower().strip()
		rows = [
			r
			for r in rows
			if q in str(r.get("checkin_id") or "").lower()
			or q in str(r.get("room_number") or "").lower()
			or q in str(r.get("guest") or "").lower()
			or q in str(r.get("room_type") or "").lower()
			or q in str(r.get("status") or "").lower()
			or q in str(r.get("created_by") or "").lower()
		]

	# Totals are computed on filtered rows (the visible table rows)
	totals = {
		"nights": sum(cint(r.get("nights")) for r in rows),
		"discount": _money(sum(flt(r.get("discount")) for r in rows)),
		"amount": _money(sum(flt(r.get("amount")) for r in rows)),
		"paid_amount": _money(sum(flt(r.get("paid_amount")) for r in rows)),
		"outstanding": _money(sum(flt(r.get("outstanding")) for r in rows)),
	}

	return {
		"rows": rows,
		"stats": stats,
		"totals": totals,
		"rooms": sorted(list(set([r.get("room_number") for r in rows if r.get("room_number")]))),
		"floors": sorted(list(set([r.get("floor") for r in rows if r.get("floor")]))),
		"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
		"filters": {
			"date_from": str(date_from),
			"date_to": str(date_to),
		},
	}