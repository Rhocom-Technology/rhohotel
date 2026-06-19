# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RoomLockMapping(Document):
    def validate(self):
        if not self.external_lock_id:
            frappe.throw(_("External Lock ID is required. Obtain this from the provider dashboard."))
        self._check_duplicate()

    def _check_duplicate(self):
        existing = frappe.db.get_value(
            "Room Lock Mapping",
            {
                "room": self.room,
                "provider": self.provider,
                "name": ["!=", self.name or ""],
            },
            "name",
        )
        if existing:
            frappe.throw(
                _("A Room Lock Mapping for room {0} and provider {1} already exists: {2}").format(
                    self.room, self.provider, existing
                )
            )
