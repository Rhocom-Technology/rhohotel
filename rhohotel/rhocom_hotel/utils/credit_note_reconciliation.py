import frappe
from frappe import _
from frappe.utils import flt, today


def enqueue_credit_note_reconciliation(credit_note, source_invoice=None, check_in=None, reservation=None):
	"""Queue accounting reconciliation for a submitted Sales Invoice credit note."""
	if not credit_note:
		return

	frappe.enqueue(
		"rhohotel.rhocom_hotel.utils.credit_note_reconciliation.reconcile_sales_credit_note",
		queue="short",
		enqueue_after_commit=True,
		user="Administrator",
		credit_note=credit_note,
		source_invoice=source_invoice,
		check_in=check_in,
		reservation=reservation,
	)


@frappe.whitelist()
def reconcile_sales_credit_note(credit_note, source_invoice=None, check_in=None, reservation=None, sync_folio=True):
	"""Apply a Sales Invoice return against its intended invoice using ERPNext reconciliation.

	The frontdesk folio can mathematically offset a return invoice, but Accounts
	Receivable only stops showing it as unallocated after ERPNext creates the
	reconciliation Journal Entry. This function performs that accounting step.
	"""
	if not credit_note or not frappe.db.exists("Sales Invoice", credit_note):
		frappe.throw(_("Credit note {0} was not found.").format(credit_note))
	if isinstance(sync_folio, str):
		sync_folio = sync_folio.lower() not in {"0", "false", "no"}

	credit_doc = frappe.get_doc("Sales Invoice", credit_note)
	if int(credit_doc.docstatus or 0) != 1:
		frappe.throw(_("Credit note {0} must be submitted before reconciliation.").format(credit_note))
	if not int(credit_doc.is_return or 0):
		return {"status": "skipped", "reason": "not_a_credit_note", "credit_note": credit_note}

	source_invoice = source_invoice or credit_doc.return_against
	if not source_invoice:
		return {"status": "skipped", "reason": "no_source_invoice", "credit_note": credit_note}
	if not frappe.db.exists("Sales Invoice", source_invoice):
		frappe.throw(_("Source invoice {0} was not found.").format(source_invoice))

	source_doc = frappe.get_doc("Sales Invoice", source_invoice)
	if int(source_doc.docstatus or 0) != 1:
		frappe.throw(_("Source invoice {0} must be submitted before reconciliation.").format(source_invoice))
	if source_doc.customer != credit_doc.customer:
		frappe.throw(_("Credit note and source invoice must belong to the same customer."))

	credit_available = _get_credit_note_open_amount(credit_doc.name)
	source_outstanding = _get_invoice_open_amount(source_doc.name)
	if credit_available > 0 and source_outstanding <= 0:
		alternate_invoice = _find_alternate_outstanding_invoice(
			credit_doc,
			check_in=check_in or credit_doc.get("custom_hotel_room_check_in"),
			reservation=reservation,
			exclude={credit_doc.name, source_doc.name},
		)
		if alternate_invoice:
			source_doc = frappe.get_doc("Sales Invoice", alternate_invoice)
			source_invoice = source_doc.name
			source_outstanding = _get_invoice_open_amount(source_doc.name)
	allocated_amount = min(credit_available, source_outstanding)

	if allocated_amount <= 0:
		return {
			"status": "skipped",
			"reason": "nothing_to_reconcile",
			"credit_note": credit_doc.name,
			"source_invoice": source_doc.name,
			"credit_available": credit_available,
			"source_outstanding": source_outstanding,
		}

	account = credit_doc.debit_to or source_doc.debit_to
	if not account:
		frappe.throw(_("Receivable account is missing for credit note {0}.").format(credit_doc.name))

	currency = (
		frappe.db.get_value("Account", account, "account_currency")
		or frappe.db.get_value("Company", credit_doc.company, "default_currency")
	)
	exchange_rate = flt(getattr(credit_doc, "conversion_rate", None) or 1)

	from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import reconcile_dr_cr_note

	current_user = frappe.session.user
	try:
		if current_user != "Administrator":
			frappe.set_user("Administrator")
		reconcile_dr_cr_note(
			[
				frappe._dict(
					{
						"voucher_type": "Sales Invoice",
						"voucher_no": credit_doc.name,
						"against_voucher_type": "Sales Invoice",
						"against_voucher": source_doc.name,
						"account": account,
						"party_type": "Customer",
						"party": credit_doc.customer,
						"dr_or_cr": "credit_in_account_currency",
						"unreconciled_amount": credit_available,
						"unadjusted_amount": credit_available,
						"allocated_amount": allocated_amount,
						"difference_amount": 0,
						"difference_account": None,
						"debit_or_credit_note_posting_date": today(),
						"currency": currency,
						"exchange_rate": exchange_rate,
						"cost_center": _get_credit_note_cost_center(credit_doc),
					}
				)
			],
			credit_doc.company,
		)
	finally:
		if current_user != frappe.session.user:
			frappe.set_user(current_user)

	if sync_folio:
		try:
			_sync_related_folio(check_in=check_in or credit_doc.get("custom_hotel_room_check_in"), reservation=reservation)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Folio sync failed after credit note reconciliation")

	frappe.db.commit()
	return {
		"status": "reconciled",
		"credit_note": credit_doc.name,
		"source_invoice": source_doc.name,
		"allocated_amount": allocated_amount,
	}


@frappe.whitelist()
def reconcile_credit_notes_for_checkin(check_in, sync_folio=True):
	if not check_in:
		frappe.throw(_("Check-in is required."))
	if isinstance(sync_folio, str):
		sync_folio = sync_folio.lower() not in {"0", "false", "no"}

	rows = frappe.get_all(
		"Sales Invoice",
		filters={
			"custom_hotel_room_check_in": check_in,
			"docstatus": 1,
			"is_return": 1,
			"outstanding_amount": ["<", 0],
		},
		fields=["name", "return_against"],
	)
	return [
		reconcile_sales_credit_note(
			row.name,
			source_invoice=row.return_against,
			check_in=check_in,
			sync_folio=sync_folio,
		)
		for row in rows
		if row.return_against
	]


@frappe.whitelist()
def reconcile_credit_notes_for_reservation(reservation, sync_folio=True):
	if not reservation:
		frappe.throw(_("Reservation is required."))

	doc = frappe.get_doc("Hotel Reservation", reservation)
	invoice_names = [doc.sales_invoice] if doc.get("sales_invoice") else []
	invoice_names.extend(
		frappe.get_all(
			"Hotel Reservation Invoice",
			filters={"parent": reservation},
			pluck="invoice",
		)
	)
	invoice_names = list({name for name in invoice_names if name})
	if not invoice_names:
		return []

	rows = frappe.get_all(
		"Sales Invoice",
		filters={
			"name": ["in", invoice_names],
			"docstatus": 1,
			"is_return": 1,
			"outstanding_amount": ["<", 0],
		},
		fields=["name", "return_against"],
	)
	return [
		reconcile_sales_credit_note(
			row.name,
			source_invoice=row.return_against,
			reservation=reservation,
			sync_folio=sync_folio,
		)
		for row in rows
		if row.return_against
	]


def _get_invoice_open_amount(invoice_name):
	return max(0.0, flt(frappe.db.get_value("Sales Invoice", invoice_name, "outstanding_amount") or 0))


def _get_credit_note_open_amount(credit_note):
	outstanding = flt(frappe.db.get_value("Sales Invoice", credit_note, "outstanding_amount") or 0)
	return abs(outstanding) if outstanding < 0 else 0.0


def _get_credit_note_cost_center(credit_doc):
	for item in credit_doc.get("items") or []:
		if item.cost_center:
			return item.cost_center
	return None


def _find_alternate_outstanding_invoice(credit_doc, check_in=None, reservation=None, exclude=None):
	exclude = set(exclude or [])
	invoice_names = []
	if check_in and frappe.db.has_column("Sales Invoice", "custom_hotel_room_check_in"):
		invoice_names.extend(
			frappe.get_all(
				"Sales Invoice",
				filters={
					"custom_hotel_room_check_in": check_in,
					"docstatus": 1,
					"is_return": 0,
					"customer": credit_doc.customer,
					"outstanding_amount": [">", 0],
				},
				pluck="name",
				order_by="posting_date asc, creation asc",
			)
		)

	if reservation and frappe.db.exists("Hotel Reservation", reservation):
		res_doc = frappe.get_doc("Hotel Reservation", reservation)
		if res_doc.get("sales_invoice"):
			invoice_names.append(res_doc.sales_invoice)
		invoice_names.extend(
			frappe.get_all(
				"Hotel Reservation Invoice",
				filters={"parent": reservation},
				pluck="invoice",
			)
		)

	invoice_names = [name for name in dict.fromkeys(invoice_names) if name and name not in exclude]
	if not invoice_names:
		return None

	row = frappe.db.get_value(
		"Sales Invoice",
		{
			"name": ["in", invoice_names],
			"docstatus": 1,
			"is_return": 0,
			"customer": credit_doc.customer,
			"outstanding_amount": [">", 0],
		},
		"name",
		order_by="posting_date asc, creation asc",
	)
	return row


def _sync_related_folio(check_in=None, reservation=None):
	if check_in:
		from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

		sync_checkin_folio_totals(check_in)
	if reservation and frappe.db.exists("Hotel Reservation", reservation):
		from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import (
			get_payment_summary_for_reservation,
		)

		get_payment_summary_for_reservation(reservation)
