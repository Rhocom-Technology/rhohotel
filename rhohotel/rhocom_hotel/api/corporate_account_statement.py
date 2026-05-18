import frappe
from frappe.utils import getdate, nowdate, add_days, flt


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


def _get_customer_display(customer):
	if not customer:
		return "Unknown"

	try:
		if _has_doctype("Customer") and frappe.db.exists("Customer", customer):
			customer_name = frappe.db.get_value("Customer", customer, "customer_name")
			return customer_name or customer
	except Exception:
		pass

	return customer


def _get_sales_invoice_rows(date_from, date_to, customer=None, search=None):
	if not _has_doctype("Sales Invoice"):
		return []

	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
	customer_field = _get_field("Sales Invoice", ["customer"])
	customer_name_field = _get_field("Sales Invoice", ["customer_name"])
	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
	outstanding_field = _get_field("Sales Invoice", ["outstanding_amount"])
	remarks_field = _get_field("Sales Invoice", ["remarks", "custom_reference", "po_no"])

	conditions = ["docstatus = 1"]
	params = {}

	if posting_date_field:
		conditions.append("{0} BETWEEN %(date_from)s AND %(date_to)s".format(posting_date_field))
		params["date_from"] = date_from
		params["date_to"] = date_to

	if customer and customer_field:
		conditions.append("{0} = %(customer)s".format(customer_field))
		params["customer"] = customer

	if search:
		search_fields = ["name"]
		for field in [customer_field, customer_name_field, remarks_field]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]
	for field in [
		posting_date_field,
		customer_field,
		customer_name_field,
		grand_total_field,
		outstanding_field,
		remarks_field,
	]:
		if field and field not in select_fields:
			select_fields.append(field)

	sql = """
		SELECT {fields}
		FROM `tabSales Invoice`
		WHERE {conditions}
		ORDER BY {date_field} ASC, name ASC
	""".format(
		fields=", ".join(select_fields),
		conditions=" AND ".join(conditions),
		date_field=posting_date_field or "creation",
	)

	invoices = frappe.db.sql(sql, params, as_dict=True)

	rows = []

	for inv in invoices:
		cust = inv.get(customer_field) if customer_field else ""
		cust_name = inv.get(customer_name_field) if customer_name_field else ""
		amount = flt(inv.get(grand_total_field)) if grand_total_field else 0
		outstanding = flt(inv.get(outstanding_field)) if outstanding_field else 0

		rows.append(
			{
				"date": str(inv.get(posting_date_field))
				if posting_date_field and inv.get(posting_date_field)
				else "",
				"party": cust,
				"party_name": cust_name or _get_customer_display(cust),
				"transaction_type": "Sales Invoice",
				"reference": inv.get("name"),
				"description": inv.get(remarks_field) if remarks_field else "Corporate billing invoice",
				"debit": amount,
				"credit": 0,
				"outstanding": outstanding,
				"source": "Sales Invoice",
			}
		)

	return rows


def _get_payment_rows(date_from, date_to, customer=None, search=None):
	if not _has_doctype("Payment Entry"):
		return []

	posting_date_field = _get_field("Payment Entry", ["posting_date"])
	party_field = _get_field("Payment Entry", ["party"])
	party_name_field = _get_field("Payment Entry", ["party_name"])
	party_type_field = _get_field("Payment Entry", ["party_type"])
	paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])
	reference_no_field = _get_field("Payment Entry", ["reference_no", "cheque_no"])
	remarks_field = _get_field("Payment Entry", ["remarks"])

	conditions = ["docstatus = 1"]
	params = {}

	if posting_date_field:
		conditions.append("{0} BETWEEN %(date_from)s AND %(date_to)s".format(posting_date_field))
		params["date_from"] = date_from
		params["date_to"] = date_to

	if party_type_field:
		conditions.append("{0} = 'Customer'".format(party_type_field))

	if customer and party_field:
		conditions.append("{0} = %(customer)s".format(party_field))
		params["customer"] = customer

	if search:
		search_fields = ["name"]
		for field in [party_field, party_name_field, reference_no_field, remarks_field]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append("(" + " OR ".join(["{0} LIKE %(search)s".format(f) for f in search_fields]) + ")")
		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]
	for field in [
		posting_date_field,
		party_field,
		party_name_field,
		paid_amount_field,
		reference_no_field,
		remarks_field,
	]:
		if field and field not in select_fields:
			select_fields.append(field)

	sql = """
		SELECT {fields}
		FROM `tabPayment Entry`
		WHERE {conditions}
		ORDER BY {date_field} ASC, name ASC
	""".format(
		fields=", ".join(select_fields),
		conditions=" AND ".join(conditions),
		date_field=posting_date_field or "creation",
	)

	payments = frappe.db.sql(sql, params, as_dict=True)

	rows = []

	for pay in payments:
		party = pay.get(party_field) if party_field else ""
		party_name = pay.get(party_name_field) if party_name_field else ""

		rows.append(
			{
				"date": str(pay.get(posting_date_field))
				if posting_date_field and pay.get(posting_date_field)
				else "",
				"party": party,
				"party_name": party_name or _get_customer_display(party),
				"transaction_type": "Payment Entry",
				"reference": pay.get("name"),
				"description": pay.get(remarks_field)
				if remarks_field
				else pay.get(reference_no_field)
				if reference_no_field
				else "Payment received",
				"debit": 0,
				"credit": flt(pay.get(paid_amount_field)) if paid_amount_field else 0,
				"outstanding": 0,
				"source": "Payment Entry",
			}
		)

	return rows


def _get_opening_balance(date_from, customer=None):
	opening = 0

	if _has_doctype("Sales Invoice"):
		posting_date_field = _get_field("Sales Invoice", ["posting_date"])
		customer_field = _get_field("Sales Invoice", ["customer"])
		grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])

		if posting_date_field and grand_total_field:
			conditions = ["docstatus = 1", "{0} < %(date_from)s".format(posting_date_field)]
			params = {"date_from": date_from}

			if customer and customer_field:
				conditions.append("{0} = %(customer)s".format(customer_field))
				params["customer"] = customer

			opening += flt(
				frappe.db.sql(
					"""
				SELECT SUM({amount_field})
				FROM `tabSales Invoice`
				WHERE {conditions}
				""".format(
						amount_field=grand_total_field,
						conditions=" AND ".join(conditions),
					),
					params,
				)[0][0]
				or 0
			)

	if _has_doctype("Payment Entry"):
		posting_date_field = _get_field("Payment Entry", ["posting_date"])
		party_field = _get_field("Payment Entry", ["party"])
		party_type_field = _get_field("Payment Entry", ["party_type"])
		paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])

		if posting_date_field and paid_amount_field:
			conditions = ["docstatus = 1", "{0} < %(date_from)s".format(posting_date_field)]
			params = {"date_from": date_from}

			if party_type_field:
				conditions.append("{0} = 'Customer'".format(party_type_field))

			if customer and party_field:
				conditions.append("{0} = %(customer)s".format(party_field))
				params["customer"] = customer

			opening -= flt(
				frappe.db.sql(
					"""
				SELECT SUM({amount_field})
				FROM `tabPayment Entry`
				WHERE {conditions}
				""".format(
						amount_field=paid_amount_field,
						conditions=" AND ".join(conditions),
					),
					params,
				)[0][0]
				or 0
			)

	return opening


def _get_customers():
	if not _has_doctype("Customer"):
		return []

	try:
		return frappe.db.sql(
			"""
			SELECT name, customer_name
			FROM `tabCustomer`
			ORDER BY customer_name ASC, name ASC
			""",
			as_dict=True,
		)
	except Exception:
		return []


@frappe.whitelist()
def get_corporate_account_statement(
	date_from=None,
	date_to=None,
	customer=None,
	transaction_type=None,
	search=None,
	account_page=1,
	account_page_size=10,
):
	date_from = _date_or_default(date_from, add_days(nowdate(), -30))
	date_to = _date_or_default(date_to, nowdate())

	invoice_rows = _get_sales_invoice_rows(date_from, date_to, customer, search)
	payment_rows = _get_payment_rows(date_from, date_to, customer, search)

	rows = invoice_rows + payment_rows

	if transaction_type:
		rows = [row for row in rows if row.get("transaction_type") == transaction_type]

	rows = sorted(rows, key=lambda x: (str(x.get("date") or ""), str(x.get("reference") or "")))

	opening_balance = _get_opening_balance(date_from, customer)
	running_balance = opening_balance

	for row in rows:
		running_balance += flt(row.get("debit")) - flt(row.get("credit"))
		row["running_balance"] = running_balance

	total_debit = sum(flt(row.get("debit")) for row in rows)
	total_credit = sum(flt(row.get("credit")) for row in rows)
	closing_balance = opening_balance + total_debit - total_credit

	account_map = {}

	for row in rows:
		party = row.get("party") or "Unknown"
		party_name = row.get("party_name") or party

		if party not in account_map:
			account_map[party] = {
				"customer": party,
				"customer_name": party_name,
				"transactions": 0,
				"total_debit": 0,
				"total_credit": 0,
				"balance": 0,
			}

		account_map[party]["transactions"] += 1
		account_map[party]["total_debit"] += flt(row.get("debit"))
		account_map[party]["total_credit"] += flt(row.get("credit"))
		account_map[party]["balance"] += flt(row.get("debit")) - flt(row.get("credit"))

	account_summary = sorted(account_map.values(), key=lambda x: flt(x.get("balance")), reverse=True)

	account_summary_page = _paginate(account_summary, account_page, account_page_size)

	return {
		"rows": rows,
		"customers": _get_customers(),
		"account_summary": account_summary_page["rows"],
		"account_summary_total": account_summary_page["total"],
		"account_summary_page": account_summary_page["page"],
		"account_summary_page_size": account_summary_page["page_size"],
		"account_summary_total_pages": account_summary_page["total_pages"],
		"summary": {
			"opening_balance": opening_balance,
			"total_debit": total_debit,
			"total_credit": total_credit,
			"closing_balance": closing_balance,
			"transaction_count": len(rows),
			"customer_count": len(account_map),
		},
	}
