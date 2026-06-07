# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import json
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, nowdate, date_diff
import math

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

		overlapping_bookings = frappe.db.sql(
			"""
			SELECT
				name,
				customer_name,
				hall,
				start_datetime,
				end_datetime
			FROM `tabHall Booking`
			WHERE hall = %(hall)s
			AND docstatus = 1
			AND name != %(name)s
			AND (
					%(start)s < end_datetime
				AND %(end)s > start_datetime
			)
			""",
			{
				"hall": self.hall,
				"name": self.name or "",
				"start": self.start_datetime,
				"end": self.end_datetime,
			},
			as_dict=True,
		)

		if overlapping_bookings:
			conflict = overlapping_bookings[0]

			frappe.throw(
				(
					"Hall '{hall}' is not available for the selected time.<br><br>"
					"<b>Conflicting Booking:</b> {booking}<br>"
					"<b>Customer:</b> {customer}<br>"
					"<b>Booked From:</b> {start}<br>"
					"<b>Booked To:</b> {end}"
				).format(
					hall=self.hall,
					booking=conflict.name,
					customer=conflict.customer_name or "N/A",
					start=frappe.format(
						conflict.start_datetime,
						{"fieldtype": "Datetime"}
					),
					end=frappe.format(
						conflict.end_datetime,
						{"fieldtype": "Datetime"}
					),
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

		if flt(self.discount_amount or 0) > 0:
			if self.discount_type == "Percentage":
				if flt(self.discount_amount) > 100:
					frappe.throw("Hall discount percentage cannot be greater than 100%.")

				hall_net = hall_gross - (hall_gross * flt(self.discount_amount) / 100)

			else:
				if flt(self.discount_amount) > hall_gross:
					frappe.throw("Hall discount cannot be greater than hall amount.")

				hall_net = hall_gross - flt(self.discount_amount)

		hall_net = max(0, hall_net)

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
			"rate": hall_net / hall_qty,
			"income_account": default_income,
			"cost_center": cost_center,
		})

		for billing in self.get("additional_billings", []):
			qty = flt(billing.qty or 1)
			net_amount = flt(billing.amount or 0)

			invoice.append("items", {
				"item_code": billing.service,
				"qty": qty,
				"rate": net_amount / qty,
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

	if not booking.sales_invoice:
		frappe.throw("Please create the main invoice before adjusting this booking.")

	start_dt = get_datetime(start_datetime)
	end_dt = get_datetime(end_datetime)

	if end_dt <= start_dt:
		frappe.throw("End date must be after start date.")

	new_total_days = max(1, date_diff(getdate(end_dt), getdate(start_dt)) + 1)
	previous_total_days = flt(booking.total_days or 0)

	overlapping_bookings = frappe.db.sql(
		"""
		SELECT name
		FROM `tabHall Booking`
		WHERE hall = %(hall)s
		  AND docstatus = 1
		  AND name != %(name)s
		  AND (
			  %(start)s < end_datetime
			  AND %(end)s > start_datetime
		  )
		""",
		{
			"hall": booking.hall,
			"name": booking.name or "",
			"start": start_dt,
			"end": end_dt,
		},
		as_dict=True,
	)

	if overlapping_bookings:
		frappe.throw(
			"Hall '{0}' is already booked between {1} and {2}.".format(
				booking.hall, start_dt, end_dt
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
		net_rate = net_adjustment / diff_days if diff_days else 0

		invoice_data = {
			"doctype": "Sales Invoice",
			"customer": booking.customer_name,
			"posting_date": nowdate(),
			"company": company,
			"items": [
				{
					"item_code": hall.item_name or booking.hall,
					"rate": net_rate,
					"qty": qty,
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