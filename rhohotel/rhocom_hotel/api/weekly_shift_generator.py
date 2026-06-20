# import json

# import frappe
# from frappe import _
# from frappe.utils import cstr, getdate, add_days, format_time

# # ---------------------------------------------------------------------------
# # Weekly Shift Generator API
# #
# # Backs frontend/src/pages/shift/WeeklyShiftGenerator.vue
# # ---------------------------------------------------------------------------


# def _week_dates(week_start):
#     start = getdate(week_start) if week_start else getdate(frappe.utils.nowdate())
#     return [add_days(start, i) for i in range(7)]


# def _short_department(department):
#     value = cstr(department or "")
#     return value.split(" - ")[0].strip() if " - " in value else value


# def _normalize_department(department):
#     return cstr(department or "").strip()


# def _format_shift_time(start_time, end_time):
#     if start_time is None or end_time is None:
#         return ""
#     try:
#         return f"{format_time(start_time, 'hh:mm a')} - {format_time(end_time, 'hh:mm a')}"
#     except Exception:
#         return ""


# def _get_default_company():
#     return frappe.defaults.get_global_default("company") or frappe.db.get_value(
#         "Company", {}, "name", order_by="creation asc"
#     )


# @frappe.whitelist()
# def get_departments():
#     """Return distinct active department names for the department dropdown,
#     scoped to the default company only -- matches the Shift List page and
#     avoids leaking departments from other companies (e.g. _Test Company)
#     into the dropdown."""
#     default_company = _get_default_company()

#     rows = frappe.db.sql(
#         """
#         SELECT DISTINCT department AS value
#         FROM `tabEmployee`
#         WHERE status = 'Active'
#           AND IFNULL(department, '') != ''
#           AND (%(company)s = '' OR company = %(company)s)
#         ORDER BY department
#         """,
#         {"company": default_company or ""},
#         as_dict=1,
#     )

#     departments = []
#     for row in rows:
#         label = _short_department(row.get("value"))
#         if label and label not in departments:
#             departments.append(label)

#     return departments


# @frappe.whitelist()
# def get_weekly_roster(department=None, week_start=None):
#     week_dates = _week_dates(week_start)
#     week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
#     department = _normalize_department(department)
#     default_company = _get_default_company()

#     employees = frappe.db.sql(
#         """
#         SELECT
#             name AS employee,
#             employee_name,
#             designation,
#             department
#         FROM `tabEmployee`
#         WHERE status = 'Active'
#           AND (%(company)s = '' OR company = %(company)s)
#           AND (%(department)s = '' OR department LIKE %(department_like)s)
#         ORDER BY employee_name
#         """,
#         {
#             "company": default_company or "",
#             "department": department,
#             "department_like": f"%{department}%",
#         },
#         as_dict=1,
#     )

#     employee_names = [e.employee for e in employees]

#     assignment_map = {}
#     if employee_names:
#         rows = frappe.db.sql(
#             """
#             SELECT
#                 sa.employee,
#                 sa.shift_type,
#                 sa.start_date,
#                 sa.end_date,
#                 sa.status,
#                 st.start_time,
#                 st.end_time
#             FROM `tabShift Assignment` sa
#             LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
#             WHERE sa.employee IN %(employees)s
#               AND sa.start_date <= %(end)s
#               AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
#               AND sa.docstatus = 1
#             """,
#             {
#                 "employees": employee_names,
#                 "start": week_start_dt,
#                 "end": week_end_dt,
#             },
#             as_dict=1,
#         )

#         for row in rows:
#             row_start = row.start_date
#             row_end = row.end_date or row.start_date
#             if row_end < row_start:
#                 row_end = row_start
#             for day in week_dates:
#                 if row_start <= day <= row_end:
#                     assignment_map.setdefault(row.employee, {})[cstr(day)] = {
#                         "shift_type": row.shift_type,
#                         "status": row.status,
#                         "time": _format_shift_time(row.start_time, row.end_time),
#                     }

#     staff = []
#     for emp in employees:
#         shifts = {}
#         for day in week_dates:
#             key = cstr(day)
#             entry = assignment_map.get(emp.employee, {}).get(key)

#             if not entry:
#                 shifts[key] = {"shift_type": "OFF", "status": "Off", "time": ""}
#             elif entry["status"] == "Inactive":
#                 shifts[key] = {"shift_type": entry["shift_type"], "status": "Leave", "time": entry["time"]}
#             else:
#                 shifts[key] = {
#                     "shift_type": entry["shift_type"],
#                     "status": "Active",
#                     "time": entry["time"],
#                 }

#         staff.append({
#             "employee": emp.employee,
#             "employee_name": emp.employee_name,
#             "designation": emp.designation or "",
#             "area": _short_department(emp.department),
#             "shifts": shifts,
#         })

#     total_slots = len(staff) * 7
#     assigned_slots = sum(
#         1
#         for row in staff
#         for value in row["shifts"].values()
#         if value["status"] == "Active"
#     )
#     coverage_level = round((assigned_slots / total_slots) * 100) if total_slots else 0

#     return {
#         "staff": staff,
#         "stats": {
#             "coverage_level": coverage_level,
#             "conflict_alerts": _count_conflicts(staff),
#             "total_slots": total_slots,
#             "assigned_slots": assigned_slots,
#         },
#     }


# def _count_conflicts(staff):
#     conflicts = 0
#     for row in staff:
#         shifts = row["shifts"]
#         leave_days = [d for d, v in shifts.items() if v["status"] == "Leave"]
#         working_days = [d for d, v in shifts.items() if v["status"] == "Active"]
#         if leave_days and len(working_days) >= 6:
#             conflicts += 1
#     return conflicts


# @frappe.whitelist()
# def get_shift_types():
#     shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")

#     options = [{"value": row.name, "label": row.name} for row in shift_types]
#     options.append({"value": "OFF", "label": "OFF"})

#     return options


# @frappe.whitelist()
# def get_weekly_draft(department=None, week_start=None):
#     week_dates = _week_dates(week_start)
#     week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
#     department = _normalize_department(department)
#     default_company = _get_default_company()

#     employees = frappe.db.sql(
#         """
#         SELECT
#             name AS employee,
#             employee_name,
#             designation,
#             department
#         FROM `tabEmployee`
#         WHERE status = 'Active'
#           AND (%(company)s = '' OR company = %(company)s)
#           AND (%(department)s = '' OR department LIKE %(department_like)s)
#         ORDER BY employee_name
#         """,
#         {
#             "company": default_company or "",
#             "department": department,
#             "department_like": f"%{department}%",
#         },
#         as_dict=1,
#     )

#     employee_names = [e.employee for e in employees]

#     assignment_map = {}
#     has_draft = False

#     if employee_names:
#         rows = frappe.db.sql(
#             """
#             SELECT
#                 sa.employee,
#                 sa.shift_type,
#                 sa.start_date,
#                 sa.end_date,
#                 sa.status,
#                 sa.docstatus,
#                 st.start_time,
#                 st.end_time
#             FROM `tabShift Assignment` sa
#             LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
#             WHERE sa.employee IN %(employees)s
#               AND sa.start_date <= %(end)s
#               AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
#               AND sa.docstatus < 2
#             ORDER BY sa.docstatus ASC
#             """,
#             {
#                 "employees": employee_names,
#                 "start": week_start_dt,
#                 "end": week_end_dt,
#             },
#             as_dict=1,
#         )

#         for row in rows:
#             row_start = row.start_date
#             row_end = row.end_date or row.start_date
#             if row_end < row_start:
#                 row_end = row_start
#             for day in week_dates:
#                 if row_start <= day <= row_end:
#                     key = cstr(day)
#                     existing_row = assignment_map.get(row.employee, {}).get(key)
#                     if existing_row is None or row.docstatus == 0:
#                         assignment_map.setdefault(row.employee, {})[key] = row
#             if row.docstatus == 0:
#                 has_draft = True

#     staff = []
#     for emp in employees:
#         shifts = {}
#         for day in week_dates:
#             key = cstr(day)
#             row = assignment_map.get(emp.employee, {}).get(key)

#             if not row:
#                 shifts[key] = {"value": "OFF", "status": "Off", "time": "", "draft": False}
#             elif row.status == "Inactive":
#                 shifts[key] = {
#                     "value": row.shift_type,
#                     "status": "Leave",
#                     "time": _format_shift_time(row.start_time, row.end_time),
#                     "draft": row.docstatus == 0,
#                 }
#             else:
#                 shifts[key] = {
#                     "value": row.shift_type,
#                     "status": "Active",
#                     "time": _format_shift_time(row.start_time, row.end_time),
#                     "draft": row.docstatus == 0,
#                 }

#         staff.append({
#             "employee": emp.employee,
#             "employee_name": emp.employee_name,
#             "designation": emp.designation or "",
#             "area": _short_department(emp.department),
#             "shifts": shifts,
#         })

#     total_slots = len(staff) * 7
#     assigned_slots = sum(
#         1
#         for row in staff
#         for value in row["shifts"].values()
#         if value["status"] == "Active"
#     )
#     coverage_level = round((assigned_slots / total_slots) * 100) if total_slots else 0

#     return {
#         "staff": staff,
#         "has_draft": has_draft,
#         "stats": {
#             "coverage_level": coverage_level,
#             "conflict_alerts": _count_conflicts([
#                 {"shifts": {d: {"status": c["status"]} for d, c in row["shifts"].items()}}
#                 for row in staff
#             ]),
#             "total_slots": total_slots,
#             "assigned_slots": assigned_slots,
#         },
#     }


# def _parse_assignments(assignments):
#     if isinstance(assignments, str):
#         try:
#             assignments = json.loads(assignments) if assignments else {}
#         except (ValueError, TypeError):
#             assignments = {}
#     return assignments or {}


# def _resolve_shift_type_for_leave(employee, existing_shift_type):
#     if existing_shift_type:
#         return existing_shift_type

#     default_shift = frappe.db.get_value("Employee", employee, "default_shift")
#     if default_shift and frappe.db.exists("Shift Type", default_shift):
#         return default_shift

#     return frappe.db.get_value("Shift Type", {}, "name", order_by="name asc")


# def _remove_assignment(name, docstatus):
#     if docstatus == 1:
#         doc = frappe.get_doc("Shift Assignment", name)
#         doc.flags.ignore_permissions = True
#         doc.cancel()
#         docstatus = doc.docstatus
#     if docstatus in (0, 2):
#         frappe.delete_doc("Shift Assignment", name, ignore_permissions=True, force=True)


# def _get_overlapping_assignment(employee, date):
#     rows = frappe.db.sql(
#         """
#         SELECT name, employee, docstatus, shift_type, status, start_date, end_date
#         FROM `tabShift Assignment`
#         WHERE employee = %(employee)s
#           AND docstatus < 2
#           AND start_date <= %(date)s
#           AND (
#               (end_date IS NULL AND start_date = %(date)s)
#               OR end_date >= %(date)s
#               OR end_date < start_date
#           )
#         ORDER BY docstatus ASC
#         LIMIT 1
#         """,
#         {"employee": employee, "date": date},
#         as_dict=1,
#     )
#     if not rows:
#         return None

#     row = rows[0]
#     if row.end_date and row.end_date < row.start_date:
#         row.end_date = row.start_date
#         frappe.db.set_value("Shift Assignment", row.name, "end_date", row.start_date, update_modified=False)
#     elif row.end_date is None:
#         # A missing end_date means this is a single-day assignment, not an
#         # open-ended/indefinite one -- normalize in-memory so every caller
#         # downstream (e.g. _exclude_date_from_assignment) sees a real,
#         # consistent end_date rather than having to special-case None.
#         row.end_date = row.start_date

#     return row


# def _exclude_date_from_assignment(existing, date, employee_doc=None):
#     start = existing.start_date
#     # A missing end_date means this is a single-day assignment (end == start),
#     # not an open-ended/indefinite range -- matches the convention used
#     # elsewhere in this file (e.g. `row.end_date or row.start_date`).
#     end = existing.end_date or start

#     if start == date and end == date:
#         _remove_assignment(existing.name, existing.docstatus)
#         return

#     if start == date:
#         _resize_assignment(existing, add_days(date, 1), end)
#         return

#     if end == date:
#         _resize_assignment(existing, start, add_days(date, -1))
#         return

#     if not employee_doc:
#         employee_doc = frappe.db.get_value(
#             "Employee", existing.employee, ["employee_name", "company"], as_dict=1
#         )

#     before_end = add_days(date, -1)
#     after_start = add_days(date, 1)
#     after_end = end

#     _resize_assignment(existing, start, before_end)

#     after = frappe.get_doc({
#         "doctype": "Shift Assignment",
#         "employee": existing.employee,
#         "employee_name": employee_doc.employee_name if employee_doc else None,
#         "company": employee_doc.company if employee_doc else None,
#         "shift_type": existing.shift_type,
#         "start_date": after_start,
#         "end_date": after_end,
#         "status": existing.status,
#     })
#     after.insert(ignore_permissions=True)
#     if existing.docstatus == 1:
#         after.flags.ignore_permissions = True
#         after.submit()


# def _resize_assignment(existing, new_start, new_end):
#     if existing.docstatus == 1 and new_start != existing.start_date:
#         doc = frappe.get_doc("Shift Assignment", existing.name)
#         employee_name = doc.employee_name
#         company = doc.company
#         shift_type = doc.shift_type
#         status = doc.status
#         employee = doc.employee

#         doc.flags.ignore_permissions = True
#         doc.cancel()
#         frappe.delete_doc("Shift Assignment", doc.name, ignore_permissions=True, force=True)

#         new_doc = frappe.get_doc({
#             "doctype": "Shift Assignment",
#             "employee": employee,
#             "employee_name": employee_name,
#             "company": company,
#             "shift_type": shift_type,
#             "start_date": new_start,
#             "end_date": new_end,
#             "status": status,
#         })
#         new_doc.insert(ignore_permissions=True)
#         new_doc.flags.ignore_permissions = True
#         new_doc.submit()
#         return

#     doc = frappe.get_doc("Shift Assignment", existing.name)
#     doc.start_date = new_start
#     doc.end_date = new_end
#     doc.flags.ignore_permissions = True
#     doc.save(ignore_permissions=True)


# def _apply_draft_assignments(department, week_start, assignments, publish=False, allowed_dates=None):
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to update the roster."))

#     assignments = _parse_assignments(assignments)
#     if allowed_dates is not None:
#         week_dates = {cstr(d) for d in allowed_dates}
#     else:
#         week_dates = {cstr(d) for d in _week_dates(week_start)}
#     warnings = []

#     for employee, day_map in assignments.items():
#         if not frappe.db.exists("Employee", employee):
#             continue
#         if not isinstance(day_map, dict):
#             continue

#         employee_doc = frappe.db.get_value(
#             "Employee", employee, ["employee_name", "company"], as_dict=1
#         )

#         for date_str, value in day_map.items():
#             if date_str not in week_dates:
#                 continue

#             value = cstr(value).strip() or "OFF"
#             date = getdate(date_str)

#             try:
#                 existing = _get_overlapping_assignment(employee, date)

#                 is_exact_single_day = bool(
#                     existing and existing.start_date == date and (existing.end_date or existing.start_date) == date
#                 )

#                 if value == "OFF":
#                     if existing:
#                         _exclude_date_from_assignment(existing, date, employee_doc)
#                     continue

#                 if value == "Leave":
#                     shift_type = _resolve_shift_type_for_leave(
#                         employee, existing.shift_type if existing else None
#                     )
#                     if not shift_type:
#                         continue
#                     target_status = "Inactive"
#                 else:
#                     if not frappe.db.exists("Shift Type", value):
#                         continue
#                     shift_type = value
#                     target_status = "Active"

#                 if existing and is_exact_single_day and existing.shift_type == shift_type:
#                     doc = frappe.get_doc("Shift Assignment", existing.name)
#                 else:
#                     if existing:
#                         _exclude_date_from_assignment(existing, date, employee_doc)
#                     doc = frappe.get_doc({
#                         "doctype": "Shift Assignment",
#                         "employee": employee,
#                         "employee_name": employee_doc.employee_name if employee_doc else None,
#                         "company": employee_doc.company if employee_doc else None,
#                         "shift_type": shift_type,
#                         "start_date": date,
#                         "end_date": date,
#                         "status": target_status,
#                     })
#                     doc.insert(ignore_permissions=True)

#                 if doc.status != target_status:
#                     doc.status = target_status
#                     doc.save(ignore_permissions=True)

#                 if publish and doc.docstatus == 0:
#                     doc.flags.ignore_permissions = True
#                     doc.submit()
#             except Exception as exc:
#                 frappe.db.rollback()
#                 frappe.log_error(
#                     f"Weekly Shift Generator - failed to apply {employee} / {date_str} = {value}: {exc}",
#                     reference_doctype="Shift Assignment",
#                 )
#                 warnings.append(f"{employee_doc.employee_name if employee_doc else employee} on {date_str}: {cstr(exc)}")

#     return {"ok": True, "warnings": warnings}


# @frappe.whitelist()
# def save_weekly_draft(department=None, week_start=None, assignments=None):
#     return _apply_draft_assignments(department, week_start, assignments, publish=False)


# @frappe.whitelist()
# def publish_weekly_draft(department=None, week_start=None, assignments=None):
#     return _apply_draft_assignments(department, week_start, assignments, publish=True)


# @frappe.whitelist()
# def create_shift_type(name, start_time, end_time):
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to add a Shift Type."))

#     name = cstr(name).strip()
#     if not name:
#         frappe.throw(_("Shift Type name is required."))
#     if not start_time or not end_time:
#         frappe.throw(_("Start Time and End Time are required."))

#     if frappe.db.exists("Shift Type", name):
#         frappe.throw(_("Shift Type {0} already exists.").format(name))

#     def _normalize_time(value):
#         value = cstr(value).strip()
#         return value if len(value.split(":")) == 3 else f"{value}:00"

#     doc = frappe.get_doc({
#         "doctype": "Shift Type",
#         "name": name,
#         "start_time": _normalize_time(start_time),
#         "end_time": _normalize_time(end_time),
#     })
#     doc.insert(ignore_permissions=True)

#     return {"name": doc.name}


# @frappe.whitelist()
# def get_all_shift_types():
#     """Full Shift Type list (name + start/end time) for the View All Shift
#     Types modal -- get_shift_types() above only returns name, which isn't
#     enough to display or edit times."""
#     rows = frappe.get_all(
#         "Shift Type",
#         fields=["name", "start_time", "end_time"],
#         order_by="name asc",
#     )

#     in_use_counts = frappe.db.sql(
#         """
#         SELECT shift_type, COUNT(*) AS total
#         FROM `tabShift Assignment`
#         WHERE docstatus < 2
#         GROUP BY shift_type
#         """,
#         as_dict=True,
#     )
#     in_use_map = {row.shift_type: row.total for row in in_use_counts}

#     for row in rows:
#         row["in_use_count"] = in_use_map.get(row.name, 0)
#         row["time_label"] = _format_shift_time(row.start_time, row.end_time)

#     return rows


# @frappe.whitelist()
# def update_shift_type(name, start_time, end_time):
#     """Edit an existing Shift Type's start/end time. Renaming is
#     intentionally out of scope here -- Shift Type uses its name as the
#     document's primary key, so changing it would require frappe.rename_doc
#     and updating every Shift Assignment/roster cell referencing the old
#     name. If renaming is needed later, add it as a separate explicit
#     action rather than folding it into this edit."""
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to edit a Shift Type."))

#     name = cstr(name).strip()
#     if not name:
#         frappe.throw(_("Shift Type name is required."))
#     if not frappe.db.exists("Shift Type", name):
#         frappe.throw(_("Shift Type {0} was not found.").format(name))
#     if not start_time or not end_time:
#         frappe.throw(_("Start Time and End Time are required."))

#     def _normalize_time(value):
#         value = cstr(value).strip()
#         return value if len(value.split(":")) == 3 else f"{value}:00"

#     doc = frappe.get_doc("Shift Type", name)
#     doc.start_time = _normalize_time(start_time)
#     doc.end_time = _normalize_time(end_time)
#     doc.save(ignore_permissions=True)

#     return {"name": doc.name}


# @frappe.whitelist()
# def get_assignment_tool_options():
#     default_company = _get_default_company()

#     shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")
#     branches = frappe.get_all("Branch", fields=["name"], order_by="name asc")
#     designations = frappe.get_all("Designation", fields=["name"], order_by="name asc")
#     employment_types = frappe.get_all("Employment Type", fields=["name"], order_by="name asc")
#     grades = frappe.get_all("Employee Grade", fields=["name"], order_by="name asc")

#     # Department is confirmed company-scoped (used the same way in
#     # get_weekly_roster / get_weekly_draft elsewhere in this file).
#     departments = frappe.get_all(
#         "Department",
#         filters={"disabled": 0, "company": default_company} if default_company else {"disabled": 0},
#         fields=["name"],
#         order_by="name asc",
#     )

#     return {
#         "companies": [default_company] if default_company else [],
#         "shift_types": [s.name for s in shift_types],
#         "branches": [b.name for b in branches],
#         "designations": [d.name for d in designations],
#         "employment_types": [e.name for e in employment_types],
#         "grades": [g.name for g in grades],
#         "departments": [d.name for d in departments],
#         "default_company": default_company,
#     }


# @frappe.whitelist()
# def get_assignment_tool_employees(
#     company=None,
#     branch=None,
#     department=None,
#     designation=None,
#     grade=None,
#     employment_type=None,
#     shift_type=None,
#     start_date=None,
#     end_date=None,
#     status="Active",
# ):
#     filters = {"status": "Active"}

#     company = company or _get_default_company()

#     for field, value in (
#         ("company", company),
#         ("branch", branch),
#         ("department", department),
#         ("designation", designation),
#         ("grade", grade),
#         ("employment_type", employment_type),
#     ):
#         if value:
#             filters[field] = value

#     if start_date:
#         start = getdate(start_date)
#         filters["date_of_joining"] = ["<=", start]

#     employees = frappe.get_all(
#         "Employee",
#         filters=filters,
#         fields=["name as employee", "employee_name", "branch", "department", "designation", "default_shift"],
#         order_by="employee_name asc",
#     )

#     if not employees:
#         return []

#     if cstr(status) == "Active" and start_date:
#         start = getdate(start_date)
#         end = getdate(end_date) if end_date else None

#         existing_filters = {
#             "employee": ["in", [e.employee for e in employees]],
#             "status": "Active",
#             "docstatus": 1,
#         }

#         existing = frappe.get_all(
#             "Shift Assignment",
#             filters=existing_filters,
#             fields=["employee", "start_date", "end_date"],
#         )

#         busy = set()
#         for row in existing:
#             row_start = row.start_date
#             row_end = row.end_date or row_start
#             if row_end < start:
#                 continue
#             if end and row_start > end:
#                 continue
#             busy.add(row.employee)

#         employees = [e for e in employees if e.employee not in busy]

#     for emp in employees:
#         emp["department"] = _short_department(emp.get("department"))

#     return employees


# def _has_overlapping_assignment_in_range(employee, start, end):
#     """Check whether `employee` has any existing (non-cancelled) Shift
#     Assignment overlapping [start, end]. Used by bulk_assign_shift to
#     detect a conflict before attempting to insert, since HRMS's own
#     validate_overlapping_shifts() throws a raw, unfriendly error that the
#     bulk-assign loop would otherwise just swallow into a bare 'failure'
#     entry with no explanation.
#     """
#     rows = frappe.db.sql(
#         """
#         SELECT name, start_date, end_date
#         FROM `tabShift Assignment`
#         WHERE employee = %(employee)s
#           AND docstatus < 2
#           AND start_date <= %(end)s
#           AND ifnull(end_date, start_date) >= %(start)s
#         LIMIT 1
#         """,
#         {"employee": employee, "start": start, "end": end},
#         as_dict=1,
#     )
#     return rows[0] if rows else None


# @frappe.whitelist()
# def bulk_assign_shift(employees, company, shift_type, start_date, end_date=None, status="Active"):
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to assign shifts."))

#     if isinstance(employees, str):
#         employees = json.loads(employees) if employees else []

#     if not employees:
#         frappe.throw(_("Please select at least one employee."))
#     if not company:
#         frappe.throw(_("Company is required."))
#     if not shift_type or not frappe.db.exists("Shift Type", shift_type):
#         frappe.throw(_("A valid Shift Type is required."))
#     if not start_date:
#         frappe.throw(_("Start Date is required."))

#     start = getdate(start_date)
#     end = getdate(end_date) if end_date else None
#     if end and end < start:
#         frappe.throw(_("End Date cannot be before Start Date."))

#     status = cstr(status or "Active").strip()
#     if status not in ("Active", "Inactive"):
#         frappe.throw(_("Status must be Active or Inactive."))

#     success, failure = [], []

#     for employee in employees:
#         employee_name = employee
#         try:
#             if not frappe.db.exists("Employee", employee):
#                 failure.append({
#                     "employee": employee,
#                     "employee_name": employee,
#                     "reason": "Employee not found.",
#                 })
#                 continue

#             employee_doc = frappe.db.get_value(
#                 "Employee", employee, ["employee_name", "department"], as_dict=1
#             )
#             employee_name = employee_doc.employee_name if employee_doc else employee

#             conflict = _has_overlapping_assignment_in_range(employee, start, end or start)
#             if conflict:
#                 failure.append({
#                     "employee": employee,
#                     "employee_name": employee_name,
#                     "reason": "Already has Shift Assignment {0} overlapping these dates.".format(
#                         conflict.name
#                     ),
#                 })
#                 continue

#             doc = frappe.get_doc({
#                 "doctype": "Shift Assignment",
#                 "employee": employee,
#                 "employee_name": employee_name,
#                 "company": company,
#                 "shift_type": shift_type,
#                 "start_date": start,
#                 "end_date": end,
#                 "status": status,
#             })
#             doc.insert(ignore_permissions=True)
#             doc.flags.ignore_permissions = True
#             doc.submit()
#             success.append({
#                 "employee": employee,
#                 "employee_name": employee_name,
#                 "name": doc.name,
#             })
#         except Exception as exc:
#             frappe.db.rollback()
#             frappe.log_error(
#                 f"Weekly Shift Generator - bulk assign failed for employee {employee}.",
#                 reference_doctype="Shift Assignment",
#             )
#             failure.append({
#                 "employee": employee,
#                 "employee_name": employee_name,
#                 "reason": cstr(exc),
#             })

#     return {"success": success, "failure": failure}


# @frappe.whitelist()
# def ai_auto_assign(department=None, week_start=None):
#     frappe.throw("AI Auto Assign is not yet available.")





import json

import frappe
from frappe import _
from frappe.utils import cstr, getdate, add_days, format_time

# ---------------------------------------------------------------------------
# Weekly Shift Generator API
#
# Backs frontend/src/pages/shift/WeeklyShiftGenerator.vue
# ---------------------------------------------------------------------------


def _week_dates(week_start):
    start = getdate(week_start) if week_start else getdate(frappe.utils.nowdate())
    return [add_days(start, i) for i in range(7)]


def _short_department(department):
    value = cstr(department or "")
    return value.split(" - ")[0].strip() if " - " in value else value


def _normalize_department(department):
    return cstr(department or "").strip()


def _format_shift_time(start_time, end_time):
    if start_time is None or end_time is None:
        return ""
    try:
        return f"{format_time(start_time, 'hh:mm a')} - {format_time(end_time, 'hh:mm a')}"
    except Exception:
        return ""


def _get_default_company():
    return frappe.defaults.get_global_default("company") or frappe.db.get_value(
        "Company", {}, "name", order_by="creation asc"
    )


def _is_global_roster_admin():
    """System Manager, Hotel Manager, and Administrator can manage any department."""
    if frappe.session.user == "Administrator":
        return True
    return bool(set(frappe.get_roles(frappe.session.user)).intersection(
        {"System Manager", "Hotel Manager"}
    ))


def _get_manager_department():
    """Return the department of the logged-in user's Employee record, or None."""
    return frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        "department",
    )


def _assert_department_access(department):
    """Throw PermissionError if the current user is not allowed to manage
    the given department. Global admins are always allowed. Department managers
    can only access their own department."""
    if _is_global_roster_admin():
        return
    manager_dept = _get_manager_department()
    if not manager_dept:
        frappe.throw(
            "Your Employee record has no department. Contact your administrator.",
            frappe.PermissionError,
        )
    if _normalize_department(department) != _normalize_department(manager_dept):
        frappe.throw(
            "You can only manage shifts for your own department.",
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_departments():
    """Return distinct active department names for the department dropdown,
    scoped to the default company only -- matches the Shift List page and
    avoids leaking departments from other companies (e.g. _Test Company)
    into the dropdown.

    Global admins (System Manager, Hotel Manager, Administrator) see ALL
    departments. Department-level managers only see their own department.
    """
    # Global admins see everything
    global_admin_roles = {"System Manager", "Hotel Manager"}
    user_roles = set(frappe.get_roles(frappe.session.user))
    is_global_admin = (
        frappe.session.user == "Administrator"
        or bool(user_roles.intersection(global_admin_roles))
    )

    default_company = _get_default_company()

    if is_global_admin:
        rows = frappe.db.sql(
            """
            SELECT DISTINCT department AS value
            FROM `tabEmployee`
            WHERE status = 'Active'
              AND IFNULL(department, '') != ''
              AND (%(company)s = '' OR company = %(company)s)
            ORDER BY department
            """,
            {"company": default_company or ""},
            as_dict=1,
        )
    else:
        # Scope to the manager's own department only
        employee_dept = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user, "status": "Active"},
            "department",
        )
        if not employee_dept:
            return []

        rows = frappe.db.sql(
            """
            SELECT DISTINCT department AS value
            FROM `tabEmployee`
            WHERE status = 'Active'
              AND IFNULL(department, '') != ''
              AND (%(company)s = '' OR company = %(company)s)
              AND department = %(department)s
            ORDER BY department
            """,
            {"company": default_company or "", "department": employee_dept},
            as_dict=1,
        )

    departments = []
    for row in rows:
        label = _short_department(row.get("value"))
        if label and label not in departments:
            departments.append(label)

    return departments


def _compute_coverage_stats(staff, week_dates):
    """A day is a conflict if at least one Shift Type that exists in the
    system (ALL Shift Type records, even unused ones) has zero people in
    this department actively working it that day. Conflict Alerts is a
    simple day-count (0-7). Coverage Level is the inverse fraction of
    conflict-free days, e.g. 5 clean days out of 7 = ~71%.
    """
    total_shift_types = frappe.db.count("Shift Type")

    conflict_days = 0
    for day in week_dates:
        key = cstr(day)
        covered_shift_types = set()
        for row in staff:
            cell = row["shifts"].get(key)
            if cell and cell.get("status") == "Active" and cell.get("shift_type"):
                covered_shift_types.add(cell["shift_type"])

        if total_shift_types == 0 or len(covered_shift_types) < total_shift_types:
            conflict_days += 1

    total_days = len(week_dates) or 7
    coverage_level = round(((total_days - conflict_days) / total_days) * 100)

    return coverage_level, conflict_days


@frappe.whitelist()
def get_weekly_roster(department=None, week_start=None):
    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    department = _normalize_department(department)
    _assert_department_access(department)
    default_company = _get_default_company()

    employees = frappe.db.sql(
        """
        SELECT
            name AS employee,
            employee_name,
            designation,
            department
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND (%(company)s = '' OR company = %(company)s)
          AND (%(department)s = '' OR department LIKE %(department_like)s)
        ORDER BY employee_name
        """,
        {
            "company": default_company or "",
            "department": department,
            "department_like": f"%{department}%",
        },
        as_dict=1,
    )

    employee_names = [e.employee for e in employees]

    assignment_map = {}
    if employee_names:
        rows = frappe.db.sql(
            """
            SELECT
                sa.employee,
                sa.shift_type,
                sa.start_date,
                sa.end_date,
                sa.status,
                st.start_time,
                st.end_time
            FROM `tabShift Assignment` sa
            LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
            WHERE sa.employee IN %(employees)s
              AND sa.start_date <= %(end)s
              AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
              AND sa.docstatus = 1
            """,
            {
                "employees": employee_names,
                "start": week_start_dt,
                "end": week_end_dt,
            },
            as_dict=1,
        )

        for row in rows:
            row_start = row.start_date
            row_end = row.end_date or row.start_date
            if row_end < row_start:
                row_end = row_start
            for day in week_dates:
                if row_start <= day <= row_end:
                    assignment_map.setdefault(row.employee, {})[cstr(day)] = {
                        "shift_type": row.shift_type,
                        "status": row.status,
                        "time": _format_shift_time(row.start_time, row.end_time),
                    }

    staff = []
    for emp in employees:
        shifts = {}
        for day in week_dates:
            key = cstr(day)
            entry = assignment_map.get(emp.employee, {}).get(key)

            if not entry:
                shifts[key] = {"shift_type": "OFF", "status": "Off", "time": ""}
            elif entry["status"] == "Inactive":
                shifts[key] = {"shift_type": entry["shift_type"], "status": "Leave", "time": entry["time"]}
            else:
                shifts[key] = {
                    "shift_type": entry["shift_type"],
                    "status": "Active",
                    "time": entry["time"],
                }

        staff.append({
            "employee": emp.employee,
            "employee_name": emp.employee_name,
            "designation": emp.designation or "",
            "area": _short_department(emp.department),
            "shifts": shifts,
        })

    total_slots = len(staff) * 7
    assigned_slots = sum(
        1
        for row in staff
        for value in row["shifts"].values()
        if value["status"] == "Active"
    )

    coverage_level, conflict_alerts = _compute_coverage_stats(staff, week_dates)

    return {
        "staff": staff,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": conflict_alerts,
            "total_slots": total_slots,
            "assigned_slots": assigned_slots,
        },
    }


@frappe.whitelist()
def get_shift_types():
    shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")

    options = [{"value": row.name, "label": row.name} for row in shift_types]
    options.append({"value": "OFF", "label": "OFF"})

    return options


@frappe.whitelist()
def get_weekly_draft(department=None, week_start=None):
    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    department = _normalize_department(department)
    _assert_department_access(department)
    default_company = _get_default_company()

    employees = frappe.db.sql(
        """
        SELECT
            name AS employee,
            employee_name,
            designation,
            department
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND (%(company)s = '' OR company = %(company)s)
          AND (%(department)s = '' OR department LIKE %(department_like)s)
        ORDER BY employee_name
        """,
        {
            "company": default_company or "",
            "department": department,
            "department_like": f"%{department}%",
        },
        as_dict=1,
    )

    employee_names = [e.employee for e in employees]

    assignment_map = {}
    has_draft = False

    if employee_names:
        rows = frappe.db.sql(
            """
            SELECT
                sa.employee,
                sa.shift_type,
                sa.start_date,
                sa.end_date,
                sa.status,
                sa.docstatus,
                st.start_time,
                st.end_time
            FROM `tabShift Assignment` sa
            LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
            WHERE sa.employee IN %(employees)s
              AND sa.start_date <= %(end)s
              AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
              AND sa.docstatus < 2
            ORDER BY sa.docstatus ASC
            """,
            {
                "employees": employee_names,
                "start": week_start_dt,
                "end": week_end_dt,
            },
            as_dict=1,
        )

        for row in rows:
            row_start = row.start_date
            row_end = row.end_date or row.start_date
            if row_end < row_start:
                row_end = row_start
            for day in week_dates:
                if row_start <= day <= row_end:
                    key = cstr(day)
                    existing_row = assignment_map.get(row.employee, {}).get(key)
                    if existing_row is None or row.docstatus == 0:
                        assignment_map.setdefault(row.employee, {})[key] = row
            if row.docstatus == 0:
                has_draft = True

    staff = []
    for emp in employees:
        shifts = {}
        for day in week_dates:
            key = cstr(day)
            row = assignment_map.get(emp.employee, {}).get(key)

            if not row:
                shifts[key] = {"value": "OFF", "status": "Off", "time": "", "draft": False}
            elif row.status == "Inactive":
                shifts[key] = {
                    "value": row.shift_type,
                    "status": "Leave",
                    "time": _format_shift_time(row.start_time, row.end_time),
                    "draft": row.docstatus == 0,
                }
            else:
                shifts[key] = {
                    "value": row.shift_type,
                    "status": "Active",
                    "time": _format_shift_time(row.start_time, row.end_time),
                    "draft": row.docstatus == 0,
                }

        staff.append({
            "employee": emp.employee,
            "employee_name": emp.employee_name,
            "designation": emp.designation or "",
            "area": _short_department(emp.department),
            "shifts": shifts,
        })

    total_slots = len(staff) * 7
    assigned_slots = sum(
        1
        for row in staff
        for value in row["shifts"].values()
        if value["status"] == "Active"
    )

    # Build a parallel staff list shaped like get_weekly_roster's (shift_type
    # instead of value) so the same coverage/conflict logic applies
    # identically whether viewing the live roster or the draft.
    staff_for_stats = [
        {
            "shifts": {
                d: {"shift_type": cell["value"], "status": cell["status"]}
                for d, cell in row["shifts"].items()
            }
        }
        for row in staff
    ]
    coverage_level, conflict_alerts = _compute_coverage_stats(staff_for_stats, week_dates)

    return {
        "staff": staff,
        "has_draft": has_draft,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": conflict_alerts,
            "total_slots": total_slots,
            "assigned_slots": assigned_slots,
        },
    }


def _parse_assignments(assignments):
    if isinstance(assignments, str):
        try:
            assignments = json.loads(assignments) if assignments else {}
        except (ValueError, TypeError):
            assignments = {}
    return assignments or {}


def _resolve_shift_type_for_leave(employee, existing_shift_type):
    if existing_shift_type:
        return existing_shift_type

    default_shift = frappe.db.get_value("Employee", employee, "default_shift")
    if default_shift and frappe.db.exists("Shift Type", default_shift):
        return default_shift

    return frappe.db.get_value("Shift Type", {}, "name", order_by="name asc")


def _remove_assignment(name, docstatus):
    if docstatus == 1:
        doc = frappe.get_doc("Shift Assignment", name)
        doc.flags.ignore_permissions = True
        doc.cancel()
        docstatus = doc.docstatus
    if docstatus in (0, 2):
        frappe.delete_doc("Shift Assignment", name, ignore_permissions=True, force=True)


def _get_overlapping_assignment(employee, date):
    rows = frappe.db.sql(
        """
        SELECT name, employee, docstatus, shift_type, status, start_date, end_date
        FROM `tabShift Assignment`
        WHERE employee = %(employee)s
          AND docstatus < 2
          AND start_date <= %(date)s
          AND (
              (end_date IS NULL AND start_date = %(date)s)
              OR end_date >= %(date)s
              OR end_date < start_date
          )
        ORDER BY docstatus ASC
        LIMIT 1
        """,
        {"employee": employee, "date": date},
        as_dict=1,
    )
    if not rows:
        return None

    row = rows[0]
    if row.end_date and row.end_date < row.start_date:
        row.end_date = row.start_date
        frappe.db.set_value("Shift Assignment", row.name, "end_date", row.start_date, update_modified=False)
    elif row.end_date is None:
        row.end_date = row.start_date

    return row


def _exclude_date_from_assignment(existing, date, employee_doc=None):
    start = existing.start_date
    end = existing.end_date or start

    if start == date and end == date:
        _remove_assignment(existing.name, existing.docstatus)
        return

    if start == date:
        _resize_assignment(existing, add_days(date, 1), end)
        return

    if end == date:
        _resize_assignment(existing, start, add_days(date, -1))
        return

    if not employee_doc:
        employee_doc = frappe.db.get_value(
            "Employee", existing.employee, ["employee_name", "company"], as_dict=1
        )

    before_end = add_days(date, -1)
    after_start = add_days(date, 1)
    after_end = end

    _resize_assignment(existing, start, before_end)

    after = frappe.get_doc({
        "doctype": "Shift Assignment",
        "employee": existing.employee,
        "employee_name": employee_doc.employee_name if employee_doc else None,
        "company": employee_doc.company if employee_doc else None,
        "shift_type": existing.shift_type,
        "start_date": after_start,
        "end_date": after_end,
        "status": existing.status,
    })
    after.insert(ignore_permissions=True)
    if existing.docstatus == 1:
        after.flags.ignore_permissions = True
        after.submit()


def _resize_assignment(existing, new_start, new_end):
    if existing.docstatus == 1 and new_start != existing.start_date:
        doc = frappe.get_doc("Shift Assignment", existing.name)
        employee_name = doc.employee_name
        company = doc.company
        shift_type = doc.shift_type
        status = doc.status
        employee = doc.employee

        doc.flags.ignore_permissions = True
        doc.cancel()
        frappe.delete_doc("Shift Assignment", doc.name, ignore_permissions=True, force=True)

        new_doc = frappe.get_doc({
            "doctype": "Shift Assignment",
            "employee": employee,
            "employee_name": employee_name,
            "company": company,
            "shift_type": shift_type,
            "start_date": new_start,
            "end_date": new_end,
            "status": status,
        })
        new_doc.insert(ignore_permissions=True)
        new_doc.flags.ignore_permissions = True
        new_doc.submit()
        return

    doc = frappe.get_doc("Shift Assignment", existing.name)
    doc.start_date = new_start
    doc.end_date = new_end
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)


def _apply_draft_assignments(department, week_start, assignments, publish=False, allowed_dates=None):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to update the roster."))
    _assert_department_access(department)

    assignments = _parse_assignments(assignments)
    if allowed_dates is not None:
        week_dates = {cstr(d) for d in allowed_dates}
    else:
        week_dates = {cstr(d) for d in _week_dates(week_start)}
    warnings = []

    for employee, day_map in assignments.items():
        if not frappe.db.exists("Employee", employee):
            continue
        if not isinstance(day_map, dict):
            continue

        employee_doc = frappe.db.get_value(
            "Employee", employee, ["employee_name", "company"], as_dict=1
        )

        for date_str, value in day_map.items():
            if date_str not in week_dates:
                continue

            value = cstr(value).strip() or "OFF"
            date = getdate(date_str)

            try:
                existing = _get_overlapping_assignment(employee, date)

                is_exact_single_day = bool(
                    existing and existing.start_date == date and (existing.end_date or existing.start_date) == date
                )

                if value == "OFF":
                    if existing:
                        _exclude_date_from_assignment(existing, date, employee_doc)
                    continue

                if value == "Leave":
                    shift_type = _resolve_shift_type_for_leave(
                        employee, existing.shift_type if existing else None
                    )
                    if not shift_type:
                        continue
                    target_status = "Inactive"
                else:
                    if not frappe.db.exists("Shift Type", value):
                        continue
                    shift_type = value
                    target_status = "Active"

                if existing and is_exact_single_day and existing.shift_type == shift_type:
                    doc = frappe.get_doc("Shift Assignment", existing.name)
                else:
                    if existing:
                        _exclude_date_from_assignment(existing, date, employee_doc)
                    doc = frappe.get_doc({
                        "doctype": "Shift Assignment",
                        "employee": employee,
                        "employee_name": employee_doc.employee_name if employee_doc else None,
                        "company": employee_doc.company if employee_doc else None,
                        "shift_type": shift_type,
                        "start_date": date,
                        "end_date": date,
                        "status": target_status,
                    })
                    doc.insert(ignore_permissions=True)

                if doc.status != target_status:
                    doc.status = target_status
                    doc.save(ignore_permissions=True)

                if publish and doc.docstatus == 0:
                    doc.flags.ignore_permissions = True
                    doc.submit()
            except Exception as exc:
                frappe.db.rollback()
                frappe.log_error(
                    f"Weekly Shift Generator - failed to apply {employee} / {date_str} = {value}: {exc}",
                    reference_doctype="Shift Assignment",
                )
                warnings.append(f"{employee_doc.employee_name if employee_doc else employee} on {date_str}: {cstr(exc)}")

    return {"ok": True, "warnings": warnings}


@frappe.whitelist()
def save_weekly_draft(department=None, week_start=None, assignments=None):
    return _apply_draft_assignments(department, week_start, assignments, publish=False)


@frappe.whitelist()
def publish_weekly_draft(department=None, week_start=None, assignments=None):
    return _apply_draft_assignments(department, week_start, assignments, publish=True)


@frappe.whitelist()
def create_shift_type(name, start_time, end_time):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to add a Shift Type."))

    name = cstr(name).strip()
    if not name:
        frappe.throw(_("Shift Type name is required."))
    if not start_time or not end_time:
        frappe.throw(_("Start Time and End Time are required."))

    if frappe.db.exists("Shift Type", name):
        frappe.throw(_("Shift Type {0} already exists.").format(name))

    def _normalize_time(value):
        value = cstr(value).strip()
        return value if len(value.split(":")) == 3 else f"{value}:00"

    doc = frappe.get_doc({
        "doctype": "Shift Type",
        "name": name,
        "start_time": _normalize_time(start_time),
        "end_time": _normalize_time(end_time),
    })
    doc.insert(ignore_permissions=True)

    return {"name": doc.name}


@frappe.whitelist()
def get_all_shift_types():
    """Full Shift Type list (name + start/end time) for the View All Shift
    Types modal -- get_shift_types() above only returns name, which isn't
    enough to display or edit times."""
    rows = frappe.get_all(
        "Shift Type",
        fields=["name", "start_time", "end_time"],
        order_by="name asc",
    )

    in_use_counts = frappe.db.sql(
        """
        SELECT shift_type, COUNT(*) AS total
        FROM `tabShift Assignment`
        WHERE docstatus < 2
        GROUP BY shift_type
        """,
        as_dict=True,
    )
    in_use_map = {row.shift_type: row.total for row in in_use_counts}

    for row in rows:
        row["in_use_count"] = in_use_map.get(row.name, 0)
        row["time_label"] = _format_shift_time(row.start_time, row.end_time)

    return rows


@frappe.whitelist()
def update_shift_type(name, start_time, end_time):
    """Edit an existing Shift Type's start/end time. Renaming is
    intentionally out of scope here -- Shift Type uses its name as the
    document's primary key, so changing it would require frappe.rename_doc
    and updating every Shift Assignment/roster cell referencing the old
    name. If renaming is needed later, add it as a separate explicit
    action rather than folding it into this edit."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to edit a Shift Type."))

    name = cstr(name).strip()
    if not name:
        frappe.throw(_("Shift Type name is required."))
    if not frappe.db.exists("Shift Type", name):
        frappe.throw(_("Shift Type {0} was not found.").format(name))
    if not start_time or not end_time:
        frappe.throw(_("Start Time and End Time are required."))

    def _normalize_time(value):
        value = cstr(value).strip()
        return value if len(value.split(":")) == 3 else f"{value}:00"

    doc = frappe.get_doc("Shift Type", name)
    doc.start_time = _normalize_time(start_time)
    doc.end_time = _normalize_time(end_time)
    doc.save(ignore_permissions=True)

    return {"name": doc.name}


@frappe.whitelist()
def get_assignment_tool_options():
    default_company = _get_default_company()

    shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")
    branches = frappe.get_all("Branch", fields=["name"], order_by="name asc")
    designations = frappe.get_all("Designation", fields=["name"], order_by="name asc")
    employment_types = frappe.get_all("Employment Type", fields=["name"], order_by="name asc")
    grades = frappe.get_all("Employee Grade", fields=["name"], order_by="name asc")

    departments = frappe.get_all(
        "Department",
        filters={"disabled": 0, "company": default_company} if default_company else {"disabled": 0},
        fields=["name"],
        order_by="name asc",
    )

    return {
        "companies": [default_company] if default_company else [],
        "shift_types": [s.name for s in shift_types],
        "branches": [b.name for b in branches],
        "designations": [d.name for d in designations],
        "employment_types": [e.name for e in employment_types],
        "grades": [g.name for g in grades],
        "departments": [d.name for d in departments],
        "default_company": default_company,
    }


@frappe.whitelist()
def get_assignment_tool_employees(
    company=None,
    branch=None,
    department=None,
    designation=None,
    grade=None,
    employment_type=None,
    shift_type=None,
    start_date=None,
    end_date=None,
    status="Active",
):
    filters = {"status": "Active"}

    company = company or _get_default_company()

    for field, value in (
        ("company", company),
        ("branch", branch),
        ("department", department),
        ("designation", designation),
        ("grade", grade),
        ("employment_type", employment_type),
    ):
        if value:
            filters[field] = value

    if start_date:
        start = getdate(start_date)
        filters["date_of_joining"] = ["<=", start]

    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name as employee", "employee_name", "branch", "department", "designation", "default_shift"],
        order_by="employee_name asc",
    )

    if not employees:
        return []

    if cstr(status) == "Active" and start_date:
        start = getdate(start_date)
        end = getdate(end_date) if end_date else None

        existing_filters = {
            "employee": ["in", [e.employee for e in employees]],
            "status": "Active",
            "docstatus": 1,
        }

        existing = frappe.get_all(
            "Shift Assignment",
            filters=existing_filters,
            fields=["employee", "start_date", "end_date"],
        )

        busy = set()
        for row in existing:
            row_start = row.start_date
            row_end = row.end_date or row_start
            if row_end < start:
                continue
            if end and row_start > end:
                continue
            busy.add(row.employee)

        employees = [e for e in employees if e.employee not in busy]

    for emp in employees:
        emp["department"] = _short_department(emp.get("department"))

    return employees


def _has_overlapping_assignment_in_range(employee, start, end):
    rows = frappe.db.sql(
        """
        SELECT name, start_date, end_date
        FROM `tabShift Assignment`
        WHERE employee = %(employee)s
          AND docstatus < 2
          AND start_date <= %(end)s
          AND ifnull(end_date, start_date) >= %(start)s
        LIMIT 1
        """,
        {"employee": employee, "start": start, "end": end},
        as_dict=1,
    )
    return rows[0] if rows else None


@frappe.whitelist()
def bulk_assign_shift(employees, company, shift_type, start_date, end_date=None, status="Active"):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to assign shifts."))

    if isinstance(employees, str):
        employees = json.loads(employees) if employees else []

    if not employees:
        frappe.throw(_("Please select at least one employee."))
    if not company:
        frappe.throw(_("Company is required."))
    if not shift_type or not frappe.db.exists("Shift Type", shift_type):
        frappe.throw(_("A valid Shift Type is required."))
    if not start_date:
        frappe.throw(_("Start Date is required."))

    start = getdate(start_date)
    end = getdate(end_date) if end_date else None
    if end and end < start:
        frappe.throw(_("End Date cannot be before Start Date."))

    status = cstr(status or "Active").strip()
    if status not in ("Active", "Inactive"):
        frappe.throw(_("Status must be Active or Inactive."))

    success, failure = [], []

    for employee in employees:
        employee_name = employee
        try:
            if not frappe.db.exists("Employee", employee):
                failure.append({
                    "employee": employee,
                    "employee_name": employee,
                    "reason": "Employee not found.",
                })
                continue

            employee_doc = frappe.db.get_value(
                "Employee", employee, ["employee_name", "department"], as_dict=1
            )
            employee_name = employee_doc.employee_name if employee_doc else employee

            conflict = _has_overlapping_assignment_in_range(employee, start, end or start)
            if conflict:
                failure.append({
                    "employee": employee,
                    "employee_name": employee_name,
                    "reason": "Already has Shift Assignment {0} overlapping these dates.".format(
                        conflict.name
                    ),
                })
                continue

            doc = frappe.get_doc({
                "doctype": "Shift Assignment",
                "employee": employee,
                "employee_name": employee_name,
                "company": company,
                "shift_type": shift_type,
                "start_date": start,
                "end_date": end,
                "status": status,
            })
            doc.insert(ignore_permissions=True)
            doc.flags.ignore_permissions = True
            doc.submit()
            success.append({
                "employee": employee,
                "employee_name": employee_name,
                "name": doc.name,
            })
        except Exception as exc:
            frappe.db.rollback()
            frappe.log_error(
                f"Weekly Shift Generator - bulk assign failed for employee {employee}.",
                reference_doctype="Shift Assignment",
            )
            failure.append({
                "employee": employee,
                "employee_name": employee_name,
                "reason": cstr(exc),
            })

    return {"success": success, "failure": failure}


@frappe.whitelist()
def ai_auto_assign(department=None, week_start=None):
    """
    Suggestion-only endpoint for the weekly shift roster.

    Reads current draft/live cells, submitted staff preferences, previous shift history,
    and valid Shift Types, then returns shift suggestions for the manager to review.

    THIS METHOD NEVER creates, edits, deletes, saves, publishes, submits, or cancels
    any Shift Assignment, Staff Shift Preference, or any other record.  All writes
    remain exclusively under the existing save_weekly_draft() / publish_weekly_draft()
    endpoints, which are only triggered by explicit user action after review.

    Returns:
        {
            "staff":       [...],   # Preview cells — same shape as get_weekly_draft
            "suggestions": [...],   # Per-cell suggestion metadata
            "stats":       {...},
            "source":      "ai" | "fallback",
            "warnings":    [...],
            "summary":     {...},
        }
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to use AI Suggest Shifts."))

    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    department = _normalize_department(department)
    default_company = _get_default_company()

    # ── 1. Active employees ────────────────────────────────────────────────────
    employees = frappe.db.sql(
        """
        SELECT name AS employee, employee_name, designation, department, default_shift
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND (%(company)s = '' OR company = %(company)s)
          AND (%(department)s = '' OR department LIKE %(department_like)s)
        ORDER BY employee_name
        """,
        {
            "company": default_company or "",
            "department": department,
            "department_like": f"%{department}%",
        },
        as_dict=1,
    )

    if not employees:
        return {
            "staff": [],
            "suggestions": [],
            "stats": {"coverage_level": 0, "conflict_alerts": 0, "total_slots": 0, "assigned_slots": 0},
            "source": "fallback",
            "warnings": ["No active employees found for this department and week."],
            "summary": {"total": 0, "ai_applied": 0, "fallback_applied": 0, "locked_skipped": 0},
        }

    employee_names = [e.employee for e in employees]

    # ── 2. Current draft / live cells (read-only) ─────────────────────────────
    current_cells = _ai_get_current_cells(employee_names, week_dates, week_start_dt, week_end_dt)

    # ── 3. Valid shift types ──────────────────────────────────────────────────
    shift_type_rows = frappe.get_all(
        "Shift Type", fields=["name", "start_time", "end_time"], order_by="name asc"
    )
    valid_shift_names = {r.name for r in shift_type_rows}

    # ── 4. Submitted preferences for this week (read-only) ───────────────────
    preferences = _ai_get_preferences(employee_names, week_start_dt)

    # ── 5. Previous 4-week shift history (read-only) ─────────────────────────
    prev_shifts = _ai_get_previous_shifts(employee_names, week_start_dt, lookback_weeks=4)

    # ── 6. Deterministic fallback suggestions ────────────────────────────────
    fallback_sug = _ai_fallback_suggestions(
        employees, week_dates, current_cells, preferences, prev_shifts, valid_shift_names
    )

    # ── 7. Try AI provider if enabled ────────────────────────────────────────
    suggestions = fallback_sug
    source = "fallback"
    warnings = []

    try:
        from rhohotel.rhocom_hotel.api import ai_engine as _engine
        settings = _engine.get_settings()
        if settings.get("enabled"):
            ai_raw, ai_warns = _ai_call_provider(
                employees, week_dates, current_cells, preferences, prev_shifts,
                valid_shift_names, shift_type_rows, settings, _engine,
            )
            if ai_raw:
                merged, merge_warns = _ai_merge(
                    ai_raw, fallback_sug, current_cells, valid_shift_names,
                    week_dates, employee_names,
                )
                warnings.extend(merge_warns)
                suggestions = merged
                source = "ai"
            else:
                # AI call failed or returned unusable output — log internally but
                # don't surface noisy technical warnings in the UI; fallback is
                # already populated and the user will get good suggestions.
                for w in ai_warns:
                    frappe.log_error(w, "AI Roster Suggest (silent)")
    except Exception as exc:
        frappe.log_error(f"AI roster suggestion: {exc}", "AI Roster Suggest")

    # ── 8. Shape preview response ─────────────────────────────────────────────
    suggestions_map = {(s["employee"], s["date"]): s for s in suggestions}
    locked_skipped = 0
    staff_out = []

    for emp in employees:
        shifts_out = {}
        for day in week_dates:
            date_str = cstr(day)
            cell = current_cells.get(emp.employee, {}).get(date_str, {})

            if _ai_is_locked(cell):
                locked_skipped += 1
                shifts_out[date_str] = {
                    "value": cell.get("value", "OFF"),
                    "status": cell.get("status", "Active"),
                    "time": cell.get("time", ""),
                    "draft": False,
                    "aiSuggested": False,
                }
                continue

            sug = suggestions_map.get((emp.employee, date_str))
            if sug:
                st = sug["shift_type"]
                shifts_out[date_str] = {
                    "value": st,
                    "status": (
                        "Inactive" if st == "Leave"
                        else "Off" if st == "OFF"
                        else "Active"
                    ),
                    "time": _ai_shift_time(st, shift_type_rows),
                    "draft": True,
                    "aiSuggested": True,
                }
            else:
                shifts_out[date_str] = {
                    "value": cell.get("value", "OFF"),
                    "status": cell.get("status", "Off"),
                    "time": cell.get("time", ""),
                    "draft": cell.get("draft", False),
                    "aiSuggested": False,
                }

        staff_out.append({
            "employee": emp.employee,
            "employee_name": emp.employee_name,
            "designation": emp.designation or "",
            "area": _short_department(emp.department),
            "shifts": shifts_out,
        })

    stats_staff = [
        {
            "shifts": {
                d: {"shift_type": c["value"], "status": c["status"]}
                for d, c in row["shifts"].items()
            }
        }
        for row in staff_out
    ]
    coverage_level, conflict_alerts = _compute_coverage_stats(stats_staff, week_dates)
    total_slots = len(staff_out) * 7
    assigned_slots = sum(
        1 for r in staff_out for c in r["shifts"].values() if c["status"] == "Active"
    )
    ai_applied = sum(1 for s in suggestions if s.get("source") == "ai")

    return {
        "staff": staff_out,
        "suggestions": suggestions,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": conflict_alerts,
            "total_slots": total_slots,
            "assigned_slots": assigned_slots,
        },
        "source": source,
        "warnings": warnings,
        "summary": {
            "total": len(suggestions),
            "ai_applied": ai_applied,
            "fallback_applied": len(suggestions) - ai_applied,
            "locked_skipped": locked_skipped,
        },
    }


# ── AI Roster Helpers ─────────────────────────────────────────────────────────
# All helpers below are read-only.  None of them create, edit, delete, save,
# publish, submit, or cancel any record.

def _ai_get_current_cells(employee_names, week_dates, week_start_dt, week_end_dt):
    """Read current draft + published shift cells for the week (read-only)."""
    result = {}
    if not employee_names:
        return result

    rows = frappe.db.sql(
        """
        SELECT sa.employee, sa.shift_type, sa.start_date, sa.end_date,
               sa.status, sa.docstatus, st.start_time, st.end_time
        FROM `tabShift Assignment` sa
        LEFT JOIN `tabShift Type` st ON st.name = sa.shift_type
        WHERE sa.employee IN %(employees)s
          AND sa.start_date <= %(end)s
          AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
          AND sa.docstatus < 2
        ORDER BY sa.docstatus ASC
        """,
        {"employees": employee_names, "start": week_start_dt, "end": week_end_dt},
        as_dict=1,
    )

    for row in rows:
        row_start = row.start_date
        row_end = row.end_date or row.start_date
        if row_end < row_start:
            row_end = row_start
        for day in week_dates:
            if row_start <= day <= row_end:
                date_str = cstr(day)
                existing = result.get(row.employee, {}).get(date_str)
                if existing is None or row.docstatus == 0:
                    result.setdefault(row.employee, {})[date_str] = {
                        "value": row.shift_type or "OFF",
                        "status": (
                            "Leave" if row.status == "Inactive"
                            else "Active" if row.shift_type
                            else "Off"
                        ),
                        "time": _format_shift_time(row.start_time, row.end_time),
                        "draft": row.docstatus == 0,
                    }

    return result


def _ai_is_locked(cell):
    """Mirror the frontend isLocked: published (not draft) with a real shift value."""
    return bool(
        cell
        and not cell.get("draft", True)
        and cell.get("value", "OFF") != "OFF"
    )


def _ai_get_preferences(employee_names, week_start_dt):
    """Read submitted Staff Shift Preference detail rows for the week (read-only)."""
    result = {}
    if not employee_names:
        return result

    pref_rows = frappe.db.sql(
        """
        SELECT pref.employee, pref.name AS pref_name
        FROM `tabStaff Shift Preference` pref
        WHERE pref.employee IN %(employees)s
          AND pref.week_start = %(week_start)s
          AND pref.status = 'Submitted'
        """,
        {"employees": employee_names, "week_start": week_start_dt},
        as_dict=1,
    )

    if not pref_rows:
        return result

    pref_map = {r.pref_name: r.employee for r in pref_rows}
    pref_names = list(pref_map.keys())

    details = frappe.db.sql(
        """
        SELECT parent, date, preferred_shift, alternative_shift, availability, note
        FROM `tabStaff Shift Preference Detail`
        WHERE parent IN %(parents)s
        ORDER BY date ASC
        """,
        {"parents": pref_names},
        as_dict=1,
    )

    for row in details:
        emp = pref_map.get(row.parent)
        if not emp:
            continue
        result.setdefault(emp, {})[cstr(row.date)] = {
            "preferred_shift": row.preferred_shift or "",
            "alternative_shift": row.alternative_shift or "",
            "availability": row.availability or "Available",
            "note": row.note or "",
        }

    return result


def _ai_get_previous_shifts(employee_names, week_start_dt, lookback_weeks=4):
    """Get published Active shifts in the N weeks before week_start (read-only)."""
    result = {}
    if not employee_names:
        return result

    history_end = add_days(week_start_dt, -1)
    history_start = add_days(week_start_dt, -(lookback_weeks * 7))

    rows = frappe.db.sql(
        """
        SELECT sa.employee, sa.shift_type, sa.start_date, sa.end_date
        FROM `tabShift Assignment` sa
        WHERE sa.employee IN %(employees)s
          AND sa.docstatus = 1
          AND sa.status = 'Active'
          AND sa.start_date <= %(end)s
          AND (sa.end_date IS NULL OR sa.end_date >= %(start)s)
        """,
        {"employees": employee_names, "start": history_start, "end": history_end},
        as_dict=1,
    )

    hs = getdate(history_start)
    he = getdate(history_end)

    for row in rows:
        rs = max(getdate(row.start_date), hs)
        re = min(getdate(row.end_date or row.start_date), he)
        if re < rs:
            continue
        day = rs
        while day <= re:
            result.setdefault(row.employee, []).append({
                "shift_type": row.shift_type,
                "day_of_week": day.weekday(),
                "date": cstr(day),   # used for last-week detection
            })
            day = add_days(day, 1)

    return result


def _ai_fallback_suggestions(employees, week_dates, current_cells, preferences, prev_shifts, valid_shift_names):
    """
    Holistic week-level shift scheduler.

    Guarantees (preference-respecting, best-effort):
    - 2 days OFF per employee per week (preference unavailability honoured first;
      remaining off days chosen deterministically so reruns give the same result).
    - At least one employee on each configured shift type per working day (coverage).
    - No day where all working staff share a single shift type (conflict prevention).
    - Submitted staff preferences and unavailability are the highest priority.
    - Last week's published shifts and 4-week patterns are used for continuity.
    """
    import hashlib as _hashlib
    import random   as _random
    from collections import Counter as _Counter

    DAY_NAMES  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    shift_list = sorted(s for s in valid_shift_names if s not in ("OFF", "Leave"))

    if not employees:
        return []

    week_date_strs = [cstr(d) for d in week_dates]
    week_start_dt  = week_dates[0]

    # ── Build per-employee data maps ──────────────────────────────────────────
    emp_prefs = {emp.employee: preferences.get(emp.employee, {}) for emp in employees}

    lw_start = getdate(add_days(week_start_dt, -7))
    lw_end   = getdate(add_days(week_start_dt, -1))

    emp_patterns  = {}   # {emp: {dow: most_common_shift}}  — 4-week history
    emp_last_week = {}   # {emp: {dow: shift_type}}         — previous week only

    for emp in employees:
        prev      = prev_shifts.get(emp.employee, [])
        by_dow    = {}
        lw_by_dow = {}
        for entry in prev:
            st  = entry.get("shift_type", "")
            dow = entry.get("day_of_week", 0)
            if st not in valid_shift_names:
                continue
            by_dow.setdefault(dow, []).append(st)
            d = entry.get("date")
            if d:
                try:
                    if lw_start <= getdate(d) <= lw_end:
                        lw_by_dow[dow] = st   # most recent wins
                except Exception:
                    pass
        emp_patterns[emp.employee]  = {
            dow: _Counter(shifts).most_common(1)[0][0]
            for dow, shifts in by_dow.items()
        }
        emp_last_week[emp.employee] = lw_by_dow

    # ── Phase 1: Locked cells (published, not draft) ──────────────────────────
    locked = {}   # {(emp, date): shift_type}
    for emp in employees:
        for date_str in week_date_strs:
            cell = current_cells.get(emp.employee, {}).get(date_str, {})
            if _ai_is_locked(cell):
                locked[(emp.employee, date_str)] = cell.get("value", "OFF")

    # ── Phase 2: Assign 2 days off per employee ───────────────────────────────
    emp_off_days = {}   # {emp: set of date_strs}

    for emp in employees:
        forced_off        = set()   # preference: unavailable
        preferred_working = set()   # preference: has a shift — avoid making off

        for date_str in week_date_strs:
            if (emp.employee, date_str) in locked:
                continue
            pref = emp_prefs[emp.employee].get(date_str, {})
            if pref.get("availability") == "Unavailable":
                forced_off.add(date_str)
            elif pref.get("preferred_shift") or pref.get("alternative_shift"):
                preferred_working.add(date_str)

        locked_off_count = sum(
            1 for d in week_date_strs if locked.get((emp.employee, d)) == "OFF"
        )
        needed_off = max(0, 2 - locked_off_count - len(forced_off))

        # Primary candidates: not forced-off, not locked, not strongly preferred
        free_cands = [
            d for d in week_date_strs
            if d not in forced_off
            and (emp.employee, d) not in locked
            and d not in preferred_working
        ]
        # Fallback pool: also includes preferred-working days (last resort)
        all_cands = [
            d for d in week_date_strs
            if d not in forced_off and (emp.employee, d) not in locked
        ]

        # Deterministic shuffle: same employee + week always yields same off days
        _seed = int(_hashlib.md5(
            f"{emp.employee}|{week_date_strs[0]}".encode()
        ).hexdigest(), 16) % (2 ** 32)
        rng = _random.Random(_seed)
        rng.shuffle(free_cands)
        rng.shuffle(all_cands)

        off_days = set(forced_off)
        pool = free_cands if len(free_cands) >= needed_off else all_cands
        for d in pool:
            if d not in off_days:
                off_days.add(d)
                if len(off_days) - len(forced_off) >= needed_off:
                    break

        emp_off_days[emp.employee] = off_days

    # ── Phase 3: Initial per-cell shift assignment ────────────────────────────
    assignment = {emp.employee: {} for emp in employees}
    reason_map = {}   # {(emp, date): (reason_str, confidence, preference_match)}

    for emp in employees:
        default = cstr(emp.get("default_shift") or "")
        for i, day in enumerate(week_dates):
            date_str = week_date_strs[i]
            dow      = day.weekday()
            day_name = DAY_NAMES[dow]
            key      = (emp.employee, date_str)

            if key in locked:
                assignment[emp.employee][date_str] = locked[key]
                continue

            if date_str in emp_off_days.get(emp.employee, set()):
                pref = emp_prefs[emp.employee].get(date_str, {})
                if pref.get("availability") == "Unavailable":
                    reason_map[key] = (f"Staff marked unavailable on {day_name}.", "high", True)
                else:
                    reason_map[key] = (f"Scheduled rest day on {day_name}.", "medium", False)
                assignment[emp.employee][date_str] = "OFF"
                continue

            pref    = emp_prefs[emp.employee].get(date_str, {})
            pref_sh = pref.get("preferred_shift", "")
            alt_sh  = pref.get("alternative_shift", "")
            last_wk = emp_last_week[emp.employee].get(dow)
            pattern = emp_patterns[emp.employee].get(dow)

            if pref_sh and pref_sh in valid_shift_names:
                assignment[emp.employee][date_str] = pref_sh
                reason_map[key] = (f"Matches {day_name} preference.", "high", True)
            elif alt_sh and alt_sh in valid_shift_names and alt_sh != pref_sh:
                assignment[emp.employee][date_str] = alt_sh
                reason_map[key] = (f"Matches {day_name} alternative preference.", "medium", True)
            elif last_wk and last_wk in valid_shift_names:
                assignment[emp.employee][date_str] = last_wk
                reason_map[key] = (f"Continuing last week\u2019s {day_name} shift.", "medium", False)
            elif pattern and pattern in valid_shift_names:
                assignment[emp.employee][date_str] = pattern
                reason_map[key] = (f"Historical {day_name} pattern.", "medium", False)
            elif default and default in valid_shift_names:
                assignment[emp.employee][date_str] = default
                reason_map[key] = ("Employee\u2019s configured default shift.", "low", False)
            elif shift_list:
                assignment[emp.employee][date_str] = shift_list[0]
                reason_map[key] = ("No prior data; first available shift assigned.", "low", False)
            else:
                assignment[emp.employee][date_str] = "OFF"
                reason_map[key] = ("No shift types configured.", "low", False)

    # ── Phase 4: Coverage & conflict correction (day-level) ──────────────────
    if shift_list:
        for i, day in enumerate(week_dates):
            date_str = week_date_strs[i]
            day_name = DAY_NAMES[day.weekday()]

            # Only consider employees who can be reassigned (not locked)
            working = [
                emp for emp in employees
                if assignment[emp.employee].get(date_str) != "OFF"
                and (emp.employee, date_str) not in locked
            ]
            if not working:
                continue

            # Can't cover more shift types than we have working employees
            target_shifts = shift_list[:min(len(shift_list), len(working))]

            def _no_hard_pref(e):
                return not emp_prefs[e.employee].get(date_str, {}).get("preferred_shift")

            counts = _Counter(assignment[e.employee][date_str] for e in working)

            # (a) Conflict prevention: if everyone is on the same shift, redistribute
            if len(counts) == 1 and len(working) > 1:
                ordered = sorted(working, key=lambda e: 0 if _no_hard_pref(e) else 1)
                for idx, emp in enumerate(ordered):
                    new_sh = target_shifts[idx % len(target_shifts)]
                    assignment[emp.employee][date_str] = new_sh
                    old_r = reason_map.get((emp.employee, date_str), ("", "low", False))
                    reason_map[(emp.employee, date_str)] = (
                        f"Redistributed to prevent single-shift conflict on {day_name}.",
                        "low",
                        old_r[2],
                    )
                counts = _Counter(assignment[e.employee][date_str] for e in working)

            # (b) Coverage: ensure each target shift type has at least 1 person
            uncovered = [s for s in target_shifts if counts.get(s, 0) == 0]
            if uncovered:
                by_shift = {}
                for e in working:
                    sh = assignment[e.employee][date_str]
                    by_shift.setdefault(sh, []).append(e)

                # Build reassignment pool: excess employees (no hard preference)
                # from the most over-represented shifts
                pool = []
                for sh, sh_emps in sorted(by_shift.items(), key=lambda kv: -len(kv[1])):
                    excess = sh_emps[1:]   # keep 1 per shift, offer the rest
                    pool.extend(e for e in excess if _no_hard_pref(e))

                for j, needed_sh in enumerate(uncovered):
                    if j < len(pool):
                        emp = pool[j]
                        assignment[emp.employee][date_str] = needed_sh
                        reason_map[(emp.employee, date_str)] = (
                            f"Assigned {needed_sh} to ensure shift coverage on {day_name}.",
                            "low",
                            False,
                        )

    # ── Phase 5: Build final suggestions list ─────────────────────────────────
    suggestions = []
    for emp in employees:
        for i, day in enumerate(week_dates):
            date_str = week_date_strs[i]
            if (emp.employee, date_str) in locked:
                continue

            shift_type = assignment[emp.employee].get(date_str, "OFF")
            dow        = day.weekday()
            day_name   = DAY_NAMES[dow]
            key        = (emp.employee, date_str)

            reason, confidence, pref_match = reason_map.get(
                key, ("Assigned based on available data.", "low", False)
            )

            prev_note = ""
            if shift_type != "OFF":
                same_dow = [
                    p["shift_type"] for p in prev_shifts.get(emp.employee, [])
                    if p.get("day_of_week") == dow and p.get("shift_type") in valid_shift_names
                ]
                if same_dow:
                    cnt = same_dow.count(shift_type)
                    if cnt:
                        prev_note = f"{shift_type} on {cnt}/{len(same_dow)} recent {day_name}s"

            suggestions.append({
                "employee":            emp.employee,
                "date":                date_str,
                "shift_type":          shift_type,
                "confidence":          confidence,
                "reason":              reason,
                "preference_match":    pref_match,
                "previous_shift_note": prev_note,
                "source":              "fallback",
            })

    return suggestions


def _ai_call_provider(
    employees, week_dates, current_cells, preferences, prev_shifts,
    valid_shift_names, shift_type_rows, settings, _engine,
):
    """Call the configured AI provider with a structured scheduling prompt (read-only)."""
    from collections import Counter as _Counter

    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    warnings = []

    week_list = [cstr(d) for d in week_dates]
    valid_list = sorted(s for s in valid_shift_names if s not in ("Leave",)) + ["OFF"]

    # ── Build compact employee table: id | name | default_shift ──────────────
    emp_lines = []
    for e in employees:
        emp_lines.append(f"{e.employee}|{e.employee_name}|{cstr(e.get('default_shift') or 'OFF')}")

    # ── Build compact unavailability / preference lines ───────────────────────
    pref_lines = []
    for emp in employees:
        for date_str, p in preferences.get(emp.employee, {}).items():
            avail = p.get("availability", "Available")
            pref = p.get("preferred_shift", "")
            alt = p.get("alternative_shift", "")
            if avail == "Unavailable":
                pref_lines.append(f"{emp.employee},{date_str},UNAVAILABLE")
            elif pref:
                pref_lines.append(f"{emp.employee},{date_str},prefer={pref}" + (f",alt={alt}" if alt else ""))

    # ── Build compact historical pattern lines ────────────────────────────────
    pattern_lines = []
    for emp in employees:
        prev = prev_shifts.get(emp.employee, [])
        if not prev:
            continue
        by_dow = {}
        for entry in prev:
            st = entry.get("shift_type", "")
            if st in valid_shift_names:
                by_dow.setdefault(entry.get("day_of_week", 0), []).append(st)
        for dow, shifts in sorted(by_dow.items()):
            top = _Counter(shifts).most_common(1)[0][0]
            pattern_lines.append(f"{emp.employee},{DAY_NAMES[dow]},{top}")

    # ── Estimate required output tokens and override max_tokens ──────────────
    # Each output object: ~{"employee":"HR-EMP-00001","date":"2026-06-22","shift_type":"Day Shift","confidence":"low","reason":"x","preference_match":false}
    # ≈ 120 chars ≈ 30 tokens.  Add 20% buffer.
    required_tokens = int(len(employees) * 7 * 35 * 1.2) + 200
    effective_settings = dict(settings)
    effective_settings["max_tokens"] = max(settings.get("max_tokens", 600), required_tokens, 2048)

    prompt = (
        "You are a hotel shift scheduling assistant.\n"
        "Return ONLY a valid JSON array — no prose, no markdown fences, nothing else.\n\n"
        "RULES (strict priority):\n"
        "1. UNAVAILABLE employee on a date → shift_type MUST be \"OFF\".\n"
        "2. Respect prefer= shift, then alt= shift.\n"
        "3. Use historical day-of-week pattern when available.\n"
        "4. Use employee default_shift, else first from valid_shifts.\n"
        "5. Each employee must have exactly 2 days OFF per week (UNAVAILABLE days count as OFF).\n"
        "6. Every configured shift type must appear at least once per working day (coverage).\n"
        "7. Never assign ALL working employees to a single shift type on the same day (no conflict).\n"
        "8. Produce a suggestion for every employee for every date.\n\n"
        f"Week dates (YYYY-MM-DD): {', '.join(week_list)}\n"
        f"Valid shifts: {', '.join(valid_list)}\n\n"
        "Employees (id|name|default_shift):\n"
        + "\n".join(emp_lines) + "\n\n"
        + ("Preferences/unavailability (employee,date,info):\n" + "\n".join(pref_lines) + "\n\n" if pref_lines else "")
        + ("Historical patterns (employee,day,usual_shift):\n" + "\n".join(pattern_lines) + "\n\n" if pattern_lines else "")
        + "Each JSON object must have exactly these keys: "
        '"employee" (id), "date" (YYYY-MM-DD), "shift_type", "confidence" (high/medium/low), '
        '"reason" (≤10 words), "preference_match" (true/false).\n'
        "Output the JSON array now:"
    )

    try:
        if not _engine.is_safe(prompt):
            return [], ["AI scheduling prompt was blocked by safety filter."]

        messages = [{"role": "user", "content": prompt}]
        raw = _engine.call_simple(messages, effective_settings)
        if not raw:
            return [], ["AI returned an empty response."]

        s = raw.find("[")
        e_idx = raw.rfind("]")
        if s == -1 or e_idx == -1:
            # Log enough of the response to diagnose the problem
            frappe.log_error(
                f"AI roster: no JSON array in response (first 400 chars): {raw[:400]}",
                "AI Roster Suggest",
            )
            return [], [f"AI response did not contain a JSON array (got: {raw[:80]!r})."]

        parsed = json.loads(raw[s:e_idx + 1])
        if not isinstance(parsed, list):
            return [], ["AI response is not a JSON array."]

        for item in parsed:
            item["source"] = "ai"

        return parsed, warnings

    except json.JSONDecodeError as exc:
        frappe.log_error(
            f"AI roster JSON parse error: {exc}\nRaw (first 400): {raw[:400] if 'raw' in dir() else 'N/A'}",
            "AI Roster Suggest",
        )
        return [], [f"AI JSON parse error: {cstr(exc)[:80]}"]
    except Exception as exc:
        frappe.log_error(f"AI roster provider call: {exc}", "AI Roster Suggest")
        return [], [f"AI call failed: {cstr(exc)[:80]}"]


def _ai_merge(ai_raw, fallback_sug, current_cells, valid_shift_names, week_dates, employee_names):
    """Validate AI suggestions, fill gaps with deterministic fallback, and enforce business rules."""
    from collections import Counter as _Counter

    warnings = []
    valid_dates = {cstr(d) for d in week_dates}
    emp_set = set(employee_names)

    ai_map = {}
    invalid = 0

    for s in ai_raw:
        emp = s.get("employee", "")
        date = s.get("date", "")
        shift = s.get("shift_type", "")
        if emp not in emp_set or date not in valid_dates:
            invalid += 1
            continue
        if shift not in valid_shift_names and shift != "OFF":
            invalid += 1
            continue
        if _ai_is_locked(current_cells.get(emp, {}).get(date, {})):
            continue
        ai_map[(emp, date)] = s

    if invalid:
        warnings.append(
            f"AI returned {invalid} suggestion(s) with invalid employee/date/shift — "
            "those cells were replaced by rule-based fallback."
        )

    covered = set(ai_map.keys())
    merged = list(ai_map.values())
    for s in fallback_sug:
        if (s["employee"], s["date"]) not in covered:
            merged.append(s)

    # ── Business-rule enforcement on merged output ────────────────────────────
    # Rule: each employee should have at most 2 OFF days per week.
    # If the AI hallucinated and assigned more OFFs, replace the excess with
    # the corresponding fallback suggestion (which obeys the 2-days-off rule).
    fallback_index = {(s["employee"], s["date"]): s for s in fallback_sug}

    emp_off_count = _Counter(
        s["employee"] for s in merged if s.get("shift_type") == "OFF"
    )
    over_rested = {emp for emp, cnt in emp_off_count.items() if cnt > 2}

    if over_rested:
        corrected_count = 0
        emp_off_used = _Counter()
        result = []
        for s in merged:
            if s["employee"] in over_rested and s.get("shift_type") == "OFF":
                emp_off_used[s["employee"]] += 1
                if emp_off_used[s["employee"]] > 2:
                    # Replace with fallback (which correctly scheduled this cell)
                    fb = fallback_index.get((s["employee"], s["date"]))
                    if fb:
                        result.append(fb)
                        corrected_count += 1
                        continue
            result.append(s)
        merged = result
        if corrected_count:
            warnings.append(
                f"AI assigned too many OFF days for {len(over_rested)} employee(s); "
                f"{corrected_count} cell(s) replaced with rule-based suggestions."
            )

    return merged, warnings


def _ai_shift_time(shift_type, shift_type_rows):
    """Look up formatted start–end time label for a Shift Type."""
    if not shift_type or shift_type == "OFF":
        return ""
    for row in shift_type_rows:
        if row.name == shift_type:
            return _format_shift_time(row.start_time, row.end_time)
    return ""