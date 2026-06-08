# Copyright (c) 2025
# Rhocom Technology Ltd

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class BillTransfer(Document):

    # --------------------------------------
    # VALIDATION
    # --------------------------------------
    def validate(self):
        if self.from_guest == self.to_guest:
            frappe.throw("You cannot transfer a bill to the same guest.")

        if self.total_amount <= 0:
            frappe.throw("Total amount must be greater than zero.")

        if not self.source_invoice:
            frappe.throw("Source Invoice is required to process bill transfer.")

    # --------------------------------------
    # SUBMISSION LOGIC
    # --------------------------------------
    def on_submit(self):
        if self.status != "Approved":
            frappe.throw("Bill Transfer must be approved before submission.")

        self.create_journal_entry()

    # --------------------------------------
    #   CREATE ONE JOURNAL ENTRY
    # --------------------------------------
    def create_journal_entry(self):

        # Get the company from the source invoice
        company = frappe.db.get_value("Sales Invoice", self.source_invoice, "company")
        
        # Load the source invoice
        inv = frappe.get_doc("Sales Invoice", self.source_invoice)

        # The customer on the source invoice (Guest A)
        invoice_customer = inv.customer

        # Resolve Guest B's ERPNext Customer
        to_guest_customer = frappe.db.get_value("Hotel Guest", self.to_guest, "customer")
        if not to_guest_customer:
            frappe.throw(f"Guest '{self.to_guest}' does not have a linked Customer record.")

        # Fetch the company's default receivable account
        receivable_account = frappe.db.get_value(
            "Company",
            company,
            "default_receivable_account"
        )

        if not receivable_account:
            frappe.throw("Default Receivable Account is not set in Company master.")

        # ---------------------------------
        # Create JE document
        # ---------------------------------
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Journal Entry"
        je.posting_date = nowdate()
        je.company = company
        je.custom_hotel_room_check_in = self.to_check_in
        je.user_remark = f"Bill Transfer from {self.from_guest} to {self.to_guest} ({self.name})"

        # ----------------------------
        # Line 1 — CREDIT Guest A
        # ----------------------------
        je.append("accounts", {
            "account": receivable_account,
            "party_type": "Customer",
            "party": invoice_customer,
            "credit_in_account_currency": self.total_amount,
            "debit_in_account_currency": 0,
            "reference_type": "Sales Invoice",
            "reference_name": self.source_invoice
        })

        # ----------------------------
        # Line 2 — DEBIT Guest B
        # ----------------------------
        je.append("accounts", {
            "account": receivable_account,
            "party_type": "Customer",
            "party": to_guest_customer,
            "debit_in_account_currency": self.total_amount,
            "credit_in_account_currency": 0
        })

        # Save & Submit JE
        je.flags.ignore_permissions = True
        je.insert(ignore_permissions=True)
        je.submit()

        # Store link
        self.journal_entry = je.name
        self.db_set("journal_entry", je.name)

        try:
            from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

            if self.from_check_in:
                sync_checkin_folio_totals(self.from_check_in)
            if self.to_check_in:
                sync_checkin_folio_totals(self.to_check_in)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Bill Transfer folio sync failed")

        frappe.msgprint(f"Journal Entry <b>{je.name}</b> created successfully.")


# --------------------
#   APPROVAL METHOD
# --------------------
@frappe.whitelist()
def approve_transfer(docname):
    doc = frappe.get_doc("Bill Transfer", docname)

    if "Manager" not in frappe.get_roles():
        frappe.throw("Only users with Manager role can approve Bill Transfers.")

    if doc.status != "Pending Approval":
        frappe.throw("Bill Transfer is not in Pending Approval state.")

    doc.status = "Approved"
    doc.authorized_by = frappe.session.user
    doc.save()

    frappe.msgprint("Bill Transfer approved. You can now Submit the document.")


# ------------------------------------------
#   LIST / FILTER API
# ------------------------------------------
@frappe.whitelist()
def get_bill_transfers(status="", from_date="", to_date="", search=""):
    """Return list of Bill Transfer documents for the frontend list page."""
    conditions = []
    values = {}

    if status:
        conditions.append("bt.status = %(status)s")
        values["status"] = status

    if from_date:
        conditions.append("DATE(bt.creation) >= %(from_date)s")
        values["from_date"] = from_date

    if to_date:
        conditions.append("DATE(bt.creation) <= %(to_date)s")
        values["to_date"] = to_date

    if search:
        s = f"%{search}%"
        conditions.append(
            "(bt.name LIKE %(s)s OR bt.from_guest LIKE %(s)s OR bt.to_guest LIKE %(s)s OR bt.source_invoice LIKE %(s)s)"
        )
        values["s"] = s

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            bt.name,
            bt.status,
            bt.from_guest,
            bt.to_guest,
            bt.from_check_in,
            bt.to_check_in,
            bt.source_invoice,
            bt.total_amount,
            bt.reason,
            bt.authorized_by,
            bt.journal_entry,
            bt.creation,
            bt.modified
        FROM `tabBill Transfer` bt
        {where}
        ORDER BY bt.creation DESC
        LIMIT 200
        """,
        values,
        as_dict=True,
    )

    return rows or []


# ------------------------------------------
#   APPROVE AND EXECUTE (frontend workflow)
# ------------------------------------------
@frappe.whitelist()
def approve_and_execute_transfer(docname):
    """Approve and submit a Bill Transfer document, creating the journal entry."""
    doc = frappe.get_doc("Bill Transfer", docname)

    if doc.status not in ("Pending Approval", "Draft"):
        frappe.throw(f"Bill Transfer {docname} is not in Pending Approval state.")

    doc.status = "Approved"
    doc.authorized_by = frappe.session.user
    doc.flags.ignore_permissions = True
    doc.save()
    doc.submit()

    return {"name": doc.name, "journal_entry": doc.journal_entry}


# ------------------------------------------
#   GET SINGLE TRANSFER DETAIL (with items)
# ------------------------------------------
@frappe.whitelist()
def get_bill_transfer_detail(docname):
    """Return a single Bill Transfer with its child items for the approval panel."""
    doc = frappe.get_doc("Bill Transfer", docname)
    frappe.has_permission("Bill Transfer", "read", doc=doc, throw=True)

    items = [
        {
            "description": row.description,
            "amount": row.amount,
            "reference_document": row.reference_document,
        }
        for row in (doc.items or [])
    ]

    return {
        "name": doc.name,
        "status": doc.status,
        "from_guest": doc.from_guest,
        "from_check_in": doc.from_check_in,
        "to_guest": doc.to_guest,
        "to_check_in": doc.to_check_in,
        "source_invoice": doc.source_invoice,
        "total_amount": doc.total_amount,
        "reason": doc.reason,
        "authorized_by": doc.authorized_by,
        "journal_entry": doc.journal_entry,
        "creation": str(doc.creation),
        "modified": str(doc.modified),
        "items": items,
    }


# ------------------------------------------
#   REJECT TRANSFER
# ------------------------------------------
@frappe.whitelist()
def reject_transfer(docname, rejection_reason=""):
    """Cancel/reject a Pending Approval or Draft Bill Transfer."""
    doc = frappe.get_doc("Bill Transfer", docname)

    if doc.status not in ("Pending Approval", "Draft"):
        frappe.throw(f"Bill Transfer {docname} cannot be rejected in its current state ({doc.status}).")

    doc.status = "Cancelled"
    doc.authorized_by = frappe.session.user
    if rejection_reason:
        doc.reason = (doc.reason or "") + f"\n[Rejected by {frappe.session.user}: {rejection_reason}]"
    doc.flags.ignore_permissions = True
    doc.save()

    return {"name": doc.name, "status": doc.status}
