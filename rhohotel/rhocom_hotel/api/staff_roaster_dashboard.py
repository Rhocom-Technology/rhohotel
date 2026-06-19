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


def _classify_shift_bucket(shift_type, start_time):
    """Buckets a Shift Type into Morning / Afternoon / Night for the
    'Today's Shift Split' card, based on its configured start_time.
    Falls back to name-matching if start_time isn't available, consistent
    with how WeeklyShiftGenerator.vue colors shift cells by name.
    """
    name = cstr(shift_type or "").lower()
    if "night" in name:
        return "night"
    if "afternoon" in name or "evening" in name:
        return "afternoon"
    if "morning" in name or "day" in name:
        return "morning"

    if start_time is not None:
        try:
            hour = int(cstr(start_time).split(":")[0])
            if hour < 12:
                return "morning"
            if hour < 18:
                return "afternoon"
            return "night"
        except (ValueError, IndexError):
            pass

    return "morning"


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
        SELECT sa.employee, sa.shift_type, sa.start_date, sa.end_date, emp.department,
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
                "department": _short_department(row.department),
                "start_time": row.start_time,
                "date": cstr(day),
            }
            published_days.append(entry)
            if cstr(day) == today_str:
                today_rows.append(entry)
            day = add_days(day, 1)

    published_today = len(today_rows)

    # --- Weekly Coverage (reuses the same definition as Weekly Shift
    # Generator: a day is a conflict if any Shift Type in the system has
    # zero coverage that day; coverage = conflict-free days / 7) ----------
    total_shift_types = frappe.db.count("Shift Type")
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

    # --- Today's Shift Split (Morning / Afternoon / Night) ------------------
    shift_split = {"morning": 0, "afternoon": 0, "night": 0}
    for row in today_rows:
        bucket = _classify_shift_bucket(row["shift_type"], row["start_time"])
        shift_split[bucket] += 1

    # --- Department Overview (today, per department) ------------------------
    dept_today = {}
    for row in today_rows:
        dept = row["department"] or "Unassigned"
        bucket = _classify_shift_bucket(row["shift_type"], row["start_time"])
        if dept not in dept_today:
            dept_today[dept] = {"morning": 0, "afternoon": 0, "night": 0}
        dept_today[dept][bucket] += 1

    dept_overview = []
    for dept, counts in sorted(dept_today.items()):
        total = counts["morning"] + counts["afternoon"] + counts["night"]
        if total == 0:
            coverage = "Gap"
        elif counts["morning"] and counts["afternoon"] and counts["night"]:
            coverage = "Covered"
        else:
            coverage = "Watch"
        dept_overview.append({
            "department": dept,
            "morning": counts["morning"],
            "afternoon": counts["afternoon"],
            "night": counts["night"],
            "coverage": coverage,
        })

    return {
        "company": company or "",
        "week_start": cstr(week_start_dt),
        "week_end": cstr(week_end_dt),
        "week_label": week_label,
        "today_label": today_label,
        "today_date": today.strftime("%d %b %Y"),
        "stats": {
            "publishedToday": published_today,
            "weeklyCoverage": weekly_coverage,
            "preferenceSubmitted": preference_submitted,
            "preferenceTotal": preference_total,
            "swapRequestsPending": swap_pending,
        },
        "shiftSplit": shift_split,
        "deptOverview": dept_overview,
    }