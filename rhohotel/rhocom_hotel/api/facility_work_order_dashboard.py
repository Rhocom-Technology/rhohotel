import frappe
from frappe.utils import nowdate, getdate, add_days, date_diff, flt

OPEN_STATES = [
    "Draft",
    "Pending Requesting Officer Approval",
    "Pending Facility Supervisor Approval",
    "Pending Department Head Signature"
]

@frappe.whitelist()
def get_facility_work_order_dashboard(days=30):
    try:
        days = int(days)
    except Exception:
        days = 30

    today = getdate(nowdate())
    start_date = add_days(today, -days + 1)

    return {
        "summary": get_summary(today),
        "secondary_cards": get_secondary_cards(today),
        "status_breakdown": get_group_counts("workflow_state"),
        "active_priority_levels": get_active_priority_levels(),
        "category_breakdown": get_group_counts("category"),
        "department_breakdown": get_department_breakdown(),
        "daily_trend": get_daily_trend(start_date, today),
        "aging": get_aging(today),
        "linked_documents": get_linked_document_summary(),
        "sla": get_sla_summary(today),
        "technician_workload": get_technician_workload(),
        "location_type_breakdown": get_location_type_breakdown(),
        "recent_work_orders": get_recent_work_orders(),
        "urgent_work_orders": get_urgent_work_orders(today),
        "top_locations": get_top_locations(),
        "stats": get_stats_alias(today),
    }


def get_summary(today):
    total = frappe.db.count("Facility Work Order")

    open_count = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": ["in", OPEN_STATES]}
    )

    closed_count = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": "Closed"}
    )

    rejected_count = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": "Rejected"}
    )

    cancelled_count = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": "Cancelled"}
    )

    urgent_open = frappe.db.count(
        "Facility Work Order",
        {
            "workflow_state": ["in", OPEN_STATES],
            "priority": ["in", ["Urgent", "Emergency"]]
        }
    )

    pending_supervisor = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": "Pending Facility Supervisor Approval"}
    )

    pending_head = frappe.db.count(
        "Facility Work Order",
        {"workflow_state": "Pending Department Head Signature"}
    )

    closed_today = 0
    if frappe.db.has_column("Facility Work Order", "closed_on"):
        closed_today = frappe.db.count(
            "Facility Work Order",
            {
                "workflow_state": "Closed",
                "closed_on": ["between", [str(today) + " 00:00:00", str(today) + " 23:59:59"]]
            }
        )

    avg_resolution_hours = get_average_resolution_hours()

    close_rate = 0
    if total:
        close_rate = round((flt(closed_count) / flt(total)) * 100, 1)

    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "rejected": rejected_count,
        "cancelled": cancelled_count,
        "urgent_open": urgent_open,
        "pending_supervisor": pending_supervisor,
        "pending_head": pending_head,
        "closed_today": closed_today,
        "avg_resolution_hours": avg_resolution_hours,
        "close_rate": close_rate
    }


def get_secondary_cards(today):
    overdue = get_overdue_count(today)

    unassigned = 0
    if frappe.db.has_column("Facility Work Order", "assigned_technician"):
        unassigned = frappe.db.count(
            "Facility Work Order",
            {
                "workflow_state": ["in", OPEN_STATES],
                "assigned_technician": ["is", "not set"]
            }
        )

    closed = frappe.db.count("Facility Work Order", {"workflow_state": "Closed"})
    rejected = frappe.db.count("Facility Work Order", {"workflow_state": "Rejected"})
    cancelled = frappe.db.count("Facility Work Order", {"workflow_state": "Cancelled"})

    return {
        "overdue": overdue,
        "unassigned": unassigned,
        "closed": closed,
        "rejected": rejected,
        "cancelled": cancelled
    }


def get_overdue_count(today):
    if not frappe.db.has_column("Facility Work Order", "expected_completion_date"):
        return 0

    return frappe.db.count(
        "Facility Work Order",
        {
            "workflow_state": ["in", OPEN_STATES],
            "expected_completion_date": ["<", today]
        }
    )


def get_average_resolution_hours():
    closed_field = "closed_on" if frappe.db.has_column("Facility Work Order", "closed_on") else None
    completion_field = "completion_date" if frappe.db.has_column("Facility Work Order", "completion_date") else None

    if not closed_field and not completion_field:
        return 0

    end_expr = "closed_on" if closed_field else "completion_date"

    if closed_field and completion_field:
        end_expr = "IFNULL(closed_on, completion_date)"

    rows = frappe.db.sql(
        """
        SELECT
            TIMESTAMPDIFF(HOUR, date_reported, {end_expr}) AS hours_taken
        FROM `tabFacility Work Order`
        WHERE workflow_state = 'Closed'
          AND date_reported IS NOT NULL
          AND {end_expr} IS NOT NULL
        """.format(end_expr=end_expr),
        as_dict=True
    )

    valid = [
        flt(row.hours_taken)
        for row in rows
        if row.hours_taken is not None and flt(row.hours_taken) >= 0
    ]

    if not valid:
        return 0

    return round(sum(valid) / len(valid), 1)


def get_group_counts(fieldname):
    if not frappe.db.has_column("Facility Work Order", fieldname):
        return []

    rows = frappe.db.sql(
        """
        SELECT
            IFNULL({fieldname}, 'Not Set') AS label,
            COUNT(name) AS value
        FROM `tabFacility Work Order`
        GROUP BY IFNULL({fieldname}, 'Not Set')
        ORDER BY value DESC
        """.format(fieldname=fieldname),
        as_dict=True
    )

    return rows


def get_active_priority_levels():
    if not frappe.db.has_column("Facility Work Order", "priority"):
        return []

    rows = frappe.db.sql(
        """
        SELECT
            IFNULL(priority, 'Not Set') AS label,
            COUNT(name) AS value
        FROM `tabFacility Work Order`
        WHERE workflow_state IN %(open_states)s
        GROUP BY IFNULL(priority, 'Not Set')
        ORDER BY
            CASE
                WHEN priority = 'Emergency' THEN 1
                WHEN priority = 'Urgent' THEN 2
                WHEN priority = 'Routine' THEN 3
                ELSE 4
            END
        """,
        {"open_states": OPEN_STATES},
        as_dict=True
    )

    return rows


def get_department_breakdown():
    if not frappe.db.has_column("Facility Work Order", "requesting_department"):
        return []

    rows = frappe.db.sql(
        """
        SELECT
            IFNULL(requesting_department, 'Not Set') AS label,
            COUNT(name) AS total,
            SUM(CASE WHEN workflow_state IN %(open_states)s THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN workflow_state = 'Closed' THEN 1 ELSE 0 END) AS closed_count
        FROM `tabFacility Work Order`
        GROUP BY IFNULL(requesting_department, 'Not Set')
        ORDER BY total DESC
        LIMIT 8
        """,
        {"open_states": OPEN_STATES},
        as_dict=True
    )

    return rows


def get_daily_trend(start_date, today):
    rows = frappe.db.sql(
        """
        SELECT
            DATE(date_reported) AS report_date,
            COUNT(name) AS total,
            SUM(CASE WHEN workflow_state = 'Closed' THEN 1 ELSE 0 END) AS closed_count
        FROM `tabFacility Work Order`
        WHERE DATE(date_reported) BETWEEN %(start_date)s AND %(today)s
        GROUP BY DATE(date_reported)
        ORDER BY DATE(date_reported)
        """,
        {
            "start_date": start_date,
            "today": today
        },
        as_dict=True
    )

    row_map = {}
    for row in rows:
        row_map[str(row.report_date)] = row

    output = []
    current = getdate(start_date)

    while current <= getdate(today):
        key = str(current)
        row = row_map.get(key)

        output.append({
            "date": key,
            "label": current.strftime("%d %b"),
            "total": row.total if row else 0,
            "closed": row.closed_count if row else 0
        })

        current = add_days(current, 1)

    return output


def get_aging(today):
    work_orders = frappe.get_all(
        "Facility Work Order",
        filters={"workflow_state": ["in", OPEN_STATES]},
        fields=["name", "date_reported", "priority", "workflow_state"]
    )

    buckets = {
        "0-1 Days": 0,
        "2-3 Days": 0,
        "4-7 Days": 0,
        "8+ Days": 0
    }

    for row in work_orders:
        if not row.get("date_reported"):
            continue

        age = date_diff(today, getdate(row.date_reported))

        if age <= 1:
            buckets["0-1 Days"] += 1
        elif age <= 3:
            buckets["2-3 Days"] += 1
        elif age <= 7:
            buckets["4-7 Days"] += 1
        else:
            buckets["8+ Days"] += 1

    return [{"label": key, "value": value} for key, value in buckets.items()]


def get_sla_summary(today):
    rows = frappe.get_all(
        "Facility Work Order",
        filters={"workflow_state": ["in", OPEN_STATES]},
        fields=["name", "priority", "date_reported"]
    )

    breached = 0
    warning = 0
    healthy = 0

    for row in rows:
        if not row.date_reported:
            healthy += 1
            continue

        age = date_diff(today, getdate(row.date_reported))
        priority = row.priority or "Routine"

        if priority == "Emergency":
            limit = 1
        elif priority == "Urgent":
            limit = 2
        else:
            limit = 7

        if age > limit:
            breached += 1
        elif age == limit:
            warning += 1
        else:
            healthy += 1

    return {
        "healthy": healthy,
        "warning": warning,
        "breached": breached
    }


def get_technician_workload():
    if not frappe.db.has_column("Facility Work Order", "assigned_technician"):
        return []

    rows = frappe.db.sql(
        """
        SELECT
            assigned_technician,
            COUNT(name) AS total_assigned,
            SUM(CASE WHEN workflow_state IN %(open_states)s THEN 1 ELSE 0 END) AS active_orders,
            SUM(CASE WHEN workflow_state = 'Closed' THEN 1 ELSE 0 END) AS closed_orders
        FROM `tabFacility Work Order`
        WHERE assigned_technician IS NOT NULL
          AND assigned_technician != ''
        GROUP BY assigned_technician
        ORDER BY active_orders DESC, total_assigned DESC
        LIMIT 10
        """,
        {"open_states": OPEN_STATES},
        as_dict=True
    )

    for row in rows:
        row["technician_name"] = get_technician_name(row.assigned_technician)

    return rows


def get_technician_name(technician):
    if not technician:
        return "Unassigned"

    if frappe.db.exists("DocType", "Maintenance Technician"):
        value = (
            frappe.db.get_value("Maintenance Technician", technician, "technician_name")
            or frappe.db.get_value("Maintenance Technician", technician, "employee_name")
        )
        if value:
            return value

    return technician


def get_location_type_breakdown():
    if not frappe.db.has_column("Facility Work Order", "location_type"):
        return []

    rows = frappe.db.sql(
        """
        SELECT
            IFNULL(location_type, 'Not Set') AS label,
            COUNT(name) AS value
        FROM `tabFacility Work Order`
        GROUP BY IFNULL(location_type, 'Not Set')
        ORDER BY value DESC
        """,
        as_dict=True
    )

    return rows


def get_linked_document_summary():
    linked_doctypes = [
        "Vehicle Maintenance Report",
        "Equipment Repair Authorization",
        "Machine Access Log",
        "Removed Parts Register",
        "Asset Repair"
    ]

    output = []

    for doctype in linked_doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue

        if not frappe.db.has_column(doctype, "facility_work_order"):
            continue

        total = frappe.db.count(doctype)

        submitted = 0
        draft = 0
        cancelled = 0

        if frappe.db.has_column(doctype, "docstatus"):
            submitted = frappe.db.count(doctype, {"docstatus": 1})
            draft = frappe.db.count(doctype, {"docstatus": 0})
            cancelled = frappe.db.count(doctype, {"docstatus": 2})

        output.append({
            "doctype": doctype,
            "total": total,
            "submitted": submitted,
            "draft": draft,
            "cancelled": cancelled
        })

    return output


def get_recent_work_orders():
    fields = [
        "name",
        "workflow_state",
        "priority",
        "category",
        "requesting_department",
        "contact_person",
        "date_reported",
        "location_type",
        "room",
        "asset_location",
        "location_description",
        "asset",
        "modified"
    ]

    if frappe.db.has_column("Facility Work Order", "assigned_technician"):
        fields.append("assigned_technician")

    rows = frappe.get_all(
        "Facility Work Order",
        fields=fields,
        order_by="modified desc",
        limit_page_length=10
    )

    enrich_work_orders(rows)
    return rows


def get_urgent_work_orders(today):
    rows = frappe.get_all(
        "Facility Work Order",
        filters={
            "workflow_state": ["in", OPEN_STATES],
            "priority": ["in", ["Urgent", "Emergency"]]
        },
        fields=[
            "name",
            "workflow_state",
            "priority",
            "category",
            "requesting_department",
            "contact_person",
            "date_reported",
            "location_type",
            "room",
            "asset_location",
            "location_description",
            "asset"
        ],
        order_by="date_reported asc",
        limit_page_length=8
    )

    enrich_work_orders(rows)

    for row in rows:
        row["age_days"] = date_diff(today, getdate(row.date_reported)) if row.date_reported else 0

    return rows


def get_top_locations():
    rows = frappe.get_all(
        "Facility Work Order",
        filters={"workflow_state": ["in", OPEN_STATES]},
        fields=[
            "name",
            "location_type",
            "room",
            "asset_location",
            "location_description"
        ],
        limit_page_length=500
    )

    counts = {}

    for row in rows:
        location = get_location_display(row)
        counts[location] = counts.get(location, 0) + 1

    output = []
    for location, count in counts.items():
        output.append({
            "location": location,
            "open_work_orders": count
        })

    output.sort(key=lambda x: x["open_work_orders"], reverse=True)
    return output[:8]


def enrich_work_orders(rows):
    employee_cache = {}
    room_cache = {}

    for row in rows:
        row["location_display"] = get_location_display(row, room_cache)

        if row.get("contact_person"):
            if row.contact_person not in employee_cache:
                employee_cache[row.contact_person] = (
                    frappe.db.get_value("Employee", row.contact_person, "employee_name")
                    or row.contact_person
                )
            row["contact_person_name"] = employee_cache[row.contact_person]
        else:
            row["contact_person_name"] = None

        if row.get("assigned_technician"):
            row["technician_name"] = get_technician_name(row.assigned_technician)
        else:
            row["technician_name"] = "Unassigned"


def get_location_display(row, room_cache=None):
    if room_cache is None:
        room_cache = {}

    location_type = row.get("location_type")

    if location_type == "Room":
        room = row.get("room")
        if not room:
            return "Room"

        if room not in room_cache:
            room_cache[room] = frappe.db.get_value("Hotel Room", room, "room_number") or room

        return "Room " + str(room_cache[room])

    if location_type == "Asset Location":
        return row.get("asset_location") or "Asset Location"

    if location_type == "Other Location":
        return row.get("location_description") or "Other Location"

    return row.get("asset") or "Not Set"


def get_stats_alias(today):
    summary = get_summary(today)
    secondary = get_secondary_cards(today)

    urgent_count = 0
    emergency_count = 0

    for row in get_active_priority_levels():
        if row.label == "Urgent":
            urgent_count = row.value
        if row.label == "Emergency":
            emergency_count = row.value

    return {
        "total": summary["total"],
        "active": summary["open"],
        "emergency_active": emergency_count,
        "closed_this_week": 0,
        "closed_this_month": 0,
        "avg_resolution_hrs": summary["avg_resolution_hours"],
        "overdue": secondary["overdue"],
        "unassigned": secondary["unassigned"],
        "closed": summary["closed"],
        "rejected": summary["rejected"],
        "cancelled": summary["cancelled"],
        "urgent_active": urgent_count
    }