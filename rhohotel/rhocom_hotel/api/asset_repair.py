import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week


RH_FIELDS = [
    "rh_reported_by",
    "rh_priority",
    "rh_issue_type",
    "rh_approved",
    "rh_approved_by",
    "rh_approved_on",
    "rh_assigned_technician",
    "rh_location_type",
    "rh_hotel_room",
    "rh_asset_location",
]


def _has_column(doctype, fieldname):
    return frappe.db.has_column(doctype, fieldname)


def _existing_fields(doctype, fields):
    return [field for field in fields if field in ("name", "owner", "creation", "modified", "docstatus") or _has_column(doctype, field)]


def _fallback_approval(row):
    if row.get("repair_status") == "Cancelled":
        return "Rejected"
    if int(row.get("docstatus") or 0) == 1:
        return "Approved"
    return "Pending"


def _apply_rh_defaults(records):
    for row in records:
        for field in RH_FIELDS:
            row.setdefault(field, None)
        row["rh_approved"] = row.get("rh_approved") or _fallback_approval(row)
        row["rh_priority"] = row.get("rh_priority") or "Medium"
    return records


def _build_filters(filter_status=None, filter_asset=None):
    filters = {}
    if filter_asset:
        filters["asset"] = filter_asset

    if filter_status:
        if _has_column("Asset Repair", "repair_status") and filter_status in ("Pending", "Completed", "Cancelled"):
            filters["repair_status"] = filter_status
        elif _has_column("Asset Repair", "rh_approved"):
            filters["rh_approved"] = filter_status
        elif filter_status == "Approved":
            filters["docstatus"] = 1
        elif filter_status == "Rejected":
            filters["repair_status"] = "Cancelled"
        else:
            filters["docstatus"] = 0
    return filters


@frappe.whitelist()
def get_repair_dashboard():
    """Stats for the asset repair list page."""
    pending = frappe.db.count("Asset Repair", {"repair_status": "Pending"})
    completed = frappe.db.count("Asset Repair", {"repair_status": "Completed"})
    cancelled = frappe.db.count("Asset Repair", {"repair_status": "Cancelled"})
    total = pending + completed + cancelled

    if _has_column("Asset Repair", "rh_approved"):
        approved = frappe.db.count("Asset Repair", {"rh_approved": "Approved"})
        rejected = frappe.db.count("Asset Repair", {"rh_approved": "Rejected"})
    else:
        approved = frappe.db.count("Asset Repair", {"docstatus": 1})
        rejected = cancelled

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "completed": completed,
        "rejected": rejected,
    }


@frappe.whitelist()
def get_repair_list(
    search=None,
    filter_status=None,
    filter_asset=None,
    page=1,
    page_size=25
):
    """Paginated asset repair list."""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = _build_filters(filter_status, filter_asset)
    fields = _existing_fields("Asset Repair", [
        "name", "asset", "asset_name", "repair_status", "failure_date",
        "completion_date", "description", "repair_cost", "total_repair_cost",
        "docstatus", "owner", "creation",
        *RH_FIELDS,
    ])
    search_fields = _existing_fields("Asset Repair", ["name", "asset", "asset_name", "description"])
    or_filters = []
    if search:
        q = f"%{search}%"
        or_filters = [[field, "like", q] for field in search_fields]

    repairs = frappe.get_all(
        "Asset Repair",
        filters=filters,
        or_filters=or_filters or None,
        fields=fields,
        order_by="creation desc",
        limit_page_length=page_size,
        limit_start=(page - 1) * page_size
    )
    if or_filters:
        total = len(frappe.get_all(
            "Asset Repair",
            filters=filters,
            or_filters=or_filters,
            fields=["name"],
            limit_page_length=100000,
        ))
    else:
        total = frappe.db.count("Asset Repair", filters)

    repairs = _apply_rh_defaults(repairs)

    # Add approval info
    for repair in repairs:
        repair["is_approved"] = repair.get("docstatus") == 1
        repair["is_rejected"] = repair.get("repair_status") == "Cancelled"
        # Get owner full name
        repair["created_by"] = frappe.db.get_value("User", repair.get("owner"), "full_name") or repair.get("owner")

    return {
        "repairs": repairs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_asset_repair(repair_name):
    """Full asset repair detail."""
    if not frappe.db.exists("Asset Repair", repair_name):
        frappe.throw(f"Asset Repair '{repair_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset Repair", repair_name)

    stock_items = []
    for item in doc.stock_items or []:
        stock_items.append({
            "item_code": item.item_code,
            "item_name": frappe.db.get_value("Item", item.item_code, "item_name") if item.item_code else None,
            "warehouse": item.warehouse,
            "consumed_quantity": item.consumed_quantity,
            "serial_and_batch_bundle": item.get("serial_and_batch_bundle"),
            "total_value": item.get("total_value"),
        })

    # Resolve rh_reported_by name
    reported_by_name = None
    if doc.get("rh_reported_by"):
        reported_by_name = frappe.db.get_value("Employee", doc.rh_reported_by, "employee_name")

    # Resolve rh_assigned_technician name
    technician_name = None
    if doc.get("rh_assigned_technician"):
        technician_name = frappe.db.get_value("Maintenance Technician", doc.rh_assigned_technician, "technician_name")

    # Resolve rh_approved_by name
    approved_by_name = None
    if doc.get("rh_approved_by"):
        approved_by_name = frappe.db.get_value("User", doc.rh_approved_by, "full_name")

    # Resolve hotel room number
    hotel_room_number = None
    if doc.get("rh_hotel_room"):
        hotel_room_number = frappe.db.get_value("Hotel Room", doc.rh_hotel_room, "room_number")

    return {
        "name": doc.name,
        "asset": doc.asset,
        "asset_name": doc.asset_name,
        "company": doc.company,
        "failure_date": doc.failure_date,
        "completion_date": doc.completion_date,
        "repair_status": doc.repair_status,
        "description": doc.description,
        "actions_performed": doc.actions_performed,
        "downtime": doc.downtime,
        "repair_cost": doc.repair_cost,
        "total_repair_cost": doc.total_repair_cost,
        "capitalize_repair_cost": doc.capitalize_repair_cost,
        "stock_consumption": doc.stock_consumption,
        "stock_items": stock_items,
        "increase_in_asset_life": doc.increase_in_asset_life,
        "purchase_invoice": doc.purchase_invoice,
        "cost_center": doc.cost_center,
        "project": doc.project,
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
def create_asset_repair(
    asset,
    failure_date,
    description=None,
    actions_performed=None,
    repair_cost=0,
    capitalize_repair_cost=0,
    stock_consumption=0,
    stock_items=None,
    increase_in_asset_life=0,
    cost_center=None,
    project=None,
    rh_location_type=None,
    rh_hotel_room=None,
    rh_asset_location=None,
    rh_reported_by=None,
    rh_priority=None,
    rh_assigned_technician=None,
    rh_issue_type=None
):
    """Create a new Asset Repair (saved as draft, pending approval)."""
    doc = frappe.new_doc("Asset Repair")
    doc.asset = asset
    doc.failure_date = failure_date
    doc.description = description
    doc.actions_performed = actions_performed
    doc.repair_cost = float(repair_cost or 0)
    doc.capitalize_repair_cost = int(capitalize_repair_cost or 0)
    doc.stock_consumption = int(stock_consumption or 0)
    doc.increase_in_asset_life = int(increase_in_asset_life or 0)
    doc.cost_center = cost_center
    doc.project = project

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

    if stock_items:
        if isinstance(stock_items, str):
            stock_items = json.loads(stock_items)
        for item in stock_items:
            doc.append("stock_items", {
                "item_code": item.get("item_code"),
                "warehouse": item.get("warehouse"),
                "consumed_quantity": item.get("consumed_quantity", 1),
            })

    doc.insert()

    return {
        "name": doc.name,
        "repair_status": doc.repair_status,
        "message": "Asset Repair created successfully. Pending approval.",
    }


@frappe.whitelist()
def update_asset_repair(
    repair_name,
    asset=None,
    failure_date=None,
    description=None,
    actions_performed=None,
    repair_cost=None,
    capitalize_repair_cost=None,
    stock_consumption=None,
    stock_items=None,
    increase_in_asset_life=None,
    cost_center=None,
    project=None,
    purchase_invoice=None,
    rh_location_type=None,
    rh_hotel_room=None,
    rh_asset_location=None,
    rh_reported_by=None,
    rh_priority=None,
    rh_assigned_technician=None,
    rh_issue_type=None
):
    """Update an existing draft Asset Repair."""
    if not frappe.db.exists("Asset Repair", repair_name):
        frappe.throw(f"Asset Repair '{repair_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset Repair", repair_name)

    if doc.docstatus != 0:
        frappe.throw("Only draft repairs can be edited.")
    if doc.repair_status == "Completed":
        frappe.throw("Completed repairs cannot be edited.")

    if asset is not None:
        doc.asset = asset
    if failure_date is not None:
        doc.failure_date = failure_date
    if description is not None:
        doc.description = description
    if actions_performed is not None:
        doc.actions_performed = actions_performed
    if repair_cost is not None:
        doc.repair_cost = float(repair_cost)
    if capitalize_repair_cost is not None:
        doc.capitalize_repair_cost = int(capitalize_repair_cost)
    if stock_consumption is not None:
        doc.stock_consumption = int(stock_consumption)
    if increase_in_asset_life is not None:
        doc.increase_in_asset_life = int(increase_in_asset_life)
    if cost_center is not None:
        doc.cost_center = cost_center
    if project is not None:
        doc.project = project
    if purchase_invoice is not None:
        doc.purchase_invoice = purchase_invoice

    # Handle stock_items child table
    if stock_items is not None:
        if isinstance(stock_items, str):
            stock_items = json.loads(stock_items)
        doc.stock_items = []
        for item in stock_items:
            doc.append("stock_items", {
                "item_code": item.get("item_code"),
                "warehouse": item.get("warehouse"),
                "consumed_quantity": item.get("consumed_quantity", 1),
            })

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

    doc.save()

    return {
        "name": doc.name,
        "repair_status": doc.repair_status,
        "message": "Asset Repair updated successfully.",
    }


@frappe.whitelist()
def approve_asset_repair(repair_name):
    """Approve an asset repair. Only Admin/Hotel Manager can do this."""
    if not frappe.db.exists("Asset Repair", repair_name):
        frappe.throw(f"Asset Repair '{repair_name}' not found", frappe.DoesNotExistError)

    # Check permissions - must be Admin or Hotel Manager
    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = ["Administrator", "Hotel Manager", "System Manager"]
    if not any(role in user_roles for role in allowed_roles):
        frappe.throw("Only Admin or Hotel Manager can approve asset repairs.", frappe.PermissionError)

    doc = frappe.get_doc("Asset Repair", repair_name)
    if doc.docstatus != 0:
        frappe.throw("This repair has already been processed.")

    # Set rh_approved to Approved (triggers the override's on_update)
    doc.rh_approved = "Approved"
    doc.save()

    return {
        "name": doc.name,
        "repair_status": doc.repair_status,
        "rh_approved": doc.rh_approved,
        "message": "Asset Repair approved successfully.",
    }


@frappe.whitelist()
def reject_asset_repair(repair_name, reason=None):
    """Reject an asset repair. Only Admin/Hotel Manager can do this."""
    if not frappe.db.exists("Asset Repair", repair_name):
        frappe.throw(f"Asset Repair '{repair_name}' not found", frappe.DoesNotExistError)

    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = ["Administrator", "Hotel Manager", "System Manager"]
    if not any(role in user_roles for role in allowed_roles):
        frappe.throw("Only Admin or Hotel Manager can reject asset repairs.", frappe.PermissionError)

    doc = frappe.get_doc("Asset Repair", repair_name)

    if doc.docstatus == 2:
        frappe.throw("This repair has already been rejected.")

    # Set rh_approved to Rejected (triggers the override's on_update → _handle_rejection)
    doc.rh_approved = "Rejected"
    doc.save()

    if reason:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Asset Repair",
            "reference_name": repair_name,
            "content": f"Rejected: {reason}",
        }).insert(ignore_permissions=True)

    return {
        "name": doc.name,
        "repair_status": doc.repair_status,
        "rh_approved": doc.rh_approved,
        "message": "Asset Repair rejected.",
    }


@frappe.whitelist()
def complete_asset_repair(repair_name, completion_date=None, actions_performed=None):
    """Mark an asset repair as completed."""
    from frappe.utils import now_datetime

    if not frappe.db.exists("Asset Repair", repair_name):
        frappe.throw(f"Asset Repair '{repair_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset Repair", repair_name)

    if doc.repair_status == "Completed":
        frappe.throw("This repair is already completed.")

    doc.repair_status = "Completed"
    doc.completion_date = completion_date or now_datetime()
    if actions_performed:
        doc.actions_performed = actions_performed
    doc.save()

    # Submit the document (docstatus 0 → 1)
    if doc.docstatus == 0:
        doc.submit()

    return {
        "name": doc.name,
        "repair_status": doc.repair_status,
        "docstatus": doc.docstatus,
        "message": "Asset Repair completed and submitted.",
    }


@frappe.whitelist()
def get_assets_for_repair():
    """Get list of assets available for repair selection."""
    assets = frappe.get_all(
        "Asset",
        filters={"docstatus": 1, "name": ["not like", "_Test%"]},
        fields=["name", "asset_name", "location", "asset_category", "company"],
        order_by="asset_name asc",
        limit_page_length=0
    )
    return assets


@frappe.whitelist()
def get_employees_for_repair():
    """Get list of employees for reported_by dropdown."""
    return frappe.get_all(
        "Employee",
        filters={"status": "Active", "name": ["not like", "_Test%"]},
        fields=["name", "employee_name"],
        order_by="employee_name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_technicians_for_repair():
    """Get list of maintenance technicians."""
    return frappe.get_all(
        "Maintenance Technician",
        filters={"name": ["not like", "_Test%"]},
        fields=["name", "technician_name"],
        order_by="technician_name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_hotel_rooms_for_repair():
    """Get list of hotel rooms."""
    return frappe.get_all(
        "Hotel Room",
        filters={"name": ["not like", "_Test%"]},
        fields=["name", "room_number"],
        order_by="room_number asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_cost_centers(company=None):
    """Get list of cost centers for dropdown."""
    filters = {"is_group": 0, "name": ["not like", "_Test%"]}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Cost Center",
        filters=filters,
        fields=["name"],
        order_by="name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_projects(company=None):
    """Get list of projects for dropdown."""
    filters = {"name": ["not like", "_Test%"]}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Project",
        filters=filters,
        fields=["name", "project_name"],
        order_by="name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_locations():
    """Get list of locations for asset location dropdown."""
    return frappe.get_all(
        "Location",
        filters={"name": ["not like", "_Test%"]},
        fields=["name"],
        order_by="name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_items_for_stock(company=None):
    """Get list of stock items for consumption table."""
    filters = {"disabled": 0, "is_stock_item": 1, "name": ["not like", "_Test%"]}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_name"],
        order_by="item_name asc",
        limit_page_length=0
    )


@frappe.whitelist()
def get_warehouses(company=None):
    """Get list of warehouses for stock consumption table."""
    filters = {"disabled": 0, "is_group": 0, "name": ["not like", "_Test%"]}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Warehouse",
        filters=filters,
        fields=["name"],
        order_by="name asc",
        limit_page_length=0
    )
