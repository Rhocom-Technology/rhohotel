import frappe
import json
from frappe.utils import nowdate, get_first_day_of_week


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_machine_access_log_dashboard():
    """Dashboard statistics for Machine Access Log."""
    today = nowdate()
    week_start = get_first_day_of_week(today)

    total = frappe.db.count("Machine Access Log")
    draft = frappe.db.count("Machine Access Log", {"docstatus": 0})
    submitted = frappe.db.count("Machine Access Log", {"docstatus": 1})
    cancelled = frappe.db.count("Machine Access Log", {"docstatus": 2})

    this_week = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMachine Access Log`
        WHERE DATE(creation) >= %s AND DATE(creation) <= %s
    """, (week_start, today), as_dict=1)[0].cnt or 0

    today_count = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMachine Access Log`
        WHERE DATE(date_opened) = %s
    """, (today,), as_dict=1)[0].cnt or 0

    # By location type
    location_breakdown = frappe.db.sql("""
        SELECT IFNULL(location_type, 'Not Set') as location_type, COUNT(name) as count
        FROM `tabMachine Access Log`
        GROUP BY location_type ORDER BY count DESC
    """, as_dict=1)

    # Top machines accessed
    top_machines = frappe.db.sql("""
        SELECT IFNULL(machine_name, 'Unknown') as machine_name, COUNT(name) as count
        FROM `tabMachine Access Log`
        WHERE machine_name IS NOT NULL AND machine_name != ''
        GROUP BY machine_name ORDER BY count DESC LIMIT 10
    """, as_dict=1)

    # Top technicians
    top_technicians = frappe.db.sql("""
        SELECT IFNULL(technician, 'Unassigned') as technician, COUNT(name) as count
        FROM `tabMachine Access Log`
        WHERE technician IS NOT NULL AND technician != ''
        GROUP BY technician ORDER BY count DESC LIMIT 10
    """, as_dict=1)

    # Recent logs
    recent = frappe.db.sql("""
        SELECT name, machine_name, date_opened, technician, docstatus,
               facility_work_order, location_type, room, asset_location
        FROM `tabMachine Access Log`
        ORDER BY creation DESC LIMIT 10
    """, as_dict=1)

    # Monthly trend (last 6 months)
    monthly_trend = frappe.db.sql("""
        SELECT DATE_FORMAT(creation, '%%Y-%%m') as month, COUNT(name) as count
        FROM `tabMachine Access Log`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY month ORDER BY month ASC
    """, as_dict=1)

    return {
        "total": total,
        "draft": draft,
        "submitted": submitted,
        "cancelled": cancelled,
        "this_week": this_week,
        "today": today_count,
        "location_breakdown": location_breakdown,
        "top_machines": top_machines,
        "top_technicians": top_technicians,
        "recent": recent,
        "monthly_trend": monthly_trend,
    }


# ══════════════════════════════════════════════════════════════════════════════
# LIST
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_machine_access_log_stats():
    """Stats cards for list page."""
    total = frappe.db.count("Machine Access Log")
    draft = frappe.db.count("Machine Access Log", {"docstatus": 0})
    submitted = frappe.db.count("Machine Access Log", {"docstatus": 1})
    today_count = frappe.db.sql("""
        SELECT COUNT(name) as cnt FROM `tabMachine Access Log`
        WHERE DATE(date_opened) = %s
    """, (nowdate(),), as_dict=1)[0].cnt or 0

    return {
        "total": total,
        "draft": draft,
        "submitted": submitted,
        "today": today_count,
    }


@frappe.whitelist()
def get_machine_access_log_list(page=1, page_size=20, filters=None):
    """Paginated list with optional filters."""
    if isinstance(filters, str):
        filters = json.loads(filters)
    filters = filters or {}

    page = int(page)
    page_size = int(page_size)
    offset = (page - 1) * page_size

    where_clauses = ["1=1"]
    values = {}

    if filters.get("docstatus") is not None:
        where_clauses.append("mal.docstatus = %(docstatus)s")
        values["docstatus"] = int(filters["docstatus"])

    if filters.get("facility_work_order"):
        where_clauses.append("mal.facility_work_order = %(facility_work_order)s")
        values["facility_work_order"] = filters["facility_work_order"]

    if filters.get("technician"):
        where_clauses.append("mal.technician = %(technician)s")
        values["technician"] = filters["technician"]

    if filters.get("machine_name"):
        where_clauses.append("mal.machine_name LIKE %(machine_name)s")
        values["machine_name"] = f"%{filters['machine_name']}%"

    if filters.get("location_type"):
        where_clauses.append("mal.location_type = %(location_type)s")
        values["location_type"] = filters["location_type"]

    if filters.get("date_from"):
        where_clauses.append("mal.date_opened >= %(date_from)s")
        values["date_from"] = filters["date_from"]

    if filters.get("date_to"):
        where_clauses.append("mal.date_opened <= %(date_to)s")
        values["date_to"] = filters["date_to"]

    if filters.get("search"):
        where_clauses.append("(mal.name LIKE %(search)s OR mal.machine_name LIKE %(search)s OR mal.reason_for_access LIKE %(search)s)")
        values["search"] = f"%{filters['search']}%"

    where = " AND ".join(where_clauses)

    count = frappe.db.sql(
        f"SELECT COUNT(mal.name) as cnt FROM `tabMachine Access Log` mal WHERE {where}",
        values, as_dict=1
    )[0].cnt or 0

    values["limit"] = page_size
    values["offset"] = offset

    records = frappe.db.sql(f"""
        SELECT mal.name, mal.facility_work_order, mal.asset, mal.machine_name,
               mal.date_opened, mal.time_opened, mal.time_closed,
               mal.location_type, mal.room, mal.asset_location, mal.location_description,
               mal.reason_for_access, mal.technician, mal.witness, mal.docstatus
        FROM `tabMachine Access Log` mal
        WHERE {where}
        ORDER BY mal.creation DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """, values, as_dict=1)

    return {
        "records": records,
        "total": count,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-count // page_size)),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DETAIL
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_machine_access_log(name):
    """Get full detail for a single Machine Access Log."""
    doc = frappe.get_doc("Machine Access Log", name)

    # Resolve linked names
    technician_name = ""
    if doc.technician:
        technician_name = frappe.db.get_value("Maintenance Technician", doc.technician, "technician_name") or doc.technician

    witness_name = ""
    if doc.witness:
        witness_name = frappe.db.get_value("Employee", doc.witness, "employee_name") or doc.witness

    user_roles = frappe.get_roles(frappe.session.user)

    return {
        "name": doc.name,
        "docstatus": doc.docstatus,
        "facility_work_order": doc.facility_work_order,
        "asset": doc.asset,
        "machine_name": doc.machine_name,
        "date_opened": str(doc.date_opened) if doc.date_opened else None,
        "time_opened": str(doc.time_opened) if doc.time_opened else None,
        "time_closed": str(doc.time_closed) if doc.time_closed else None,
        "location_type": doc.location_type,
        "room": doc.room,
        "asset_location": doc.asset_location,
        "location_description": doc.location_description,
        "reason_for_access": doc.reason_for_access,
        "technician": doc.technician,
        "technician_name": technician_name,
        "witness": doc.witness,
        "witness_name": witness_name,
        "parts_removed": doc.parts_removed,
        "condition_on_exit": doc.condition_on_exit,
        "technician_confirmed": doc.technician_confirmed,
        "witness_confirmed": doc.witness_confirmed,
        "user_roles": user_roles,
        "owner": doc.owner,
        "creation": str(doc.creation) if doc.creation else None,
        "modified": str(doc.modified) if doc.modified else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CREATE / SAVE / SUBMIT / CANCEL
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_machine_access_log(log_data):
    """Create a new Machine Access Log."""
    if isinstance(log_data, str):
        log_data = json.loads(log_data)

    try:
        doc = frappe.new_doc("Machine Access Log")
        doc.facility_work_order = log_data.get("facility_work_order") or None
        doc.asset = log_data.get("asset") or None
        doc.machine_name = log_data.get("machine_name") or ""
        doc.date_opened = log_data.get("date_opened") or nowdate()
        doc.time_opened = log_data.get("time_opened") or None
        doc.time_closed = log_data.get("time_closed") or None
        doc.location_type = log_data.get("location_type", "Room")
        doc.room = log_data.get("room") or None
        doc.asset_location = log_data.get("asset_location") or None
        doc.location_description = log_data.get("location_description") or None
        doc.reason_for_access = log_data.get("reason_for_access") or ""
        doc.technician = log_data.get("technician") or None
        doc.witness = log_data.get("witness") or None
        doc.parts_removed = log_data.get("parts_removed") or ""
        doc.condition_on_exit = log_data.get("condition_on_exit") or ""
        doc.technician_confirmed = log_data.get("technician_confirmed") or 0
        doc.witness_confirmed = log_data.get("witness_confirmed") or 0

        doc.insert()
        frappe.db.commit()
        return {"success": True, "name": doc.name}

    except frappe.PermissionError:
        frappe.db.rollback()
        return {"success": False, "error": "You do not have permission to create a Machine Access Log. Please contact your administrator."}
    except frappe.MandatoryError as e:
        frappe.db.rollback()
        missing = str(e).replace(":", "").strip()
        return {"success": False, "error": f"Required fields missing: {missing}"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {"success": False, "error": str(e)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_machine_access_log error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def save_machine_access_log(name, log_data):
    """Save/update a Machine Access Log (only if Draft)."""
    if isinstance(log_data, str):
        log_data = json.loads(log_data)

    try:
        doc = frappe.get_doc("Machine Access Log", name)
        if doc.docstatus != 0:
            return {"success": False, "error": "Can only edit logs in Draft status"}

        editable_fields = [
            "facility_work_order", "asset", "machine_name", "date_opened",
            "time_opened", "time_closed", "location_type", "room",
            "asset_location", "location_description", "reason_for_access",
            "technician", "witness", "parts_removed", "condition_on_exit",
            "technician_confirmed", "witness_confirmed"
        ]

        for field in editable_fields:
            if field in log_data:
                setattr(doc, field, log_data[field])

        doc.save()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "save_machine_access_log error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_machine_access_log(name):
    """Submit a Machine Access Log."""
    try:
        doc = frappe.get_doc("Machine Access Log", name)
        doc.submit()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_machine_access_log error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_machine_access_log(name):
    """Cancel a Machine Access Log."""
    try:
        doc = frappe.get_doc("Machine Access Log", name)
        doc.cancel()
        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_machine_access_log error")
        frappe.db.rollback()
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# DROPDOWN HELPERS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_technicians_list():
    """Technicians for dropdown."""
    return frappe.get_all(
        "Maintenance Technician",
        fields=["name", "technician_name"],
        order_by="technician_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_witnesses_list():
    """Employees for witness dropdown."""
    return frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "department"],
        filters={"status": "Active"},
        order_by="employee_name asc",
        limit_page_length=500
    )


@frappe.whitelist()
def get_work_order_prefill(work_order_name):
    """Get Facility Work Order details for pre-filling a new Machine Access Log."""
    if not work_order_name or not frappe.db.exists("Facility Work Order", work_order_name):
        return {"success": False, "error": "Work Order not found"}

    doc = frappe.get_doc("Facility Work Order", work_order_name)
    asset_name = ""
    if doc.asset:
        asset_name = frappe.db.get_value("Asset", doc.asset, "asset_name") or ""

    return {
        "success": True,
        "asset": doc.asset or "",
        "machine_name": asset_name,
        "location_type": doc.location_type or "Room",
        "room": doc.room or "",
        "asset_location": doc.asset_location or "",
        "location_description": doc.location_description or "",
    }
