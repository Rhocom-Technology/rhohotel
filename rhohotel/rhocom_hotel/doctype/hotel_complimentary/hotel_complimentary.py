import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class HotelComplimentary(Document):

    def validate(self):
        if not self.guest:
            frappe.throw("Please enter a guest name.", title="Guest Required")
        if not self.complimentary_type:
            frappe.throw("Please select a complimentary type.", title="Type Required")
        if not self.department:
            frappe.throw("Please select a department.", title="Department Required")
        if not self.approval_level:
            frappe.throw("Please select an approval level.", title="Approval Level Required")
        if not self.issue_date:
            frappe.throw("Please select an issue date.", title="Issue Date Required")
        if self.expiry_date and self.issue_date and self.expiry_date < self.issue_date:
            frappe.throw("Expiry date cannot be before the issue date.", title="Invalid Dates")
        if self.is_new():
            self.issued_by = frappe.session.user
        self._sync_redemption_amounts()

    def on_update(self):
        self._stamp_approval()
        self._stamp_consumption()

    def _stamp_approval(self):
        if self.status == "Approved" and not self.approved_on:
            self.db_set("approved_by", frappe.session.user)
            self.db_set("approved_on", now_datetime())

    def _stamp_consumption(self):
        if self.status == "Consumed" and not self.consumed_on:
            self.db_set("consumed_on", now_datetime())

    def _sync_redemption_amounts(self):
        value = flt(self.value)
        redeemed = min(max(flt(self.redeemed_amount), 0), value)
        self.redeemed_amount = redeemed
        self.remaining_value = max(value - redeemed, 0)
