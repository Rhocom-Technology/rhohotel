import frappe
from frappe.utils import getdate, nowdate, add_days, date_diff, flt


def _date_or_default(value, default_value):
	try:
		return getdate(value) if value else getdate(default_value)
	except Exception:
		return getdate(default_value)


def _has_doctype(doctype):
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		return False


def _has_column(doctype, column):
	try:
		return bool(frappe.db.has_column(doctype, column))
	except Exception:
		return False


def _get_field(doctype, candidates):
	for field in candidates:
		if _has_column(doctype, field):
			return field
	return None


def _paginate(data, page=1, page_size=10):
	try:
		page = int(page or 1)
	except Exception:
		page = 1

	try:
		page_size = int(page_size or 10)
	except Exception:
		page_size = 10

	if page < 1:
		page = 1

	if page_size < 1:
		page_size = 10

	total = len(data)
	total_pages = int((total + page_size - 1) / page_size) if total else 1

	if page > total_pages:
		page = total_pages

	start = (page - 1) * page_size
	end = start + page_size

	return {
		"rows": data[start:end],
		"total": total,
		"page": page,
		"page_size": page_size,
		"total_pages": total_pages,
	}


def _aging_bucket(days):
	days = int(days or 0)

	if days <= 0:
		return "Current"
	if days <= 30:
		return "1-30"
	if days <= 60:
		return "31-60"
	if days <= 90:
		return "61-90"

	return "90+"


def _billing_status(outstanding, due_date):
	outstanding = flt(outstanding)

	if outstanding <= 0:
		return "Paid"

	if due_date and getdate(due_date) < getdate(nowdate()):
		return "Overdue"

	return "Unpaid"


def _get_payment_amount(invoice_name):
	if not invoice_name:
		return 0

	try:
		if _has_doctype("Payment Entry Reference"):
			paid = (
				frappe.db.sql(
					"""
				SELECT SUM(allocated_amount)
				FROM `tabPayment Entry Reference`
				WHERE reference_doctype = 'Sales Invoice'
				  AND reference_name = %s
				""",
					(invoice_name,),
				)[0][0]
				or 0
			)

			return flt(paid)
	except Exception:
		pass

	return 0


@frappe.whitelist()
def get_corporate_billing_statement(
	date_from=None,
	date_to=None,
	company=None,
	status=None,
	aging_bucket=None,
	search=None,
	company_page=1,
	company_page_size=10,
	aging_page=1,
	aging_page_size=10,
	company_summary_search=None,
	company_summary_status=None,
	company_summary_min_outstanding=None,
):
	date_from = _date_or_default(date_from, add_days(nowdate(), -30))
	date_to = _date_or_default(date_to, nowdate())

	rows = []
	companies = set()

	def empty_response():
		return {
			"rows": [],
			"companies": [],
			"company_summary": [],
			"company_summary_total": 0,
			"company_summary_page": 1,
			"company_summary_page_size": int(company_page_size or 10),
			"company_summary_total_pages": 1,
			"aging_breakdown": [],
			"aging_breakdown_total": 0,
			"aging_breakdown_page": 1,
			"aging_breakdown_page_size": int(aging_page_size or 10),
			"aging_breakdown_total_pages": 1,
			"summary": {
				"total_billing": 0,
				"total_paid": 0,
				"outstanding": 0,
				"overdue": 0,
				"invoice_count": 0,
				"company_count": 0,
			},
		}

	if not _has_doctype("Sales Invoice"):
		return empty_response()

	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return empty_response()

	customer_field = _get_field("Sales Invoice", ["customer"])
	customer_name_field = _get_field("Sales Invoice", ["customer_name"])
	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
	due_date_field = _get_field("Sales Invoice", ["due_date"])
	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
	outstanding_field = _get_field("Sales Invoice", ["outstanding_amount"])
	paid_field = _get_field("Sales Invoice", ["paid_amount"])
	is_return_field = _get_field("Sales Invoice", ["is_return"])
	remarks_field = _get_field("Sales Invoice", ["remarks", "custom_reference", "po_no"])

	guest_field = _get_field(
		"Sales Invoice",
		[
			"custom_guest",
			"guest",
			"guest_name",
			"custom_guest_name",
			"customer_name",
		],
	)

	company_field = _get_field(
		"Sales Invoice",
		[
			"custom_corporate_company",
			"corporate_company",
			"custom_company_name",
			"company_name",
			"customer",
		],
	)

	conditions = ["docstatus = 1"]
	params = {}

	if posting_date_field:
		conditions.append("{0} BETWEEN %(date_from)s AND %(date_to)s".format(posting_date_field))
		params["date_from"] = date_from
		params["date_to"] = date_to

	if customer_field:
		conditions.append("{0} IN %(corporate_customers)s".format(customer_field))
		params["corporate_customers"] = tuple(corporate_customers)

	if company and customer_field:
		conditions.append("{0} = %(company)s".format(customer_field))
		params["company"] = company

	if search:
		search_fields = ["name"]

		for field in [
			customer_field,
			customer_name_field,
			guest_field,
			company_field,
			remarks_field,
		]:
			if field and field not in search_fields:
				search_fields.append(field)

		search_sql = []

		for field in search_fields:
			search_sql.append("{0} LIKE %(search)s".format(field))

		conditions.append("(" + " OR ".join(search_sql) + ")")
		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]

	for field in [
		posting_date_field,
		due_date_field,
		customer_field,
		customer_name_field,
		guest_field,
		company_field,
		grand_total_field,
		paid_field,
		outstanding_field,
		is_return_field,
		remarks_field,
	]:
		if field and field not in select_fields:
			select_fields.append(field)

	sql = """
		SELECT {fields}
		FROM `tabSales Invoice`
		WHERE {conditions}
		ORDER BY {date_field} DESC, name DESC
	""".format(
		fields=", ".join(select_fields),
		conditions=" AND ".join(conditions),
		date_field=posting_date_field or "creation",
	)

	invoices = frappe.db.sql(sql, params, as_dict=True)

	for inv in invoices:
		invoice_name = inv.get("name")
		invoice_date = inv.get(posting_date_field) if posting_date_field else ""
		due_date = inv.get(due_date_field) if due_date_field else ""

		raw_billed_amount = flt(inv.get(grand_total_field)) if grand_total_field else 0
		is_return = bool(inv.get(is_return_field)) if is_return_field else raw_billed_amount < 0
		billed_amount = -abs(raw_billed_amount) if is_return else raw_billed_amount

		if is_return:
			paid_amount = 0
		elif paid_field:
			paid_amount = flt(inv.get(paid_field))
		else:
			paid_amount = _get_payment_amount(invoice_name)

		if outstanding_field:
			raw_outstanding = flt(inv.get(outstanding_field))
			outstanding_amount = -abs(raw_outstanding) if is_return else raw_outstanding
		else:
			outstanding_amount = billed_amount - paid_amount

		customer = inv.get(customer_field) if customer_field else ""
		customer_name = inv.get(customer_name_field) if customer_name_field else ""
		raw_company = inv.get(company_field) if company_field else ""

		company_name = customer_name or raw_company or customer or "Unknown"

		guest = ""
		if guest_field:
			guest = inv.get(guest_field) or ""

		if not guest:
			guest = customer_name or customer or ""

		reference = ""
		if remarks_field:
			reference = inv.get(remarks_field) or ""

		days_overdue = 0

		if due_date:
			days_overdue = date_diff(nowdate(), due_date)

		bucket = _aging_bucket(days_overdue)
		computed_status = _billing_status(outstanding_amount, due_date)

		if status and computed_status != status:
			continue

		if aging_bucket and bucket != aging_bucket:
			continue

		companies.add(customer)

		rows.append(
			{
				"invoice": invoice_name,
				"date": str(invoice_date) if invoice_date else "",
				"company": company_name,
				"customer": customer,
				"guest": guest,
				"reference": reference,
				"due_date": str(due_date) if due_date else "",
				"billed_amount": billed_amount,
				"paid_amount": paid_amount,
				"outstanding_amount": outstanding_amount,
				"is_return": 1 if is_return else 0,
				"aging_bucket": bucket,
				"status": computed_status,
			}
		)

	total_billing = sum(flt(row.get("billed_amount")) for row in rows)
	total_paid = sum(flt(row.get("paid_amount")) for row in rows)
	total_outstanding = sum(flt(row.get("outstanding_amount")) for row in rows)
	total_overdue = sum(
		flt(row.get("outstanding_amount"))
		for row in rows
		if row.get("status") == "Overdue"
	)

	company_map = {}

	for row in rows:
		customer_id = row.get("customer") or row.get("company") or "Unknown"
		company_name = row.get("company") or customer_id

		if customer_id not in company_map:
			company_map[customer_id] = {
				"company": company_name,
				"customer": customer_id,
				"invoices": 0,
				"billed": 0,
				"paid": 0,
				"outstanding": 0,
				"status": "Paid",
			}

		company_map[customer_id]["invoices"] += 1
		company_map[customer_id]["billed"] += flt(row.get("billed_amount"))
		company_map[customer_id]["paid"] += flt(row.get("paid_amount"))
		company_map[customer_id]["outstanding"] += flt(row.get("outstanding_amount"))

	for customer_id in company_map:
		if company_map[customer_id]["outstanding"] > 0:
			company_map[customer_id]["status"] = "Outstanding"

	company_summary = list(company_map.values())

	if company_summary_search:
		q = str(company_summary_search).lower()
		company_summary = [
			item for item in company_summary
			if q in str(item.get("company") or "").lower()
			or q in str(item.get("customer") or "").lower()
		]

	if company_summary_status == "Outstanding":
		company_summary = [
			item for item in company_summary
			if flt(item.get("outstanding")) > 0
		]
	elif company_summary_status == "Paid":
		company_summary = [
			item for item in company_summary
			if flt(item.get("outstanding")) <= 0
		]

	if company_summary_min_outstanding:
		company_summary = [
			item for item in company_summary
			if flt(item.get("outstanding")) >= flt(company_summary_min_outstanding)
		]

	company_summary = sorted(
		company_summary,
		key=lambda x: flt(x.get("outstanding")),
		reverse=True
	)

	aging_map = {}

	for row in rows:
		bucket = row.get("aging_bucket") or "Current"
		aging_map[bucket] = aging_map.get(bucket, 0) + flt(row.get("outstanding_amount"))

	aging_breakdown = sorted(
		[
			{"bucket": bucket, "amount": amount}
			for bucket, amount in aging_map.items()
		],
		key=lambda x: flt(x.get("amount")),
		reverse=True,
	)

	company_summary_page = _paginate(
		company_summary,
		company_page,
		company_page_size
	)

	aging_breakdown_page = _paginate(
		aging_breakdown,
		aging_page,
		aging_page_size
	)

	return {
		"rows": rows,
		"companies": sorted(list(companies)),
		"company_summary": company_summary_page["rows"],
		"company_summary_total": company_summary_page["total"],
		"company_summary_page": company_summary_page["page"],
		"company_summary_page_size": company_summary_page["page_size"],
		"company_summary_total_pages": company_summary_page["total_pages"],
		"aging_breakdown": aging_breakdown_page["rows"],
		"aging_breakdown_total": aging_breakdown_page["total"],
		"aging_breakdown_page": aging_breakdown_page["page"],
		"aging_breakdown_page_size": aging_breakdown_page["page_size"],
		"aging_breakdown_total_pages": aging_breakdown_page["total_pages"],
		"summary": {
			"total_billing": total_billing,
			"total_paid": total_paid,
			"outstanding": total_outstanding,
			"overdue": total_overdue,
			"invoice_count": len(rows),
			"company_count": len(company_map),
		},
	}

def _get_corporate_customers():
    if not _has_doctype("Hotel Guest"):
        return []

    guest_type_field = _get_field("Hotel Guest", ["guest_type"])
    customer_field = _get_field("Hotel Guest", ["customer"])

    if not guest_type_field or not customer_field:
        return []

    rows = frappe.db.sql(
        """
        SELECT DISTINCT `{customer_field}` AS customer
        FROM `tabHotel Guest`
        WHERE `{guest_type_field}` = 'Corporate'
          AND IFNULL(`{customer_field}`, '') != ''
        """.format(
            customer_field=customer_field,
            guest_type_field=guest_type_field
        ),
        as_dict=True
    )

    return [row.customer for row in rows if row.customer]
