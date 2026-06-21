# import frappe
# import json
# from frappe.utils import nowdate, add_days, get_first_day_of_week

# MANAGER_ROLES = ("Maintenance Manager", "System Manager", "Hotel Manager")


# def _is_maintenance_manager():
#     if frappe.session.user == "Administrator":
#         return True
#     roles = set(frappe.get_roles(frappe.session.user))
#     return bool(roles.intersection(MANAGER_ROLES))


# def _get_logged_in_employee_name():
#     """Returns the Employee record name linked to the current session user,
#     or None if there isn't one (e.g. Administrator with no Employee record).
#     """
#     return frappe.db.get_value(
#         "Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
#     )


# def _get_logged_in_technician_name(employee_name=None):
#     """Returns the Maintenance Technician record name linked (via its
#     `employee` field) to the current session user, or None if the user
#     has no Employee record or no Maintenance Technician record at all.
#     """
#     employee_name = employee_name if employee_name is not None else _get_logged_in_employee_name()
#     if not employee_name:
#         return None
#     return frappe.db.get_value(
#         "Maintenance Technician", {"employee": employee_name}, "name"
#     )


# def _can_view_task(task, employee_name=None, technician_name=None):
#     """A user can view a Maintenance Task's detail if they are:
#     - A Maintenance Manager, System Manager, or Hotel Manager (sees everything)
#     - The assigned technician on the task
#     - The supervisor/witness on the task
#     - The employee who originally reported/created the request (reported_by)
#     Anyone else gets a PermissionError regardless of role.
#     """
#     if _is_maintenance_manager():
#         return True

#     if employee_name is None:
#         employee_name = _get_logged_in_employee_name()
#     if technician_name is None:
#         technician_name = _get_logged_in_technician_name(employee_name)

#     if technician_name and task.assigned_technician == technician_name:
#         return True

#     if employee_name and task.supervisor == employee_name:
#         return True

#     if employee_name and task.reported_by == employee_name:
#         return True

#     return False


# def _can_edit_task(task, employee_name=None, technician_name=None):
#     """Editing the task form (filling work performed, times, parts, checklist)
#     is restricted to the assigned technician and manager roles only.
#     Supervisors, reporters, and other viewers can open the task but cannot
#     write to it -- their role is approval, not task execution.
#     """
#     if _is_maintenance_manager():
#         return True

#     if employee_name is None:
#         employee_name = _get_logged_in_employee_name()
#     if technician_name is None:
#         technician_name = _get_logged_in_technician_name(employee_name)

#     if technician_name and task.assigned_technician == technician_name:
#         return True

#     return False


# @frappe.whitelist()
# def get_maintenance_dashboard():
#     today = nowdate()
#     week_start = get_first_day_of_week(today)

#     status_counts = {}
#     for status in ["Open", "In Progress", "Done", "Hold", "Cancelled"]:
#         status_counts[status] = frappe.db.count(
#             "Maintenance Task", {"status": status}
#         )

#     done_today = frappe.db.count(
#         "Maintenance Task",
#         {"status": "Done", "end_time": ["like", f"{today}%"]}
#     )

#     done_this_week = frappe.db.sql("""
#         SELECT COUNT(name) as cnt
#         FROM `tabMaintenance Task`
#         WHERE status = 'Done'
#         AND DATE(end_time) >= %s
#         AND DATE(end_time) <= %s
#     """, (week_start, today), as_dict=1)[0].cnt or 0

#     scheduled_today = frappe.db.count(
#         "Maintenance Task",
#         {
#             "status": ["in", ["Open", "In Progress"]],
#             "start_time": ["like", f"{today}%"]
#         }
#     )

#     urgent_open = frappe.db.count(
#         "Maintenance Task",
#         {"priority": "High", "status": ["not in", ["Done", "Cancelled"]]}
#     )

#     return {
#         "open": status_counts.get("Open", 0),
#         "in_progress": status_counts.get("In Progress", 0),
#         "on_hold": status_counts.get("Hold", 0),
#         "done": status_counts.get("Done", 0),
#         "cancelled": status_counts.get("Cancelled", 0),
#         "done_today": done_today,
#         "done_this_week": done_this_week,
#         "scheduled_today": scheduled_today,
#         "urgent_open": urgent_open,
#     }


# @frappe.whitelist()
# def get_maintenance_list(
#     search=None,
#     filter_type=None,
#     filter_priority=None,
#     filter_status=None,
#     filter_technician=None,
#     page=1,
#     page_size=25
# ):
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except (TypeError, ValueError):
#         page, page_size = 1, 25

#     filters = {}
#     if filter_type:
#         filters["task_type"] = filter_type
#     if filter_priority:
#         filters["priority"] = filter_priority
#     if filter_status:
#         filters["status"] = filter_status
#     if filter_technician:
#         filters["assigned_technician"] = filter_technician

#     task_fields = [
#         "name", "task_type", "status", "priority",
#         "location", "task_description",
#         "assigned_technician", "start_time", "end_time",
#         "maintenance_request", "workflow_state"
#     ]

#     if search:
#         tasks = frappe.db.sql("""
#             SELECT
#                 name, task_type, status, priority,
#                 location, task_description,
#                 assigned_technician, start_time, end_time,
#                 maintenance_request, workflow_state
#             FROM `tabMaintenance Task`
#             WHERE (
#                 name LIKE %(q)s
#                 OR location LIKE %(q)s
#                 OR task_description LIKE %(q)s
#             )
#             {filter_clause}
#             ORDER BY modified DESC
#             LIMIT %(limit)s OFFSET %(offset)s
#         """.format(
#             filter_clause=_build_filter_clause(filters)
#         ), {
#             "q": f"%{search}%",
#             "limit": page_size,
#             "offset": (page - 1) * page_size
#         }, as_dict=1)

#         total = frappe.db.sql("""
#             SELECT COUNT(name) as cnt FROM `tabMaintenance Task`
#             WHERE (name LIKE %(q)s OR location LIKE %(q)s OR task_description LIKE %(q)s)
#             {filter_clause}
#         """.format(filter_clause=_build_filter_clause(filters)),
#             {"q": f"%{search}%"}, as_dict=1)[0].cnt or 0
#     else:
#         tasks = frappe.get_all(
#             "Maintenance Task",
#             filters=filters,
#             fields=task_fields,
#             order_by="modified desc",
#             limit_page_length=page_size,
#             limit_start=(page - 1) * page_size
#         )
#         total = frappe.db.count("Maintenance Task", filters)

#     tech_cache = {}
#     for task in tasks:
#         tech_id = task.get("assigned_technician")
#         if tech_id:
#             if tech_id not in tech_cache:
#                 tech_cache[tech_id] = frappe.db.get_value(
#                     "Maintenance Technician", tech_id, "technician_name"
#                 ) or tech_id
#             task["technician_name"] = tech_cache[tech_id]
#         else:
#             task["technician_name"] = "Unassigned"

#     return {
#         "tasks": tasks,
#         "total": total,
#         "page": page,
#         "page_size": page_size,
#         "total_pages": max(1, -(-total // page_size)),
#     }


# @frappe.whitelist()
# def get_maintenance_technicians_filter():
#     return frappe.get_all(
#         "Maintenance Technician",
#         filters={"visible_for_assignment": 1},
#         fields=["name", "technician_name"],
#         order_by="technician_name asc",
#         limit_page_length=200
#     )


# def _build_filter_clause(filters):
#     clauses = []
#     for field, value in filters.items():
#         safe_field = field.replace("`", "")
#         safe_value = value.replace("'", "''")
#         clauses.append(f"AND `{safe_field}` = '{safe_value}'")
#     return " ".join(clauses)


# # ── Task detail ────────────────────────────────────────────────────────────────

# @frappe.whitelist()
# def get_maintenance_task(task_name):
#     if not frappe.db.exists("Maintenance Task", task_name):
#         frappe.throw(f"Maintenance Task '{task_name}' not found", frappe.DoesNotExistError)

#     task = frappe.get_doc("Maintenance Task", task_name)

#     if not _can_view_task(task):
#         frappe.throw(
#             "You can only view tasks assigned to you or where you are the supervisor/witness.",
#             frappe.PermissionError,
#         )

#     # Resolve technician name
#     technician_name = None
#     if task.assigned_technician:
#         technician_name = frappe.db.get_value(
#             "Maintenance Technician", task.assigned_technician, "technician_name"
#         )

#     # Resolve supervisor name
#     supervisor_name = None
#     if task.supervisor:
#         supervisor_name = frappe.db.get_value("Employee", task.supervisor, "employee_name")

#     # Resolve reported_by name
#     reported_by_name = None
#     if task.reported_by:
#         reported_by_name = frappe.db.get_value("Employee", task.reported_by, "employee_name")

#     # Resolve requesting_department — fall back to linked request if null on task
#     requesting_dept = task.requesting_department
#     if not requesting_dept and task.maintenance_request:
#         requesting_dept = frappe.db.get_value(
#             "Maintenance Request", task.maintenance_request, "requesting_department"
#         )
#     # If still empty, try resolving from reported_by employee
#     if not requesting_dept and task.reported_by:
#         requesting_dept = frappe.db.get_value("Employee", task.reported_by, "department")

#     requesting_dept_name = requesting_dept or None

#     # Resolve witness_department — fall back to linked request if null on task
#     witness_dept = task.witness_department
#     if not witness_dept and task.maintenance_request:
#         witness_dept = frappe.db.get_value(
#             "Maintenance Request", task.maintenance_request, "witness_department"
#         )
#     # If still empty, try resolving from supervisor employee
#     if not witness_dept and task.supervisor:
#         witness_dept = frappe.db.get_value("Employee", task.supervisor, "department")

#     witness_dept_name = witness_dept or None

#     # Resolve asset name
#     asset_name = None
#     if task.asset:
#         asset_name = frappe.db.get_value("Asset", task.asset, "asset_name") or task.asset

#     # Resolve request title
#     request_title = None
#     if task.maintenance_request:
#         request_title = frappe.db.get_value(
#             "Maintenance Request", task.maintenance_request, "issue_description"
#         ) or task.maintenance_request

#     # Parts used child table
#     parts_used = []
#     for p in task.parts_used or []:
#         parts_used.append({
#             "name": p.name,
#             "item_code": p.item_code,
#             "item_name": p.item_name or "",
#             "qty": p.quantity,
#             "uom": p.uom or "",
#             "warehouse": p.warehouse or "",
#             "available_qty": p.available_qty or 0,
#             "stock_entry": p.stock_entry or "",
#         })

#     # Parts returned child table
#     parts_returned = []
#     for p in task.parts_returned or []:
#         parts_returned.append({
#             "name": p.name,
#             "item_code": p.item_code,
#             "item_name": p.item_name or "",
#             "qty": p.quantity,
#             "uom": p.uom or "",
#             "warehouse": p.warehouse or "",
#             "available_qty": p.available_qty or 0,
#             "stock_entry": p.stock_entry or "",
#         })

#     return {
#         "name": task.name,
#         "docstatus": task.docstatus,
#         "workflow_state": task.workflow_state or "",

#         # Task details
#         "task_type": task.task_type,
#         "priority": task.priority,
#         "status": task.status,
#         "maintenance_request": task.maintenance_request,
#         "request_title": request_title,

#         # Location (read-only, copied from request)
#         "location": task.location,
#         "request_location_type": task.request_location_type or "",

#         # Assignment (read-only, copied from request)
#         "assigned_technician": task.assigned_technician,
#         "technician_name": technician_name,
#         "supervisor": task.supervisor,
#         "supervisor_name": supervisor_name,

#         # Reporter info (read-only, copied from request)
#         "reported_by": task.reported_by,
#         "reported_by_name": reported_by_name,
#         "requesting_department": requesting_dept or task.requesting_department or "",
#         "requesting_department_name": requesting_dept_name,
#         "witness_department": witness_dept or task.witness_department or "",
#         "witness_department_name": witness_dept_name,
#         "issue_type": task.issue_type or "",

#         # Timing
#         "start_time": str(task.start_time) if task.start_time else None,
#         "end_time": str(task.end_time) if task.end_time else None,

#         # Description
#         "task_description": task.task_description or "",
#         "work_performed": task.work_performed or "",
#         "completion_notes": task.completion_notes or "",

#         # Checklist
#         "inspection_required": task.inspection_required,
#         "fault_diagnosed": task.fault_diagnosed,
#         "test_run_passed": task.test_run_passed,

#         # Parts / materials
#         "parts_used": parts_used,
#         "parts_returned": parts_returned,
#         "parts_approval_status": task.parts_approval_status or "Not Requested",
#         "parts_approved_by": task.parts_approved_by or "",
#         "parts_approved_on": str(task.parts_approved_on) if task.parts_approved_on else None,
#         "material_issue_stock_entry": task.material_issue_stock_entry or "",
#         "material_return_stock_entry": task.material_return_stock_entry or "",
#         "asset": task.asset or "",
#         "asset_name": asset_name or "",

#         # Whether the current user is allowed to fill/edit the task form.
#         # True only for the assigned technician and manager roles
#         # (Maintenance Manager, System Manager, Hotel Manager).
#         # Supervisors, reporters, and other viewers can see the task
#         # but not write to it.
#         "can_edit": _can_edit_task(task),
#     }


# @frappe.whitelist()
# def save_maintenance_task(task_name, task_data, parts_used=None, parts_returned=None):
#     if isinstance(task_data, str):
#         task_data = json.loads(task_data)
#     if isinstance(parts_used, str):
#         parts_used = json.loads(parts_used)
#     if isinstance(parts_returned, str):
#         parts_returned = json.loads(parts_returned)

#     try:
#         task = frappe.get_doc("Maintenance Task", task_name)

#         if task.docstatus == 1:
#             return {"success": False, "error": "Cannot edit a submitted task"}

#         # Only editable fields — read-only fields (copied from request) are excluded
#         field_map = [
#             "task_type", "work_performed", "completion_notes",
#             "inspection_required", "fault_diagnosed", "test_run_passed"
#         ]
#         for field in field_map:
#             if field in task_data:
#                 setattr(task, field, task_data[field])

#         if task_data.get("start_time"):
#             task.start_time = task_data["start_time"]
#         if task_data.get("end_time"):
#             task.end_time = task_data["end_time"]

#         # Parts used
#         if parts_used is not None:
#             task.set("parts_used", [])
#             for p in parts_used:
#                 if p.get("item_code"):
#                     task.append("parts_used", {
#                         "item_code": p["item_code"],
#                         "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
#                         "quantity": p.get("qty") or p.get("quantity") or 1,
#                         "uom": p.get("uom") or "",
#                         "warehouse": p.get("warehouse") or "",
#                         "cost": p.get("cost") or 0,
#                     })

#         # Parts returned
#         if parts_returned is not None:
#             task.set("parts_returned", [])
#             for p in parts_returned:
#                 if p.get("item_code"):
#                     task.append("parts_returned", {
#                         "item_code": p["item_code"],
#                         "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
#                         "quantity": p.get("qty") or p.get("quantity") or 1,
#                         "uom": p.get("uom") or "",
#                         "warehouse": p.get("warehouse") or "",
#                         "cost": p.get("cost") or 0,
#                     })

#         task.save()
#         frappe.db.commit()
#         return {"success": True}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "save_maintenance_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


# @frappe.whitelist()
# def submit_maintenance_task(task_name):
#     try:
#         task = frappe.get_doc("Maintenance Task", task_name)
#         if task.docstatus == 1:
#             return {"success": False, "error": "Task is already submitted"}
#         task.submit()
#         frappe.db.commit()
#         return {"success": True}
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "submit_maintenance_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


# @frappe.whitelist()
# def cancel_maintenance_task(task_name):
#     try:
#         task = frappe.get_doc("Maintenance Task", task_name)
#         task.cancel()
#         frappe.db.commit()
#         return {"success": True}
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "cancel_maintenance_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


# @frappe.whitelist()
# def get_technicians_for_task():
#     return frappe.get_all(
#         "Maintenance Technician",
#         filters={"visible_for_assignment": 1, "availability": ["!=", "Unavailable"]},
#         fields=["name", "technician_name", "availability", "primary_specialization"],
#         order_by="technician_name asc",
#         limit_page_length=200
#     )


# @frappe.whitelist()
# def get_supervisors_for_task():
#     return frappe.get_all(
#         "Employee",
#         filters={"status": "Active"},
#         fields=["name", "employee_name", "designation"],
#         order_by="employee_name asc",
#         limit_page_length=200
#     )


# @frappe.whitelist()
# def get_items_for_parts():
#     items = frappe.get_all(
#         "Item",
#         filters={"disabled": 0, "is_stock_item": 1},
#         fields=["name", "item_name", "stock_uom"],
#         order_by="item_name asc",
#         limit_page_length=500
#     )

#     for item in items:
#         item["available_qty"] = frappe.db.sql("""
#             SELECT COALESCE(SUM(actual_qty), 0)
#             FROM `tabBin`
#             WHERE item_code = %s
#         """, item.name)[0][0] or 0

#     return items


# @frappe.whitelist()
# def get_warehouses_for_parts(company=None):
#     if not company:
#         company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")

#     filters = {
#         "is_group": 0,
#         "disabled": 0
#     }

#     if company:
#         filters["company"] = company

#     return frappe.get_all(
#         "Warehouse",
#         filters=filters,
#         fields=["name", "warehouse_name", "company"],
#         order_by="warehouse_name asc",
#         limit_page_length=200
#     )


# @frappe.whitelist()
# def create_maintenance_task(task_data, parts_used=None):
#     if isinstance(task_data, str):
#         task_data = json.loads(task_data)
#     if isinstance(parts_used, str):
#         parts_used = json.loads(parts_used)

#     try:
#         task = frappe.new_doc("Maintenance Task")
#         task.task_type = task_data.get("task_type", "Corrective")
#         task.priority = task_data.get("priority", "Medium")
#         task.status = task_data.get("status", "Open")
#         task.location = task_data.get("location") or ""
#         task.task_description = task_data.get("task_description") or ""
#         task.assigned_technician = task_data.get("assigned_technician") or None
#         task.supervisor = task_data.get("supervisor") or None
#         task.maintenance_request = task_data.get("maintenance_request") or None
#         task.inspection_required = 1 if task_data.get("inspection_required") else 0
#         task.fault_diagnosed = 1 if task_data.get("fault_diagnosed") else 0
#         task.test_run_passed = 1 if task_data.get("test_run_passed") else 0
#         task.completion_notes = task_data.get("completion_notes") or ""

#         if task_data.get("start_time"):
#             task.start_time = task_data["start_time"]
#         if task_data.get("end_time"):
#             task.end_time = task_data["end_time"]

#         if parts_used:
#             for p in parts_used:
#                 if p.get("item_code"):
#                     task.append("parts_used", {
#                         "item_code": p["item_code"],
#                         "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
#                         "quantity": p.get("qty") or p.get("quantity") or 1,
#                         "uom": p.get("uom") or "",
#                         "warehouse": p.get("warehouse") or "",
#                         "cost": p.get("cost") or 0,
#                     })

#         task.insert()
#         frappe.db.commit()
#         return {"success": True, "task_name": task.name}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "create_maintenance_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


# @frappe.whitelist()
# def get_maintenance_dashboard_summary():
#     today = nowdate()
#     week_start = get_first_day_of_week(today)

#     open_count      = frappe.db.count("Maintenance Task", {"status": "Open"})
#     in_progress     = frappe.db.count("Maintenance Task", {"status": "In Progress"})
#     done_count      = frappe.db.count("Maintenance Task", {"status": "Done"})
#     hold_count      = frappe.db.count("Maintenance Task", {"status": "Hold"})
#     cancelled_count = frappe.db.count("Maintenance Task", {"status": "Cancelled"})
#     urgent_open     = frappe.db.count("Maintenance Task", {"priority": "High", "status": ["not in", ["Done", "Cancelled"]]})

#     done_this_week = frappe.db.sql("""
#         SELECT COUNT(name) as cnt FROM `tabMaintenance Task`
#         WHERE status = 'Done'
#         AND DATE(end_time) >= %s AND DATE(end_time) <= %s
#     """, (week_start, today), as_dict=1)[0].cnt or 0

#     type_counts = frappe.db.sql("""
#         SELECT task_type, COUNT(name) as cnt
#         FROM `tabMaintenance Task`
#         WHERE task_type IS NOT NULL
#         GROUP BY task_type
#     """, as_dict=1)
#     total_typed = sum(r.cnt for r in type_counts) or 1
#     type_mix = {r.task_type: round((r.cnt / total_typed) * 100, 1) for r in type_counts}
#     corrective_pct = type_mix.get("Corrective", 0)

#     avg_res = frappe.db.sql("""
#         SELECT AVG(TIMESTAMPDIFF(HOUR, start_time, end_time)) as avg_hrs
#         FROM `tabMaintenance Task`
#         WHERE status = 'Done'
#         AND start_time IS NOT NULL AND end_time IS NOT NULL
#         AND DATE(end_time) >= %s
#     """, (week_start,), as_dict=1)
#     avg_resolution_hrs = round(avg_res[0].avg_hrs or 0, 1) if avg_res else 0

#     top_locations = frappe.db.sql("""
#         SELECT location, COUNT(name) as open_tasks
#         FROM `tabMaintenance Task`
#         WHERE status NOT IN ('Done','Cancelled')
#         AND location IS NOT NULL AND location != ''
#         GROUP BY location
#         ORDER BY open_tasks DESC
#         LIMIT 4
#     """, as_dict=1)

#     recent = frappe.get_all(
#         "Maintenance Task",
#         fields=["name", "task_type", "status", "priority",
#                 "assigned_technician", "location", "task_description", "modified",
#                 "workflow_state"],
#         order_by="modified desc",
#         limit_page_length=5
#     )

#     tech_cache = {}
#     for task in recent:
#         if task.get("assigned_technician"):
#             tid = task["assigned_technician"]
#             if tid not in tech_cache:
#                 tech_cache[tid] = frappe.db.get_value("Maintenance Technician", tid, "technician_name") or tid
#             task["technician_name"] = tech_cache[tid]
#         else:
#             task["technician_name"] = "Unassigned"

#     return {
#         "stats": {
#             "open": open_count,
#             "in_progress": in_progress,
#             "done": done_count,
#             "hold": hold_count,
#             "cancelled": cancelled_count,
#             "urgent_open": urgent_open,
#             "done_this_week": done_this_week,
#             "avg_resolution_hrs": avg_resolution_hrs,
#         },
#         "type_mix": type_mix,
#         "corrective_pct": corrective_pct,
#         "top_locations": top_locations,
#         "recent_activity": recent,
#     }





import frappe
import json
from frappe.utils import nowdate, add_days, get_first_day_of_week

MANAGER_ROLES = ("Maintenance Manager", "Facility Manager", "System Manager", "Hotel Manager")
STOCK_ROLES = ("Stock Manager", "Stock User")


def _is_maintenance_manager():
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles(frappe.session.user))
    return bool(roles.intersection(MANAGER_ROLES))


def _get_logged_in_employee_name():
    """Returns the Employee record name linked to the current session user,
    or None if there isn't one (e.g. Administrator with no Employee record).
    """
    return frappe.db.get_value(
        "Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
    )


def _get_logged_in_technician_name(employee_name=None):
    """Returns the Maintenance Technician record name linked (via its
    `employee` field) to the current session user, or None if the user
    has no Employee record or no Maintenance Technician record at all.
    """
    employee_name = employee_name if employee_name is not None else _get_logged_in_employee_name()
    if not employee_name:
        return None
    return frappe.db.get_value(
        "Maintenance Technician", {"employee": employee_name}, "name"
    )


def _can_view_task(task, employee_name=None, technician_name=None):
    """A user can view a Maintenance Task's detail if they are:
    - A Maintenance Manager, System Manager, or Hotel Manager (sees everything)
    - A Stock Manager / Stock User (for approving parts requests)
    - The assigned technician on the task
    - The supervisor/witness on the task
    - The employee who originally reported/created the request (reported_by)
    Anyone else gets a PermissionError regardless of role.
    """
    if _is_maintenance_manager():
        return True

    user_roles = set(frappe.get_roles(frappe.session.user))
    if user_roles.intersection(STOCK_ROLES):
        return True

    if employee_name is None:
        employee_name = _get_logged_in_employee_name()
    if technician_name is None:
        technician_name = _get_logged_in_technician_name(employee_name)

    if technician_name and task.assigned_technician == technician_name:
        return True

    if employee_name and task.supervisor == employee_name:
        return True

    if employee_name and task.reported_by == employee_name:
        return True

    return False


def _can_edit_task(task, employee_name=None, technician_name=None):
    """Editing the task form (filling work performed, times, parts, checklist)
    is restricted to the assigned technician and manager roles only.
    Supervisors, reporters, and other viewers can open the task but cannot
    write to it -- their role is approval, not task execution.
    """
    if _is_maintenance_manager():
        return True

    if employee_name is None:
        employee_name = _get_logged_in_employee_name()
    if technician_name is None:
        technician_name = _get_logged_in_technician_name(employee_name)

    if technician_name and task.assigned_technician == technician_name:
        return True

    return False


def _get_allowed_actions(task):
    """Return the list of workflow action names the current user may take on
    *task* right now, based on role and transition conditions.
    Used by get_maintenance_task so the frontend can hide unauthorised buttons.
    """
    try:
        from frappe.model.workflow import get_workflow
        workflow = get_workflow("Maintenance Task")
        current_state = task.get(workflow.workflow_state_field)
        user = frappe.session.user
        user_roles = set(frappe.get_roles(user))
        actions = []
        for t in workflow.transitions:
            if t.state != current_state:
                continue
            allowed_role = t.get("allowed") or ""
            if allowed_role and allowed_role != "All" and user != "Administrator":
                if allowed_role not in user_roles:
                    continue
            if not _is_maintenance_transition_allowed(t, task, user):
                continue
            actions.append(t.action)
        return actions
    except Exception:
        return []


@frappe.whitelist()
def get_maintenance_dashboard():
    today = nowdate()
    week_start = get_first_day_of_week(today)

    status_counts = {}
    for status in ["Open", "In Progress", "Done", "Hold", "Cancelled"]:
        status_counts[status] = frappe.db.count(
            "Maintenance Task", {"status": status}
        )

    done_today = frappe.db.count(
        "Maintenance Task",
        {"status": "Done", "end_time": ["like", f"{today}%"]}
    )

    done_this_week = frappe.db.sql("""
        SELECT COUNT(name) as cnt
        FROM `tabMaintenance Task`
        WHERE status = 'Done'
        AND DATE(end_time) >= %s
        AND DATE(end_time) <= %s
    """, (week_start, today), as_dict=1)[0].cnt or 0

    scheduled_today = frappe.db.count(
        "Maintenance Task",
        {
            "status": ["in", ["Open", "In Progress"]],
            "start_time": ["like", f"{today}%"]
        }
    )

    urgent_open = frappe.db.count(
        "Maintenance Task",
        {"priority": "High", "status": ["not in", ["Done", "Cancelled"]]}
    )

    return {
        "open": status_counts.get("Open", 0),
        "in_progress": status_counts.get("In Progress", 0),
        "on_hold": status_counts.get("Hold", 0),
        "done": status_counts.get("Done", 0),
        "cancelled": status_counts.get("Cancelled", 0),
        "done_today": done_today,
        "done_this_week": done_this_week,
        "scheduled_today": scheduled_today,
        "urgent_open": urgent_open,
    }


@frappe.whitelist()
def get_maintenance_list(
    search=None,
    filter_type=None,
    filter_priority=None,
    filter_status=None,
    filter_technician=None,
    page=1,
    page_size=25
):
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = {}
    if filter_type:
        filters["task_type"] = filter_type
    if filter_priority:
        filters["priority"] = filter_priority
    if filter_status:
        filters["status"] = filter_status
    if filter_technician:
        filters["assigned_technician"] = filter_technician

    task_fields = [
        "name", "task_type", "status", "priority",
        "location", "task_description",
        "assigned_technician", "start_time", "end_time",
        "maintenance_request", "workflow_state"
    ]

    if search:
        tasks = frappe.db.sql("""
            SELECT
                name, task_type, status, priority,
                location, task_description,
                assigned_technician, start_time, end_time,
                maintenance_request, workflow_state
            FROM `tabMaintenance Task`
            WHERE (
                name LIKE %(q)s
                OR location LIKE %(q)s
                OR task_description LIKE %(q)s
            )
            {filter_clause}
            ORDER BY modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """.format(
            filter_clause=_build_filter_clause(filters)
        ), {
            "q": f"%{search}%",
            "limit": page_size,
            "offset": (page - 1) * page_size
        }, as_dict=1)

        total = frappe.db.sql("""
            SELECT COUNT(name) as cnt FROM `tabMaintenance Task`
            WHERE (name LIKE %(q)s OR location LIKE %(q)s OR task_description LIKE %(q)s)
            {filter_clause}
        """.format(filter_clause=_build_filter_clause(filters)),
            {"q": f"%{search}%"}, as_dict=1)[0].cnt or 0
    else:
        tasks = frappe.get_all(
            "Maintenance Task",
            filters=filters,
            fields=task_fields,
            order_by="modified desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size
        )
        total = frappe.db.count("Maintenance Task", filters)

    tech_cache = {}
    for task in tasks:
        tech_id = task.get("assigned_technician")
        if tech_id:
            if tech_id not in tech_cache:
                tech_cache[tech_id] = frappe.db.get_value(
                    "Maintenance Technician", tech_id, "technician_name"
                ) or tech_id
            task["technician_name"] = tech_cache[tech_id]
        else:
            task["technician_name"] = "Unassigned"

    return {
        "tasks": tasks,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_maintenance_technicians_filter():
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1},
        fields=["name", "technician_name"],
        order_by="technician_name asc",
        limit_page_length=200
    )


def _build_filter_clause(filters):
    clauses = []
    for field, value in filters.items():
        safe_field = field.replace("`", "")
        safe_value = value.replace("'", "''")
        clauses.append(f"AND `{safe_field}` = '{safe_value}'")
    return " ".join(clauses)


# ── Workflow actions ─────────────────────────────────────────────────────────────

def _is_maintenance_transition_allowed(transition, task, user):
    """Evaluate a Maintenance Task workflow transition condition.

    Strategy:
    1. Try Frappe's native is_transition_condition_satisfied() first.
       This handles simple doc-field conditions like
       ``doc.parts_used and doc.start_time`` without issue.
    2. If that raises (because the condition uses ``bool()``, ``set()``, or
       ``frappe.get_roles()`` which are absent from safe_eval's restricted
       globals), fall back to plain-Python role/supervisor evaluation.

    Fallback patterns handled:

    Pattern A (set-intersection style):
        bool(set(frappe.get_roles(user)).intersection({'Role A', 'Role B'}))

    Pattern B (Has-Role query style):
        frappe.db.get_value('Has Role', {'parent': user, 'role': 'Role A'}, 'role')

    Both are handled by extracting role names from the condition string and
    checking them against the requesting user's actual roles.
    """
    import re

    if not transition.condition:
        return True

    # --- Step 1: try native safe_eval (works for simple doc-field conditions) ---
    try:
        from frappe.model.workflow import is_transition_condition_satisfied
        return is_transition_condition_satisfied(transition, task)
    except Exception:
        pass  # fall through to role-based evaluation for bool()/set()/get_roles() conditions

    cond = transition.condition

    # --- Step 2a: supervisor user match ---
    if "doc.supervisor" in cond and task.get("supervisor"):
        supervisor_user = frappe.db.get_value("Employee", task.get("supervisor"), "user_id")
        if supervisor_user and supervisor_user == user:
            return True

    # --- Step 2b: role-based match ---
    user_roles = set(frappe.get_roles(user))
    role_names = set()

    # Pattern A: intersection({...}) — extract from the set literal
    for set_content in re.findall(r"intersection\(\{([^}]+)\}\)", cond):
        role_names.update(re.findall(r"'([^']+)'", set_content))

    # Pattern B: 'role': 'RoleName' — extract from dict-style filter
    role_names.update(re.findall(r"'role':\s*'([^']+)'", cond))

    return bool(user_roles.intersection(role_names))


@frappe.whitelist()
def apply_maintenance_workflow(task_name, action):
    """Apply a workflow action on a Maintenance Task.

    Uses a role-based gate rather than Frappe's doctype-level permissions, so
    that roles with domain access (e.g. Stock Manager) can trigger transitions
    even though they don't hold a full doctype permission on Maintenance Task.

    All role / transition validation is done as the requesting user. The actual
    doc.save() runs as Administrator because Frappe's validate_workflow() calls
    get_transitions() on _doc_before_save (an internally-created copy), which
    re-runs doc.check_permission("read") -- domain roles like Stock Manager
    don't pass that check. Setting doc.flags.ignore_permissions only covers the
    outer doc instance, not the internal copy.

    NOTE: We intentionally bypass frappe's is_transition_condition_satisfied()
    here because it calls frappe.safe_eval() which raises
    ``NameError: name 'bool' is not defined`` for workflow conditions that use
    frappe.session.user comparisons on certain Frappe/Python versions.  The
    equivalent logic is implemented in _is_maintenance_transition_allowed().
    """
    MAINTENANCE_ROLES = {
        "Maintenance Manager", "Facility Manager", "System Manager",
        "Hotel Manager", "Stock Manager", "Stock User",
        "Maintenance Technician", "Employee",
    }
    requesting_user = frappe.session.user
    user_roles = set(frappe.get_roles(requesting_user))
    if requesting_user != "Administrator" and not user_roles.intersection(MAINTENANCE_ROLES):
        frappe.throw("Not permitted to perform workflow actions on Maintenance Tasks.", frappe.PermissionError)

    try:
        from frappe.model.workflow import get_workflow, has_approval_access

        # Validate with the real requesting user
        task = frappe.get_doc("Maintenance Task", task_name)
        workflow = get_workflow("Maintenance Task")
        current_state = task.get(workflow.workflow_state_field)

        # Use _is_maintenance_transition_allowed instead of is_transition_condition_satisfied
        # to avoid the safe_eval 'bool' NameError bug in Frappe.
        possible = [
            t for t in workflow.transitions
            if t.state == current_state and _is_maintenance_transition_allowed(t, task, requesting_user)
        ]
        transition = next((t for t in possible if t.action == action), None)
        if not transition:
            return {"success": False, "error": '"{}" is not a valid action from state "{}".'.format(action, current_state)}

        allowed_role = transition.get("allowed") or ""
        if allowed_role and allowed_role != "All" and requesting_user != "Administrator":
            if allowed_role not in user_roles:
                return {"success": False, "error": 'This action requires the "{}" role.'.format(allowed_role)}

        if not has_approval_access(requesting_user, task, transition):
            return {"success": False, "error": "Self approval is not allowed."}

        # Run the save as Administrator so Frappe's internal doctype-level
        # permission checks inside validate_workflow pass cleanly.
        frappe.set_user("Administrator")

        task = frappe.get_doc("Maintenance Task", task_name)
        task.set(workflow.workflow_state_field, transition.next_state)

        next_state_def = next((s for s in workflow.states if s.state == transition.next_state), None)
        if next_state_def and next_state_def.update_field:
            task.set(next_state_def.update_field, next_state_def.update_value)

        from frappe.model.document import DocStatus
        new_docstatus = DocStatus(int(next_state_def.doc_status or 0) if next_state_def else 0)

        # Override validate_workflow on this specific instance to bypass the
        # broken frappe.safe_eval call (NameError 'bool' is not defined).
        # We have already validated the transition above, so this is safe.
        # All other validations (mandatory, dates, custom validate/before_submit,
        # etc.) still run as normal.
        task.validate_workflow = lambda: None

        try:
            if new_docstatus.is_submitted():
                task.submit()
            else:
                task.save()
        finally:
            # Restore the class method on this instance
            try:
                del task.validate_workflow
            except AttributeError:
                pass

        # "Approve Store Items" now transitions to "In Progress" (not Pending FM
        # Approval), so on_update's post_approval_states trigger won't fire.
        # Create stock entries explicitly here while still running as Administrator.
        if action == "Approve Store Items":
            try:
                task._create_stock_entries()
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    "apply_maintenance_workflow: stock entry creation failed for {}".format(task_name)
                )

        frappe.db.commit()
        return {"success": True, "workflow_state": task.workflow_state}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "apply_maintenance_workflow: {} / {}".format(task_name, action))
        return {"success": False, "error": str(e)}
    finally:
        frappe.set_user(requesting_user)

# ── Task detail ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_maintenance_task(task_name):
    if not frappe.db.exists("Maintenance Task", task_name):
        frappe.throw(f"Maintenance Task '{task_name}' not found", frappe.DoesNotExistError)

    task = frappe.get_doc("Maintenance Task", task_name)

    if not _can_view_task(task):
        frappe.throw(
            "You can only view tasks assigned to you or where you are the supervisor/witness.",
            frappe.PermissionError,
        )

    # Resolve technician name
    technician_name = None
    if task.assigned_technician:
        technician_name = frappe.db.get_value(
            "Maintenance Technician", task.assigned_technician, "technician_name"
        )

    # Resolve supervisor name
    supervisor_name = None
    if task.supervisor:
        supervisor_name = frappe.db.get_value("Employee", task.supervisor, "employee_name")

    # Resolve reported_by name
    reported_by_name = None
    if task.reported_by:
        reported_by_name = frappe.db.get_value("Employee", task.reported_by, "employee_name")

    # Resolve requesting_department — fall back to linked request if null on task
    requesting_dept = task.requesting_department
    if not requesting_dept and task.maintenance_request:
        requesting_dept = frappe.db.get_value(
            "Maintenance Request", task.maintenance_request, "requesting_department"
        )
    # If still empty, try resolving from reported_by employee
    if not requesting_dept and task.reported_by:
        requesting_dept = frappe.db.get_value("Employee", task.reported_by, "department")

    requesting_dept_name = requesting_dept or None

    # Resolve witness_department — fall back to linked request if null on task
    witness_dept = task.witness_department
    if not witness_dept and task.maintenance_request:
        witness_dept = frappe.db.get_value(
            "Maintenance Request", task.maintenance_request, "witness_department"
        )
    # If still empty, try resolving from supervisor employee
    if not witness_dept and task.supervisor:
        witness_dept = frappe.db.get_value("Employee", task.supervisor, "department")

    witness_dept_name = witness_dept or None

    # Resolve asset name
    asset_name = None
    if task.asset:
        asset_name = frappe.db.get_value("Asset", task.asset, "asset_name") or task.asset

    # Resolve request title
    request_title = None
    if task.maintenance_request:
        request_title = frappe.db.get_value(
            "Maintenance Request", task.maintenance_request, "issue_description"
        ) or task.maintenance_request

    # Photos attached on the originating Maintenance Request -- shown
    # read-only on the task so the technician can see what was reported
    # without needing to navigate to the request page separately.
    request_images = {"image_1": None, "image_2": None, "image_3": None}
    if task.maintenance_request:
        img_row = frappe.db.get_value(
            "Maintenance Request", task.maintenance_request,
            ["image_1", "image_2", "image_3"], as_dict=True
        )
        if img_row:
            request_images = {
                "image_1": img_row.image_1 or None,
                "image_2": img_row.image_2 or None,
                "image_3": img_row.image_3 or None,
            }

    # Parts used child table
    parts_used = []
    for p in task.parts_used or []:
        parts_used.append({
            "name": p.name,
            "item_code": p.item_code,
            "item_name": p.item_name or "",
            "qty": p.quantity,
            "uom": p.uom or "",
            "warehouse": p.warehouse or "",
            "available_qty": p.available_qty or 0,
            "stock_entry": p.stock_entry or "",
        })

    # Parts returned child table
    parts_returned = []
    for p in task.parts_returned or []:
        parts_returned.append({
            "name": p.name,
            "item_code": p.item_code,
            "item_name": p.item_name or "",
            "qty": p.quantity,
            "uom": p.uom or "",
            "warehouse": p.warehouse or "",
            "available_qty": p.available_qty or 0,
            "stock_entry": p.stock_entry or "",
        })

    return {
        "name": task.name,
        "docstatus": task.docstatus,
        "workflow_state": task.workflow_state or "",

        # Task details
        "task_type": task.task_type,
        "priority": task.priority,
        "status": task.status,
        "maintenance_request": task.maintenance_request,
        "request_title": request_title,
        "request_image_1": request_images["image_1"],
        "request_image_2": request_images["image_2"],
        "request_image_3": request_images["image_3"],

        # Location (read-only, copied from request)
        "location": task.location,
        "request_location_type": task.request_location_type or "",

        # Assignment (read-only, copied from request)
        "assigned_technician": task.assigned_technician,
        "technician_name": technician_name,
        "supervisor": task.supervisor,
        "supervisor_name": supervisor_name,

        # Reporter info (read-only, copied from request)
        "reported_by": task.reported_by,
        "reported_by_name": reported_by_name,
        "requesting_department": requesting_dept or task.requesting_department or "",
        "requesting_department_name": requesting_dept_name,
        "witness_department": witness_dept or task.witness_department or "",
        "witness_department_name": witness_dept_name,
        "issue_type": task.issue_type or "",

        # Timing
        "start_time": str(task.start_time) if task.start_time else None,
        "end_time": str(task.end_time) if task.end_time else None,

        # Description
        "task_description": task.task_description or "",
        "work_performed": task.work_performed or "",
        "completion_notes": task.completion_notes or "",

        # Checklist
        "inspection_required": task.inspection_required,
        "fault_diagnosed": task.fault_diagnosed,
        "test_run_passed": task.test_run_passed,

        # Parts / materials
        "parts_used": parts_used,
        "parts_returned": parts_returned,
        "parts_approval_status": task.parts_approval_status or "Not Requested",
        "parts_approved_by": task.parts_approved_by or "",
        "parts_approved_on": str(task.parts_approved_on) if task.parts_approved_on else None,
        "material_issue_stock_entry": task.material_issue_stock_entry or "",
        "material_return_stock_entry": task.material_return_stock_entry or "",
        "asset": task.asset or "",
        "asset_name": asset_name or "",

        # Whether the current user is allowed to fill/edit the task form.
        # True only for the assigned technician and manager roles
        # (Maintenance Manager, System Manager, Hotel Manager).
        # Supervisors, reporters, and other viewers can see the task
        # but not write to it.
        "can_edit": _can_edit_task(task),

        # List of workflow action names the current user may trigger right now.
        # The frontend uses this to show/hide action buttons.
        "allowed_actions": _get_allowed_actions(task),
    }


@frappe.whitelist()
def save_maintenance_task(task_name, task_data, parts_used=None, parts_returned=None):
    if isinstance(task_data, str):
        task_data = json.loads(task_data)
    if isinstance(parts_used, str):
        parts_used = json.loads(parts_used)
    if isinstance(parts_returned, str):
        parts_returned = json.loads(parts_returned)

    try:
        task = frappe.get_doc("Maintenance Task", task_name)

        if task.docstatus == 1:
            return {"success": False, "error": "Cannot edit a submitted task"}

        # Only editable fields — read-only fields (copied from request) are excluded
        field_map = [
            "task_type", "work_performed", "completion_notes",
            "inspection_required", "fault_diagnosed", "test_run_passed"
        ]
        for field in field_map:
            if field in task_data:
                setattr(task, field, task_data[field])

        if task_data.get("start_time"):
            task.start_time = task_data["start_time"]
        if task_data.get("end_time"):
            task.end_time = task_data["end_time"]

        # Parts used
        if parts_used is not None:
            # Rows already linked to a stock entry are locked — preserve them
            # from the DB and only allow adding/modifying un-issued rows.
            locked = [
                p for p in (task.parts_used or [])
                if p.get("stock_entry")
            ]
            task.set("parts_used", [])
            for p in locked:
                task.append("parts_used", {
                    "item_code": p.item_code,
                    "item_name": p.item_name or "",
                    "quantity": p.quantity,
                    "uom": p.uom or "",
                    "warehouse": p.warehouse or "",
                    "cost": p.cost or 0,
                    "stock_entry": p.stock_entry,
                })
            for p in parts_used:
                if p.get("item_code") and not p.get("stock_entry"):
                    task.append("parts_used", {
                        "item_code": p["item_code"],
                        "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
                        "quantity": p.get("qty") or p.get("quantity") or 1,
                        "uom": p.get("uom") or "",
                        "warehouse": p.get("warehouse") or "",
                        "cost": p.get("cost") or 0,
                    })

        # Parts returned
        if parts_returned is not None:
            # Rows already linked to a stock entry are locked — preserve them
            # from the DB and only allow adding/modifying un-returned rows.
            locked_returned = [
                p for p in (task.parts_returned or [])
                if p.get("stock_entry")
            ]
            task.set("parts_returned", [])
            for p in locked_returned:
                task.append("parts_returned", {
                    "item_code": p.item_code,
                    "item_name": p.item_name or "",
                    "quantity": p.quantity,
                    "uom": p.uom or "",
                    "warehouse": p.warehouse or "",
                    "cost": p.cost or 0,
                    "stock_entry": p.stock_entry,
                })
            for p in parts_returned:
                if p.get("item_code") and not p.get("stock_entry"):
                    task.append("parts_returned", {
                        "item_code": p["item_code"],
                        "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
                        "quantity": p.get("qty") or p.get("quantity") or 1,
                        "uom": p.get("uom") or "",
                        "warehouse": p.get("warehouse") or "",
                        "cost": p.get("cost") or 0,
                    })

        task.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "save_maintenance_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_maintenance_task(task_name):
    try:
        task = frappe.get_doc("Maintenance Task", task_name)
        if task.docstatus == 1:
            return {"success": False, "error": "Task is already submitted"}
        task.submit()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_maintenance_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_maintenance_task(task_name):
    try:
        task = frappe.get_doc("Maintenance Task", task_name)
        task.cancel()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_maintenance_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_technicians_for_task():
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1, "availability": ["!=", "Unavailable"]},
        fields=["name", "technician_name", "availability", "primary_specialization"],
        order_by="technician_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_supervisors_for_task():
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation"],
        order_by="employee_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_items_for_parts():
    items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["name", "item_name", "stock_uom"],
        order_by="item_name asc",
        limit_page_length=500
    )

    for item in items:
        item["available_qty"] = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_qty), 0)
            FROM `tabBin`
            WHERE item_code = %s
        """, item.name)[0][0] or 0

    return items


@frappe.whitelist()
def get_warehouses_for_parts(company=None):
    if not company:
        company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")

    filters = {
        "is_group": 0,
        "disabled": 0
    }

    if company:
        filters["company"] = company

    return frappe.get_all(
        "Warehouse",
        filters=filters,
        fields=["name", "warehouse_name", "company"],
        order_by="warehouse_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_item_available_qty(item_code, warehouse=None):
    if not item_code:
        return {"available_qty": 0}

    if warehouse:
        qty = frappe.db.sql(
            """
            SELECT COALESCE(SUM(actual_qty), 0)
            FROM `tabBin`
            WHERE item_code = %s AND warehouse = %s
            """,
            (item_code, warehouse),
        )[0][0] or 0
    else:
        qty = frappe.db.sql(
            """
            SELECT COALESCE(SUM(actual_qty), 0)
            FROM `tabBin`
            WHERE item_code = %s
            """,
            (item_code,),
        )[0][0] or 0

    return {"available_qty": qty}


@frappe.whitelist()
def create_maintenance_task(task_data, parts_used=None):
    if isinstance(task_data, str):
        task_data = json.loads(task_data)
    if isinstance(parts_used, str):
        parts_used = json.loads(parts_used)

    try:
        task = frappe.new_doc("Maintenance Task")
        task.task_type = task_data.get("task_type", "Corrective")
        task.priority = task_data.get("priority", "Medium")
        task.status = task_data.get("status", "Open")
        task.location = task_data.get("location") or ""
        task.task_description = task_data.get("task_description") or ""
        task.assigned_technician = task_data.get("assigned_technician") or None
        task.supervisor = task_data.get("supervisor") or None
        task.maintenance_request = task_data.get("maintenance_request") or None
        task.inspection_required = 1 if task_data.get("inspection_required") else 0
        task.fault_diagnosed = 1 if task_data.get("fault_diagnosed") else 0
        task.test_run_passed = 1 if task_data.get("test_run_passed") else 0
        task.completion_notes = task_data.get("completion_notes") or ""

        if task_data.get("start_time"):
            task.start_time = task_data["start_time"]
        if task_data.get("end_time"):
            task.end_time = task_data["end_time"]

        if parts_used:
            for p in parts_used:
                if p.get("item_code"):
                    task.append("parts_used", {
                        "item_code": p["item_code"],
                        "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
                        "quantity": p.get("qty") or p.get("quantity") or 1,
                        "uom": p.get("uom") or "",
                        "warehouse": p.get("warehouse") or "",
                        "cost": p.get("cost") or 0,
                    })

        task.insert()
        frappe.db.commit()
        return {"success": True, "task_name": task.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_maintenance_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_maintenance_dashboard_summary():
    today = nowdate()
    week_start = get_first_day_of_week(today)

    open_count      = frappe.db.count("Maintenance Task", {"status": "Open"})
    in_progress     = frappe.db.count("Maintenance Task", {"status": "In Progress"})
    done_count      = frappe.db.count("Maintenance Task", {"status": "Done"})
    hold_count      = frappe.db.count("Maintenance Task", {"status": "Hold"})
    cancelled_count = frappe.db.count("Maintenance Task", {"status": "Cancelled"})
    urgent_open     = frappe.db.count("Maintenance Task", {"priority": "High", "status": ["not in", ["Done", "Cancelled"]]})
    pending_requests = frappe.db.count("Maintenance Request", {"status": "Pending"})
    urgent_pending_requests = frappe.db.count(
        "Maintenance Request", {"status": "Pending", "priority": ["in", ["Critical", "High"]]}
    )

    done_this_week = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMaintenance Task`
        WHERE status = 'Done'
        AND DATE(end_time) >= %s AND DATE(end_time) <= %s
    """, (week_start, today), as_dict=1)[0].cnt or 0

    type_counts = frappe.db.sql("""
        SELECT task_type, COUNT(name) as cnt
        FROM `tabMaintenance Task`
        WHERE task_type IS NOT NULL
        GROUP BY task_type
    """, as_dict=1)
    total_typed = sum(r.cnt for r in type_counts) or 1
    type_mix = {r.task_type: round((r.cnt / total_typed) * 100, 1) for r in type_counts}
    corrective_pct = type_mix.get("Corrective", 0)

    avg_res = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, start_time, end_time)) as avg_hrs
        FROM `tabMaintenance Task`
        WHERE status = 'Done'
        AND start_time IS NOT NULL AND end_time IS NOT NULL
        AND DATE(end_time) >= %s
    """, (week_start,), as_dict=1)
    avg_resolution_hrs = round(avg_res[0].avg_hrs or 0, 1) if avg_res else 0

    top_locations = frappe.db.sql("""
        SELECT location, COUNT(name) as open_tasks
        FROM `tabMaintenance Task`
        WHERE status NOT IN ('Done','Cancelled')
        AND location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY open_tasks DESC
        LIMIT 4
    """, as_dict=1)

    recent = frappe.get_all(
        "Maintenance Task",
        fields=["name", "task_type", "status", "priority",
                "assigned_technician", "location", "task_description", "modified",
                "workflow_state"],
        order_by="modified desc",
        limit_page_length=5
    )

    tech_cache = {}
    for task in recent:
        if task.get("assigned_technician"):
            tid = task["assigned_technician"]
            if tid not in tech_cache:
                tech_cache[tid] = frappe.db.get_value("Maintenance Technician", tid, "technician_name") or tid
            task["technician_name"] = tech_cache[tid]
        else:
            task["technician_name"] = "Unassigned"

    return {
        "stats": {
            "pending_requests": pending_requests,
            "urgent_pending_requests": urgent_pending_requests,
            "open": open_count,
            "in_progress": in_progress,
            "done": done_count,
            "hold": hold_count,
            "cancelled": cancelled_count,
            "urgent_open": urgent_open,
            "done_this_week": done_this_week,
            "avg_resolution_hrs": avg_resolution_hrs,
        },
        "type_mix": type_mix,
        "corrective_pct": corrective_pct,
        "top_locations": top_locations,
        "recent_activity": recent,
    }