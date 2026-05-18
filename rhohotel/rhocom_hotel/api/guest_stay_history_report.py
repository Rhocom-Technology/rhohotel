# import frappe
# from frappe.utils import (
# 	nowdate,
# 	getdate,
# 	get_datetime,
# 	flt,
# 	cint,
# 	format_datetime,
# )


# def _money(value):
# 	return flt(value or 0, 2)


# def _date_or_default(value, default_value):
# 	try:
# 		return getdate(value) if value else getdate(default_value)
# 	except Exception:
# 		return getdate(default_value)


# def _dt_label(value):
# 	if not value:
# 		return ""
# 	try:
# 		return format_datetime(value, "dd-MM-yyyy HH:mm")
# 	except Exception:
# 		return str(value)


# def _date_label(value):
# 	if not value:
# 		return ""
# 	try:
# 		return format_datetime(value, "dd-MM-yyyy")
# 	except Exception:
# 		return str(value)


# def _has_doctype(doctype):
# 	try:
# 		return bool(frappe.db.exists("DocType", doctype))
# 	except Exception:
# 		return False


# def _has_column(doctype, column):
# 	try:
# 		return bool(frappe.db.has_column(doctype, column))
# 	except Exception:
# 		return False


# def _get_invoice_totals(checkin_names):
# 	totals = {}

# 	if not checkin_names:
# 		return totals

# 	for name in checkin_names:
# 		totals[name] = {
# 			"amount": 0,
# 			"outstanding": 0,
# 			"paid_amount": 0,
# 		}

# 	placeholders = ", ".join(["%s"] * len(checkin_names))

# 	if _has_doctype("Sales Invoice") and _has_column("Sales Invoice", "custom_hotel_room_check_in"):
# 		rows = frappe.db.sql(
# 			"""
# 			SELECT
# 				custom_hotel_room_check_in AS checkin,
# 				SUM(grand_total) AS amount,
# 				SUM(outstanding_amount) AS outstanding
# 			FROM `tabSales Invoice`
# 			WHERE docstatus = 1
# 			  AND custom_hotel_room_check_in IN ({0})
# 			GROUP BY custom_hotel_room_check_in
# 			""".format(placeholders),
# 			tuple(checkin_names),
# 			as_dict=True,
# 		)

# 		for row in rows:
# 			if row.checkin in totals:
# 				totals[row.checkin]["amount"] += flt(row.amount)
# 				totals[row.checkin]["outstanding"] += flt(row.outstanding)

# 	if _has_doctype("POS Invoice") and _has_column("POS Invoice", "custom_hotel_room_check_in"):
# 		rows = frappe.db.sql(
# 			"""
# 			SELECT
# 				custom_hotel_room_check_in AS checkin,
# 				SUM(grand_total) AS amount,
# 				SUM(outstanding_amount) AS outstanding
# 			FROM `tabPOS Invoice`
# 			WHERE docstatus = 1
# 			  AND custom_hotel_room_check_in IN ({0})
# 			GROUP BY custom_hotel_room_check_in
# 			""".format(placeholders),
# 			tuple(checkin_names),
# 			as_dict=True,
# 		)

# 		for row in rows:
# 			if row.checkin in totals:
# 				totals[row.checkin]["amount"] += flt(row.amount)
# 				totals[row.checkin]["outstanding"] += flt(row.outstanding)

# 	if _has_doctype("Payment Entry") and _has_column("Payment Entry", "custom_hotel_room_check_in"):
# 		rows = frappe.db.sql(
# 			"""
# 			SELECT
# 				custom_hotel_room_check_in AS checkin,
# 				SUM(paid_amount) AS paid_amount
# 			FROM `tabPayment Entry`
# 			WHERE docstatus = 1
# 			  AND payment_type = 'Receive'
# 			  AND custom_hotel_room_check_in IN ({0})
# 			GROUP BY custom_hotel_room_check_in
# 			""".format(placeholders),
# 			tuple(checkin_names),
# 			as_dict=True,
# 		)

# 		for row in rows:
# 			if row.checkin in totals:
# 				totals[row.checkin]["paid_amount"] += flt(row.paid_amount)

# 	for name in totals:
# 		amount = flt(totals[name]["amount"])
# 		outstanding = flt(totals[name]["outstanding"])
# 		paid_amount = flt(totals[name]["paid_amount"])

# 		if paid_amount <= 0 and amount > 0:
# 			paid_amount = amount - outstanding

# 		totals[name]["paid_amount"] = max(flt(paid_amount), 0)

# 	return totals


# def _classify_guest_type(guest_doc, checkin_count):
# 	"""Classify guest type based on guest data and visit count."""
# 	guest_type = guest_doc.get("guest_type") or ""

# 	if guest_type == "Corporate":
# 		return "Corporate"

# 	loyalty = guest_doc.get("loyalty_tier") or ""
# 	if loyalty in ("Platinum", "Gold", "VIP"):
# 		return "VIP"

# 	if checkin_count >= 3:
# 		return "Repeat"

# 	if checkin_count == 1:
# 		return "New"

# 	return "Repeat" if checkin_count > 1 else "New"


# def _get_payment_status(amount, paid_amount, outstanding):
# 	amount = flt(amount or 0)
# 	paid_amount = flt(paid_amount or 0)
# 	outstanding = flt(outstanding or 0)

# 	if amount <= 0:
# 		return "Settled"

# 	if outstanding <= 0 or paid_amount >= amount:
# 		return "Settled"

# 	if paid_amount > 0:
# 		return "Part Paid"

# 	return "Outstanding"


# @frappe.whitelist()
# def get_guest_stay_history(
# 	date_from=None,
# 	date_to=None,
# 	guest_type=None,
# 	room_type=None,
# 	payment=None,
# 	source=None,
# 	search=None,
# ):
# 	date_from = _date_or_default(date_from, nowdate())
# 	date_to = _date_or_default(date_to, nowdate())

# 	from_dt = get_datetime(str(date_from) + " 00:00:00")
# 	to_dt = get_datetime(str(date_to) + " 23:59:59")

# 	# Get all check-ins within date range
# 	checkins = frappe.db.sql(
# 		"""
# 		SELECT
# 			ci.name,
# 			ci.guest,
# 			ci.room_number,
# 			ci.room_type,
# 			ci.check_in_datetime,
# 			ci.expected_check_out_datetime,
# 			ci.actual_check_out_datetime,
# 			ci.number_of_nights,
# 			ci.rate_amount,
# 			ci.discount,
# 			ci.total_charges,
# 			ci.total_outstanding_amount,
# 			ci.reservation_source,
# 			ci.status,
# 			ci.owner,
# 			g.hotel_guest_name AS guest_name,
# 			g.phone_number,
# 			g.contact_number,
# 			g.guest_type AS g_guest_type,
# 			g.loyalty_tier,
# 			g.preference,
# 			g.notes AS guest_notes
# 		FROM `tabHotel Room Check In` ci
# 		LEFT JOIN `tabHotel Guest` g ON g.name = ci.guest
# 		WHERE ci.docstatus != 2
# 		  AND ci.check_in_datetime BETWEEN %s AND %s
# 		ORDER BY ci.check_in_datetime DESC
# 		""",
# 		(from_dt, to_dt),
# 		as_dict=True,
# 	)

# 	# Count total check-ins per guest for repeat classification
# 	guest_names = list(set(ci.guest for ci in checkins if ci.guest))
# 	guest_checkin_counts = {}

# 	if guest_names:
# 		placeholders = ", ".join(["%s"] * len(guest_names))
# 		counts = frappe.db.sql(
# 			"""
# 			SELECT guest, COUNT(*) AS cnt
# 			FROM `tabHotel Room Check In`
# 			WHERE docstatus != 2 AND guest IN ({0})
# 			GROUP BY guest
# 			""".format(placeholders),
# 			tuple(guest_names),
# 			as_dict=True,
# 		)
# 		for c in counts:
# 			guest_checkin_counts[c.guest] = cint(c.cnt)

# 	# Get last visit dates per guest (most recent check-in before the current one)
# 	guest_last_visits = {}
# 	if guest_names:
# 		placeholders = ", ".join(["%s"] * len(guest_names))
# 		visits = frappe.db.sql(
# 			"""
# 			SELECT guest, MAX(check_in_datetime) AS last_visit
# 			FROM `tabHotel Room Check In`
# 			WHERE docstatus != 2
# 			  AND guest IN ({0})
# 			  AND check_in_datetime < %s
# 			GROUP BY guest
# 			""".format(placeholders),
# 			tuple(guest_names) + (from_dt,),
# 			as_dict=True,
# 		)
# 		for v in visits:
# 			guest_last_visits[v.guest] = v.last_visit

# 	# Get invoice/payment totals
# 	checkin_names = [ci.name for ci in checkins]
# 	invoice_totals = _get_invoice_totals(checkin_names)

# 	# Get reservation source names
# 	source_names = list(set(ci.reservation_source for ci in checkins if ci.reservation_source))
# 	source_map = {}
# 	if source_names:
# 		sources = frappe.get_all(
# 			"Market Place",
# 			filters={"name": ["in", source_names]},
# 			fields=["name", "market_place_name"],
# 		)
# 		source_map = {s.name: s.market_place_name or s.name for s in sources}

# 	# Get room numbers
# 	room_names = list(set(ci.room_number for ci in checkins if ci.room_number))
# 	room_map = {}
# 	if room_names:
# 		rooms = frappe.get_all(
# 			"Hotel Room",
# 			filters={"name": ["in", room_names]},
# 			fields=["name", "room_number"],
# 		)
# 		room_map = {r.name: r.room_number or r.name for r in rooms}

# 	# Build rows
# 	rows = []
# 	for ci in checkins:
# 		inv = invoice_totals.get(ci.name, {})

# 		amount = _money(inv.get("amount") or ci.total_charges or 0)
# 		outstanding = _money(inv.get("outstanding") or ci.total_outstanding_amount or 0)
# 		paid_amount = _money(inv.get("paid_amount") or max(amount - outstanding, 0))

# 		checkin_count = guest_checkin_counts.get(ci.guest, 1)
# 		guest_type_val = _classify_guest_type(
# 			{"guest_type": ci.g_guest_type, "loyalty_tier": ci.loyalty_tier},
# 			checkin_count,
# 		)

# 		source_label = source_map.get(ci.reservation_source, ci.reservation_source or "Walk-in")
# 		if not source_label:
# 			source_label = "Walk-in"

# 		payment_status = _get_payment_status(amount, paid_amount, outstanding)

# 		phone = ci.phone_number or ci.contact_number or ""
# 		if ci.g_guest_type == "Corporate":
# 			phone = "Corporate"

# 		last_visit = guest_last_visits.get(ci.guest)
# 		last_visit_label = _date_label(last_visit) if last_visit else "First Visit"

# 		room_display = room_map.get(ci.room_number, ci.room_number or "")

# 		preference = ci.preference or ci.guest_notes or ""
# 		if len(preference) > 40:
# 			preference = preference[:40] + "..."

# 		nights = cint(ci.number_of_nights) or 1

# 		row = {
# 			"id": ci.name,
# 			"guestId": ci.guest or "",
# 			"guestName": ci.guest_name or ci.guest or "",
# 			"phone": phone,
# 			"room": room_display,
# 			"room_type": ci.room_type or "",
# 			"checkin": _dt_label(ci.check_in_datetime),
# 			"checkout": _dt_label(ci.actual_check_out_datetime or ci.expected_check_out_datetime),
# 			"nights": nights,
# 			"type": guest_type_val,
# 			"totalSpend": amount,
# 			"balance": outstanding,
# 			"status": payment_status,
# 			"source": source_label,
# 			"lastVisit": last_visit_label,
# 			"notes": preference,
# 		}

# 		rows.append(row)

# 	# Apply filters
# 	if guest_type:
# 		rows = [r for r in rows if r["type"] == guest_type]

# 	if room_type:
# 		rows = [r for r in rows if r["room_type"] == room_type]

# 	if payment:
# 		rows = [r for r in rows if r["status"] == payment]

# 	if source:
# 		rows = [r for r in rows if r["source"] == source]

# 	if search:
# 		q = str(search).lower().strip()
# 		rows = [
# 			r
# 			for r in rows
# 			if q in str(r.get("guestId") or "").lower()
# 			or q in str(r.get("guestName") or "").lower()
# 			or q in str(r.get("room") or "").lower()
# 			or q in str(r.get("phone") or "").lower()
# 			or q in str(r.get("type") or "").lower()
# 			or q in str(r.get("source") or "").lower()
# 		]

# 	# Compute stats
# 	total_stays = len(rows)
# 	unique_guests = len(set(r["guestId"] for r in rows if r["guestId"]))
# 	repeat_guests = len([r for r in rows if r["type"] == "Repeat"])
# 	total_nights = sum(r["nights"] for r in rows)
# 	total_revenue = _money(sum(r["totalSpend"] for r in rows))
# 	avg_stay = round(total_nights / total_stays, 1) if total_stays else 0

# 	stats = {
# 		"totalStays": total_stays,
# 		"uniqueGuests": unique_guests,
# 		"repeatGuests": repeat_guests,
# 		"repeatRatio": "{:.1f}%".format((repeat_guests / total_stays) * 100) if total_stays else "0%",
# 		"roomNights": total_nights,
# 		"totalRevenue": total_revenue,
# 		"avgStay": avg_stay,
# 	}

# 	totals = {
# 		"spend": _money(sum(r["totalSpend"] for r in rows)),
# 		"balance": _money(sum(r["balance"] for r in rows)),
# 		"needFollowup": len([r for r in rows if r["balance"] > 0]),
# 	}

# 	return {
# 		"rows": rows,
# 		"stats": stats,
# 		"totals": totals,
# 		"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
# 		"filters": {
# 			"date_from": str(date_from),
# 			"date_to": str(date_to),
# 		},
# 	}


import frappe
from frappe.utils import nowdate, getdate, get_datetime, add_days, flt, cint, format_datetime


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
		return format_datetime(value, "dd-MM-yyyy")
	except Exception:
		return str(value)


def _get_payment_status(total_spend, balance, corporate_check_in=None):
	total_spend = flt(total_spend or 0)
	balance = flt(balance or 0)

	if corporate_check_in and balance > 0:
		return "Corporate Credit"

	if total_spend <= 0:
		return "Outstanding"

	if balance <= 0:
		return "Settled"

	if balance < total_spend:
		return "Part Paid"

	return "Outstanding"


def _get_guest_type(row, total_guest_stays):
	loyalty_tier = row.get("loyalty_tier")
	guest_type = row.get("guest_type")
	nights = cint(row.get("number_of_nights") or 0)

	if row.get("corporate_check_in") or guest_type == "Corporate":
		return "Corporate"

	if loyalty_tier in ("VIP", "Platinum"):
		return "VIP"

	if nights >= 7:
		return "Long Stay"

	if total_guest_stays > 1:
		return "Repeat"

	return "New"


def _get_source(row):
	if row.get("corporate_check_in"):
		return "Corporate"

	source = row.get("reservation_source") or row.get("market_place") or row.get("guest_market_place")

	if not source:
		guest_type = row.get("guest_type")
		if guest_type == "Corporate":
			return "Corporate"
		if guest_type == "Walk-in":
			return "Walk-in"
		return "Direct"

	source_text = str(source).strip()

	if source_text.lower() in ("walk in", "walk-in", "walkin"):
		return "Walk-in"

	return source_text


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
def get_guest_stay_history(
	date_from=None,
	date_to=None,
	guest_type=None,
	room_type=None,
	payment=None,
	source=None,
	search=None,
):
	date_from = _date_or_default(date_from, add_days(nowdate(), -7))
	date_to = _date_or_default(date_to, nowdate())

	from_dt = get_datetime(str(date_from) + " 00:00:00")
	to_dt = get_datetime(str(date_to) + " 23:59:59")

	rows = frappe.db.sql(
		"""
		SELECT
			ci.name,
			ci.guest,
			ci.room_number,
			ci.room_type,
			ci.check_in_datetime,
			ci.expected_check_out_datetime,
			ci.actual_check_out_datetime,
			ci.number_of_nights,
			ci.rate_amount,
			ci.discount,
			ci.total_charges,
			ci.total_outstanding_amount,
			ci.reservation_source,
			ci.corporate_check_in,
			ci.housekeeping_notes,
			ci.status AS checkin_status,
			g.hotel_guest_name,
			g.phone_number,
			g.contact_number,
			g.guest_type,
			g.market_place AS guest_market_place,
			g.preference,
			g.notes,
			g.loyalty_tier
		FROM `tabHotel Room Check In` ci
		LEFT JOIN `tabHotel Guest` g ON g.name = ci.guest
		WHERE ci.docstatus != 2
		  AND ci.check_in_datetime BETWEEN %s AND %s
		ORDER BY ci.check_in_datetime DESC
		""",
		(from_dt, to_dt),
		as_dict=True,
	)

	guest_ids = list(set([r.guest for r in rows if r.guest]))
	stay_count_map = {}
	last_visit_map = {}

	if guest_ids:
		placeholders = ", ".join(["%s"] * len(guest_ids))

		count_rows = frappe.db.sql(
			"""
			SELECT guest, COUNT(*) AS total_stays
			FROM `tabHotel Room Check In`
			WHERE docstatus != 2
			  AND guest IN ({0})
			GROUP BY guest
			""".format(placeholders),
			tuple(guest_ids),
			as_dict=True,
		)

		for row in count_rows:
			stay_count_map[row.guest] = cint(row.total_stays)

		last_rows = frappe.db.sql(
			"""
			SELECT guest, MAX(check_in_datetime) AS last_visit
			FROM `tabHotel Room Check In`
			WHERE docstatus != 2
			  AND guest IN ({0})
			  AND check_in_datetime < %s
			GROUP BY guest
			""".format(placeholders),
			tuple(guest_ids) + (from_dt,),
			as_dict=True,
		)

		for row in last_rows:
			last_visit_map[row.guest] = row.last_visit

	invoice_totals = _get_invoice_totals([r.name for r in rows])

	data = []

	for row in rows:
		inv = invoice_totals.get(row.name, {})

		total_spend = _money(inv.get("amount") or row.get("total_charges") or 0)
		balance = _money(inv.get("outstanding") or row.get("total_outstanding_amount") or 0)

		total_guest_stays = stay_count_map.get(row.guest, 1)
		derived_guest_type = _get_guest_type(row, total_guest_stays)
		derived_source = _get_source(row)
		payment_status = _get_payment_status(total_spend, balance, row.get("corporate_check_in"))

		notes = (
			row.get("room_preferences")
			or row.get("preference")
			or row.get("housekeeping_notes")
			or row.get("notes")
			or "No special request"
		)

		item = {
			"id": row.name,
			"guestId": row.guest or "",
			"guestName": row.hotel_guest_name or row.guest or "Unknown Guest",
			"phone": row.phone_number or row.contact_number or "—",
			"room": row.room_number or "—",
			"roomType": row.room_type or "—",
			"checkin": _dt_label(row.check_in_datetime),
			"checkout": _dt_label(row.actual_check_out_datetime or row.expected_check_out_datetime),
			"nights": cint(row.number_of_nights or 0),
			"type": derived_guest_type,
			"totalSpend": total_spend,
			"balance": balance,
			"status": payment_status,
			"source": derived_source,
			"lastVisit": _dt_label(last_visit_map.get(row.guest))
			if last_visit_map.get(row.guest)
			else "First Visit",
			"notes": notes,
			"loyaltyTier": row.loyalty_tier or "",
			"checkinStatus": row.checkin_status or "",
		}

		data.append(item)

	if guest_type:
		data = [r for r in data if r["type"] == guest_type]

	if room_type:
		data = [r for r in data if r["roomType"] == room_type]

	if payment:
		data = [r for r in data if r["status"] == payment]

	if source:
		data = [r for r in data if r["source"] == source]

	if search:
		q = str(search).lower().strip()
		data = [
			r
			for r in data
			if q in str(r.get("guestId") or "").lower()
			or q in str(r.get("guestName") or "").lower()
			or q in str(r.get("phone") or "").lower()
			or q in str(r.get("room") or "").lower()
			or q in str(r.get("roomType") or "").lower()
			or q in str(r.get("type") or "").lower()
			or q in str(r.get("source") or "").lower()
		]

	total_stays = len(data)
	unique_guests = len(set([r["guestId"] for r in data if r["guestId"]]))
	repeat_guests = len([r for r in data if r["type"] == "Repeat"])
	room_nights = sum(cint(r["nights"]) for r in data)
	total_revenue = _money(sum(flt(r["totalSpend"]) for r in data))
	total_balance = _money(sum(flt(r["balance"]) for r in data))

	stats = {
		"totalStays": total_stays,
		"uniqueGuests": unique_guests,
		"repeatGuests": repeat_guests,
		"repeatRatio": str(round((repeat_guests / total_stays) * 100, 1)) + "%" if total_stays else "0%",
		"roomNights": room_nights,
		"totalRevenue": total_revenue,
		"avgStay": round(room_nights / total_stays, 1) if total_stays else 0,
	}

	totals = {
		"spend": total_revenue,
		"balance": total_balance,
		"needFollowup": len([r for r in data if flt(r["balance"]) > 0]),
	}

	room_types = sorted(list(set([r["roomType"] for r in data if r["roomType"] and r["roomType"] != "—"])))
	sources = sorted(list(set([r["source"] for r in data if r["source"]])))

	return {
		"rows": data,
		"stats": stats,
		"totals": totals,
		"room_types": room_types,
		"sources": sources,
		"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
		"filters": {
			"date_from": str(date_from),
			"date_to": str(date_to),
		},
	}
