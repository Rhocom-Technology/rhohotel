import frappe
from frappe.utils import getdate, nowdate, flt, cint


def _date_or_default(value, default_value):
	try:
		return getdate(value) if value else getdate(default_value)
	except Exception:
		return getdate(default_value)


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


def _get_value(doc, field):
	if field:
		return doc.get(field)
	return None


def _status_class(status):
	if not status:
		return "Unknown"
	return str(status)


def _payment_mode_from_invoice(invoice_name):
	if not invoice_name or not _has_doctype("Sales Invoice Payment"):
		return ""

	try:
		rows = frappe.db.sql(
			"""
			SELECT mode_of_payment
			FROM `tabSales Invoice Payment`
			WHERE parent = %s
			""",
			(invoice_name,),
			as_dict=True,
		)

		return ", ".join([row.mode_of_payment for row in rows if row.mode_of_payment])
	except Exception:
		return ""


def _get_sales_invoice_rows(audit_date, revenue_type=None, pos_profile=None, search=None):
	if not _has_doctype("Sales Invoice"):
		return []

	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
	customer_field = _get_field("Sales Invoice", ["customer"])
	customer_name_field = _get_field("Sales Invoice", ["customer_name"])
	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
	net_total_field = _get_field("Sales Invoice", ["net_total", "base_net_total"])
	tax_field = _get_field("Sales Invoice", ["total_taxes_and_charges"])
	discount_field = _get_field("Sales Invoice", ["discount_amount", "additional_discount_amount"])
	outstanding_field = _get_field("Sales Invoice", ["outstanding_amount"])
	paid_field = _get_field("Sales Invoice", ["paid_amount"])
	status_field = _get_field("Sales Invoice", ["status"])
	pos_profile_field = _get_field("Sales Invoice", ["pos_profile"])
	is_pos_field = _get_field("Sales Invoice", ["is_pos"])

	room_checkin_field = _get_field(
		"Sales Invoice",
		[
			"custom_hotel_room_check_in",
		],
	)

	reservation_field = _get_field(
		"Sales Invoice",
		[
			"custom_reservation",
			"reservation",
			"hotel_reservation",
			"booking",
		],
	)

	if not posting_date_field:
		return []

	conditions = [
		"docstatus = 1",
		"{0} = %(audit_date)s".format(posting_date_field),
	]

	params = {
		"audit_date": audit_date,
	}

	if pos_profile and pos_profile_field:
		conditions.append("{0} = %(pos_profile)s".format(pos_profile_field))
		params["pos_profile"] = pos_profile

	if revenue_type == "Room Revenue" and room_checkin_field:
		conditions.append("{0} IS NOT NULL AND {0} != ''".format(room_checkin_field))

	if revenue_type == "POS Revenue" and is_pos_field:
		conditions.append("{0} = 1".format(is_pos_field))

		if room_checkin_field:
			conditions.append("({0} IS NULL OR {0} = '')".format(room_checkin_field))

	if revenue_type == "Other Revenue":
		if room_checkin_field:
			conditions.append("({0} IS NULL OR {0} = '')".format(room_checkin_field))

		if is_pos_field:
			conditions.append("({0} = 0 OR {0} IS NULL)".format(is_pos_field))

	if search:
		search_fields = ["name"]

		for field in [
			customer_field,
			customer_name_field,
			room_checkin_field,
			reservation_field,
			pos_profile_field,
		]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]

	for field in [
		posting_date_field,
		customer_field,
		customer_name_field,
		grand_total_field,
		net_total_field,
		tax_field,
		discount_field,
		outstanding_field,
		paid_field,
		status_field,
		pos_profile_field,
		is_pos_field,
		room_checkin_field,
		reservation_field,
	]:
		if field and field not in select_fields:
			select_fields.append(field)

	sql = """
		SELECT {fields}
		FROM `tabSales Invoice`
		WHERE {conditions}
		ORDER BY name DESC
	""".format(
		fields=", ".join(select_fields),
		conditions=" AND ".join(conditions),
	)

	invoices = frappe.db.sql(sql, params, as_dict=True)
	rows = []

	for inv in invoices:
		invoice_name = inv.get("name")
		room_checkin = _get_value(inv, room_checkin_field)
		is_pos = cint(_get_value(inv, is_pos_field)) if is_pos_field else 0

		if room_checkin:
			transaction_type = "Room Revenue"
		elif is_pos:
			transaction_type = "POS Revenue"
		else:
			transaction_type = "Other Revenue"

		rows.append(
			{
				"date": str(inv.get(posting_date_field) or ""),
				"transaction_type": transaction_type,
				"reference": invoice_name,
				"guest": inv.get(customer_name_field) or inv.get(customer_field) or "",
				"room": room_checkin or "",
				"reservation": _get_value(inv, reservation_field) or "",
				"pos_profile": _get_value(inv, pos_profile_field) or "",
				"payment_mode": _payment_mode_from_invoice(invoice_name),
				"net_amount": flt(_get_value(inv, net_total_field)),
				"tax": flt(_get_value(inv, tax_field)),
				"discount": flt(_get_value(inv, discount_field)),
				"gross_amount": flt(_get_value(inv, grand_total_field)),
				"paid_amount": flt(_get_value(inv, paid_field)),
				"outstanding_amount": flt(_get_value(inv, outstanding_field)),
				"status": _status_class(_get_value(inv, status_field)),
			}
		)

	return rows


def _get_payment_entry_rows(audit_date, search=None):
	if not _has_doctype("Payment Entry"):
		return []

	posting_date_field = _get_field("Payment Entry", ["posting_date"])
	party_field = _get_field("Payment Entry", ["party"])
	party_name_field = _get_field("Payment Entry", ["party_name"])
	paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])
	mode_field = _get_field("Payment Entry", ["mode_of_payment"])
	reference_field = _get_field("Payment Entry", ["reference_no", "cheque_no"])
	remarks_field = _get_field("Payment Entry", ["remarks"])

	if not posting_date_field:
		return []

	conditions = [
		"docstatus = 1",
		"{0} = %(audit_date)s".format(posting_date_field),
	]

	params = {
		"audit_date": audit_date,
	}

	if search:
		search_fields = ["name"]

		for field in [party_field, party_name_field, mode_field, reference_field, remarks_field]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]

	for field in [
		posting_date_field,
		party_field,
		party_name_field,
		paid_amount_field,
		mode_field,
		reference_field,
		remarks_field,
	]:
		if field and field not in select_fields:
			select_fields.append(field)

	sql = """
		SELECT {fields}
		FROM `tabPayment Entry`
		WHERE {conditions}
		ORDER BY name DESC
	""".format(
		fields=", ".join(select_fields),
		conditions=" AND ".join(conditions),
	)

	payments = frappe.db.sql(sql, params, as_dict=True)
	rows = []

	for pay in payments:
		rows.append(
			{
				"date": str(pay.get(posting_date_field) or ""),
				"transaction_type": "Payment",
				"reference": pay.get("name"),
				"guest": pay.get(party_name_field) or pay.get(party_field) or "",
				"room": "",
				"reservation": "",
				"pos_profile": "",
				"payment_mode": pay.get(mode_field) or "",
				"net_amount": 0,
				"tax": 0,
				"discount": 0,
				"gross_amount": 0,
				"paid_amount": flt(pay.get(paid_amount_field)),
				"outstanding_amount": 0,
				"status": "Paid",
			}
		)

	return rows


def _get_room_stats(audit_date):
	stats = {
		"total_rooms": 0,
		"occupied_rooms": 0,
		"vacant_rooms": 0,
		"occupancy_percent": 0,
	}

	if _has_doctype("Room"):
		try:
			stats["total_rooms"] = frappe.db.count("Room") or 0
		except Exception:
			stats["total_rooms"] = 0

	if _has_doctype("Hotel Room"):
		try:
			stats["total_rooms"] = frappe.db.count("Hotel Room") or stats["total_rooms"]
		except Exception:
			pass

	occupied = 0

	for doctype in ["Reservation", "Hotel Reservation", "Room Reservation", "Booking"]:
		if not _has_doctype(doctype):
			continue

		checkin_field = _get_field(
			doctype, ["check_in", "checkin", "arrival_date", "from_date", "start_date"]
		)
		checkout_field = _get_field(
			doctype, ["check_out", "checkout", "departure_date", "to_date", "end_date"]
		)
		status_field = _get_field(doctype, ["status"])
		room_field = _get_field(doctype, ["room", "room_number", "custom_room"])

		if not checkin_field or not checkout_field:
			continue

		conditions = [
			"{0} <= %(audit_date)s".format(checkin_field),
			"{0} > %(audit_date)s".format(checkout_field),
		]

		if status_field:
			conditions.append("{0} NOT IN ('Cancelled', 'No Show')".format(status_field))

		try:
			if room_field:
				occupied = (
					frappe.db.sql(
						"""
					SELECT COUNT(DISTINCT {room_field})
					FROM `tab{doctype}`
					WHERE {conditions}
					""".format(
							room_field=room_field,
							doctype=doctype,
							conditions=" AND ".join(conditions),
						),
						{"audit_date": audit_date},
					)[0][0]
					or 0
				)
			else:
				occupied = (
					frappe.db.sql(
						"""
					SELECT COUNT(*)
					FROM `tab{doctype}`
					WHERE {conditions}
					""".format(
							doctype=doctype,
							conditions=" AND ".join(conditions),
						),
						{"audit_date": audit_date},
					)[0][0]
					or 0
				)

			break
		except Exception:
			continue

	stats["occupied_rooms"] = cint(occupied)
	stats["vacant_rooms"] = max(cint(stats["total_rooms"]) - cint(occupied), 0)

	if stats["total_rooms"]:
		stats["occupancy_percent"] = flt((flt(stats["occupied_rooms"]) / flt(stats["total_rooms"])) * 100, 2)

	return stats


def _get_arrival_departure_counts(audit_date):
	result = {
		"arrivals": 0,
		"departures": 0,
		"stayovers": 0,
	}

	for doctype in ["Reservation", "Hotel Reservation", "Room Reservation", "Booking"]:
		if not _has_doctype(doctype):
			continue

		checkin_field = _get_field(
			doctype, ["check_in", "checkin", "arrival_date", "from_date", "start_date"]
		)
		checkout_field = _get_field(
			doctype, ["check_out", "checkout", "departure_date", "to_date", "end_date"]
		)
		status_field = _get_field(doctype, ["status"])

		if not checkin_field or not checkout_field:
			continue

		status_condition = ""
		if status_field:
			status_condition = "AND {0} NOT IN ('Cancelled', 'No Show')".format(status_field)

		try:
			result["arrivals"] = (
				frappe.db.sql(
					"""
				SELECT COUNT(*)
				FROM `tab{doctype}`
				WHERE {checkin_field} = %(audit_date)s {status_condition}
				""".format(
						doctype=doctype,
						checkin_field=checkin_field,
						status_condition=status_condition,
					),
					{"audit_date": audit_date},
				)[0][0]
				or 0
			)

			result["departures"] = (
				frappe.db.sql(
					"""
				SELECT COUNT(*)
				FROM `tab{doctype}`
				WHERE {checkout_field} = %(audit_date)s {status_condition}
				""".format(
						doctype=doctype,
						checkout_field=checkout_field,
						status_condition=status_condition,
					),
					{"audit_date": audit_date},
				)[0][0]
				or 0
			)

			result["stayovers"] = (
				frappe.db.sql(
					"""
				SELECT COUNT(*)
				FROM `tab{doctype}`
				WHERE {checkin_field} < %(audit_date)s
				  AND {checkout_field} > %(audit_date)s
				  {status_condition}
				""".format(
						doctype=doctype,
						checkin_field=checkin_field,
						checkout_field=checkout_field,
						status_condition=status_condition,
					),
					{"audit_date": audit_date},
				)[0][0]
				or 0
			)

			break
		except Exception:
			continue

	return result


def _get_pos_profiles():
	if not _has_doctype("POS Profile"):
		return []

	try:
		return frappe.db.sql(
			"""
			SELECT name
			FROM `tabPOS Profile`
			ORDER BY name ASC
			""",
			as_dict=True,
		)
	except Exception:
		return []


@frappe.whitelist()
def get_night_audit_summary_report(
	audit_date=None, revenue_type=None, pos_profile=None, status=None, search=None
):
	audit_date = _date_or_default(audit_date, nowdate())

	invoice_rows = _get_sales_invoice_rows(audit_date, revenue_type, pos_profile, search)
	payment_rows = _get_payment_entry_rows(audit_date, search)

	rows = invoice_rows + payment_rows

	if status:
		rows = [row for row in rows if row.get("status") == status]

	rows = sorted(
		rows,
		key=lambda x: (str(x.get("transaction_type") or ""), str(x.get("reference") or "")),
	)

	room_revenue = sum(
		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "Room Revenue"
	)
	pos_revenue = sum(
		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "POS Revenue"
	)
	other_revenue = sum(
		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "Other Revenue"
	)

	total_revenue = room_revenue + pos_revenue + other_revenue
	total_tax = sum(flt(row.get("tax")) for row in rows)
	total_discount = sum(flt(row.get("discount")) for row in rows)
	total_paid = sum(flt(row.get("paid_amount")) for row in rows)
	total_outstanding = sum(flt(row.get("outstanding_amount")) for row in rows)

	payment_map = {}
	for row in rows:
		mode_text = row.get("payment_mode") or "Unknown"
		modes = str(mode_text).split(",")

		for mode_raw in modes:
			mode = mode_raw.strip() or "Unknown"
			payment_map[mode] = payment_map.get(mode, 0) + flt(row.get("paid_amount"))

	payment_breakdown = sorted(
		[{"mode": mode, "amount": amount} for mode, amount in payment_map.items() if amount],
		key=lambda x: flt(x.get("amount")),
		reverse=True,
	)

	revenue_map = {}
	for row in rows:
		transaction_type = row.get("transaction_type") or "Unknown"
		revenue_map[transaction_type] = revenue_map.get(transaction_type, 0) + flt(row.get("gross_amount"))

	revenue_breakdown = sorted(
		[{"type": revenue_type, "amount": amount} for revenue_type, amount in revenue_map.items()],
		key=lambda x: flt(x.get("amount")),
		reverse=True,
	)

	exceptions = []
	for row in rows:
		if flt(row.get("outstanding_amount")) > 0:
			exceptions.append(
				{
					"type": "Outstanding Balance",
					"reference": row.get("reference"),
					"description": row.get("guest") or "",
					"exception_amount": flt(row.get("outstanding_amount")),
					"amount_to_be_paid": flt(row.get("outstanding_amount")),
					"status": row.get("status"),
				}
			)

		if flt(row.get("discount")) > 0:
			exceptions.append(
				{
					"type": "Discount Given",
					"reference": row.get("reference"),
					"description": row.get("guest") or "",
					"exception_amount": flt(row.get("discount")),
					"amount_to_be_paid": flt(row.get("outstanding_amount")),
					"status": row.get("status"),
				}
			)

	room_stats = _get_room_stats(audit_date)
	movement_stats = _get_arrival_departure_counts(audit_date)

	return {
		"rows": rows,
		"payment_breakdown": payment_breakdown,
		"revenue_breakdown": revenue_breakdown,
		"exceptions": exceptions[:50],
		"pos_profiles": [row.name for row in _get_pos_profiles()],
		"summary": {
			"audit_date": str(audit_date),
			"room_revenue": room_revenue,
			"pos_revenue": pos_revenue,
			"other_revenue": other_revenue,
			"total_revenue": total_revenue,
			"total_tax": total_tax,
			"total_discount": total_discount,
			"total_paid": total_paid,
			"total_outstanding": total_outstanding,
			"transaction_count": len(rows),
			"exceptions_count": len(exceptions),
			"total_rooms": room_stats.get("total_rooms"),
			"occupied_rooms": room_stats.get("occupied_rooms"),
			"vacant_rooms": room_stats.get("vacant_rooms"),
			"occupancy_percent": room_stats.get("occupancy_percent"),
			"arrivals": movement_stats.get("arrivals"),
			"departures": movement_stats.get("departures"),
			"stayovers": movement_stats.get("stayovers"),
		},
	}
