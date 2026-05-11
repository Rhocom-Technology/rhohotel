import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week, now_datetime


@frappe.whitelist()
def get_request_dashboard():
    """
    Stats for the maintenance request list page.
    Status values: Pending, Approved, In Progress, Completed, Cancelled, Rejected
    """
    today = nowdate()
    week_start = get_first_day_of_week(today)

    pending = frappe.db.count("Maintenance Request", {"status": "Pending"})
    completed = frappe.db.count("Maintenance Request", {"status": "Completed"})
    cancelled = frappe.db.count("Maintenance Request", {"status": "Cancelled"})
    total = frappe.db.count("Maintenance Request")

    # Urgent = Critical or High priority, still Pending
    urgent_pending = frappe.db.count(
        "Maintenance Request",
        {"status": "Pending", "priority": ["in", ["Critical", "High"]]}
    )

    # Approved but not yet completed (waiting for task)
    approved_pending = frappe.db.count(
        "Maintenance Request",
        {"approved": "Approved", "status": ["in", ["Pending", "Approved"]]}
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

    fields = [
        "name", "room", "location_type", "location", "issue_type",
        "priority", "status", "reported_by", "reported_at",
        "approved", "approved_by", "approved_on",
        "assigned_technician", "task", "completion_date"
    ]

    if search:
        q = f"%{search}%"
        requests = frappe.db.sql("""
            SELECT name, room, location_type, location, issue_type,
                   priority, status, reported_by, reported_at,
                   approved, approved_by, approved_on,
                   assigned_technician, task, completion_date
            FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR location LIKE %(q)s
                   OR issue_type LIKE %(q)s)
            ORDER BY reported_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"q": q, "limit": page_size, "offset": (page - 1) * page_size}, as_dict=1)

        result = frappe.db.sql(
            """
            SELECT COUNT(name) as cnt
            FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR location LIKE %(q)s
                   OR issue_type LIKE %(q)s)
            """,
            {"q": q},
            as_dict=1
        )
        total = result[0].cnt if result else 0
    else:
        requests = frappe.get_all(
            "Maintenance Request",
            filters=filters,
            fields=fields,
            order_by="reported_at desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size
        )
        total = frappe.db.count("Maintenance Request", filters)

    # Resolve display names
    room_cache = {}
    employee_cache = {}
    tech_cache = {}

    for req in requests:
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

        # Technician name
        if req.get("assigned_technician"):
            if req["assigned_technician"] not in tech_cache:
                tech_cache[req["assigned_technician"]] = frappe.db.get_value("Maintenance Technician", req["assigned_technician"], "technician_name") or req["assigned_technician"]
            req["technician_name"] = tech_cache[req["assigned_technician"]]
        else:
            req["technician_name"] = None

        # Location display
        if req.get("location_type") == "Room":
            req["location_display"] = req.get("room_number") or req.get("room") or "—"
        else:
            req["location_display"] = req.get("location") or "—"

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

    room_number = frappe.db.get_value("Hotel Room", req.room, "room_number") if req.room else None
    reported_by_name = frappe.db.get_value("Employee", req.reported_by, "employee_name") if req.reported_by else None

    technician_name = None
    if req.assigned_technician:
        technician_name = frappe.db.get_value(
            "Maintenance Technician", req.assigned_technician, "technician_name"
        )

    # Linked maintenance task
    linked_task = None
    if req.task:
        linked_task = frappe.db.get_value(
            "Maintenance Task",
            req.task,
            ["name", "status", "assigned_technician"],
            as_dict=1
        )

    task_technician_name = None
    if linked_task and linked_task.get("assigned_technician"):
        task_technician_name = frappe.db.get_value(
            "Maintenance Technician",
            linked_task["assigned_technician"],
            "technician_name"
        )

    return {
        "name": req.name,
        "location_type": req.location_type,
        "room": req.room,
        "room_number": room_number,
        "location": req.location,
        "issue_type": req.issue_type,
        "priority": req.priority,
        "status": req.status,
        "reported_by": req.reported_by,
        "reported_by_name": reported_by_name,
        "reported_at": str(req.reported_at) if req.reported_at else None,
        "completion_date": str(req.completion_date) if req.completion_date else None,
        "issue_description": req.issue_description,
        "approved": req.approved,
        "approved_by": req.approved_by,
        "approved_on": str(req.approved_on) if req.approved_on else None,
        "assigned_technician": req.assigned_technician,
        "technician_name": technician_name,
        "task": req.task,
        "linked_task": linked_task,
        "task_technician_name": task_technician_name,
    }


@frappe.whitelist()
def create_maintenance_request(request_data):
    """Create a new Maintenance Request."""
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        req = frappe.new_doc("Maintenance Request")
        req.location_type = request_data.get("location_type") or "Room"
        req.room = request_data.get("room") if req.location_type == "Room" else None
        req.location = request_data.get("location") if req.location_type == "Other Location" else None
        req.issue_type = request_data.get("issue_type")
        req.priority = request_data.get("priority", "Medium")
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
def approve_request(request_name, assigned_technician=None):
    """
    Approve a maintenance request.
    Sets approved='Approved', assigns technician, then saves.
    The controller on_update handles stamping approval time,
    auto-creating the task, and updating room flags.
    """
    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved == "Approved":
            return {"success": False, "error": "Request is already approved"}

        if assigned_technician:
            req.assigned_technician = assigned_technician

        if not req.assigned_technician:
            return {"success": False, "error": "Please assign a technician before approving"}

        req.approved = "Approved"
        req.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "approve_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def reject_request(request_name):
    """Reject a maintenance request."""
    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved == "Rejected":
            return {"success": False, "error": "Request is already rejected"}

        req.approved = "Rejected"
        req.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "reject_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_maintenance_request(request_name, request_data):
    """
    Update an unapproved Maintenance Request.
    Only allowed when approved = 'Pending'.
    """
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved != "Pending":
            return {"success": False, "error": "Cannot edit an approved or rejected request"}

        if req.status not in ("Pending",):
            return {"success": False, "error": f"Cannot edit a request with status '{req.status}'"}

        # Only update editable fields
        editable = [
            "location_type", "room", "location", "issue_type",
            "priority", "reported_by", "issue_description"
        ]
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
    """Mark a Maintenance Request as Completed."""
    try:
        req = frappe.get_doc("Maintenance Request", request_name)
        if req.status == "Completed":
            return {"success": True}
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
def get_technicians_for_request():
    """Technicians available for assignment dropdown"""
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1, "availability": ["!=", "Unavailable"]},
        fields=["name", "technician_name", "availability", "primary_specialization"],
        order_by="technician_name asc",
        limit_page_length=200
    )
