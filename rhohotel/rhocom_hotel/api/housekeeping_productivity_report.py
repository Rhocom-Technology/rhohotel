import frappe
from frappe.utils import nowdate, add_days, getdate, get_datetime, cint, format_datetime


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


def _dt(value):
	if not value:
		return ""
	try:
		return format_datetime(value, "dd-MM-yyyy HH:mm")
	except Exception:
		return str(value)


def _get_field(doctype, candidates):
	for field in candidates:
		if _has_column(doctype, field):
			return field
	return None


def _clean_status(value):
	return str(value or "").strip().lower()


def _is_cleaned(status):
	status = _clean_status(status)
	return status in [
		"cleaned",
		"completed",
		"done",
		"finished",
		"cleaning completed",
		"ready",
		"room cleaned",
	]


def _is_inspected(status):
	status = _clean_status(status)
	return status in [
		"inspected",
		"approved",
		"checked",
		"verified",
		"inspection completed",
		"room inspected",
	]


@frappe.whitelist()
def get_housekeeping_productivity_report(
	date_from=None, date_to=None, housekeeper=None, floor=None, status=None, search=None
):
	date_from = _date_or_default(date_from, add_days(nowdate(), -7))
	date_to = _date_or_default(date_to, nowdate())

	from_dt = get_datetime(str(date_from) + " 00:00:00")
	to_dt = get_datetime(str(date_to) + " 23:59:59")

	if not _has_doctype("Housekeeping Task"):
		return {
			"rows": [],
			"summary": {
				"total_tasks": 0,
				"rooms_cleaned": 0,
				"rooms_inspected": 0,
				"pending_tasks": 0,
				"issue_count": 0,
				"guest_requests": 0,
				"avg_duration": 0,
			},
			"housekeepers": [],
			"floors": [],
			"statuses": [],
			"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
			"filters": {
				"date_from": str(date_from),
				"date_to": str(date_to),
			},
		}

	doctype = "Housekeeping Task"

	room_field = _get_field(doctype, ["room", "room_number", "hotel_room"])
	housekeeper_field = _get_field(doctype, ["housekeeper", "assigned_to", "attendant", "employee"])
	inspector_field = _get_field(doctype, ["inspector", "supervisor", "checked_by", "inspected_by"])
	status_field = _get_field(doctype, ["status", "workflow_state"])
	start_field = _get_field(
		doctype,
		["start_time", "started_at", "actual_start_time", "cleaning_start_time", "creation"],
	)
	end_field = _get_field(
		doctype,
		["end_time", "ended_at", "actual_end_time", "cleaning_end_time", "modified"],
	)
	date_field = _get_field(doctype, ["date", "task_date", "posting_date", "creation"])
	issue_field = _get_field(doctype, ["issue", "maintenance_issue", "remarks", "notes"])
	request_field = _get_field(doctype, ["guest_requests", "request_count"])

	select_parts = [
		"name",
		"`{0}` as room".format(room_field) if room_field else "'' as room",
		"`{0}` as housekeeper".format(housekeeper_field) if housekeeper_field else "'' as housekeeper",
		"`{0}` as inspector".format(inspector_field) if inspector_field else "'' as inspector",
		"`{0}` as status".format(status_field) if status_field else "'Pending' as status",
		"`{0}` as start_time".format(start_field) if start_field else "creation as start_time",
		"`{0}` as end_time".format(end_field) if end_field else "modified as end_time",
		"`{0}` as issue".format(issue_field) if issue_field else "'' as issue",
		"`{0}` as guest_requests".format(request_field) if request_field else "0 as guest_requests",
	]

	conditions = ["docstatus != 2"]
	values = []

	if date_field:
		conditions.append("`{0}` BETWEEN %s AND %s".format(date_field))
		values.extend([from_dt, to_dt])

	if housekeeper and housekeeper_field:
		conditions.append("`{0}` = %s".format(housekeeper_field))
		values.append(housekeeper)

	if status and status_field:
		conditions.append("`{0}` = %s".format(status_field))
		values.append(status)

	sql = """
		SELECT {select_fields}
		FROM `tabHousekeeping Task`
		WHERE {conditions}
		ORDER BY modified DESC
	""".format(
		select_fields=", ".join(select_parts),
		conditions=" AND ".join(conditions),
	)

	tasks = frappe.db.sql(sql, tuple(values), as_dict=True)

	room_names = list(set([t.room for t in tasks if t.get("room")]))
	room_map = {}

	if room_names and _has_doctype("Hotel Room"):
		room_placeholders = ", ".join(["%s"] * len(room_names))

		room_rows = frappe.db.sql(
			"""
			SELECT
				name,
				room_number,
				room_type,
				floor
			FROM `tabHotel Room`
			WHERE name IN ({0}) OR room_number IN ({0})
			""".format(room_placeholders),
			tuple(room_names + room_names),
			as_dict=True,
		)

		for room_row in room_rows:
			room_map[room_row.name] = room_row
			if room_row.room_number:
				room_map[room_row.room_number] = room_row

	rows = []

	for task in tasks:
		room_doc = room_map.get(task.room, {})
		room_number = room_doc.get("room_number") or task.room or "—"
		room_floor = room_doc.get("floor") or ""

		if floor and str(room_floor) != str(floor):
			continue

		start_time = task.get("start_time")
		end_time = task.get("end_time")

		duration = 0
		try:
			if start_time and end_time:
				duration = int((get_datetime(end_time) - get_datetime(start_time)).total_seconds() / 60)
				if duration < 0:
					duration = 0
		except Exception:
			duration = 0

		task_status = task.get("status") or "Pending"

		row = {
			"id": task.name,
			"room": room_number,
			"room_type": room_doc.get("room_type") or "",
			"floor": room_floor,
			"housekeeper": task.get("housekeeper") or "Unassigned",
			"inspector": task.get("inspector") or "",
			"status": task_status,
			"is_cleaned": 1 if _is_cleaned(task_status) else 0,
			"is_inspected": 1 if _is_inspected(task_status) else 0,
			"start_time": _dt(start_time),
			"end_time": _dt(end_time),
			"duration": duration,
			"guest_requests": cint(task.get("guest_requests") or 0),
			"issue": task.get("issue") or "",
		}

		rows.append(row)

	if search:
		q = str(search).lower().strip()
		rows = [
			r
			for r in rows
			if q in str(r.get("id") or "").lower()
			or q in str(r.get("room") or "").lower()
			or q in str(r.get("room_type") or "").lower()
			or q in str(r.get("housekeeper") or "").lower()
			or q in str(r.get("inspector") or "").lower()
			or q in str(r.get("status") or "").lower()
			or q in str(r.get("issue") or "").lower()
		]

	total_duration = sum([cint(r.get("duration") or 0) for r in rows])
	total_tasks = len(rows)

	summary = {
		"total_tasks": total_tasks,
		"rooms_cleaned": len([r for r in rows if cint(r.get("is_cleaned")) == 1]),
		"rooms_inspected": len([r for r in rows if cint(r.get("is_inspected")) == 1]),
		"pending_tasks": len([r for r in rows if _clean_status(r.get("status")) in ["pending", "open", "assigned"]]),
		"issue_count": len([r for r in rows if r.get("issue")]),
		"guest_requests": sum([cint(r.get("guest_requests") or 0) for r in rows]),
		"avg_duration": int(total_duration / total_tasks) if total_tasks else 0,
	}

	housekeepers = sorted(
		list(
			set(
				[
					r["housekeeper"]
					for r in rows
					if r.get("housekeeper") and r.get("housekeeper") != "Unassigned"
				]
			)
		)
	)

	floors = sorted(list(set([str(r["floor"]) for r in rows if r.get("floor")])))
	statuses = sorted(list(set([str(r["status"]) for r in rows if r.get("status")])))

	return {
		"rows": rows,
		"summary": summary,
		"housekeepers": housekeepers,
		"floors": floors,
		"statuses": statuses,
		"generated_at": format_datetime(get_datetime(), "dd-MM-yyyy HH:mm:ss"),
		"filters": {
			"date_from": str(date_from),
			"date_to": str(date_to),
		},
	}