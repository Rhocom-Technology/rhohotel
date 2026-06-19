import frappe
from frappe.utils import cstr, getdate, add_days, format_time


def _get_default_company():
    return frappe.defaults.get_global_default("company") or frappe.db.get_value(
        "Company", {}, "name", order_by="creation asc"
    )


def _short_department(department):
    value = cstr(department or "")
    return value.split(" - ")[0].strip() if " - " in value else value


def _week_start(value=None):
    d = getdate(value) if value else getdate()
    return add_days(d, -d.weekday())


def _week_dates(week_start):
    start = _week_start(week_start)
    return [add_days(start, i) for i in range(7)]


@frappe.whitelist()
def get_dashboard(week_start=None):
    company = _get_default_company()
    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    today = getdate()
    today_str = cstr(today)

    week_label = f"{week_start_dt.strftime('%d %b')} - {week_end_dt.strftime('%d %b %Y')}"
    today_label = today.strftime("%A, %d %b %Y")

    # --- Published Shifts Today / This Week, and shift-day expansion -------
    # Mirrors the day-expansion approach used in shift_list.get_shift_stats:
    # a single multi-day Shift Assignment contributes one entry per day it
    # actually covers within the requested range, not one entry total.
    rows = frappe.db.sql(
        """
        SELECT sa.employee, sa.shift_type, sa.start_date, sa.end_date, sa.status, emp.department,
               st.start_time
        FROM `tabShift Assignment` sa
        INNER JOIN `tabEmployee` emp ON emp.name = sa.employee
        LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
        WHERE sa.docstatus = 1
          AND emp.status = 'Active'
          AND (%(company)s = '' OR emp.company = %(company)s)
          AND sa.start_date <= %(week_end)s
          AND IFNULL(sa.end_date, sa.start_date) >= %(week_start)s
        """,
        {"company": company or "", "week_start": week_start_dt, "week_end": week_end_dt},
        as_dict=True,
    )

    published_days = []
    today_rows = []
    for row in rows:
        start = max(getdate(row.start_date), week_start_dt)
        end = min(getdate(row.end_date or row.start_date), week_end_dt)
        day = start
        while day <= end:
            entry = {
                "employee": row.employee,
                "shift_type": row.shift_type,
                "status": row.status,
                "department": _short_department(row.department),
                "start_time": row.start_time,
                "date": cstr(day),
            }
            published_days.append(entry)
            if cstr(day) == today_str:
                today_rows.append(entry)
            day = add_days(day, 1)

    published_today = len(today_rows)

    # --- Weekly Coverage (a day is a conflict if any Shift Type in the
    # system has zero coverage that day; coverage = conflict-free days / 7) -
    all_shift_type_names = [r.name for r in frappe.get_all("Shift Type", fields=["name"], order_by="name asc")]
    total_shift_types = len(all_shift_type_names)
    conflict_days = 0
    for day in week_dates:
        day_str = cstr(day)
        covered = {d["shift_type"] for d in published_days if d["date"] == day_str and d["shift_type"]}
        if total_shift_types == 0 or len(covered) < total_shift_types:
            conflict_days += 1
    weekly_coverage = round(((7 - conflict_days) / 7) * 100)

    # --- Preference Submitted / Total --------------------------------------
    pref_rows = frappe.db.sql(
        """
        SELECT status, COUNT(*) AS total
        FROM `tabStaff Shift Preference`
        WHERE week_start = %(week_start)s
          AND (%(company)s = '' OR company = %(company)s)
        GROUP BY status
        """,
        {"week_start": week_start_dt, "company": company or ""},
        as_dict=True,
    )
    preference_submitted = sum(r.total for r in pref_rows if r.status == "Submitted")
    preference_draft = sum(r.total for r in pref_rows if r.status == "Draft")

    preference_total = frappe.db.count(
        "Employee",
        {"status": "Active", "company": company} if company else {"status": "Active"},
    )

    # --- Swap Requests Pending ----------------------------------------------
    # Shift Swap Request has no company field, so this is intentionally
    # company-agnostic (counts all pending swap requests system-wide).
    swap_pending = frappe.db.count("Shift Swap Request", {"status": "Pending"})

    # --- Today's Shift Split (one entry per real Shift Type name) -----------
    shift_split_today = {name: 0 for name in all_shift_type_names}
    for row in today_rows:
        if row["shift_type"] in shift_split_today:
            shift_split_today[row["shift_type"]] += 1
        elif row["shift_type"]:
            # A shift type that's been assigned but no longer exists as a
            # Shift Type record (e.g. deleted/renamed) -- still surface it
            # rather than silently dropping the count.
            shift_split_today[row["shift_type"]] = shift_split_today.get(row["shift_type"], 0) + 1

    # --- This Week's Shift Split (same, across all 7 days) ------------------
    shift_split_week = {name: 0 for name in all_shift_type_names}
    for row in published_days:
        if row["shift_type"]:
            shift_split_week[row["shift_type"]] = shift_split_week.get(row["shift_type"], 0) + 1

    # --- Table 1: Shift Type totals per day (pivot: shift type x day) -------
    shift_type_by_day = {
        name: {cstr(d): 0 for d in week_dates} for name in all_shift_type_names
    }
    for row in published_days:
        st = row["shift_type"]
        if not st:
            continue
        if st not in shift_type_by_day:
            shift_type_by_day[st] = {cstr(d): 0 for d in week_dates}
        shift_type_by_day[st][row["date"]] += 1

    shift_type_table = [
        {"shift_type": name, "days": days, "total": sum(days.values())}
        for name, days in sorted(shift_type_by_day.items())
    ]

    # --- Today's Department Overview: which shift types were covered today,
    # per department --------------------------------------------------------
    dept_today = {}
    for row in today_rows:
        dept = row["department"] or "Unassigned"
        dept_today.setdefault(dept, set())
        if row["shift_type"]:
            dept_today[dept].add(row["shift_type"])

    dept_overview = []
    for dept, covered in sorted(dept_today.items()):
        if not covered:
            coverage = "Gap"
        elif total_shift_types and len(covered) >= total_shift_types:
            coverage = "Covered"
        else:
            coverage = "Watch"
        dept_overview.append({
            "department": dept,
            "shift_types": sorted(covered),
            "coverage": coverage,
        })

    # --- Table 2: per department, per day, staff with published assignment -
    # Count unique employees that have a published Shift Assignment on each
    # day, regardless of assignment status.
    dept_week = {}
    for row in published_days:
        dept = row["department"] or "Unassigned"
        if dept not in dept_week:
            dept_week[dept] = {cstr(d): set() for d in week_dates}
        if row.get("employee") and row.get("shift_type"):
            dept_week[dept][row["date"]].add(row["employee"])

    dept_overview_week = []
    for dept, days in sorted(dept_week.items()):
        zero_days = sum(1 for v in days.values() if not v)
        if zero_days >= 4:
            coverage = "Gap"
        elif zero_days >= 1:
            coverage = "Watch"
        else:
            coverage = "Covered"
        dept_overview_week.append({
            "department": dept,
            "days": {d: sorted(v) for d, v in days.items()},
            "coverage": coverage,
        })

    # --- Table 3: per department, per day, number of published shifts -----
    # Count all published shift assignments for the week (docstatus=1),
    # regardless of assignment status, to reflect total shift volume.
    dept_shift_count_week_map = {}
    for row in published_days:
        if not row.get("shift_type"):
            continue
        dept = row["department"] or "Unassigned"
        if dept not in dept_shift_count_week_map:
            dept_shift_count_week_map[dept] = {cstr(d): 0 for d in week_dates}
        dept_shift_count_week_map[dept][row["date"]] += 1

    dept_shift_count_week = [
        {"department": dept, "days": days}
        for dept, days in sorted(dept_shift_count_week_map.items())
    ]

    return {
        "company": company or "",
        "week_start": cstr(week_start_dt),
        "week_end": cstr(week_end_dt),
        "week_label": week_label,
        "today_label": today_label,
        "today_date": today.strftime("%d %b %Y"),
        "week_dates": [cstr(d) for d in week_dates],
        "shift_type_names": all_shift_type_names,
        "stats": {
            "publishedToday": published_today,
            "publishedThisWeek": len(published_days),
            "weeklyCoverage": weekly_coverage,
            "preferenceSubmitted": preference_submitted,
            "preferenceTotal": preference_total,
            "swapRequestsPending": swap_pending,
        },
        "shiftSplitToday": shift_split_today,
        "shiftSplitWeek": shift_split_week,
        "shiftTypeTable": shift_type_table,
        "deptOverview": dept_overview,
        "deptOverviewWeek": dept_overview_week,
        "deptShiftCountWeek": dept_shift_count_week,
    }