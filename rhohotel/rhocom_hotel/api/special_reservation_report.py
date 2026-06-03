import frappe
from frappe.utils import add_days, flt, getdate, nowdate


def _date_or_default(value, default_value):
	try:
		return getdate(value) if value else getdate(default_value)
	except Exception:
		return getdate(default_value)


def _room_summary(reservation_name):
	rows = frappe.get_all(
		"Hotel Reservation Room",
		filters={"parent": reservation_name},
		fields=[
			"room_number",
			"room_type",
			"occupant_name",
			"occupant_phone",
			"status",
			"rate_per_night",
			"room_total",
		],
		order_by="idx asc",
	)
	return rows or []


@frappe.whitelist()
def get_special_reservation_report(
	date_from=None,
	date_to=None,
	reservation_type=None,
	status=None,
	search=None,
):
	"""House Use / Complimentary reservation report with theoretical revenue."""
	date_from = _date_or_default(date_from, add_days(nowdate(), -30))
	date_to = _date_or_default(date_to, nowdate())

	types = ["House Use", "Complimentary"]
	if reservation_type in types:
		types = [reservation_type]

	conditions = [
		"hr.docstatus != 2",
		"hr.reservation_type IN %(types)s",
		"hr.from_date <= %(date_to)s",
		"hr.to_date >= %(date_from)s",
	]
	params = {
		"types": tuple(types),
		"date_from": date_from,
		"date_to": date_to,
	}

	if status:
		conditions.append("hr.reservation_status = %(status)s")
		params["status"] = status

	if search:
		conditions.append(
			"""(
				hr.name LIKE %(search)s
				OR hr.primary_guest_name LIKE %(search)s
				OR hr.comp_reason LIKE %(search)s
				OR hr.internal_cost_center LIKE %(search)s
			)"""
		)
		params["search"] = f"%{search}%"

	reservations = frappe.db.sql(
		"""
		SELECT
			hr.name,
			hr.reservation_number,
			hr.reservation_type,
			hr.reservation_status,
			hr.primary_guest_name,
			hr.primary_guest_phone,
			hr.from_date,
			hr.to_date,
			hr.number_of_nights,
			hr.comp_reason,
			hr.internal_cost_center,
			hr.theoretical_room_revenue,
			hr.subtotal,
			hr.total_amount,
			hr.creation
		FROM `tabHotel Reservation` hr
		WHERE {conditions}
		ORDER BY hr.from_date DESC, hr.creation DESC
		""".format(conditions=" AND ".join(conditions)),
		params,
		as_dict=True,
	)

	rows = []
	for reservation in reservations:
		rooms = _room_summary(reservation.name)
		rows.append(
			{
				**reservation,
				"rooms": rooms,
				"room_count": len(rooms),
				"room_numbers": ", ".join([row.room_number for row in rooms if row.room_number]),
				"occupants": ", ".join(
					dict.fromkeys(
						[
							row.occupant_name
							for row in rooms
							if row.occupant_name
						]
					)
				),
			}
		)

	total_theoretical = sum(flt(row.get("theoretical_room_revenue")) for row in rows)
	house_use_count = sum(1 for row in rows if row.get("reservation_type") == "House Use")
	complimentary_count = sum(1 for row in rows if row.get("reservation_type") == "Complimentary")
	room_nights = sum(
		flt(row.get("number_of_nights")) * flt(row.get("room_count"))
		for row in rows
	)

	return {
		"rows": rows,
		"summary": {
			"reservation_count": len(rows),
			"house_use_count": house_use_count,
			"complimentary_count": complimentary_count,
			"room_nights": room_nights,
			"theoretical_room_revenue": total_theoretical,
		},
	}
