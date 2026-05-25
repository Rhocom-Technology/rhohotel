"""
ai_tools.py — Read-only hotel data tools for the AI engine.

All functions here are called internally by ai_engine.py.
They are NOT decorated with @frappe.whitelist() and always run under
the current session user's Frappe permissions — never with ignore_permissions.
"""

import frappe
from frappe.utils import today, getdate, flt
import json


# ── Occupancy ────────────────────────────────────────────────────────────────

def get_occupancy_summary():
	"""Current hotel room occupancy counts and percentage."""
	try:
		rooms = frappe.get_all(
			"Hotel Room",
			fields=["name", "occupancy_status", "room_type", "floor"],
			limit_page_length=0,
		)
		total = len(rooms)
		if not total:
			return {"total_rooms": 0, "occupied": 0, "vacant": 0, "maintenance": 0, "occupancy_pct": 0}

		def _match(r, *values):
			return (r.get("occupancy_status") or "").lower() in values

		occupied = sum(1 for r in rooms if _match(r, "occupied"))
		vacant = sum(1 for r in rooms if _match(r, "vacant"))
		maintenance = sum(1 for r in rooms if _match(r, "maintenance", "unavailable", "out of service"))

		return {
			"total_rooms": total,
			"occupied": occupied,
			"vacant": vacant,
			"maintenance": maintenance,
			"occupancy_pct": round((occupied / total) * 100, 1) if total else 0,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_occupancy_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Revenue ──────────────────────────────────────────────────────────────────

def get_revenue_summary(date=None):
	"""Revenue summary for a given date (defaults to today)."""
	try:
		target_date = getdate(date) if date else getdate(today())

		total_rev = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(grand_total), 0) AS total
			FROM `tabSales Invoice`
			WHERE DATE(posting_date) = %s AND docstatus = 1
			""",
			(target_date,),
			as_dict=True,
		)
		total_revenue = flt(total_rev[0].total if total_rev else 0)

		payments = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(paid_amount), 0) AS total
			FROM `tabPayment Entry`
			WHERE DATE(posting_date) = %s AND docstatus = 1 AND payment_type = 'Receive'
			""",
			(target_date,),
			as_dict=True,
		)
		total_collected = flt(payments[0].total if payments else 0)

		return {
			"date": str(target_date),
			"total_revenue": total_revenue,
			"total_collected": total_collected,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_revenue_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── In-House Guests ──────────────────────────────────────────────────────────

def get_inhouse_guests(limit=20):
	"""List of guests currently checked in."""
	try:
		guests = frappe.get_all(
			"Hotel Room Check In",
			filters=[["docstatus", "=", 1]],
			fields=[
				"name", "guest", "room_number",
				"check_in_datetime", "expected_check_out_datetime",
				"total_outstanding_amount",
			],
			order_by="check_in_datetime desc",
			limit_page_length=int(limit),
		)
		return {"guests": [dict(g) for g in guests], "count": len(guests)}
	except Exception as e:
		frappe.log_error(f"AI tool get_inhouse_guests: {e}", "AI Tool Error")
		return {"error": str(e), "guests": [], "count": 0}


# ── Reservations ─────────────────────────────────────────────────────────────

def get_reservations(status=None, date=None, limit=20):
	"""List hotel reservations, optionally filtered by status and check-in date."""
	try:
		filters = []
		if status:
			filters.append(["status", "=", status])
		if date:
			filters.append(["check_in_date", "=", getdate(date)])

		reservations = frappe.get_all(
			"Hotel Reservation",
			filters=filters,
			fields=["name", "guest", "status", "check_in_date", "check_out_date", "room_type", "net_total"],
			order_by="check_in_date desc",
			limit_page_length=int(limit),
		)
		return {"reservations": [dict(r) for r in reservations], "count": len(reservations)}
	except Exception as e:
		frappe.log_error(f"AI tool get_reservations: {e}", "AI Tool Error")
		return {"error": str(e), "reservations": [], "count": 0}


# ── Overdue Checkouts ─────────────────────────────────────────────────────────

def get_overdue_checkouts():
	"""Guests who have passed their expected checkout date but have not checked out."""
	try:
		overdue = frappe.db.sql(
			"""
			SELECT
				ci.name,
				ci.guest,
				ci.room_number,
				ci.expected_check_out_datetime,
				ci.total_outstanding_amount,
				DATEDIFF(NOW(), ci.expected_check_out_datetime) AS overdue_days
			FROM `tabHotel Room Check In` ci
			WHERE ci.docstatus = 1
			  AND ci.expected_check_out_datetime < NOW()
			ORDER BY ci.expected_check_out_datetime ASC
			LIMIT 50
			""",
			as_dict=True,
		)
		return {"overdue": [dict(r) for r in overdue], "count": len(overdue)}
	except Exception as e:
		frappe.log_error(f"AI tool get_overdue_checkouts: {e}", "AI Tool Error")
		return {"error": str(e), "overdue": [], "count": 0}


# ── Guest Profile ─────────────────────────────────────────────────────────────

def get_guest_profile(guest_name):
	"""Retrieve profile for a specific hotel guest."""
	try:
		guest = frappe.get_doc("Hotel Guest", guest_name)
		return {
			"name": guest.name,
			"hotel_guest_name": guest.hotel_guest_name,
			"guest_type": getattr(guest, "guest_type", None),
			"loyalty_tier": getattr(guest, "loyalty_tier", None) or "Base",
			"phone_number": getattr(guest, "phone_number", None),
			"email": getattr(guest, "email", None),
			"nationality": getattr(guest, "nationality", None),
			"total_stays": getattr(guest, "total_stays", 0),
			"lifetime_spend": flt(getattr(guest, "lifetime_spend", 0)),
		}
	except frappe.DoesNotExistError:
		return {"error": f"Guest '{guest_name}' not found."}
	except frappe.PermissionError:
		return {"error": "You do not have permission to view this guest profile."}
	except Exception as e:
		frappe.log_error(f"AI tool get_guest_profile: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Outstanding Invoices ──────────────────────────────────────────────────────

def get_outstanding_invoices(limit=20):
	"""Unpaid or overdue sales invoices."""
	try:
		invoices = frappe.get_all(
			"Sales Invoice",
			filters=[["docstatus", "=", 1], ["outstanding_amount", ">", 0]],
			fields=["name", "customer", "grand_total", "outstanding_amount", "due_date", "posting_date"],
			order_by="outstanding_amount desc",
			limit_page_length=int(limit),
		)
		total_outstanding = sum(flt(i.outstanding_amount) for i in invoices)
		return {
			"invoices": [dict(i) for i in invoices],
			"count": len(invoices),
			"total_outstanding": total_outstanding,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_outstanding_invoices: {e}", "AI Tool Error")
		return {"error": str(e), "invoices": [], "count": 0}


# ── Housekeeping Summary ──────────────────────────────────────────────────────

def get_housekeeping_summary():
	"""Housekeeping task counts by status."""
	try:
		statuses = ["Pending", "Assigned", "In Progress", "Completed", "Approved", "On Hold"]
		counts = {}
		for s in statuses:
			key = s.lower().replace(" ", "_")
			counts[key] = frappe.db.count("Housekeeping Task", {"status": s, "docstatus": ["!=", 2]})
		total = sum(counts.values())
		done = counts.get("completed", 0) + counts.get("approved", 0)
		return {
			"task_counts": counts,
			"total": total,
			"active": counts.get("pending", 0) + counts.get("assigned", 0) + counts.get("in_progress", 0),
			"completion_rate": round((done / total) * 100, 1) if total else 0,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_housekeeping_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Maintenance Summary ───────────────────────────────────────────────────────

def get_maintenance_summary():
	"""Maintenance task and request counts."""
	try:
		open_tasks = frappe.db.count(
			"Maintenance Task", {"status": ["in", ["Open", "In Progress"]], "docstatus": ["!=", 2]}
		)
		urgent_tasks = frappe.db.count(
			"Maintenance Task",
			{"priority": "Urgent", "status": ["in", ["Open", "In Progress"]], "docstatus": ["!=", 2]},
		)
		completed_today = frappe.db.count(
			"Maintenance Task", {"status": "Completed", "modified": [">=", today()]}
		)
		open_requests = frappe.db.count(
			"Maintenance Request", {"status": ["in", ["Open", "Pending"]], "docstatus": ["!=", 2]}
		)
		return {
			"open_tasks": open_tasks,
			"urgent_tasks": urgent_tasks,
			"completed_today": completed_today,
			"open_requests": open_requests,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_maintenance_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── POS Summary ───────────────────────────────────────────────────────────────

def get_pos_summary(date=None):
	"""POS sales summary for a given date."""
	try:
		target_date = getdate(date) if date else getdate(today())
		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(grand_total), 0) AS gross_sales, COUNT(*) AS invoice_count
			FROM `tabPOS Invoice`
			WHERE DATE(posting_date) = %s AND docstatus = 1
			""",
			(target_date,),
			as_dict=True,
		)
		row = result[0] if result else {}
		return {
			"date": str(target_date),
			"gross_sales": flt(row.get("gross_sales", 0)),
			"invoice_count": int(row.get("invoice_count", 0)),
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_pos_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Payment Summary ───────────────────────────────────────────────────────────

def get_payment_summary(date=None):
	"""Payment receipts by method for a given date."""
	try:
		target_date = getdate(date) if date else getdate(today())
		by_method = frappe.db.sql(
			"""
			SELECT mode_of_payment, COALESCE(SUM(paid_amount), 0) AS total
			FROM `tabPayment Entry`
			WHERE DATE(posting_date) = %s AND docstatus = 1 AND payment_type = 'Receive'
			GROUP BY mode_of_payment
			ORDER BY total DESC
			""",
			(target_date,),
			as_dict=True,
		)
		total = sum(flt(r.total) for r in by_method)
		return {
			"date": str(target_date),
			"total_collected": total,
			"by_method": [dict(r) for r in by_method],
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_payment_summary: {e}", "AI Tool Error")
		return {"error": str(e)}


def get_guest_payment_total(guest_query, include_pos=True):
	"""Total amount paid so far by a guest resolved by name/ID/customer mapping."""
	try:
		q = str(guest_query or "").strip()
		if len(q) < 2:
			return {"error": "Guest query must be at least 2 characters."}

		guest_filters = [
			["name", "=", q],
			["hotel_guest_name", "=", q],
			["name", "like", f"%{q}%"],
			["hotel_guest_name", "like", f"%{q}%"],
		]
		guest_rows = frappe.get_all(
			"Hotel Guest",
			or_filters=guest_filters,
			fields=["name", "hotel_guest_name", "customer"],
			order_by="modified desc",
			limit_page_length=20,
		)
		if not guest_rows:
			return {"error": f"No guest found for '{q}'."}

		# Prioritize exact name display matches when available.
		q_lower = q.lower()
		exact_match = next(
			(
				g
				for g in guest_rows
				if (g.get("name") or "").lower() == q_lower
				or (g.get("hotel_guest_name") or "").lower() == q_lower
			),
			None,
		)
		target = exact_match or guest_rows[0]

		aliases = {x for x in [target.get("name"), target.get("hotel_guest_name"), target.get("customer")] if x}
		if not aliases:
			return {"error": f"No customer/guest alias found for '{q}'."}

		alias_list = sorted(aliases)
		placeholders = ", ".join(["%s"] * len(alias_list))

		payment_row = frappe.db.sql(
			f"""
			SELECT COALESCE(SUM(paid_amount), 0) AS total
			FROM `tabPayment Entry`
			WHERE docstatus = 1
			  AND payment_type = 'Receive'
			  AND party_type = 'Customer'
			  AND party IN ({placeholders})
			""",
			tuple(alias_list),
			as_dict=True,
		)
		payment_entry_total = flt((payment_row[0] or {}).get("total", 0))

		pos_total = 0.0
		if include_pos:
			pos_row = frappe.db.sql(
				f"""
				SELECT COALESCE(SUM(paid_amount), 0) AS total
				FROM `tabPOS Invoice`
				WHERE docstatus = 1
				  AND customer IN ({placeholders})
				""",
				tuple(alias_list),
				as_dict=True,
			)
			pos_total = flt((pos_row[0] or {}).get("total", 0))

		return {
			"guest": target.get("hotel_guest_name") or target.get("name"),
			"guest_id": target.get("name"),
			"customer": target.get("customer") or target.get("name"),
			"aliases_checked": alias_list,
			"payment_entry_total": payment_entry_total,
			"pos_paid_total": pos_total,
			"total_paid": payment_entry_total + pos_total,
		}
	except Exception as e:
		frappe.log_error(f"AI tool get_guest_payment_total: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Guest Search ──────────────────────────────────────────────────────────────

def search_guests(query, limit=10):
	"""Search hotel guests by name, phone, or email."""
	try:
		q = str(query or "").strip()
		if len(q) < 2:
			return {"error": "Search query must be at least 2 characters.", "guests": []}

		guests = frappe.get_all(
			"Hotel Guest",
			or_filters=[
				["hotel_guest_name", "like", f"%{q}%"],
				["phone_number", "like", f"%{q}%"],
				["email", "like", f"%{q}%"],
			],
			fields=["name", "hotel_guest_name", "phone_number", "email", "loyalty_tier", "guest_type"],
			limit_page_length=int(limit),
		)
		return {"guests": [dict(g) for g in guests], "count": len(guests)}
	except Exception as e:
		frappe.log_error(f"AI tool search_guests: {e}", "AI Tool Error")
		return {"error": str(e), "guests": [], "count": 0}
