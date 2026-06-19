# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LockProvider(Document):
    def validate(self):
        self._validate_provider_code()
        self._enforce_single_default()

    def _validate_provider_code(self):
        if not self.provider_code:
            frappe.throw(_("Provider Code is required."))
        if " " in self.provider_code:
            frappe.throw(_("Provider Code must not contain spaces. Use underscore instead (e.g. 'tt_hotel')."))

    def _enforce_single_default(self):
        """If this provider is set as default, clear the flag on all others."""
        if not self.is_default:
            return
        existing = frappe.db.get_value(
            "Lock Provider",
            {"is_default": 1, "name": ["!=", self.name]},
            "name",
        )
        if existing:
            frappe.db.set_value("Lock Provider", existing, "is_default", 0)
