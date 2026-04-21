import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class MaintenanceTask(Document):

    # ------------------------------------------------------------------
    # LIFECYCLE HOOKS
    # ------------------------------------------------------------------

    def validate(self):
        self.validate_technician_not_supervisor()
        self.validate_location()
        self.validate_dates()
        self.validate_no_duplicate_open_task()
        self.sync_parts_approval_status()

    def before_submit(self):
        self._run_submit_validations()

    def on_submit(self):
        frappe.db.set_value("Maintenance Task", self.name, "status", "Done")
        self.status = "Done"
        self.update_maintenance_request_status()
        self.update_asset_status()
        self.create_stock_entry_for_parts()

    def on_cancel(self):
        self.revert_maintenance_request_if_needed()
        self.cancel_linked_stock_entry()

    # ------------------------------------------------------------------
    # VALIDATE
    # ------------------------------------------------------------------

    def validate_technician_not_supervisor(self):
        if (
            self.assigned_to
            and self.supervisor
            and self.assigned_to == self.supervisor
        ):
            frappe.throw(
                "The <b>Assigned Technician</b> and <b>Supervisor</b> "
                "cannot be the same person."
            )

    def validate_location(self):
        if not self.location:
            frappe.throw("Please enter a <b>Location</b> for this task.")

    def validate_dates(self):
        if self.start_time and self.end_time:
            if get_datetime(self.end_time) <= get_datetime(self.start_time):
                frappe.throw("<b>End Time</b> must be after <b>Start Time</b>.")

    def validate_no_duplicate_open_task(self):
        if not self.asset:
            return

        existing = frappe.db.get_value(
            "Maintenance Task",
            filters={
                "asset": self.asset,
                "status": ["in", ["Open", "In Progress", "Hold"]],
                "name": ["!=", self.name],
                "docstatus": ["!=", 2],
            },
            fieldname="name",
        )

        if existing:
            asset_label = (
                frappe.db.get_value("Asset", self.asset, "asset_name") or self.asset
            )
            frappe.throw(
                f"Cannot create a new task for asset <b>{asset_label}</b>. "
                f"Task <b>{existing}</b> is still open. "
                f"Please complete or cancel it first.",
                title="Duplicate Open Task",
            )

    def sync_parts_approval_status(self):
        """
        Auto-manage parts_approval_status:
        - No parts → clear the status
        - Parts added/changed → set to 'Pending Approval' if not already 'Approved'
          UNLESS the approval is still valid (no changes since it was approved)
        """
        if not self.parts_used:
            self.parts_approval_status = ""
            self.parts_approved_by = None
            self.parts_approved_on = None
            return

        # If already approved, check whether parts have changed since approval
        if self.parts_approval_status == "Approved":
            if self._parts_changed_since_approval():
                self.parts_approval_status = "Pending Approval"
                self.parts_approved_by = None
                self.parts_approved_on = None
                frappe.msgprint(
                    "Parts have been modified. Approval has been reset — "
                    "please request re-approval before submitting.",
                    indicator="orange",
                    title="Parts Re-Approval Required"
                )
        elif self.parts_approval_status != "Pending Approval":
            # First time parts are added
            self.parts_approval_status = "Pending Approval"

    def _parts_changed_since_approval(self):
        """
        Compare current parts_used rows against the last saved version in DB.
        Returns True if any change is detected.
        """
        if not self.name or self.is_new():
            return False

        try:
            saved = frappe.get_doc("Maintenance Task", self.name)
            saved_parts = {
                (p.item_code, str(p.quantity), p.warehouse or "", p.store_impact or "")
                for p in (saved.parts_used or [])
            }
            current_parts = {
                (p.item_code, str(p.quantity), p.warehouse or "", p.store_impact or "")
                for p in (self.parts_used or [])
            }
            return saved_parts != current_parts
        except Exception:
            return True

    # ------------------------------------------------------------------
    # BEFORE SUBMIT
    # ------------------------------------------------------------------

    def _run_submit_validations(self):
        errors = []

        if not self.start_time:
            errors.append("• <b>Start Time</b> is required.")

        if not self.end_time:
            errors.append("• <b>End Time</b> is required.")

        if self.start_time and self.end_time:
            if get_datetime(self.end_time) <= get_datetime(self.start_time):
                errors.append("• <b>End Time</b> must be after <b>Start Time</b>.")

        if not (self.work_performed or "").strip():
            errors.append("• <b>Work Performed</b> is required.")

        if not (self.final_asset_status or "").strip():
            errors.append("• <b>Final Asset Status</b> is required.")

        if self.inspection_required and not self.supervisor_verified:
            errors.append(
                "• <b>Supervisor Verified</b> must be checked "
                "(Inspection Required is enabled)."
            )

        # ── PARTS APPROVAL VALIDATION ──────────────────────────────────
        if self.parts_used:
            if self.parts_approval_status != "Approved":
                errors.append(
                    "• <b>Parts approval is required</b>. Parts have been added but "
                    "not yet approved by an Admin or Hotel Manager. "
                    "Use the 'Request Part Approval' button and await approval."
                )

            # Validate stock availability for each part
            warehouse_errors = self._validate_parts_stock()
            errors.extend(warehouse_errors)

        if errors:
            frappe.throw(
                "Please fix the following before submitting:<br><br>"
                + "<br>".join(errors),
                title="Cannot Submit",
            )

    def _validate_parts_stock(self):
        """
        Validate that all parts with store_impact = 'Reduce Stock'
        have sufficient stock in the specified warehouse.
        """
        errors = []
        warehouse = frappe.db.get_single_value("Hotel Settings", "consumable_warehouse")

        for idx, part in enumerate(self.parts_used, 1):
            if part.store_impact != "Reduce Stock":
                continue

            item_warehouse = part.warehouse or warehouse
            if not item_warehouse:
                errors.append(
                    f"• Row {idx}: No warehouse configured for <b>{part.item_code}</b>. "
                    "Set a warehouse on the part or configure Hotel Settings."
                )
                continue

            available = frappe.db.get_value(
                "Bin",
                {"item_code": part.item_code, "warehouse": item_warehouse},
                "actual_qty",
            ) or 0

            if available < (part.quantity or 0):
                errors.append(
                    f"• Row {idx}: Insufficient stock for <b>{part.item_code}</b> "
                    f"in <b>{item_warehouse}</b>. "
                    f"Available: {available}, Required: {part.quantity}."
                )

        return errors

    # ------------------------------------------------------------------
    # ON SUBMIT — side effects
    # ------------------------------------------------------------------

    def create_stock_entry_for_parts(self):
        """
        Create a Material Issue Stock Entry for all parts with
        store_impact = 'Reduce Stock'. Mirrors the housekeeping task pattern.
        """
        if not self.parts_used:
            return

        items_to_issue = [
            p for p in self.parts_used
            if p.store_impact == "Reduce Stock" and p.item_code
        ]

        if not items_to_issue:
            return

        default_warehouse = frappe.db.get_single_value("Hotel Settings", "consumable_warehouse")

        try:
            stock_entry_type = frappe.db.get_value(
                "Stock Entry Type",
                {"purpose": "Material Issue"},
                "name",
            )
            if not stock_entry_type:
                frappe.throw(
                    "Stock Entry Type 'Material Issue' does not exist. "
                    "Please create it first."
                )

            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = stock_entry_type
            stock_entry.company = frappe.db.get_default("company")
            stock_entry.from_warehouse = default_warehouse
            stock_entry.remarks = (
                f"Maintenance Task: {self.name} — Asset: {self.asset} — Location: {self.location}"
            )

            for part in items_to_issue:
                item_warehouse = part.warehouse or default_warehouse
                item_uom = frappe.db.get_value("Item", part.item_code, "stock_uom") or "Nos"
                stock_entry.append("items", {
                    "item_code": part.item_code,
                    "qty": part.quantity,
                    "s_warehouse": item_warehouse,
                    "uom": item_uom,
                })

            stock_entry.insert(ignore_permissions=True)
            stock_entry.submit()

            frappe.db.set_value("Maintenance Task", self.name, "stock_entry", stock_entry.name)

            frappe.msgprint(
                f"✓ Stock Entry <b>{stock_entry.name}</b> created for "
                f"{len(items_to_issue)} part(s).",
                indicator="green",
                title="Stock Entry Created",
            )

        except frappe.ValidationError as ve:
            frappe.log_error(frappe.get_traceback(), "Maintenance Task Stock Entry Error")
            frappe.msgprint(
                f"Stock Entry validation error: {str(ve)}. Please create manually.",
                indicator="yellow",
                title="Stock Entry Error",
            )
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Maintenance Task Stock Entry Error")
            frappe.msgprint(
                f"Stock Entry error: {str(e)}. Please create manually.",
                indicator="yellow",
                title="Stock Entry Error",
            )

    def update_maintenance_request_status(self):
        if not self.maintenance_request:
            return

        pending_tasks = frappe.db.count(
            "Maintenance Task",
            filters={
                "maintenance_request": self.maintenance_request,
                "status": ["in", ["Open", "In Progress", "Hold"]],
                "name": ["!=", self.name],
                "docstatus": ["!=", 2],
            },
        )

        if pending_tasks == 0:
            frappe.db.set_value(
                "Maintenance Request",
                self.maintenance_request,
                {
                    "status": "Completed",
                    "completion_date": now_datetime(),
                },
            )
            frappe.db.commit()
            frappe.msgprint(
                f"Maintenance Request <b>{self.maintenance_request}</b> "
                "marked as <b>Completed</b>.",
                indicator="green",
                alert=True,
            )

    def update_asset_status(self):
        if not (self.asset and self.final_asset_status):
            return

        status_map = {
            "Operational":    "In Location",
            "Out of Service": "Out of Order",
            "Under Repair":   "In Maintenance",
            "Decommissioned": "Scrapped",
        }

        asset_status = status_map.get(self.final_asset_status)
        if asset_status:
            try:
                frappe.db.set_value("Asset", self.asset, "status", asset_status)
                frappe.db.commit()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # ON CANCEL
    # ------------------------------------------------------------------

    def revert_maintenance_request_if_needed(self):
        if not self.maintenance_request:
            return

        mr_status = frappe.db.get_value(
            "Maintenance Request",
            self.maintenance_request,
            "status",
        )

        if mr_status == "Completed":
            frappe.db.set_value(
                "Maintenance Request",
                self.maintenance_request,
                "status",
                "Pending",
            )
            frappe.db.commit()

    def cancel_linked_stock_entry(self):
        """Cancel the linked stock entry if it exists."""
        if not self.stock_entry:
            return

        try:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()
                frappe.msgprint(
                    f"Stock Entry <b>{self.stock_entry}</b> has been cancelled.",
                    indicator="orange",
                    title="Stock Entry Cancelled",
                )
        except Exception as e:
            frappe.log_error(
                f"Failed to cancel stock entry {self.stock_entry}: {str(e)}",
                "Maintenance Task Cancel",
            )


# ------------------------------------------------------------------
# WHITELISTED METHODS
# ------------------------------------------------------------------

@frappe.whitelist()
def approve_parts(task_name):
    """
    Called when Admin / Hotel Manager clicks 'Approve Parts'.
    Sets parts_approval_status = 'Approved' and stamps approver details.
    Only System Manager and Hotel Manager roles are permitted.
    """
    allowed_roles = {"System Manager", "Hotel Manager"}
    user_roles = set(frappe.get_roles(frappe.session.user))

    if not (allowed_roles & user_roles):
        frappe.throw(
            "Only <b>System Manager</b> or <b>Hotel Manager</b> can approve parts.",
            frappe.PermissionError,
        )

    task = frappe.get_doc("Maintenance Task", task_name)

    if task.docstatus == 1:
        frappe.throw("Cannot approve parts on a submitted task.")

    if not task.parts_used:
        frappe.throw("No parts found on this task to approve.")

    # Validate stock availability before approving
    warehouse_errors = task._validate_parts_stock()
    if warehouse_errors:
        frappe.throw(
            "Cannot approve — stock issues found:<br><br>"
            + "<br>".join(warehouse_errors),
            title="Stock Validation Failed",
        )

    frappe.db.set_value("Maintenance Task", task_name, {
        "parts_approval_status": "Approved",
        "parts_approved_by":     frappe.session.user,
        "parts_approved_on":     now_datetime(),
    })
    frappe.db.commit()

    return {
        "approved_by": frappe.db.get_value("User", frappe.session.user, "full_name"),
        "approved_on": str(now_datetime()),
    }


@frappe.whitelist()
def request_part_approval(task_name):
    """
    Called when technician clicks 'Request Part Approval'.
    Sets status to 'Pending Approval' (idempotent) and notifies managers.
    """
    task = frappe.get_doc("Maintenance Task", task_name)

    if task.docstatus == 1:
        frappe.throw("Cannot request approval on a submitted task.")

    if not task.parts_used:
        frappe.throw("Please add parts before requesting approval.")

    if task.parts_approval_status == "Approved":
        frappe.throw("Parts are already approved. Modify parts first if re-approval is needed.")

    frappe.db.set_value("Maintenance Task", task_name, {
        "parts_approval_status": "Pending Approval",
        "parts_approved_by":     None,
        "parts_approved_on":     None,
    })
    frappe.db.commit()

    # Optional: notify managers via Frappe notification
    _notify_managers_for_parts_approval(task_name)

    return {"status": "Pending Approval"}


def _notify_managers_for_parts_approval(task_name):
    """Send in-app notification to Hotel Managers and System Managers."""
    try:
        managers = frappe.db.get_all(
            "Has Role",
            filters={"role": ["in", ["Hotel Manager", "System Manager"]], "parenttype": "User"},
            fields=["parent"],
            distinct=True,
        )

        task_url = f"/rhohotel/maintenance/task/{task_name}"
        for mgr in managers:
            frappe.publish_realtime(
                "eval_js",
                f'frappe.show_alert({{message: "Parts approval requested for task {task_name}", indicator: "blue"}}, 8)',
                user=mgr.parent,
            )
    except Exception:
        pass  # Notifications are best-effort


# ------------------------------------------------------------------
# AUTO-CREATE from Maintenance Request
# ------------------------------------------------------------------

def auto_create_task_from_request(mr):
    if mr.request_type != "Maintenance" or not mr.approved:
        return

    existing = frappe.db.exists(
        "Maintenance Task",
        {
            "maintenance_request": mr.name,
            "docstatus": ["!=", 2],
        },
    )
    if existing:
        return

    task = frappe.get_doc({
        "doctype":             "Maintenance Task",
        "maintenance_request": mr.name,
        "task_type":           "Corrective",
        "priority":            mr.priority,
        "status":              "Open",
        "location":            mr.room or "See Maintenance Request",
        "asset":               mr.asset,
        "task_description":    mr.issue_description,
    })
    task.flags.ignore_permissions = True
    task.insert()
    frappe.db.commit()

    frappe.msgprint(
        f"Maintenance Task <b>{task.name}</b> auto-created from this request.",
        indicator="green",
        alert=True,
    )