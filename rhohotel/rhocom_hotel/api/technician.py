import frappe
import json


@frappe.whitelist()
def get_employees_for_technician():
    """Active employees for the in-house technician link"""
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "department", "cell_number", "personal_email"],
        order_by="employee_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_vendors_for_technician():
    """Active suppliers/vendors for the outsourced technician link"""
    return frappe.get_all(
        "Supplier",
        filters={"disabled": 0},
        fields=["name", "supplier_name", "supplier_type", "mobile_no", "email_id"],
        order_by="supplier_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def create_technician(technician_data):
    """Create a new Maintenance Technician doc"""
    if isinstance(technician_data, str):
        technician_data = json.loads(technician_data)

    try:
        tech = frappe.new_doc("Maintenance Technician")
        tech.technician_name = technician_data.get("technician_name", "").strip()
        tech.technician_type = technician_data.get("technician_type", "In-House")
        tech.availability = technician_data.get("availability", "Available")

        if tech.technician_type == "In-House":
            tech.employee = technician_data.get("employee") or None
            tech.supplier = None
        else:
            tech.supplier = technician_data.get("supplier") or None
            tech.employee = None

        tech.primary_specialization = technician_data.get("primary_specialization", "")
        tech.secondary_skills = technician_data.get("secondary_skills", "")
        tech.phone = technician_data.get("phone", "")
        tech.email = technician_data.get("email", "")
        tech.shift = technician_data.get("shift", "")
        tech.response_priority_group = technician_data.get("response_priority_group", "Standard")
        tech.can_receive_urgent = 1 if technician_data.get("can_receive_urgent") else 0
        tech.visible_for_assignment = 1 if technician_data.get("visible_for_assignment") else 0
        tech.notes = technician_data.get("notes", "")
        tech.supported_categories = technician_data.get("supported_categories", "")
        tech.certification = technician_data.get("certification", "")

        tech.insert()
        frappe.db.commit()
        return {"success": True, "technician_name": tech.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_technician error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_technician(technician_id):
    """Full technician profile with computed stats"""
    if not frappe.db.exists("Maintenance Technician", technician_id):
        frappe.throw(f"Technician '{technician_id}' not found", frappe.DoesNotExistError)

    tech = frappe.get_doc("Maintenance Technician", technician_id)

    # Actual fields from Maintenance Task doctype JSON:
    #   status options: Open | In Progress | Done | Hold | Cancelled
    #   link field to technician: assigned_technician
    #   description field: task_description
    #   timing fields: start_time, end_time (Datetime)
    #   no completion_date field — use end_time for completed tasks

    # ── Open assignments ────────────────────────────────────────────────────
    open_tasks = frappe.get_all(
        "Maintenance Task",
        filters={
            "assigned_technician": technician_id,
            "status": ["not in", ["Done", "Cancelled", "Hold"]]
        },
        fields=["name", "task_description", "status", "priority", "start_time", "asset"],
        order_by="start_time asc",
        limit_page_length=20
    )

    # ── Stats ───────────────────────────────────────────────────────────────
    total_assigned = frappe.db.count(
        "Maintenance Task", {"assigned_technician": technician_id}
    )
    total_completed = frappe.db.count(
        "Maintenance Task", {"assigned_technician": technician_id, "status": "Done"}
    )
    completion_score = (
        round((total_completed / total_assigned) * 100, 1)
        if total_assigned > 0 else 0
    )

    # ── Recent completed (latest 3) — use end_time for date ────────────────
    recent_completed = frappe.get_all(
        "Maintenance Task",
        filters={"assigned_technician": technician_id, "status": "Done"},
        fields=["name", "task_description", "end_time", "asset", "status"],
        order_by="end_time desc",
        limit_page_length=3
    )

    # ── Linked name ─────────────────────────────────────────────────────────
    linked_name = None
    if tech.employee:
        linked_name = frappe.db.get_value("Employee", tech.employee, "employee_name")
    elif tech.supplier:
        linked_name = frappe.db.get_value("Supplier", tech.supplier, "supplier_name")

    return {
        "name": tech.name,
        "technician_name": tech.technician_name,
        "technician_type": tech.technician_type,
        "availability": tech.availability,
        "response_priority_group": tech.response_priority_group,
        "can_receive_urgent": tech.can_receive_urgent,
        "visible_for_assignment": tech.visible_for_assignment,
        "employee": tech.employee,
        "supplier": tech.supplier,
        "linked_name": linked_name,
        "primary_specialization": tech.primary_specialization,
        "secondary_skills": tech.secondary_skills,
        "phone": tech.phone,
        "email": tech.email,
        "shift": tech.shift,
        "notes": tech.notes,
        "supported_categories": tech.supported_categories,
        "certification": tech.certification,
        "total_tasks_assigned": total_assigned,
        "total_tasks_completed": total_completed,
        "completion_score": completion_score,
        "open_tasks": open_tasks,
        "open_tasks_count": len(open_tasks),
        "recent_completed": recent_completed,
    }


@frappe.whitelist()
def update_technician(technician_id, technician_data):
    """Update an existing Maintenance Technician"""
    if isinstance(technician_data, str):
        technician_data = json.loads(technician_data)

    try:
        tech = frappe.get_doc("Maintenance Technician", technician_id)

        tech.technician_name = technician_data.get("technician_name", tech.technician_name).strip()
        tech.technician_type = technician_data.get("technician_type", tech.technician_type)
        tech.availability = technician_data.get("availability", tech.availability)
        tech.response_priority_group = technician_data.get("response_priority_group", tech.response_priority_group)
        tech.can_receive_urgent = 1 if technician_data.get("can_receive_urgent") else 0
        tech.visible_for_assignment = 1 if technician_data.get("visible_for_assignment") else 0
        tech.primary_specialization = technician_data.get("primary_specialization", "")
        tech.secondary_skills = technician_data.get("secondary_skills", "")
        tech.phone = technician_data.get("phone", "")
        tech.email = technician_data.get("email", "")
        tech.shift = technician_data.get("shift", "")
        tech.notes = technician_data.get("notes", "")
        tech.supported_categories = technician_data.get("supported_categories", "")
        tech.certification = technician_data.get("certification", "")

        if tech.technician_type == "In-House":
            tech.employee = technician_data.get("employee") or None
            tech.supplier = None
        else:
            tech.supplier = technician_data.get("supplier") or None
            tech.employee = None

        tech.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_technician error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_availability(technician_id, availability):
    """Quick availability toggle"""
    try:
        frappe.db.set_value("Maintenance Technician", technician_id, "availability", availability)
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_availability error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_open_maintenance_tasks():
    """Open tasks for the assign modal dropdown"""
    return frappe.get_all(
        "Maintenance Task",
        filters={"status": ["not in", ["Done", "Cancelled"]]},
        fields=["name", "task_description", "status", "priority", "asset"],
        order_by="creation desc",
        limit_page_length=100
    )


@frappe.whitelist()
def get_technicians_list():
    """Technician list with computed stats for the register page"""
    technicians = frappe.get_all(
        "Maintenance Technician",
        fields=[
            "name", "technician_name", "technician_type", "availability",
            "primary_specialization", "phone", "email",
            "employee", "supplier", "response_priority_group",
            "can_receive_urgent", "visible_for_assignment"
        ],
        order_by="technician_name asc",
        limit_page_length=500
    )

    for tech in technicians:
        if tech.get("employee"):
            tech["linked_name"] = frappe.db.get_value(
                "Employee", tech["employee"], "employee_name"
            ) or tech["employee"]
            tech["source_label"] = tech["linked_name"]
        elif tech.get("supplier"):
            tech["linked_name"] = frappe.db.get_value(
                "Supplier", tech["supplier"], "supplier_name"
            ) or tech["supplier"]
            tech["source_label"] = tech["linked_name"]
        else:
            tech["linked_name"] = None
            tech["source_label"] = "—"

        tech["open_tasks_count"] = frappe.db.count(
            "Maintenance Task",
            {
                "assigned_technician": tech["name"],
                "status": ["not in", ["Done", "Cancelled", "Hold"]]
            }
        )

    # total = len(technicians)
    # in_house = sum(1 for t in technicians if t["technician_type"] == "In-House")
    # outsourced = sum(1 for t in technicians if t["technician_type"] == "Outsourced")
    # available = sum(1 for t in technicians if t["availability"] == "Available")

    total = len(technicians)

    in_house = sum(
        1 for t in technicians
        if t.get("technician_type") == "In-House"
    )

    outsourced = sum(
        1 for t in technicians
        if t.get("technician_type") == "Outsourced"
    )

    available = sum(
        1 for t in technicians
        if t.get("availability") == "Available"
    )

    return {
        "technicians": technicians,
        "stats": {
            "total": total,
            "in_house": in_house,
            "outsourced": outsourced,
            "available": available,
        }
    }


@frappe.whitelist()
def assign_task_to_technician(task_name, technician_id, note=None):
    """
    Assign an existing open Maintenance Task to this technician.
    Sets assigned_technician and updates status to In Progress if still Open.
    """
    try:
        if not frappe.db.exists("Maintenance Task", task_name):
            return {"success": False, "error": f"Task '{task_name}' not found"}

        if not frappe.db.exists("Maintenance Technician", technician_id):
            return {"success": False, "error": f"Technician '{technician_id}' not found"}

        task = frappe.get_doc("Maintenance Task", task_name)

        if task.docstatus == 1:
            return {"success": False, "error": "Cannot reassign a submitted task"}

        task.assigned_technician = technician_id
        if task.status == "Open":
            task.status = "In Progress"
        if note:
            existing = task.completion_notes or ""
            task.completion_notes = (existing + f"\n[Assignment note]: {note}").strip()

        task.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "assign_task_to_technician error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}