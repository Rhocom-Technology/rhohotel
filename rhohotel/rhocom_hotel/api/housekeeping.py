import frappe
from frappe.utils import nowdate, add_days
from datetime import datetime

@frappe.whitelist()
def get_dashboard():
    """
    Housekeeping Dashboard Aggregation API
    Based strictly on Housekeeping Task doctype
    """
    
    today = nowdate()
    
    # ---------------------------
    # 1. TASK STATISTICS BY STATUS
    # ---------------------------
    task_stats = frappe.db.sql("""
        SELECT
            status,
            COUNT(name) as count
        FROM `tabHousekeeping Task`
        GROUP BY status
    """, as_dict=1)
    
    stats = {
        "Pending": 0,
        "Approved": 0,
        "Assigned": 0,
        "In Progress": 0,
        "Completed": 0,
        "On Hold": 0,
        "Cancelled": 0
    }
    
    for row in task_stats:
        if row.status in stats:
            stats[row.status] = row.count
    
    # Derived room status (based on task status)
    dirty_rooms = stats["Pending"] + stats["Assigned"] + stats["In Progress"]
    clean_rooms = stats["Completed"]
    
    # ---------------------------
    # 2. TASK STATISTICS BY PRIORITY
    # ---------------------------
    priority_stats = frappe.db.sql("""
        SELECT
            priority,
            COUNT(name) as count
        FROM `tabHousekeeping Task`
        GROUP BY priority
    """, as_dict=1)
    
    priorities = {
        "Low": 0,
        "Medium": 0,
        "High": 0,
        "Urgent": 0
    }
    
    for row in priority_stats:
        if row.priority in priorities:
            priorities[row.priority] = row.count
    
    # ---------------------------
    # 3. TASK STATISTICS BY TYPE
    # ---------------------------
    task_type_stats = frappe.db.sql("""
        SELECT
            task_type,
            COUNT(name) as count
        FROM `tabHousekeeping Task`
        GROUP BY task_type
    """, as_dict=1)
    
    # ---------------------------
    # 4. RECENT ROOM UPDATES (LIMITED TO 10)
    # ---------------------------
    room_board = frappe.db.sql("""
        SELECT
            name,
            room,
            task_type,
            status,
            priority,
            employee,
            start_time,
            end_time
        FROM `tabHousekeeping Task`
        ORDER BY modified DESC
        LIMIT 10
    """, as_dict=1)
    
    # ---------------------------
    # 5. ATTENDANT WORKLOAD (LIMITED TO 10)
    # ---------------------------
    attendants = frappe.db.sql("""
        SELECT
            employee,
            COUNT(name) as total_tasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'On Hold' THEN 1 ELSE 0 END) as on_hold,
            SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM `tabHousekeeping Task`
        WHERE employee IS NOT NULL AND employee != ''
        GROUP BY employee
        ORDER BY total_tasks DESC
        LIMIT 10
    """, as_dict=1)
    
    attendants_data = []
    for a in attendants:
        summary = f"{a.total_tasks} total • {a.completed} completed • {a.in_progress} in progress • {a.assigned} assigned • {a.pending} pending"
        if a.on_hold > 0:
            summary += f" • {a.on_hold} on hold"
        attendants_data.append({
            "employee": a.employee,
            "name": frappe.db.get_value("Employee", a.employee, "employee_name") or a.employee,
            "summary": summary,
            "total_tasks": a.total_tasks,
            "completed": a.completed,
            "in_progress": a.in_progress,
            "assigned": a.assigned,
            "pending": a.pending,
            "on_hold": a.on_hold,
            "cancelled": a.cancelled
        })
    
    # ---------------------------
    # 6. HIGH PRIORITY TASKS (LIMITED TO 10)
    # ---------------------------
    high_priority_tasks = frappe.db.sql("""
        SELECT
            name,
            room,
            task_type,
            status,
            priority,
            employee,
            start_time
        FROM `tabHousekeeping Task`
        WHERE priority IN ('High', 'Urgent')
        AND status NOT IN ('Completed', 'Cancelled')
        ORDER BY 
            CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 END,
            modified DESC
        LIMIT 10
    """, as_dict=1)
    
    # ---------------------------
    # 7. TODAY'S TASKS (LIMITED TO 10)
    # ---------------------------
    today_tasks = frappe.db.sql("""
        SELECT
            name,
            room,
            task_type,
            status,
            priority,
            employee,
            start_time,
            end_time
        FROM `tabHousekeeping Task`
        WHERE DATE(start_time) = %s
        ORDER BY start_time ASC
        LIMIT 10
    """, today, as_dict=1)
    
    # ---------------------------
    # 8. INVENTORY CHANGES SUMMARY
    # ---------------------------
    inventory_changes = frappe.db.sql("""
        SELECT
            change_type,
            SUM(quantity_changed) as total_quantity,
            COUNT(*) as total_items
        FROM `tabHousekeeping Task Inventory Change`
        GROUP BY change_type
    """, as_dict=1)
    
    inventory_summary = {
        "Added": {"quantity": 0, "items": 0},
        "Removed": {"quantity": 0, "items": 0},
        "Replaced": {"quantity": 0, "items": 0}
    }
    
    for change in inventory_changes:
        if change.change_type in inventory_summary:
            inventory_summary[change.change_type]["quantity"] = change.total_quantity or 0
            inventory_summary[change.change_type]["items"] = change.total_items or 0
    
    # Top changed items (LIMITED TO 5)
    top_items = frappe.db.sql("""
        SELECT
            item,
            change_type,
            SUM(quantity_changed) as total_quantity
        FROM `tabHousekeeping Task Inventory Change`
        GROUP BY item, change_type
        ORDER BY total_quantity DESC
        LIMIT 5
    """, as_dict=1)

    # ---------------------------
    # 9. RECENT NOTES (LIMITED TO 5)
    # ---------------------------
    recent_notes = frappe.db.sql("""
        SELECT
            name,
            room,
            notes,
            modified,
            modified_by
        FROM `tabHousekeeping Task`
        WHERE notes IS NOT NULL AND notes != ''
        ORDER BY modified DESC
        LIMIT 5
    """, as_dict=1)
    
    # ---------------------------
    # 10. COMPLETION TREND (Last 7 days)
    # ---------------------------
    seven_days_ago = add_days(today, -7)
    completion_trend = frappe.db.sql("""
        SELECT
            DATE(end_time) as completion_date,
            COUNT(name) as completed_count
        FROM `tabHousekeeping Task`
        WHERE status = 'Completed'
        AND end_time IS NOT NULL
        AND DATE(end_time) >= %s
        GROUP BY DATE(end_time)
        ORDER BY completion_date ASC
        LIMIT 7
    """, seven_days_ago, as_dict=1)
    
    # ---------------------------
    # RESPONSE
    # ---------------------------
    return {
        "date": today,
        "statistics": {
            "by_status": stats,
            "by_priority": priorities,
            "by_task_type": task_type_stats,
            "total_tasks": sum(stats.values()),
            "active_tasks": stats["Pending"] + stats["Approved"] + stats["Assigned"] + stats["In Progress"],
            "completion_rate": round((stats["Completed"] / sum(stats.values()) * 100), 1) if sum(stats.values()) > 0 else 0
        },
        "room_metrics": {
            "dirty_rooms": dirty_rooms,
            "clean_rooms": clean_rooms,
            "rooms_under_maintenance": stats["On Hold"],
            "rooms_blocked": stats["Cancelled"]
        },
        "priority_tasks": high_priority_tasks,
        "today_tasks": today_tasks,
        "attendants": attendants_data,
        "recent_room_updates": room_board,
        "inventory_summary": inventory_summary,
        "top_inventory_items": top_items,
        "recent_notes": recent_notes,
        "completion_trend": completion_trend
    }


# @frappe.whitelist()
# def get_task_details(task_name=None, status=None, employee=None, priority=None):
#     """
#     Get filtered housekeeping tasks with room details
#     """
#     filters = {}
#     if task_name:
#         filters["name"] = task_name
#     if status:
#         filters["status"] = status
#     if employee:
#         filters["employee"] = employee
#     if priority:
#         filters["priority"] = priority
    
#     tasks = frappe.get_all(
#         "Housekeeping Task",
#         fields=["name", "room", "task_type", "status", "priority", "employee", "start_time", "end_time", "notes", "docstatus", "checklist_template"],
#         filters=filters,
#         order_by="modified desc",
#         limit_page_length=100
#     )
    
#     # Add room details to each task
#     for task in tasks:
#         if task.get("room"):
#             room_details = frappe.db.get_value("Hotel Room", 
#                 task.get("room"),
#                 ["room_number", "room_type", "floor", "status", "housekeeping_status"],
#                 as_dict=1
#             )
#             if room_details:
#                 task["room_number"] = room_details.get("room_number")
#                 task["room_type"] = room_details.get("room_type")
#                 task["floor"] = room_details.get("floor")
#                 task["room_status"] = room_details.get("status")
#                 task["housekeeping_status"] = room_details.get("housekeeping_status")
    
#     return tasks


@frappe.whitelist()
def get_employees():
    """
    Get list of employees for dropdown filter
    """
    employees = frappe.db.sql("""
        SELECT 
            name,
            employee_name
        FROM `tabEmployee`
        WHERE status = 'Active'
        ORDER BY employee_name ASC
    """, as_dict=1)
    
    return employees


@frappe.whitelist()
def get_inventory_details():
    """
    Get detailed inventory changes
    """
    changes = frappe.db.sql("""
        SELECT
            ht.name as task_name,
            ht.room,
            ht.task_type,
            htic.item,
            htic.change_type,
            htic.quantity_changed,
            htic.reason,
            htic.uom,
            ht.modified
        FROM `tabHousekeeping Task Inventory Change` htic
        INNER JOIN `tabHousekeeping Task` ht ON ht.name = htic.parent
        ORDER BY ht.modified DESC
        LIMIT 50
    """, as_dict=1)
    
    return changes


@frappe.whitelist()
def get_room_details(room_name):
    """
    Get room details including room type, floor, and status from Hotel Room doctype
    """
    if not room_name:
        return {}
    
    room = frappe.db.get_value("Hotel Room", 
        {"name": room_name}, 
        ["room_number", "room_type", "floor", "status", "housekeeping_status", "operational_status", "current_guest"],
        as_dict=1
    )
    
    if room and room.get("room_type"):
        # Get room type details
        room_type = frappe.db.get_value("Hotel Room Type", 
            room.get("room_type"),
            ["room_type", "capacity", "base_adult", "max_adult"],
            as_dict=1
        )
        if room_type:
            room["room_type_name"] = room_type.get("room_type")
            room["capacity"] = room_type.get("capacity")
    
    return room or {}


@frappe.whitelist()
def get_checklist_templates():
    """
    Get list of checklist templates
    """
    templates = frappe.get_all("Task Checklist Template", fields=["name"])
    return templates


@frappe.whitelist()
def get_checklist_template(template_name):
    """
    Get checklist template items
    """
    if not template_name:
        return {"name": "", "items": []}
    
    template = frappe.get_doc("Task Checklist Template", template_name)
    return {
        "name": template.name,
        "items": template.checklist_items if template.checklist_items else []
    }


@frappe.whitelist()
def get_task_inventory(task_name):
    """
    Get inventory changes for a task
    """
    changes = frappe.db.sql("""
        SELECT
            item,
            quantity_changed,
            change_type,
            reason,
            uom
        FROM `tabHousekeeping Task Inventory Change`
        WHERE parent = %s
    """, task_name, as_dict=1)
    
    return changes


# @frappe.whitelist()
# def update_task(task_name, task_data, inventory_items=None, checklist_items=None):
#     """
#     Update a housekeeping task with inventory and checklist
#     """
#     try:
#         task = frappe.get_doc("Housekeeping Task", task_name)
        
#         # Update basic fields
#         if "task_type" in task_data:
#             task.task_type = task_data["task_type"]
#         if "priority" in task_data:
#             task.priority = task_data["priority"]
#         if "employee" in task_data:
#             task.employee = task_data["employee"]
#         if "status" in task_data:
#             task.status = task_data["status"]
#         if "start_time" in task_data and task_data["start_time"]:
#             task.start_time = task_data["start_time"]
#         if "notes" in task_data:
#             task.notes = task_data["notes"]
#         if "checklist_template" in task_data:
#             task.checklist_template = task_data["checklist_template"]
        
#         # Update inventory items
#         if inventory_items is not None:
#             task.set("room_inventory_changes", [])
#             for item in inventory_items:
#                 if item.get("item") and item.get("item") != "":
#                     task.append("room_inventory_changes", {
#                         "item": item.get("item"),
#                         "quantity_changed": item.get("quantity_changed", 1),
#                         "change_type": item.get("change_type", "Added"),
#                         "reason": item.get("reason", "")
#                     })
        
#         # Update checklist items
#         if checklist_items is not None:
#             task.set("checklist_items", [])
#             for item in checklist_items:
#                 if item.get("item_name") or item.get("description"):
#                     task.append("checklist_items", {
#                         "item_name": item.get("item_name") or item.get("description"),
#                         "remarks": "Completed" if item.get("completed") else "Pending",
#                         "status": "Pass" if item.get("completed") else "Fail"
#                     })
        
#         task.save()
#         frappe.db.commit()
        
#         return {"success": True, "message": "Task updated successfully"}
#     except Exception as e:
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


# @frappe.whitelist()
# def get_task_details(task_name=None, status=None, employee=None, priority=None):
#     """
#     Get filtered housekeeping tasks with room details + child table data
#     """
#     filters = {}
#     if task_name:
#         filters["name"] = task_name
#     if status:
#         filters["status"] = status
#     if employee:
#         filters["employee"] = employee
#     if priority:
#         filters["priority"] = priority

#     tasks = frappe.get_all(
#         "Housekeeping Task",
#         fields=[
#             "name", "room", "task_type", "status", "priority", "employee",
#             "start_time", "end_time", "notes", "docstatus", "checklist_template"
#         ],
#         filters=filters,
#         order_by="modified desc",
#         limit_page_length=100
#     )

#     for task in tasks:
#         # Room details
#         if task.get("room"):
#             room_details = frappe.db.get_value(
#                 "Hotel Room",
#                 task["room"],
#                 ["room_number", "room_type", "floor", "status", "housekeeping_status"],
#                 as_dict=1
#             )
#             if room_details:
#                 task["room_number"] = room_details.get("room_number")
#                 task["room_type"] = room_details.get("room_type")
#                 task["floor"] = room_details.get("floor")
#                 task["room_status"] = room_details.get("status")
#                 task["housekeeping_status"] = room_details.get("housekeeping_status")

#         # ── FIX 1: Load inventory child table ──────────────────────────────
#         task["room_inventory_changes"] = frappe.get_all(
#             "Housekeeping Task Inventory Change",
#             filters={"parent": task["name"]},
#             fields=["item", "quantity_changed", "change_type", "reason", "uom"],
#             order_by="idx asc"
#         )

#         # ── Load checklist child table ──────────────────────────────────────
#         task["checklist_items"] = frappe.get_all(
#             "Task Checklist Item",
#             filters={"parent": task["name"]},
#             fields=["item_description", "is_mandatory", "is_completed", "sequence", "notes"],
#             order_by="sequence asc, idx asc"
#         )

#     return tasks


# @frappe.whitelist()
# def update_task(task_name, task_data, inventory_items=None, checklist_items=None):
#     """
#     Update a housekeeping task with inventory and checklist
#     """
#     import json

#     # frappe-ui passes JSON strings for complex params — parse if needed
#     if isinstance(task_data, str):
#         task_data = json.loads(task_data)
#     if isinstance(inventory_items, str):
#         inventory_items = json.loads(inventory_items)
#     if isinstance(checklist_items, str):
#         checklist_items = json.loads(checklist_items)

#     try:
#         task = frappe.get_doc("Housekeeping Task", task_name)

#         # Basic fields
#         field_map = {
#             "task_type": "task_type",
#             "priority": "priority",
#             "employee": "employee",
#             "status": "status",
#             "notes": "notes",
#             "checklist_template": "checklist_template",
#         }
#         for key, field in field_map.items():
#             if key in task_data:
#                 setattr(task, field, task_data[key])

#         if task_data.get("start_time"):
#             task.start_time = task_data["start_time"]

#         # ── FIX 1: Save inventory child table ──────────────────────────────
#         if inventory_items is not None:
#             task.set("room_inventory_changes", [])
#             for item in inventory_items:
#                 if item.get("item"):   # only skip truly empty rows
#                     task.append("room_inventory_changes", {
#                         "item": item["item"],
#                         "quantity_changed": item.get("quantity_changed") or 1,
#                         "change_type": item.get("change_type") or "Added",
#                         "reason": item.get("reason") or "",
#                     })

#         # ── FIX 2: Save checklist child table using correct field names ─────
#         # Vue sends: { item_description, is_mandatory, is_completed, sequence, notes }
#         # Task Checklist Item doctype fields: item_description, is_mandatory, is_completed, sequence, notes
#         if checklist_items is not None:
#             task.set("checklist_items", [])
#             for item in checklist_items:
#                 desc = (
#                     item.get("item_description")
#                     or item.get("item_name")
#                     or item.get("description")
#                     or ""
#                 ).strip()
#                 if not desc:
#                     continue
#                 task.append("checklist_items", {
#                     "item_description": desc,
#                     "is_mandatory": 1 if item.get("is_mandatory") else 0,
#                     "is_completed": 1 if item.get("is_completed") else 0,
#                     "sequence": item.get("sequence") or 0,
#                     "notes": item.get("notes") or "",
#                 })

#         task.save()
#         frappe.db.commit()
#         return {"success": True, "message": "Task updated successfully"}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "update_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}

# @frappe.whitelist()
# def get_task_details(task_name=None, status=None, employee=None, priority=None):
#     """
#     Get filtered housekeeping tasks with room details + child table data
#     """
#     filters = {}
#     if task_name:
#         filters["name"] = task_name
#     if status:
#         filters["status"] = status
#     if employee:
#         filters["employee"] = employee
#     if priority:
#         filters["priority"] = priority

#     tasks = frappe.get_all(
#         "Housekeeping Task",
#         fields=[
#             "name", "room", "task_type", "status", "priority", "employee",
#             "start_time", "end_time", "notes", "docstatus", "checklist_template"
#         ],
#         filters=filters,
#         order_by="modified desc",
#         limit_page_length=100
#     )

#     for task in tasks:
#         # Room details
#         if task.get("room"):
#             room_details = frappe.db.get_value(
#                 "Hotel Room",
#                 task["room"],
#                 ["room_number", "room_type", "floor", "status", "housekeeping_status"],
#                 as_dict=1
#             )
#             task["room_inventory_before"] = frappe.get_all(
#                 "Hotel Room Inventory",
#                 filters={"parent": task["room"]},
#                 fields=["item", "item_name", "quantity", "uom"],
#                 order_by="idx asc"
#             )
#             else:
#                 task["room_inventory_before"] = []
            
#             if room_details:
#                 task["room_number"] = room_details.get("room_number")
#                 task["room_type"] = room_details.get("room_type")
#                 task["floor"] = room_details.get("floor")
#                 task["room_status"] = room_details.get("status")
#                 task["housekeeping_status"] = room_details.get("housekeeping_status")

#         # ── FIX 1: Load inventory child table ──────────────────────────────
#         task["room_inventory_changes"] = frappe.get_all(
#             "Housekeeping Task Inventory Change",
#             filters={"parent": task["name"]},
#             fields=["item", "quantity_changed", "change_type", "reason", "uom"],
#             order_by="idx asc"
#         )

#         # ── Load checklist child table ──────────────────────────────────────
#         task["checklist_items"] = frappe.get_all(
#             "Task Checklist Item",
#             filters={"parent": task["name"]},
#             fields=["item_description", "is_mandatory", "is_completed", "sequence", "notes"],
#             order_by="sequence asc, idx asc"
#         )
        
        

#     return tasks

# @frappe.whitelist()
# def get_task_details(task_name=None, status=None, employee=None, priority=None):
#     """
#     Get filtered housekeeping tasks with room details + child table data
#     """

#     filters = {}

#     if task_name:
#         filters["name"] = task_name

#     if status:
#         filters["status"] = status

#     if employee:
#         filters["employee"] = employee

#     if priority:
#         filters["priority"] = priority

#     tasks = frappe.get_all(
#         "Housekeeping Task",
#         fields=[
#             "name",
#             "room",
#             "task_type",
#             "status",
#             "priority",
#             "employee",
#             "start_time",
#             "end_time",
#             "notes",
#             "docstatus",
#             "checklist_template"
#         ],
#         filters=filters,
#         order_by="modified desc",
#         limit_page_length=100
#     )

#     for task in tasks:

#         # ── Room details ─────────────────────────────────────────────
#         if task.get("room"):

#             room_details = frappe.db.get_value(
#                 "Hotel Room",
#                 task["room"],
#                 [
#                     "room_number",
#                     "room_type",
#                     "floor",
#                     "status",
#                     "housekeeping_status"
#                 ],
#                 as_dict=1
#             )

#             task["room_inventory_before"] = frappe.get_all(
#                 "Hotel Room Inventory",
#                 filters={"parent": task["room"]},
#                 fields=[
#                     "item",
#                     "item_name",
#                     "quantity",
#                     "uom"
#                 ],
#                 order_by="idx asc"
#             )

#             if room_details:
#                 task["room_number"] = room_details.get("room_number")
#                 task["room_type"] = room_details.get("room_type")
#                 task["floor"] = room_details.get("floor")
#                 task["room_status"] = room_details.get("status")
#                 task["housekeeping_status"] = room_details.get("housekeeping_status")

#         else:
#             task["room_inventory_before"] = []

#         # ── Inventory changes child table ───────────────────────────
#         task["room_inventory_changes"] = frappe.get_all(
#             "Housekeeping Task Inventory Change",
#             filters={"parent": task["name"]},
#             fields=[
#                 "item",
#                 "quantity_changed",
#                 "change_type",
#                 "reason",
#                 "uom"
#             ],
#             order_by="idx asc"
#         )

#         # ── Checklist child table ───────────────────────────────────
#         task["checklist_items"] = frappe.get_all(
#             "Task Checklist Item",
#             filters={"parent": task["name"]},
#             fields=[
#                 "item_description",
#                 "is_mandatory",
#                 "is_completed",
#                 "sequence",
#                 "notes"
#             ],
#             order_by="sequence asc, idx asc"
#         )

#     return tasks


@frappe.whitelist()
def get_task_details(task_name=None, status=None, employee=None, priority=None):
    filters = {}

    if task_name:
        filters["name"] = task_name
    if status:
        filters["status"] = status
    if employee:
        filters["employee"] = employee
    if priority:
        filters["priority"] = priority

    tasks = frappe.get_all(
        "Housekeeping Task",
        fields=[
            "name", "room", "task_type", "status", "priority", "employee",
            "start_time", "end_time", "notes", "docstatus", "checklist_template"
        ],
        filters=filters,
        order_by="modified desc",
        limit_page_length=100
    )

    for task in tasks:
        if task.get("room"):
            room_details = frappe.db.get_value(
                "Hotel Room",
                task["room"],
                ["room_number", "room_type", "floor", "status", "housekeeping_status"],
                as_dict=1
            )

            task["room_inventory_before"] = frappe.get_all(
                "Hotel Room Inventory Item",
                filters={"parent": task["room"]},
                fields=["item", "quantity"],
                order_by="idx asc"
            )

            for inv in task["room_inventory_before"]:
                inv["item_name"] = frappe.db.get_value("Item", inv.get("item"), "item_name") or inv.get("item")
                inv["uom"] = frappe.db.get_value("Item", inv.get("item"), "stock_uom") or ""

            if room_details:
                task["room_number"] = room_details.get("room_number")
                task["room_type"] = room_details.get("room_type")
                task["floor"] = room_details.get("floor")
                task["room_status"] = room_details.get("status")
                task["housekeeping_status"] = room_details.get("housekeeping_status")
        else:
            task["room_inventory_before"] = []

        task["room_inventory_changes"] = frappe.get_all(
            "Housekeeping Task Inventory Change",
            filters={"parent": task["name"]},
            fields=["item", "quantity_changed", "change_type", "reason", "uom"],
            order_by="idx asc"
        )

        task["checklist_items"] = frappe.get_all(
            "Task Checklist Item",
            filters={"parent": task["name"]},
            fields=["item_description", "is_mandatory", "is_completed", "sequence", "notes"],
            order_by="sequence asc, idx asc"
        )

    return tasks

# @frappe.whitelist()
# def update_task(task_name, task_data, inventory_items=None, checklist_items=None):
#     """
#     Update a housekeeping task with inventory and checklist
#     """
#     import json

#     # frappe-ui passes JSON strings for complex params — parse if needed
#     if isinstance(task_data, str):
#         task_data = json.loads(task_data)
#     if isinstance(inventory_items, str):
#         inventory_items = json.loads(inventory_items)
#     if isinstance(checklist_items, str):
#         checklist_items = json.loads(checklist_items)

#     try:
#         task = frappe.get_doc("Housekeeping Task", task_name)

#         # Basic fields
#         field_map = {
#             "task_type": "task_type",
#             "priority": "priority",
#             "employee": "employee",
#             "status": "status",
#             "notes": "notes",
#             "checklist_template": "checklist_template",
#         }
#         for key, field in field_map.items():
#             if key in task_data:
#                 setattr(task, field, task_data[key])

#         if task_data.get("start_time"):
#             task.start_time = task_data["start_time"]
#         if task_data.get("end_time"):
#             task.end_time = task_data["end_time"]

#         # ── FIX 1: Save inventory child table ──────────────────────────────
#         if inventory_items is not None:
#             task.set("room_inventory_changes", [])
#             for item in inventory_items:
#                 if item.get("item"):   # only skip truly empty rows
#                     task.append("room_inventory_changes", {
#                         "item": item["item"],
#                         "quantity_changed": item.get("quantity_changed") or 1,
#                         "change_type": item.get("change_type") or "Added",
#                         "reason": item.get("reason") or "",
#                     })

#         # ── FIX 2: Save checklist child table using correct field names ─────
#         # Vue sends: { item_description, is_mandatory, is_completed, sequence, notes }
#         # Task Checklist Item doctype fields: item_description, is_mandatory, is_completed, sequence, notes
#         if checklist_items is not None:
#             task.set("checklist_items", [])
#             for item in checklist_items:
#                 desc = (
#                     item.get("item_description")
#                     or item.get("item_name")
#                     or item.get("description")
#                     or ""
#                 ).strip()
#                 if not desc:
#                     continue
#                 task.append("checklist_items", {
#                     "item_description": desc,
#                     "is_mandatory": 1 if item.get("is_mandatory") else 0,
#                     "is_completed": 1 if item.get("is_completed") else 0,
#                     "sequence": item.get("sequence") or 0,
#                     "notes": item.get("notes") or "",
#                 })

#         task.save()
#         frappe.db.commit()
#         return {"success": True, "message": "Task updated successfully"}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "update_task error")
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_room_inventory(room_name):
    if not room_name:
        return []

    items = frappe.get_all(
        "Hotel Room Inventory Item",
        filters={"parent": room_name},
        fields=["item", "quantity"],
        order_by="idx asc"
    )

    for item in items:
        item["item_name"] = frappe.db.get_value("Item", item.get("item"), "item_name") or item.get("item")
        item["uom"] = frappe.db.get_value("Item", item.get("item"), "stock_uom") or ""

    return items
    
    
    

@frappe.whitelist()
def update_task(task_name, task_data, inventory_items=None, checklist_items=None):
    """
    Update a housekeeping task with inventory and checklist
    """
    if isinstance(task_data, str):
        task_data = json.loads(task_data)
    if isinstance(inventory_items, str):
        inventory_items = json.loads(inventory_items)
    if isinstance(checklist_items, str):
        checklist_items = json.loads(checklist_items)
 
    try:
        task = frappe.get_doc("Housekeeping Task", task_name)
 
        field_map = {
            "task_type": "task_type",
            "priority": "priority",
            "employee": "employee",
            "status": "status",
            "notes": "notes",
            "checklist_template": "checklist_template",
        }
        for key, field in field_map.items():
            if key in task_data:
                setattr(task, field, task_data[key])
 
        if task_data.get("start_time"):
            task.start_time = task_data["start_time"]
        if task_data.get("end_time"):
            task.end_time = task_data["end_time"]
 
        if inventory_items is not None:
            task.set("room_inventory_changes", [])
            for item in inventory_items:
                if item.get("item"):
                    task.append("room_inventory_changes", {
                        "item": item["item"],
                        "quantity_changed": item.get("quantity_changed") or 1,
                        "change_type": item.get("change_type") or "Added",
                        "reason": item.get("reason") or "",
                    })
 
        if checklist_items is not None:
            task.set("checklist_items", [])
            for item in checklist_items:
                desc = (
                    item.get("item_description")
                    or item.get("item_name")
                    or item.get("description")
                    or ""
                ).strip()
                if not desc:
                    continue
                task.append("checklist_items", {
                    "item_description": desc,
                    "is_mandatory": 1 if item.get("is_mandatory") else 0,
                    "is_completed": 1 if item.get("is_completed") else 0,
                    "sequence": item.get("sequence") or 0,
                    "notes": item.get("notes") or "",
                })
 
        task.flags.ignore_permissions = True
        task.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Task updated successfully"}
 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}
 

 
# @frappe.whitelist()
# def submit_task(task_name):
#     """
#     Submit a housekeeping task
#     """
#     try:
#         task = frappe.get_doc("Housekeeping Task", task_name)
#         task.flags.ignore_permissions = True
#         task.submit()
#         frappe.db.commit()
#         return {"success": True, "message": "Task submitted successfully"}
#     except Exception as e:
#         frappe.db.rollback()
#         return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_task(task_name):
    try:
        task = frappe.get_doc("Housekeeping Task", task_name)

        if task.docstatus == 1:
            return {"success": False, "error": "Task is already submitted"}

        task.status = "Completed"
        task.flags.ignore_permissions = True
        task.submit()

        frappe.db.commit()
        return {
            "success": True,
            "message": "Task submitted successfully",
            "stock_entry": task.stock_entry
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def cancel_task(task_name):
    """
    Cancel a submitted housekeeping task
    """
    try:
        task = frappe.get_doc("Housekeeping Task", task_name)
        task.flags.ignore_permissions = True
        task.cancel()
        frappe.db.commit()
        return {"success": True, "message": "Task cancelled successfully"}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def delete_task(task_name):
    """
    Delete a housekeeping task (draft only)
    """
    try:
        task = frappe.get_doc("Housekeeping Task", task_name)
        if task.docstatus == 1:
            return {"success": False, "error": "Cannot delete submitted task. Cancel it first."}
        task.delete()
        frappe.db.commit()
        return {"success": True, "message": "Task deleted successfully"}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_items():
    """
    Get list of stock items for inventory select dropdown
    """
    return frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["name", "item_name"],
        order_by="item_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_rooms():
    """Rooms list for the new-task room selector"""
    return frappe.get_all(
        "Hotel Room",
        filters={"status": ["!=", "Out of Order"]},
        fields=["name", "room_number", "room_type", "floor", "status"],
        order_by="room_number asc",
        limit_page_length=500
    )
 
 
@frappe.whitelist()
def create_task(task_data, inventory_items=None, checklist_items=None):
    """Create a new Housekeeping Task doc"""
    import json
    if isinstance(task_data, str):
        task_data = json.loads(task_data)
    if isinstance(inventory_items, str):
        inventory_items = json.loads(inventory_items)
    if isinstance(checklist_items, str):
        checklist_items = json.loads(checklist_items)
 
    try:
        task = frappe.new_doc("Housekeeping Task")
        task.room = task_data.get("room")
        task.task_type = task_data.get("task_type", "Checkout Cleaning")
        task.priority = task_data.get("priority", "Medium")
        task.status = task_data.get("status", "Pending")
        task.employee = task_data.get("employee") or None
        task.checklist_template = task_data.get("checklist_template") or None
        task.notes = task_data.get("notes") or ""
        if task_data.get("start_time"):
            task.start_time = task_data["start_time"]
        if task_data.get("end_time"):
            task.end_time = task_data["end_time"]
 
        if inventory_items:
            for item in inventory_items:
                if item.get("item"):
                    task.append("room_inventory_changes", {
                        "item": item["item"],
                        "quantity_changed": item.get("quantity_changed") or 1,
                        "change_type": item.get("change_type") or "Added",
                        "reason": item.get("reason") or "",
                    })
 
        if checklist_items:
            for item in checklist_items:
                desc = (item.get("item_description") or "").strip()
                if desc:
                    task.append("checklist_items", {
                        "item_description": desc,
                        "is_mandatory": 1 if item.get("is_mandatory") else 0,
                        "is_completed": 1 if item.get("is_completed") else 0,
                        "sequence": item.get("sequence") or 0,
                        "notes": item.get("notes") or "",
                    })
 
        task.flags.ignore_permissions = True
        task.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "task_name": task.name}
 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}
 
    """
    Get filtered housekeeping tasks with room details + child table data
    """
    filters = {}
    if task_name:
        filters["name"] = task_name
    if status:
        filters["status"] = status
    if employee:
        filters["employee"] = employee
    if priority:
        filters["priority"] = priority
 
    tasks = frappe.get_all(
        "Housekeeping Task",
        fields=[
            "name", "room", "task_type", "status", "priority", "employee",
            "start_time", "end_time", "notes", "docstatus", "checklist_template"
        ],
        filters=filters,
        order_by="modified desc",
        limit_page_length=100
    )
 
    for task in tasks:
        # Room details
        if task.get("room"):
            room_details = frappe.db.get_value(
                "Hotel Room",
                task["room"],
                ["room_number", "room_type", "floor", "status", "housekeeping_status"],
                as_dict=1
            )
            if room_details:
                task["room_number"] = room_details.get("room_number")
                task["room_type"] = room_details.get("room_type")
                task["floor"] = room_details.get("floor")
                task["room_status"] = room_details.get("status")
                task["housekeeping_status"] = room_details.get("housekeeping_status")
 
        # ── FIX 1: Load inventory child table ──────────────────────────────
        task["room_inventory_changes"] = frappe.get_all(
            "Housekeeping Task Inventory Change",
            filters={"parent": task["name"]},
            fields=["item", "quantity_changed", "change_type", "reason", "uom"],
            order_by="idx asc"
        )
 
        # ── Load checklist child table ──────────────────────────────────────
        task["checklist_items"] = frappe.get_all(
            "Task Checklist Item",
            filters={"parent": task["name"]},
            fields=["item_description", "is_mandatory", "is_completed", "sequence", "notes"],
            order_by="sequence asc, idx asc"
        )
 
    return tasks
