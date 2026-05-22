import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week


@frappe.whitelist()
def get_facility_work_order_stats():
    """Stats for the list page header cards."""
    today = nowdate()
    week_start = get_first_day_of_week(today)

    active_states = [
        "Draft",
        "Pending Requesting Officer Approval",
        "Pending Facility Supervisor Approval",
        "Pending Department Head Signature",
    ]

    active = frappe.db.count(
        "Facility Work Order", {"workflow_state": ["in", active_states]}
    )
    closed = frappe.db.count(
        "Facility Work Order", {"workflow_state": "Closed"}
    )
    emergency = frappe.db.count(
        "Facility Work Order",
        {"priority": "Emergency", "workflow_state": ["in", active_states]}
    )
    urgent = frappe.db.count(
        "Facility Work Order",
        {"priority": "Urgent", "workflow_state": ["in", active_states]}
    )
    closed_this_week = frappe.db.sql("""
        SELECT COUNT(name) as cnt
        FROM `tabFacility Work Order`
        WHERE workflow_state = 'Closed'
        AND DATE(closed_on) >= %s AND DATE(closed_on) <= %s
    """, (week_start, today), as_dict=1)[0].cnt or 0

    overdue = frappe.db.sql("""
        SELECT COUNT(name) as cnt
        FROM `tabFacility Work Order`
        WHERE workflow_state NOT IN ('Closed','Rejected','Cancelled')
        AND expected_completion_date IS NOT NULL
        AND expected_completion_date < %s
    """, (today,), as_dict=1)[0].cnt or 0

    unassigned = frappe.db.sql("""
        SELECT COUNT(name) as cnt
        FROM `tabFacility Work Order`
        WHERE workflow_state NOT IN ('Closed','Rejected','Cancelled')
        AND (assigned_technician IS NULL OR assigned_technician = '')
    """, as_dict=1)[0].cnt or 0

    rejected = frappe.db.count("Facility Work Order", {"workflow_state": "Rejected"})

    return {
        "active": active,
        "closed": closed,
        "emergency": emergency,
        "urgent": urgent,
        "closed_this_week": closed_this_week,
        "overdue": overdue,
        "unassigned": unassigned,
        "rejected": rejected,
    }


@frappe.whitelist()
def get_facility_work_order_list(
    search=None,
    filter_priority=None,
    filter_status=None,
    filter_category=None,
    filter_department=None,
    filter_technician=None,
    page=1,
    page_size=25
):
    """Paginated facility work order list with filters."""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = {}
    if filter_priority:
        filters["priority"] = filter_priority
    if filter_status:
        filters["workflow_state"] = filter_status
    if filter_category:
        filters["category"] = filter_category
    if filter_department:
        filters["requesting_department"] = filter_department
    if filter_technician:
        filters["assigned_technician"] = filter_technician

    fields = [
        "name", "requesting_department", "contact_person", "date_reported",
        "priority", "category", "workflow_state", "assigned_technician",
        "location_type", "room", "asset_location", "location_description",
        "expected_completion_date"
    ]

    if search:
        orders = frappe.db.sql("""
            SELECT
                name, requesting_department, contact_person, date_reported,
                priority, category, workflow_state, assigned_technician,
                location_type, room, asset_location, location_description,
                expected_completion_date
            FROM `tabFacility Work Order`
            WHERE (
                name LIKE %(q)s
                OR requesting_department LIKE %(q)s
                OR category LIKE %(q)s
                OR room LIKE %(q)s
                OR location_description LIKE %(q)s
                OR description_of_problem LIKE %(q)s
            )
            {filter_clause}
            ORDER BY date_reported DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """.format(
            filter_clause=_build_filter_clause(filters)
        ), {
            "q": f"%{search}%",
            "limit": page_size,
            "offset": (page - 1) * page_size
        }, as_dict=1)

        total = frappe.db.sql("""
            SELECT COUNT(name) as cnt FROM `tabFacility Work Order`
            WHERE (
                name LIKE %(q)s
                OR requesting_department LIKE %(q)s
                OR category LIKE %(q)s
                OR room LIKE %(q)s
                OR location_description LIKE %(q)s
                OR description_of_problem LIKE %(q)s
            )
            {filter_clause}
        """.format(filter_clause=_build_filter_clause(filters)),
            {"q": f"%{search}%"}, as_dict=1)[0].cnt or 0
    else:
        orders = frappe.get_all(
            "Facility Work Order",
            filters=filters,
            fields=fields,
            order_by="date_reported desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size
        )
        total = frappe.db.count("Facility Work Order", filters)

    # Resolve technician names & location display
    tech_cache = {}
    for order in orders:
        tid = order.get("assigned_technician")
        if tid:
            if tid not in tech_cache:
                tech_cache[tid] = frappe.db.get_value(
                    "Maintenance Technician", tid, "technician_name"
                ) or tid
            order["technician_name"] = tech_cache[tid]
        else:
            order["technician_name"] = "Unassigned"

        order["location_display"] = (
            order.get("room")
            or order.get("asset_location")
            or order.get("location_description")
            or "—"
        )

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_facility_work_order_filters():
    """Dropdown options for filters."""
    technicians = frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1},
        fields=["name", "technician_name"],
        order_by="technician_name asc",
        limit_page_length=200
    )
    departments = frappe.get_all(
        "Department",
        fields=["name"],
        order_by="name asc",
        limit_page_length=100
    )
    return {
        "technicians": technicians,
        "departments": departments,
    }


@frappe.whitelist()
def get_facility_work_order(order_name):
    """Full facility work order detail with resolved names."""
    if not frappe.db.exists("Facility Work Order", order_name):
        frappe.throw(f"Facility Work Order '{order_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Facility Work Order", order_name)

    # Resolve linked names
    technician_name = None
    if doc.assigned_technician:
        technician_name = frappe.db.get_value(
            "Maintenance Technician", doc.assigned_technician, "technician_name"
        )

    contact_person_name = None
    if doc.contact_person:
        contact_person_name = frappe.db.get_value(
            "Employee", doc.contact_person, "employee_name"
        )

    # Location display
    location_display = (
        doc.room or doc.asset_location or doc.location_description or "—"
    )

    # Get available workflow actions for current user
    workflow_actions = _get_workflow_actions(doc)

    # Get user roles for permission checks
    user_roles = frappe.get_roles(frappe.session.user)

    # Check linked documents
    linked_docs = _get_linked_documents(doc.name)

    return {
        "name": doc.name,
        "workflow_state": doc.workflow_state,
        "requesting_department": doc.requesting_department,
        "contact_person": doc.contact_person,
        "contact_person_name": contact_person_name,
        "date_reported": str(doc.date_reported) if doc.date_reported else None,
        "priority": doc.priority,
        "category": doc.category,
        "location_type": doc.location_type,
        "room": doc.room,
        "asset_location": doc.asset_location,
        "location_description": doc.location_description,
        "location_display": location_display,
        "asset": doc.asset,
        "description_of_problem": doc.description_of_problem,
        "inspection_findings": doc.inspection_findings,
        "assigned_technician": doc.assigned_technician,
        "technician_name": technician_name,
        "estimated_materials": doc.estimated_materials,
        "expected_completion_date": str(doc.expected_completion_date) if doc.expected_completion_date else None,
        "action_taken": doc.action_taken,
        "completion_date": str(doc.completion_date) if doc.completion_date else None,
        "submitted_by": doc.submitted_by,
        "submitted_on": str(doc.submitted_on) if doc.submitted_on else None,
        "closed_by": doc.closed_by,
        "closed_on": str(doc.closed_on) if doc.closed_on else None,
        "workflow_actions": workflow_actions,
        "user_roles": user_roles,
        "linked_docs": linked_docs,
    }


@frappe.whitelist()
def save_facility_work_order(order_name, order_data):
    """Save/update a facility work order."""
    if isinstance(order_data, str):
        order_data = json.loads(order_data)

    try:
        doc = frappe.get_doc("Facility Work Order", order_name)

        # Role required to edit in each state (from workflow Allow Edit)
        # "All" means any user with write permission on the doc can edit
        state_role_map = {
            "Draft": None,  # All - no role restriction
            "Pending Requesting Officer Approval": None,  # All
            "Pending Facility Supervisor Approval": ["Facilities Supervisor", "System Manager", "Administrator"],
            "Pending Department Head Signature": ["Department Head", "System Manager", "Administrator"],
        }

        # Check edit permission based on workflow state
        editable_fields_map = {
            "Draft": [
                "requesting_department", "contact_person", "priority", "category",
                "location_type", "room", "asset_location", "location_description",
                "asset", "description_of_problem"
            ],
            "Pending Requesting Officer Approval": [
                "requesting_department", "contact_person", "priority", "category",
                "location_type", "room", "asset_location", "location_description",
                "asset", "description_of_problem"
            ],
            "Pending Facility Supervisor Approval": [
                "inspection_findings", "assigned_technician", "estimated_materials",
                "expected_completion_date", "action_taken"
            ],
            "Pending Department Head Signature": [],
        }

        allowed_fields = editable_fields_map.get(doc.workflow_state, [])
        if not allowed_fields:
            return {"success": False, "error": f"Cannot edit in state: {doc.workflow_state}"}

        # Check user has required role for this state
        required_roles = state_role_map.get(doc.workflow_state, [])
        if required_roles is not None:
            user_roles = frappe.get_roles(frappe.session.user)
            if not any(role in user_roles for role in required_roles):
                return {"success": False, "error": "You do not have permission to edit in this state"}

        for field in allowed_fields:
            if field in order_data:
                setattr(doc, field, order_data[field])

        doc.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "save_facility_work_order error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_facility_work_order(order_data):
    """Create a new Facility Work Order."""
    if isinstance(order_data, str):
        order_data = json.loads(order_data)

    try:
        doc = frappe.new_doc("Facility Work Order")
        doc.requesting_department = order_data.get("requesting_department") or ""
        doc.contact_person = order_data.get("contact_person") or ""
        doc.priority = order_data.get("priority", "Routine")
        doc.category = order_data.get("category") or ""
        doc.location_type = order_data.get("location_type", "Room")
        doc.room = order_data.get("room") or None
        doc.asset_location = order_data.get("asset_location") or None
        doc.location_description = order_data.get("location_description") or None
        doc.asset = order_data.get("asset") or None
        doc.description_of_problem = order_data.get("description_of_problem") or ""

        doc.insert()
        frappe.db.commit()
        return {"success": True, "order_name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_facility_work_order error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def apply_workflow_action(order_name, action):
    """Apply a workflow action to the Facility Work Order."""
    try:
        doc = frappe.get_doc("Facility Work Order", order_name)
        frappe.model.workflow.apply_workflow(doc, action)
        frappe.db.commit()
        return {"success": True, "new_state": doc.workflow_state}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "apply_workflow_action error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_facility_work_order(order_name):
    """Cancel a facility work order (set to Cancelled state)."""
    try:
        doc = frappe.get_doc("Facility Work Order", order_name)

        if doc.workflow_state in ["Closed", "Cancelled"]:
            return {"success": False, "error": "Cannot cancel an already closed/cancelled order"}

        doc.workflow_state = "Cancelled"
        doc.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_facility_work_order error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_technicians_for_assignment():
    """Technicians available for assignment."""
    return frappe.get_all(
        "Maintenance Technician",
        filters={"visible_for_assignment": 1},
        fields=["name", "technician_name", "availability", "primary_specialization"],
        order_by="technician_name asc",
        limit_page_length=200
    )


@frappe.whitelist()
def get_employees_for_contact():
    """Active employees for contact person dropdown."""
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "department"],
        order_by="employee_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_departments_list():
    """Department list for dropdown."""
    return frappe.get_all(
        "Department",
        fields=["name"],
        order_by="name asc",
        limit_page_length=100
    )


@frappe.whitelist()
def get_rooms_list():
    """Hotel rooms for room dropdown."""
    return frappe.get_all(
        "Hotel Room",
        fields=["name", "room_number"],
        order_by="name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_assets_list():
    """Assets for asset dropdown."""
    return frappe.get_all(
        "Asset",
        fields=["name", "asset_name", "location"],
        order_by="asset_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_locations_list():
    """Locations for asset location dropdown."""
    return frappe.get_all(
        "Location",
        fields=["name"],
        order_by="name asc",
        limit_page_length=500
    )


# ── Helper functions ─────────────────────────────────────────────────────────

def _build_filter_clause(filters):
    """Build extra AND clauses from a filters dict for raw SQL."""
    clauses = []
    for field, value in filters.items():
        safe_field = frappe.scrub(field)
        clauses.append(f"AND `{safe_field}` = {frappe.db.escape(value)}")
    return " ".join(clauses)


def _get_workflow_actions(doc):
    """Get available workflow actions for the current user on this document."""
    try:
        from frappe.model.workflow import get_transitions
        transitions = get_transitions(doc)
        return [
            {"action": t.get("action"), "next_state": t.get("next_state")}
            for t in transitions
        ]
    except Exception:
        return []


def _get_linked_documents(order_name):
    """Get counts of linked sub-documents."""
    linked = {}
    link_doctypes = [
        ("Machine Access Log", "facility_work_order"),
        ("Removed Parts Register", "facility_work_order"),
        ("Vehicle Maintenance Report", "facility_work_order"),
        ("Equipment Repair Authorization", "facility_work_order"),
    ]
    for dt, fieldname in link_doctypes:
        if frappe.db.exists("DocType", dt):
            count = frappe.db.count(dt, {fieldname: order_name})
            linked[dt] = count
        else:
            linked[dt] = 0
    return linked
