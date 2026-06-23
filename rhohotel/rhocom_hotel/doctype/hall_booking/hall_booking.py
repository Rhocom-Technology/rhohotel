# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import json
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, nowdate, date_diff
import math


def _line_discount_percentage(gross_amount, discount_value):
	gross_amount = flt(gross_amount or 0)
	discount_value = flt(discount_value or 0)
	if gross_amount <= 0 or discount_value <= 0:
		return 0
	return flt((discount_value / gross_amount) * 100, 6)


def _discount_value(gross_amount, discount_type, discount_amount):
	gross_amount = flt(gross_amount or 0)
	discount_amount = flt(discount_amount or 0)
	if gross_amount <= 0 or discount_amount <= 0:
		return 0

	if (discount_type or "Fixed Amount") == "Percentage":
		discount_amount = min(discount_amount, 100)
		return gross_amount * (discount_amount / 100)

	return min(discount_amount, gross_amount)

class HallBooking(Document):
	def validate(self):
		self.validate_booking_overlap()
		self.set_totals()

	def on_submit(self):
		self.create_customer_if_not_exists()
		# self.create_invoice()
	
 
	def set_totals(self):
		start_dt = get_datetime(self.start_datetime)
		end_dt = get_datetime(self.end_datetime)

		if end_dt <= start_dt:
			frappe.throw("End Date must be after Start Date.")

		self.total_days = max(
			1,
			date_diff(getdate(end_dt), getdate(start_dt)) + 1
		)
		self.total_amount = flt(self.rate or 0) * self.total_days

		hall_total = flt(self.total_amount or 0)
		hall_discount_value = flt(self.discount_amount or 0)

		if self.discount_type == "Percentage":
			if hall_discount_value > 100:
				frappe.throw("Hall discount percentage cannot be greater than 100%.")
			hall_discount = hall_total * (hall_discount_value / 100)
		else:
			if hall_discount_value > hall_total:
				frappe.throw("Hall discount amount cannot be greater than hall total.")
			hall_discount = hall_discount_value

		hall_net_total = max(0, hall_total - hall_discount)

		additional_total = 0

		for row in self.get("additional_billings", []):
			row.qty = flt(row.qty or 1)
			row.rate = flt(row.rate or 0)
			row.discount_type = row.discount_type or "Fixed Amount"
			row.discount_amount = flt(row.discount_amount or 0)

			gross = row.qty * row.rate

			if row.discount_type == "Percentage":
				if row.discount_amount > 100:
					frappe.throw(
						"Discount percentage cannot be greater than 100% for service {0}."
						.format(row.service)
					)
				line_discount = gross * (row.discount_amount / 100)
			else:
				if row.discount_amount > gross:
					frappe.throw(
						"Discount amount cannot be greater than service amount for {0}."
						.format(row.service)
					)
				line_discount = row.discount_amount

			row.amount = max(0, gross - line_discount)
			additional_total += flt(row.amount)

		self.net_total = max(0, hall_net_total + additional_total)
	
 
	def validate_booking_overlap(self):
		if not self.hall or not self.start_datetime or not self.end_datetime:
			return

		start_dt = get_datetime(self.start_datetime)
		end_dt = get_datetime(self.end_datetime)

		if end_dt <= start_dt:
			frappe.throw("End Date must be after Start Date.")

		overlapping_bookings = frappe.db.sql(
			"""
			SELECT
				name,
				customer_name,
				hall,
				start_datetime,
				end_datetime,
				event_status,
				completed_on
			FROM `tabHall Booking`
			WHERE hall = %(hall)s
			AND docstatus = 1
			AND name != %(name)s
			AND IFNULL(event_status, 'Scheduled') != 'Cancelled'
			""",
			{
				"hall": self.hall,
				"name": self.name or "",
			},
			as_dict=True,
		)

		for conflict in overlapping_bookings:
			conflict_start = get_datetime(conflict.start_datetime)

			if conflict.event_status == "Completed" and conflict.completed_on:
				conflict_end = get_datetime(conflict.completed_on)
				completed_message = (
					"<br><b>Completed At:</b> {completed}<br>"
					"This booking has already been completed, so the hall is available only after the completed time. "
					"Please choose a start time after {completed}."
				).format(
					completed=frappe.format(
						conflict_end,
						{"fieldtype": "Datetime"}
					)
				)
			else:
				conflict_end = get_datetime(conflict.end_datetime)
				completed_message = (
					"<br>This booking has not been completed yet. "
					"Please choose a time outside the booked period."
				)

			if conflict_end <= start_dt:
				continue

			if conflict_start >= end_dt:
				continue

			frappe.throw(
				(
					"Hall '{hall}' is not available for the selected time.<br><br>"
					"<b>Conflicting Booking:</b> {booking}<br>"
					"<b>Customer:</b> {customer}<br>"
					"<b>Booked From:</b> {start}<br>"
					"<b>Booked To:</b> {end}"
					"{completed_message}"
				).format(
					hall=self.hall,
					booking=conflict.name,
					customer=conflict.customer_name or "N/A",
					start=frappe.format(
						conflict.start_datetime,
						{"fieldtype": "Datetime"}
					),
					end=frappe.format(
						conflict_end,
						{"fieldtype": "Datetime"}
					),
					completed_message=completed_message,
				)
			)
  
	def create_invoice(self):
		hall = frappe.get_doc("Hall", self.hall)

		company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not company:
			frappe.throw(_("No default company set in Global Defaults."))

		company_doc = frappe.get_doc("Company", company)
		default_income = frappe.db.get_value("Company", company, "default_income_account")

		if not default_income:
			frappe.throw(_("No default income account set for Company {0}.").format(company))

		cost_center = company_doc.cost_center

		hall_qty = flt(self.total_days or 1)
		hall_gross = flt(self.total_amount or 0)
		hall_net = hall_gross
		hall_discount_value = 0

		if flt(self.discount_amount or 0) > 0:
			if self.discount_type == "Percentage":
				if flt(self.discount_amount) > 100:
					frappe.throw("Hall discount percentage cannot be greater than 100%.")

				hall_discount_value = hall_gross * flt(self.discount_amount) / 100
				hall_net = hall_gross - hall_discount_value

			else:
				if flt(self.discount_amount) > hall_gross:
					frappe.throw("Hall discount cannot be greater than hall amount.")

				hall_discount_value = flt(self.discount_amount)
				hall_net = hall_gross - hall_discount_value

		hall_net = max(0, hall_net)
		hall_discount_percentage = _line_discount_percentage(hall_gross, hall_discount_value)
		hall_rate = (hall_gross / hall_qty) if hall_qty else 0
		hall_net_rate = (hall_net / hall_qty) if hall_qty else 0
		hall_discount_amount_per_unit = max(0, hall_rate - hall_net_rate)

		invoice = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": self.customer_name,
			"posting_date": getdate(self.end_datetime),
			"due_date": getdate(self.end_datetime),
			"set_posting_time": 1,
			"company": company,
			"items": [],
		})

		invoice.append("items", {
			"item_code": hall.item_name or self.hall,
			"qty": hall_qty,
			"price_list_rate": hall_rate,
			"rate": hall_net_rate,
			"discount_percentage": hall_discount_percentage,
			"discount_amount": hall_discount_amount_per_unit,
			"income_account": default_income,
			"cost_center": cost_center,
		})

		for billing in self.get("additional_billings", []):
			qty = flt(billing.qty or 1)
			rate = flt(billing.rate or 0)
			gross_amount = qty * rate
			discount_type = billing.discount_type or "Fixed Amount"
			discount_amount = flt(billing.discount_amount or 0)

			if discount_type == "Percentage":
				line_discount = gross_amount * (discount_amount / 100)
			else:
				line_discount = min(discount_amount, gross_amount)

			line_net = max(0, gross_amount - line_discount)
			net_rate = (line_net / qty) if qty else 0
			line_discount_amount_per_unit = max(0, rate - net_rate)
			line_discount_percentage = _line_discount_percentage(gross_amount, line_discount)

			invoice.append("items", {
				"item_code": billing.service,
				"qty": qty,
				"price_list_rate": rate,
				"rate": net_rate,
				"discount_percentage": line_discount_percentage,
				"discount_amount": line_discount_amount_per_unit,
				"income_account": default_income,
				"cost_center": cost_center,
			})

		invoice.set_taxes()
		invoice.insert(ignore_permissions=True)
		invoice.submit()

		self.sales_invoice = invoice.name
		self.save(ignore_permissions=True)
 
	def create_customer_if_not_exists(self):
		if not frappe.db.exists("Customer", self.customer_name):
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": self.customer_name,
				"customer_type": "Individual",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			})
			customer.insert(ignore_permissions=True)


@frappe.whitelist()
def get_hall_rate(hall_name):
	hall = frappe.get_doc("Hall", hall_name)
	return hall.rate

@frappe.whitelist()
def adjust_booking_datetime(
	booking_name,
	start_datetime,
	end_datetime,
	reason=None,
	discount_type=None,
	discount_amount=0,
):
	booking = frappe.get_doc("Hall Booking", booking_name)

	if booking.docstatus != 1:
		frappe.throw("Only submitted bookings can be adjusted.")

	start_dt = get_datetime(start_datetime)
	end_dt = get_datetime(end_datetime)

	if end_dt <= start_dt:
		frappe.throw("End date must be after start date.")

	new_total_days = max(1, date_diff(getdate(end_dt), getdate(start_dt)) + 1)
	previous_total_days = flt(booking.total_days or 0)

	# Check overlap using effective end time.
	# If a previous booking was marked Completed, its completed_on becomes its real end time.
	overlapping_bookings = frappe.db.sql(
		"""
		SELECT
			name,
			customer_name,
			start_datetime,
			end_datetime,
			event_status,
			completed_on
		FROM `tabHall Booking`
		WHERE hall = %(hall)s
		  AND docstatus = 1
		  AND name != %(name)s
		  AND IFNULL(event_status, 'Scheduled') != 'Cancelled'
		""",
		{
			"hall": booking.hall,
			"name": booking.name or "",
		},
		as_dict=True,
	)

	for conflict in overlapping_bookings:
		conflict_start = get_datetime(conflict.start_datetime)

		if conflict.event_status == "Completed" and conflict.completed_on:
			conflict_end = get_datetime(conflict.completed_on)
		else:
			conflict_end = get_datetime(conflict.end_datetime)

		if conflict_end <= start_dt:
			continue

		if conflict_start >= end_dt:
			continue

		frappe.throw(
			(
				"Hall '{hall}' is already booked for the selected time.<br><br>"
				"<b>Conflicting Booking:</b> {booking}<br>"
				"<b>Customer:</b> {customer}<br>"
				"<b>Booked From:</b> {start}<br>"
				"<b>Booked To:</b> {end}"
			).format(
				hall=booking.hall,
				booking=conflict.name,
				customer=conflict.customer_name or "N/A",
				start=frappe.format(conflict.start_datetime, {"fieldtype": "Datetime"}),
				end=frappe.format(conflict_end, {"fieldtype": "Datetime"}),
			)
		)

	hall = frappe.get_doc("Hall", booking.hall)

	company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		frappe.throw("No default company set in Global Defaults.")

	income_account = frappe.db.get_value("Company", company, "default_income_account")
	if not income_account:
		frappe.throw("No default income account set for Company {0}.".format(company))

	cost_center = frappe.db.get_value("Company", company, "cost_center")

	adjustment_invoice = None
	new_net_total = flt(booking.net_total or 0)

	discount_type = discount_type or "Fixed Amount"
	discount_amount = flt(discount_amount or 0)
	adjustment_discount = 0
	net_adjustment = 0

	if new_total_days != previous_total_days:
		diff_days = abs(new_total_days - previous_total_days)
		qty = diff_days if new_total_days > previous_total_days else -diff_days

		rate_per_day = flt(hall.rate or booking.rate or 0)
		gross_adjustment = diff_days * rate_per_day

		if discount_type == "Percentage":
			if discount_amount > 100:
				frappe.throw("Adjustment discount percentage cannot be greater than 100%.")

			adjustment_discount = gross_adjustment * (discount_amount / 100)

		else:
			if discount_amount > gross_adjustment:
				frappe.throw("Adjustment discount amount cannot be greater than adjustment amount.")

			adjustment_discount = discount_amount

		net_adjustment = max(0, gross_adjustment - adjustment_discount)
		adjustment_discount_percentage = _line_discount_percentage(gross_adjustment, adjustment_discount)
		net_rate = (net_adjustment / diff_days) if diff_days else 0
		adjustment_discount_amount_per_unit = max(0, rate_per_day - net_rate)

		invoice_data = {
			"doctype": "Sales Invoice",
			"customer": booking.customer_name,
			"posting_date": nowdate(),
			"company": company,
			"items": [
				{
					"item_code": hall.item_name or booking.hall,
					"price_list_rate": rate_per_day,
					"rate": net_rate,
					"qty": qty,
					"discount_percentage": adjustment_discount_percentage,
					"discount_amount": adjustment_discount_amount_per_unit,
					"income_account": income_account,
					"cost_center": cost_center,
				}
			],
			"custom_hall_booking": booking.name,
		}

		if qty < 0:
			invoice_data["is_return"] = 1

		invoice = frappe.get_doc(invoice_data)
		invoice.insert(ignore_permissions=True)
		invoice.submit()

		adjustment_invoice = invoice.name
		new_net_total = flt(booking.net_total or 0) + flt(invoice.grand_total or 0)

	booking.append("adjustment_history", {
		"previous_start": booking.start_datetime,
		"previous_end": booking.end_datetime,
		"previous_days": previous_total_days,
		"new_start": start_dt,
		"new_end": end_dt,
		"new_days": new_total_days,
		"adjustment_reason": reason,
		"adjusted_by": frappe.session.user,
		"adjusted_on": nowdate(),
		"adjustment_invoice": adjustment_invoice,
		"discount_type": discount_type,
		"discount_amount": discount_amount,
		"discount_value": adjustment_discount,
	})

	booking.start_datetime = start_dt
	booking.end_datetime = end_dt
	booking.total_days = new_total_days
	booking.total_amount = flt(hall.rate or booking.rate or 0) * new_total_days
	booking.net_total = new_net_total

	booking.flags.ignore_validate_update_after_submit = True
	booking.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"previous_days": previous_total_days,
		"new_days": new_total_days,
		"adjustment_invoice": adjustment_invoice,
		"discount_type": discount_type,
		"discount_amount": discount_amount,
		"discount_value": adjustment_discount,
		"net_adjustment": net_adjustment,
	}
 
@frappe.whitelist()
def get_payment_status(booking_name):
	booking = frappe.get_doc("Hall Booking", booking_name)

	if not booking.sales_invoice:
		return "No Invoice"

	invoice = frappe.get_doc("Sales Invoice", booking.sales_invoice)

	if invoice.outstanding_amount <= 0:
		return "Paid"
	elif invoice.outstanding_amount < invoice.grand_total:
		return "Partially Paid"
	else:
		return "Unpaid"


@frappe.whitelist()
def create_payment_entry(booking, data):
	data = frappe._dict(json.loads(data))
	booking = frappe.get_doc("Hall Booking", booking)

	if booking.docstatus != 1:
		frappe.throw("Only submitted bookings can receive payment.")

	invoice_names = []

	if booking.sales_invoice:
		invoice_names.append(booking.sales_invoice)

	for row in booking.get("adjustment_history", []):
		if row.adjustment_invoice:
			invoice_names.append(row.adjustment_invoice)

	if not invoice_names:
		frappe.throw("No invoice linked to this booking.")

	unpaid_invoices = []

	for inv_name in invoice_names:
		inv = frappe.get_doc("Sales Invoice", inv_name)
		if inv.docstatus == 1 and flt(inv.outstanding_amount) > 0:
			unpaid_invoices.append(inv)

	if not unpaid_invoices:
		frappe.throw("All invoices for this booking are already fully paid.")

	company = frappe.db.get_single_value("Global Defaults", "default_company")
	mop = frappe.get_doc("Mode of Payment", data.payment_mode)

	if not mop.accounts:
		frappe.throw("Mode of Payment has no accounts configured.")

	mop_account = next((a.default_account for a in mop.accounts if a.company == company), None)

	if not mop_account:
		frappe.throw("No account found for Mode of Payment in {0}".format(company))

	existing_pe = frappe.db.get_value("Payment Entry", {"reference_no": data.reference_no})
	if existing_pe:
		frappe.throw("A Payment Entry with this reference number already exists.")

	paid_amount = flt(data.paid_amount)
	remaining_amount = paid_amount
	references = []

	for inv in unpaid_invoices:
		if remaining_amount <= 0:
			break

		allocated = min(remaining_amount, flt(inv.outstanding_amount))

		references.append({
			"reference_doctype": "Sales Invoice",
			"reference_name": inv.name,
			"allocated_amount": allocated,
		})

		remaining_amount -= allocated

	if not references:
		frappe.throw("No outstanding invoice found for this booking.")

	pe = frappe.get_doc({
		"doctype": "Payment Entry",
		"payment_type": "Receive",
		"company": company,
		"posting_date": data.payment_date,
		"party_type": "Customer",
		"party": unpaid_invoices[0].customer,
		"mode_of_payment": data.payment_mode,
		"paid_to": mop_account,
		"paid_amount": paid_amount,
		"received_amount": paid_amount,
		"reference_no": data.reference_no,
		"reference_date": data.reference_date,
		"remarks": data.remarks,
		"references": references,
	})

	pe.insert(ignore_permissions=True)
	pe.submit()

	return pe.name

@frappe.whitelist()
def create_invoice_for_booking(booking_name):
	booking = frappe.get_doc("Hall Booking", booking_name)

	if booking.docstatus != 1:
		frappe.throw("Only submitted bookings can be invoiced.")

	if booking.sales_invoice:
		frappe.throw("Invoice already exists for this booking.")

	booking.create_invoice()

	return {
		"name": booking.name,
		"sales_invoice": booking.sales_invoice
	}


def _reprice_hall_invoice(invoice_name, hall_item_code, qty, day_rate, discount_type, discount_amount):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)

	if invoice.docstatus != 1:
		frappe.throw("Invoice {0} is not submitted.".format(invoice_name))

	if flt(invoice.outstanding_amount or 0) != flt(invoice.grand_total or 0):
		frappe.throw(
			"Invoice {0} already has payment. Reverse payment before repair.".format(invoice_name)
		)

	hall_row = None
	for row in invoice.get("items", []):
		if row.item_code == hall_item_code:
			hall_row = row
			break

	if not hall_row and invoice.get("items"):
		hall_row = invoice.items[0]

	if not hall_row:
		frappe.throw("Invoice {0} has no items to repair.".format(invoice_name))

	qty = flt(qty or 0)
	day_rate = flt(day_rate or 0)
	gross_total = abs(qty) * day_rate
	discount_value = _discount_value(gross_total, discount_type, discount_amount)
	net_total = max(0, gross_total - discount_value)
	net_rate = (net_total / abs(qty)) if qty else 0

	hall_row.qty = qty
	hall_row.price_list_rate = day_rate
	hall_row.rate = net_rate
	hall_row.discount_percentage = _line_discount_percentage(gross_total, discount_value)
	hall_row.discount_amount = max(0, day_rate - net_rate)

	invoice.flags.ignore_validate_update_after_submit = True
	invoice.set_missing_values()
	invoice.calculate_taxes_and_totals()
	invoice.save(ignore_permissions=True)
	invoice.reload()

	return {
		"invoice": invoice.name,
		"grand_total": flt(invoice.grand_total or 0),
		"outstanding_amount": flt(invoice.outstanding_amount or 0),
	}


@frappe.whitelist()
def repair_booking_invoice_discounts(booking_name):
	booking = frappe.get_doc("Hall Booking", booking_name)
	hall = frappe.get_doc("Hall", booking.hall)
	hall_item_code = hall.item_name or booking.hall
	day_rate = flt(hall.rate or booking.rate or 0)

	history_rows = sorted(
		list(booking.get("adjustment_history", [])),
		key=lambda r: flt(r.idx or 0),
	)

	if history_rows:
		original_days = flt(history_rows[0].previous_days or 0)
	else:
		original_days = flt(booking.total_days or 0)

	if original_days <= 0:
		original_days = 1

	repaired = []
	total_grand = 0
	total_outstanding = 0

	if booking.sales_invoice:
		result = _reprice_hall_invoice(
			booking.sales_invoice,
			hall_item_code,
			original_days,
			day_rate,
			booking.discount_type,
			booking.discount_amount,
		)
		repaired.append(result)
		total_grand += flt(result.get("grand_total") or 0)
		total_outstanding += flt(result.get("outstanding_amount") or 0)

	for row in history_rows:
		if not row.adjustment_invoice:
			continue

		diff_days = abs(flt(row.new_days or 0) - flt(row.previous_days or 0))
		if diff_days <= 0:
			continue

		qty = diff_days if flt(row.new_days or 0) > flt(row.previous_days or 0) else -diff_days
		result = _reprice_hall_invoice(
			row.adjustment_invoice,
			hall_item_code,
			qty,
			day_rate,
			row.discount_type,
			row.discount_amount,
		)
		repaired.append(result)
		total_grand += flt(result.get("grand_total") or 0)
		total_outstanding += flt(result.get("outstanding_amount") or 0)

	booking.flags.ignore_validate_update_after_submit = True
	booking.net_total = flt(max(0, total_grand), 2)
	booking.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"booking": booking.name,
		"booking_net_total": flt(booking.net_total or 0),
		"total_invoice_amount": flt(total_grand or 0),
		"total_outstanding": flt(total_outstanding or 0),
		"repaired_invoices": repaired,
	}