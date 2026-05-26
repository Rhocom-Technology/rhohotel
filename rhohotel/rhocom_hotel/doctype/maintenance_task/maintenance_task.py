# import frappe
# from frappe.model.document import Document
# from frappe.utils import get_datetime, now_datetime


# class MaintenanceTask(Document):

#     # ── Lifecycle hooks ────────────────────────────────────────────────────────

#     def validate(self):
#         self._validate_technician_not_supervisor()
#         self._validate_dates()

#     def before_submit(self):
#         self._run_submit_validations()

#     def on_submit(self):
#         self.db_set("status", "Done")
#         self._create_stock_entries()
#         self._complete_maintenance_request()

#     def on_cancel(self):
#         self._cancel_stock_entries()
#         self._revert_maintenance_request()

#     # ── Validate ───────────────────────────────────────────────────────────────

#     def _validate_technician_not_supervisor(self):
#         if not self.assigned_technician or not self.supervisor:
#             return
#         emp = frappe.db.get_value(
#             "Maintenance Technician",
#             self.assigned_technician,
#             "employee"
#         )
#         if emp and emp == self.supervisor:
#             frappe.throw(
#                 "The assigned technician's linked employee cannot also "
#                 "be the supervisor.",
#                 title="Invalid Assignment"
#             )

#     def _validate_dates(self):
#         if self.start_time and self.end_time:
#             if get_datetime(self.end_time) <= get_datetime(self.start_time):
#                 frappe.throw("End Time must be after Start Time.")

#     # ── Before submit ──────────────────────────────────────────────────────────

#     def _run_submit_validations(self):
#         errors = []

#         if not self.start_time:
#             errors.append("• Start Time is required.")
#         if not self.end_time:
#             errors.append("• End Time is required.")
#         if self.start_time and self.end_time:
#             if get_datetime(self.end_time) <= get_datetime(self.start_time):
#                 errors.append("• End Time must be after Start Time.")
#         if not (self.work_performed or "").strip():
#             errors.append("• Work Performed is required.")
#         if self.inspection_required and not self.supervisor_verified:
#             errors.append(
#                 "• Supervisor Verified must be checked when "
#                 "Inspection Required is enabled."
#             )
#         if self.parts_used:
#             stock_errors = self._validate_parts_stock()
#             errors.extend(stock_errors)

#         if errors:
#             frappe.throw(
#                 "Please fix the following before submitting:<br><br>"
#                 + "<br>".join(errors),
#                 title="Cannot Submit"
#             )

#     def _validate_parts_stock(self):
#         errors = []
#         for idx, part in enumerate(self.parts_used, 1):
#             if part.store_impact != "Reduce Stock":
#                 continue
#             if not part.warehouse:
#                 errors.append(
#                     f"• Row {idx}: Warehouse is required for "
#                     f"<b>{part.item_code}</b> when Store Impact is "
#                     f"Reduce Stock."
#                 )
#                 continue
#             available = frappe.db.get_value(
#                 "Bin",
#                 {"item_code": part.item_code, "warehouse": part.warehouse},
#                 "actual_qty"
#             ) or 0
#             if available < (part.quantity or 0):
#                 errors.append(
#                     f"• Row {idx}: Insufficient stock for "
#                     f"<b>{part.item_code}</b> in <b>{part.warehouse}</b>. "
#                     f"Available: {available}, Required: {part.quantity}."
#                 )
#         return errors

#     # ── On submit ──────────────────────────────────────────────────────────────

#     def _create_stock_entries(self):
#         if not self.parts_used:
#             return

#         issue_parts = [
#             p for p in self.parts_used
#             if p.store_impact == "Reduce Stock"
#             and p.item_code
#             and p.warehouse
#         ]
#         receipt_parts = [
#             p for p in self.parts_used
#             if p.store_impact == "Return to Store"
#             and p.item_code
#             and p.warehouse
#         ]

#         if issue_parts:
#             self._create_stock_entry(issue_parts, "Material Issue")
#         if receipt_parts:
#             self._create_stock_entry(receipt_parts, "Material Receipt")

#     def _create_stock_entry(self, parts, purpose):
#         try:
#             company = frappe.db.get_default("company")
#             stock_entry = frappe.new_doc("Stock Entry")
#             stock_entry.stock_entry_type = purpose
#             stock_entry.company = company
#             stock_entry.remarks = (
#                 f"Maintenance Task: {self.name} — "
#                 f"Request: {self.maintenance_request or 'N/A'} — "
#                 f"Location: {self.location}"
#             )

#             for part in parts:
#                 item_uom = part.uom or frappe.db.get_value(
#                     "Item", part.item_code, "stock_uom"
#                 ) or "Nos"

#                 if purpose == "Material Issue":
#                     stock_entry.append("items", {
#                         "item_code": part.item_code,
#                         "item_name": part.item_name or "",
#                         "qty": part.quantity,
#                         "uom": item_uom,
#                         "s_warehouse": part.warehouse,
#                     })
#                 else:
#                     stock_entry.append("items", {
#                         "item_code": part.item_code,
#                         "item_name": part.item_name or "",
#                         "qty": part.quantity,
#                         "uom": item_uom,
#                         "t_warehouse": part.warehouse,
#                     })

#             stock_entry.insert(ignore_permissions=True)
#             stock_entry.submit()

#             impact = (
#                 "Reduce Stock" if purpose == "Material Issue"
#                 else "Return to Store"
#             )
#             for part in self.parts_used:
#                 if part.store_impact == impact:
#                     frappe.db.set_value(
#                         "Maintenance Parts Used",
#                         part.name,
#                         "stock_entry",
#                         stock_entry.name
#                     )

#             frappe.msgprint(
#                 f"Stock Entry <b>{stock_entry.name}</b> ({purpose}) "
#                 f"created for {len(parts)} item(s).",
#                 indicator="green",
#                 title="Stock Entry Created"
#             )

#         except frappe.ValidationError as ve:
#             frappe.log_error(
#                 frappe.get_traceback(),
#                 f"Maintenance Task {purpose} Error"
#             )
#             frappe.msgprint(
#                 f"Stock Entry ({purpose}) validation error: {str(ve)}. "
#                 "Please create manually.",
#                 indicator="yellow",
#                 title="Stock Entry Error"
#             )
#         except Exception as e:
#             frappe.log_error(
#                 frappe.get_traceback(),
#                 f"Maintenance Task {purpose} Error"
#             )
#             frappe.msgprint(
#                 f"Stock Entry ({purpose}) error: {str(e)}. "
#                 "Please create manually.",
#                 indicator="yellow",
#                 title="Stock Entry Error"
#             )

#     def _complete_maintenance_request(self):
#         if not self.maintenance_request:
#             return

#         mr = frappe.get_doc(
#             "Maintenance Request", self.maintenance_request
#         )

#         frappe.db.set_value(
#             "Maintenance Request",
#             self.maintenance_request,
#             {
#                 "status": "Completed",
#                 "completion_date": now_datetime()
#             }
#         )

#         if mr.location_type == "Room" and mr.room:
#             frappe.db.set_value(
#                 "Hotel Room", mr.room, "maintenance_flag", 0
#             )

#         frappe.db.commit()
#         frappe.msgprint(
#             f"Maintenance Request <b>{self.maintenance_request}</b> "
#             "marked as Completed.",
#             indicator="green",
#             alert=True
#         )

#     # ── On cancel ──────────────────────────────────────────────────────────────

#     def _cancel_stock_entries(self):
#         if not self.parts_used:
#             return

#         cancelled = set()
#         for part in self.parts_used:
#             if not part.stock_entry or part.stock_entry in cancelled:
#                 continue
#             try:
#                 se = frappe.get_doc("Stock Entry", part.stock_entry)
#                 if se.docstatus == 1:
#                     se.cancel()
#                     frappe.msgprint(
#                         f"Stock Entry <b>{part.stock_entry}</b> cancelled.",
#                         indicator="orange",
#                         title="Stock Entry Cancelled"
#                     )
#                 cancelled.add(part.stock_entry)
#             except Exception as e:
#                 frappe.log_error(
#                     f"Failed to cancel stock entry "
#                     f"{part.stock_entry}: {str(e)}",
#                     "Maintenance Task Cancel"
#                 )

#     def _revert_maintenance_request(self):
#         if not self.maintenance_request:
#             return

#         try:
#             mr = frappe.get_doc(
#                 "Maintenance Request", self.maintenance_request
#             )
#             if mr.status not in ("Cancelled", "Rejected"):
#                 frappe.db.set_value(
#                     "Maintenance Request",
#                     self.maintenance_request,
#                     {
#                         "status": "Cancelled",
#                         "task": None
#                     }
#                 )
#                 # Clear room flag
#                 if mr.location_type == "Room" and mr.room:
#                     frappe.db.set_value(
#                         "Hotel Room", mr.room, "maintenance_flag", 0
#                     )
#                 frappe.db.commit()
#                 frappe.msgprint(
#                     f"Maintenance Request "
#                     f"<b>{self.maintenance_request}</b> "
#                     "has been cancelled.",
#                     indicator="orange",
#                     title="Request Cancelled"
#                 )
#         except Exception as e:
#             frappe.log_error(
#                 str(e),
#                 "Maintenance Task Cancel — Request Sync"
#             )


# # ── Whitelisted methods ────────────────────────────────────────────────────────

# @frappe.whitelist()
# def approve_parts(task_name):
#     """Approve parts. Only Hotel Manager and System Manager."""
#     allowed_roles = {"System Manager", "Hotel Manager"}
#     user_roles = set(frappe.get_roles(frappe.session.user))

#     if not (allowed_roles & user_roles):
#         frappe.throw(
#             "Only a Hotel Manager or System Manager can approve parts.",
#             frappe.PermissionError
#         )

#     task = frappe.get_doc("Maintenance Task", task_name)

#     if task.docstatus == 1:
#         frappe.throw("Cannot approve parts on a submitted task.")
#     if not task.parts_used:
#         frappe.throw("No parts found on this task to approve.")

#     stock_errors = task._validate_parts_stock()
#     if stock_errors:
#         frappe.throw(
#             "Cannot approve — stock issues found:<br><br>"
#             + "<br>".join(stock_errors),
#             title="Stock Validation Failed"
#         )

#     frappe.db.set_value("Maintenance Task", task_name, {
#         "parts_approval_status": "Approved",
#         "parts_approved_by": frappe.session.user,
#         "parts_approved_on": now_datetime(),
#     })
#     frappe.db.commit()

#     return {
#         "approved_by": frappe.db.get_value(
#             "User", frappe.session.user, "full_name"
#         ),
#         "approved_on": str(now_datetime()),
#     }


# @frappe.whitelist()
# def request_part_approval(task_name):
#     """Mark parts as Pending Approval."""
#     task = frappe.get_doc("Maintenance Task", task_name)

#     if task.docstatus == 1:
#         frappe.throw("Cannot request approval on a submitted task.")
#     if not task.parts_used:
#         frappe.throw("Please add parts before requesting approval.")
#     if task.parts_approval_status == "Approved":
#         frappe.throw(
#             "Parts are already approved. "
#             "Modify parts first if re-approval is needed."
#         )

#     frappe.db.set_value("Maintenance Task", task_name, {
#         "parts_approval_status": "Pending Approval",
#         "parts_approved_by": None,
#         "parts_approved_on": None,
#     })
#     frappe.db.commit()

#     return {"status": "Pending Approval"}



import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class MaintenanceTask(Document):

    def validate(self):
        self._validate_technician_not_supervisor()
        self._validate_dates()

    def before_submit(self):
        self._run_submit_validations()

    def on_submit(self):
        # self.db_set("status", "Done")
        self._create_stock_entries()
        self._complete_maintenance_request()

    def on_cancel(self):
        self._cancel_stock_entries()
        self._revert_maintenance_request()

    def _validate_technician_not_supervisor(self):
        if not self.assigned_technician or not self.supervisor:
            return

        emp = frappe.db.get_value(
            "Maintenance Technician",
            self.assigned_technician,
            "employee"
        )

        if emp and emp == self.supervisor:
            frappe.throw(
                "The assigned technician's linked employee cannot also be the supervisor.",
                title="Invalid Assignment"
            )

    def _validate_dates(self):
        if self.start_time and self.end_time:
            if get_datetime(self.end_time) <= get_datetime(self.start_time):
                frappe.throw("End Time must be after Start Time.")

    def _run_submit_validations(self):
        errors = []

        if not self.start_time:
            errors.append("• Start Time is required.")

        if not self.end_time:
            errors.append("• End Time is required.")

        if self.start_time and self.end_time:
            if get_datetime(self.end_time) <= get_datetime(self.start_time):
                errors.append("• End Time must be after Start Time.")

        if not (self.work_performed or "").strip():
            errors.append("• Work Performed is required.")

        # if self.inspection_required and not self.supervisor_verified:
        #     errors.append("• Supervisor / Witness Verified must be checked.")

        if self.parts_used:
            errors.extend(self._validate_parts_stock())

        if self.parts_returned:
            errors.extend(self._validate_return_parts())

        if errors:
            frappe.throw(
                "Please fix the following before submitting:<br><br>"
                + "<br>".join(errors),
                title="Cannot Submit"
            )

    def _validate_parts_stock(self):
        errors = []

        for idx, part in enumerate(self.parts_used or [], 1):
            if not part.item_code:
                errors.append("• Parts Used Row {0}: Item Code is required.".format(idx))
                continue

            if not part.warehouse:
                errors.append(
                    "• Parts Used Row {0}: Warehouse is required for <b>{1}</b>.".format(
                        idx,
                        part.item_code
                    )
                )
                continue

            available = frappe.db.get_value(
                "Bin",
                {
                    "item_code": part.item_code,
                    "warehouse": part.warehouse
                },
                "actual_qty"
            ) or 0

            if available < (part.quantity or 0):
                errors.append(
                    "• Parts Used Row {0}: Insufficient stock for <b>{1}</b> in <b>{2}</b>. Available: {3}, Required: {4}.".format(
                        idx,
                        part.item_code,
                        part.warehouse,
                        available,
                        part.quantity
                    )
                )

        return errors

    def _validate_return_parts(self):
        errors = []

        for idx, part in enumerate(self.parts_returned or [], 1):
            if not part.item_code:
                errors.append("• Parts Returned Row {0}: Item Code is required.".format(idx))
                continue

            if not part.warehouse:
                errors.append(
                    "• Parts Returned Row {0}: Warehouse is required for <b>{1}</b>.".format(
                        idx,
                        part.item_code
                    )
                )

        return errors

    def _create_stock_entries(self):
        if self.parts_used:
            issue_entry = self._create_stock_entry(
                self.parts_used,
                "Material Issue"
            )

            if issue_entry:
                self.db_set("material_issue_stock_entry", issue_entry)

        if self.parts_returned:
            return_entry = self._create_stock_entry(
                self.parts_returned,
                "Material Receipt"
            )

            if return_entry:
                self.db_set("material_return_stock_entry", return_entry)

    def _create_stock_entry(self, parts, purpose):
        company = frappe.db.get_default("company")

        if not company:
            frappe.throw("Default Company is required to create Stock Entry.")

        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = purpose
        stock_entry.company = company
        stock_entry.remarks = (
            "Maintenance Task: {0} — Request: {1} — Location: {2}".format(
                self.name,
                self.maintenance_request or "N/A",
                self.location or "N/A"
            )
        )

        for part in parts:
            item_uom = (
                part.uom
                or frappe.db.get_value("Item", part.item_code, "stock_uom")
                or "Nos"
            )

            row = {
                "item_code": part.item_code,
                "item_name": part.item_name or "",
                "qty": part.quantity,
                "uom": item_uom
            }

            if purpose == "Material Issue":
                row["s_warehouse"] = part.warehouse
            else:
                row["t_warehouse"] = part.warehouse

            stock_entry.append("items", row)

        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()

        for part in parts:
            frappe.db.set_value(
                "Maintenance Parts Used",
                part.name,
                "stock_entry",
                stock_entry.name
            )

        frappe.msgprint(
            "Stock Entry <b>{0}</b> ({1}) created.".format(
                stock_entry.name,
                purpose
            ),
            indicator="green",
            title="Stock Entry Created"
        )

        return stock_entry.name

    def _complete_maintenance_request(self):
        if not self.maintenance_request:
            return

        mr = frappe.get_doc("Maintenance Request", self.maintenance_request)

        frappe.db.set_value(
            "Maintenance Request",
            self.maintenance_request,
            {
                "status": "Completed",
                "completion_date": now_datetime()
            }
        )

        if mr.location_type == "Room" and mr.room:
            frappe.db.set_value(
                "Hotel Room",
                mr.room,
                "maintenance_flag",
                0
            )

        frappe.db.commit()

        frappe.msgprint(
            "Maintenance Request <b>{0}</b> marked as Completed.".format(
                self.maintenance_request
            ),
            indicator="green",
            alert=True
        )

    def _cancel_stock_entries(self):
        stock_entries = set()

        if self.material_issue_stock_entry:
            stock_entries.add(self.material_issue_stock_entry)

        if self.material_return_stock_entry:
            stock_entries.add(self.material_return_stock_entry)

        for se_name in stock_entries:
            try:
                se = frappe.get_doc("Stock Entry", se_name)

                if se.docstatus == 1:
                    se.cancel()

                    frappe.msgprint(
                        "Stock Entry <b>{0}</b> cancelled.".format(se.name),
                        indicator="orange",
                        title="Stock Entry Cancelled"
                    )

            except Exception as e:
                frappe.log_error(
                    str(e),
                    "Maintenance Task Cancel Stock Entry"
                )

    def _revert_maintenance_request(self):
        if not self.maintenance_request:
            return

        try:
            mr = frappe.get_doc("Maintenance Request", self.maintenance_request)

            if mr.status not in ("Cancelled", "Rejected"):
                frappe.db.set_value(
                    "Maintenance Request",
                    self.maintenance_request,
                    {
                        "status": "Cancelled",
                        "task": None
                    }
                )

                if mr.location_type == "Room" and mr.room:
                    frappe.db.set_value(
                        "Hotel Room",
                        mr.room,
                        "maintenance_flag",
                        0
                    )

                frappe.db.commit()

                frappe.msgprint(
                    "Maintenance Request <b>{0}</b> has been cancelled.".format(
                        self.maintenance_request
                    ),
                    indicator="orange",
                    title="Request Cancelled"
                )

        except Exception as e:
            frappe.log_error(
                str(e),
                "Maintenance Task Cancel — Request Sync"
            )


@frappe.whitelist()
def approve_parts(task_name):
    allowed_roles = set(["System Manager", "Hotel Manager"])
    user_roles = set(frappe.get_roles(frappe.session.user))

    if not allowed_roles.intersection(user_roles):
        frappe.throw(
            "Only a Hotel Manager or System Manager can approve parts.",
            frappe.PermissionError
        )

    task = frappe.get_doc("Maintenance Task", task_name)

    if task.docstatus == 1:
        frappe.throw("Cannot approve parts on a submitted task.")

    if not task.parts_used and not task.parts_returned:
        frappe.throw("No parts found on this task to approve.")

    stock_errors = task._validate_parts_stock()

    if stock_errors:
        frappe.throw(
            "Cannot approve — stock issues found:<br><br>"
            + "<br>".join(stock_errors),
            title="Stock Validation Failed"
        )

    frappe.db.set_value(
        "Maintenance Task",
        task_name,
        {
            "parts_approval_status": "Approved",
            "parts_approved_by": frappe.session.user,
            "parts_approved_on": now_datetime()
        }
    )

    frappe.db.commit()

    return {
        "approved_by": frappe.db.get_value(
            "User",
            frappe.session.user,
            "full_name"
        ),
        "approved_on": str(now_datetime())
    }


@frappe.whitelist()
def request_part_approval(task_name):
    task = frappe.get_doc("Maintenance Task", task_name)

    if task.docstatus == 1:
        frappe.throw("Cannot request approval on a submitted task.")

    if not task.parts_used and not task.parts_returned:
        frappe.throw("Please add used or returned parts before requesting approval.")

    if task.parts_approval_status == "Approved":
        frappe.throw(
            "Parts are already approved. Modify parts first if re-approval is needed."
        )

    frappe.db.set_value(
        "Maintenance Task",
        task_name,
        {
            "parts_approval_status": "Pending Approval",
            "parts_approved_by": None,
            "parts_approved_on": None
        }
    )

    frappe.db.commit()

    return {"status": "Pending Approval"}