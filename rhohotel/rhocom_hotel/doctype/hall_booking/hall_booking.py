# Copyright (c) 2025, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import json
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, nowdate


class HallBooking(Document):
	def validate(self):
		self.validate_booking_overlap()
		self.set_totals()

		for row in self.additional_billings:
			if row.discount_amount and row.discount_amount > (row.qty * row.rate):
				frappe.throw("Discount cannot be greater than amount for service {0}".format(row.service))

	def on_submit(self):
		self.create_customer_if_not_exists()
		self.create_invoice()

	def set_totals(self):
		start_dt = get_datetime(self.start_datetime)
		end_dt = get_datetime(self.end_datetime)

		if end_dt <= start_dt:
			frappe.throw("End Date must be after Start Date.")

		self.total_days = max(1, math.ceil((end_dt - start_dt).total_seconds() / 86400))
		self.total_amount = flt(self.rate or 0) * self.total_days

		additional_total = 0
		for row in self.get("additional_billings", []):
			row.qty = flt(row.qty or 1)
			row.rate = flt(row.rate or 0)
			row.discount_amount = flt(row.discount_amount or 0)
			row.amount = (row.qty * row.rate) - row.discount_amount
			additional_total += flt(row.amount)

		gross_total = flt(self.total_amount) + additional_total
		discount = flt(self.discount_amount or 0)

		if discount > 0:
			if self.discount_type == "Percentage":
				discount = gross_total * (discount / 100)

			gross_total -= discount

		self.net_total = max(0, gross_total)

	def validate_booking_overlap(self):
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
				"hall": self.hall,
				"name": self.name or "",
				"start": self.start_datetime,
				"end": self.end_datetime,
			},
			as_dict=True,
		)

		if overlapping_bookings:
			frappe.throw(
				"Hall '{0}' is already booked between {1} and {2}.".format(
					self.hall, self.start_datetime, self.end_datetime
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

		total_amount = flt(hall.rate or 0) * flt(self.total_days or 1)

		invoice = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": self.customer_name,
			"posting_date": getdate(self.end_datetime),
			"due_date": getdate(self.end_datetime),
			"set_posting_time": 1,
			"company": company,
			"items": [
				{
					"item_code": hall.item_name or self.hall,
					"rate": hall.rate,
					"qty": self.total_days,
					"amount": total_amount,
					"income_account": default_income,
					"cost_center": cost_center,
					"discount_amount": 0.0,
				}
			],
		})

		for billing in self.get("additional_billings", []):
			invoice.append("items", {
				"item_code": billing.service,
				"rate": billing.rate,
				"qty": billing.qty,
				"amount": billing.amount,
				"income_account": default_income,
				"cost_center": cost_center,
				"discount_amount": billing.discount_amount or 0.0,
			})

		invoice.set_taxes()

		if self.discount_amount and self.discount_amount > 0:
			if self.discount_type == "Percentage":
				invoice.additional_discount_percentage = self.discount_amount
			else:
				invoice.discount_amount = self.discount_amount

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
def adjust_booking_datetime(booking_name, start_datetime, end_datetime, reason=None):
	booking = frappe.get_doc("Hall Booking", booking_name)

	if booking.docstatus != 1:
		frappe.throw("Only submitted bookings can be adjusted.")

	start_dt = get_datetime(start_datetime)
	end_dt = get_datetime(end_datetime)

	if end_dt <= start_dt:
		frappe.throw("End date must be after start date.")

	new_total_days = max(1, math.ceil((end_dt - start_dt).total_seconds() / 86400))
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
		frappe.throw("Hall '{0}' is already booked between {1} and {2}.".format(
			booking.hall, start_dt, end_dt
		))

	hall = frappe.get_doc("Hall", booking.hall)
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	income_account = frappe.db.get_value("Company", company, "default_income_account")
	cost_center = frappe.db.get_value("Company", company, "cost_center")

	adjustment_invoice = None
	new_net_total = flt(booking.net_total or 0)

	if new_total_days != previous_total_days:
		diff_days = abs(new_total_days - previous_total_days)
		qty = diff_days if new_total_days > previous_total_days else -diff_days

		invoice_data = {
			"doctype": "Sales Invoice",
			"customer": booking.customer_name,
			"posting_date": nowdate(),
			"company": company,
			"items": [
				{
					"item_code": hall.item_name or booking.hall,
					"rate": hall.rate,
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
	})

	booking.start_datetime = start_dt
	booking.end_datetime = end_dt
	booking.total_days = new_total_days
	booking.total_amount = flt(hall.rate or 0) * new_total_days
	booking.net_total = new_net_total

	booking.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"previous_days": previous_total_days,
		"new_days": new_total_days,
		"adjustment_invoice": adjustment_invoice,
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