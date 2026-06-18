# import frappe
# from frappe.utils import getdate, nowdate, flt, cint


# def _date_or_default(value, default_value):
# 	try:
# 		return getdate(value) if value else getdate(default_value)
# 	except Exception:
# 		return getdate(default_value)


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


# def _get_field(doctype, candidates):
# 	for field in candidates:
# 		if _has_column(doctype, field):
# 			return field
# 	return None


# def _get_value(doc, field):
# 	if field:
# 		return doc.get(field)
# 	return None


# def _status_class(status):
# 	if not status:
# 		return "Unknown"
# 	return str(status)


# def _payment_mode_from_invoice(invoice_name):
# 	if not invoice_name or not _has_doctype("Sales Invoice Payment"):
# 		return ""

# 	try:
# 		rows = frappe.db.sql(
# 			"""
# 			SELECT mode_of_payment
# 			FROM `tabSales Invoice Payment`
# 			WHERE parent = %s
# 			""",
# 			(invoice_name,),
# 			as_dict=True,
# 		)

# 		return ", ".join([row.mode_of_payment for row in rows if row.mode_of_payment])
# 	except Exception:
# 		return ""


# def _get_sales_invoice_rows(audit_date, revenue_type=None, pos_profile=None, search=None):
# 	if not _has_doctype("Sales Invoice"):
# 		return []

# 	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
# 	customer_field = _get_field("Sales Invoice", ["customer"])
# 	customer_name_field = _get_field("Sales Invoice", ["customer_name"])
# 	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
# 	net_total_field = _get_field("Sales Invoice", ["net_total", "base_net_total"])
# 	tax_field = _get_field("Sales Invoice", ["total_taxes_and_charges"])
# 	discount_field = _get_field("Sales Invoice", ["discount_amount", "additional_discount_amount"])
# 	outstanding_field = _get_field("Sales Invoice", ["outstanding_amount"])
# 	paid_field = _get_field("Sales Invoice", ["paid_amount"])
# 	status_field = _get_field("Sales Invoice", ["status"])
# 	pos_profile_field = _get_field("Sales Invoice", ["pos_profile"])
# 	is_pos_field = _get_field("Sales Invoice", ["is_pos"])

# 	room_checkin_field = _get_field(
# 		"Sales Invoice",
# 		[
# 			"custom_hotel_room_check_in",
# 		],
# 	)

# 	reservation_field = _get_field(
# 		"Sales Invoice",
# 		[
# 			"custom_reservation",
# 			"reservation",
# 			"hotel_reservation",
# 			"booking",
# 		],
# 	)

# 	if not posting_date_field:
# 		return []

# 	conditions = [
# 		"docstatus = 1",
# 		"{0} = %(audit_date)s".format(posting_date_field),
# 	]

# 	params = {
# 		"audit_date": audit_date,
# 	}

# 	if pos_profile and pos_profile_field:
# 		conditions.append("{0} = %(pos_profile)s".format(pos_profile_field))
# 		params["pos_profile"] = pos_profile

# 	if revenue_type == "Room Revenue" and room_checkin_field:
# 		conditions.append("{0} IS NOT NULL AND {0} != ''".format(room_checkin_field))

# 	if revenue_type == "POS Revenue" and is_pos_field:
# 		conditions.append("{0} = 1".format(is_pos_field))

# 		if room_checkin_field:
# 			conditions.append("({0} IS NULL OR {0} = '')".format(room_checkin_field))

# 	if revenue_type == "Other Revenue":
# 		if room_checkin_field:
# 			conditions.append("({0} IS NULL OR {0} = '')".format(room_checkin_field))

# 		if is_pos_field:
# 			conditions.append("({0} = 0 OR {0} IS NULL)".format(is_pos_field))

# 	if search:
# 		search_fields = ["name"]

# 		for field in [
# 			customer_field,
# 			customer_name_field,
# 			room_checkin_field,
# 			reservation_field,
# 			pos_profile_field,
# 		]:
# 			if field and field not in search_fields:
# 				search_fields.append(field)

# 		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
# 		params["search"] = "%{0}%".format(search)

# 	select_fields = ["name"]

# 	for field in [
# 		posting_date_field,
# 		customer_field,
# 		customer_name_field,
# 		grand_total_field,
# 		net_total_field,
# 		tax_field,
# 		discount_field,
# 		outstanding_field,
# 		paid_field,
# 		status_field,
# 		pos_profile_field,
# 		is_pos_field,
# 		room_checkin_field,
# 		reservation_field,
# 	]:
# 		if field and field not in select_fields:
# 			select_fields.append(field)

# 	sql = """
# 		SELECT {fields}
# 		FROM `tabSales Invoice`
# 		WHERE {conditions}
# 		ORDER BY name DESC
# 	""".format(
# 		fields=", ".join(select_fields),
# 		conditions=" AND ".join(conditions),
# 	)

# 	invoices = frappe.db.sql(sql, params, as_dict=True)
# 	rows = []

# 	for inv in invoices:
# 		invoice_name = inv.get("name")
# 		room_checkin = _get_value(inv, room_checkin_field)
# 		is_pos = cint(_get_value(inv, is_pos_field)) if is_pos_field else 0

# 		if room_checkin:
# 			transaction_type = "Room Revenue"
# 		elif is_pos:
# 			transaction_type = "POS Revenue"
# 		else:
# 			transaction_type = "Other Revenue"

# 		rows.append(
# 			{
# 				"date": str(inv.get(posting_date_field) or ""),
# 				"transaction_type": transaction_type,
# 				"reference": invoice_name,
# 				"guest": inv.get(customer_name_field) or inv.get(customer_field) or "",
# 				"room": room_checkin or "",
# 				"reservation": _get_value(inv, reservation_field) or "",
# 				"pos_profile": _get_value(inv, pos_profile_field) or "",
# 				"payment_mode": _payment_mode_from_invoice(invoice_name),
# 				"net_amount": flt(_get_value(inv, net_total_field)),
# 				"tax": flt(_get_value(inv, tax_field)),
# 				"discount": flt(_get_value(inv, discount_field)),
# 				"gross_amount": flt(_get_value(inv, grand_total_field)),
# 				"paid_amount": flt(_get_value(inv, paid_field)),
# 				"outstanding_amount": flt(_get_value(inv, outstanding_field)),
# 				"status": _status_class(_get_value(inv, status_field)),
# 			}
# 		)

# 	return rows


# def _get_payment_entry_rows(audit_date, search=None):
# 	if not _has_doctype("Payment Entry"):
# 		return []

# 	posting_date_field = _get_field("Payment Entry", ["posting_date"])
# 	party_field = _get_field("Payment Entry", ["party"])
# 	party_name_field = _get_field("Payment Entry", ["party_name"])
# 	paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])
# 	mode_field = _get_field("Payment Entry", ["mode_of_payment"])
# 	reference_field = _get_field("Payment Entry", ["reference_no", "cheque_no"])
# 	remarks_field = _get_field("Payment Entry", ["remarks"])

# 	if not posting_date_field:
# 		return []

# 	conditions = [
# 		"docstatus = 1",
# 		"{0} = %(audit_date)s".format(posting_date_field),
# 	]

# 	params = {
# 		"audit_date": audit_date,
# 	}

# 	if search:
# 		search_fields = ["name"]

# 		for field in [party_field, party_name_field, mode_field, reference_field, remarks_field]:
# 			if field and field not in search_fields:
# 				search_fields.append(field)

# 		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
# 		params["search"] = "%{0}%".format(search)

# 	select_fields = ["name"]

# 	for field in [
# 		posting_date_field,
# 		party_field,
# 		party_name_field,
# 		paid_amount_field,
# 		mode_field,
# 		reference_field,
# 		remarks_field,
# 	]:
# 		if field and field not in select_fields:
# 			select_fields.append(field)

# 	sql = """
# 		SELECT {fields}
# 		FROM `tabPayment Entry`
# 		WHERE {conditions}
# 		ORDER BY name DESC
# 	""".format(
# 		fields=", ".join(select_fields),
# 		conditions=" AND ".join(conditions),
# 	)

# 	payments = frappe.db.sql(sql, params, as_dict=True)
# 	rows = []

# 	for pay in payments:
# 		rows.append(
# 			{
# 				"date": str(pay.get(posting_date_field) or ""),
# 				"transaction_type": "Payment",
# 				"reference": pay.get("name"),
# 				"guest": pay.get(party_name_field) or pay.get(party_field) or "",
# 				"room": "",
# 				"reservation": "",
# 				"pos_profile": "",
# 				"payment_mode": pay.get(mode_field) or "",
# 				"net_amount": 0,
# 				"tax": 0,
# 				"discount": 0,
# 				"gross_amount": 0,
# 				"paid_amount": flt(pay.get(paid_amount_field)),
# 				"outstanding_amount": 0,
# 				"status": "Paid",
# 			}
# 		)

# 	return rows


# def _get_room_stats(audit_date):
# 	stats = {
# 		"total_rooms": 0,
# 		"occupied_rooms": 0,
# 		"vacant_rooms": 0,
# 		"occupancy_percent": 0,
# 	}

# 	if _has_doctype("Room"):
# 		try:
# 			stats["total_rooms"] = frappe.db.count("Room") or 0
# 		except Exception:
# 			stats["total_rooms"] = 0

# 	if _has_doctype("Hotel Room"):
# 		try:
# 			stats["total_rooms"] = frappe.db.count("Hotel Room") or stats["total_rooms"]
# 		except Exception:
# 			pass

# 	occupied = 0

# 	for doctype in ["Reservation", "Hotel Reservation", "Room Reservation", "Booking"]:
# 		if not _has_doctype(doctype):
# 			continue

# 		checkin_field = _get_field(
# 			doctype, ["check_in", "checkin", "arrival_date", "from_date", "start_date"]
# 		)
# 		checkout_field = _get_field(
# 			doctype, ["check_out", "checkout", "departure_date", "to_date", "end_date"]
# 		)
# 		status_field = _get_field(doctype, ["status"])
# 		room_field = _get_field(doctype, ["room", "room_number", "custom_room"])

# 		if not checkin_field or not checkout_field:
# 			continue

# 		conditions = [
# 			"{0} <= %(audit_date)s".format(checkin_field),
# 			"{0} > %(audit_date)s".format(checkout_field),
# 		]

# 		if status_field:
# 			conditions.append("{0} NOT IN ('Cancelled', 'No Show')".format(status_field))

# 		try:
# 			if room_field:
# 				occupied = (
# 					frappe.db.sql(
# 						"""
# 					SELECT COUNT(DISTINCT {room_field})
# 					FROM `tab{doctype}`
# 					WHERE {conditions}
# 					""".format(
# 							room_field=room_field,
# 							doctype=doctype,
# 							conditions=" AND ".join(conditions),
# 						),
# 						{"audit_date": audit_date},
# 					)[0][0]
# 					or 0
# 				)
# 			else:
# 				occupied = (
# 					frappe.db.sql(
# 						"""
# 					SELECT COUNT(*)
# 					FROM `tab{doctype}`
# 					WHERE {conditions}
# 					""".format(
# 							doctype=doctype,
# 							conditions=" AND ".join(conditions),
# 						),
# 						{"audit_date": audit_date},
# 					)[0][0]
# 					or 0
# 				)

# 			break
# 		except Exception:
# 			continue

# 	stats["occupied_rooms"] = cint(occupied)
# 	stats["vacant_rooms"] = max(cint(stats["total_rooms"]) - cint(occupied), 0)

# 	if stats["total_rooms"]:
# 		stats["occupancy_percent"] = flt((flt(stats["occupied_rooms"]) / flt(stats["total_rooms"])) * 100, 2)

# 	return stats


# def _get_arrival_departure_counts(audit_date):
# 	result = {
# 		"arrivals": 0,
# 		"departures": 0,
# 		"stayovers": 0,
# 	}

# 	for doctype in ["Reservation", "Hotel Reservation", "Room Reservation", "Booking"]:
# 		if not _has_doctype(doctype):
# 			continue

# 		checkin_field = _get_field(
# 			doctype, ["check_in", "checkin", "arrival_date", "from_date", "start_date"]
# 		)
# 		checkout_field = _get_field(
# 			doctype, ["check_out", "checkout", "departure_date", "to_date", "end_date"]
# 		)
# 		status_field = _get_field(doctype, ["status"])

# 		if not checkin_field or not checkout_field:
# 			continue

# 		status_condition = ""
# 		if status_field:
# 			status_condition = "AND {0} NOT IN ('Cancelled', 'No Show')".format(status_field)

# 		try:
# 			result["arrivals"] = (
# 				frappe.db.sql(
# 					"""
# 				SELECT COUNT(*)
# 				FROM `tab{doctype}`
# 				WHERE {checkin_field} = %(audit_date)s {status_condition}
# 				""".format(
# 						doctype=doctype,
# 						checkin_field=checkin_field,
# 						status_condition=status_condition,
# 					),
# 					{"audit_date": audit_date},
# 				)[0][0]
# 				or 0
# 			)

# 			result["departures"] = (
# 				frappe.db.sql(
# 					"""
# 				SELECT COUNT(*)
# 				FROM `tab{doctype}`
# 				WHERE {checkout_field} = %(audit_date)s {status_condition}
# 				""".format(
# 						doctype=doctype,
# 						checkout_field=checkout_field,
# 						status_condition=status_condition,
# 					),
# 					{"audit_date": audit_date},
# 				)[0][0]
# 				or 0
# 			)

# 			result["stayovers"] = (
# 				frappe.db.sql(
# 					"""
# 				SELECT COUNT(*)
# 				FROM `tab{doctype}`
# 				WHERE {checkin_field} < %(audit_date)s
# 				  AND {checkout_field} > %(audit_date)s
# 				  {status_condition}
# 				""".format(
# 						doctype=doctype,
# 						checkin_field=checkin_field,
# 						checkout_field=checkout_field,
# 						status_condition=status_condition,
# 					),
# 					{"audit_date": audit_date},
# 				)[0][0]
# 				or 0
# 			)

# 			break
# 		except Exception:
# 			continue

# 	return result


# def _get_pos_profiles():
# 	if not _has_doctype("POS Profile"):
# 		return []

# 	try:
# 		return frappe.db.sql(
# 			"""
# 			SELECT name
# 			FROM `tabPOS Profile`
# 			ORDER BY name ASC
# 			""",
# 			as_dict=True,
# 		)
# 	except Exception:
# 		return []


# @frappe.whitelist()
# def get_night_audit_summary_report(
# 	audit_date=None, revenue_type=None, pos_profile=None, status=None, search=None
# ):
# 	audit_date = _date_or_default(audit_date, nowdate())

# 	invoice_rows = _get_sales_invoice_rows(audit_date, revenue_type, pos_profile, search)
# 	payment_rows = _get_payment_entry_rows(audit_date, search)

# 	rows = invoice_rows + payment_rows

# 	if status:
# 		rows = [row for row in rows if row.get("status") == status]

# 	rows = sorted(
# 		rows,
# 		key=lambda x: (str(x.get("transaction_type") or ""), str(x.get("reference") or "")),
# 	)

# 	room_revenue = sum(
# 		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "Room Revenue"
# 	)
# 	pos_revenue = sum(
# 		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "POS Revenue"
# 	)
# 	other_revenue = sum(
# 		flt(row.get("gross_amount")) for row in rows if row.get("transaction_type") == "Other Revenue"
# 	)

# 	total_revenue = room_revenue + pos_revenue + other_revenue
# 	total_tax = sum(flt(row.get("tax")) for row in rows)
# 	total_discount = sum(flt(row.get("discount")) for row in rows)
# 	total_paid = sum(flt(row.get("paid_amount")) for row in rows)
# 	total_outstanding = sum(flt(row.get("outstanding_amount")) for row in rows)

# 	payment_map = {}
# 	for row in rows:
# 		mode_text = row.get("payment_mode") or "Unknown"
# 		modes = str(mode_text).split(",")

# 		for mode_raw in modes:
# 			mode = mode_raw.strip() or "Unknown"
# 			payment_map[mode] = payment_map.get(mode, 0) + flt(row.get("paid_amount"))

# 	payment_breakdown = sorted(
# 		[{"mode": mode, "amount": amount} for mode, amount in payment_map.items() if amount],
# 		key=lambda x: flt(x.get("amount")),
# 		reverse=True,
# 	)

# 	revenue_map = {}
# 	for row in rows:
# 		transaction_type = row.get("transaction_type") or "Unknown"
# 		revenue_map[transaction_type] = revenue_map.get(transaction_type, 0) + flt(row.get("gross_amount"))

# 	revenue_breakdown = sorted(
# 		[{"type": revenue_type, "amount": amount} for revenue_type, amount in revenue_map.items()],
# 		key=lambda x: flt(x.get("amount")),
# 		reverse=True,
# 	)

# 	exceptions = []
# 	for row in rows:
# 		if flt(row.get("outstanding_amount")) > 0:
# 			exceptions.append(
# 				{
# 					"type": "Outstanding Balance",
# 					"reference": row.get("reference"),
# 					"description": row.get("guest") or "",
# 					"exception_amount": flt(row.get("outstanding_amount")),
# 					"amount_to_be_paid": flt(row.get("outstanding_amount")),
# 					"status": row.get("status"),
# 				}
# 			)

# 		if flt(row.get("discount")) > 0:
# 			exceptions.append(
# 				{
# 					"type": "Discount Given",
# 					"reference": row.get("reference"),
# 					"description": row.get("guest") or "",
# 					"exception_amount": flt(row.get("discount")),
# 					"amount_to_be_paid": flt(row.get("outstanding_amount")),
# 					"status": row.get("status"),
# 				}
# 			)

# 	room_stats = _get_room_stats(audit_date)
# 	movement_stats = _get_arrival_departure_counts(audit_date)

# 	return {
# 		"rows": rows,
# 		"payment_breakdown": payment_breakdown,
# 		"revenue_breakdown": revenue_breakdown,
# 		"exceptions": exceptions[:50],
# 		"pos_profiles": [row.name for row in _get_pos_profiles()],
# 		"summary": {
# 			"audit_date": str(audit_date),
# 			"room_revenue": room_revenue,
# 			"pos_revenue": pos_revenue,
# 			"other_revenue": other_revenue,
# 			"total_revenue": total_revenue,
# 			"total_tax": total_tax,
# 			"total_discount": total_discount,
# 			"total_paid": total_paid,
# 			"total_outstanding": total_outstanding,
# 			"transaction_count": len(rows),
# 			"exceptions_count": len(exceptions),
# 			"total_rooms": room_stats.get("total_rooms"),
# 			"occupied_rooms": room_stats.get("occupied_rooms"),
# 			"vacant_rooms": room_stats.get("vacant_rooms"),
# 			"occupancy_percent": room_stats.get("occupancy_percent"),
# 			"arrivals": movement_stats.get("arrivals"),
# 			"departures": movement_stats.get("departures"),
# 			"stayovers": movement_stats.get("stayovers"),
# 		},
# 	}


import frappe
from frappe.utils import getdate, nowdate, flt, cint, get_datetime, cstr


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


def _night_audit_invoice_source(value):
    return cstr(value).strip().lower()


def _is_room_revenue_source(source):
    source = _night_audit_invoice_source(source)
    if not source:
        return True
    room_keywords = ("room", "accommodation", "lodging", "stay", "night audit")
    return any(keyword in source for keyword in room_keywords)


def _is_fnb_revenue_source(source):
    source = _night_audit_invoice_source(source)
    fnb_keywords = ("restaurant", "bar", "food", "beverage", "f&b", "pos")
    return any(keyword in source for keyword in fnb_keywords)


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
    source_field = _get_field("Sales Invoice", ["custom_invoice_source"])

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

    if search:
        search_fields = ["name"]

        for field in [
            customer_field,
            customer_name_field,
            room_checkin_field,
            reservation_field,
            pos_profile_field,
            source_field,
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
        source_field,
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
        source = _night_audit_invoice_source(_get_value(inv, source_field))
        is_pos = cint(_get_value(inv, is_pos_field)) if is_pos_field else 0

        if room_checkin and _is_room_revenue_source(source):
            transaction_type = "Room Revenue"
        elif _is_fnb_revenue_source(source) or is_pos:
            transaction_type = "POS Revenue"
        else:
            transaction_type = "Other Revenue"

        if revenue_type and transaction_type != revenue_type:
            continue

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
                "paid_amount": flt(_get_value(inv, paid_field)) or max(
                    flt(_get_value(inv, grand_total_field)) - flt(_get_value(inv, outstanding_field)), 0
                ),
                "outstanding_amount": flt(_get_value(inv, outstanding_field)),
                "status": _status_class(_get_value(inv, status_field)),
            }
        )

    return rows


def _get_pos_invoice_rows(audit_date, revenue_type=None, pos_profile=None, search=None):
    if revenue_type and revenue_type != "POS Revenue":
        return []

    if not _has_doctype("POS Invoice"):
        return []

    posting_date_field = _get_field("POS Invoice", ["posting_date"])
    customer_field = _get_field("POS Invoice", ["customer"])
    customer_name_field = _get_field("POS Invoice", ["customer_name"])
    grand_total_field = _get_field("POS Invoice", ["grand_total", "rounded_total"])
    net_total_field = _get_field("POS Invoice", ["net_total", "base_net_total"])
    tax_field = _get_field("POS Invoice", ["total_taxes_and_charges"])
    discount_field = _get_field("POS Invoice", ["discount_amount", "additional_discount_amount"])
    status_field = _get_field("POS Invoice", ["status"])
    pos_profile_field = _get_field("POS Invoice", ["pos_profile"])
    room_checkin_field = _get_field("POS Invoice", ["custom_hotel_room_check_in"])
    consolidated_field = _get_field("POS Invoice", ["consolidated_invoice"])

    if not posting_date_field:
        return []

    conditions = [
        "pi.docstatus = 1",
        "pi.{0} = %(audit_date)s".format(posting_date_field),
    ]
    params = {"audit_date": audit_date}

    if consolidated_field:
        conditions.append("(pi.{0} IS NULL OR pi.{0} = '')".format(consolidated_field))

    if pos_profile and pos_profile_field:
        conditions.append("pi.{0} = %(pos_profile)s".format(pos_profile_field))
        params["pos_profile"] = pos_profile

    if search:
        search_fields = ["pi.name"]
        for field in [customer_field, customer_name_field, pos_profile_field, room_checkin_field]:
            if field:
                search_fields.append("pi.{0}".format(field))
        conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
        params["search"] = "%{0}%".format(search)

    room_link_expr = "pi.{0}".format(room_checkin_field) if room_checkin_field else "NULL"
    select_fields = ["pi.name"]
    group_fields = ["pi.name"]
    aliases = {
        posting_date_field: "posting_date",
        customer_field: "customer",
        customer_name_field: "customer_name",
        grand_total_field: "grand_total",
        net_total_field: "net_total",
        tax_field: "tax",
        discount_field: "discount",
        status_field: "status",
        pos_profile_field: "pos_profile",
        room_checkin_field: "room",
    }

    for field, alias in aliases.items():
        if field:
            select_fields.append("pi.{0} AS {1}".format(field, alias))
            group_fields.append("pi.{0}".format(field))

    sql = """
        SELECT {fields},
               COALESCE(SUM(
                   CASE
                     WHEN LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%room%%'
                       OR LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%folio%%'
                       OR LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%post to room%%'
                       OR (LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%credit%%'
                           AND {room_link_expr} IS NOT NULL AND {room_link_expr} != '')
                     THEN pip.amount ELSE 0
                   END
               ), 0) AS room_posting_amount,
               GROUP_CONCAT(DISTINCT pip.mode_of_payment ORDER BY pip.mode_of_payment SEPARATOR ', ') AS payment_mode
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabPOS Invoice Payment` pip ON pip.parent = pi.name
        WHERE {conditions}
        GROUP BY {group_fields}
        ORDER BY pi.name DESC
    """.format(
        fields=", ".join(select_fields),
        conditions=" AND ".join(conditions),
        group_fields=", ".join(group_fields),
        room_link_expr=room_link_expr,
    )

    try:
        invoices = frappe.db.sql(sql, params, as_dict=True)
    except Exception:
        return []

    rows = []
    for inv in invoices:
        gross = max(flt(inv.get("grand_total")) - flt(inv.get("room_posting_amount")), 0)
        if gross <= 0:
            continue
        net = flt(inv.get("net_total"))
        rows.append(
            {
                "date": str(inv.get("posting_date") or ""),
                "transaction_type": "POS Revenue",
                "reference": inv.get("name"),
                "guest": inv.get("customer_name") or inv.get("customer") or "",
                "room": inv.get("room") or "",
                "reservation": "",
                "pos_profile": inv.get("pos_profile") or "",
                "payment_mode": inv.get("payment_mode") or "",
                "net_amount": min(net, gross) if net else gross,
                "tax": flt(inv.get("tax")),
                "discount": flt(inv.get("discount")),
                "gross_amount": gross,
                "paid_amount": gross,
                "outstanding_amount": 0,
                "status": _status_class(inv.get("status") or "Paid"),
            }
        )

    return rows

def _get_payment_entry_rows(audit_date, search=None):
    """
    Return standalone Payment Entry rows for the audit date.
    These represent actual cash/transfer receipts and are shown in the
    Payments section.  They do NOT contribute to revenue totals – revenue
    comes from Sales Invoices only.
    """
    if not _has_doctype("Payment Entry"):
        return []

    posting_date_field = _get_field("Payment Entry", ["posting_date"])
    party_field = _get_field("Payment Entry", ["party"])
    party_name_field = _get_field("Payment Entry", ["party_name"])
    paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])
    mode_field = _get_field("Payment Entry", ["mode_of_payment"])
    reference_field = _get_field("Payment Entry", ["reference_no", "cheque_no"])
    remarks_field = _get_field("Payment Entry", ["remarks"])
    payment_type_field = _get_field("Payment Entry", ["payment_type"])

    if not posting_date_field:
        return []

    conditions = [
        "docstatus = 1",
        "{0} = %(audit_date)s".format(posting_date_field),
    ]

    # Only include incoming payments (Receive), not internal transfers
    if payment_type_field:
        conditions.append("{0} = 'Receive'".format(payment_type_field))

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
                # Payment rows have no revenue amounts
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
    """
    Derive room occupancy from Hotel Room Check In records that overlap
    the audit date (checked-in before end-of-day, not yet checked out).
    """
    stats = {
        "total_rooms": 0,
        "occupied_rooms": 0,
        "vacant_rooms": 0,
        "occupancy_percent": 0,
    }

    # Total rooms from Hotel Room doctype
    if _has_doctype("Hotel Room"):
        try:
            stats["total_rooms"] = cint(frappe.db.count("Hotel Room")) or 0
        except Exception:
            pass

    # Occupied = active check-ins that span the audit date
    if _has_doctype("Hotel Room Check In"):
        try:
            from_dt = get_datetime(str(audit_date) + " 00:00:00")
            to_dt = get_datetime(str(audit_date) + " 23:59:59")

            occupied = frappe.db.sql(
                """
                SELECT COUNT(DISTINCT room_number)
                FROM `tabHotel Room Check In`
                WHERE docstatus != 2
                  AND status = 'Checked In'
                  AND check_in_datetime <= %s
                  AND IFNULL(actual_check_out_datetime, expected_check_out_datetime) >= %s
                """,
                (to_dt, from_dt),
            )[0][0] or 0

            stats["occupied_rooms"] = cint(occupied)
        except Exception:
            pass

    stats["vacant_rooms"] = max(stats["total_rooms"] - stats["occupied_rooms"], 0)

    if stats["total_rooms"]:
        stats["occupancy_percent"] = round(
            (stats["occupied_rooms"] / stats["total_rooms"]) * 100, 2
        )

    return stats


def _get_arrival_departure_counts(audit_date):
    """
    Count arrivals (check_in on audit_date), departures (check_out on
    audit_date) and stayovers from Hotel Room Check In.
    """
    result = {
        "arrivals": 0,
        "departures": 0,
        "stayovers": 0,
    }

    if not _has_doctype("Hotel Room Check In"):
        return result

    try:
        audit_dt_start = get_datetime(str(audit_date) + " 00:00:00")
        audit_dt_end = get_datetime(str(audit_date) + " 23:59:59")

        # Arrivals: check-in datetime falls on the audit date
        result["arrivals"] = frappe.db.sql(
            """
            SELECT COUNT(*)
            FROM `tabHotel Room Check In`
            WHERE docstatus != 2
              AND status = 'Checked In'
              AND check_in_datetime BETWEEN %s AND %s
            """,
            (audit_dt_start, audit_dt_end),
        )[0][0] or 0

        # Departures: actual or expected checkout falls on the audit date
        result["departures"] = frappe.db.sql(
            """
            SELECT COUNT(*)
            FROM `tabHotel Room Check In`
            WHERE docstatus != 2
              AND status = 'Checked In'
              AND IFNULL(actual_check_out_datetime, expected_check_out_datetime)
                  BETWEEN %s AND %s
            """,
            (audit_dt_start, audit_dt_end),
        )[0][0] or 0

        # Stayovers: checked in before audit date and checkout after it
        result["stayovers"] = frappe.db.sql(
            """
            SELECT COUNT(*)
            FROM `tabHotel Room Check In`
            WHERE docstatus != 2
              AND status = 'Checked In'
              AND check_in_datetime < %s
              AND IFNULL(actual_check_out_datetime, expected_check_out_datetime) > %s
            """,
            (audit_dt_start, audit_dt_end),
        )[0][0] or 0

    except Exception:
        pass

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
    invoice_rows += _get_pos_invoice_rows(audit_date, revenue_type, pos_profile, search)
    payment_rows = _get_payment_entry_rows(audit_date, search)

    # All rows for display in the detailed table
    rows = invoice_rows + payment_rows

    if status:
        rows = [row for row in rows if row.get("status") == status]

    rows = sorted(
        rows,
        key=lambda x: (str(x.get("transaction_type") or ""), str(x.get("reference") or "")),
    )

    # Revenue totals come from invoice rows only (not payment rows)
    room_revenue = sum(
        flt(row.get("gross_amount")) for row in invoice_rows if row.get("transaction_type") == "Room Revenue"
    )
    pos_revenue = sum(
        flt(row.get("gross_amount")) for row in invoice_rows if row.get("transaction_type") == "POS Revenue"
    )
    other_revenue = sum(
        flt(row.get("gross_amount")) for row in invoice_rows if row.get("transaction_type") == "Other Revenue"
    )

    total_revenue = room_revenue + pos_revenue + other_revenue

    # Tax and discount from invoice rows only
    total_tax = sum(flt(row.get("tax")) for row in invoice_rows)
    total_discount = sum(flt(row.get("discount")) for row in invoice_rows)

    # Paid: sum of paid_amount across invoices (already includes PE allocations)
    total_paid = sum(flt(row.get("paid_amount")) for row in invoice_rows)

    # Outstanding: unpaid invoice balances
    total_outstanding = sum(flt(row.get("outstanding_amount")) for row in invoice_rows)

    # Payment breakdown: group standalone Payment Entry rows by mode
    payment_map = {}
    for row in payment_rows:
        mode_text = row.get("payment_mode") or "Unknown"
        modes = str(mode_text).split(",")

        for mode_raw in modes:
            mode = mode_raw.strip() or "Unknown"
            payment_map[mode] = payment_map.get(mode, 0) + flt(row.get("paid_amount"))

    # Also include invoice-level payment modes
    for row in invoice_rows:
        if flt(row.get("paid_amount")) > 0:
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
    for row in invoice_rows:
        transaction_type = row.get("transaction_type") or "Unknown"
        revenue_map[transaction_type] = revenue_map.get(transaction_type, 0) + flt(row.get("gross_amount"))

    revenue_breakdown = sorted(
        [{"type": rtype, "amount": amount} for rtype, amount in revenue_map.items()],
        key=lambda x: flt(x.get("amount")),
        reverse=True,
    )

    exceptions = []
    for row in invoice_rows:
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

    # Standalone Payment Entries received on the audit date
    pe_total = sum(flt(row.get("paid_amount")) for row in payment_rows)

    # Credit notes: invoices with negative grand_total posted on audit date
    credit_notes_count  = sum(1 for row in invoice_rows if flt(row.get("gross_amount")) < 0)
    credit_notes_amount = flt(abs(sum(
        flt(row.get("gross_amount")) for row in invoice_rows if flt(row.get("gross_amount")) < 0
    )), 2)

    room_stats    = _get_room_stats(audit_date)
    movement_stats = _get_arrival_departure_counts(audit_date)

    return {
        "rows": rows,
        "payment_breakdown": payment_breakdown,
        "revenue_breakdown": revenue_breakdown,
        "exceptions": exceptions[:50],
        "pos_profiles": [row.name for row in _get_pos_profiles()],
        "summary": {
            "audit_date":          str(audit_date),
            # Revenue
            "room_revenue":        room_revenue,
            "pos_revenue":         pos_revenue,
            "other_revenue":       other_revenue,
            "total_revenue":       total_revenue,
            # Tax & discount
            "total_tax":           total_tax,
            "total_discount":      total_discount,
            # Payments
            "total_paid":          total_paid,
            "pe_total":            pe_total,
            "total_outstanding":   total_outstanding,
            # Credit notes
            "credit_notes_count":  credit_notes_count,
            "credit_notes_amount": credit_notes_amount,
            # Counts
            "transaction_count":   len(invoice_rows),
            "pe_count":            len(payment_rows),
            "exceptions_count":    len(exceptions),
            # Room stats
            "total_rooms":         room_stats.get("total_rooms"),
            "occupied_rooms":      room_stats.get("occupied_rooms"),
            "vacant_rooms":        room_stats.get("vacant_rooms"),
            "occupancy_percent":   room_stats.get("occupancy_percent"),
            "arrivals":            movement_stats.get("arrivals"),
            "departures":          movement_stats.get("departures"),
            "stayovers":           movement_stats.get("stayovers"),
        },
    }