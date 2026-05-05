import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week, now_datetime


@frappe.whitelist()
def get_request_dashboard():
    """
    Stats for the maintenance request list page.
    Uses actual status values: Pending, Completed, Cancelled
    """
    today = nowdate()
    week_start = get_first_day_of_week(today)

    pending = frappe.db.count("Maintenance Request", {"status": "Pending"})
    completed = frappe.db.count("Maintenance Request", {"status": "Completed"})
    cancelled = frappe.db.count("Maintenance Request", {"status": "Cancelled"})
    total = pending + completed + cancelled

    # Urgent = Critical or High priority, still Pending
    urgent_pending = frappe.db.count(
        "Maintenance Request",
        {"status": "Pending", "priority": ["in", ["Critical", "High"]]}
    )

    # Approved but pending (waiting for action)
    approved_pending = frappe.db.count(
        "Maintenance Request",
        {"status": "Pending", "approved": 1}
    )

    # Resolved this week
    result = frappe.db.sql("""
    SELECT COUNT(name) as cnt FROM `tabMaintenance Request`
    WHERE status = 'Completed'
    AND DATE(completion_date) >= %s
    AND DATE(completion_date) <= %s
    """, (week_start, today), as_dict=1)

    resolved_this_week = result[0].cnt if result and len(result) > 0 else 0

    return {
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled,
        "total": total,
        "urgent_pending": urgent_pending,
        "approved_pending": approved_pending,
        "resolved_this_week": resolved_this_week,
    }


@frappe.whitelist()
def get_request_list(
    search=None,
    filter_priority=None,
    filter_status=None,
    filter_issue_type=None,
    filter_room=None,
    page=1,
    page_size=25
):
    """Paginated maintenance request list"""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = {}
    if filter_priority:
        filters["priority"] = filter_priority
    if filter_status:
        filters["status"] = filter_status
    if filter_issue_type:
        filters["issue_type"] = filter_issue_type
    if filter_room:
        filters["room"] = filter_room

    if search:
        q = f"%{search}%"
        requests = frappe.db.sql("""
            SELECT name, room, asset, issue_type, priority, status,
                   reported_by, reported_at, approved, approval_time,
                   completion_date, asset_repair
            FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR asset LIKE %(q)s)
            ORDER BY reported_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"q": q, "limit": page_size, "offset": (page - 1) * page_size}, as_dict=1)

        result = frappe.db.sql(
            """
            SELECT COUNT(name) as cnt
            FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR asset LIKE %(q)s)
            """,
            {"q": q},
            as_dict=1
        )
        total = result[0].cnt if result else 0
    else:
        requests = frappe.get_all(
            "Maintenance Request",
            filters=filters,
            fields=[
                "name", "room", "asset", "issue_type", "priority", "status",
                "reported_by", "reported_at", "approved", "approval_time",
                "completion_date", "asset_repair"
            ],
            order_by="reported_at desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size
        )
        total = frappe.db.count("Maintenance Request", filters)

    # Resolve display names
    asset_cache = {}
    room_cache = {}
    employee_cache = {}

    for req in requests:
        # Asset name
        if req.get("asset"):
            if req["asset"] not in asset_cache:
                asset_cache[req["asset"]] = frappe.db.get_value("Asset", req["asset"], "asset_name") or req["asset"]
            req["asset_name"] = asset_cache[req["asset"]]
        else:
            req["asset_name"] = None

        # Room number
        if req.get("room"):
            if req["room"] not in room_cache:
                room_cache[req["room"]] = frappe.db.get_value("Hotel Room", req["room"], "room_number") or req["room"]
            req["room_number"] = room_cache[req["room"]]
        else:
            req["room_number"] = None

        # Reporter name
        if req.get("reported_by"):
            if req["reported_by"] not in employee_cache:
                employee_cache[req["reported_by"]] = frappe.db.get_value("Employee", req["reported_by"], "employee_name") or req["reported_by"]
            req["reported_by_name"] = employee_cache[req["reported_by"]]
        else:
            req["reported_by_name"] = None

        # Linked maintenance task (if any)
        req["maintenance_task"] = frappe.db.get_value(
            "Maintenance Task",
            {"maintenance_request": req["name"]},
            "name"
        )

    return {
        "requests": requests,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_maintenance_request(request_name):
    """Full maintenance request detail"""
    if not frappe.db.exists("Maintenance Request", request_name):
        frappe.throw(f"Maintenance Request '{request_name}' not found", frappe.DoesNotExistError)

    req = frappe.get_doc("Maintenance Request", request_name)

    asset_name = frappe.db.get_value("Asset", req.asset, "asset_name") if req.asset else None
    room_number = frappe.db.get_value("Hotel Room", req.room, "room_number") if req.room else None
    reported_by_name = frappe.db.get_value("Employee", req.reported_by, "employee_name") if req.reported_by else None

    # Linked maintenance task
    linked_task = frappe.db.get_value(
        "Maintenance Task",
        {"maintenance_request": request_name},
        ["name", "status", "assigned_technician"],
        as_dict=1
    )

    technician_name = None
    if linked_task and linked_task.get("assigned_technician"):
        technician_name = frappe.db.get_value(
            "Maintenance Technician",
            linked_task["assigned_technician"],
            "technician_name"
        )

    return {
        "name": req.name,
        "room": req.room,
        "room_number": room_number,
        "asset": req.asset,
        "asset_name": asset_name,
        "issue_type": req.issue_type,
        "priority": req.priority,
        "request_type": req.request_type,
        "status": req.status,
        "reported_by": req.reported_by,
        "reported_by_name": reported_by_name,
        "reported_at": str(req.reported_at) if req.reported_at else None,
        "completion_date": str(req.completion_date) if req.completion_date else None,
        "issue_description": req.issue_description,
        "approved": req.approved,
        "approval_time": str(req.approval_time) if req.approval_time else None,
        "asset_repair": req.asset_repair,
        "linked_task": linked_task,
        "technician_name": technician_name,
    }


@frappe.whitelist()
def create_maintenance_request(request_data):
    """
    Create a new Maintenance Request.
    request_type must be 'Repair' or 'Maintenance':
      - Repair     → Asset Repair is auto-created by the controller on approval
      - Maintenance → Convert to Task button appears after approval
    """
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        req = frappe.new_doc("Maintenance Request")
        req.room = request_data.get("room")
        req.asset = request_data.get("asset")
        req.issue_type = request_data.get("issue_type")
        req.priority = request_data.get("priority", "Medium")
        req.request_type = request_data.get("request_type") or "Repair"
        req.reported_by = request_data.get("reported_by")
        req.reported_at = request_data.get("reported_at") or now_datetime()
        req.issue_description = request_data.get("issue_description") or ""
        req.status = "Pending"

        req.insert()
        frappe.db.commit()
        return {"success": True, "request_name": req.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_maintenance_request error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def approve_request(request_name):
    """Approve a maintenance request"""
    try:
        req = frappe.get_doc("Maintenance Request", request_name)
        req.approve_request()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "approve_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def convert_to_task(request_name, task_data=None):
    """
    Convert a Maintenance Request into a Maintenance Task.
    Strictly maps only fields that exist on the Maintenance Task doctype.
    """
    if isinstance(task_data, str):
        task_data = json.loads(task_data) if task_data else {}
    task_data = task_data or {}

    try:
        if not frappe.db.exists("Maintenance Request", request_name):
            return {"success": False, "error": "Request not found"}

        req = frappe.get_doc("Maintenance Request", request_name)

        if req.request_type == "Repair":
            return {"success": False, "error": "This is a Repair request — it creates an Asset Repair, not a Maintenance Task. Change request type to 'Maintenance' to convert to a task."}

        existing_task = frappe.db.get_value("Maintenance Task", {"maintenance_request": request_name}, "name")
        if existing_task:
            return {"success": False, "error": f"Already converted to task {existing_task}"}

        task = frappe.new_doc("Maintenance Task")
        task.maintenance_request = request_name
        task.asset = req.asset
        task.task_type = task_data.get("task_type") or "Corrective"
        task.priority = _map_priority(req.priority)
        task.status = "Open"
        task.location = task_data.get("location") or ""
        task.task_description = task_data.get("task_description") or ""
        task.inspection_required = 1

        # assigned_technician is a Link to Maintenance Technician
        tech = task_data.get("assigned_technician")
        if tech and frappe.db.exists("Maintenance Technician", tech):
            task.assigned_technician = tech

        # supervisor is a Link to Employee
        sup = task_data.get("supervisor")
        if sup and frappe.db.exists("Employee", sup):
            task.supervisor = sup

        # Some versions of the controller reference assigned_to — patch it
        # so the hook doesn't crash even if the field doesn't exist on the doctype
        if not hasattr(task, "assigned_to"):
            task.assigned_to = None

        task.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "task_name": task.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "convert_to_task error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


def _map_priority(mr_priority):
    """Map Maintenance Request priority to Maintenance Task priority"""
    return {
        "Critical": "High",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low",
    }.get(mr_priority, "Medium")


@frappe.whitelist()
def update_maintenance_request(request_name, request_data):
    """
    Update an unapproved Maintenance Request.
    Only allowed when approved = 0.
    Follows doctype fields strictly:
      room, asset, issue_type, priority, request_type,
      reported_by, reported_at, issue_description
    """
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved:
            return {"success": False, "error": "Cannot edit an approved request"}

        if req.status != "Pending":
            return {"success": False, "error": f"Cannot edit a request with status '{req.status}'"}

        # Only update editable fields
        editable = ["room", "asset", "issue_type", "priority", "request_type", "reported_by", "issue_description"]
        for field in editable:
            if field in request_data and request_data[field] is not None:
                setattr(req, field, request_data[field])

        if request_data.get("reported_at"):
            req.reported_at = request_data["reported_at"]

        req.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_maintenance_request error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def complete_maintenance_request(request_name):
    """
    Mark a Maintenance Request as Completed.
    Called when the linked Asset Repair or Maintenance Task is done,
    so the duplicate-pending check is cleared for new requests on the same asset/room.
    """
    try:
        req = frappe.get_doc("Maintenance Request", request_name)
        if req.status == "Completed":
            return {"success": True}  # already done
        req.db_set("status", "Completed")
        req.db_set("completion_date", now_datetime())
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "complete_maintenance_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_rooms_for_request():
    """Hotel rooms for the room dropdown"""
    return frappe.get_all(
        "Hotel Room",
        fields=["name", "room_number", "status"],
        order_by="room_number asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_employees_for_request():
    """Active employees for the reported_by dropdown"""
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "department"],
        order_by="employee_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_assets_for_request():
    """Assets for the request form dropdown"""
    return frappe.get_all(
        "Asset",
        filters={"docstatus": 1, "status": ["not in", ["Scrapped", "Sold"]]},
        fields=["name", "asset_name", "location", "asset_category"],
        order_by="asset_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_asset_repair(asset_repair_name):
    """Get Asset Repair doc details for inline display"""
    if not frappe.db.exists("Asset Repair", asset_repair_name):
        return None
    ar = frappe.get_doc("Asset Repair", asset_repair_name)
    return {
        "name": ar.name,
        "asset": ar.asset,
        "asset_name": frappe.db.get_value("Asset", ar.asset, "asset_name") if ar.asset else None,
        "failure_date": str(ar.failure_date) if ar.failure_date else None,
        "repair_status": ar.repair_status,
        "description": ar.description,
        "repair_cost": ar.repair_cost if hasattr(ar, "repair_cost") else None,
        "docstatus": ar.docstatus,
    }


@frappe.whitelist()
def get_room_assets(room_name):
    """
    Get assets linked to a room via Hotel Room Amenity items.
    Returns assets whose item_code matches items in the room's amenities child table.
    Falls back to all assets if no amenities found.
    """
    if not room_name or not frappe.db.exists("Hotel Room", room_name):
        return []

    room = frappe.get_doc("Hotel Room", room_name)
    amenities = room.get("amenities", [])
    item_codes = [a.item for a in amenities if a.item]

    if not item_codes:
        # No amenities — return all active assets so the form is still usable
        return frappe.get_all(
            "Asset",
            filters={"docstatus": 1, "status": ["not in", ["Scrapped", "Sold"]]},
            fields=["name", "asset_name", "item_code", "location", "asset_category"],
            order_by="asset_name asc",
            limit_page_length=200
        )

    return frappe.get_all(
        "Asset",
        filters={
            "item_code": ["in", item_codes],
            "docstatus": 1,
            "status": ["not in", ["Scrapped", "Sold"]]
        },
        fields=["name", "asset_name", "item_code", "location", "asset_category"],
        order_by="asset_name asc"
    )


@frappe.whitelist()
def save_asset_repair(asset_repair_name, repair_data):
    """
    Save editable fields on an Asset Repair doc (draft only).
    Editable fields from doctype: repair_status, completion_date,
    description, actions_performed, repair_cost, capitalize_repair_cost.
    """
    if isinstance(repair_data, str):
        repair_data = json.loads(repair_data)

    try:
        if not frappe.db.exists("Asset Repair", asset_repair_name):
            return {"success": False, "error": "Asset Repair not found"}

        ar = frappe.get_doc("Asset Repair", asset_repair_name)

        if ar.docstatus == 1:
            return {"success": False, "error": "Asset Repair is already submitted"}
        if ar.docstatus == 2:
            return {"success": False, "error": "Asset Repair is cancelled"}

        if "repair_status" in repair_data:
            ar.repair_status = repair_data["repair_status"]
        if "completion_date" in repair_data and repair_data["completion_date"]:
            ar.completion_date = repair_data["completion_date"]
        if "description" in repair_data:
            ar.description = repair_data["description"]
        if "actions_performed" in repair_data:
            ar.actions_performed = repair_data["actions_performed"]
        if "repair_cost" in repair_data:
            ar.repair_cost = repair_data["repair_cost"] or 0
        if "capitalize_repair_cost" in repair_data:
            ar.capitalize_repair_cost = 1 if repair_data["capitalize_repair_cost"] else 0

        ar.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "save_asset_repair error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_asset_repair(asset_repair_name):
    """
    Submit an Asset Repair doc.
    The controller's before_submit checks repair_status != 'Pending',
    so status must be 'Completed' before calling this.
    """
    try:
        if not frappe.db.exists("Asset Repair", asset_repair_name):
            return {"success": False, "error": "Asset Repair not found"}

        ar = frappe.get_doc("Asset Repair", asset_repair_name)

        if ar.docstatus == 1:
            return {"success": False, "error": "Already submitted"}
        if ar.repair_status == "Pending":
            return {"success": False, "error": "Set Repair Status to 'Completed' before submitting"}
        if not ar.completion_date:
            return {"success": False, "error": "Completion Date is required before submitting"}

        ar.submit()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_asset_repair error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}