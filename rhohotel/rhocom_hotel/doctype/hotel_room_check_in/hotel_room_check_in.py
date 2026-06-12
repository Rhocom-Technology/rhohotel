# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint, utils
from frappe.model.document import Document
from datetime import datetime, time
from frappe.utils import get_datetime, now_datetime
from frappe.utils import nowdate, getdate, date_diff, fmt_money
from rhohotel.api import get_room_rate
from frappe.utils import flt
from datetime import datetime, time


class HotelRoomCheckIn(Document):
	def validate(self):
		self.validate_guest_phone_number()
		self.validate_rate_amount()
		self.validate_discount()
		self.validate_room()
		self.set_checkout_time()
		self.validate_dates()
		self.calculate_total_charges()
		self.validate_rate_and_session()

	def validate_guest_phone_number(self):
		if not self.is_new():
			return
		from rhohotel.rhocom_hotel.utils.phone import validate_phone_number

		self.contact_number = validate_phone_number(
			self.contact_number,
			label="Guest Phone Number",
			required=True,
		)

	def set_checkout_time(self):
		"""Set the time part of expected_check_out_datetime from Hotel Settings."""
		if self.expected_check_out_datetime and not self.late_checkout:
			hotel_settings = frappe.get_single("Hotel Settings")
			if hotel_settings.default_check_out_time:
				expected_checkout_date = get_datetime(self.expected_check_out_datetime).date()
				self.expected_check_out_datetime = get_datetime(
					f"{expected_checkout_date} {hotel_settings.default_check_out_time}"
				)

	def calculate_total_charges(self):
		"""Calculate total charges based on number of nights and rate amount."""
		if self.check_in_datetime and self.expected_check_out_datetime and self.rate_amount:
			check_in_dt = get_datetime(self.check_in_datetime)
			expected_checkout_dt = get_datetime(self.expected_check_out_datetime)
			number_of_nights = utils.date_diff(expected_checkout_dt.date(), check_in_dt.date())

			if self.discount:
				base_amount = number_of_nights * self.rate_amount

				if self.discount_type == "Percentage":
					self.total_charges = base_amount * (1 - (self.discount / 100))
				else:
					self.total_charges = base_amount - self.discount

				# Ensure total is not negative
				if self.total_charges < 0:
					self.total_charges = 0
			else:
				self.total_charges = number_of_nights * self.rate_amount

	def validate_rate_amount(self):
		if self.rate_amount <= 0:
			frappe.throw(_("Rate amount must be greater than zero"))

	def validate_rate_and_session(self):
		# Only require a tariff when rate_amount was not explicitly provided.
		if flt(self.rate_amount) > 0:
			return
		tariff = frappe.get_all("Hotel Room Tariff", filters={"room_type": self.room_type})
		if not tariff:
			frappe.throw(_("No valid tariff found for Room Type {0}").format(self.room_type))

	def set_rate_amount(self):
		tariff = frappe.get_all(
			"Hotel Room Tariff",
			filters={"room_type": self.room_type, "rate_type": self.rate_type, "is_active": 1},
			fields=["rate_amount"],
			limit=1,
		)

		if not tariff:
			tariff = frappe.get_all(
				"Hotel Room Tariff",
				filters={"room_type": self.room_type, "is_active": 1},
				fields=["rate_amount"],
				limit=1,
			)

		if tariff:
			self.rate_amount = tariff[0].rate_amount

	def validate_room(self):
		if not frappe.db.exists("Hotel Room", self.room_number):
			frappe.throw(_("Room {0} does not exist").format(self.room_number))

		# Allow explicit skip for internal flows (reservation check-in) that
		# have already validated availability and room state.
		if self.flags.get("skip_availability_check"):
			return

		room = frappe.get_doc("Hotel Room", self.room_number)

		# Only block rooms that are physically occupied right now.
		# "Reserved" means a future booking exists — the time-based availability
		# check below handles whether dates actually conflict.
		if room.status == "Occupied":
			frappe.throw(_("Room {0} is currently occupied. Please check out the current guest first.").format(self.room_number))

		from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available

		assert_room_available(
			self.room_number,
			self.check_in_datetime,
			self.expected_check_out_datetime,
			exclude_checkin=self.name if not self.is_new() else None,
		)

	def validate_dates(self):
		if get_datetime(self.check_in_datetime) > get_datetime(self.expected_check_out_datetime):
			frappe.throw(_("Check-in time cannot be after expected check-out time"))

	def on_submit(self):
		self.status = "Checked In"
		self.db_set("status", "Checked In")

		self.update_room_status("Occupied")
		self.update_room()
		self.make_sales_invoice()

		frappe.publish_realtime("rhohotel_front_desk_update")

	def on_cancel(self):
		self.status = "Cancelled"
		self.db_set("status", "Cancelled")

		self.update_room_status("Vacant")
		frappe.publish_realtime("rhohotel_front_desk_update")

	def on_load(self):
		pass

	def update_room_status(self, status):
		frappe.db.set_value("Hotel Room", self.room_number, "status", status)

	def update_room(self):
		room = frappe.get_doc("Hotel Room", self.room_number)
		room.current_guest = self.guest
		room.current_check_in = self.name
		room.save(ignore_permissions=True)

	def validate_discount(self):
		if self.discount_type == "None" or not self.discount_type:
			# If discount_type is "None" or not set, ensure discount is 0
			self.discount = 0
			return

		# Handle None discount value
		if self.discount is None:
			self.discount = 0

		if self.discount_type == "Percentage":
			if not (0 <= self.discount <= 100):
				frappe.throw(_("Discount percentage must be between 0 and 100"))
		elif self.discount_type in ["Amount", "Fixed Amount"]:
			if self.discount < 0:
				frappe.throw(_("Discount amount cannot be negative"))

	def make_sales_invoice(self):
		from rhohotel.rhocom_hotel.utils.billing_routing import resolve_payer

		# ------------------------------------------------------------------
		# Resolve payer via billing routing engine
		# ------------------------------------------------------------------
		# Prefer the canonical Hotel Reservation for routing; fall back to
		# the legacy Hotel Room Reservation.
		canonical_res_name = getattr(self, "canonical_reservation", None)
		payer_info = None

		if canonical_res_name and frappe.db.exists("Hotel Reservation", canonical_res_name):
			# For reservation-based check-ins, room billing is managed at the
			# reservation level via "Create Invoice". Never create a per-check-in
			# invoice here — room charges are covered by the reservation workflow
			# regardless of whether the reservation-level invoice exists yet.
			return

		# ------------------------------------------------------------------
		# Handle fallback (no canonical reservation linked) – use guest customer
		# ------------------------------------------------------------------
		if not payer_info:
			pass  # fall through to guest customer resolution below

		# ------------------------------------------------------------------
		# Determine customer from payer_info or fallback to guest customer
		# ------------------------------------------------------------------
		customer = None
		payer_type = "Guest"

		if payer_info:
			payer_type = payer_info.get("payer_type", "Guest")
			customer = payer_info.get("customer")

		# Internal types (House Use / Comp) – no billing invoice
		if payer_type == "Internal (Cost Centre)":
			return

		if not customer:
			customer = frappe.get_value("Hotel Guest", self.guest, "customer")

		if not customer:
			frappe.throw(
				_("Cannot create invoice: no customer linked to guest {0}.").format(self.guest)
			)

		# ------------------------------------------------------------------
		# Build and submit the Sales Invoice
		# ------------------------------------------------------------------
		room_doc = frappe.get_doc("Hotel Room", self.room_number)

		si = frappe.new_doc("Sales Invoice")
		si.customer = customer
		si.custom_hotel_room_check_in = self.name
		si.due_date = get_datetime(self.expected_check_out_datetime).date()
		si.posting_date = get_datetime(self.check_in_datetime).date()

		si.append(
			"items",
			{
				"item_code": room_doc.erpnext_item,
				"rate": self.rate_amount,
				"qty": self.number_of_nights,
				"amount": self.total_charges,
				"description": _("Room charge for {0} from {1} to {2}").format(
					self.room_number,
					get_datetime(self.check_in_datetime).date(),
					get_datetime(self.expected_check_out_datetime).date(),
				),
			},
		)

		si.set_taxes()

		if self.discount:
			if self.discount_type == "Percentage":
				si.additional_discount_percentage = self.discount
			else:
				si.discount_amount = self.discount

		# Never auto-allocate advances — payment must be received explicitly
		si.allocate_advances_automatically = 0

		si.insert(ignore_permissions=True)
		si.submit()


@frappe.whitelist()
def set_checkin_invoice_list(self):
	"""Fetch all linked invoices for a given check-in"""
	invoices = []

	# Get Sales Invoices
	sales_invoices = frappe.get_all(
		"Sales Invoice",
		filters={"custom_hotel_room_check_in": self.name},
		fields=["name", "grand_total", "outstanding_amount"],
	)

	for inv in sales_invoices:
		invoices.append(
			{
				"invoice_type": "Sales Invoice",
				"invoice": inv.name,
				"amount": inv.grand_total,
				"outstanding_amount": inv.outstanding_amount,
			}
		)

	# # Get POS Invoices
	pos_invoices = frappe.get_all(
		"POS Invoice",
		filters={"custom_hotel_room_check_in": self.name},
		fields=["name", "grand_total", "outstanding_amount"],
	)

	for inv in pos_invoices:
		invoices.append(
			{
				"invoice_type": "POS Invoice",
				"invoice": inv.name,
				"amount": inv.grand_total,
				"outstanding_amount": inv.outstanding_amount,
			}
		)

	return invoices


@frappe.whitelist()
def get_linked_documents(check_in):
	"""Get linked invoices, payments, sessions, and journal entries for a check-in."""

	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in)

	# -----------------------------
	# Get POS Invoices
	# -----------------------------
	pos_invoices = []
	if frappe.db.has_column("POS Invoice", "custom_hotel_room_check_in"):
		pos_invoices = frappe.get_all(
			"POS Invoice",
			filters={"custom_hotel_room_check_in": check_in_doc.name, "status": "Unpaid"},
			fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount", "pos_profile"],
		)

	for inv in pos_invoices:
		inv["invoice_type"] = "POS Invoice"

	# -----------------------------
	# Get Sales Invoices
	# -----------------------------
	sales_invoices = []
	if frappe.db.has_column("Sales Invoice", "custom_hotel_room_check_in"):
		sales_invoices = frappe.get_all(
			"Sales Invoice",
			filters={"custom_hotel_room_check_in": check_in_doc.name, "status": ["!=", "Cancelled"]},
			fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount"],
		)

	for inv in sales_invoices:
		inv["invoice_type"] = "Room Invoice"
		inv["pos_profile"] = None  # keep consistent structure

	# Merge invoices
	invoices = sales_invoices + pos_invoices

	# -----------------------------
	# Get Journal Entries
	# -----------------------------
	journal_entries = []
	if frappe.db.has_column("Journal Entry", "custom_hotel_room_check_in"):
		journal_entries = frappe.get_all(
			"Journal Entry",
			filters={"custom_hotel_room_check_in": check_in_doc.name},
			fields=["name", "voucher_type", "posting_date", "remark as remarks"],
		)

	# For totals we need debit/credit → lookup child table
	for je in journal_entries:
		accounts = frappe.get_all(
			"Journal Entry Account", filters={"parent": je["name"]}, fields=["debit", "credit", "party"]
		)

		total_debit = sum(a.debit or 0 for a in accounts)
		total_credit = sum(a.credit or 0 for a in accounts)
		party = None
		for a in accounts:
			if a.party:
				party = a.party
				break

		je["total_debit"] = total_debit
		je["total_credit"] = total_credit
		je["party"] = party

	# -----------------------------
	# Get Payment Entries
	# -----------------------------
	payments = []
	if frappe.db.has_column("Payment Entry", "custom_hotel_room_check_in"):
		payments = frappe.get_all(
			"Payment Entry",
			filters={"custom_hotel_room_check_in": check_in_doc.name, "payment_type": "Receive", "docstatus": 1},
			fields=["name", "party", "posting_date", "paid_amount"],
		)

	# -----------------------------
	# Get Payment Sessions
	# -----------------------------
	payment_sessions = []
	if frappe.db.exists("DocType", "Payment Session") and frappe.db.has_column(
		"Payment Session", "hotel_room_check_in"
	):
		payment_sessions = frappe.get_all(
			"Payment Session",
			filters={"hotel_room_check_in": check_in_doc.name, "status": "Paid"},
			fields=["name", "posting_date", "total_amount"],
		)

	# -----------------------------
	# Totals
	# -----------------------------
	total_outstanding_amount = sum(inv.outstanding_amount or 0 for inv in invoices)
	total_charges = sum(inv.grand_total or 0 for inv in invoices)

	# -----------------------------
	# Guest Email
	# -----------------------------
	guest_doc = frappe.get_doc("Hotel Guest", check_in_doc.guest)
	guest_email = guest_doc.email

	# -----------------------------
	# Final Return
	# -----------------------------
	return {
		"invoices": invoices,
		"journal_entries": journal_entries,
		"payments": payments,
		"payment_sessions": payment_sessions,
		"total_outstanding_amount": total_outstanding_amount,
		"total_charges": total_charges,
		"guest_email": guest_email,
	}


@frappe.whitelist()
def get_outstanding_for_check_in(check_in):
	"""Return only the outstanding amount for faster UI checks."""
	data = get_linked_documents(check_in)
	return {"outstanding": data.get("total_outstanding_amount", 0)}


@frappe.whitelist()
def make_check_out(source_name, target_doc=None):
	# Block check-out for non-managers if outstanding invoices exist
	if "Hotel Manager" not in frappe.get_roles(frappe.session.user):
		data = get_linked_documents(source_name)
		outstanding = data.get("total_outstanding_amount", 0)

		if outstanding > 0:
			frappe.throw(
				_(
					"Cannot check out because there are outstanding invoices totaling {0}. Please settle them first."
				).format(frappe.format_value(outstanding))
			)

	def get_mapped_doc():
		check_in = frappe.get_doc("Hotel Room Check In", source_name)
		check_out = frappe.new_doc("Hotel Room Check Out")
		check_out.check_in = check_in.name
		check_out.guest = check_in.guest
		check_out.room_number = check_in.room_number
		check_out.check_in_datetime = check_in.check_in_datetime
		check_out.check_out_datetime = now_datetime()
		check_out.insert(ignore_permissions=True)
		return check_out

	doc = get_mapped_doc()
	return doc


@frappe.whitelist()
def apply_discount(check_in_name, discount_amount, reason=None, source_invoice=None):
	"""
	Apply a discount to the Hotel Room Check In document by creating a credit note.
	If source_invoice is provided, a background reconciliation job applies the
	credit note against that invoice in Accounts Receivable.
	"""
	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)

	customer = frappe.get_value("Hotel Guest", check_in_doc.guest, "customer")
	if not customer:
		frappe.throw(_("No customer linked to guest {0}").format(check_in_doc.guest))

	room_doc = frappe.get_doc("Hotel Room", check_in_doc.room_number)

	credit_note_data = {
		"doctype": "Sales Invoice",
		"customer": customer,
		"is_return": 1,
		"update_stock": 0,
		"custom_hotel_room_check_in": check_in_doc.name,
		"items": [{"item_code": room_doc.erpnext_item, "qty": -1, "rate": discount_amount}],
		"posting_date": frappe.utils.today(),
		"remarks": reason or f"Discount applied to Check In {check_in_doc.name}",
	}

	if source_invoice:
		credit_note_data["return_against"] = source_invoice
		# Keep the receivable account aligned so the reconciliation Journal Entry
		# can apply the credit note against the selected invoice.
		src_fields = frappe.db.get_value(
			"Sales Invoice", source_invoice, ["debit_to", "company"], as_dict=1
		)
		if src_fields:
			if src_fields.debit_to:
				credit_note_data["debit_to"] = src_fields.debit_to
			if src_fields.company:
				credit_note_data["company"] = src_fields.company

	credit_note = frappe.get_doc(credit_note_data)
	credit_note.flags.ignore_permissions = True
	credit_note.flags.ignore_mandatory = True
	credit_note.flags.ignore_links = True
	credit_note.insert()
	credit_note.submit()

	if source_invoice:
		from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import enqueue_credit_note_reconciliation

		enqueue_credit_note_reconciliation(
			credit_note.name,
			source_invoice=source_invoice,
			check_in=check_in_doc.name,
		)

	try:
		from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

		sync_checkin_folio_totals(check_in_doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after discount")

	return {"status": "success", "credit_note": credit_note.name}


def _validate_room_voucher_for_checkin(complimentary, check_in_doc):
	if complimentary.complimentary_type != "Room Voucher":
		frappe.throw(_("Complimentary {0} is not a Room Voucher.").format(complimentary.name))

	if complimentary.department != "Front Desk":
		frappe.throw(_("Room Voucher {0} must be routed to Front Desk.").format(complimentary.name))

	if complimentary.status not in ("Approved", "In Progress"):
		frappe.throw(_("Room Voucher {0} is not approved for redemption.").format(complimentary.name))

	if complimentary.expiry_date and getdate(complimentary.expiry_date) < getdate(nowdate()):
		frappe.throw(_("Room Voucher {0} has expired.").format(complimentary.name))

	remaining_value = flt(complimentary.get("remaining_value")) if complimentary.get("remaining_value") is not None else flt(complimentary.value) - flt(complimentary.get("redeemed_amount"))
	if remaining_value <= 0:
		frappe.throw(_("Room Voucher {0} has no redeemable value.").format(complimentary.name))

	if complimentary.check_in and complimentary.check_in != check_in_doc.name:
		frappe.throw(_("Room Voucher {0} belongs to another check-in.").format(complimentary.name))

	if complimentary.room and complimentary.room != check_in_doc.room_number:
		frappe.throw(_("Room Voucher {0} belongs to room {1}.").format(complimentary.name, complimentary.room))

	if not complimentary.check_in and not complimentary.room:
		guest_name = frappe.db.get_value("Hotel Guest", check_in_doc.guest, "hotel_guest_name") or check_in_doc.guest
		if complimentary.guest and complimentary.guest.strip().lower() not in {guest_name.lower(), str(check_in_doc.guest).lower()}:
			frappe.throw(_("Room Voucher {0} belongs to another guest.").format(complimentary.name))


@frappe.whitelist()
def apply_room_voucher(check_in_name, complimentary_name, source_invoice):
	"""Redeem an approved Room Voucher by creating a credit note on a room invoice."""
	if not complimentary_name:
		frappe.throw(_("Select a Room Voucher."))
	if not source_invoice:
		frappe.throw(_("Select a room invoice for this voucher."))

	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
	if not frappe.db.exists("Hotel Complimentary", complimentary_name):
		frappe.throw(_("Room Voucher {0} not found.").format(complimentary_name))

	complimentary = frappe.get_doc("Hotel Complimentary", complimentary_name)
	_validate_room_voucher_for_checkin(complimentary, check_in_doc)

	if not frappe.db.exists("Sales Invoice", source_invoice):
		frappe.throw(_("Sales Invoice {0} not found.").format(source_invoice))

	invoice = frappe.get_doc("Sales Invoice", source_invoice)
	if int(invoice.docstatus or 0) != 1 or int(invoice.is_return or 0):
		frappe.throw(_("Select a submitted, non-return room invoice."))
	if flt(invoice.outstanding_amount) <= 0:
		frappe.throw(_("Selected invoice has no outstanding balance."))
	if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
		invoice_source = (invoice.get("custom_invoice_source") or "").strip().lower()
		if invoice_source in {"restaurant", "pos invoice"}:
			frappe.throw(_("Room Vouchers can only be applied to room charge invoices."))

	remaining_value = flt(complimentary.get("remaining_value")) if complimentary.get("remaining_value") is not None else flt(complimentary.value) - flt(complimentary.get("redeemed_amount"))
	voucher_amount = min(remaining_value, flt(invoice.outstanding_amount))
	if voucher_amount <= 0:
		frappe.throw(_("Room Voucher {0} cannot be applied to this invoice.").format(complimentary.name))

	reason = _("Room Voucher {0} redeemed against {1}").format(complimentary.name, source_invoice)
	result = apply_discount(
		check_in_name=check_in_doc.name,
		discount_amount=voucher_amount,
		reason=reason,
		source_invoice=source_invoice,
	)

	credit_note = result.get("credit_note")
	from rhohotel.rhocom_hotel.api.complimentary import redeem_complimentary_value

	redemption = redeem_complimentary_value(
		complimentary_name=complimentary.name,
		applied_amount=voucher_amount,
		transaction_reference=_("Credit Note {0} against Sales Invoice {1}").format(credit_note, source_invoice),
		department="Front Desk",
	)

	frappe.db.commit()
	return {
		"status": "success",
		"credit_note": credit_note,
		"source_invoice": source_invoice,
		"complimentary_name": complimentary.name,
		"applied_amount": voucher_amount,
		"remaining_value": redemption.get("remaining_value"),
		"voucher_status": redemption.get("status"),
	}


def _get_oldest_open_checkin_charge_invoice(check_in_name):
	return frappe.db.get_value(
		"Sales Invoice",
		{
			"custom_hotel_room_check_in": check_in_name,
			"docstatus": 1,
			"is_return": 0,
			"outstanding_amount": [">", 0],
		},
		"name",
		order_by="posting_date asc, creation asc",
	)


@frappe.whitelist()
def make_refund(source_name, target_doc=None):
	def get_mapped_doc():
		# Get total payments made against the check-in
		payments = frappe.get_all(
			"Payment Entry",
			filters={"custom_hotel_room_check_in": source_name},
			fields=["sum(paid_amount) as total_paid"],
		)
		total_paid = payments[0].total_paid if payments and payments[0].total_paid else 0

		check_in = frappe.get_doc("Hotel Room Check In", source_name)
		refund = frappe.new_doc("Hotel Refund")
		refund.guest = check_in.guest
		refund.check_in = check_in.name
		refund.refund_amount = total_paid
		refund.reason = f"Refund for Check In {check_in.name}"
		return refund

	doc = get_mapped_doc()
	return doc


@frappe.whitelist()
def extend_stay(check_in_name, number_of_nights):
	"""
	Extends a guest's stay by updating the expected_check_out_datetime
	and creating a new Sales Invoice for the extension period.
	"""
	number_of_nights = int(number_of_nights)
	if number_of_nights <= 0:
		frappe.throw(_("Number of nights must be a positive number."))

	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
	current_checkout_dt = get_datetime(check_in_doc.expected_check_out_datetime)
	new_checkout_dt = utils.add_to_date(current_checkout_dt, days=number_of_nights)
	new_expected_checkout = new_checkout_dt.strftime("%Y-%m-%d %H:%M:%S")

	# Check for conflicts during the extension period
	from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available
	assert_room_available(
		check_in_doc.room_number,
		current_checkout_dt,
		new_checkout_dt,
		exclude_checkin=check_in_doc.name,
		exclude_canonical=getattr(check_in_doc, "canonical_reservation", None) or getattr(check_in_doc, "reservation", None),
	)

	# Create a new Sales Invoice for the extension
	extension_amount = number_of_nights * check_in_doc.rate_amount
	room_doc = frappe.get_doc("Hotel Room", check_in_doc.room_number)
	customer = frappe.get_value("Hotel Guest", check_in_doc.guest, "customer")

	si = frappe.new_doc("Sales Invoice")
	si.customer = customer
	si.custom_hotel_room_check_in = check_in_doc.name
	si.due_date = new_checkout_dt.date()
	si.posting_date = now_datetime().date()
	si.append(
		"items",
		{
			"item_code": room_doc.erpnext_item,
			"rate": check_in_doc.rate_amount,
			"qty": number_of_nights,
			"amount": extension_amount,
			"description": _("Stay extension for {0} from {1} to {2}").format(
				check_in_doc.room_number,
				current_checkout_dt.strftime("%Y-%m-%d"),
				new_checkout_dt.strftime("%Y-%m-%d"),
			),
		},
	)
	si.set_taxes()
	si.insert(ignore_permissions=True)
	si.submit()

	# Add a record to the extensions child table
	check_in_doc.append(
		"extensions",
		{
			"extension_date": now_datetime(),
			"previous_checkout_date": current_checkout_dt,
			"new_checkout_date": new_checkout_dt,
			"number_of_nights": number_of_nights,
			"extension_invoice": si.name,
			"amount": extension_amount,
		},
	)

	# Update the check-in document's checkout time and save it to persist the extension record
	check_in_doc.expected_check_out_datetime = new_expected_checkout
	check_in_doc.save(ignore_permissions=True)

	# Add a comment to the check-in document for history
	check_in_doc.add_comment(
		"Comment",
		text=_("Stay extended to {0}. New invoice {1} created for {2}.").format(
			new_expected_checkout, si.name, frappe.utils.fmt_money(extension_amount)
		),
	)

	frappe.msgprint(_("Stay extended successfully. New invoice {0} created.").format(si.name))
	return {"sales_invoice": si.name}


@frappe.whitelist()
def reduce_stay(check_in_name, new_checkout):
	"""
	Reduce the expected check-out datetime for a guest.
	Rules:
	- New checkout must be earlier than current expected checkout.
	- New checkout cannot be in the past.
	- If new checkout is today, only allowed if current time <= default checkout time.
	"""

	from frappe.utils import now_datetime, get_datetime, getdate, date_diff, flt
	from datetime import datetime

	doc = frappe.get_doc("Hotel Room Check In", check_in_name)

	# Convert incoming datetime string
	new_dt = get_datetime(new_checkout)
	current_dt = get_datetime(doc.expected_check_out_datetime)
	now_dt = now_datetime()

	# --- 1. Must be earlier than current expected checkout ---
	if not (new_dt < current_dt):
		frappe.throw(
			f"New checkout must be earlier than current expected checkout: {frappe.format_value(current_dt)}"
		)

	# --- 2. Cannot be in the past ---
	if new_dt < now_dt:
		frappe.throw("New checkout cannot be in the past.")

	# --- 3. Special rule for reducing to today ---
	today = getdate(now_dt)
	new_date = getdate(new_dt)

	# Get default checkout time from Hotel Settings
	settings = frappe.get_doc("Hotel Settings")
	default_time = settings.default_check_out_time  # string "HH:mm:ss"

	# Build "today at default checkout time"
	today_default_dt = datetime.strptime(f"{today} {default_time}", "%Y-%m-%d %H:%M:%S")

	if new_date == today:
		if now_dt > today_default_dt:
			frappe.throw(
				f"Reducing stay to today is not allowed because default checkout time "
				f"({frappe.format_value(today_default_dt)}) has already passed."
			)
		if new_dt > today_default_dt:
			frappe.throw(
				f"For today, new checkout must not be later than the default checkout time "
				f"({frappe.format_value(today_default_dt)})."
			)

	# --- Everything ok → update document ---
	# Recalculate number of nights
	new_nights = date_diff(getdate(new_dt), getdate(doc.check_in_datetime))
	if new_nights < 1:
		new_nights = 1

	# --- Calculate difference and create credit note if reducing stay ---
	diff_nights = doc.number_of_nights - new_nights
	if diff_nights > 0:
		credit_amount = flt(doc.rate_amount) * diff_nights

		customer = frappe.get_value("Hotel Guest", doc.guest, "customer")
		if not customer:
			frappe.throw(_("No customer linked to guest {0}").format(doc.guest))

		room_doc = frappe.get_doc("Hotel Room", doc.room_number)
		source_invoice = _get_oldest_open_checkin_charge_invoice(doc.name)

		# Create credit note (Sales Invoice with is_return = 1)
		credit_note_data = {
				"doctype": "Sales Invoice",
				"customer": customer,
				"is_return": 1,
				"update_stock": 0,
				"check_in": doc.name,
				"custom_hotel_room_check_in": doc.name,
				"items": [
					{
						"item_code": room_doc.erpnext_item,
						"qty": -diff_nights,
						"rate": doc.rate_amount,
						"amount": credit_amount,
					}
				],
				"posting_date": frappe.utils.today(),
				"remarks": f"Credit note for reduced stay ({diff_nights} nights)",
		}
		if source_invoice:
			credit_note_data["return_against"] = source_invoice
			src_fields = frappe.db.get_value(
				"Sales Invoice", source_invoice, ["debit_to", "company"], as_dict=1
			)
			if src_fields:
				if src_fields.debit_to:
					credit_note_data["debit_to"] = src_fields.debit_to
				if src_fields.company:
					credit_note_data["company"] = src_fields.company

		credit_note = frappe.get_doc(credit_note_data)
		credit_note.flags.ignore_permissions = True
		credit_note.flags.ignore_mandatory = True
		credit_note.flags.ignore_links = True
		credit_note.insert()
		credit_note.submit()
		if source_invoice:
			from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import enqueue_credit_note_reconciliation

			enqueue_credit_note_reconciliation(
				credit_note.name,
				source_invoice=source_invoice,
				check_in=doc.name,
			)

	# Update check-in document
	doc.expected_check_out_datetime = new_dt
	doc.number_of_nights = new_nights
	doc.save()
	frappe.db.commit()

	return {
		"status": "success",
		"new_checkout": new_dt,
		"new_nights": new_nights,
		"credit_nights": diff_nights if diff_nights > 0 else 0,
		"credit_amount": credit_amount if diff_nights > 0 else 0,
	}


@frappe.whitelist()
def adjust_stay(check_in_name, new_checkout, discount_type, new_discount=None, source_invoice=None):
	from frappe.utils import now_datetime, get_datetime, getdate, date_diff, flt

	# Safe-get doc (avoid missing permissions)
	doc = frappe.get_doc("Hotel Room Check In", check_in_name)
	if not frappe.has_permission("Hotel Room Check In", "write", doc=doc):
		frappe.throw(_("Not permitted to adjust this check-in."), frappe.PermissionError)

	# Convert datetime
	new_dt = get_datetime(new_checkout)
	current_dt = get_datetime(doc.expected_check_out_datetime)
	checkin_dt = get_datetime(doc.check_in_datetime)
	now_dt = now_datetime()

	# === VALIDATIONS ===
	if new_dt == current_dt:
		frappe.throw("New checkout is the same as current checkout. No adjustment needed.")
	if new_dt <= checkin_dt:
		frappe.throw("New checkout must be after check-in date.")
	if new_dt < now_dt:
		frappe.throw("New checkout cannot be in the past.")

	adjustment_type = "Extension" if new_dt > current_dt else "Reduction"

	# Special rule for reduction
	if adjustment_type == "Reduction":
		settings = frappe.get_cached_doc("Hotel Settings")
		default_time = settings.default_check_out_time or "12:00:00"

		today = getdate(now_dt)
		new_date = getdate(new_dt)
		today_default_dt = get_datetime(f"{today} {default_time}")

		if new_date == today:
			if now_dt > today_default_dt:
				frappe.throw(
					f"Cannot reduce stay to today; default checkout time ({default_time}) has passed."
				)
			if new_dt > today_default_dt:
				frappe.throw(f"New checkout must be on or before default checkout time ({default_time}).")

	# Night calculations
	new_nights = date_diff(getdate(new_dt), getdate(doc.check_in_datetime)) or 1
	current_nights = doc.number_of_nights or 1
	diff_nights = abs(current_nights - new_nights)
	if diff_nights == 0:
		frappe.throw("The new checkout results in the same number of nights.")

	# === Making sure no reservations or check-ins conflict with the new dates ===
	if adjustment_type == "Extension":
		from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available
		assert_room_available(
			doc.room_number,
			current_dt,
			new_dt,
			exclude_checkin=doc.name,
			exclude_canonical=getattr(doc, "canonical_reservation", None) or getattr(doc, "reservation", None),
		)

	amount = flt(doc.rate_amount) * diff_nights
	adjustment_invoice_name = None

	customer = frappe.get_value("Hotel Guest", doc.guest, "customer")
	if not customer:
		frappe.throw(_("No customer linked to guest {0}").format(doc.guest))

	room_doc = frappe.get_doc("Hotel Room", doc.room_number)
	item_code = room_doc.erpnext_item or doc.room_number
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(_("No valid ERPNext Item linked to room {0}.").format(doc.room_number))

	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)
	if not company:
		frappe.throw(_("No default Company configured. Cannot create stay adjustment invoice."))

	default_income = frappe.db.get_value("Company", company, "default_income_account")
	if not default_income:
		frappe.throw(_("No default income account set for Company {0}.").format(company))

	source_invoice_doc = None
	if source_invoice:
		source_invoice_doc = frappe.get_doc("Sales Invoice", source_invoice)
		if source_invoice_doc.docstatus != 1:
			frappe.throw(_("Source invoice {0} must be submitted.").format(source_invoice))
		if source_invoice_doc.is_return:
			frappe.throw(_("Source invoice {0} is already a return invoice.").format(source_invoice))
		if source_invoice_doc.custom_hotel_room_check_in != doc.name:
			frappe.throw(_("Source invoice {0} is not linked to this check-in.").format(source_invoice))

	try:
		# === EXTENSION INVOICE ===
		if adjustment_type == "Extension":
			invoice = frappe.get_doc(
				{
					"doctype": "Sales Invoice",
					"customer": customer,
					"company": company,
					"is_return": 0,
					"update_stock": 0,
					"custom_hotel_room_check_in": doc.name,
					"posting_date": frappe.utils.today(),
					"due_date": getdate(new_dt),
					"remarks": f"Stay extension for Check In {doc.name} ({diff_nights} night(s))",
					"items": [
						{
							"item_code": item_code,
							"qty": diff_nights,
							"rate": doc.rate_amount,
							"amount": diff_nights * doc.rate_amount,
							"income_account": default_income,
							"description": _("Stay extension for room {0}: {1} additional night(s).").format(
								doc.room_number, diff_nights
							),
						}
					],
				}
			)

			if new_discount and flt(new_discount) > 0:
				if discount_type == "Percentage":
					if flt(new_discount) >= 100:
						frappe.throw("Discount percentage cannot be 100% or more.")
					invoice.additional_discount_percentage = flt(new_discount)
				elif discount_type == "Fixed Amount":
					invoice.discount_amount = flt(new_discount)

			if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
				invoice.custom_invoice_source = "Stay Adjustment"
			invoice.set_taxes()
			invoice.insert(ignore_permissions=True)
			invoice.submit()
			adjustment_invoice_name = invoice.name

		# === REDUCTION CREDIT NOTE ===
		else:
			credit_note_data = {
				"doctype": "Sales Invoice",
				"customer": customer,
				"company": company,
				"is_return": 1,
				"update_stock": 0,
				"custom_hotel_room_check_in": doc.name,
				"posting_date": frappe.utils.today(),
				"due_date": frappe.utils.today(),
				"remarks": f"Stay reduction credit for Check In {doc.name} ({diff_nights} night(s))",
				"items": [
					{
						"item_code": item_code,
						"qty": -diff_nights,
						"rate": doc.rate_amount,
						"income_account": default_income,
						"description": _("Stay reduction credit for room {0}: {1} reduced night(s).").format(
							doc.room_number, diff_nights
						),
					}
				],
			}

			if source_invoice_doc:
				credit_note_data["return_against"] = source_invoice
				src_fields = frappe.db.get_value(
					"Sales Invoice", source_invoice, ["debit_to", "company"], as_dict=1
				)
				if src_fields:
					if src_fields.debit_to:
						credit_note_data["debit_to"] = src_fields.debit_to
					if src_fields.company:
						credit_note_data["company"] = src_fields.company

			credit_note = frappe.get_doc(credit_note_data)

			if new_discount and flt(new_discount) > 0:
				if discount_type == "Percentage":
					if flt(new_discount) >= 100:
						frappe.throw("Discount percentage cannot be 100% or more.")
					credit_note.additional_discount_percentage = flt(new_discount)
				elif discount_type == "Fixed Amount":
					credit_note.discount_amount = flt(new_discount)

			if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
				credit_note.custom_invoice_source = "Stay Adjustment"
			credit_note.set_taxes()
			credit_note.insert(ignore_permissions=True)
			credit_note.submit()
			adjustment_invoice_name = credit_note.name

			if source_invoice:
				from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import enqueue_credit_note_reconciliation

				enqueue_credit_note_reconciliation(
					credit_note.name,
					source_invoice=source_invoice,
					check_in=doc.name,
				)

		# === Update Check-In Document ===
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_validate_update_after_submit = True
		doc.flags.skip_availability_check = True

		doc.append(
			"adjustments",
			{
				"adjustment_date": now_datetime(),
				"adjustment_type": adjustment_type,
				"previous_checkout_datetime": doc.expected_check_out_datetime,
				"new_checkout_datetime": new_dt,
				"previous_number_of_nights": current_nights,
				"new_number_of_nights": new_nights,
				"nights_difference": diff_nights if adjustment_type == "Extension" else -diff_nights,
				"adjustment_invoice": adjustment_invoice_name,
				"amount": amount,
				"workflow_state": "Completed",
			},
		)

		doc.expected_check_out_datetime = new_dt
		doc.number_of_nights = new_nights
		doc.save(ignore_permissions=True)

		try:
			from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

			sync_checkin_folio_totals(doc.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after stay adjustment")

		frappe.db.commit()

		return {
			"status": "success",
			"adjustment_type": adjustment_type,
			"adjustment_invoice": adjustment_invoice_name,
			"new_checkout": new_dt,
			"new_nights": new_nights,
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "adjust_stay")
		frappe.throw(f"Failed to process stay adjustment: {str(e)}")


@frappe.whitelist()
def transfer_room(check_in_name, new_room_number, note=None):
	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in_name)
	if not frappe.has_permission("Hotel Room Check In", "write", doc=check_in_doc):
		frappe.throw(_("Not permitted to transfer this check-in."), frappe.PermissionError)

	# ensure new room exists
	if not frappe.db.exists("Hotel Room", new_room_number):
		frappe.throw(_("New room {0} does not exist.").format(new_room_number))
	if check_in_doc.room_number == new_room_number:
		frappe.throw(_("Guest is already in Room {0}.").format(new_room_number))

	new_room_doc = frappe.get_doc("Hotel Room", new_room_number)
	if new_room_doc.status != "Vacant":
		frappe.throw(_("New room {0} is not vacant.").format(new_room_number))

	# Ensure check-in is active
	if check_in_doc.status != "Checked In":
		frappe.throw(_("Only active check-ins can be transferred."))

	# Validate via all 3 booking surfaces (exclude the current check-in which occupies
	# the source room — the target room must be conflict-free for the remaining stay)
	from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available
	assert_room_available(
		new_room_number,
		check_in_doc.check_in_datetime,
		check_in_doc.expected_check_out_datetime,
	)

	try:
		# Free the old room
		old_room_doc = frappe.get_doc("Hotel Room", check_in_doc.room_number)
		old_room_number = check_in_doc.room_number
		old_rate = flt(check_in_doc.rate_amount)

		old_room_doc.db_set("current_check_in", None)
		old_room_doc.db_set("current_guest", None)
		old_room_doc.db_set("status", "Vacant")
		old_room_doc.add_comment(
			"Comment",
			text=_("Guest transferred out to {0}. {1}").format(new_room_number, note or ""),
		)
		old_room_doc.save(ignore_permissions=True)

		# Update the new room details
		new_room_doc.status = "Occupied"
		new_room_doc.current_guest = check_in_doc.guest
		new_room_doc.current_check_in = check_in_doc.name
		new_room_doc.save(ignore_permissions=True)

		# get new room type rate
		new_rate_data = get_room_rate(new_room_doc.room_type, "", str(getdate(check_in_doc.check_in_datetime)))
		new_rate = flt(new_rate_data)
		if new_rate <= 0:
			frappe.throw(_("No valid rate found for Room Type {0}").format(new_room_doc.room_type))

		# Update check-in document (fixed: also update room_type)
		check_in_doc.flags.ignore_permissions = True
		check_in_doc.flags.ignore_mandatory = True
		check_in_doc.flags.ignore_validate_update_after_submit = True
		check_in_doc.flags.skip_availability_check = True
		check_in_doc.room_number = new_room_number
		check_in_doc.room_type = new_room_doc.room_type
		check_in_doc.rate_amount = new_rate
		check_in_doc.add_comment(
			"Comment",
			text=_("Guest transferred from {0} to {1}. {2}").format(old_room_number, new_room_number, note or ""),
		)

		# Log transfer history
		check_in_doc.append(
			"transfer_history",
			{
				"transfer_datetime": now_datetime(),
				"from_room": old_room_number,
				"to_room": new_room_number,
				"reason": note,
				"user": frappe.session.user,
			},
		)
		check_in_doc.save(ignore_permissions=True)

		# Create rate-difference invoice for remaining nights
		rate_invoice = adjust_room_rate(
			check_in_doc,
			old_room_number,
			new_room_number,
			old_rate,
			note,
			new_rate=new_rate,
		)

		try:
			from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

			sync_checkin_folio_totals(check_in_doc.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after room transfer")

		frappe.db.commit()
		frappe.publish_realtime("rhohotel_front_desk_update")

		return {
			"success": True,
			"message": _("Guest transferred successfully to Room {0}").format(new_room_number),
			"rate_invoice": rate_invoice,
		}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "transfer_room")
		frappe.throw(_("Failed to transfer room: {0}").format(str(e)))


def adjust_room_rate(check_in_doc, old_room_number, new_room_number, old_rate, note=None, new_rate=None):
	"""Create a rate-difference invoice (positive or negative) for the remaining nights after a room transfer.

	- new room rate > old rate  → positive Sales Invoice (guest owes the difference)
	- new room rate < old rate  → credit note / return SI (guest is owed the difference)
	- same rate                 → no invoice
	"""

	new_room = frappe.get_doc("Hotel Room", new_room_number)

	# Prefer the rate already applied to the check-in during transfer. Recomputing
	# here can silently return a generic/default rate and skip the adjustment.
	today = getdate(nowdate())
	new_rate = flt(new_rate if new_rate is not None else check_in_doc.rate_amount)
	if new_rate <= 0:
		# fallback: active tariff without day-type filter
		new_rate = flt(get_room_rate(new_room.room_type, "", str(today)))
	if new_rate <= 0:
		new_rate = flt(
			frappe.db.get_value(
				"Hotel Room Tariff",
				{"room_type": new_room.room_type, "is_active": 1},
				"rate_amount",
			)
		)

	# Remaining nights: from today (transfer day) to expected checkout.
	# Same-day transfers still consume the new room for the current stay day, so
	# apply one billable night/day when there is a rate difference.
	expected_checkout = getdate(check_in_doc.expected_check_out_datetime)
	remaining_nights = max(date_diff(expected_checkout, today), 1)
	nightly_diff = new_rate - flt(old_rate)
	total_diff = nightly_diff * remaining_nights

	if total_diff == 0:
		# Identical rate – nothing to invoice
		check_in_doc.add_comment(
			"Comment",
			text=_("Room transfer to {0}: no rate change ({1}/night). No adjustment invoice needed.").format(
				new_room_number, fmt_money(new_rate, 2)
			),
		)
		return None

	# Resolve customer
	customer = frappe.db.get_value("Hotel Guest", check_in_doc.guest, "customer")
	if not customer:
		frappe.throw(_("No customer linked to guest {0}").format(check_in_doc.guest))

	# Resolve company with proper fallback
	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)
	if not company:
		frappe.throw(_("No default Company configured. Cannot create rate-difference invoice."))

	default_income = frappe.db.get_value("Company", company, "default_income_account")
	if not default_income:
		frappe.throw(_("No default income account set for Company {0}.").format(company))

	# Resolve item code (try new room first, fall back to old room)
	item_code = new_room.erpnext_item
	if not item_code:
		item_code = frappe.db.get_value("Hotel Room", old_room_number, "erpnext_item")
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(
			_("No valid ERPNext item linked to rooms {0} or {1}. Cannot create invoice.").format(
				old_room_number, new_room_number
			)
		)

	is_upgrade = total_diff > 0
	invoice_title = "Room Transfer Upgrade" if is_upgrade else "Room Transfer Downgrade"
	# qty is positive for upgrade (charge), negative for downgrade (credit note)
	qty = remaining_nights if is_upgrade else -remaining_nights

	invoice = frappe.new_doc("Sales Invoice")
	invoice.customer = customer
	invoice.company = company
	invoice.posting_date = nowdate()
	invoice.due_date = nowdate()
	invoice.is_return = 0 if is_upgrade else 1
	invoice.update_stock = 0
	invoice.custom_hotel_room_check_in = check_in_doc.name
	source_invoice = None
	if not is_upgrade:
		source_invoice = frappe.db.get_value(
			"Sales Invoice",
			{
				"custom_hotel_room_check_in": check_in_doc.name,
				"docstatus": 1,
				"is_return": 0,
				"outstanding_amount": [">", 0],
			},
			"name",
			order_by="posting_date asc, creation asc",
		)
		if source_invoice:
			invoice.return_against = source_invoice
			src_fields = frappe.db.get_value(
				"Sales Invoice", source_invoice, ["debit_to", "company"], as_dict=1
			)
			if src_fields:
				if src_fields.debit_to:
					invoice.debit_to = src_fields.debit_to
				if src_fields.company:
					invoice.company = src_fields.company
	if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
		invoice.custom_invoice_source = "Room Transfer"
	invoice.remarks = _(
		"Room transfer from {0} to {1}: rate adjustment for {2} remaining night(s)."
	).format(old_room_number, new_room_number, remaining_nights)

	invoice.append(
		"items",
		{
			"item_code": item_code,
			"item_name": invoice_title,
			"description": _(
				"{0}: {1} night(s) × {2}/night rate difference ({3} → {4})"
			).format(
				invoice_title,
				remaining_nights,
				fmt_money(abs(nightly_diff), 2),
				fmt_money(flt(old_rate), 2),
				fmt_money(new_rate, 2),
			),
			"qty": qty,
			"rate": abs(nightly_diff),
			"income_account": default_income,
		},
	)

	invoice.set_taxes()
	invoice.save(ignore_permissions=True)
	invoice.submit()

	if source_invoice:
		from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import enqueue_credit_note_reconciliation

		enqueue_credit_note_reconciliation(
			invoice.name,
			source_invoice=source_invoice,
			check_in=check_in_doc.name,
		)

	action = _("Charged") if is_upgrade else _("Credited")
	check_in_doc.add_comment(
		"Comment",
		text=_(
			"Room transfer adjustment: {0} {1} ({2} night(s) × {3}/night). Invoice {4} created."
		).format(
			action,
			fmt_money(abs(total_diff), 2),
			remaining_nights,
			fmt_money(abs(nightly_diff), 2),
			invoice.name,
		),
	)

	frappe.msgprint(
		_("{0} rate adjustment of {1} applied for {2} remaining night(s). Invoice {3} created.").format(
			action, fmt_money(abs(total_diff), 2), remaining_nights, invoice.name
		),
		alert=True,
	)

	return invoice.name


@frappe.whitelist()
def apply_late_checkout_charge(check_in, item, charge_type, amount):
	from frappe.utils import flt

	"""
    Create Sales Invoice for late checkout charge
    """

	check_in_doc = frappe.get_doc("Hotel Room Check In", check_in)
	if check_in_doc.late_checkout:
		return {
			"status": "skipped",
			"sales_invoice": None,
			"amount": 0,
			"message": _("Late check-out was approved at check-in, so no late check-out charge is applied."),
		}

	# --------------------------------
	# Safety: prevent duplicate charge
	# --------------------------------
	# existing = frappe.db.exists(
	#     "Sales Invoice Item",
	#     {
	#         "item_code": item,
	#         "custom_hotel_room_check_in": check_in
	#     }
	# )

	# if existing:
	#     frappe.throw("Late check-out charge has already been applied.")

	# ----------------------------
	# Customer validation using check-in guest
	# ----------------------------
	if not item or not frappe.db.exists("Item", item):
		frappe.throw(_("Late check-out charge item is not configured or no longer exists."))

	customer = frappe.get_value("Hotel Guest", check_in_doc.guest, "customer")
	if not customer:
		frappe.throw("No customer linked to this check-in.")

	# ----------------------------
	# Determine charge amount
	# ----------------------------
	rate = amount

	if charge_type == "Percentage":
		if not check_in_doc.rate_amount:
			frappe.throw("Room rate not found for percentage charge.")

		room_rate = flt(check_in_doc.rate_amount)
		percentage = flt(amount)

		rate = (room_rate * percentage) / 100

	if flt(rate) <= 0:
		frappe.throw(_("Late check-out charge amount must be greater than zero."))

	existing = frappe.db.sql(
		"""
		SELECT sii.name
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.item_code = %s
		  AND si.custom_hotel_room_check_in = %s
		  AND si.docstatus < 2
		LIMIT 1
		""",
		(item, check_in),
	)
	if existing:
		frappe.throw(_("Late check-out charge has already been applied."))

	# ----------------------------
	# Create Sales Invoice
	# ----------------------------
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		frappe.throw(_("No default Company configured. Cannot create late check-out charge."))

	si = frappe.new_doc("Sales Invoice")
	si.customer = customer
	si.posting_date = nowdate()
	si.company = company
	si.due_date = nowdate()
	si.custom_hotel_room_check_in = check_in
	si.flags.ignore_permissions = True
	si.flags.ignore_mandatory = True
	if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
		si.custom_invoice_source = "Late Charges"

	# ----------------------------
	# Add item
	# ----------------------------
	si.append("items", {"item_code": item, "qty": 1, "rate": rate, "description": "Late Check-out Charge"})
	si.set_taxes()
	si.save(ignore_permissions=True)
	si.submit()
	check_in_doc.db_set("late_checkout", 1, update_modified=False)

	return {"status": "success", "sales_invoice": si.name, "amount": rate}
