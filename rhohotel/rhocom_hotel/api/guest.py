import frappe
from frappe import _
from frappe.utils import cstr, flt, nowdate
from rhohotel.rhocom_hotel.utils.phone import validate_phone_number


# ---------------------------------------------------------------------------
# Guest List
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_guests(search=None, guest_type=None, loyalty_tier=None, status=None,
               page=1, page_size=25):
	"""Return paginated guest list with optional filters and computed stats."""
	page = int(page or 1)
	page_size = int(page_size or 25)

	filters = {}
	if guest_type:
		filters["guest_type"] = guest_type
	if loyalty_tier:
		filters["loyalty_tier"] = loyalty_tier

	fields = [
		"name", "hotel_guest_name", "guest_type", "title", "gender",
		"phone_number", "email", "nationality", "date_of_birth",
		"id_type", "id_number", "address", "notes", "contact_number",
		"contact_person_name", "preference", "loyalty_tier", "passport_photo", "id_document_scan",
	]

	guests = frappe.get_all(
		"Hotel Guest",
		filters=filters,
		fields=fields,
		order_by="hotel_guest_name asc",
		limit_page_length=1000,
	)

	# Attach active check-in status
	active_checkins = frappe.get_all(
		"Hotel Room Check In",
		filters={"status": "Checked In"},
		fields=["guest", "room_number", "total_outstanding_amount"],
		limit_page_length=5000,
	)
	checkin_map = {}
	for ci in active_checkins:
		g = cstr(ci.get("guest")).strip()
		if g:
			checkin_map[g] = ci

	# Attach stay counts
	stay_counts = frappe.db.sql(
		"""
		SELECT guest, COUNT(*) as cnt
		FROM `tabHotel Room Check In`
		WHERE status IN ('Checked In', 'Checked Out')
		GROUP BY guest
		""",
		as_dict=True,
	)
	stay_map = {row.guest: row.cnt for row in stay_counts}

	# Last stay date per guest
	last_stays = frappe.db.sql(
		"""
		SELECT guest, MAX(check_in_datetime) as last_stay
		FROM `tabHotel Room Check In`
		WHERE status = 'Checked Out'
		GROUP BY guest
		""",
		as_dict=True,
	)
	last_stay_map = {row.guest: row.last_stay for row in last_stays}

	result = []
	for g in guests:
		name = cstr(g.get("name")).strip()
		ci = checkin_map.get(name)
		current_status = "In-House" if ci else None

		# Search filter (server-side simple filter)
		if search:
			q = search.lower()
			searchable = " ".join([
				cstr(g.get("hotel_guest_name")),
				cstr(g.get("phone_number")),
				cstr(g.get("email")),
				cstr(g.get("id_number")),
			]).lower()
			if q not in searchable:
				continue

		# Status filter
		if status:
			if status == "In-House" and not ci:
				continue
			if status != "In-House" and ci:
				continue

		stays = stay_map.get(name, 0)
		last_stay = last_stay_map.get(name)
		balance = flt(ci.get("total_outstanding_amount", 0)) if ci else 0

		result.append({
			"name": name,
			"hotel_guest_name": cstr(g.get("hotel_guest_name")),
			"guest_type": cstr(g.get("guest_type")),
			"phone_number": cstr(g.get("phone_number")),
			"email": cstr(g.get("email")),
			"nationality": cstr(g.get("nationality")),
			"loyalty_tier": cstr(g.get("loyalty_tier")) or "Base",
			"current_status": current_status or "Checked Out",
			"stays": stays,
			"last_stay": last_stay.strftime("%d %b %Y") if last_stay else "—",
			"balance": f"₦{balance:,.0f}" if balance else "₦0.00",
			"balance_raw": balance,
			"room_number": cstr(ci.get("room_number")) if ci else None,
		})

	total = len(result)
	start = (page - 1) * page_size
	paginated = result[start: start + page_size]

	return {
		"guests": paginated,
		"total": total,
		"page": page,
		"page_size": page_size,
	}


# ---------------------------------------------------------------------------
# Guest Stats (for header cards)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_guest_stats():
	"""Return stats for the Guest List header cards."""
	total_guests = frappe.db.count("Hotel Guest")

	in_house = frappe.db.count("Hotel Room Check In", {"status": "Checked In"})

	vip_count = frappe.db.count("Hotel Guest", {"loyalty_tier": ["in", ["VIP", "Platinum", "Gold"]]})

	outstanding_raw = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(total_outstanding_amount), 0) as total
		FROM `tabHotel Room Check In`
		WHERE status = 'Checked In' AND total_outstanding_amount > 0
		""",
		as_dict=True,
	)
	outstanding = flt(outstanding_raw[0].total) if outstanding_raw else 0

	def fmt_currency(amount):
		if amount >= 1_000_000:
			return f"₦{amount / 1_000_000:.1f}M"
		if amount >= 1_000:
			return f"₦{amount / 1_000:.0f}K"
		return f"₦{amount:,.0f}"

	return {
		"total_guests": total_guests,
		"in_house": in_house,
		"vip_count": vip_count,
		"outstanding": fmt_currency(outstanding),
	}


# ---------------------------------------------------------------------------
# Single Guest
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_guest(name):
	"""Return a single Hotel Guest document with computed stay data."""
	if not frappe.db.exists("Hotel Guest", name):
		frappe.throw(_("Guest not found: {0}").format(name), frappe.DoesNotExistError)

	doc = frappe.get_doc("Hotel Guest", name)

	# Active check-in
	active_ci = frappe.db.get_value(
		"Hotel Room Check In",
		{"guest": name, "status": "Checked In"},
		["name", "room_number", "room_type", "check_in_datetime",
		 "expected_check_out_datetime", "total_outstanding_amount"],
		as_dict=True,
	)

	# Stay history
	stays = frappe.get_all(
		"Hotel Room Check In",
		filters={"guest": name, "docstatus": ["!=", 2]},
		fields=[
			"name", "room_number", "room_type", "check_in_datetime",
			"expected_check_out_datetime", "actual_check_out_datetime",
			"status", "total_charges", "total_outstanding_amount", "number_of_nights",
			"reservation_source",
		],
		order_by="check_in_datetime desc",
		limit_page_length=100,
	)

	total_stays = len(stays)
	checkin_totals = _get_checkin_invoice_totals([s.get("name") for s in stays if s.get("name")])
	lifetime_spend = 0
	for stay in stays:
		checkin_name = stay.get("name")
		totals = checkin_totals.get(checkin_name, {})
		amount = flt(totals.get("amount"))
		outstanding = flt(totals.get("outstanding"))
		paid_amount = flt(totals.get("paid_amount"))

		if paid_amount > 0:
			lifetime_spend += paid_amount
		elif amount > 0:
			lifetime_spend += max(0, amount - outstanding)
		else:
			# Fallback for older stays without linked invoices.
			lifetime_spend += max(0, flt(stay.get("total_charges")) - flt(stay.get("total_outstanding_amount")))

	# Build timeline from stay history
	timeline = []
	for s in stays[:5]:
		ci_date = s.get("check_in_datetime")
		label = ci_date.strftime("%b %Y") if ci_date else "—"
		room = cstr(s.get("room_number"))
		rtype = cstr(s.get("room_type"))
		status = cstr(s.get("status"))
		desc = f"Stay • Room {room} • {rtype} • {status}"
		timeline.append({"date": label, "desc": desc, "color": "#3b82f6"})

	id_document_scan = _get_guest_id_document_url(doc)

	return {
		"name": doc.name,
		"hotel_guest_name": doc.hotel_guest_name,
		"guest_type": doc.guest_type,
		"title": doc.title,
		"gender": doc.gender,
		"phone_number": doc.phone_number,
		"email": doc.email,
		"nationality": doc.nationality,
		"date_of_birth": str(doc.date_of_birth) if doc.date_of_birth else "",
		"address": doc.address,
		"id_type": doc.id_type,
		"id_number": doc.id_number,
		"contact_number": doc.contact_number,
		"contact_person_name": doc.contact_person_name or "",
		"preference": doc.preference or "",
		"loyalty_tier": doc.loyalty_tier or "Base",
		"notes": doc.notes,
		"passport_photo": doc.passport_photo or "",
		"id_document_scan": id_document_scan,
		# computed
		"total_stays": total_stays,
		"lifetime_spend": lifetime_spend,
		"active_checkin": active_ci,
		"timeline": timeline,
		"current_status": "In-House" if active_ci else "Checked Out",
	}


def _get_checkin_invoice_totals(checkin_names):
	"""Return invoiced and outstanding totals keyed by Hotel Room Check In name."""
	totals = {}
	if not checkin_names:
		return totals

	for checkin_name in checkin_names:
		totals[checkin_name] = {"amount": 0, "outstanding": 0, "paid_amount": 0}

	placeholders = ", ".join(["%s"] * len(checkin_names))

	if _has_column("Sales Invoice", "custom_hotel_room_check_in"):
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
			if row.get("checkin") in totals:
				totals[row.get("checkin")]["amount"] += flt(row.get("amount"))
				totals[row.get("checkin")]["outstanding"] += flt(row.get("outstanding"))

	if _has_column("POS Invoice", "custom_hotel_room_check_in"):
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
			if row.get("checkin") in totals:
				totals[row.get("checkin")]["amount"] += flt(row.get("amount"))
				totals[row.get("checkin")]["outstanding"] += flt(row.get("outstanding"))

	if _has_column("Payment Entry", "custom_hotel_room_check_in"):
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
			if row.get("checkin") in totals:
				totals[row.get("checkin")]["paid_amount"] += flt(row.get("paid_amount"))

	return totals


def _has_column(doctype, column):
	try:
		return bool(frappe.db.has_column(doctype, column))
	except Exception:
		return False


def _get_guest_id_document_url(doc):
	"""Resolve the guest ID document from the field or its attached File record."""
	if doc.id_document_scan:
		return doc.id_document_scan

	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Hotel Guest",
			"attached_to_name": doc.name,
			"attached_to_field": "id_document_scan",
		},
		fields=["file_url"],
		order_by="creation desc",
		limit_page_length=1,
	)
	return files[0].file_url if files else ""


# ---------------------------------------------------------------------------
# Create Guest
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_guest(
	hotel_guest_name,
	guest_type="Individual",
	title=None,
	gender=None,
	phone_number=None,
	email=None,
	nationality=None,
	date_of_birth=None,
	address=None,
	id_type=None,
	id_number=None,
	contact_number=None,
	contact_person_name=None,
	preference=None,
	loyalty_tier=None,
	notes=None,
	id_document_scan=None,
):
	"""Create a new Hotel Guest document."""
	hotel_guest_name = cstr(hotel_guest_name).strip()
	if not hotel_guest_name:
		frappe.throw(_("Guest name is required."))

	if frappe.db.exists("Hotel Guest", hotel_guest_name):
		frappe.throw(_("A guest with the name '{0}' already exists.").format(hotel_guest_name))

	phone_number = validate_phone_number(phone_number, label=_("Phone Number"), required=True)
	contact_number = validate_phone_number(contact_number, label=_("Contact Person Number"))

	doc = frappe.new_doc("Hotel Guest")
	doc.hotel_guest_name = hotel_guest_name
	doc.guest_type = guest_type or "Individual"
	doc.title = title or ""
	doc.gender = gender or ""
	doc.phone_number = phone_number or ""
	doc.email = email or ""
	doc.nationality = nationality or ""
	doc.date_of_birth = date_of_birth or None
	doc.address = address or ""
	doc.id_type = id_type or ""
	doc.id_number = id_number or ""
	doc.contact_number = contact_number or ""
	doc.contact_person_name = contact_person_name or ""
	doc.preference = preference or ""
	doc.loyalty_tier = loyalty_tier or "Base"
	doc.notes = notes or ""
	doc.id_document_scan = id_document_scan or ""

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"name": doc.name, "hotel_guest_name": doc.hotel_guest_name}


# ---------------------------------------------------------------------------
# Update Guest
# ---------------------------------------------------------------------------

@frappe.whitelist()
def update_guest(
	name,
	hotel_guest_name=None,
	guest_type=None,
	title=None,
	gender=None,
	phone_number=None,
	email=None,
	nationality=None,
	date_of_birth=None,
	address=None,
	id_type=None,
	id_number=None,
	contact_number=None,
	contact_person_name=None,
	preference=None,
	loyalty_tier=None,
	notes=None,
	id_document_scan=None,
):
	"""Update an existing Hotel Guest document."""
	if not frappe.db.exists("Hotel Guest", name):
		frappe.throw(_("Guest not found: {0}").format(name), frappe.DoesNotExistError)

	doc = frappe.get_doc("Hotel Guest", name)

	if phone_number is not None:
		phone_number = validate_phone_number(phone_number, label=_("Phone Number"), required=True)
	if contact_number is not None:
		contact_number = validate_phone_number(contact_number, label=_("Contact Person Number"))

	# hotel_guest_name is handled separately below (rename logic)
	if guest_type is not None:
		doc.guest_type = guest_type
	if title is not None:
		doc.title = title
	if gender is not None:
		doc.gender = gender
	if phone_number is not None:
		doc.phone_number = phone_number
	if email is not None:
		doc.email = email
	if nationality is not None:
		doc.nationality = nationality
	if date_of_birth is not None:
		doc.date_of_birth = date_of_birth or None
	if address is not None:
		doc.address = address
	if id_type is not None:
		doc.id_type = id_type
	if id_number is not None:
		doc.id_number = id_number
	if contact_number is not None:
		doc.contact_number = contact_number
	if contact_person_name is not None:
		doc.contact_person_name = contact_person_name
	if preference is not None:
		doc.preference = preference
	if loyalty_tier is not None:
		doc.loyalty_tier = loyalty_tier
	if notes is not None:
		doc.notes = notes
	if id_document_scan is not None:
		doc.id_document_scan = id_document_scan

	# If the guest name is changing, handle rename separately to avoid
	# autoname conflict (name == hotel_guest_name in this doctype)
	new_name = cstr(hotel_guest_name).strip() if hotel_guest_name is not None else None
	name_is_changing = bool(new_name and new_name != name)

	if name_is_changing:
		# Save all other fields first, keeping the old hotel_guest_name so
		# the autoname constraint is satisfied
		doc.hotel_guest_name = name
		doc.save(ignore_permissions=True)
		# Now rename: this updates `name` and `hotel_guest_name` atomically
		frappe.rename_doc("Hotel Guest", name, new_name, force=True, merge=False)
		# Also update the linked Customer display name
		customer = frappe.db.get_value("Hotel Guest", new_name, "customer")
		if customer:
			try:
				frappe.db.set_value("Customer", customer, "customer_name", new_name)
			except Exception:
				pass
		frappe.db.commit()
		return get_guest(new_name)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return get_guest(doc.name)
