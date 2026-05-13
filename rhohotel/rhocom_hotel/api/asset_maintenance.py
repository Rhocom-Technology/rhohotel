import frappe
import json


@frappe.whitelist()
def get_maintenance_dashboard():
    """Stats for the asset maintenance list page."""
    total = frappe.db.count("Asset Maintenance", {"docstatus": ["!=", 2]})
    pending = frappe.db.count("Asset Maintenance", {"rh_approved": "Pending", "docstatus": 0})
    approved = frappe.db.count("Asset Maintenance", {"rh_approved": "Approved", "docstatus": ["!=", 2]})
    rejected = frappe.db.count("Asset Maintenance", {"rh_approved": "Rejected"})

    # Task-level stats
    overdue_tasks = frappe.db.count("Asset Maintenance Task", {"maintenance_status": "Overdue"})
    planned_tasks = frappe.db.count("Asset Maintenance Task", {"maintenance_status": "Planned"})

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "overdue_tasks": overdue_tasks,
        "planned_tasks": planned_tasks,
    }


@frappe.whitelist()
def get_maintenance_list(
    search=None,
    filter_status=None,
    page=1,
    page_size=25
):
    """Paginated asset maintenance list."""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = {"docstatus": ["!=", 2]}
    if filter_status:
        filters["rh_approved"] = filter_status

    if search:
        q = f"%{search}%"
        repairs = frappe.db.sql("""
            SELECT name, asset_name, company, asset_category, item_code, item_name,
                   maintenance_team, maintenance_manager_name, docstatus, owner, creation, modified,
                   rh_reported_by, rh_priority, rh_issue_type, rh_approved,
                   rh_approved_by, rh_approved_on, rh_assigned_technician,
                   rh_location_type, rh_hotel_room, rh_asset_location
            FROM `tabAsset Maintenance`
            WHERE (name LIKE %(q)s OR asset_name LIKE %(q)s OR asset_category LIKE %(q)s
                   OR item_name LIKE %(q)s)
            AND docstatus != 2
            {status_filter}
            ORDER BY creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """.format(
            status_filter="AND rh_approved = %(status)s" if filter_status else ""
        ), {
            "q": q,
            "limit": page_size,
            "offset": (page - 1) * page_size,
            "status": filter_status,
        }, as_dict=1)

        count_sql = """
            SELECT COUNT(name) as cnt
            FROM `tabAsset Maintenance`
            WHERE (name LIKE %(q)s OR asset_name LIKE %(q)s OR asset_category LIKE %(q)s
                   OR item_name LIKE %(q)s)
            AND docstatus != 2
            {status_filter}
        """.format(
            status_filter="AND rh_approved = %(status)s" if filter_status else ""
        )
        result = frappe.db.sql(count_sql, {"q": q, "status": filter_status}, as_dict=1)
        total = result[0].cnt if result else 0
    else:
        repairs = frappe.get_all(
            "Asset Maintenance",
            filters=filters,
            fields=[
                "name", "asset_name", "company", "asset_category", "item_code", "item_name",
                "maintenance_team", "maintenance_manager_name", "docstatus", "owner", "creation", "modified",
                "rh_reported_by", "rh_priority", "rh_issue_type", "rh_approved",
                "rh_approved_by", "rh_approved_on", "rh_assigned_technician",
                "rh_location_type", "rh_hotel_room", "rh_asset_location"
            ],
            order_by="creation desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size
        )
        total = frappe.db.count("Asset Maintenance", filters)

    for r in repairs:
        r["created_by"] = frappe.db.get_value("User", r.get("owner"), "full_name") or r.get("owner")

    return {
        "records": repairs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_asset_maintenance(name):
    """Full asset maintenance detail."""
    if not frappe.db.exists("Asset Maintenance", name):
        frappe.throw(f"Asset Maintenance '{name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset Maintenance", name)

    # Resolve names
    reported_by_name = None
    if doc.get("rh_reported_by"):
        reported_by_name = frappe.db.get_value("Employee", doc.rh_reported_by, "employee_name")

    technician_name = None
    if doc.get("rh_assigned_technician"):
        technician_name = frappe.db.get_value("Maintenance Technician", doc.rh_assigned_technician, "technician_name")

    approved_by_name = None
    if doc.get("rh_approved_by"):
        approved_by_name = frappe.db.get_value("User", doc.rh_approved_by, "full_name")

    hotel_room_number = None
    if doc.get("rh_hotel_room"):
        hotel_room_number = frappe.db.get_value("Hotel Room", doc.rh_hotel_room, "room_number")

    # Build tasks
    tasks = []
    for task in doc.get("asset_maintenance_tasks") or []:
        tasks.append({
            "name": task.name,
            "maintenance_task": task.maintenance_task,
            "maintenance_type": task.maintenance_type,
            "maintenance_status": task.maintenance_status,
            "start_date": str(task.start_date) if task.start_date else None,
            "end_date": str(task.end_date) if task.end_date else None,
            "periodicity": task.periodicity,
            "certificate_required": task.certificate_required,
            "assign_to": task.assign_to,
            "assign_to_name": task.assign_to_name,
            "next_due_date": str(task.next_due_date) if task.next_due_date else None,
            "last_completion_date": str(task.last_completion_date) if task.last_completion_date else None,
            "description": task.description,
        })

    return {
        "name": doc.name,
        "asset_name": doc.asset_name,
        "asset_category": doc.asset_category,
        "company": doc.company,
        "item_code": doc.item_code,
        "item_name": doc.item_name,
        "maintenance_team": doc.maintenance_team,
        "maintenance_manager": doc.maintenance_manager,
        "maintenance_manager_name": doc.maintenance_manager_name,
        "asset_maintenance_tasks": tasks,
        "docstatus": doc.docstatus,
        "owner": doc.owner,
        "created_by": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
        "creation": doc.creation,
        "modified": doc.modified,
        # Custom rh_ fields
        "rh_location_type": doc.get("rh_location_type"),
        "rh_hotel_room": doc.get("rh_hotel_room"),
        "rh_hotel_room_number": hotel_room_number,
        "rh_asset_location": doc.get("rh_asset_location"),
        "rh_reported_by": doc.get("rh_reported_by"),
        "rh_reported_by_name": reported_by_name,
        "rh_priority": doc.get("rh_priority"),
        "rh_assigned_technician": doc.get("rh_assigned_technician"),
        "rh_technician_name": technician_name,
        "rh_issue_type": doc.get("rh_issue_type"),
        "rh_approved": doc.get("rh_approved"),
        "rh_approved_by": doc.get("rh_approved_by"),
        "rh_approved_by_name": approved_by_name,
        "rh_approved_on": doc.get("rh_approved_on"),
    }


@frappe.whitelist()
def create_asset_maintenance(
    asset_name,
    company,
    maintenance_team=None,
    tasks=None,
    rh_location_type=None,
    rh_hotel_room=None,
    rh_asset_location=None,
    rh_reported_by=None,
    rh_priority=None,
    rh_assigned_technician=None,
    rh_issue_type=None
):
    """Create a new Asset Maintenance (saved as draft, pending approval)."""
    doc = frappe.new_doc("Asset Maintenance")
    doc.asset_name = asset_name
    doc.company = company
    if maintenance_team:
        doc.maintenance_team = maintenance_team

    # Custom rh_ fields
    if rh_location_type:
        doc.rh_location_type = rh_location_type
    if rh_hotel_room:
        doc.rh_hotel_room = rh_hotel_room
    if rh_asset_location:
        doc.rh_asset_location = rh_asset_location
    if rh_reported_by:
        doc.rh_reported_by = rh_reported_by
    if rh_priority:
        doc.rh_priority = rh_priority
    if rh_assigned_technician:
        doc.rh_assigned_technician = rh_assigned_technician
    if rh_issue_type:
        doc.rh_issue_type = rh_issue_type

    # Add tasks
    if tasks:
        if isinstance(tasks, str):
            tasks = json.loads(tasks)
        for t in tasks:
            doc.append("asset_maintenance_tasks", {
                "maintenance_task": t.get("maintenance_task"),
                "maintenance_type": t.get("maintenance_type", "Preventive Maintenance"),
                "maintenance_status": t.get("maintenance_status", "Planned"),
                "start_date": t.get("start_date") or frappe.utils.today(),
                "periodicity": t.get("periodicity"),
                "description": t.get("description"),
            })

    doc.insert()

    return {
        "name": doc.name,
        "message": "Asset Maintenance created successfully. Pending approval.",
    }


@frappe.whitelist()
def update_asset_maintenance(
    name,
    asset_name=None,
    company=None,
    maintenance_team=None,
    tasks=None,
    rh_location_type=None,
    rh_hotel_room=None,
    rh_asset_location=None,
    rh_reported_by=None,
    rh_priority=None,
    rh_assigned_technician=None,
    rh_issue_type=None
):
    """Update an existing draft Asset Maintenance."""
    if not frappe.db.exists("Asset Maintenance", name):
        frappe.throw(f"Asset Maintenance '{name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset Maintenance", name)

    if doc.docstatus != 0:
        frappe.throw("Only draft records can be edited.")

    if asset_name is not None:
        doc.asset_name = asset_name
    if company is not None:
        doc.company = company
    if maintenance_team is not None:
        doc.maintenance_team = maintenance_team

    # Custom rh_ fields
    if rh_location_type is not None:
        doc.rh_location_type = rh_location_type
    if rh_hotel_room is not None:
        doc.rh_hotel_room = rh_hotel_room
    if rh_asset_location is not None:
        doc.rh_asset_location = rh_asset_location
    if rh_reported_by is not None:
        doc.rh_reported_by = rh_reported_by
    if rh_priority is not None:
        doc.rh_priority = rh_priority
    if rh_assigned_technician is not None:
        doc.rh_assigned_technician = rh_assigned_technician
    if rh_issue_type is not None:
        doc.rh_issue_type = rh_issue_type

    # Replace tasks
    if tasks is not None:
        if isinstance(tasks, str):
            tasks = json.loads(tasks)
        doc.asset_maintenance_tasks = []
        for t in tasks:
            doc.append("asset_maintenance_tasks", {
                "maintenance_task": t.get("maintenance_task"),
                "maintenance_type": t.get("maintenance_type", "Preventive Maintenance"),
                "maintenance_status": t.get("maintenance_status", "Planned"),
                "start_date": t.get("start_date") or frappe.utils.today(),
                "periodicity": t.get("periodicity"),
                "description": t.get("description"),
            })

    doc.save()

    return {
        "name": doc.name,
        "message": "Asset Maintenance updated successfully.",
    }


@frappe.whitelist()
def approve_asset_maintenance(name):
    """Approve an asset maintenance. Only Admin/Hotel Manager can do this."""
    if not frappe.db.exists("Asset Maintenance", name):
        frappe.throw(f"Asset Maintenance '{name}' not found", frappe.DoesNotExistError)

    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = ["Administrator", "Hotel Manager", "System Manager"]
    if not any(role in user_roles for role in allowed_roles):
        frappe.throw("Only Admin or Hotel Manager can approve.", frappe.PermissionError)

    doc = frappe.get_doc("Asset Maintenance", name)
    if doc.docstatus != 0:
        frappe.throw("This record has already been processed.")

    doc.rh_approved = "Approved"
    doc.save()

    return {
        "name": doc.name,
        "rh_approved": doc.rh_approved,
        "message": "Asset Maintenance approved successfully.",
    }


@frappe.whitelist()
def reject_asset_maintenance(name, reason=None):
    """Reject an asset maintenance. Only Admin/Hotel Manager can do this."""
    if not frappe.db.exists("Asset Maintenance", name):
        frappe.throw(f"Asset Maintenance '{name}' not found", frappe.DoesNotExistError)

    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = ["Administrator", "Hotel Manager", "System Manager"]
    if not any(role in user_roles for role in allowed_roles):
        frappe.throw("Only Admin or Hotel Manager can reject.", frappe.PermissionError)

    doc = frappe.get_doc("Asset Maintenance", name)

    if doc.docstatus == 2:
        frappe.throw("This record has already been rejected.")

    doc.rh_approved = "Rejected"
    doc.save()

    if reason:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Asset Maintenance",
            "reference_name": name,
            "content": f"Rejected: {reason}",
        }).insert(ignore_permissions=True)

    return {
        "name": doc.name,
        "rh_approved": doc.rh_approved,
        "message": "Asset Maintenance rejected.",
    }


# ── Dropdown helpers ──────────────────────────────────────────────────────────

@frappe.whitelist()
def get_companies():
    """Get list of companies for dropdown."""
    return frappe.get_all(
        "Company",
        filters={"name": ["not like", "_Test%"]},
        fields=["name", "company_name"],
        order_by="name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_assets_for_maintenance(company=None):
    """Assets that don't already have an active maintenance record."""
    existing = frappe.get_all(
        "Asset Maintenance",
        filters={"docstatus": ["!=", 2]},
        pluck="asset_name"
    )
    filters = [
        ["docstatus", "=", 1],
        ["name", "not like", "_Test%"],
    ]
    if existing:
        filters.append(["name", "not in", existing])
    if company:
        filters.append(["company", "=", company])
    return frappe.get_all(
        "Asset",
        filters=filters,
        fields=["name", "asset_name", "company", "asset_category"],
        order_by="asset_name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_maintenance_teams(company=None):
    """Get list of Asset Maintenance Teams."""
    filters = {"name": ["not like", "_Test%"]}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Asset Maintenance Team",
        filters=filters,
        fields=["name", "maintenance_manager_name"],
        order_by="name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_users_for_assignment():
    """Get list of users for task assignment."""
    return frappe.get_all(
        "User",
        filters={"enabled": 1, "name": ["not like", "_Test%"], "user_type": "System User"},
        fields=["name", "full_name"],
        order_by="full_name asc",
        limit_page_length=0
    )
