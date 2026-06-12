import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, cstr, cint, get_datetime, time_diff_in_seconds


def validate_shift_login(login_manager):
	"""
	Block login for employees on the roster who are outside their shift hours.

	Logic:
	- No linked Employee → allow (non-employee users)
	- Employee has no Shift Assignment for today → allow (not on roster)
	- Employee has Shift Assignment → must be within shift hours (+ grace period)

	Configured via Hotel Settings:
	- enable_shift_login_restriction (Check)
	- shift_login_grace_minutes (Int, default 30)
	"""
	if not login_manager or not login_manager.user:
		return

	user = login_manager.user
	if user in ("Administrator", "Guest"):
		return

	# Check if feature is enabled
	try:
		settings = frappe.get_cached_doc("Hotel Settings")
	except Exception:
		return

	if not cint(settings.get("enable_shift_login_restriction")):
		return

	# Resolve user → Employee
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	if not employee:
		return  # Not linked to an employee — no restriction

	# Check if employee has an active Shift Assignment for today
	today = nowdate()
	shift_assignments = frappe.db.sql(
		"""
		SELECT sa.shift_type
		FROM `tabShift Assignment` sa
		WHERE sa.employee = %s
		  AND sa.status = 'Active'
		  AND sa.docstatus = 1
		  AND sa.start_date <= %s
		  AND (sa.end_date IS NULL OR sa.end_date >= %s)
		""",
		(employee, today, today),
		as_dict=1,
	)

	if not shift_assignments:
		return  # Not on roster — no restriction

	# Employee IS on roster — check if current time is within any assigned shift
	grace_minutes = cint(settings.get("shift_login_grace_minutes") or 30)
	current_time = nowtime()

	for assignment in shift_assignments:
		shift_type = assignment.get("shift_type")
		if not shift_type:
			continue

		shift_doc = frappe.db.get_value(
			"Shift Type",
			shift_type,
			["start_time", "end_time"],
			as_dict=1,
		)
		if not shift_doc:
			continue

		if _is_within_shift(current_time, shift_doc.start_time, shift_doc.end_time, grace_minutes):
			return  # Within shift window — allow login

	# If we reach here, employee is on roster but NOT within any shift window → BLOCK
	shift_names = ", ".join(set(a.get("shift_type") for a in shift_assignments if a.get("shift_type")))
	shift_details = _get_shift_time_details(shift_assignments)

	_notify_manager_of_blocked_login(employee, user, shift_names, current_time)

	frappe.throw(
		_("Access denied. You can only log in during your assigned shift.<br><br>"
		  "Your roster for today:<br>{0}<br><br>"
		  "Current time: {1}").format(shift_details, current_time[:5]),
		frappe.AuthenticationError,
	)


def _is_within_shift(current_time_str, start_time, end_time, grace_minutes=30):
	"""Check if current time falls within the shift window (with grace period before start)."""
	from datetime import timedelta

	# Convert to seconds from midnight for comparison
	current_seconds = _time_to_seconds(current_time_str)
	start_seconds = _timedelta_to_seconds(start_time)
	end_seconds = _timedelta_to_seconds(end_time)
	grace_seconds = grace_minutes * 60

	# Adjust start for grace period (allow login early)
	effective_start = start_seconds - grace_seconds

	if end_seconds > start_seconds:
		# Normal shift (e.g., 07:00 - 15:00)
		return effective_start <= current_seconds <= end_seconds
	else:
		# Overnight shift (e.g., 22:00 - 06:00)
		# Either current time is after (start - grace) OR before end
		if effective_start >= 0:
			return current_seconds >= effective_start or current_seconds <= end_seconds
		else:
			# Grace period wraps to previous day (e.g., start 00:30, grace 60min → -30min → 23:30)
			effective_start_wrapped = effective_start + 86400
			return current_seconds >= effective_start_wrapped or current_seconds <= end_seconds


def _time_to_seconds(time_str):
	"""Convert HH:MM:SS or HH:MM string to seconds from midnight."""
	parts = cstr(time_str).split(":")
	hours = int(parts[0]) if len(parts) > 0 else 0
	minutes = int(parts[1]) if len(parts) > 1 else 0
	seconds = int(parts[2]) if len(parts) > 2 else 0
	return hours * 3600 + minutes * 60 + seconds


def _timedelta_to_seconds(td):
	"""Convert a timedelta or time string to seconds from midnight."""
	from datetime import timedelta

	if isinstance(td, timedelta):
		return int(td.total_seconds())
	return _time_to_seconds(cstr(td))


def _get_shift_time_details(shift_assignments):
	"""Build a readable string of shift times for the error message."""
	details = []
	seen = set()
	for assignment in shift_assignments:
		shift_type = assignment.get("shift_type")
		if not shift_type or shift_type in seen:
			continue
		seen.add(shift_type)
		shift_doc = frappe.db.get_value(
			"Shift Type",
			shift_type,
			["start_time", "end_time"],
			as_dict=1,
		)
		if shift_doc:
			start = _format_time(shift_doc.start_time)
			end = _format_time(shift_doc.end_time)
			details.append(f"<b>{shift_type}</b>: {start} – {end}")
		else:
			details.append(f"<b>{shift_type}</b>")
	return "<br>".join(details) if details else "No shift details available"


def _format_time(td):
	"""Format a timedelta or time string as HH:MM."""
	from datetime import timedelta

	if isinstance(td, timedelta):
		total_seconds = int(td.total_seconds())
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		return f"{hours:02d}:{minutes:02d}"
	parts = cstr(td).split(":")
	return f"{parts[0]}:{parts[1]}" if len(parts) >= 2 else cstr(td)


def _notify_manager_of_blocked_login(employee, user, shift_names, current_time):
	"""Log the violation and notify Hotel Managers."""
	employee_name = frappe.db.get_value("Employee", employee, "employee_name") or employee

	# Log to Error Log for audit trail
	frappe.log_error(
		title="Shift Login Violation",
		message=(
			f"Employee: {employee_name} ({employee})\n"
			f"User: {user}\n"
			f"Attempted at: {nowdate()} {current_time[:5]}\n"
			f"Assigned shift(s): {shift_names}\n"
			f"Action: Login blocked — outside shift hours"
		),
	)

	# Send email notification to Hotel Managers
	try:
		manager_users = frappe.db.sql_list("""
			SELECT DISTINCT u.name
			FROM `tabHas Role` hr
			JOIN `tabUser` u ON u.name = hr.parent
			WHERE hr.role = 'Hotel Manager'
			  AND u.enabled = 1
			  AND u.name NOT IN ('Administrator', 'Guest')
		""")

		if manager_users:
			frappe.sendmail(
				recipients=manager_users,
				subject=_("Shift Login Violation: {0}").format(employee_name),
				message=_(
					"<p>An employee attempted to log in outside their assigned shift hours.</p>"
					"<table style='border-collapse:collapse;margin-top:10px;'>"
					"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>Employee:</td>"
					"<td style='padding:4px 0;'>{0} ({1})</td></tr>"
					"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>User:</td>"
					"<td style='padding:4px 0;'>{2}</td></tr>"
					"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>Attempted at:</td>"
					"<td style='padding:4px 0;'>{3} {4}</td></tr>"
					"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>Assigned shift(s):</td>"
					"<td style='padding:4px 0;'>{5}</td></tr>"
					"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>Action:</td>"
					"<td style='padding:4px 0;color:red;'>Login blocked</td></tr>"
					"</table>"
				).format(employee_name, employee, user, nowdate(), current_time[:5], shift_names),
				now=True,
			)
	except Exception:
		# Don't let notification failure block the auth flow
		frappe.log_error(
			title="Shift Login Notification Failed",
			message=frappe.get_traceback(),
		)
