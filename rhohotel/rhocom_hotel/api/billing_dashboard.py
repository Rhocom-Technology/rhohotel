"""
Billing Dashboard API — rhohotel
=================================
Provides a single whitelisted endpoint that powers the Billing Dashboard page.

Endpoint
--------
rhohotel.billing_dashboard.get_billing_dashboard_data

Parameters
----------
from_date : str  (YYYY-MM-DD, optional) — start of date range filter
to_date   : str  (YYYY-MM-DD, optional) — end of date range filter

Returns
-------
{
  "stats": {
    "individual_guest_balance": float,   # total outstanding on individual-guest invoices
    "corporate_balance":        float,   # total outstanding on corporate-account invoices
    "invoices_in_range":        int,     # invoices posted within the date range
    "unallocated_payments":     int      # payment entries with unallocated amount > 0
  },
  "activity_feed": [
    {
      "id":     str,
      "title":  str,
      "desc":   str,
      "status": str   # "Unpaid" | "Follow-up" | "Open" | "Unapplied"
    },
    ...
  ],
  "insights": {
    "corporate_aging": {
      "current":   float,   # outstanding on corporate invoices due today or later
      "days_1_30": float,   # overdue 1-30 days
      "days_31_plus": float # overdue 31+ days
    },
    "corporate_followup_count": int,  # corporate invoices due within 48 hours
    "checkout_risk_count":      int   # in-house reservations with unsettled folio balance
  }
}
"""

import frappe
from frappe.utils import flt, getdate, nowdate, add_days


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_billing_dashboard_data(from_date=None, to_date=None):
    """
    Central data loader for the Billing Dashboard page.

    When from_date / to_date are supplied the date-sensitive stat
    (invoices_in_range) is scoped to that window; all balance / aging
    figures always reflect the live outstanding state regardless of the
    date filter.
    """
    today = getdate(nowdate())
    from_dt = getdate(from_date) if from_date else add_days(today, -7)
    to_dt   = getdate(to_date)   if to_date   else today

    stats         = _build_stats(from_dt, to_dt, today)
    activity_feed = _build_activity_feed(from_dt, to_dt)
    insights      = _build_insights(today)

    return {
        "stats":         stats,
        "activity_feed": activity_feed,
        "insights":      insights,
    }


# ---------------------------------------------------------------------------
# Shared helpers — corporate customer resolution
# ---------------------------------------------------------------------------

def _get_corporate_customers():
    """Return ERPNext Customer names linked to Hotel Guests of type Corporate.
    Mirrors the logic in corporate_billing.py exactly."""
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
    return [r.customer for r in rows if r.customer]


# ---------------------------------------------------------------------------
# Stats block
# ---------------------------------------------------------------------------

def _build_stats(from_dt, to_dt, today):
    """KPI cards on the dashboard."""

    individual = _invoice_totals("Guest")
    corporate = _invoice_totals("Corporate")

    individual_balance = individual["receivable"]
    corporate_balance = corporate["receivable"]

    total_receivables = round(individual_balance + corporate_balance, 2)
    total_invoiced = round(individual["invoiced"] + corporate["invoiced"], 2)
    total_paid = round(individual["paid"] + corporate["paid"], 2)

    invoices_in_range = frappe.db.count(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "posting_date": ["between", [from_dt, to_dt]],
        },
    )

    unallocated_payments = frappe.db.count(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "unallocated_amount": [">", 0],
            "posting_date": ["between", [from_dt, to_dt]],
        },
    )

    return {
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_receivables": total_receivables,

        "individual_invoiced": individual["invoiced"],
        "individual_paid": individual["paid"],
        "individual_guest_balance": individual_balance,

        "corporate_invoiced": corporate["invoiced"],
        "corporate_paid": corporate["paid"],
        "corporate_balance": corporate_balance,

        "invoices_in_range": invoices_in_range,
        "unallocated_payments": unallocated_payments,
    }
    
    
def _outstanding_balance(payer_type: str) -> float:
    """
    Sum outstanding_amount on submitted Sales Invoices.
    Corporate  → invoices whose customer is in the Hotel Guest corporate list.
    Guest      → all other submitted invoices with outstanding > 0.
    Mirrors the approach used in corporate_billing.py.
    """
    corporate_customers = _get_corporate_customers()

    if payer_type == "Corporate":
        if not corporate_customers:
            return 0.0
        rows = frappe.db.sql(
            """
            SELECT SUM(outstanding_amount) AS total
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND outstanding_amount > 0
              AND customer IN %(customers)s
            """,
            {"customers": tuple(corporate_customers)},
            as_dict=True,
        )
        return flt((rows[0].total or 0) if rows else 0, 2)
    else:
        # Guest: all outstanding invoices NOT belonging to corporate customers
        if corporate_customers:
            rows = frappe.db.sql(
                """
                SELECT SUM(outstanding_amount) AS total
                FROM `tabSales Invoice`
                WHERE docstatus = 1
                  AND outstanding_amount > 0
                  AND customer NOT IN %(customers)s
                """,
                {"customers": tuple(corporate_customers)},
                as_dict=True,
            )
        else:
            rows = frappe.db.sql(
                """
                SELECT SUM(outstanding_amount) AS total
                FROM `tabSales Invoice`
                WHERE docstatus = 1
                  AND outstanding_amount > 0
                """,
                as_dict=True,
            )
        return flt((rows[0].total or 0) if rows else 0, 2)


def _build_activity_feed(from_dt, to_dt):
    """
    Build a unified activity feed from:
      • Recent unpaid / overdue corporate invoices
      • Open guest folios (check-in records with balance)
      • Unapplied payment entries
      • Corporate follow-up reminders
    Sorted newest-first; capped at 20 items.
    """
    items = []
    items += _feed_unpaid_corporate_invoices(from_dt, to_dt)
    items += _feed_open_guest_folios(from_dt, to_dt)
    items += _feed_unapplied_payments(from_dt, to_dt)

    # Sort by a combined date key descending
    items.sort(key=lambda x: x.get("_sort_date", ""), reverse=True)

    # Strip internal sort key and add sequential ids
    feed = []
    for i, item in enumerate(items[:50], start=1):
        item.pop("_sort_date", None)
        item["id"] = i
        feed.append(item)

    return feed


def _feed_unpaid_corporate_invoices(from_dt, to_dt):
    """Submitted corporate invoices that are still outstanding in the date range."""
    corporate_customers = _get_corporate_customers()
    if not corporate_customers:
        return []

    invoices = frappe.db.sql(
        """
        SELECT name, customer, outstanding_amount, due_date, posting_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND outstanding_amount > 0
          AND posting_date BETWEEN %(from_dt)s AND %(to_dt)s
          AND customer IN %(customers)s
        ORDER BY posting_date DESC
        LIMIT 10
        """,
        {"from_dt": str(from_dt), "to_dt": str(to_dt), "customers": tuple(corporate_customers)},
        as_dict=True,
    )

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
            "desc":       f"Corporate invoice • ₦{_fmt(inv.outstanding_amount)} outstanding • {days_label}",
            "status":     status,
            "_sort_date": str(inv.posting_date),
        })
    return items


def _feed_open_guest_folios(from_dt, to_dt):
    """Hotel check-ins with an outstanding balance (open guest folios)."""
    if not frappe.db.table_exists("Hotel Room Check In"):
        return []

    checkins = frappe.db.sql("""
        SELECT
            ci.name,
            ci.guest,
            ci.room_number,
            ci.total_outstanding_amount,
            DATE(ci.expected_check_out_datetime) AS checkout_date
        FROM `tabHotel Room Check In` ci
        WHERE
            ci.docstatus = 1
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
            "desc":       (
                f"Room {ci.room_number} • {ci.guest} • "
                f"₦{_fmt(ci.total_outstanding_amount)} balance • "
                f"departure {ci.checkout_date}"
            ),
            "status":     "Open",
            "_sort_date": str(ci.checkout_date),
        })
    return items
def _feed_unapplied_payments(from_dt, to_dt):
    """Submitted payment entries with unallocated amounts in the date range."""
    payments = frappe.db.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
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
            "desc":       (
                f"{pe.mode_of_payment} • ₦{_fmt(pe.unallocated_amount)} unallocated • "
                f"{pe.party} • {ref_label}"
            ),
            "status":     "Unapplied",
            "_sort_date": str(pe.posting_date),
        })
    return items


# ---------------------------------------------------------------------------
# Insights panel
# ---------------------------------------------------------------------------

def _build_insights(today):
    """Right-panel insight cards."""
    aging   = _corporate_aging(today)
    followup = _corporate_followup_count(today)
    risk     = _checkout_risk_count()

    return {
        "corporate_aging":         aging,
        "corporate_followup_count": followup,
        "checkout_risk_count":     risk,
    }


def _corporate_aging(today):
    """Break down outstanding corporate invoice balances into 4 age buckets."""
    corporate_customers = _get_corporate_customers()
    if not corporate_customers:
        return {"current": 0.0, "days_1_30": 0.0, "days_31_60": 0.0, "days_60_plus": 0.0, "total": 0.0}

    invoices = frappe.db.sql(
        """
        SELECT outstanding_amount, due_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND outstanding_amount > 0
          AND customer IN %(customers)s
        """,
        {"customers": tuple(corporate_customers)},
        as_dict=True,
    )

    current = days_1_30 = days_31_60 = days_60_plus = 0.0
    for inv in invoices:
        amt = flt(inv.outstanding_amount)
        if not inv.due_date or getdate(inv.due_date) >= today:
            current += amt
        else:
            overdue_days = (today - getdate(inv.due_date)).days
            if overdue_days <= 30:
                days_1_30 += amt
            elif overdue_days <= 60:
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


def _corporate_followup_count(today):
    """Number of corporate invoices due within the next 48 hours."""
    corporate_customers = _get_corporate_customers()
    if not corporate_customers:
        return 0

    cutoff = add_days(today, 2)
    result = frappe.db.sql(
        """
        SELECT COUNT(*) AS cnt
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND outstanding_amount > 0
          AND due_date BETWEEN %(today)s AND %(cutoff)s
          AND customer IN %(customers)s
        """,
        {"today": str(today), "cutoff": str(cutoff), "customers": tuple(corporate_customers)},
        as_dict=True,
    )
    return result[0].cnt if result else 0


def _checkout_risk_count():
    """Number of in-house check-ins that still have an outstanding balance."""
    if not frappe.db.table_exists("Hotel Room Check In"):
        return 0

    # Use total_outstanding_amount directly on the doctype — avoids N+1 queries.
    result = frappe.db.sql(
        """
        SELECT COUNT(*) AS cnt
        FROM `tabHotel Room Check In`
        WHERE docstatus = 1
          AND status = 'Checked In'
          AND total_outstanding_amount > 0
        """,
        as_dict=True,
    )
    return result[0].cnt if result else 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(amount) -> str:
    """Format a number with commas, no decimals when whole, e.g. 1,250,000."""
    amount = flt(amount)
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def _invoice_totals(payer_type):
    corporate_customers = _get_corporate_customers()

    if payer_type == "Corporate":
        if not corporate_customers:
            return {"invoiced": 0, "paid": 0, "receivable": 0}

        rows = frappe.db.sql("""
            SELECT
                SUM(grand_total) AS invoiced,
                SUM(grand_total - outstanding_amount) AS paid,
                SUM(outstanding_amount) AS receivable
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND customer IN %(customers)s
        """, {
            "customers": tuple(corporate_customers)
        }, as_dict=True)

    else:
        if corporate_customers:
            rows = frappe.db.sql("""
                SELECT
                    SUM(grand_total) AS invoiced,
                    SUM(grand_total - outstanding_amount) AS paid,
                    SUM(outstanding_amount) AS receivable
                FROM `tabSales Invoice`
                WHERE docstatus = 1
                  AND customer NOT IN %(customers)s
            """, {
                "customers": tuple(corporate_customers)
            }, as_dict=True)
        else:
            rows = frappe.db.sql("""
                SELECT
                    SUM(grand_total) AS invoiced,
                    SUM(grand_total - outstanding_amount) AS paid,
                    SUM(outstanding_amount) AS receivable
                FROM `tabSales Invoice`
                WHERE docstatus = 1
            """, as_dict=True)

    row = rows[0] if rows else {}

    return {
        "invoiced": flt(row.invoiced or 0),
        "paid": flt(row.paid or 0),
        "receivable": flt(row.receivable or 0),
    }