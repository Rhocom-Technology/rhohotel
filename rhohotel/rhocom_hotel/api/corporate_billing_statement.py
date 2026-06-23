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


def _billing_status(outstanding, due_date, as_of_date=None):
	outstanding = flt(outstanding)

	if outstanding <= 0:
		return "Paid"

	compare_date = getdate(as_of_date) if as_of_date else getdate(nowdate())

	if due_date and getdate(due_date) < compare_date:
		return "Overdue"

	return "Unpaid"


def _get_customer_name_map(customers):
	if not customers:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT name, customer_name
		FROM `tabCustomer`
		WHERE name IN %(customers)s
		""",
		{"customers": tuple(customers)},
		as_dict=True,
	)

	return {row.get("name"): (row.get("customer_name") or row.get("name")) for row in rows}


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

	customer_name_map = _get_customer_name_map(corporate_customers)

	ple_conditions = [
		"ple.docstatus = 1",
		"ple.account_type = 'Receivable'",
		"ple.party_type = 'Customer'",
		"ple.delinked = 0",
		"ple.posting_date BETWEEN %(date_from)s AND %(date_to)s",
		"ple.party IN %(corporate_customers)s",
	]

	params = {
		"date_from": str(date_from),
		"date_to": str(date_to),
		"corporate_customers": tuple(corporate_customers),
	}

	if company:
		ple_conditions.append("ple.party = %(company)s")
		params["company"] = company

	voucher_rows = frappe.db.sql(
		"""
		SELECT
			agg.customer,
			agg.target_voucher AS invoice,
			agg.posting_date,
			agg.billed_amount,
			agg.paid_amount,
			agg.outstanding_amount,
			si.customer_name,
			si.due_date,
			IFNULL(si.remarks, '') AS reference,
			IFNULL(si.is_return, 0) AS is_return
		FROM (
			SELECT
				ple.party AS customer,
				CASE
					WHEN IFNULL(ple.against_voucher_type, '') = 'Sales Invoice'
					 AND IFNULL(ple.against_voucher_no, '') != ''
					THEN ple.against_voucher_no
					ELSE ple.voucher_no
				END AS target_voucher,
				MAX(ple.posting_date) AS posting_date,
				SUM(CASE WHEN ple.amount > 0 THEN ple.amount ELSE 0 END) AS billed_amount,
				SUM(CASE WHEN ple.amount < 0 THEN ABS(ple.amount) ELSE 0 END) AS paid_amount,
				SUM(ple.amount) AS outstanding_amount
			FROM `tabPayment Ledger Entry` ple
			WHERE {conditions}
			GROUP BY ple.party, target_voucher
		) agg
		LEFT JOIN `tabSales Invoice` si ON si.name = agg.target_voucher
		ORDER BY agg.posting_date DESC, agg.target_voucher DESC
		""".format(conditions=" AND ".join(ple_conditions)),
		params,
		as_dict=True,
	)

	search_q = (str(search).strip().lower() if search else "")

	for row in voucher_rows:
		customer = row.get("customer") or ""
		invoice_name = row.get("invoice") or ""
		invoice_date = row.get("posting_date")
		due_date = row.get("due_date")

		billed_amount = flt(row.get("billed_amount") or 0)
		paid_amount = flt(row.get("paid_amount") or 0)
		outstanding_amount = flt(row.get("outstanding_amount") or 0)

		customer_name = row.get("customer_name") or customer_name_map.get(customer) or customer
		company_name = customer_name or customer or "Unknown"
		guest = company_name
		reference = row.get("reference") or ""

		days_overdue = 0
		if due_date:
			days_overdue = date_diff(str(date_to), due_date)

		bucket = _aging_bucket(days_overdue)
		computed_status = _billing_status(outstanding_amount, due_date, as_of_date=date_to)

		if status and computed_status != status:
			continue

		if aging_bucket and bucket != aging_bucket:
			continue

		if search_q:
			search_blob = " ".join(
				[
					str(invoice_name or ""),
					str(company_name or ""),
					str(customer or ""),
					str(guest or ""),
					str(reference or ""),
				]
			).lower()
			if search_q not in search_blob:
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
				"is_return": int(row.get("is_return") or 0),
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
