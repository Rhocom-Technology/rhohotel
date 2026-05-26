import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week, now_datetime


@frappe.whitelist()
def get_request_dashboard():
    today = nowdate()
    week_start = get_first_day_of_week(today)

    pending          = frappe.db.count("Maintenance Request", {"status": "Pending"})
    completed        = frappe.db.count("Maintenance Request", {"status": "Completed"})
    cancelled        = frappe.db.count("Maintenance Request", {"status": "Cancelled"})
    total            = frappe.db.count("Maintenance Request")
    urgent_pending   = frappe.db.count("Maintenance Request", {"status": "Pending", "priority": ["in", ["Critical", "High"]]})
    approved_pending = frappe.db.count("Maintenance Request", {"approved": "Approved", "status": ["in", ["Pending", "Approved"]]})

    result = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMaintenance Request`
        WHERE status = 'Completed'
        AND DATE(completion_date) >= %s
        AND DATE(completion_date) <= %s
    """, (week_start, today), as_dict=1)
    resolved_this_week = result[0].cnt if result else 0

    return {
        "pending":           pending,
        "completed":         completed,
        "cancelled":         cancelled,
        "total":             total,
        "urgent_pending":    urgent_pending,
        "approved_pending":  approved_pending,
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
    if filter_priority:  filters["priority"]   = filter_priority
    if filter_status:    filters["status"]      = filter_status
    if filter_issue_type: filters["issue_type"] = filter_issue_type
    if filter_room:      filters["room"]        = filter_room

    fields = [
        "name", "room", "location_type", "location", "asset_location", "asset",
        "issue_type", "priority", "status",
        "reported_by", "requesting_department", "reported_at",
        "witness_employee", "witness_department",
        "approved", "approved_by", "approved_on",
        "assigned_technician", "task", "completion_date"
    ]

    if search:
        q = f"%{search}%"
        requests = frappe.db.sql("""
            SELECT name, room, location_type, location, asset_location, asset,
                   issue_type, priority, status,
                   reported_by, requesting_department, reported_at,
                   witness_employee, witness_department,
                   approved, approved_by, approved_on,
                   assigned_technician, task, completion_date
            FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR location LIKE %(q)s
                   OR issue_type LIKE %(q)s OR asset_location LIKE %(q)s)
            ORDER BY reported_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"q": q, "limit": page_size, "offset": (page - 1) * page_size}, as_dict=1)

        result = frappe.db.sql("""
            SELECT COUNT(name) as cnt FROM `tabMaintenance Request`
            WHERE (name LIKE %(q)s OR room LIKE %(q)s OR location LIKE %(q)s
                   OR issue_type LIKE %(q)s OR asset_location LIKE %(q)s)
        """, {"q": q}, as_dict=1)
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
    room_cache     = {}
    employee_cache = {}
    tech_cache     = {}

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

        # Witness name
        if req.get("witness_employee"):
            if req["witness_employee"] not in employee_cache:
                employee_cache[req["witness_employee"]] = frappe.db.get_value("Employee", req["witness_employee"], "employee_name") or req["witness_employee"]
            req["witness_employee_name"] = employee_cache[req["witness_employee"]]
        else:
            req["witness_employee_name"] = None

        # Technician name
        if req.get("assigned_technician"):
            if req["assigned_technician"] not in tech_cache:
                tech_cache[req["assigned_technician"]] = frappe.db.get_value("Maintenance Technician", req["assigned_technician"], "technician_name") or req["assigned_technician"]
            req["technician_name"] = tech_cache[req["assigned_technician"]]
        else:
            req["technician_name"] = None

        # Location display
        lt = req.get("location_type")
        if lt == "Room":
            req["location_display"] = req.get("room_number") or req.get("room") or "—"
        elif lt == "Asset Location":
            req["location_display"] = req.get("asset") or req.get("asset_location") or "—"
        else:
            req["location_display"] = req.get("location") or "—"

    return {
        "requests":    requests,
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_maintenance_request(request_name):
    """Full maintenance request detail"""
    if not frappe.db.exists("Maintenance Request", request_name):
        frappe.throw(f"Maintenance Request '{request_name}' not found", frappe.DoesNotExistError)

    req = frappe.get_doc("Maintenance Request", request_name)

    room_number          = frappe.db.get_value("Hotel Room", req.room, "room_number") if req.room else None
    reported_by_name     = frappe.db.get_value("Employee", req.reported_by, "employee_name") if req.reported_by else None
    witness_employee_name = frappe.db.get_value("Employee", req.witness_employee, "employee_name") if req.witness_employee else None

    technician_name = None
    if req.assigned_technician:
        technician_name = frappe.db.get_value("Maintenance Technician", req.assigned_technician, "technician_name")

    linked_task = None
    if req.task:
        linked_task = frappe.db.get_value(
            "Maintenance Task", req.task,
            ["name", "status", "assigned_technician"], as_dict=1
        )

    task_technician_name = None
    if linked_task and linked_task.get("assigned_technician"):
        task_technician_name = frappe.db.get_value(
            "Maintenance Technician", linked_task["assigned_technician"], "technician_name"
        )

    return {
        "name":                  req.name,
        "location_type":         req.location_type,
        "room":                  req.room,
        "room_number":           room_number,
        "asset_location":        req.asset_location or "",
        "location":              req.location or "",
        "issue_type":            req.issue_type,
        "priority":              req.priority,
        "status":                req.status,

        "reported_by":           req.reported_by,
        "reported_by_name":      reported_by_name,
        "reported_at":           str(req.reported_at) if req.reported_at else None,
        "requesting_department": req.requesting_department or "",

        "witness_employee":      req.witness_employee or "",
        "witness_employee_name": witness_employee_name,
        "witness_department":    req.witness_department or "",

        "approved":              req.approved,
        "approved_by":           req.approved_by or "",
        "approved_on":           str(req.approved_on) if req.approved_on else None,

        "assigned_technician":   req.assigned_technician or "",
        "technician_name":       technician_name,

        "task":                  req.task or "",
        "linked_task":           linked_task,
        "task_technician_name":  task_technician_name,
        "completion_date":       str(req.completion_date) if req.completion_date else None,
        "issue_description":     req.issue_description or "",
        "asset":                 req.asset or "",
    }


@frappe.whitelist()
def create_maintenance_request(request_data):
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        location_type    = request_data.get("location_type") or "Room"
        room             = request_data.get("room")             if location_type == "Room"             else None
        asset_location   = request_data.get("asset_location")   if location_type == "Asset Location"   else None
        location         = request_data.get("location")         if location_type == "Other Location"   else None
        issue_type       = request_data.get("issue_type")
        witness_employee = request_data.get("witness_employee") or None
        asset            = request_data.get("asset") or None

        # Duplicate check
        # filters = {
        #     "issue_type":    issue_type,
        #     "location_type": location_type,
        #     "status":        ["in", ["Pending", "Approved", "In Progress"]],
        # }
        # if location_type == "Room" and room:
        #     filters["room"] = room
        # elif location_type == "Asset Location" and asset_location:
        #     filters["asset_location"] = asset_location
        # elif location_type == "Other Location" and location:
        #     filters["location"] = location

        # existing = frappe.db.get_value("Maintenance Request", filters, "name")
        # if existing:
        #     return {"success": True, "request_name": existing, "already_existed": True}

        req = frappe.new_doc("Maintenance Request")
        req.location_type    = location_type
        req.room             = room
        req.asset_location   = asset_location
        req.location         = location
        req.issue_type       = issue_type
        req.priority         = request_data.get("priority", "Medium")
        req.reported_by      = request_data.get("reported_by")
        req.witness_employee = witness_employee
        req.reported_at      = request_data.get("reported_at") or now_datetime()
        req.issue_description = request_data.get("issue_description") or ""
        req.asset            = asset
        req.status           = "Pending"

        # Auto-resolve departments from employee records
        if req.reported_by:
            req.requesting_department = frappe.db.get_value(
                "Employee", req.reported_by, "department"
            ) or None
        if req.witness_employee:
            req.witness_department = frappe.db.get_value(
                "Employee", req.witness_employee, "department"
            ) or None

        req.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "request_name": req.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_maintenance_request error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def approve_request(request_name, assigned_technician=None, witness_employee=None):
    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved == "Approved":
            return {"success": False, "error": "Request is already approved"}

        if assigned_technician:
            req.assigned_technician = assigned_technician

        if witness_employee:
            req.witness_employee = witness_employee

        if not req.assigned_technician:
            return {"success": False, "error": "Please assign a technician before approving"}

        if not req.witness_employee:
            return {"success": False, "error": "Please select a Supervisor / Witness before approving"}

        req.approved = "Approved"
        req.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "approve_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def reject_request(request_name):
    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved == "Rejected":
            return {"success": False, "error": "Request is already rejected"}

        req.approved = "Rejected"
        req.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "reject_request error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_maintenance_request(request_name, request_data):
    if isinstance(request_data, str):
        request_data = json.loads(request_data)

    try:
        req = frappe.get_doc("Maintenance Request", request_name)

        if req.approved != "Pending":
            return {"success": False, "error": "Cannot edit an approved or rejected request"}

        if req.status not in ("Pending",):
            return {"success": False, "error": f"Cannot edit a request with status '{req.status}'"}

        editable = [
            "location_type", "room", "asset_location", "asset", "location",
            "issue_type", "priority", "reported_by",
            "witness_employee", "issue_description"
        ]
        for field in editable:
            if field in request_data and request_data[field] is not None:
                setattr(req, field, request_data[field])

        if request_data.get("reported_at"):
            req.reported_at = request_data["reported_at"]

        # Re-resolve departments whenever employee fields change
        if req.reported_by:
            req.requesting_department = frappe.db.get_value(
                "Employee", req.reported_by, "department"
            ) or None
        if req.witness_employee:
            req.witness_department = frappe.db.get_value(
                "Employee", req.witness_employee, "department"
            ) or None

        req.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_maintenance_request error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def complete_maintenance_request(request_name):
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
    return frappe.get_all(
        "Hotel Room",
        fields=["name", "room_number", "status"],
        order_by="room_number asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_asset_locations_for_request():
    """ERPNext Location records for the Asset Location dropdown"""
    return frappe.get_all(
        "Location",
        fields=["name", "location_name"],
        order_by="location_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_employees_for_request():
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "department"],
        order_by="employee_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_technicians_for_request():
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1, "availability": ["!=", "Unavailable"]},
        fields=["name", "technician_name", "availability", "primary_specialization"],
        order_by="technician_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_assets_for_request():
    """Active ERPNext assets for the asset dropdown"""
    return frappe.get_all(
        "Asset",
        filters={"docstatus": 1},
        fields=["name", "asset_name", "asset_category", "location"],
        order_by="asset_name asc",
        limit_page_length=500
    )