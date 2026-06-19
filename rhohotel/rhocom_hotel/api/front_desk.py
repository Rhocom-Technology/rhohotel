import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, flt, cstr
import json


def _safe_json(filters):
	import json

	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	try:
		return json.loads(filters)
	except Exception:
		return {}


def _normalize_room_status(value):
	status = cstr(value).strip().lower()
	mapping = {
		"vacant": "Vacant",
		"occupied": "Occupied",
		"reserved": "Reserved",
		"maintenance": "Maintenance",
	}
	return mapping.get(status, cstr(value).strip() or "Unknown")


def _normalize_housekeeping_status(value):
	status = cstr(value).strip().lower()
	mapping = {
		"clean": "Clean",
		"dirty": "Dirty",
		"in progress": "In Progress",
		"inspected": "Inspected",
	}
	return mapping.get(status, cstr(value).strip() or "Unknown")


def _night_audit_invoice_source(value):
	return cstr(value).strip().lower()


def _is_room_revenue_source(source):
	source = _night_audit_invoice_source(source)
	if not source:
		# No source tag — treat as room revenue only when caller confirms a check-in link
		return True
	room_keywords = ("room", "accommodation", "lodging", "stay", "night audit", "late charge", "transfer")
	return any(keyword in source for keyword in room_keywords)


def _is_fnb_revenue_source(source):
	source = _night_audit_invoice_source(source)
	fnb_keywords = ("restaurant", "bar", "food", "beverage", "f&b", "pos", "laundry", "spa", "minibar")
	return any(keyword in source for keyword in fnb_keywords)


def _room_column_expr(fieldname, alias=None, fallback="NULL"):
	alias = alias or fieldname
	if frappe.db.has_column("Hotel Room", fieldname):
		return f"room.`{fieldname}` as `{alias}`"
	return f"{fallback} as `{alias}`"


def _as_bool(value):
	if isinstance(value, bool):
		return value
	if value is None:
		return False
	return cstr(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _compute_room_subtitle(room):
	if room.get("overdue"):
		return "Overdue check-out"
	if room.get("status") == "Maintenance":
		return "Under maintenance"
	if room.get("housekeeping_status") == "Dirty":
		return "Needs housekeeping attention"
	if room.get("status") == "Reserved":
		return "Arrival expected"
	if room.get("expected_check_out_datetime"):
		checkout = room.get("expected_check_out_datetime")
		return f"Check-out: {checkout.strftime('%d %b')} • {checkout.strftime('%I:%M %p')}"
	return "Ready for walk-in or reservation"


def _matches_room_view_filters(room, filters):
	query = cstr(filters.get("search")).strip().lower()
	if query:
		if not (
			query in cstr(room.get("room_number")).lower()
			or query in cstr(room.get("current_guest")).lower()
			or query in cstr(room.get("room_type")).lower()
		):
			return False

	if filters.get("floor") and cstr(room.get("floor")) != cstr(filters.get("floor")):
		return False
	if filters.get("room_type") and cstr(room.get("room_type")) != cstr(filters.get("room_type")):
		return False
	if filters.get("status") and cstr(room.get("status")) != cstr(filters.get("status")):
		return False
	if filters.get("housekeeping_status") and cstr(room.get("housekeeping_status")) != cstr(
		filters.get("housekeeping_status")
	):
		return False
	if _as_bool(filters.get("only_overdue")) and not room.get("overdue"):
		return False
	if _as_bool(filters.get("vip_only")) and room.get("status") != "Reserved":
		return False
	if _as_bool(filters.get("dirty_only")) and room.get("housekeeping_status") != "Dirty":
		return False

	return True


@frappe.whitelist()
def get_room_view_data(filters=None):
	"""Return RoomView payload with normalized room rows and stats.

	Optional filters keys:
	- search
	- floor
	- room_type
	- status
	- housekeeping_status
	- only_overdue
	- vip_only
	- dirty_only
	"""
	filters = _safe_json(filters)

	rooms = frappe.get_all(
		"Hotel Room",
		fields=[
			"name",
			"room_number",
			"room_type",
			"floor",
			"status",
			"housekeeping_status",
			"current_guest",
		],
		order_by="room_number asc",
		limit_page_length=1000,
	)

	active_checkins = frappe.get_all(
		"Hotel Room Check In",
		filters={"status": "Checked In"},
		fields=[
			"name",
			"room_number",
			"guest",
			"reservation_source",
			"expected_check_out_datetime",
			"total_outstanding_amount",
		],
		limit_page_length=1000,
	)

	checkin_map = {}
	for checkin in active_checkins:
		key = cstr(checkin.get("room_number")).strip()
		if key:
			checkin_map[key] = checkin

	today = frappe.utils.today()
	reservation_rows = frappe.db.sql(
		"""
		SELECT
			rr.room_number,
			rr.room_type,
			rr.rate_per_night,
			rr.number_of_nights,
			hr.name AS reservation,
			hr.primary_guest_name,
			hr.primary_guest_phone,
			hr.primary_guest_email,
			hr.corporate_guest,
			hr.customer,
			hr.reservation_type,
			hr.from_date,
			hr.to_date
		FROM `tabHotel Reservation Room` rr
		INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
		WHERE hr.docstatus != 2
		  AND hr.reservation_status = 'Confirmed'
		  AND hr.from_date = %s
		ORDER BY hr.creation ASC
		""",
		today,
		as_dict=True,
	)
	reservation_map = {}
	for reservation in reservation_rows:
		key = cstr(reservation.get("room_number")).strip()
		if key and key not in reservation_map:
			reservation_map[key] = reservation

	now = now_datetime()
	room_rows = []
	for room in rooms:
		room_key = cstr(room.get("room_number") or room.get("name")).strip()
		checkin = checkin_map.get(room_key) or {}
		reservation = reservation_map.get(room_key) or {}
		status = _normalize_room_status(room.get("status"))
		if reservation and status == "Vacant":
			status = "Reserved"
		elif status == "Reserved" and not reservation:
			# Room was marked Reserved for a future reservation — treat as Vacant for today's view
			status = "Vacant"
		housekeeping_status = _normalize_housekeeping_status(room.get("housekeeping_status"))
		expected_checkout = checkin.get("expected_check_out_datetime")
		overdue = bool(status == "Occupied" and expected_checkout and expected_checkout < now)
		unpaid = flt(checkin.get("total_outstanding_amount")) > 0

		row = {
			"name": room.get("name"),
			"room_number": room.get("room_number") or room.get("name"),
			"room_type": room.get("room_type"),
			"floor": room.get("floor"),
			"status": status,
			"housekeeping_status": housekeeping_status,
			"current_guest": room.get("current_guest") or checkin.get("guest") or reservation.get("primary_guest_name"),
			"check_in": checkin.get("name"),
			"reservation": reservation.get("reservation"),
			"reservation_type": reservation.get("reservation_type"),
			"reservation_arrival": reservation.get("from_date"),
			"reservation_departure": reservation.get("to_date"),
			"reserved_for": reservation.get("primary_guest_name"),
			"guest_phone": reservation.get("primary_guest_phone"),
			"guest_email": reservation.get("primary_guest_email"),
			"corporate_guest": reservation.get("corporate_guest"),
			"customer": reservation.get("customer"),
			"rate_per_night": flt(reservation.get("rate_per_night")),
			"number_of_nights": reservation.get("number_of_nights"),
			"reservation_source": checkin.get("reservation_source"),
			"expected_check_out_datetime": expected_checkout,
			"total_outstanding_amount": flt(checkin.get("total_outstanding_amount")),
			"overdue": overdue,
			"unpaid": unpaid,
		}
		row["subtitle"] = _compute_room_subtitle(row)
		room_rows.append(row)

	reserved_today = len({row.get("reservation") for row in reservation_rows if row.get("reservation")})

	stats = {
		"vacant": len([r for r in room_rows if r.get("status") == "Vacant"]),
		"occupied": len([r for r in room_rows if r.get("status") == "Occupied"]),
		"reserved": reserved_today,
		"dirty": len([r for r in room_rows if r.get("housekeeping_status") == "Dirty"]),
		"maintenance": len([r for r in room_rows if r.get("status") == "Maintenance"]),
		"overdue": len([r for r in room_rows if r.get("overdue")]),
		"unpaid": len([r for r in room_rows if r.get("unpaid")]),
		"vip": len([r for r in room_rows if r.get("status") == "Reserved"]),
	}

	filtered = [row for row in room_rows if _matches_room_view_filters(row, filters)]

	return {
		"rooms": filtered,
		"stats": stats,
		"total_rooms": len(room_rows),
		"filtered_rooms": len(filtered),
	}


@frappe.whitelist()
def get_rooms_summary(filters=None):
	"""Return list of rooms with status, maintenance, current_check_in info and reservation/check-out times.
	filters (json string) can include: floor, room_type, status, maintenance, upcoming_checkout_hours
	"""
	import json

	filters = json.loads(filters) if filters else {}
	conds = ["1=1"]
	args = []
	if filters.get("floor"):
		conds.append("room.floor = %s")
		args.append(filters.get("floor"))
	if filters.get("room_type"):
		conds.append("room.room_type = %s")
		args.append(filters.get("room_type"))
	if filters.get("status"):
		conds.append("room.status = %s")
		args.append(filters.get("status"))
	if filters.get("maintenance") and frappe.db.has_column("Hotel Room", "maintenance_flag"):
		conds.append("room.maintenance_flag = 1")
	if filters.get("housekeeper_present") and frappe.db.has_column("Hotel Room", "last_keycard_user"):
		conds.append("room.last_keycard_user IS NOT NULL")

	# upcoming checkout window
	upcoming_hours = filters.get("upcoming_checkout_hours")
	if upcoming_hours:
		end = add_to_date(now_datetime(), hours=upcoming_hours)
		conds.append("(ci.expected_check_out_datetime between %s and %s)")
		args.extend([now_datetime(), end])

	maintenance_expr = _room_column_expr("maintenance_flag", "maintenance", "0")
	last_keycard_user_expr = _room_column_expr("last_keycard_user")
	last_keycard_time_expr = _room_column_expr("last_keycard_time")
	current_check_in_expr = _room_column_expr("current_check_in")
	current_check_in_join = "room.current_check_in" if frappe.db.has_column("Hotel Room", "current_check_in") else "NULL"
	reservation_link = (
		"ci.canonical_reservation"
		if frappe.db.has_column("Hotel Room Check In", "canonical_reservation")
		else "NULL"
	)

	query = f"""
		select
			room.name as room,
			room.room_number as room_number,
			room.room_type as room_type,
			room.floor as floor,
			room.status as status,
			{maintenance_expr},
			{last_keycard_user_expr},
			{last_keycard_time_expr},
			{current_check_in_expr},
			COALESCE(g.hotel_guest_name, ci.guest) as guest_name,
			ci.expected_check_out_datetime as expected_check_out_datetime,
			r.name as reservation,
			r.source_channel as reservation_source
		from
			`tabHotel Room` room
		left join
			`tabHotel Room Check In` ci on ci.name = {current_check_in_join}
		left join
			`tabHotel Guest` g on g.name = ci.guest
		left join
			`tabHotel Reservation` r on r.name = {reservation_link}
		where {" AND ".join(conds)}
		order by room.floor, room.name
	"""
	rows = frappe.db.sql(query, tuple(args), as_dict=1)
	return rows


@frappe.whitelist()
def make_check_out(checkin_name):
	"""Perform checkout for the given Hotel Room Check In docname.
	Sets actual_check_out_datetime, status and frees up the room.
	"""
	ci = frappe.get_doc("Hotel Room Check In", checkin_name)
	if ci.status == "Checked Out":
		frappe.throw(_("Check-in {0} already checked out").format(checkin_name))
	from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

	folio = sync_checkin_folio_totals(checkin_name)
	summary = folio.get("summary") or {}
	outstanding = flt(summary.get("collectible_outstanding") or summary.get("balance_amount"))
	if outstanding > 0:
		roles = frappe.get_roles(frappe.session.user)
		if frappe.session.user != "Administrator" and "Front Desk Manager" not in roles:
			frappe.throw(
				_("Only a Front Desk Manager can check out a guest with an outstanding bill.")
			)
	ci.actual_check_out_datetime = now_datetime()
	ci.status = "Checked Out"
	# placeholder: calculate extra charges here if required
	if not ci.total_charges:
		ci.total_charges = 0.0
	ci.save()

	# update linked room
	if ci.room_number:
		room = frappe.get_doc("Hotel Room", ci.room_number)
		room.status = "Vacant"
		room.current_check_in = None
		room.save()

	# optionally submit the checkin doc if submittable
	if ci.docstatus == 0 and ci.meta.is_submittable:
		ci.submit()

	return {"success": True, "checkin": ci.name}


@frappe.whitelist()
def get_checkin_invoice_list(check_in):
	"""Return compact list of invoices and totals for a check-in."""
	if not check_in:
		frappe.throw("Check-in not supplied")

	from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

	folio = sync_checkin_folio_totals(check_in)
	summary = folio.get("summary") or {}
	invoices = []
	for row in folio.get("sales_invoices") or []:
		invoices.append(
			{
				"name": row.get("name"),
				"posting_date": row.get("posting_date"),
				"grand_total": row.get("grand_total"),
				"outstanding_amount": row.get("net_outstanding_amount") if not row.get("is_return") else row.get("open_credit_amount"),
				"raw_outstanding_amount": row.get("raw_outstanding_amount"),
				"docstatus": 1,
				"customer": row.get("customer"),
				"is_return": row.get("is_return"),
			}
		)

	return {
		"invoices": invoices,
		"total_invoiced": summary.get("net_bill", 0),
		"total_outstanding": summary.get("balance_amount", 0),
		"billing_summary": summary,
	}


@frappe.whitelist()
def collect_payment_for_checkin(check_in, allocations=None, payment_info=None):
	"""Create and submit a Payment Entry for a Hotel Room Check In.

	allocations: JSON string or list of {invoice: name, amount: value}
	payment_info: JSON string or dict with keys: mode_of_payment, paid_amount, reference_no, reference_date, remarks
	Returns: dict with payment_entry name
	"""
	import json

	if not check_in:
		frappe.throw("Check-in not supplied")

	allocations = (
		json.loads(allocations) if allocations and isinstance(allocations, str) else (allocations or [])
	)
	payment_info = (
		json.loads(payment_info) if payment_info and isinstance(payment_info, str) else (payment_info or {})
	)

	company = frappe.db.get_single_value("Global Defaults", "default_company")
	mop = frappe.get_doc("Mode of Payment", payment_info.get("mode_of_payment"))

	if not mop.accounts:
		frappe.throw("Mode of Payment has no accounts configured.")

	mop_account = next((a.default_account for a in mop.accounts if a.company == company), None)

	if not mop_account:
		frappe.throw(f"No account found for Mode of Payment in {company}")

	receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")
	if not receivable_account:
		frappe.throw("Default Receivable Account is not set for the company.")

	# avoid duplicate reference numbers
	if payment_info.get("reference_no"):
		existing_pe = frappe.db.get_value("Payment Entry", {"reference_no": payment_info.get("reference_no")})
		if existing_pe:
			frappe.throw("A Payment Entry with this reference number already exists.")

	# Fetch check-in and guest/customer
	ci = frappe.get_doc("Hotel Room Check In", check_in)
	guest = None
	customer = None
	try:
		if ci.guest:
			guest = frappe.get_doc("Hotel Guest", ci.guest)
			customer = guest.customer
	except Exception:
		customer = None

	allocation_invoice_names = []
	for alloc in allocations:
		ref_doctype = alloc.get("doctype") or "Sales Invoice"
		ref_name = alloc.get("invoice") or alloc.get("invoice_name") or alloc.get("name")
		if ref_doctype == "Sales Invoice" and ref_name:
			allocation_invoice_names.append(ref_name)
	if allocation_invoice_names:
		invoice_customers = frappe.get_all(
			"Sales Invoice",
			filters={"name": ["in", list(dict.fromkeys(allocation_invoice_names))], "docstatus": 1},
			pluck="customer",
		)
		invoice_customers = list(dict.fromkeys([name for name in invoice_customers if name]))
		if len(invoice_customers) > 1:
			frappe.throw(_("Selected invoices belong to different customers. Please receive payment for one customer at a time."))
		if invoice_customers:
			customer = invoice_customers[0]

	total_paid = float(payment_info.get("paid_amount") or 0)
	if total_paid <= 0:
		total_paid = sum(float(a.get("amount") or 0) for a in allocations)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.party_type = "Customer"
	pe.party = customer or ci.guest or ""
	pe.paid_from = receivable_account
	pe.paid_from_account_type = "Receivable"
	pe.posting_date = payment_info.get("payment_date") or frappe.utils.today()
	pe.paid_amount = total_paid
	pe.paid_to = mop_account
	pe.received_amount = total_paid
	pe.source_exchange_rate = 1
	pe.target_exchange_rate = 1
	pe.company = company
	pe.mode_of_payment = payment_info.get("mode_of_payment") or payment_info.get("mode") or "Cash"
	if payment_info.get("reference_no"):
		pe.reference_no = payment_info.get("reference_no")
	if payment_info.get("reference_date"):
		pe.reference_date = payment_info.get("reference_date")
	if payment_info.get("remarks"):
		pe.remarks = payment_info.get("remarks")

	# link to check-in for traceability
	pe.custom_hotel_room_check_in = check_in

	# Append references
	for alloc in allocations:
		ref_name = alloc.get("invoice") or alloc.get("invoice_name") or alloc.get("name")
		ref_doctype = alloc.get("doctype") or "Sales Invoice"
		requested_amount = float(alloc.get("amount") or 0)
		if not ref_name or requested_amount <= 0:
			continue

		if ref_doctype == "Journal Entry":
			# Validate the JE belongs to this check-in
			je_check_in = frappe.db.get_value("Journal Entry", ref_name, "custom_hotel_room_check_in")
			if je_check_in != check_in:
				frappe.throw(_("Journal Entry {0} is not linked to Check In {1}.").format(ref_name, check_in))
			if frappe.db.get_value("Journal Entry", ref_name, "docstatus") != 1:
				frappe.throw(_("Journal Entry {0} is not submitted.").format(ref_name))

			# Compute outstanding on the JE
			debit_total = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(debit_in_account_currency), 0)
				FROM `tabJournal Entry Account`
				WHERE parent = %s AND debit_in_account_currency > 0 AND party_type = 'Customer'
				""",
				ref_name,
			)[0][0] or 0

			paid_already = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(per.allocated_amount), 0)
				FROM `tabPayment Entry Reference` per
				JOIN `tabPayment Entry` pe ON per.parent = pe.name
				WHERE per.reference_doctype = 'Journal Entry'
				AND per.reference_name = %s
				AND pe.docstatus = 1
				AND pe.payment_type = 'Receive'
				""",
				ref_name,
			)[0][0] or 0

			je_outstanding = max(0, float(debit_total) - float(paid_already))
			allocated_amount = min(requested_amount, je_outstanding)
			if allocated_amount <= 0:
				continue

			pe.append(
				"references",
				{
					"reference_doctype": "Journal Entry",
					"reference_name": ref_name,
					"allocated_amount": allocated_amount,
				},
			)
		else:
			invoice = frappe.get_doc("Sales Invoice", ref_name)
			if invoice.docstatus != 1:
				frappe.throw(_("Invoice {0} is not submitted.").format(ref_name))
			if invoice.custom_hotel_room_check_in != check_in:
				frappe.throw(_("Invoice {0} is not linked to Check In {1}.").format(ref_name, check_in))

			from rhohotel.rhocom_hotel.utils.folio import get_invoice_net_outstanding

			allocated_amount = min(requested_amount, float(get_invoice_net_outstanding(check_in, ref_name) or 0))
			if allocated_amount <= 0:
				continue

			pe.append(
				"references",
				{
					"reference_doctype": "Sales Invoice",
					"reference_name": ref_name,
					"allocated_amount": allocated_amount,
				},
			)

	try:
		pe.insert(ignore_permissions=True)
		# try to submit if possible
		try:
			pe.submit()
		except Exception:
			# if submission fails due to workflow/accounts, keep as draft but return name
			frappe.log_error(
				frappe.get_traceback(), "Payment Entry submit failed from collect_payment_for_checkin"
			)

		# Sync total_outstanding_amount on the check-in so the list view reflects correct status
		try:
			from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

			new_outstanding = (sync_checkin_folio_totals(check_in).get("summary") or {}).get("balance_amount", 0)
			frappe.db.set_value(
				"Hotel Room Check In", check_in, "total_outstanding_amount", new_outstanding,
				update_modified=False
			)
		except Exception:
			pass  # non-critical — list will still refresh via get_checkin_detail

		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to create Payment Entry from front desk")
		frappe.throw("Failed to create payment entry")

	return {"payment_entry": pe.name}


@frappe.whitelist()
def collect_payment_and_checkout(check_in, allocations=None, payment_info=None, force_checkout=False):
	"""Collect payment (if any) and perform checkout for a check-in.

	If outstanding invoices remain after payment and force_checkout is False, raise.
	If force_checkout is True, user must have Manager/System Manager role.
	"""
	import json

	if isinstance(force_checkout, str):
		force_checkout = force_checkout.lower() in ("1", "true", "yes")

	# First collect payment if provided
	if allocations or (
		payment_info
		and (
			payment_info.get("paid_amount")
			or (isinstance(payment_info, dict) and payment_info.get("paid_amount"))
		)
	):
		res = collect_payment_for_checkin(check_in, allocations=allocations, payment_info=payment_info)
		payment_entry = res.get("payment_entry")
	else:
		payment_entry = None

	from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

	folio = sync_checkin_folio_totals(check_in)
	summary = folio.get("summary") or {}
	outstanding = flt(summary.get("collectible_outstanding") or summary.get("balance_amount"))
	if outstanding > 0:
		if not force_checkout:
			frappe.throw(
				"Outstanding invoices remain. Collect payment or use force checkout with manager authorization."
			)
		# check roles
		roles = frappe.get_roles(frappe.session.user)
		if frappe.session.user != "Administrator" and "Front Desk Manager" not in roles:
			frappe.throw("Only a Front Desk Manager can perform a force checkout with outstanding balance")

	# perform checkout using existing helper
	check_out_res = make_check_out(check_in)

	return {"payment_entry": payment_entry, "checkout": check_out_res}


@frappe.whitelist()
def create_payment_receipt(payment_entry):
	"""Return a PDF download URL for a Payment Entry using the Payment Receipt print format."""
	if not payment_entry:
		frappe.throw("Payment entry not supplied")

	# Use frappe print format download endpoint
	site_url = frappe.utils.get_url()
	pd_url = f"/api/method/frappe.utils.print_format.download_pdf?doctype=Payment%20Entry&name={payment_entry}&format=Payment%20Receipt"
	return {"print_url": site_url + pd_url}


@frappe.whitelist()
def get_payment_list(limit=500):
	"""Return a list of Payment Entries for the front desk payment view."""
	fields = [
		"name",
		"posting_date",
		"mode_of_payment",
		"reference_no",
		"party",
		"party_name",
		"paid_amount",
		"received_amount",
		"custom_hotel_room_check_in",
		"docstatus",
	]
	if frappe.db.has_column("Payment Entry", "posting_time"):
		fields.append("posting_time")

	rows = frappe.get_all(
		"Payment Entry",
		fields=fields,
		order_by="posting_date desc, modified desc",
		limit_page_length=int(limit),
		ignore_permissions=False,
	)
	return rows


@frappe.whitelist()
def get_night_audit_data(audit_date=None):
	"""Return a full night audit snapshot for the given date (defaults to today).

	Returns:
	  - audit_date
	  - occupancy: { total_rooms, occupied, vacant, reserved, maintenance, arrivals, departures, occupancy_pct }
	  - revenue: { room_revenue, fnb_revenue, other_revenue, total_revenue, by_room_type }
	  - payments: { total_collected, by_method: [{method, amount, count}] }
	  - outstanding: { total_outstanding, guest_count, ledger: [{check_in, guest, room, amount}] }
	  - room_status: [{ room_number, room_type, floor, status, housekeeping_status, guest, check_in }]
	"""
	from frappe.utils import getdate, nowdate, flt

	audit_date = getdate(audit_date) if audit_date else getdate(nowdate())
	audit_date_str = str(audit_date)

	# ── Occupancy ────────────────────────────────────────────────────────────
	total_rooms = frappe.db.count("Hotel Room")

	occupied = frappe.db.count("Hotel Room", {"status": "Occupied"})
	vacant = frappe.db.count("Hotel Room", {"status": "Vacant"})
	reserved = frappe.db.count("Hotel Room", {"status": "Reserved"})
	maintenance = frappe.db.count("Hotel Room", {"status": "Maintenance"})

	arrivals = frappe.db.count(
		"Hotel Room Check In",
		{
			"check_in_datetime": ["between", [f"{audit_date_str} 00:00:00", f"{audit_date_str} 23:59:59"]],
			"docstatus": 1,
		},
	)

	departures = frappe.db.count(
		"Hotel Room Check In",
		{
			"actual_check_out_datetime": [
				"between",
				[f"{audit_date_str} 00:00:00", f"{audit_date_str} 23:59:59"],
			],
			"status": "Checked Out",
		},
	)

	occupancy_pct = round((occupied / total_rooms * 100), 1) if total_rooms else 0.0

	# ── Revenue ──────────────────────────────────────────────────────────────
	# Count each posted charge once. POS bills posted to a room create both a
	# linked Sales Invoice and a POS Invoice for shift tracking, so consolidated
	# POS rows are excluded here and the linked Sales Invoice is classified by
	# custom_invoice_source.
	source_field = "si.custom_invoice_source" if frappe.db.has_column("Sales Invoice", "custom_invoice_source") else "NULL"
	room_invoices = frappe.db.sql(
		"""
		SELECT si.name, si.grand_total, si.custom_hotel_room_check_in,
		       {source_field} AS custom_invoice_source,
		       ci.room_number, ci.room_type
		FROM `tabSales Invoice` si
		LEFT JOIN `tabHotel Room Check In` ci ON ci.name = si.custom_hotel_room_check_in
		WHERE si.posting_date = %s AND si.docstatus = 1
		""".format(source_field=source_field),
		audit_date_str,
		as_dict=True,
	)

	room_revenue = 0.0
	fnb_revenue = 0.0
	other_revenue = 0.0
	by_room_type_map = {}

	for r in room_invoices:
		amount = flt(r.grand_total)
		source = _night_audit_invoice_source(r.get("custom_invoice_source"))
		has_checkin = bool(r.custom_hotel_room_check_in)
		if has_checkin and _is_room_revenue_source(source):
			room_revenue += amount
			if r.room_type:
				by_room_type_map[r.room_type] = by_room_type_map.get(r.room_type, 0) + amount
		elif _is_fnb_revenue_source(source):
			fnb_revenue += amount
		else:
			other_revenue += amount

	try:
		pos_conditions = ["pi.posting_date = %s", "pi.docstatus = 1"]
		pos_room_field = "pi.custom_hotel_room_check_in" if frappe.db.has_column("POS Invoice", "custom_hotel_room_check_in") else "NULL"
		if frappe.db.has_column("POS Invoice", "consolidated_invoice"):
			pos_conditions.append("(pi.consolidated_invoice IS NULL OR pi.consolidated_invoice = '')")

		pos_rows = frappe.db.sql(
			"""
			SELECT pi.name, pi.grand_total,
			       COALESCE(SUM(
			           CASE
			             WHEN LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%room%%'
			               OR LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%folio%%'
			               OR LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%post to room%%'
			               OR (LOWER(IFNULL(pip.mode_of_payment, '')) LIKE '%%credit%%'
			                   AND {pos_room_field} IS NOT NULL AND {pos_room_field} != '')
			             THEN pip.amount ELSE 0
			           END
			       ), 0) AS room_posting_amount
			FROM `tabPOS Invoice` pi
			LEFT JOIN `tabPOS Invoice Payment` pip ON pip.parent = pi.name
			WHERE {conditions}
			GROUP BY pi.name, pi.grand_total
			""".format(conditions=" AND ".join(pos_conditions), pos_room_field=pos_room_field),
			audit_date_str,
			as_dict=True,
		)
		for row in pos_rows:
			fnb_revenue += max(flt(row.grand_total) - flt(row.room_posting_amount), 0)
	except Exception:
		pass

	total_revenue = flt(room_revenue + fnb_revenue + other_revenue)
	by_room_type = [{"room_type": k, "revenue": v} for k, v in sorted(by_room_type_map.items())]

	# ── Payments ─────────────────────────────────────────────────────────────
	payment_rows = frappe.db.sql(
		"""
		SELECT mode_of_payment, SUM(received_amount) as total, COUNT(*) as cnt
		FROM `tabPayment Entry`
		WHERE posting_date = %s AND docstatus = 1 AND payment_type = 'Receive'
		GROUP BY mode_of_payment
		ORDER BY total DESC
		""",
		audit_date_str,
		as_dict=True,
	)

	total_collected = flt(sum(r.total or 0 for r in payment_rows))
	by_method = [
		{"method": r.mode_of_payment or "Unknown", "amount": flt(r.total), "count": r.cnt}
		for r in payment_rows
	]

	# ── Outstanding Balances ─────────────────────────────────────────────────
	# Pending-payment stat: only invoices posted on the audit date.
	# This represents what was charged and not yet settled on this specific day.
	open_invoice_rows = frappe.db.sql(
		"""
		SELECT si.name, si.customer, si.customer_name, si.outstanding_amount
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		  AND si.posting_date = %s
		  AND si.outstanding_amount > 0
		  AND IFNULL(si.is_return, 0) = 0
		  AND IFNULL(si.status, '') NOT IN ('Cancelled', 'Return')
		ORDER BY si.name ASC
		""",
		audit_date_str,
		as_dict=True,
	)
	total_outstanding = flt(sum(flt(row.outstanding_amount) for row in open_invoice_rows))
	open_invoice_count = len(open_invoice_rows)

	active_checkin_rows = frappe.db.sql(
		"""
		SELECT ci.name as check_in, ci.guest, ci.room_number
		FROM `tabHotel Room Check In` ci
		WHERE ci.status = 'Checked In'
		  AND ci.docstatus = 1
		""",
		as_dict=True,
	)

	checkin_names = [r.check_in for r in active_checkin_rows]
	outstanding_map = {}
	if checkin_names and frappe.db.has_column("Sales Invoice", "custom_hotel_room_check_in"):
		si_rows = frappe.db.sql(
			"""
			SELECT custom_hotel_room_check_in,
			       COALESCE(SUM(outstanding_amount), 0) AS outstanding
			FROM `tabSales Invoice`
			WHERE custom_hotel_room_check_in IN %(checkins)s
			  AND docstatus = 1
			  AND outstanding_amount > 0
			  AND IFNULL(status, '') != 'Cancelled'
			GROUP BY custom_hotel_room_check_in
			""",
			{"checkins": checkin_names},
			as_dict=True,
		)
		for row in si_rows:
			outstanding_map[row.custom_hotel_room_check_in] = flt(row.outstanding)
	elif checkin_names:
		# Fallback: stored field if custom column doesn't exist
		fb_rows = frappe.db.sql(
			"""
			SELECT name AS check_in, total_outstanding_amount AS outstanding
			FROM `tabHotel Room Check In`
			WHERE name IN %(checkins)s
			""",
			{"checkins": checkin_names},
			as_dict=True,
		)
		for row in fb_rows:
			outstanding_map[row.check_in] = flt(row.outstanding)

	guest_name_cache = {}
	ledger = []
	for r in active_checkin_rows:
		amount = outstanding_map.get(r.check_in, 0)
		if amount <= 0:
			continue
		gid = r.guest
		if gid:
			if gid not in guest_name_cache:
				guest_name_cache[gid] = frappe.db.get_value("Hotel Guest", gid, "hotel_guest_name") or gid
			display = guest_name_cache[gid]
		else:
			display = "—"
		ledger.append({
			"check_in": r.check_in,
			"guest": display,
			"room": r.room_number or "—",
			"amount": amount,
		})

	ledger.sort(key=lambda x: x["amount"], reverse=True)
	in_house_outstanding = flt(sum(row["amount"] for row in ledger))

	# ── Room Status Snapshot ─────────────────────────────────────────────────
	rooms = frappe.get_all(
		"Hotel Room",
		fields=["name", "room_number", "room_type", "floor", "status", "housekeeping_status", "current_guest"],
		order_by="room_number asc",
		limit_page_length=500,
	)

	active_checkins = frappe.get_all(
		"Hotel Room Check In",
		filters={"status": "Checked In", "docstatus": 1},
		fields=["name", "room_number", "guest"],
		limit_page_length=500,
	)
	checkin_by_room = {cstr(c.room_number).strip(): c for c in active_checkins}

	room_status = []
	for rm in rooms:
		rn = cstr(rm.room_number or rm.name).strip()
		ci = checkin_by_room.get(rn, {})
		guest_id = rm.current_guest or (ci.get("guest") if ci else None)
		guest_display = ""
		if guest_id:
			guest_display = frappe.db.get_value("Hotel Guest", guest_id, "hotel_guest_name") or guest_id
		room_status.append(
			{
				"room_number": rm.room_number or rm.name,
				"room_type": rm.room_type or "—",
				"floor": rm.floor or "—",
				"status": _normalize_room_status(rm.status),
				"housekeeping_status": _normalize_housekeeping_status(rm.housekeeping_status),
				"guest": guest_display,
				"check_in": ci.get("name") if ci else None,
			}
		)

	# ── No-shows ─────────────────────────────────────────────────────────────
	noshows = 0
	try:
		noshows = int(
			frappe.db.sql(
				"""
				SELECT COUNT(*) FROM `tabHotel Reservation`
				WHERE DATE(from_date) = %s
				  AND reservation_status NOT IN ('Checked In','Checked Out','Cancelled')
				""",
				audit_date_str,
			)[0][0]
			or 0
		)
	except Exception:
		pass

	# ── Open POS Orders (draft invoices) ─────────────────────────────────────
	open_pos_orders = 0
	try:
		open_pos_orders = int(frappe.db.count("POS Invoice", {"docstatus": 0}) or 0)
	except Exception:
		pass

	# ── Unallocated submitted Payment Entries ────────────────────────────────
	unallocated_payments = 0
	try:
		unallocated_payments = int(
			frappe.db.sql(
				"""
				SELECT COUNT(*) FROM `tabPayment Entry` pe
				WHERE pe.posting_date = %s
				  AND pe.docstatus = 1
				  AND pe.payment_type = 'Receive'
				  AND NOT EXISTS (
				      SELECT 1 FROM `tabPayment Entry Reference` per
				      WHERE per.parent = pe.name
				  )
				""",
				audit_date_str,
			)[0][0]
			or 0
		)
	except Exception:
		pass

	# ── Hourly Movement (arrivals / departures bucketed by hour) ─────────────
	hourly_movement = []
	try:
		arr_rows = frappe.db.sql(
			"""
			SELECT HOUR(check_in_datetime) AS hr, COUNT(*) AS cnt
			FROM `tabHotel Room Check In`
			WHERE DATE(check_in_datetime) = %s AND docstatus = 1
			GROUP BY HOUR(check_in_datetime)
			""",
			audit_date_str,
			as_dict=True,
		)
		dep_rows = frappe.db.sql(
			"""
			SELECT HOUR(actual_check_out_datetime) AS hr, COUNT(*) AS cnt
			FROM `tabHotel Room Check In`
			WHERE DATE(actual_check_out_datetime) = %s AND status = 'Checked Out'
			GROUP BY HOUR(actual_check_out_datetime)
			""",
			audit_date_str,
			as_dict=True,
		)
		arr_map = {r.hr: int(r.cnt) for r in arr_rows}
		dep_map = {r.hr: int(r.cnt) for r in dep_rows}
		all_hours = sorted(set(arr_map.keys()) | set(dep_map.keys()))
		hourly_movement = [
			{"hour": h, "arrivals": arr_map.get(h, 0), "departures": dep_map.get(h, 0)}
			for h in all_hours
		]
	except Exception:
		pass

	return {
		"audit_date": audit_date_str,
		"occupancy": {
			"total_rooms": total_rooms,
			"occupied": occupied,
			"vacant": vacant,
			"reserved": reserved,
			"maintenance": maintenance,
			"arrivals": arrivals,
			"departures": departures,
			"noshows": noshows,
			"occupancy_pct": occupancy_pct,
		},
		"revenue": {
			"room_revenue": room_revenue,
			"fnb_revenue": fnb_revenue,
			"other_revenue": other_revenue,
			"total_revenue": total_revenue,
			"by_room_type": by_room_type,
		},
		"payments": {
			"total_collected": total_collected,
			"by_method": by_method,
		},
		"outstanding": {
			"total_outstanding": total_outstanding,
			"open_invoice_count": open_invoice_count,
			"guest_count": len(ledger),
			"in_house_outstanding": in_house_outstanding,
			"ledger": ledger,
		},
		"room_status": room_status,
		"critical": {
			"open_pos_orders": open_pos_orders,
			"unallocated_payments": unallocated_payments,
		},
		"hourly_movement": hourly_movement,
		"is_closed": bool(frappe.cache().get_value("rhohotel:night_audit_closed:{0}".format(audit_date_str))),
	}


def _resolve_room_docname(room):
	room = cstr(room).strip()
	if not room:
		frappe.throw(_("Room is required."))

	if frappe.db.exists("Hotel Room", room):
		return room

	docname = frappe.db.get_value("Hotel Room", {"room_number": room}, "name")
	if docname:
		return docname

	frappe.throw(_("Room {0} was not found.").format(room))


def _has_manager_role(user):
	roles = set(frappe.get_roles(user or frappe.session.user))
	return bool({"System Manager", "Hotel Manager", "Front Desk Manager"} & roles)


@frappe.whitelist()
def block_room(room, reason=None):
	"""Block a room from front desk operations.

	Sets room status to Maintenance and raises maintenance flag where available.
	"""
	user = frappe.session.user
	if not _has_manager_role(user):
		frappe.throw(_("Only a manager can block rooms."))

	docname = _resolve_room_docname(room)
	room_doc = frappe.get_doc("Hotel Room", docname)

	if cstr(room_doc.get("status")).strip().lower() == "occupied" or room_doc.get("current_check_in"):
		frappe.throw(_("Room {0} is currently occupied and cannot be blocked.").format(room_doc.room_number or room_doc.name))

	room_doc.status = "Maintenance"
	if room_doc.meta.has_field("maintenance_flag"):
		room_doc.maintenance_flag = 1
	if room_doc.meta.has_field("operational_status"):
		room_doc.operational_status = "Out of Service"

	reason_text = cstr(reason).strip() or _("Blocked from Front Desk")
	if room_doc.meta.has_field("operational_notes"):
		existing = cstr(room_doc.operational_notes or "").strip()
		stamp = now_datetime().strftime("%Y-%m-%d %H:%M")
		note = "[{0}] {1}: {2}".format(stamp, user, reason_text)
		room_doc.operational_notes = "\n".join([v for v in [existing, note] if v])

	room_doc.save(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger("rhohotel.front_desk").info(
		"room_block user=%s room=%s reason=%s", user, room_doc.name, reason_text
	)

	return {
		"status": "blocked",
		"room": room_doc.name,
		"room_number": room_doc.room_number or room_doc.name,
		"message": _("Room {0} has been blocked.").format(room_doc.room_number or room_doc.name),
	}


@frappe.whitelist()
def close_day(audit_date=None, force_close=False, reason=None):
	"""Close front-desk day with control checks and an idempotent close marker."""
	from frappe.utils import getdate, nowdate

	user = frappe.session.user
	if not _has_manager_role(user):
		frappe.throw(_("Only managers can close day."))

	if isinstance(force_close, str):
		force_close = force_close.strip().lower() in ("1", "true", "yes", "on")
	force_close = bool(force_close)

	audit_date_str = str(getdate(audit_date) if audit_date else getdate(nowdate()))
	cache_key = "rhohotel:night_audit_closed:{0}".format(audit_date_str)
	cached = frappe.cache().get_value(cache_key)
	if cached:
		try:
			already = json.loads(cached)
		except Exception:
			already = {"raw": cstr(cached)}
		return {
			"status": "already_closed",
			"audit_date": audit_date_str,
			"message": _("Day is already closed for {0}.").format(audit_date_str),
			"closed_meta": already,
		}

	# Validate control exceptions for the closing date
	open_pos_orders = 0
	unallocated_payments = 0
	outstanding_count = 0
	outstanding_amount = 0.0

	try:
		open_pos_orders = int(frappe.db.count("POS Invoice", {"docstatus": 0}) or 0)
	except Exception:
		open_pos_orders = 0

	try:
		unallocated_payments = int(
			frappe.db.sql(
				"""
				SELECT COUNT(*) FROM `tabPayment Entry` pe
				WHERE pe.posting_date = %s
				  AND pe.docstatus = 1
				  AND pe.payment_type = 'Receive'
				  AND NOT EXISTS (
				      SELECT 1 FROM `tabPayment Entry Reference` per
				      WHERE per.parent = pe.name
				  )
				""",
				audit_date_str,
			)[0][0]
			or 0
		)
	except Exception:
		unallocated_payments = 0

	try:
		outstanding_rows = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(outstanding_amount), 0) AS total,
			       COUNT(*) AS cnt
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			  AND outstanding_amount > 0
			  AND IFNULL(status, '') != 'Cancelled'
			""",
			as_dict=True,
		)
		row = (outstanding_rows or [{}])[0]
		outstanding_amount = flt(row.get("total") or 0)
		outstanding_count = int(row.get("cnt") or 0)
	except Exception:
		outstanding_amount = 0.0
		outstanding_count = 0

	blockers = []
	if open_pos_orders > 0:
		blockers.append(_("{0} open POS orders").format(open_pos_orders))
	if unallocated_payments > 0:
		blockers.append(_("{0} unallocated payments").format(unallocated_payments))
	if outstanding_count > 0:
		blockers.append(_("{0} open invoices with outstanding balance").format(outstanding_count))

	if blockers and not force_close:
		frappe.throw(
			_("Cannot close day for {0}. Resolve exceptions or force close with reason: {1}").format(
				audit_date_str, ", ".join(blockers)
			)
		)

	if blockers and force_close and not cstr(reason).strip():
		frappe.throw(_("Manager reason is required for force close."))

	close_meta = {
		"audit_date": audit_date_str,
		"closed_by": user,
		"closed_at": now_datetime().isoformat(),
		"force_close": force_close,
		"reason": cstr(reason).strip() if reason else "",
		"summary": {
			"open_pos_orders": open_pos_orders,
			"unallocated_payments": unallocated_payments,
			"outstanding_count": outstanding_count,
			"outstanding_amount": outstanding_amount,
		},
	}

	# Keep marker for 90 days to preserve idempotent behavior.
	frappe.cache().set_value(cache_key, json.dumps(close_meta), expires_in_sec=90 * 24 * 60 * 60)

	frappe.logger("rhohotel.front_desk").info(
		"close_day user=%s date=%s force=%s blockers=%s", user, audit_date_str, force_close, blockers
	)

	return {
		"status": "closed",
		"audit_date": audit_date_str,
		"message": _("Day close completed for {0}.").format(audit_date_str),
		"blockers": blockers,
		"closed_meta": close_meta,
	}
