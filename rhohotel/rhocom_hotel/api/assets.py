import frappe


@frappe.whitelist()
def get_asset_dashboard():
    """Stats for the asset dashboard page."""
    total = frappe.db.count("Asset", {"docstatus": 1, "name": ["not like", "_Test%"]})

    # Count by status
    submitted = frappe.db.count("Asset", {"docstatus": 1, "status": "Submitted", "name": ["not like", "_Test%"]})
    in_maintenance = frappe.db.count("Asset", {"docstatus": 1, "status": "In Maintenance", "name": ["not like", "_Test%"]})
    scrapped = frappe.db.count("Asset", {"docstatus": 1, "status": "Scrapped", "name": ["not like", "_Test%"]})
    draft = frappe.db.count("Asset", {"docstatus": 0, "name": ["not like", "_Test%"]})

    # ── Asset Category Analytics ─────────────────────────────────────────
    category_rows = frappe.db.sql("""
        SELECT asset_category, COUNT(*) as cnt
        FROM `tabAsset`
        WHERE docstatus = 1 AND name NOT LIKE '_Test%%'
        GROUP BY asset_category
        ORDER BY cnt DESC
    """, as_dict=1)

    categories = []
    for row in category_rows:
        cat = row.asset_category or "Uncategorised"
        pct = round(row.cnt / total * 100, 1) if total else 0
        categories.append({"label": cat, "count": row.cnt, "pct": pct})

    # ── Location with highest asset count ────────────────────────────────
    location_rows = frappe.db.sql("""
        SELECT location, COUNT(*) as cnt
        FROM `tabAsset`
        WHERE docstatus = 1 AND name NOT LIKE '_Test%%' AND location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY cnt DESC
        LIMIT 6
    """, as_dict=1)

    locations = []
    max_loc_count = location_rows[0].cnt if location_rows else 1
    for row in location_rows:
        pct = round(row.cnt / max_loc_count * 100, 1)
        locations.append({"label": row.location, "count": row.cnt, "pct": pct})

    # ── Assets with highest activity ─────────────────────────────────────
    activity_rows = frappe.db.sql("""
        SELECT a.asset, ast.asset_name, COUNT(*) as cnt
        FROM `tabAsset Activity` a
        LEFT JOIN `tabAsset` ast ON ast.name = a.asset
        WHERE a.asset NOT LIKE '_Test%%'
        GROUP BY a.asset
        ORDER BY cnt DESC
        LIMIT 5
    """, as_dict=1)

    top_active_assets = []
    max_activity = activity_rows[0].cnt if activity_rows else 1
    for row in activity_rows:
        pct = round(row.cnt / max_activity * 100, 1)
        top_active_assets.append({
            "asset": row.asset,
            "asset_name": row.asset_name or row.asset,
            "count": row.cnt,
            "pct": pct,
        })

    # ── Recent Asset Activity (latest 5) ─────────────────────────────────
    recent_rows = frappe.db.sql("""
        SELECT a.asset, ast.asset_name, a.subject, a.date, a.user
        FROM `tabAsset Activity` a
        LEFT JOIN `tabAsset` ast ON ast.name = a.asset
        WHERE a.asset NOT LIKE '_Test%%'
        ORDER BY a.date DESC
        LIMIT 5
    """, as_dict=1)

    recent_activities = []
    for row in recent_rows:
        user_name = frappe.db.get_value("User", row.user, "full_name") or row.user
        recent_activities.append({
            "asset": row.asset,
            "asset_name": row.asset_name or row.asset,
            "subject": row.subject,
            "date": row.date,
            "user": user_name,
        })

    return {
        "total": total,
        "submitted": submitted,
        "in_maintenance": in_maintenance,
        "scrapped": scrapped,
        "draft": draft,
        "categories": categories,
        "locations": locations,
        "top_active_assets": top_active_assets,
        "recent_activities": recent_activities,
    }


@frappe.whitelist()
def get_asset_list(
    search=None,
    filter_status=None,
    filter_category=None,
    filter_location=None,
    page=1,
    page_size=25,
):
    """Paginated asset list."""
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page, page_size = 1, 25

    filters = [["name", "not like", "_Test%"]]

    # Only show submitted assets by default unless a specific status is selected
    if filter_status:
        if filter_status == "Draft":
            filters.append(["docstatus", "=", 0])
        else:
            filters.append(["docstatus", "=", 1])
            filters.append(["status", "=", filter_status])
    else:
        filters.append(["docstatus", "in", [0, 1]])

    if filter_category:
        filters.append(["asset_category", "=", filter_category])
    if filter_location:
        filters.append(["location", "=", filter_location])

    fields = [
        "name", "asset_name", "asset_category", "location", "status",
        "company", "item_code", "item_name", "custodian", "department",
        "purchase_date", "gross_purchase_amount", "docstatus",
        "owner", "creation", "modified",
    ]

    if search:
        q = f"%{search}%"
        assets = frappe.db.sql("""
            SELECT {fields}
            FROM `tabAsset`
            WHERE (name LIKE %(q)s OR asset_name LIKE %(q)s
                   OR item_code LIKE %(q)s OR item_name LIKE %(q)s
                   OR location LIKE %(q)s OR asset_category LIKE %(q)s)
            {extra_filters}
            ORDER BY modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """.format(
            fields=", ".join(fields),
            extra_filters=_build_extra_sql(filters),
        ), {
            "q": q,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }, as_dict=1)

        count_result = frappe.db.sql("""
            SELECT COUNT(*) as cnt
            FROM `tabAsset`
            WHERE (name LIKE %(q)s OR asset_name LIKE %(q)s
                   OR item_code LIKE %(q)s OR item_name LIKE %(q)s
                   OR location LIKE %(q)s OR asset_category LIKE %(q)s)
            {extra_filters}
        """.format(extra_filters=_build_extra_sql(filters)), {"q": q}, as_dict=1)
        total = count_result[0].cnt if count_result else 0
    else:
        assets = frappe.get_all(
            "Asset",
            filters=filters,
            fields=fields,
            order_by="modified desc",
            limit_page_length=page_size,
            limit_start=(page - 1) * page_size,
        )
        total = frappe.db.count("Asset", filters)

    for asset in assets:
        asset["created_by"] = (
            frappe.db.get_value("User", asset.get("owner"), "full_name")
            or asset.get("owner")
        )
        # Resolve custodian name
        if asset.get("custodian"):
            asset["custodian_name"] = frappe.db.get_value(
                "Employee", asset["custodian"], "employee_name"
            )
        else:
            asset["custodian_name"] = None

    return {
        "assets": assets,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


def _build_extra_sql(filters):
    """Build SQL AND clauses from list-of-lists filters."""
    clauses = []
    for f in filters:
        field, op, value = f
        if op == "not like":
            clauses.append(f"AND {field} NOT LIKE '{value}'")
        elif op == "=":
            clauses.append(f"AND {field} = '{value}'")
        elif op == "in":
            vals = ",".join(str(v) for v in value)
            clauses.append(f"AND docstatus IN ({vals})")
    return "\n".join(clauses)


@frappe.whitelist()
def get_asset_detail(asset_name):
    """Full asset detail for the detail page."""
    if not frappe.db.exists("Asset", asset_name):
        frappe.throw(f"Asset '{asset_name}' not found", frappe.DoesNotExistError)

    doc = frappe.get_doc("Asset", asset_name)

    # Resolve custodian name
    custodian_name = None
    if doc.get("custodian"):
        custodian_name = frappe.db.get_value("Employee", doc.custodian, "employee_name")

    # Get recent activity for this asset
    activities = frappe.db.sql("""
        SELECT subject, date, user
        FROM `tabAsset Activity`
        WHERE asset = %(asset)s
        ORDER BY date DESC
        LIMIT 10
    """, {"asset": asset_name}, as_dict=1)

    for a in activities:
        a["user_name"] = frappe.db.get_value("User", a["user"], "full_name") or a["user"]

    # Get linked repairs
    repairs = frappe.get_all(
        "Asset Repair",
        filters={"asset": asset_name, "name": ["not like", "_Test%"]},
        fields=["name", "repair_status", "failure_date", "completion_date", "rh_approved", "creation"],
        order_by="creation desc",
        limit_page_length=10,
    )

    # Get linked maintenance
    maintenances = frappe.get_all(
        "Asset Maintenance",
        filters={"asset_name": asset_name, "name": ["not like", "_Test%"]},
        fields=["name", "docstatus", "rh_approved", "creation"],
        order_by="creation desc",
        limit_page_length=10,
    )

    return {
        "name": doc.name,
        "asset_name": doc.asset_name,
        "item_code": doc.item_code,
        "item_name": doc.item_name,
        "asset_category": doc.asset_category,
        "company": doc.company,
        "location": doc.location,
        "custodian": doc.custodian,
        "custodian_name": custodian_name,
        "department": doc.department,
        "status": doc.status,
        "docstatus": doc.docstatus,
        "purchase_date": doc.purchase_date,
        "available_for_use_date": doc.available_for_use_date,
        "gross_purchase_amount": doc.gross_purchase_amount,
        "asset_quantity": doc.asset_quantity,
        "calculate_depreciation": doc.calculate_depreciation,
        "value_after_depreciation": doc.value_after_depreciation,
        "maintenance_required": doc.maintenance_required,
        "policy_number": doc.policy_number,
        "insurer": doc.insurer,
        "insured_value": doc.insured_value,
        "insurance_start_date": doc.insurance_start_date,
        "insurance_end_date": doc.insurance_end_date,
        "owner": doc.owner,
        "created_by": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
        "creation": doc.creation,
        "modified": doc.modified,
        "activities": activities,
        "repairs": repairs,
        "maintenances": maintenances,
    }


@frappe.whitelist()
def get_asset_categories():
    """Get distinct asset categories for filter dropdown."""
    rows = frappe.db.sql("""
        SELECT DISTINCT asset_category
        FROM `tabAsset`
        WHERE docstatus IN (0, 1) AND name NOT LIKE '_Test%%'
          AND asset_category IS NOT NULL AND asset_category != ''
        ORDER BY asset_category
    """, as_dict=1)
    return [r.asset_category for r in rows]


@frappe.whitelist()
def get_asset_locations():
    """Get distinct locations for filter dropdown."""
    rows = frappe.db.sql("""
        SELECT DISTINCT location
        FROM `tabAsset`
        WHERE docstatus IN (0, 1) AND name NOT LIKE '_Test%%'
          AND location IS NOT NULL AND location != ''
        ORDER BY location
    """, as_dict=1)
    return [r.location for r in rows]


@frappe.whitelist()
def get_asset_statuses():
    """Get distinct statuses for filter dropdown."""
    rows = frappe.db.sql("""
        SELECT DISTINCT status
        FROM `tabAsset`
        WHERE docstatus IN (0, 1) AND name NOT LIKE '_Test%%'
          AND status IS NOT NULL AND status != ''
        ORDER BY status
    """, as_dict=1)
    return [r.status for r in rows]
