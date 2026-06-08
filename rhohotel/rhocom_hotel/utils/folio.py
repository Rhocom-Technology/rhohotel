import frappe
from frappe.utils import flt


def _has_column(doctype, column):
	try:
		return frappe.db.has_column(doctype, column)
	except Exception:
		return False


def _round(value):
	return round(flt(value), 2)


def _sales_invoice_source_expr():
	if _has_column("Sales Invoice", "custom_invoice_source"):
		return "COALESCE(NULLIF(custom_invoice_source, ''), 'Sales Invoice')"
	return "'Sales Invoice'"


def _get_sales_invoice_rows(check_in):
	if not _has_column("Sales Invoice", "custom_hotel_room_check_in"):
		return []

	return frappe.db.sql(
		f"""
		SELECT
			name,
			customer,
			posting_date,
			due_date,
			grand_total,
			outstanding_amount,
			is_return,
			return_against,
			status,
			{_sales_invoice_source_expr()} AS invoice_type
		FROM `tabSales Invoice`
		WHERE custom_hotel_room_check_in = %s
		  AND docstatus = 1
		ORDER BY posting_date DESC, creation DESC
		""",
		check_in,
		as_dict=True,
	) or []


def _get_invoice_payment_allocations(invoice_names):
	if not invoice_names:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT
			per.reference_name,
			COALESCE(SUM(ABS(per.allocated_amount)), 0) AS allocated
		FROM `tabPayment Entry Reference` per
		INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE per.reference_doctype = 'Sales Invoice'
		  AND per.reference_name IN %(invoice_names)s
		  AND pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		GROUP BY per.reference_name
		""",
		{"invoice_names": tuple(invoice_names)},
		as_dict=True,
	) or []
	return {row.reference_name: flt(row.allocated) for row in rows}


def _get_source_transfer_totals(invoice_names):
	if not invoice_names or not frappe.db.exists("DocType", "Bill Transfer"):
		return {}

	rows = frappe.db.sql(
		"""
		SELECT source_invoice, COALESCE(SUM(total_amount), 0) AS total
		FROM `tabBill Transfer`
		WHERE source_invoice IN %(invoice_names)s
		  AND status = 'Approved'
		  AND docstatus = 1
		GROUP BY source_invoice
		""",
		{"invoice_names": tuple(invoice_names)},
		as_dict=True,
	) or []
	return {row.source_invoice: flt(row.total) for row in rows}


def get_transferred_in_bills(check_in):
	if not frappe.db.exists("DocType", "Bill Transfer"):
		return []

	rows = frappe.db.sql(
		"""
		SELECT name, from_guest, source_invoice, total_amount, status,
		       creation AS transfer_date, reason, journal_entry
		FROM `tabBill Transfer`
		WHERE to_check_in = %s
		  AND status != 'Cancelled'
		ORDER BY creation DESC
		""",
		check_in,
		as_dict=True,
	) or []

	for row in rows:
		row["outstanding_amount"] = _journal_entry_outstanding(row.get("journal_entry")) if row.get("status") == "Approved" else 0

	return rows


def _journal_entry_outstanding(journal_entry):
	if not journal_entry:
		return 0

	debit_total = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(debit_in_account_currency), 0)
		FROM `tabJournal Entry Account`
		WHERE parent = %s
		  AND debit_in_account_currency > 0
		  AND party_type = 'Customer'
		""",
		journal_entry,
	)[0][0] or 0

	paid = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(ABS(per.allocated_amount)), 0)
		FROM `tabPayment Entry Reference` per
		INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE per.reference_doctype = 'Journal Entry'
		  AND per.reference_name = %s
		  AND pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		""",
		journal_entry,
	)[0][0] or 0

	return _round(max(0, flt(debit_total) - flt(paid)))


def _get_payment_totals(check_in):
	if not _has_column("Payment Entry", "custom_hotel_room_check_in"):
		return {"received": 0, "paid_out": 0}

	rows = frappe.db.sql(
		"""
		SELECT payment_type, COALESCE(SUM(paid_amount), 0) AS total
		FROM `tabPayment Entry`
		WHERE custom_hotel_room_check_in = %s
		  AND docstatus = 1
		GROUP BY payment_type
		""",
		check_in,
		as_dict=True,
	) or []
	totals = {"received": 0, "paid_out": 0}
	for row in rows:
		if row.payment_type == "Receive":
			totals["received"] += flt(row.total)
		elif row.payment_type == "Pay":
			totals["paid_out"] += flt(row.total)
	return totals


def _get_hotel_refund_total(check_in):
	if not frappe.db.exists("DocType", "Hotel Refund"):
		return 0

	return flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(refund_amount), 0)
			FROM `tabHotel Refund`
			WHERE check_in = %s
			  AND docstatus = 1
			  AND COALESCE(status, '') != 'Cancelled'
			""",
			check_in,
		)[0][0]
		or 0
	)


def get_checkin_folio(check_in):
	"""Return normalized folio rows and one canonical billing summary."""
	if not frappe.db.exists("Hotel Room Check In", check_in):
		frappe.throw(f"Check-in {check_in} not found")

	try:
		from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import (
			reconcile_credit_notes_for_checkin,
		)

		reconcile_credit_notes_for_checkin(check_in, sync_folio=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Check-in credit note reconciliation failed")

	invoices = _get_sales_invoice_rows(check_in)
	invoice_names = [row.name for row in invoices]
	payment_allocations = _get_invoice_payment_allocations(invoice_names)
	transfer_out = _get_source_transfer_totals(invoice_names)
	transferred_out_total = _round(sum(flt(amount) for amount in transfer_out.values()))

	linked_credits = {}
	unlinked_credit_balance = 0
	sales_charges_total = 0
	credit_notes_total = 0

	for row in invoices:
		row["is_return"] = int(row.get("is_return") or 0)
		row["amount"] = abs(flt(row.get("grand_total"))) if row["is_return"] else flt(row.get("grand_total"))
		row["raw_outstanding_amount"] = flt(row.get("outstanding_amount"))
		row["net_outstanding_amount"] = row["raw_outstanding_amount"]
		row["credit_applied"] = 0
		row["source_transfer_amount"] = 0
		row["open_credit_amount"] = 0

		if row["is_return"]:
			credit_amount = abs(flt(row.get("grand_total")))
			credit_notes_total += credit_amount
			row["credit_amount"] = credit_amount
			row["open_credit_amount"] = abs(flt(row.get("outstanding_amount")))
			if row.get("return_against"):
				linked_credits[row.return_against] = linked_credits.get(row.return_against, 0) + credit_amount
			else:
				unlinked_credit_balance += row["open_credit_amount"] or credit_amount
		else:
			sales_charges_total += flt(row.get("grand_total"))

	charge_rows = [row for row in invoices if not row["is_return"]]
	for row in charge_rows:
		gross = abs(flt(row.get("grand_total")))
		raw_outstanding = max(0, flt(row.get("outstanding_amount")))
		paid_allocated = flt(payment_allocations.get(row.name))
		linked_credit_amount = flt(linked_credits.get(row.name))
		source_transfer_amount = flt(transfer_out.get(row.name))
		known_adjustments = paid_allocated + linked_credit_amount + source_transfer_amount

		if known_adjustments > 0:
			expected_after_adjustments = max(0, gross - known_adjustments)
			net_outstanding = min(raw_outstanding, expected_after_adjustments)
		else:
			net_outstanding = raw_outstanding

		row["source_transfer_amount"] = _round(source_transfer_amount)
		row["net_outstanding_amount"] = _round(net_outstanding)

	remaining_credit = flt(unlinked_credit_balance)
	for row in sorted(charge_rows, key=lambda r: (str(r.get("posting_date") or ""), r.name)):
		if remaining_credit <= 0:
			break
		applied = min(flt(row["net_outstanding_amount"]), remaining_credit)
		if applied > 0:
			row["net_outstanding_amount"] = _round(flt(row["net_outstanding_amount"]) - applied)
			row["credit_applied"] = _round(flt(row["credit_applied"]) + applied)
			remaining_credit -= applied

	for row in invoices:
		if row["is_return"]:
			row["outstanding_amount"] = _round(abs(flt(row.get("outstanding_amount"))))
		else:
			row["outstanding_amount"] = _round(row["net_outstanding_amount"])

	invoice_outstanding = _round(sum(flt(row["net_outstanding_amount"]) for row in charge_rows))
	transferred_in = get_transferred_in_bills(check_in)
	acquired_total = _round(
		sum(flt(row.get("total_amount")) for row in transferred_in if row.get("status") == "Approved")
	)
	acquired_outstanding = _round(
		sum(flt(row.get("outstanding_amount")) for row in transferred_in if row.get("status") == "Approved")
	)

	payment_totals = _get_payment_totals(check_in)
	total_received = _round(payment_totals["received"])
	total_paid_out = _round(payment_totals["paid_out"])
	reserved_refunds_total = _round(_get_hotel_refund_total(check_in))

	invoice_net_total = _round(sales_charges_total - credit_notes_total - transferred_out_total)
	net_bill = _round(invoice_net_total + acquired_total)
	balance_amount = _round(net_bill - total_received + total_paid_out)
	ledger_outstanding = _round(invoice_outstanding + acquired_outstanding)
	collectible_outstanding = _round(max(0, min(ledger_outstanding, balance_amount)) if balance_amount > 0 else 0)
	credit_balance = _round(max(0, -balance_amount))
	refundable_balance = _round(max(0, credit_balance - reserved_refunds_total))

	summary = {
		"sales_charges_total": _round(sales_charges_total),
		"credit_notes_total": _round(credit_notes_total),
		"source_transfers_total": transferred_out_total,
		"invoice_net_total": invoice_net_total,
		"invoice_outstanding": invoice_outstanding,
		"open_credit_balance": _round(remaining_credit),
		"acquired_total": acquired_total,
		"acquired_outstanding": acquired_outstanding,
		"total_charges": _round(sales_charges_total + acquired_total),
		"total_credits": _round(credit_notes_total + transferred_out_total),
		"net_bill": net_bill,
		"total_received": total_received,
		"total_refunded": total_paid_out,
		"reserved_refunds_total": reserved_refunds_total,
		"ledger_outstanding": ledger_outstanding,
		"collectible_outstanding": collectible_outstanding,
		"balance_amount": balance_amount,
		"credit_balance": credit_balance,
		"refundable_balance": refundable_balance,
	}

	return {
		"sales_invoices": invoices,
		"acquired_bills": transferred_in,
		"summary": summary,
	}


def get_invoice_net_outstanding(check_in, invoice_name):
	folio = get_checkin_folio(check_in)
	for row in folio.get("sales_invoices") or []:
		if row.get("name") == invoice_name and not row.get("is_return"):
			return flt(row.get("net_outstanding_amount"))
	return 0


def sync_checkin_folio_totals(check_in):
	folio = get_checkin_folio(check_in)
	balance = flt(folio.get("summary", {}).get("balance_amount"))
	frappe.db.set_value(
		"Hotel Room Check In",
		check_in,
		"total_outstanding_amount",
		balance,
		update_modified=False,
	)
	return folio
