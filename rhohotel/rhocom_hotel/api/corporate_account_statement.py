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

	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return []

	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
	customer_field = _get_field("Sales Invoice", ["customer"])
	customer_name_field = _get_field("Sales Invoice", ["customer_name"])
	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
	outstanding_field = _get_field("Sales Invoice", ["outstanding_amount"])
	is_return_field = _get_field("Sales Invoice", ["is_return"])
	remarks_field = _get_field("Sales Invoice", ["remarks", "custom_reference", "po_no"])

	conditions = ["docstatus = 1"]
	params = {}

	if posting_date_field:
		conditions.append("{0} BETWEEN %(date_from)s AND %(date_to)s".format(posting_date_field))
		params["date_from"] = date_from
		params["date_to"] = date_to

	if customer_field:
		conditions.append("{0} IN %(corporate_customers)s".format(customer_field))
		params["corporate_customers"] = tuple(corporate_customers)

	if customer and customer_field:
		conditions.append("{0} = %(customer)s".format(customer_field))
		params["customer"] = customer

	if search:
		search_fields = ["name"]

		for field in [customer_field, customer_name_field, remarks_field]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append(
			"(" + " OR ".join(
				["{0} LIKE %(search)s".format(f) for f in search_fields]
			) + ")"
		)

		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]

	for field in [
		posting_date_field,
		customer_field,
		customer_name_field,
		grand_total_field,
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
		is_return = bool(inv.get(is_return_field)) if is_return_field else amount < 0
		debit = 0 if is_return or amount < 0 else amount
		credit = abs(amount) if is_return or amount < 0 else 0

		rows.append(
			{
				"date": str(inv.get(posting_date_field))
				if posting_date_field and inv.get(posting_date_field)
				else "",
				"party": cust,
				"party_name": cust_name or _get_customer_display(cust),
				"transaction_type": "Credit Note" if credit else "Sales Invoice",
				"reference": inv.get("name"),
				"description": inv.get(remarks_field)
				if remarks_field
				else ("Corporate billing credit note" if credit else "Corporate billing invoice"),
				"debit": debit,
				"credit": credit,
				"outstanding": outstanding,
				"source": "Sales Invoice",
			}
		)

	return rows



def _get_payment_rows(date_from, date_to, customer=None, search=None):
	if not _has_doctype("Payment Entry"):
		return []

	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return []

	posting_date_field = _get_field("Payment Entry", ["posting_date"])
	party_field = _get_field("Payment Entry", ["party"])
	party_name_field = _get_field("Payment Entry", ["party_name"])
	party_type_field = _get_field("Payment Entry", ["party_type"])
	payment_type_field = _get_field("Payment Entry", ["payment_type"])
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

	if party_field:
		conditions.append("{0} IN %(corporate_customers)s".format(party_field))
		params["corporate_customers"] = tuple(corporate_customers)

	if customer and party_field:
		conditions.append("{0} = %(customer)s".format(party_field))
		params["customer"] = customer

	if search:
		search_fields = ["name"]

		for field in [party_field, party_name_field, reference_no_field, remarks_field]:
			if field and field not in search_fields:
				search_fields.append(field)

		conditions.append(
			"(" + " OR ".join(
				["{0} LIKE %(search)s".format(f) for f in search_fields]
			) + ")"
		)

		params["search"] = "%{0}%".format(search)

	select_fields = ["name"]

	for field in [
		posting_date_field,
		party_field,
		party_name_field,
		payment_type_field,
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
		payment_type = pay.get(payment_type_field) if payment_type_field else "Receive"
		amount = flt(pay.get(paid_amount_field)) if paid_amount_field else 0
		is_refund = payment_type == "Pay"

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
				"debit": amount if is_refund else 0,
				"credit": 0 if is_refund else amount,
				"outstanding": 0,
				"source": "Payment Entry",
			}
		)

	return rows




def _get_bill_transfer_rows(date_from, date_to, customer=None, search=None):
	if not _has_doctype("Bill Transfer") or not _has_doctype("Journal Entry"):
		return []

	corporate_customers = _get_corporate_customers()
	if not corporate_customers:
		return []

	conditions = [
		"bt.docstatus = 1",
		"bt.status = 'Approved'",
		"IFNULL(bt.journal_entry, '') != ''",
		"je.docstatus = 1",
		"je.posting_date BETWEEN %(date_from)s AND %(date_to)s",
		"(to_guest.customer IN %(corporate_customers)s OR from_guest.customer IN %(corporate_customers)s)",
	]
	params = {
		"date_from": date_from,
		"date_to": date_to,
		"corporate_customers": tuple(corporate_customers),
	}

	if customer:
		conditions.append("(to_guest.customer = %(customer)s OR from_guest.customer = %(customer)s)")
		params["customer"] = customer

	if search:
		conditions.append(
			"""(
				bt.name LIKE %(search)s
				OR bt.source_invoice LIKE %(search)s
				OR bt.journal_entry LIKE %(search)s
				OR bt.reason LIKE %(search)s
				OR to_guest.hotel_guest_name LIKE %(search)s
				OR from_guest.hotel_guest_name LIKE %(search)s
			)"""
		)
		params["search"] = "%{0}%".format(search)

	transfer_rows = frappe.db.sql(
		"""
		SELECT
			bt.name,
			bt.source_invoice,
			bt.total_amount,
			bt.reason,
			bt.journal_entry,
			je.posting_date,
			to_guest.customer AS to_customer,
			to_guest.hotel_guest_name AS to_guest_name,
			from_guest.customer AS from_customer,
			from_guest.hotel_guest_name AS from_guest_name
		FROM `tabBill Transfer` bt
		INNER JOIN `tabJournal Entry` je ON je.name = bt.journal_entry
		LEFT JOIN `tabHotel Guest` to_guest ON to_guest.name = bt.to_guest
		LEFT JOIN `tabHotel Guest` from_guest ON from_guest.name = bt.from_guest
		WHERE {conditions}
		ORDER BY je.posting_date ASC, bt.name ASC
		""".format(conditions=" AND ".join(conditions)),
		params,
		as_dict=True,
	)

	rows = []
	for transfer in transfer_rows:
		if transfer.get("to_customer") in corporate_customers and (
			not customer or transfer.get("to_customer") == customer
		):
			rows.append(
				{
					"date": str(transfer.get("posting_date")) if transfer.get("posting_date") else "",
					"party": transfer.get("to_customer"),
					"party_name": transfer.get("to_guest_name") or _get_customer_display(transfer.get("to_customer")),
					"transaction_type": "Bill Transfer",
					"reference": transfer.get("journal_entry") or transfer.get("name"),
					"description": transfer.get("reason") or "Bill transferred to corporate account",
					"debit": flt(transfer.get("total_amount")),
					"credit": 0,
					"outstanding": 0,
					"source": "Bill Transfer",
					"source_invoice": transfer.get("source_invoice"),
					"bill_transfer": transfer.get("name"),
				}
			)

		if transfer.get("from_customer") in corporate_customers and (
			not customer or transfer.get("from_customer") == customer
		):
			rows.append(
				{
					"date": str(transfer.get("posting_date")) if transfer.get("posting_date") else "",
					"party": transfer.get("from_customer"),
					"party_name": transfer.get("from_guest_name") or _get_customer_display(transfer.get("from_customer")),
					"transaction_type": "Bill Transfer",
					"reference": transfer.get("journal_entry") or transfer.get("name"),
					"description": transfer.get("reason") or "Bill transferred out of corporate account",
					"debit": 0,
					"credit": flt(transfer.get("total_amount")),
					"outstanding": 0,
					"source": "Bill Transfer",
					"source_invoice": transfer.get("source_invoice"),
					"bill_transfer": transfer.get("name"),
				}
			)

	return rows


def _get_corporate_customers():
	if not _has_doctype("Hotel Guest"):
		return []

	guest_type_field = _get_field("Hotel Guest", ["guest_type"])
	customer_field = _get_field("Hotel Guest", ["customer"])

	if not guest_type_field or not customer_field:
		return []

	try:
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
			as_dict=True,
		)

		return [row.customer for row in rows if row.customer]

	except Exception:
		return []



def _get_customers():
	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return []

	if not _has_doctype("Customer"):
		return []

	try:
		return frappe.db.sql(
			"""
			SELECT
				name,
				customer_name
			FROM `tabCustomer`
			WHERE name IN %(customers)s
			ORDER BY customer_name ASC, name ASC
			""",
			{
				"customers": tuple(corporate_customers)
			},
			as_dict=True,
		)
	except Exception:
		return []


def _get_customer_name_map(customers):
	if not customers or not _has_doctype("Customer"):
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


def _get_corporate_ple_rows(date_from, date_to, corporate_customers, customer=None):
	conditions = [
		"ple.docstatus = 1",
		"ple.account_type = 'Receivable'",
		"ple.party_type = 'Customer'",
		"ple.delinked = 0",
		"ple.posting_date BETWEEN %(date_from)s AND %(date_to)s",
		"ple.party IN %(customers)s",
	]
	params = {
		"date_from": str(date_from),
		"date_to": str(date_to),
		"customers": tuple(corporate_customers),
	}

	if customer:
		conditions.append("ple.party = %(customer)s")
		params["customer"] = customer

	return frappe.db.sql(
		"""
		SELECT
			ple.name,
			ple.creation,
			ple.posting_date,
			ple.party,
			ple.voucher_type,
			ple.voucher_no,
			ple.against_voucher_type,
			ple.against_voucher_no,
			ple.amount,
			ple.remarks
		FROM `tabPayment Ledger Entry` ple
		WHERE {conditions}
		ORDER BY ple.posting_date ASC, ple.creation ASC, ple.name ASC
		""".format(conditions=" AND ".join(conditions)),
		params,
		as_dict=True,
	)


def _get_corporate_opening_balance(date_from, corporate_customers, customer=None):
	conditions = [
		"docstatus = 1",
		"account_type = 'Receivable'",
		"party_type = 'Customer'",
		"delinked = 0",
		"posting_date < %(date_from)s",
		"party IN %(customers)s",
	]
	params = {"date_from": str(date_from), "customers": tuple(corporate_customers)}

	if customer:
		conditions.append("party = %(customer)s")
		params["customer"] = customer

	return flt(
		frappe.db.sql(
			"""
			SELECT SUM(amount)
			FROM `tabPayment Ledger Entry`
			WHERE {conditions}
			""".format(conditions=" AND ".join(conditions)),
			params,
		)[0][0]
		or 0
	)


def _get_voucher_meta_for_corporate_ledger(ple_rows):
	si_names = set()
	pe_names = set()
	je_names = set()

	for row in ple_rows:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")
		if not voucher_no:
			continue
		if voucher_type == "Sales Invoice":
			si_names.add(voucher_no)
		elif voucher_type == "Payment Entry":
			pe_names.add(voucher_no)
		elif voucher_type == "Journal Entry":
			je_names.add(voucher_no)

	si_meta = {}
	if si_names and _has_doctype("Sales Invoice"):
		rows = frappe.db.sql(
			"""
			SELECT name, is_return, remarks
			FROM `tabSales Invoice`
			WHERE name IN %(names)s
			""",
			{"names": tuple(si_names)},
			as_dict=True,
		)
		si_meta = {row.get("name"): row for row in rows}

	pe_meta = {}
	if pe_names and _has_doctype("Payment Entry"):
		rows = frappe.db.sql(
			"""
			SELECT name, remarks, reference_no
			FROM `tabPayment Entry`
			WHERE name IN %(names)s
			""",
			{"names": tuple(pe_names)},
			as_dict=True,
		)
		pe_meta = {row.get("name"): row for row in rows}

	je_meta = {}
	if je_names and _has_doctype("Journal Entry"):
		has_user_remark = _has_column("Journal Entry", "user_remark")
		has_remark = _has_column("Journal Entry", "remark")

		if has_user_remark and has_remark:
			remarks_field = "CONCAT_WS('\\n', NULLIF(user_remark, ''), NULLIF(remark, '')) AS remarks"
		elif has_user_remark:
			remarks_field = "user_remark AS remarks"
		elif has_remark:
			remarks_field = "remark AS remarks"
		else:
			remarks_field = "'' AS remarks"

		rows = frappe.db.sql(
			"""
			SELECT name, {remarks_field}
			FROM `tabJournal Entry`
			WHERE name IN %(names)s
			""".format(remarks_field=remarks_field),
			{"names": tuple(je_names)},
			as_dict=True,
		)
		je_meta = {row.get("name"): row for row in rows}

	return {
		"sales_invoice": si_meta,
		"payment_entry": pe_meta,
		"journal_entry": je_meta,
	}


def _corporate_transaction_type(ple_row, voucher_meta):
	voucher_type = ple_row.get("voucher_type") or ""
	amount = flt(ple_row.get("amount") or 0)

	if voucher_type == "Sales Invoice":
		si = voucher_meta.get("sales_invoice", {}).get(ple_row.get("voucher_no"), {})
		if int(si.get("is_return") or 0) or amount < 0:
			return "Credit Note"
		return "Sales Invoice"

	if voucher_type == "Payment Entry":
		return "Payment Entry"

	if voucher_type == "Journal Entry":
		je = voucher_meta.get("journal_entry", {}).get(ple_row.get("voucher_no"), {})
		text = "{0} {1}".format(ple_row.get("remarks") or "", je.get("remarks") or "").lower()
		if "bill transfer" in text:
			return "Bill Transfer"
		return "Journal Entry"

	return voucher_type or "Ledger Entry"


def _corporate_description(ple_row, voucher_meta):
	if ple_row.get("remarks"):
		return ple_row.get("remarks")

	voucher_type = ple_row.get("voucher_type") or ""
	voucher_no = ple_row.get("voucher_no")

	if voucher_type == "Sales Invoice":
		si = voucher_meta.get("sales_invoice", {}).get(voucher_no, {})
		if si.get("remarks"):
			return si.get("remarks")

	if voucher_type == "Payment Entry":
		pe = voucher_meta.get("payment_entry", {}).get(voucher_no, {})
		if pe.get("remarks"):
			return pe.get("remarks")
		if pe.get("reference_no"):
			return pe.get("reference_no")

	if voucher_type == "Journal Entry":
		je = voucher_meta.get("journal_entry", {}).get(voucher_no, {})
		if je.get("remarks"):
			return je.get("remarks")

	return "{0} {1}".format(voucher_type or "Transaction", voucher_no or "").strip()


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

	corporate_customers = _get_corporate_customers()
	if not corporate_customers:
		return {
			"rows": [],
			"customers": [],
			"account_summary": [],
			"account_summary_total": 0,
			"account_summary_page": 1,
			"account_summary_page_size": int(account_page_size or 10),
			"account_summary_total_pages": 1,
			"summary": {
				"opening_balance": 0,
				"total_debit": 0,
				"total_credit": 0,
				"closing_balance": 0,
				"transaction_count": 0,
				"customer_count": 0,
			},
		}

	if customer and customer not in corporate_customers:
		customer = "__invalid__"

	ple_rows = _get_corporate_ple_rows(date_from, date_to, corporate_customers, customer=customer)
	voucher_meta = _get_voucher_meta_for_corporate_ledger(ple_rows)
	name_map = _get_customer_name_map(corporate_customers)

	rows = []
	for ple in ple_rows:
		debit = flt(ple.get("amount") or 0) if flt(ple.get("amount") or 0) > 0 else 0
		credit = abs(flt(ple.get("amount") or 0)) if flt(ple.get("amount") or 0) < 0 else 0
		trans_type = _corporate_transaction_type(ple, voucher_meta)

		row = {
			"date": str(ple.get("posting_date") or ""),
			"party": ple.get("party") or "",
			"party_name": name_map.get(ple.get("party")) or _get_customer_display(ple.get("party")),
			"transaction_type": trans_type,
			"reference": ple.get("voucher_no") or "",
			"description": _corporate_description(ple, voucher_meta),
			"debit": debit,
			"credit": credit,
			"outstanding": 0,
			"source": ple.get("voucher_type") or "",
			"_creation": str(ple.get("creation") or ""),
			"_name": ple.get("name") or "",
		}
		rows.append(row)

	if transaction_type:
		rows = [row for row in rows if row.get("transaction_type") == transaction_type]

	if search:
		q = str(search).lower().strip()
		rows = [
			row
			for row in rows
			if q in str(row.get("party") or "").lower()
			or q in str(row.get("party_name") or "").lower()
			or q in str(row.get("reference") or "").lower()
			or q in str(row.get("description") or "").lower()
			or q in str(row.get("transaction_type") or "").lower()
		]

	rows = sorted(
		rows,
		key=lambda x: (str(x.get("date") or ""), str(x.get("_creation") or ""), str(x.get("reference") or ""), str(x.get("_name") or "")),
	)

	opening_balance = _get_corporate_opening_balance(date_from, corporate_customers, customer=customer)
	running_balance = opening_balance

	for row in rows:
		running_balance += flt(row.get("debit")) - flt(row.get("credit"))
		row["running_balance"] = running_balance
		row.pop("_creation", None)
		row.pop("_name", None)

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


def _get_opening_balance(date_from, customer=None):
	opening = 0
	corporate_customers = _get_corporate_customers()

	if not corporate_customers:
		return 0

	if customer and customer not in corporate_customers:
		return 0

	opening += _get_sales_invoice_opening_balance(date_from, corporate_customers, customer)
	opening += _get_payment_opening_balance(date_from, corporate_customers, customer)
	opening += _get_bill_transfer_opening_balance(date_from, corporate_customers, customer)

	return opening


def _get_sales_invoice_opening_balance(date_from, corporate_customers, customer=None):
	if not _has_doctype("Sales Invoice"):
		return 0

	posting_date_field = _get_field("Sales Invoice", ["posting_date"])
	customer_field = _get_field("Sales Invoice", ["customer"])
	grand_total_field = _get_field("Sales Invoice", ["grand_total", "rounded_total"])
	is_return_field = _get_field("Sales Invoice", ["is_return"])
	if not (posting_date_field and grand_total_field and customer_field):
		return 0

	conditions = [
		"docstatus = 1",
		"{0} < %(date_from)s".format(posting_date_field),
		"{0} IN %(corporate_customers)s".format(customer_field),
	]
	params = {"date_from": date_from, "corporate_customers": tuple(corporate_customers)}
	if customer:
		conditions.append("{0} = %(customer)s".format(customer_field))
		params["customer"] = customer

	amount_expr = grand_total_field
	if is_return_field:
		amount_expr = "CASE WHEN `{0}` = 1 THEN -ABS({1}) ELSE {1} END".format(
			is_return_field,
			grand_total_field,
		)

	return flt(
		frappe.db.sql(
			"""
			SELECT SUM({amount_expr})
			FROM `tabSales Invoice`
			WHERE {conditions}
			""".format(amount_expr=amount_expr, conditions=" AND ".join(conditions)),
			params,
		)[0][0] or 0
	)


def _get_payment_opening_balance(date_from, corporate_customers, customer=None):
	if not _has_doctype("Payment Entry"):
		return 0

	posting_date_field = _get_field("Payment Entry", ["posting_date"])
	party_field = _get_field("Payment Entry", ["party"])
	party_type_field = _get_field("Payment Entry", ["party_type"])
	payment_type_field = _get_field("Payment Entry", ["payment_type"])
	paid_amount_field = _get_field("Payment Entry", ["paid_amount", "received_amount"])
	if not (posting_date_field and paid_amount_field and party_field):
		return 0

	conditions = [
		"docstatus = 1",
		"{0} < %(date_from)s".format(posting_date_field),
		"{0} IN %(corporate_customers)s".format(party_field),
	]
	params = {"date_from": date_from, "corporate_customers": tuple(corporate_customers)}
	if party_type_field:
		conditions.append("{0} = 'Customer'".format(party_type_field))
	if customer:
		conditions.append("{0} = %(customer)s".format(party_field))
		params["customer"] = customer

	amount_expr = paid_amount_field
	if payment_type_field:
		amount_expr = "CASE WHEN `{0}` = 'Pay' THEN {1} ELSE -{1} END".format(
			payment_type_field,
			paid_amount_field,
		)
	else:
		amount_expr = "-{0}".format(paid_amount_field)

	return flt(
		frappe.db.sql(
			"""
			SELECT SUM({amount_expr})
			FROM `tabPayment Entry`
			WHERE {conditions}
			""".format(amount_expr=amount_expr, conditions=" AND ".join(conditions)),
			params,
		)[0][0] or 0
	)


def _get_bill_transfer_opening_balance(date_from, corporate_customers, customer=None):
	if not _has_doctype("Bill Transfer") or not _has_doctype("Journal Entry"):
		return 0

	rows = _get_bill_transfer_rows("1900-01-01", add_days(date_from, -1), customer=customer)
	return sum(flt(row.get("debit")) - flt(row.get("credit")) for row in rows)
