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
from frappe.utils import flt, getdate, nowdate, add_days


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_billing_dashboard_data(from_date=None, to_date=None):
    today   = getdate(nowdate())
    from_dt = getdate(from_date) if from_date else add_days(today, -7)
    to_dt   = getdate(to_date)   if to_date   else today

    # Corporate customer list — fetched ONCE, passed everywhere
    corp = _get_corporate_customers()

    return {
        "stats":         _build_stats(from_dt, to_dt, today, corp),
        "activity_feed": _build_activity_feed(from_dt, to_dt, corp),
        "insights":      _build_insights(today, corp),
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
    """, as_dict=True)[0]

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
              AND party IN %(c)s
        """, {"c": tuple(corp)}, as_dict=True)[0]
    else:
        corp_row = {"invoiced": 0, "collected": 0, "outstanding": 0}

    corp_invoiced    = flt(corp_row.invoiced)
    corp_collected   = flt(corp_row.collected)
    corp_outstanding = flt(corp_row.outstanding)

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
              AND party NOT IN %(c)s
        """, {"c": tuple(corp)}, as_dict=True)[0]
    else:
        ind_row = total_row

    ind_invoiced    = flt(ind_row.invoiced)
    ind_collected   = flt(ind_row.collected)
    ind_outstanding = flt(ind_row.outstanding)

    # ── Overdue vs current (join SI for due_date, only net positive entries) ─
    overdue_row = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN si.due_date < %(today)s AND net.outstanding > 0
                     THEN net.outstanding ELSE 0 END) AS overdue,
            SUM(CASE WHEN (si.due_date >= %(today)s OR si.due_date IS NULL) AND net.outstanding > 0
                     THEN net.outstanding ELSE 0 END) AS current_amt
        FROM (
            SELECT voucher_no, SUM(amount) AS outstanding
            FROM `tabPayment Ledger Entry`
            WHERE docstatus = 1
              AND account_type = 'Receivable'
              AND party_type = 'Customer'
              AND delinked = 0
            GROUP BY voucher_no
        ) net
        LEFT JOIN `tabSales Invoice` si ON si.name = net.voucher_no
    """, {"today": str(today)}, as_dict=True)[0]

    total_overdue = flt(overdue_row.overdue)
    total_current = flt(overdue_row.current_amt)

    # ── Unreconciled credit notes ─────────────────────────────────────────────
    credit_row = frappe.db.sql("""
        SELECT COUNT(*) AS cnt, ABS(SUM(outstanding_amount)) AS amount
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_return = 1
          AND outstanding_amount != 0
    """, as_dict=True)[0]

    # ── Period-scoped counts ──────────────────────────────────────────────────
    invoices_in_range = frappe.db.count("Sales Invoice", filters={
        "docstatus": 1,
        "posting_date": ["between", [from_dt, to_dt]],
        "is_return": 0,
    })

    unallocated_payments = frappe.db.count("Payment Entry", filters={
        "docstatus": 1,
        "unallocated_amount": [">", 0],
        "posting_date": ["between", [from_dt, to_dt]],
    })

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
        "invoices_in_range":    invoices_in_range,
        "unallocated_payments": unallocated_payments,
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
        filters={"docstatus": 1, "unallocated_amount": [">", 0], "posting_date": ["between", [from_dt, to_dt]]},
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
    """4-bucket aging from PLE net outstanding per voucher, joined to SI for due_date."""
    if corporate and not corp:
        return {"current": 0.0, "days_1_30": 0.0, "days_31_60": 0.0, "days_60_plus": 0.0, "total": 0.0}

    party_filter = "AND ple.party IN %(c)s" if corporate else "AND ple.party NOT IN %(c)s"

    rows = frappe.db.sql(f"""
        SELECT si.due_date, SUM(ple.amount) AS outstanding
        FROM `tabPayment Ledger Entry` ple
        LEFT JOIN `tabSales Invoice` si ON si.name = ple.voucher_no
        WHERE ple.docstatus = 1
          AND ple.account_type = 'Receivable'
          AND ple.party_type = 'Customer'
          AND ple.delinked = 0
          {party_filter}
        GROUP BY ple.voucher_no
        HAVING SUM(ple.amount) > 0.5
    """, {"c": tuple(corp)} if corp else {}, as_dict=True)

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
    """List of unreconciled credit notes grouped by customer."""
    rows = frappe.db.sql("""
        SELECT customer, COUNT(*) AS cnt,
               ABS(SUM(outstanding_amount)) AS amount,
               ABS(SUM(grand_total)) AS grand_total
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_return = 1
          AND outstanding_amount != 0
        GROUP BY customer
        ORDER BY ABS(SUM(outstanding_amount)) DESC
        LIMIT 10
    """, as_dict=True)

    total = sum(flt(r.amount) for r in rows)
    return {
        "total_count":  sum(int(r.cnt) for r in rows),
        "total_amount": round(total, 2),
        "by_customer":  [
            {"customer": r.customer, "count": int(r.cnt), "amount": round(flt(r.amount), 2)}
            for r in rows
        ],
    }


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