"""
Billing Dashboard API — rhohotel
=================================
Uses Payment Ledger Entry (PLE) as the source of truth — the same table
the ERPNext Accounts Receivable report uses — so all figures match exactly.

Endpoint
--------
rhohotel.rhocom_hotel.api.billing_dashboard.get_billing_dashboard_data

Parameters
----------
from_date : str  (YYYY-MM-DD, optional) — start of date range filter
to_date   : str  (YYYY-MM-DD, optional) — end of date range filter
"""

import frappe
from frappe.utils import flt, getdate, nowdate, add_days, today as frappe_today


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_billing_dashboard_data(from_date=None, to_date=None):
    today   = getdate(nowdate())
    from_dt = getdate(from_date) if from_date else add_days(today, -7)
    to_dt   = getdate(to_date)   if to_date   else today
    as_of_dt = to_dt if to_dt else today

    # Corporate customer list — fetched ONCE, passed everywhere
    corp = _get_corporate_customers()

    return {
        "stats":         _build_stats(from_dt, to_dt, as_of_dt, corp),
        "activity_feed": _build_activity_feed(from_dt, to_dt, corp),
        "insights":      _build_insights(as_of_dt, corp),
    }


# ---------------------------------------------------------------------------
# Corporate customer list
# ---------------------------------------------------------------------------

def _get_corporate_customers():
    if not frappe.db.exists("DocType", "Hotel Guest"):
        return []
    rows = frappe.db.sql("""
        SELECT DISTINCT customer
        FROM `tabHotel Guest`
        WHERE guest_type = 'Corporate'
          AND IFNULL(customer, '') != ''
    """, as_dict=True)
    return [r.customer for r in rows if r.customer]


# ---------------------------------------------------------------------------
# Stats — all receivables figures from PLE to match AR report
# ---------------------------------------------------------------------------

def _build_stats(from_dt, to_dt, today, corp):
    # ── Total receivables from PLE (matches AR report exactly) ──────────────
    total_row = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_invoiced,
            SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS total_collected,
            SUM(amount) AS total_outstanding
        FROM `tabPayment Ledger Entry`
        WHERE docstatus = 1
          AND account_type = 'Receivable'
          AND party_type = 'Customer'
          AND delinked = 0
          AND posting_date <= %(to_dt)s
    """, {"to_dt": str(to_dt)}, as_dict=True)[0]

    total_invoiced    = flt(total_row.total_invoiced)
    total_collected   = flt(total_row.total_collected)
    total_outstanding = flt(total_row.total_outstanding)
    collection_rate   = round((total_collected / total_invoiced * 100) if total_invoiced else 0, 1)

    # ── Corporate split ──────────────────────────────────────────────────────
    if corp:
        corp_row = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS invoiced,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS collected,
                SUM(amount) AS outstanding
            FROM `tabPayment Ledger Entry`
            WHERE docstatus = 1
              AND account_type = 'Receivable'
              AND party_type = 'Customer'
              AND delinked = 0
              AND posting_date <= %(to_dt)s
              AND party IN %(c)s
        """, {"c": tuple(corp), "to_dt": str(to_dt)}, as_dict=True)[0]
        corp_invoiced    = flt(corp_row.invoiced)
        corp_collected   = flt(corp_row.collected)
        corp_outstanding = flt(corp_row.outstanding)
    else:
        corp_invoiced = corp_collected = corp_outstanding = 0

    # ── Individual split ─────────────────────────────────────────────────────
    if corp:
        ind_row = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS invoiced,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS collected,
                SUM(amount) AS outstanding
            FROM `tabPayment Ledger Entry`
            WHERE docstatus = 1
              AND account_type = 'Receivable'
              AND party_type = 'Customer'
              AND delinked = 0
              AND posting_date <= %(to_dt)s
              AND party NOT IN %(c)s
        """, {"c": tuple(corp), "to_dt": str(to_dt)}, as_dict=True)[0]
        ind_invoiced    = flt(ind_row.invoiced)
        ind_collected   = flt(ind_row.collected)
        ind_outstanding = flt(ind_row.outstanding)
    else:
        ind_invoiced    = total_invoiced
        ind_collected   = total_collected
        ind_outstanding = total_outstanding

    # ── Overdue/current from allocation-aware aging buckets (PLE consolidated)
    # This keeps the KPI cards on the same basis as the aging insights.
    corp_aging = _aging(to_dt, corp, corporate=True)
    ind_aging = _aging(to_dt, corp, corporate=False)

    total_overdue = (
        flt(corp_aging.get("days_1_30"))
        + flt(corp_aging.get("days_31_60"))
        + flt(corp_aging.get("days_60_plus"))
        + flt(ind_aging.get("days_1_30"))
        + flt(ind_aging.get("days_31_60"))
        + flt(ind_aging.get("days_60_plus"))
    )
    total_current = flt(corp_aging.get("current")) + flt(ind_aging.get("current"))

    # ── Unreconciled credit notes ─────────────────────────────────────────────
    credit_row = frappe.db.sql("""
        SELECT COUNT(*) AS cnt, ABS(SUM(outstanding_amount)) AS amount
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_return = 1
          AND outstanding_amount != 0
    """, as_dict=True)[0]

    # ── Period-scoped counts — explicit SQL to avoid ORM filter quirks ───────
    period_row = frappe.db.sql("""
        SELECT
            COUNT(*) AS invoices_in_range,
            SUM(grand_total) AS invoiced_in_range,
            SUM(outstanding_amount) AS outstanding_in_range
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_return = 0
          AND grand_total > 0
          AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
    """, {"from_dt": str(from_dt), "to_dt": str(to_dt)}, as_dict=True)[0]

    invoices_in_range     = int(period_row.invoices_in_range or 0)
    invoiced_in_range     = round(flt(period_row.invoiced_in_range), 2)
    outstanding_in_range  = round(flt(period_row.outstanding_in_range), 2)

    # Unallocated payments are ALL-TIME (not period-filtered) — a payment
    # received months ago may still be unallocated and needs attention.
    unallocated_payments = frappe.db.sql("""
        SELECT COUNT(*) AS cnt
        FROM `tabPayment Entry`
        WHERE docstatus = 1
          AND payment_type = 'Receive'
          AND party_type = 'Customer'
          AND IFNULL(party, '') != ''
          AND unallocated_amount > 0
    """, as_dict=True)[0].cnt or 0

    return {
        # Totals
        "total_invoiced":       round(total_invoiced, 2),
        "total_collected":      round(total_collected, 2),
        "total_outstanding":    round(total_outstanding, 2),
        "collection_rate":      collection_rate,

        # Overdue vs current
        "total_overdue":        round(total_overdue, 2),
        "total_current":        round(total_current, 2),

        # Corporate
        "corp_invoiced":        round(corp_invoiced, 2),
        "corp_collected":       round(corp_collected, 2),
        "corp_outstanding":     round(corp_outstanding, 2),

        # Individual
        "ind_invoiced":         round(ind_invoiced, 2),
        "ind_collected":        round(ind_collected, 2),
        "ind_outstanding":      round(ind_outstanding, 2),

        # Credit notes
        "unreconciled_credits_count":  int(credit_row.cnt or 0),
        "unreconciled_credits_amount": round(flt(credit_row.amount), 2),

        # Period-scoped
        "invoices_in_range":      invoices_in_range,
        "invoiced_in_range":      invoiced_in_range,
        "outstanding_in_range":   outstanding_in_range,
        "unallocated_payments":   unallocated_payments,
    }


# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------

def _build_activity_feed(from_dt, to_dt, corp):
    items = []
    items += _feed_unpaid_corporate_invoices(from_dt, to_dt, corp)
    items += _feed_open_guest_folios(from_dt, to_dt)
    items += _feed_unapplied_payments(from_dt, to_dt)

    items.sort(key=lambda x: x.get("_sort_date", ""), reverse=True)

    feed = []
    for i, item in enumerate(items[:50], start=1):
        item.pop("_sort_date", None)
        item["id"] = i
        feed.append(item)
    return feed


def _feed_unpaid_corporate_invoices(from_dt, to_dt, corp):
    if not corp:
        return []
    invoices = frappe.db.sql("""
        SELECT name, customer, outstanding_amount, due_date, posting_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND outstanding_amount > 0
          AND is_return = 0
          AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
          AND customer IN %(c)s
        ORDER BY posting_date DESC
        LIMIT 10
    """, {"from_dt": str(from_dt), "to_dt": str(to_dt), "c": tuple(corp)}, as_dict=True)

    today = getdate(nowdate())
    items = []
    for inv in invoices:
        is_overdue = inv.due_date and getdate(inv.due_date) < today
        status = "Follow-up" if is_overdue else "Unpaid"
        days_label = (
            f"overdue by {(today - getdate(inv.due_date)).days} days"
            if is_overdue and inv.due_date
            else f"due {inv.due_date}" if inv.due_date else "no due date set"
        )
        items.append({
            "title":      f"Invoice {inv.name} posted to {inv.customer}",
            "desc":       f"Corporate invoice \u2022 \u20a6{_fmt(inv.outstanding_amount)} outstanding \u2022 {days_label}",
            "status":     status,
            "_sort_date": str(inv.posting_date),
        })
    return items


def _feed_open_guest_folios(from_dt, to_dt):
    if not frappe.db.table_exists("Hotel Room Check In"):
        return []
    checkins = frappe.db.sql("""
        SELECT ci.name, ci.guest, ci.room_number, ci.total_outstanding_amount,
               DATE(ci.expected_check_out_datetime) AS checkout_date
        FROM `tabHotel Room Check In` ci
        WHERE ci.docstatus = 1
          AND ci.status = 'Checked In'
          AND ci.total_outstanding_amount > 0
          AND DATE(ci.expected_check_out_datetime) BETWEEN %s AND %s
        ORDER BY ci.expected_check_out_datetime ASC
        LIMIT 8
    """, (str(from_dt), str(to_dt)), as_dict=True)

    items = []
    for ci in checkins:
        items.append({
            "title":      f"Guest folio {ci.name} awaiting checkout settlement",
            "desc":       f"Room {ci.room_number} \u2022 {ci.guest} \u2022 \u20a6{_fmt(ci.total_outstanding_amount)} balance \u2022 departure {ci.checkout_date}",
            "status":     "Open",
            "_sort_date": str(ci.checkout_date),
        })
    return items


def _feed_unapplied_payments(from_dt, to_dt):
    payments = frappe.db.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "payment_type": "Receive",
            "party_type": "Customer",
            "unallocated_amount": [">", 0],
            "posting_date": ["between", [from_dt, to_dt]],
        },
        fields=["name", "party", "mode_of_payment", "unallocated_amount", "posting_date", "reference_no"],
        order_by="posting_date desc",
        limit=8,
    )
    items = []
    for pe in payments:
        ref_label = f"Ref: {pe.reference_no}" if pe.reference_no else "No reference"
        items.append({
            "title":      f"Receipt {pe.name} received and awaiting allocation",
            "desc":       f"{pe.mode_of_payment} \u2022 \u20a6{_fmt(pe.unallocated_amount)} unallocated \u2022 {pe.party} \u2022 {ref_label}",
            "status":     "Unapplied",
            "_sort_date": str(pe.posting_date),
        })
    return items


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

def _build_insights(today, corp):
    return {
        "corp_aging":               _aging(today, corp, corporate=True),
        "ind_aging":                _aging(today, corp, corporate=False),
        "unreconciled_credits":     _unreconciled_credits(),
        "corporate_followup_count": _corporate_followup_count(today, corp),
        "checkout_risk_count":      _checkout_risk_count(),
    }


def _aging(today, corp, corporate=True):
    """4-bucket aging from allocation-aware receivable balances."""
    if corporate and not corp:
        return {"current": 0.0, "days_1_30": 0.0, "days_31_60": 0.0, "days_60_plus": 0.0, "total": 0.0}

    if corporate:
        party_filter = "AND ple.party IN %(c)s"
        params = {"c": tuple(corp)}
    elif corp:
        party_filter = "AND ple.party NOT IN %(c)s"
        params = {"c": tuple(corp)}
    else:
        party_filter = ""
        params = {}

    rows = frappe.db.sql(f"""
        SELECT
            t.target_voucher,
            t.outstanding,
            si.due_date
        FROM (
            SELECT
                CASE
                    WHEN IFNULL(ple.against_voucher_type, '') = 'Sales Invoice'
                     AND IFNULL(ple.against_voucher_no, '') != ''
                    THEN ple.against_voucher_no
                    ELSE ple.voucher_no
                END AS target_voucher,
                SUM(ple.amount) AS outstanding
            FROM `tabPayment Ledger Entry` ple
            WHERE ple.docstatus = 1
              AND ple.account_type = 'Receivable'
              AND ple.party_type = 'Customer'
              AND ple.delinked = 0
                            AND ple.posting_date <= %(as_of)s
              {party_filter}
            GROUP BY target_voucher
            HAVING SUM(ple.amount) > 0.5
        ) t
        LEFT JOIN `tabSales Invoice` si ON si.name = t.target_voucher
        """, {**params, "as_of": str(today)}, as_dict=True)

    current = days_1_30 = days_31_60 = days_60_plus = 0.0
    for r in rows:
        amt = flt(r.outstanding)
        if not r.due_date or getdate(r.due_date) >= today:
            current += amt
        else:
            od = (today - getdate(r.due_date)).days
            if od <= 30:
                days_1_30 += amt
            elif od <= 60:
                days_31_60 += amt
            else:
                days_60_plus += amt

    total = round(current + days_1_30 + days_31_60 + days_60_plus, 2)
    return {
        "current":      round(current, 2),
        "days_1_30":    round(days_1_30, 2),
        "days_31_60":   round(days_31_60, 2),
        "days_60_plus": round(days_60_plus, 2),
        "total":        total,
    }


def _unreconciled_credits():
    """List of unreconciled credit notes AND unallocated payment entries, grouped by customer."""
    # Credit notes (Sales Invoice returns with outstanding balance)
    cn_rows = frappe.db.sql("""
        SELECT customer, COUNT(*) AS cnt,
               ABS(SUM(outstanding_amount)) AS amount
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_return = 1
          AND outstanding_amount < 0
        GROUP BY customer
        ORDER BY ABS(SUM(outstanding_amount)) DESC
    """, as_dict=True)

    # Unallocated Payment Entries (overpayments available to settle invoices)
    pe_rows = frappe.db.sql("""
        SELECT party AS customer, COUNT(*) AS cnt,
               SUM(unallocated_amount) AS amount
        FROM `tabPayment Entry`
        WHERE docstatus = 1
          AND payment_type = 'Receive'
          AND party_type = 'Customer'
          AND unallocated_amount > 0
        GROUP BY party
        ORDER BY SUM(unallocated_amount) DESC
    """, as_dict=True)

    # Merge both into a per-customer map
    merged = {}
    for r in cn_rows:
        merged[r.customer] = merged.get(r.customer, {"customer": r.customer, "credit_note_count": 0, "credit_note_amount": 0.0, "overpayment_count": 0, "overpayment_amount": 0.0})
        merged[r.customer]["credit_note_count"] += int(r.cnt)
        merged[r.customer]["credit_note_amount"] += flt(r.amount)
    for r in pe_rows:
        merged[r.customer] = merged.get(r.customer, {"customer": r.customer, "credit_note_count": 0, "credit_note_amount": 0.0, "overpayment_count": 0, "overpayment_amount": 0.0})
        merged[r.customer]["overpayment_count"] += int(r.cnt)
        merged[r.customer]["overpayment_amount"] += flt(r.amount)

    by_customer = []
    for cust, d in sorted(merged.items(), key=lambda x: -(x[1]["credit_note_amount"] + x[1]["overpayment_amount"])):
        by_customer.append({
            "customer": cust,
            "amount": round(d["credit_note_amount"] + d["overpayment_amount"], 2),
            "credit_note_count": d["credit_note_count"],
            "credit_note_amount": round(d["credit_note_amount"], 2),
            "overpayment_count": d["overpayment_count"],
            "overpayment_amount": round(d["overpayment_amount"], 2),
        })

    total_count = sum(d["credit_note_count"] + d["overpayment_count"] for d in by_customer)
    total_amount = round(sum(d["amount"] for d in by_customer), 2)

    return {
        "total_count":  total_count,
        "total_amount": total_amount,
        "by_customer":  by_customer[:10],
        # Separate totals for UI differentiation
        "credit_note_total": round(sum(flt(r.amount) for r in cn_rows), 2),
        "overpayment_total": round(sum(flt(r.amount) for r in pe_rows), 2),
    }


# ---------------------------------------------------------------------------
# Register/list endpoints used by the billing pages
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_payment_register(from_date=None, to_date=None):
    """Return live customer receipt rows for the billing Payment List."""
    filters = [
        "pe.docstatus = 1",
        "pe.payment_type = 'Receive'",
        "pe.party_type = 'Customer'",
        "IFNULL(pe.party, '') != ''",
    ]
    values = {}
    if from_date:
        filters.append("pe.posting_date >= %(from_date)s")
        values["from_date"] = str(getdate(from_date))
    if to_date:
        filters.append("pe.posting_date <= %(to_date)s")
        values["to_date"] = str(getdate(to_date))

    rows = frappe.db.sql(f"""
        SELECT
            pe.name,
            pe.party,
            pe.party_name,
            pe.mode_of_payment,
            pe.reference_no,
            pe.posting_date,
            pe.paid_amount,
            pe.unallocated_amount
        FROM `tabPayment Entry` pe
        WHERE {" AND ".join(filters)}
        ORDER BY pe.posting_date DESC, pe.creation DESC
        LIMIT 1000
    """, values, as_dict=True)

    today = getdate(nowdate())
    month_start = today.replace(day=1)
    stats = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN posting_date = %(today)s THEN paid_amount ELSE 0 END) AS received_today,
            SUM(CASE WHEN posting_date >= %(month_start)s AND posting_date <= %(today)s THEN paid_amount ELSE 0 END) AS received_month
        FROM `tabPayment Entry`
        WHERE docstatus = 1
          AND payment_type = 'Receive'
          AND party_type = 'Customer'
          AND IFNULL(party, '') != ''
    """, {"today": str(today), "month_start": str(month_start)}, as_dict=True)[0]

    return {
        "stats": {
            "received_today": round(flt(stats.received_today), 2),
            "received_month": round(flt(stats.received_month), 2),
        },
        "payments": [_payment_register_row(row) for row in rows],
    }


@frappe.whitelist()
def get_payment_entry_detail(payment_entry):
    """Return Payment Entry details for the billing Payment List view action."""
    if not payment_entry:
        frappe.throw("Payment Entry is required")

    pe = frappe.get_doc("Payment Entry", payment_entry)
    if pe.docstatus != 1:
        frappe.throw("Payment Entry must be submitted")

    references = []
    for row in pe.references or []:
        references.append({
            "reference_doctype": row.reference_doctype,
            "reference_name": row.reference_name,
            "total_amount": round(flt(row.total_amount), 2),
            "outstanding_amount": round(flt(row.outstanding_amount), 2),
            "allocated_amount": round(flt(row.allocated_amount), 2),
        })

    return {
        "name": pe.name,
        "party": pe.party,
        "party_name": pe.party_name or pe.party,
        "posting_date": str(pe.posting_date) if pe.posting_date else "",
        "mode_of_payment": pe.mode_of_payment or "",
        "reference_no": pe.reference_no or "",
        "reference_date": str(pe.reference_date) if pe.reference_date else "",
        "paid_amount": round(flt(pe.paid_amount), 2),
        "received_amount": round(flt(pe.received_amount), 2),
        "unallocated_amount": round(flt(pe.unallocated_amount), 2),
        "remarks": pe.remarks or "",
        "references": references,
    }


@frappe.whitelist()
def record_customer_payment(
    customer,
    mode_of_payment,
    paid_amount,
    payment_date=None,
    reference_no=None,
    reference_date=None,
    remarks=None,
):
    """Create and submit an unallocated customer receipt from the billing Payment List."""
    if not customer:
        frappe.throw("Customer is required")
    if not mode_of_payment:
        frappe.throw("Mode of payment is required")

    paid_amount = flt(paid_amount)
    if paid_amount <= 0:
        frappe.throw("Payment amount must be greater than zero")

    if not frappe.db.exists("Customer", customer):
        frappe.throw("Customer {0} does not exist".format(customer))

    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw("Default company is not set")

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
    pe.party = customer
    pe.paid_from = receivable_account
    pe.paid_from_account_type = "Receivable"
    pe.paid_to = mop_account
    pe.posting_date = payment_date or frappe_today()
    pe.paid_amount = paid_amount
    pe.received_amount = paid_amount
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

    pe.insert(ignore_permissions=True)
    try:
        pe.submit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Customer payment submit failed from payment list")

    frappe.db.commit()
    return {"payment_entry": pe.name}


@frappe.whitelist()
def get_invoice_register(from_date=None, to_date=None):
    """Return live Sales Invoice and credit note rows for the billing Invoice List."""
    source_field = "custom_invoice_source" if frappe.db.has_column("Sales Invoice", "custom_invoice_source") else None
    checkin_field = "custom_hotel_room_check_in" if frappe.db.has_column("Sales Invoice", "custom_hotel_room_check_in") else None
    checkin_table_exists = frappe.db.table_exists("Hotel Room Check In")

    source_select = f"si.`{source_field}` AS invoice_source," if source_field else "'' AS invoice_source,"
    checkin_select = f"si.`{checkin_field}` AS check_in," if checkin_field else "'' AS check_in,"
    room_select = "ci.room_number AS room_number," if checkin_field and checkin_table_exists else "'' AS room_number,"
    room_join = (
        f"LEFT JOIN `tabHotel Room Check In` ci ON ci.name = si.`{checkin_field}`"
        if checkin_field and checkin_table_exists
        else ""
    )

    filters = ["si.docstatus = 1", "si.grand_total != 0"]
    values = {}
    if from_date:
        filters.append("si.posting_date >= %(from_date)s")
        values["from_date"] = str(getdate(from_date))
    if to_date:
        filters.append("si.posting_date <= %(to_date)s")
        values["to_date"] = str(getdate(to_date))

    rows = frappe.db.sql(f"""
        SELECT
            si.name,
            si.customer,
            si.customer_name,
            si.posting_date,
            si.due_date,
            si.grand_total,
            si.outstanding_amount,
            si.is_return,
            si.status,
            {source_select}
            {checkin_select}
            {room_select}
            GROUP_CONCAT(DISTINCT sii.item_group ORDER BY sii.idx SEPARATOR ', ') AS item_groups
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        {room_join}
        WHERE {" AND ".join(filters)}
        GROUP BY si.name
        ORDER BY si.posting_date DESC, si.creation DESC
        LIMIT 1000
    """, values, as_dict=True)

    return {"invoices": [_invoice_register_row(row) for row in rows]}


def _payment_register_row(row):
    paid = flt(row.paid_amount)
    unallocated = flt(row.unallocated_amount)
    allocated = max(0, paid - unallocated)
    if unallocated <= 0.005:
        status = "Allocated"
    elif allocated <= 0.005:
        status = "Unallocated"
    else:
        status = "Part Allocated"

    return {
        "receiptNo": row.name,
        "payer": row.party_name or row.party,
        "payerNote": row.party,
        "method": row.mode_of_payment or "Unknown",
        "reference": row.reference_no or "",
        "date": str(row.posting_date),
        "amount": round(paid, 2),
        "allocated": round(allocated, 2),
        "unallocated": round(unallocated, 2),
        "status": status,
    }


def _invoice_register_row(row):
    outstanding = flt(row.outstanding_amount)
    grand_total = flt(row.grand_total)
    is_return = bool(row.is_return)
    status = _invoice_status(row.status, outstanding, row.due_date, grand_total, is_return)

    return {
        "invoiceNo": row.name,
        "guest": row.customer_name or row.customer,
        "guestNote": row.customer,
        "room": row.room_number or "",
        "type": "Credit Note" if is_return else row.invoice_source or _invoice_type_from_item_groups(row.item_groups),
        "issueDate": str(row.posting_date),
        "dueDate": str(row.due_date) if row.due_date else "",
        "amount": round(grand_total, 2),
        "balance": round(outstanding, 2),
        "status": status,
    }


def _invoice_status(status, outstanding, due_date, grand_total, is_return=False):
    if is_return:
        return "Credit Note" if outstanding < -0.005 else "Paid"
    if outstanding <= 0.005:
        return "Paid"
    if due_date and getdate(due_date) < getdate(nowdate()):
        return "Overdue"
    if status in ("Partly Paid", "Part Paid") or outstanding < grand_total - 0.005:
        return "Part Paid"
    return "Unpaid"


def _invoice_type_from_item_groups(item_groups):
    value = (item_groups or "").strip()
    if not value:
        return "Sales Invoice"
    first = value.split(",", 1)[0].strip()
    return first or "Sales Invoice"


def _corporate_followup_count(today, corp):
    if not corp:
        return 0
    cutoff = add_days(today, 2)
    result = frappe.db.sql("""
        SELECT COUNT(*) AS cnt
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND outstanding_amount > 0
          AND due_date BETWEEN %(today)s AND %(cutoff)s
          AND customer IN %(c)s
    """, {"today": str(today), "cutoff": str(cutoff), "c": tuple(corp)}, as_dict=True)
    return result[0].cnt if result else 0


def _checkout_risk_count():
    if not frappe.db.table_exists("Hotel Room Check In"):
        return 0
    result = frappe.db.sql("""
        SELECT COUNT(*) AS cnt
        FROM `tabHotel Room Check In`
        WHERE docstatus = 1 AND status = 'Checked In'
          AND total_outstanding_amount > 0
    """, as_dict=True)
    return result[0].cnt if result else 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(amount) -> str:
    amount = flt(amount)
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"