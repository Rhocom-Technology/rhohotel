"""
Billing — Manual Payment Reconciliation API
============================================
Allows front-desk staff to apply an overpayment (unallocated Payment Entry)
against an outstanding Sales Invoice for the same customer, without involving
the accounts department.

Endpoints
---------
get_customers_with_overpayments()
get_customer_overpayment_detail(customer)
apply_overpayment_to_invoice(payment_entry, invoice_name, amount)
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

_ALLOWED_RECONCILIATION_ROLES = {
    "System Manager",
    "Accounts Manager",
    "Accounts User",
    "Hotel Manager",
    "Front Desk Manager",
    "Front Desk User",
    "Front Desk",
}


def _require_reconciliation_permission():
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles(frappe.session.user))
    if roles & _ALLOWED_RECONCILIATION_ROLES:
        return
    frappe.throw(
        _("You do not have permission to reconcile guest overpayments."),
        frappe.PermissionError,
    )


# ---------------------------------------------------------------------------
# 1. List of customers who have unallocated (overpayment) funds
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_customers_with_overpayments():
    """Return customers that have at least one Payment Entry with unallocated_amount > 0."""
    rows = frappe.db.sql("""
        SELECT
            pe.party           AS customer,
            COUNT(pe.name)     AS payment_count,
            SUM(pe.unallocated_amount) AS total_overpayment
        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
          AND pe.payment_type = 'Receive'
          AND pe.party_type = 'Customer'
          AND pe.unallocated_amount > 0
        GROUP BY pe.party
        ORDER BY SUM(pe.unallocated_amount) DESC
    """, as_dict=True)

    result = []
    for r in rows:
        outstanding = frappe.db.sql("""
            SELECT COUNT(*) AS cnt, SUM(outstanding_amount) AS total
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND customer = %s
              AND outstanding_amount > 0
              AND is_return = 0
        """, (r.customer,), as_dict=True)
        inv = outstanding[0] if outstanding else {}
        result.append({
            "customer":           r.customer,
            "payment_count":      int(r.payment_count),
            "total_overpayment":  round(flt(r.total_overpayment), 2),
            "open_invoice_count": int(inv.cnt or 0),
            "open_invoice_total": round(flt(inv.total), 2),
        })
    return result


# ---------------------------------------------------------------------------
# 2. Detail for one customer — unallocated payments + open invoices
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_customer_overpayment_detail(customer):
    """Return unallocated payments and outstanding invoices for a specific customer."""
    if not customer:
        frappe.throw(_("Customer is required."))

    payments = frappe.db.sql("""
        SELECT
            name, posting_date, mode_of_payment,
            paid_amount, unallocated_amount, reference_no
        FROM `tabPayment Entry`
        WHERE docstatus = 1
          AND payment_type = 'Receive'
          AND party_type = 'Customer'
          AND party = %s
          AND unallocated_amount > 0
        ORDER BY posting_date DESC
    """, (customer,), as_dict=True)

    # Regular Sales Invoices
    si_rows = frappe.db.sql("""
        SELECT
            name, posting_date, due_date,
            grand_total, outstanding_amount,
            debit_to
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND customer = %s
          AND outstanding_amount > 0
          AND is_return = 0
        ORDER BY due_date ASC, posting_date ASC
    """, (customer,), as_dict=True)

    # Journal Entries from bill transfers — net outstanding = JE debit minus any
    # PE credits already applied (which land under the PE's voucher_no with
    # against_voucher_no pointing back to the JE).
    je_rows = frappe.db.sql("""
        SELECT
            jd.voucher_no          AS name,
            je.posting_date,
            je.title               AS description,
            (jd.debit - COALESCE(pc.credits, 0)) AS outstanding_amount,
            jea.account            AS debit_to
        FROM (
            SELECT voucher_no, SUM(amount) AS debit
            FROM `tabPayment Ledger Entry`
            WHERE party_type = 'Customer' AND party = %(customer)s
              AND voucher_type = 'Journal Entry'
              AND delinked = 0 AND docstatus = 1
            GROUP BY voucher_no
            HAVING SUM(amount) > 0
        ) jd
        LEFT JOIN (
            SELECT against_voucher_no, ABS(SUM(amount)) AS credits
            FROM `tabPayment Ledger Entry`
            WHERE party_type = 'Customer' AND party = %(customer)s
              AND voucher_type = 'Payment Entry'
              AND against_voucher_type = 'Journal Entry'
              AND delinked = 0 AND docstatus = 1
            GROUP BY against_voucher_no
        ) pc ON pc.against_voucher_no = jd.voucher_no
        JOIN `tabJournal Entry` je ON je.name = jd.voucher_no
        JOIN `tabJournal Entry Account` jea
            ON jea.parent = jd.voucher_no
           AND jea.party_type = 'Customer'
           AND jea.party = %(customer)s
           AND jea.debit_in_account_currency > 0
        WHERE (jd.debit - COALESCE(pc.credits, 0)) > 0.5
        ORDER BY je.posting_date ASC
    """, {"customer": customer}, as_dict=True)

    invoices = []
    for inv in si_rows:
        invoices.append({
            "name":               inv.name,
            "voucher_type":       "Sales Invoice",
            "posting_date":       str(inv.posting_date),
            "due_date":           str(inv.due_date) if inv.due_date else "",
            "grand_total":        round(flt(inv.grand_total), 2),
            "outstanding_amount": round(flt(inv.outstanding_amount), 2),
            "debit_to":           inv.debit_to,
            "description":        "",
            "is_transfer":        False,
        })
    for je in je_rows:
        invoices.append({
            "name":               je.name,
            "voucher_type":       "Journal Entry",
            "posting_date":       str(je.posting_date),
            "due_date":           "",
            "grand_total":        round(flt(je.outstanding_amount), 2),
            "outstanding_amount": round(flt(je.outstanding_amount), 2),
            "debit_to":           je.debit_to,
            "description":        je.description or "",
            "is_transfer":        True,
        })

    # Sort: due_date first, then posting_date
    invoices.sort(key=lambda x: (x["due_date"] or x["posting_date"], x["posting_date"]))

    return {
        "customer": customer,
        "payments": [
            {
                "name":               p.name,
                "posting_date":       str(p.posting_date),
                "mode_of_payment":    p.mode_of_payment or "—",
                "paid_amount":        round(flt(p.paid_amount), 2),
                "unallocated_amount": round(flt(p.unallocated_amount), 2),
                "reference_no":       p.reference_no or "",
            }
            for p in payments
        ],
        "invoices": invoices,
    }


# ---------------------------------------------------------------------------
# 3. Apply overpayment to invoice
# ---------------------------------------------------------------------------

@frappe.whitelist()
def apply_overpayment_to_invoice(payment_entry, invoice_name, amount):
    """
    Apply (part of) an unallocated Payment Entry against an outstanding
    Sales Invoice OR a bill-transfer Journal Entry for the same customer.

    Uses ERPNext's reconcile_against_document which cancels the PE internally,
    adds the reference, and re-submits — keeping all GL entries correct.
    """
    _require_reconciliation_permission()

    amount = flt(amount)
    if amount <= 0:
        frappe.throw(_("Amount must be greater than zero."))

    # --- Validate Payment Entry ---
    pe = frappe.get_doc("Payment Entry", payment_entry)
    if pe.docstatus != 1:
        frappe.throw(_("Payment Entry {0} must be submitted.").format(payment_entry))
    if pe.payment_type != "Receive":
        frappe.throw(_("Only 'Receive' type Payment Entries can be reconciled this way."))
    if flt(pe.unallocated_amount) < amount - 0.001:
        frappe.throw(
            _("Payment Entry {0} only has {1} unallocated — cannot apply {2}.").format(
                payment_entry, pe.unallocated_amount, amount
            )
        )

    # --- Detect voucher type: Sales Invoice or Journal Entry (transferred bill) ---
    is_journal_entry = frappe.db.exists("Journal Entry", invoice_name)
    is_sales_invoice = (not is_journal_entry) and frappe.db.exists("Sales Invoice", invoice_name)

    if not is_journal_entry and not is_sales_invoice:
        frappe.throw(_("Voucher {0} not found as Sales Invoice or Journal Entry.").format(invoice_name))

    if is_sales_invoice:
        inv = frappe.get_doc("Sales Invoice", invoice_name)
        if inv.docstatus != 1:
            frappe.throw(_("Invoice {0} must be submitted.").format(invoice_name))
        if inv.is_return:
            frappe.throw(_("Cannot reconcile against a credit note."))
        if inv.customer != pe.party:
            frappe.throw(
                _("Payment and invoice belong to different customers ({0} vs {1}).").format(
                    pe.party, inv.customer
                )
            )
        voucher_outstanding = flt(inv.outstanding_amount)
        if voucher_outstanding < amount - 0.001:
            frappe.throw(
                _("Invoice {0} only has {1} outstanding — cannot apply {2}.").format(
                    invoice_name, voucher_outstanding, amount
                )
            )
        receivable_account = inv.debit_to
        against_voucher_type = "Sales Invoice"

    else:  # Journal Entry (bill transfer)
        # Get net outstanding for pe.party against this JE directly —
        # avoids LIMIT 1 / wrong-party issue that causes false customer mismatch.
        # Net = JE debit entries for this party MINUS PE credits already applied.
        net_result = frappe.db.sql("""
            SELECT
                COALESCE(jd.debit, 0) - COALESCE(pc.credits, 0) AS net
            FROM (
                SELECT SUM(amount) AS debit
                FROM `tabPayment Ledger Entry`
                WHERE voucher_no = %(je)s
                  AND party_type = 'Customer' AND party = %(party)s
                  AND voucher_type = 'Journal Entry'
                  AND delinked = 0 AND docstatus = 1
            ) jd
            CROSS JOIN (
                SELECT COALESCE(ABS(SUM(amount)), 0) AS credits
                FROM `tabPayment Ledger Entry`
                WHERE against_voucher_no = %(je)s
                  AND party_type = 'Customer' AND party = %(party)s
                  AND voucher_type = 'Payment Entry'
                  AND against_voucher_type = 'Journal Entry'
                  AND delinked = 0 AND docstatus = 1
            ) pc
        """, {"je": invoice_name, "party": pe.party}, as_dict=True)
        voucher_outstanding = flt(net_result[0].net if net_result and net_result[0].net else 0)
        if voucher_outstanding <= 0:
            frappe.throw(_(
                "{0} has no outstanding balance on bill transfer {1}. "
                "It may already be fully settled."
            ).format(pe.party, invoice_name))
        if voucher_outstanding < amount - 0.001:
            frappe.throw(
                _("Bill transfer {0} only has {1} outstanding — cannot apply {2}.").format(
                    invoice_name, voucher_outstanding, amount
                )
            )
        # Get receivable account from the JE line that debited this customer
        je_account = frappe.db.sql("""
            SELECT account FROM `tabJournal Entry Account`
            WHERE parent = %s AND party_type = 'Customer' AND party = %s
              AND debit_in_account_currency > 0
            LIMIT 1
        """, (invoice_name, pe.party), as_dict=True)
        if not je_account:
            frappe.throw(_("Could not determine receivable account from Journal Entry {0}.").format(invoice_name))
        receivable_account = je_account[0].account
        against_voucher_type = "Journal Entry"

    if not receivable_account:
        frappe.throw(_("Receivable account could not be determined for {0}.").format(invoice_name))

    # --- Call ERPNext reconciliation ---
    from erpnext.accounts.utils import reconcile_against_document

    reconcile_against_document(
        [
            frappe._dict(
                {
                    "voucher_type":             "Payment Entry",
                    "voucher_no":               pe.name,
                    "voucher_detail_no":        None,
                    "against_voucher_type":     against_voucher_type,
                    "against_voucher":          invoice_name,
                    "account":                  receivable_account,
                    "exchange_rate":            flt(pe.get("conversion_rate") or 1),
                    "party_type":               "Customer",
                    "party":                    pe.party,
                    "is_advance":               "No",
                    "dr_or_cr":                 "credit_in_account_currency",
                    "unreconciled_amount":       flt(pe.unallocated_amount),
                    "unadjusted_amount":         flt(pe.unallocated_amount),
                    "allocated_amount":          amount,
                    "difference_amount":         0,
                    "difference_account":        None,
                    "difference_posting_date":   None,
                    "cost_center":               None,
                }
            )
        ]
    )

    frappe.db.commit()

    # Reload PE to get updated unallocated_amount
    pe.reload()

    # For SI we can reload the doc; for JE recalculate net from PLE
    # (JE debit - PE credits applied via against_voucher_no).
    if is_sales_invoice:
        inv.reload()
        remaining_outstanding = round(flt(inv.outstanding_amount), 2)
    else:
        net = frappe.db.sql("""
            SELECT
                COALESCE(jd.debit, 0) - COALESCE(pc.credits, 0) AS net
            FROM (
                SELECT SUM(amount) AS debit FROM `tabPayment Ledger Entry`
                WHERE voucher_no = %(je)s AND party_type='Customer' AND party=%(party)s
                  AND voucher_type='Journal Entry' AND delinked=0 AND docstatus=1
            ) jd
            CROSS JOIN (
                SELECT COALESCE(ABS(SUM(amount)), 0) AS credits FROM `tabPayment Ledger Entry`
                WHERE against_voucher_no=%(je)s AND party_type='Customer' AND party=%(party)s
                  AND voucher_type='Payment Entry' AND against_voucher_type='Journal Entry'
                  AND delinked=0 AND docstatus=1
            ) pc
        """, {"je": invoice_name, "party": pe.party}, as_dict=True)
        remaining_outstanding = round(flt(net[0].net if net and net[0].net else 0), 2)

    return {
        "success":             True,
        "payment_entry":       pe.name,
        "invoice":             invoice_name,
        "applied_amount":      amount,
        "pe_remaining":        round(flt(pe.unallocated_amount), 2),
        "invoice_outstanding": remaining_outstanding,
    }
