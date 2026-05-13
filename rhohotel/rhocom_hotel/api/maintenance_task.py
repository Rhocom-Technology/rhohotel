import frappe
import json
from frappe.utils import nowdate, add_days, get_first_day_of_week


@frappe.whitelist()
def get_maintenance_dashboard():
    """
    Stats for the maintenance list page header cards.
    Returns live counts and time-bounded counts.
    """
    today = nowdate()
    week_start = get_first_day_of_week(today)

    # ── Primary status counts ───────────────────────────────────────────────
    status_counts = {}
    for status in ["Open", "In Progress", "Done", "Hold", "Cancelled"]:
        status_counts[status] = frappe.db.count(
            "Maintenance Task", {"status": status}
        )

    # ── Time-bounded counts ─────────────────────────────────────────────────
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
    """Paginated maintenance task list with technician name resolved"""
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
        "maintenance_request"
    ]

    if search:
        tasks = frappe.db.sql("""
            SELECT
                name, task_type, status, priority,
                location, task_description,
                assigned_technician, start_time, end_time,
                maintenance_request
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

    # Resolve technician names
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
    """Technician list for the filter dropdown"""
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1},
        fields=["name", "technician_name"],
        order_by="technician_name asc",
        limit_page_length=200
    )


def _build_filter_clause(filters):
    """Build extra AND clauses from a filters dict for raw SQL"""
    clauses = []
    for field, value in filters.items():
        safe_field = field.replace("`", "")
        safe_value = value.replace("'", "''")
        clauses.append(f"AND `{safe_field}` = '{safe_value}'")
    return " ".join(clauses)


# ── Task detail functions ──────────────────────────────────────────────────────

@frappe.whitelist()
def get_maintenance_task(task_name):
    """Full maintenance task with resolved linked names"""
    if not frappe.db.exists("Maintenance Task", task_name):
        frappe.throw(f"Maintenance Task '{task_name}' not found", frappe.DoesNotExistError)

    task = frappe.get_doc("Maintenance Task", task_name)

    technician_name = None
    if task.assigned_technician:
        technician_name = frappe.db.get_value(
            "Maintenance Technician", task.assigned_technician, "technician_name"
        )

    supervisor_name = None
    if task.supervisor:
        supervisor_name = frappe.db.get_value("Employee", task.supervisor, "employee_name")

    request_title = None
    if task.maintenance_request:
        request_title = frappe.db.get_value(
            "Maintenance Request", task.maintenance_request, "issue_description"
        ) or task.maintenance_request

    parts_used = []
    for p in task.parts_used or []:
        parts_used.append({
            "name": p.name,
            "item_code": p.item_code,
            "item_name": p.item_name or "",
            "qty": p.quantity,
            "uom": p.uom,
            "warehouse": p.warehouse or "",
            "cost": p.cost or 0,
            "store_impact": p.store_impact or "Reduce Stock",
        })

    return {
        "name": task.name,
        "docstatus": task.docstatus,
        "task_type": task.task_type,
        "maintenance_request": task.maintenance_request,
        "request_title": request_title,
        "priority": task.priority,
        "status": task.status,
        "assigned_technician": task.assigned_technician,
        "technician_name": technician_name,
        "supervisor": task.supervisor,
        "supervisor_name": supervisor_name,
        "start_time": str(task.start_time) if task.start_time else None,
        "end_time": str(task.end_time) if task.end_time else None,
        "location": task.location,
        "task_description": task.task_description,
        "work_performed": task.work_performed,
        "completion_notes": task.completion_notes,
        "inspection_required": task.inspection_required,
        "fault_diagnosed": task.fault_diagnosed,
        "test_run_passed": task.test_run_passed,
        "supervisor_verified": task.supervisor_verified,
        "stock_entry": task.stock_entry,
        "parts_used": parts_used,
    }


@frappe.whitelist()
def save_maintenance_task(task_name, task_data, parts_used=None):
    """Save (draft) a maintenance task"""
    if isinstance(task_data, str):
        task_data = json.loads(task_data)
    if isinstance(parts_used, str):
        parts_used = json.loads(parts_used)

    try:
        task = frappe.get_doc("Maintenance Task", task_name)

        if task.docstatus == 1:
            return {"success": False, "error": "Cannot edit a submitted task"}

        field_map = [
            "task_type", "priority", "status", "assigned_technician",
            "supervisor", "location",
            "task_description", "work_performed", "completion_notes",
            "inspection_required", "fault_diagnosed",
            "test_run_passed", "supervisor_verified"
        ]
        for field in field_map:
            if field in task_data:
                setattr(task, field, task_data[field])

        if task_data.get("start_time"):
            task.start_time = task_data["start_time"]
        if task_data.get("end_time"):
            task.end_time = task_data["end_time"]

        if parts_used is not None:
            task.set("parts_used", [])
            for p in parts_used:
                if p.get("item_code"):
                    task.append("parts_used", {
                        "item_code": p["item_code"],
                        "item_name": p.get("item_name") or frappe.db.get_value("Item", p["item_code"], "item_name") or "",
                        "quantity": p.get("qty") or p.get("quantity") or 1,
                        "uom": p.get("uom") or "",
                        "warehouse": p.get("warehouse") or "",
                        "cost": p.get("cost") or 0,
                        "store_impact": p.get("store_impact") or "Reduce Stock",
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
    """Submit (complete) a maintenance task"""
    try:
        task = frappe.get_doc("Maintenance Task", task_name)

        if task.docstatus == 1:
            return {"success": False, "error": "Task is already submitted"}

        task.status = "Done"
        task.submit()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_maintenance_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_maintenance_task(task_name):
    """Cancel a submitted maintenance task"""
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
    """Technicians available for assignment dropdown"""
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1, "availability": ["!=", "Unavailable"]},
        fields=["name", "technician_name", "availability", "primary_specialization"],
        order_by="technician_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_supervisors_for_task():
    """Active employees for supervisor dropdown"""
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation"],
        order_by="employee_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_items_for_parts():
    """Stock items for parts used dropdown"""
    return frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["name", "item_name", "stock_uom"],
        order_by="item_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def create_maintenance_task(task_data, parts_used=None):
    """Create a new Maintenance Task doc"""
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
                        "store_impact": p.get("store_impact") or "Reduce Stock",
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
    """
    Dashboard summary for the Maintenance Control Center.
    Returns stats, task type mix, recent activity, and top locations by open tasks.
    """
    today = nowdate()
    week_start = get_first_day_of_week(today)

    # ── Status counts ────────────────────────────────────────────────────────
    open_count      = frappe.db.count("Maintenance Task", {"status": "Open"})
    in_progress     = frappe.db.count("Maintenance Task", {"status": "In Progress"})
    done_count      = frappe.db.count("Maintenance Task", {"status": "Done"})
    hold_count      = frappe.db.count("Maintenance Task", {"status": "Hold"})
    cancelled_count = frappe.db.count("Maintenance Task", {"status": "Cancelled"})
    urgent_open     = frappe.db.count("Maintenance Task", {"priority": "High", "status": ["not in", ["Done", "Cancelled"]]})

    done_this_week = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMaintenance Task`
        WHERE status = 'Done'
        AND DATE(end_time) >= %s AND DATE(end_time) <= %s
    """, (week_start, today), as_dict=1)[0].cnt or 0

    # ── Task type mix ─────────────────────────────────────────────────────────
    type_counts = frappe.db.sql("""
        SELECT task_type, COUNT(name) as cnt
        FROM `tabMaintenance Task`
        WHERE task_type IS NOT NULL
        GROUP BY task_type
    """, as_dict=1)
    total_typed = sum(r.cnt for r in type_counts) or 1
    type_mix = {r.task_type: round((r.cnt / total_typed) * 100, 1) for r in type_counts}
    corrective_pct = type_mix.get("Corrective", 0)

    # ── Avg resolution time (hrs) ─────────────────────────────────────────────
    avg_res = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, start_time, end_time)) as avg_hrs
        FROM `tabMaintenance Task`
        WHERE status = 'Done'
        AND start_time IS NOT NULL AND end_time IS NOT NULL
        AND DATE(end_time) >= %s
    """, (week_start,), as_dict=1)
    avg_resolution_hrs = round(avg_res[0].avg_hrs or 0, 1) if avg_res else 0

    # ── Top locations by open task count ──────────────────────────────────────
    top_locations = frappe.db.sql("""
        SELECT location, COUNT(name) as open_tasks
        FROM `tabMaintenance Task`
        WHERE status NOT IN ('Done','Cancelled')
        AND location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY open_tasks DESC
        LIMIT 4
    """, as_dict=1)

    # ── Recent activity (latest 5 tasks) ─────────────────────────────────────
    recent = frappe.get_all(
        "Maintenance Task",
        fields=["name", "task_type", "status", "priority",
                "assigned_technician", "location", "task_description", "modified"],
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
