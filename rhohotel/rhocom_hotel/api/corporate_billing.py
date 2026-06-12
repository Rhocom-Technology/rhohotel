import frappe
from frappe.utils import getdate, nowdate, flt, format_date, today as frappe_today


def _billing_status(grand_total, outstanding, due_date):
	outstanding = flt(outstanding)
	grand_total = flt(grand_total)

	if outstanding <= 0:
		return "Paid"

	if due_date and getdate(due_date) < getdate(nowdate()):
		return "Overdue"

	if outstanding < grand_total:
		return "Part Paid"

	return "Unpaid"


def _fmt_currency(amount):
	amount = flt(amount)
	if amount == 0:
		return "₦0.00"
	formatted = "{:,.0f}".format(amount)
	return "₦" + formatted


def _fmt_date(d):
	if not d:
		return ""
	try:
		return format_date(d, "dd MMM yyyy")
	except Exception:
		return str(d)


def _fmt_period(d):
	if not d:
		return ""
	try:
		dt = getdate(d)
		months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
		          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		return "{} {}".format(months[dt.month - 1], dt.year)
	except Exception:
		return str(d)


def _bill_action(status):
	if status == "Overdue":
		return "Follow Up"
	if status == "Paid":
		return "Print"
	return "View"


@frappe.whitelist()
def get_corporate_bills(search=None, client=None, status=None, page=1, page_size=25):
	try:
		page = int(page or 1)
	except Exception:
		page = 1

	try:
		page_size = int(page_size or 25)
	except Exception:
		page_size = 25

	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return {
			"bills": [],
			"customers": [],
			"total": 0,
			"page": page,
			"page_size": page_size,
			"total_pages": 1,
			"summary": {
				"activeBills": 0,
				"outstandingValue": "₦0.00",
				"paidThisMonth": "₦0.00",
				"overdueCount": 0,
			},
		}

	conditions = [
		"si.docstatus = 1",
		"si.customer IN %(corporate_customers)s",
	]

	params = {
		"corporate_customers": tuple(corporate_customers),
	}

	if search:
		conditions.append(
			"(si.name LIKE %(search)s OR si.customer_name LIKE %(search)s OR si.customer LIKE %(search)s)"
		)
		params["search"] = "%{}%".format(search)

	if client:
		conditions.append("(si.customer_name = %(client)s OR si.customer = %(client)s)")
		params["client"] = client

	sql = """
		SELECT
			si.name,
			si.customer,
			si.customer_name,
			si.posting_date,
			si.due_date,
			si.grand_total,
			si.outstanding_amount,
			si.remarks
		FROM `tabSales Invoice` si
		WHERE {conditions}
		ORDER BY si.posting_date DESC, si.name DESC
	""".format(conditions=" AND ".join(conditions))

	invoices = frappe.db.sql(sql, params, as_dict=True)

	bills = []

	for inv in invoices:
		grand_total = flt(inv.grand_total)
		outstanding = flt(inv.outstanding_amount)
		computed_status = _billing_status(grand_total, outstanding, inv.due_date)

		if status and computed_status != status:
			continue

		bills.append({
			"billNo": inv.name,
			"client": inv.customer_name or inv.customer or "",
			"client_id": inv.customer or "",
			"clientNote": inv.remarks or "",
			"period": _fmt_period(inv.posting_date),
			"issueDate": _fmt_date(inv.posting_date),
			"dueDate": _fmt_date(inv.due_date),
			"amount": _fmt_currency(grand_total),
			"balance": _fmt_currency(outstanding),
			"status": computed_status,
			"action": _bill_action(computed_status),
		})

	total_outstanding = sum(flt(inv.outstanding_amount) for inv in invoices)

	overdue_count = sum(
		1 for inv in invoices
		if _billing_status(inv.grand_total, inv.outstanding_amount, inv.due_date) == "Overdue"
	)

	today = nowdate()
	month_start = "{}-{}-01".format(today[:4], today[5:7])

	paid_this_month_sql = """
		SELECT COALESCE(SUM(per.allocated_amount), 0)
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON per.parent = pe.name
		JOIN `tabSales Invoice` si ON per.reference_name = si.name
		WHERE per.reference_doctype = 'Sales Invoice'
		  AND pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		  AND pe.posting_date >= %(month_start)s
		  AND si.customer IN %(corporate_customers)s
	"""

	paid_this_month = flt(
		frappe.db.sql(
			paid_this_month_sql,
			{
				"month_start": month_start,
				"corporate_customers": tuple(corporate_customers),
			}
		)[0][0] or 0
	)

	summary = {
		"activeBills": len([b for b in bills if b["status"] in ("Unpaid", "Part Paid", "Overdue")]),
		"outstandingValue": _fmt_currency(total_outstanding),
		"paidThisMonth": _fmt_currency(paid_this_month),
		"overdueCount": overdue_count,
	}

	total = len(bills)
	start = (page - 1) * page_size
	end = start + page_size
	total_pages = max(1, int((total + page_size - 1) / page_size))

	return {
		"bills": bills[start:end],
		"customers": _get_customers(),
		"total": total,
		"page": page,
		"page_size": page_size,
		"total_pages": total_pages,
		"summary": summary,
	}

@frappe.whitelist()
def get_corporate_bill_detail(invoice_name):
	"""Return full detail for a single corporate Sales Invoice."""
	if not invoice_name:
		frappe.throw("Invoice name is required")

	inv = frappe.get_doc("Sales Invoice", invoice_name)

	grand_total = flt(inv.grand_total)
	outstanding = flt(inv.outstanding_amount)
	computed_status = _billing_status(grand_total, outstanding, inv.due_date)

	# Charge breakdown from invoice items
	charges = []
	for item in (inv.items or []):
		charges.append({
			"desc": item.description or item.item_name or item.item_code or "",
			"date": _fmt_date(getattr(item, "delivery_date", None) or inv.posting_date),
			"guests": str(int(flt(item.qty))) if flt(item.qty) else "—",
			"amount": _fmt_currency(flt(item.amount)),
		})

	# Payment history from Payment Entry References
	payment_rows = frappe.db.sql(
		"""
		SELECT
			pe.name AS receipt,
			per.allocated_amount AS amount,
			pe.mode_of_payment AS method,
			pe.posting_date AS date,
			pe.reference_no AS reference
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON per.parent = pe.name
		WHERE per.reference_doctype = 'Sales Invoice'
		  AND per.reference_name = %(inv)s
		  AND pe.docstatus = 1
		ORDER BY pe.posting_date ASC, pe.creation ASC
		""",
		{"inv": invoice_name},
		as_dict=True,
	)

	payments = []
	for row in payment_rows:
		payments.append({
			"receipt": row.receipt or "",
			"amount": _fmt_currency(flt(row.amount)),
			"method": row.method or "—",
			"date": _fmt_date(row.date),
			"reference": row.reference or "—",
		})

	# Audit trail from Document Comments
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Sales Invoice",
			"reference_name": invoice_name,
			"comment_type": ["in", ["Comment", "Workflow", "Label", "Submitted", "Cancelled", "Created", "Info", "Edit"]],
		},
		fields=["content", "owner", "creation"],
		order_by="creation asc",
		limit=20,
	)

	audit = []
	for c in comments:
		audit.append({
			"action": (c.content or "").replace("<[^>]+>", "").strip() or "Activity recorded",
			"by": frappe.db.get_value("User", c.owner, "full_name") or c.owner or "System",
			"at": _fmt_date(c.creation) if c.creation else "",
		})

	if not audit:
		audit.append({
			"action": "Invoice created",
			"by": frappe.db.get_value("User", inv.owner, "full_name") or inv.owner or "System",
			"at": _fmt_date(inv.creation),
		})

	bill = {
		"billNo": inv.name,
		"client": inv.customer_name or inv.customer or "",
		"clientNote": inv.remarks or "",
		"period": _fmt_period(inv.posting_date),
		"issueDate": _fmt_date(inv.posting_date),
		"dueDate": _fmt_date(inv.due_date),
		"amount": _fmt_currency(grand_total),
		"balance": _fmt_currency(outstanding),
		"status": computed_status,
		"charges": charges,
		"payments": payments,
		"audit": audit,
	}

	return bill


@frappe.whitelist()
def record_corporate_payment(
	invoice_name,
	mode_of_payment,
	paid_amount,
	payment_date=None,
	reference_no=None,
	reference_date=None,
	remarks=None,
):
	"""Create and submit a Payment Entry for a corporate Sales Invoice."""
	if not invoice_name:
		frappe.throw("Invoice name is required")
	if not mode_of_payment:
		frappe.throw("Mode of payment is required")

	paid_amount = flt(paid_amount)
	if paid_amount <= 0:
		frappe.throw("Payment amount must be greater than zero")

	inv = frappe.get_doc("Sales Invoice", invoice_name)
	if inv.docstatus != 1:
		frappe.throw("Invoice must be submitted before recording payment")

	outstanding = flt(inv.outstanding_amount)
	if outstanding <= 0:
		frappe.throw("This invoice has no outstanding balance")

	allocated = min(paid_amount, outstanding)

	company = inv.company or frappe.db.get_single_value("Global Defaults", "default_company")

	mop = frappe.get_doc("Mode of Payment", mode_of_payment)
	if not mop.accounts:
		frappe.throw("Mode of Payment has no accounts configured")

	mop_account = next((a.default_account for a in mop.accounts if a.company == company), None)
	if not mop_account:
		frappe.throw("No account found for Mode of Payment in company {}".format(company))

	receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")
	if not receivable_account:
		frappe.throw("Default Receivable Account is not set for the company")

	if reference_no:
		existing = frappe.db.get_value("Payment Entry", {"reference_no": reference_no})
		if existing:
			frappe.throw("A Payment Entry with this reference number already exists")

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.party_type = "Customer"
	pe.party = inv.customer
	pe.paid_from = receivable_account
	pe.paid_from_account_type = "Receivable"
	pe.paid_to = mop_account
	pe.posting_date = payment_date or frappe_today()
	pe.paid_amount = allocated
	pe.received_amount = allocated
	pe.source_exchange_rate = 1
	pe.target_exchange_rate = 1
	pe.company = company
	pe.mode_of_payment = mode_of_payment
	if reference_no:
		pe.reference_no = reference_no
	if reference_date:
		pe.reference_date = reference_date
	if remarks:
		pe.remarks = remarks

	pe.append("references", {
		"reference_doctype": "Sales Invoice",
		"reference_name": invoice_name,
		"allocated_amount": allocated,
	})

	pe.insert(ignore_permissions=True)
	try:
		pe.submit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Corporate payment submit failed")

	check_in = inv.get("custom_hotel_room_check_in")
	if check_in:
		try:
			from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

			new_outstanding = (sync_checkin_folio_totals(check_in).get("summary") or {}).get("balance_amount", 0)
			frappe.db.set_value(
				"Hotel Room Check In",
				check_in,
				"total_outstanding_amount",
				new_outstanding,
				update_modified=False,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after invoice payment")

	frappe.db.commit()
	return {"payment_entry": pe.name}


@frappe.whitelist()
def get_payment_modes():
	"""Return list of active modes of payment."""
	return frappe.get_all("Mode of Payment", filters={"enabled": 1}, fields=["name"], order_by="name asc")

def _get_corporate_customers():
	if not frappe.db.exists("DocType", "Hotel Guest"):
		return []

	rows = frappe.db.sql(
		"""
		SELECT DISTINCT customer
		FROM `tabHotel Guest`
		WHERE guest_type = 'Corporate'
		  AND IFNULL(customer, '') != ''
		""",
		as_dict=True,
	)

	return [row.customer for row in rows if row.customer]

# def _get_customers():
# 	corporate_customers = _get_corporate_customers()

# 	if not corporate_customers:
# 		return []

# 	return frappe.db.sql(
# 		"""
# 		SELECT
# 			name,
# 			customer_name
# 		FROM `tabCustomer`
# 		WHERE name IN %(customers)s
# 		ORDER BY customer_name ASC, name ASC
# 		""",
# 		{
# 			"customers": tuple(corporate_customers)
# 		},
# 		as_dict=True,
# 	)

def _get_customers():
	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return []

	return frappe.db.sql(
		"""
		SELECT DISTINCT
			c.name,
			c.customer_name
		FROM `tabCustomer` c
		JOIN `tabSales Invoice` si
			ON si.customer = c.name
		WHERE c.name IN %(customers)s
		  AND si.docstatus = 1
		ORDER BY c.customer_name ASC, c.name ASC
		""",
		{
			"customers": tuple(corporate_customers)
		},
		as_dict=True,
	)