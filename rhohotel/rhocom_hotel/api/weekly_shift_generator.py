# import json

# import frappe
# from frappe import _
# from frappe.utils import cstr, getdate, add_days, format_time

# # ---------------------------------------------------------------------------
# # Weekly Shift Generator API
# #
# # Backs frontend/src/pages/shift/WeeklyShiftGenerator.vue
# #
# # - get_departments()              -> dropdown options for the page filter
# # - get_weekly_roster(department, week_start)
# #                                   -> read-only weekly grid: every active
# #                                      employee in the department (rows) x
# #                                      Sun-Sat (columns), each cell showing
# #                                      the Shift Type + start/end time for
# #                                      that day (from Shift Assignment), or
# #                                      "Leave" / "OFF" when there's none.
# # - get_assignment_tool_options()  -> options for the "Shift Assignment Tool"
# #                                      modal (companies, shift types,
# #                                      designations, branches, employment
# #                                      types, grades) -- mirrors the fields on
# #                                      the "Shift Assignment Tool" single
# #                                      doctype.
# # - get_assignment_tool_employees(filters...)
# #                                   -> employees matching the modal's quick
# #                                      filters, for the selectable employee
# #                                      list (mirrors
# #                                      ShiftAssignmentTool.get_employees).
# # - bulk_assign_shift(employees, company, shift_type, start_date, end_date,
# #                      status)
# #                                   -> creates + submits one Shift Assignment
# #                                      per employee (mirrors
# #                                      ShiftAssignmentTool.bulk_assign for the
# #                                      "Assign Shift" action).
# # - ai_auto_assign(department, week_start)
# #                                   -> rules-based suggestion preview, same
# #                                      shape as get_weekly_roster.
# # ---------------------------------------------------------------------------


# # ---------------------------------------------------------------------------
# # Helpers
# # ---------------------------------------------------------------------------

# def _week_dates(week_start):
#     start = getdate(week_start) if week_start else getdate(frappe.utils.nowdate())
#     return [add_days(start, i) for i in range(7)]


# def _short_department(department):
#     """Strip the trailing ' - Company' suffix Frappe appends to Department links."""
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


# # ---------------------------------------------------------------------------
# # Departments
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def get_departments():
#     """Return distinct active department names for the department dropdown."""
#     rows = frappe.db.sql(
#         """
#         SELECT DISTINCT department AS value
#         FROM `tabEmployee`
#         WHERE status = 'Active'
#           AND IFNULL(department, '') != ''
#         ORDER BY department
#         """,
#         as_dict=1,
#     )

#     departments = []
#     for row in rows:
#         label = _short_department(row.get("value"))
#         if label and label not in departments:
#             departments.append(label)

#     return departments


# def _get_default_company():
#     return frappe.defaults.get_global_default("company") or frappe.db.get_value(
#         "Company", {}, "name", order_by="creation asc"
#     )


# # ---------------------------------------------------------------------------
# # Weekly roster (read-only grid)
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def get_weekly_roster(department=None, week_start=None):
#     """Return every active employee in the department with their per-day
#     Shift Type + time range for the selected week (Sunday - Saturday)."""
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
#                 shifts[key] = {"shift_type": "Leave", "status": "Leave", "time": ""}
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
#     """Flag staff who have a Leave day but are still rostered (Active) on
#     every other day of the week (no real rest day around the leave)."""
#     conflicts = 0
#     for row in staff:
#         shifts = row["shifts"]
#         leave_days = [d for d, v in shifts.items() if v["status"] == "Leave"]
#         working_days = [d for d, v in shifts.items() if v["status"] == "Active"]
#         if leave_days and len(working_days) >= 6:
#             conflicts += 1
#     return conflicts


# # ---------------------------------------------------------------------------
# # Shift Types (for the draft/edit dropdown)
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def get_shift_types():
#     """Return real Shift Type records plus the OFF / Leave pseudo-options
#     for the draft/edit grid dropdown.

#     Each item: { "value": <shift type name or pseudo value>, "label": <display label> }
#     """
#     shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")

#     options = [{"value": row.name, "label": row.name} for row in shift_types]
#     options.append({"value": "Leave", "label": "Leave"})
#     options.append({"value": "OFF", "label": "OFF"})

#     return options


# # ---------------------------------------------------------------------------
# # Weekly draft (editable grid)
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def get_weekly_draft(department=None, week_start=None):
#     """Return every active employee in the department with their per-day
#     draft Shift Type for the selected week (Sunday - Saturday).

#     Includes BOTH draft (docstatus 0) and already-published (docstatus 1)
#     Shift Assignments, so the editor shows the true current state. Cells
#     with no Shift Assignment at all default to "OFF".

#     Each cell: { value, status, time, draft }
#       value  -> Shift Type name, or "OFF" / "Leave"
#       status -> "Active" | "Leave" | "Off"
#       time   -> "hh:mm A - hh:mm A" or ""
#       draft  -> true if this cell comes from an unsubmitted (docstatus 0)
#                 Shift Assignment, false if published (docstatus 1) or empty
#     """
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
#                     # If both a draft and a published row exist for the same
#                     # day, prefer the draft (it represents the latest unsaved
#                     # edit).
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
#                 shifts[key] = {"value": "Leave", "status": "Leave", "time": "", "draft": row.docstatus == 0}
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
#     """Pick a Shift Type to attach to a Leave-status Shift Assignment.

#     Preference order:
#       1. The shift type already assigned to this employee on this day.
#       2. The employee's default_shift, if set.
#       3. The first Shift Type that exists in the system.
#     """
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
#     """Return the Shift Assignment (any docstatus < 2) for this employee
#     whose date range covers `date`, if any (as a dict, or None). Open-ended
#     assignments (end_date IS NULL) are treated as covering `date` only if
#     start_date <= date.
#     """
#     rows = frappe.db.sql(
#         """
#         SELECT name, employee, docstatus, shift_type, status, start_date, end_date
#         FROM `tabShift Assignment`
#         WHERE employee = %(employee)s
#           AND docstatus < 2
#           AND start_date <= %(date)s
#           AND (end_date IS NULL OR end_date >= %(date)s OR end_date < start_date)
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
#         # Data left over from an earlier bug: a Shift Assignment with
#         # end_date before start_date. Treat it as a single-day assignment on
#         # start_date and repair it in the database.
#         row.end_date = row.start_date
#         frappe.db.set_value("Shift Assignment", row.name, "end_date", row.start_date, update_modified=False)

#     return row


# def _exclude_date_from_assignment(existing, date, employee_doc=None):
#     """Remove `date` from an existing Shift Assignment's coverage.

#     - If the assignment covers exactly `date` (single day), remove it
#       entirely.
#     - If `date` is at the start of the range, shrink the range by one day
#       from the front (start_date = date + 1). This also handles open-ended
#       assignments (end_date IS NULL) by keeping them open-ended.
#     - If `date` is at the end of a *closed* range, shrink by one day from
#       the back (end_date = date - 1).
#     - If `date` is strictly inside a closed range, split into two
#       assignments: one covering the days before `date`, and a new one
#       (same shift_type/status/docstatus) covering the days after `date`.
#     - If `date` is strictly after the start of an *open-ended* range, split
#       into a closed "before" assignment (end_date = date - 1) and a new
#       open-ended "after" assignment (start_date = date + 1, end_date = None).

#     Submitted (docstatus 1) assignments are amended via cancel + recreate,
#     since start_date is not `allow_on_submit`.
#     """
#     start = existing.start_date
#     end = existing.end_date  # None means open-ended

#     is_open_ended = end is None
#     effective_end = end if end is not None else start

#     if not is_open_ended and start == date and end == date:
#         _remove_assignment(existing.name, existing.docstatus)
#         return

#     if start == date:
#         # Shrink from the front: new start is the day after `date`.
#         # Works for both closed and open-ended ranges.
#         _resize_assignment(existing, add_days(date, 1), end)
#         return

#     if not is_open_ended and effective_end == date:
#         # Shrink from the back: new end is the day before `date`.
#         _resize_assignment(existing, start, add_days(date, -1))
#         return

#     # `date` is strictly inside the range (or strictly after start of an
#     # open-ended range) -- split into two assignments.
#     if not employee_doc:
#         employee_doc = frappe.db.get_value(
#             "Employee", existing.employee, ["employee_name", "company"], as_dict=1
#         )

#     before_end = add_days(date, -1)
#     after_start = add_days(date, 1)
#     after_end = None if is_open_ended else end

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
#     """Adjust an existing Shift Assignment's start/end date.

#     For submitted (docstatus 1) documents, only end_date is
#     `allow_on_submit`, so a start_date change requires cancel + recreate.
#     """
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


# def _apply_draft_assignments(department, week_start, assignments, publish=False):
#     """Create/update/delete Shift Assignments for each employee/day cell.

#     assignments = { employee: { "YYYY-MM-DD": "OFF" | "Leave" | "<Shift Type>" } }

#     If publish is True, every touched Shift Assignment is submitted
#     (docstatus 1, status Active/Inactive). Otherwise they are left as drafts
#     (docstatus 0).
#     """
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to update the roster."))

#     assignments = _parse_assignments(assignments)
#     week_dates = {cstr(d) for d in _week_dates(week_start)}
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
#     """Save the weekly grid as draft (unsubmitted) Shift Assignments."""
#     return _apply_draft_assignments(department, week_start, assignments, publish=False)


# @frappe.whitelist()
# def publish_weekly_draft(department=None, week_start=None, assignments=None):
#     """Save and submit the weekly grid as published (Active) Shift Assignments."""
#     return _apply_draft_assignments(department, week_start, assignments, publish=True)


# # ---------------------------------------------------------------------------
# # Add Shift Type
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def create_shift_type(name, start_time, end_time):
#     """Create a new Shift Type document.

#     start_time / end_time are accepted as "HH:MM" or "HH:MM:SS" strings; if
#     end_time is earlier than start_time the Shift Type spans midnight
#     (e.g. Night: 22:00 - 06:00), which Shift Type supports natively.
#     """
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


# # ---------------------------------------------------------------------------
# # Shift Assignment Tool (modal) options
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def get_assignment_tool_options():
#     """Return dropdown options for the Shift Assignment Tool modal, mirroring
#     the fields on the 'Shift Assignment Tool' single doctype."""
#     companies = frappe.get_all("Company", fields=["name"], order_by="name asc")
#     shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")
#     branches = frappe.get_all("Branch", fields=["name"], order_by="name asc")
#     designations = frappe.get_all("Designation", fields=["name"], order_by="name asc")
#     employment_types = frappe.get_all("Employment Type", fields=["name"], order_by="name asc")
#     grades = frappe.get_all("Employee Grade", fields=["name"], order_by="name asc")
#     departments = frappe.get_all(
#         "Department",
#         filters={"disabled": 0},
#         fields=["name"],
#         order_by="name asc",
#     )

#     default_company = _get_default_company()

#     return {
#         "companies": [c.name for c in companies],
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
#     """Return employees eligible for shift assignment, mirroring
#     ShiftAssignmentTool.get_employees_for_assigning_shift.

#     An employee is excluded if they already have an Active, submitted Shift
#     Assignment overlapping the requested date range (when status == "Active"),
#     matching the original tool's behaviour.
#     """
#     filters = {"status": "Active"}

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


# # ---------------------------------------------------------------------------
# # Bulk assign (Shift Assignment Tool -> "Assign Shift")
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def bulk_assign_shift(employees, company, shift_type, start_date, end_date=None, status="Active"):
#     """Create + submit one Shift Assignment per employee, mirroring
#     ShiftAssignmentTool._bulk_assign for the 'Assign Shift' action."""
#     if frappe.session.user == "Guest":
#         frappe.throw(_("Please log in to assign shifts."))

#     if isinstance(employees, str):
#         import json
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
#         try:
#             if not frappe.db.exists("Employee", employee):
#                 failure.append(employee)
#                 continue

#             employee_doc = frappe.db.get_value(
#                 "Employee", employee, ["employee_name", "department"], as_dict=1
#             )

#             doc = frappe.get_doc({
#                 "doctype": "Shift Assignment",
#                 "employee": employee,
#                 "employee_name": employee_doc.employee_name if employee_doc else None,
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
#                 "employee_name": employee_doc.employee_name if employee_doc else employee,
#                 "name": doc.name,
#             })
#         except Exception:
#             frappe.log_error(
#                 f"Weekly Shift Generator - bulk assign failed for employee {employee}.",
#                 reference_doctype="Shift Assignment",
#             )
#             failure.append(employee)

#     return {"success": success, "failure": failure}


# # ---------------------------------------------------------------------------
# # AI Auto Assign (preview)
# # ---------------------------------------------------------------------------

# @frappe.whitelist()
# def ai_auto_assign(department=None, week_start=None):
#     """Return a rules-based weekly shift suggestion for the department, in
#     the same shape as get_weekly_roster, for the user to review.

#     This is a preview only -- it does not write anything to the database.
#     Use bulk_assign_shift (via the Shift Assignment Tool modal) to actually
#     create Shift Assignments.
#     """
#     roster = get_weekly_roster(department=department, week_start=week_start)
#     staff = roster["staff"]
#     week_dates = _week_dates(week_start)
#     day_keys = [cstr(d) for d in week_dates]

#     if not staff:
#         return roster

#     shift_types = frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"], order_by="name asc")
#     if not shift_types:
#         return roster

#     shift_lookup = {s.name: _format_shift_time(s.start_time, s.end_time) for s in shift_types}
#     names = [s.name for s in shift_types]

#     def pick(*keywords):
#         for name in names:
#             lowered = name.lower()
#             if any(k in lowered for k in keywords):
#                 return name
#         return None

#     morning = pick("morning") or names[0]
#     afternoon = pick("afternoon", "evening") or (names[1] if len(names) > 1 else morning)
#     supervisor = pick("supervisor", "lead")

#     rotation = [morning, morning, afternoon, morning, morning, afternoon, None]

#     for idx, row in enumerate(staff):
#         designation = (row.get("designation") or "").lower()
#         existing_leave = {d for d, v in row["shifts"].items() if v["status"] == "Leave"}

#         if supervisor and "supervisor" in designation:
#             for key in day_keys:
#                 if key in existing_leave:
#                     continue
#                 row["shifts"][key] = {"shift_type": supervisor, "status": "Active", "time": shift_lookup.get(supervisor, "")}
#             continue

#         offset = idx % 7
#         for i, key in enumerate(day_keys):
#             if key in existing_leave:
#                 continue
#             shift_name = rotation[(i + offset) % len(rotation)]
#             if shift_name is None:
#                 row["shifts"][key] = {"shift_type": "OFF", "status": "Off", "time": ""}
#             else:
#                 row["shifts"][key] = {"shift_type": shift_name, "status": "Active", "time": shift_lookup.get(shift_name, "")}

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


import json

import frappe
from frappe import _
from frappe.utils import cstr, getdate, add_days, format_time

# ---------------------------------------------------------------------------
# Weekly Shift Generator API
#
# Backs frontend/src/pages/shift/WeeklyShiftGenerator.vue
#
# - get_departments()              -> dropdown options for the page filter
# - get_weekly_roster(department, week_start)
#                                   -> read-only weekly grid: every active
#                                      employee in the department (rows) x
#                                      Sun-Sat (columns), each cell showing
#                                      the Shift Type + start/end time for
#                                      that day (from Shift Assignment), or
#                                      "Leave" / "OFF" when there's none.
# - get_assignment_tool_options()  -> options for the "Shift Assignment Tool"
#                                      modal (companies, shift types,
#                                      designations, branches, employment
#                                      types, grades) -- mirrors the fields on
#                                      the "Shift Assignment Tool" single
#                                      doctype.
# - get_assignment_tool_employees(filters...)
#                                   -> employees matching the modal's quick
#                                      filters, for the selectable employee
#                                      list (mirrors
#                                      ShiftAssignmentTool.get_employees).
# - bulk_assign_shift(employees, company, shift_type, start_date, end_date,
#                      status)
#                                   -> creates + submits one Shift Assignment
#                                      per employee (mirrors
#                                      ShiftAssignmentTool.bulk_assign for the
#                                      "Assign Shift" action).
# - ai_auto_assign(department, week_start)
#                                   -> rules-based suggestion preview, same
#                                      shape as get_weekly_roster.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _week_dates(week_start):
    start = getdate(week_start) if week_start else getdate(frappe.utils.nowdate())
    return [add_days(start, i) for i in range(7)]


def _short_department(department):
    """Strip the trailing ' - Company' suffix Frappe appends to Department links."""
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


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_departments():
    """Return distinct active department names for the department dropdown."""
    rows = frappe.db.sql(
        """
        SELECT DISTINCT department AS value
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND IFNULL(department, '') != ''
        ORDER BY department
        """,
        as_dict=1,
    )

    departments = []
    for row in rows:
        label = _short_department(row.get("value"))
        if label and label not in departments:
            departments.append(label)

    return departments


def _get_default_company():
    return frappe.defaults.get_global_default("company") or frappe.db.get_value(
        "Company", {}, "name", order_by="creation asc"
    )


# ---------------------------------------------------------------------------
# Weekly roster (read-only grid)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_weekly_roster(department=None, week_start=None):
    """Return every active employee in the department with their per-day
    Shift Type + time range for the selected week (Sunday - Saturday)."""
    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    department = _normalize_department(department)
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
                shifts[key] = {"shift_type": "Leave", "status": "Leave", "time": ""}
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
    coverage_level = round((assigned_slots / total_slots) * 100) if total_slots else 0

    return {
        "staff": staff,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": _count_conflicts(staff),
            "total_slots": total_slots,
            "assigned_slots": assigned_slots,
        },
    }


def _count_conflicts(staff):
    """Flag staff who have a Leave day but are still rostered (Active) on
    every other day of the week (no real rest day around the leave)."""
    conflicts = 0
    for row in staff:
        shifts = row["shifts"]
        leave_days = [d for d, v in shifts.items() if v["status"] == "Leave"]
        working_days = [d for d, v in shifts.items() if v["status"] == "Active"]
        if leave_days and len(working_days) >= 6:
            conflicts += 1
    return conflicts


# ---------------------------------------------------------------------------
# Shift Types (for the draft/edit dropdown)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_shift_types():
    """Return real Shift Type records plus the OFF / Leave pseudo-options
    for the draft/edit grid dropdown.

    Each item: { "value": <shift type name or pseudo value>, "label": <display label> }
    """
    shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")

    options = [{"value": row.name, "label": row.name} for row in shift_types]
    options.append({"value": "Leave", "label": "Leave"})
    options.append({"value": "OFF", "label": "OFF"})

    return options


# ---------------------------------------------------------------------------
# Weekly draft (editable grid)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_weekly_draft(department=None, week_start=None):
    """Return every active employee in the department with their per-day
    draft Shift Type for the selected week (Sunday - Saturday).

    Includes BOTH draft (docstatus 0) and already-published (docstatus 1)
    Shift Assignments, so the editor shows the true current state. Cells
    with no Shift Assignment at all default to "OFF".

    Each cell: { value, status, time, draft }
      value  -> Shift Type name, or "OFF" / "Leave"
      status -> "Active" | "Leave" | "Off"
      time   -> "hh:mm A - hh:mm A" or ""
      draft  -> true if this cell comes from an unsubmitted (docstatus 0)
                Shift Assignment, false if published (docstatus 1) or empty
    """
    week_dates = _week_dates(week_start)
    week_start_dt, week_end_dt = week_dates[0], week_dates[-1]
    department = _normalize_department(department)
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
                    # If both a draft and a published row exist for the same
                    # day, prefer the draft (it represents the latest unsaved
                    # edit).
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
                shifts[key] = {"value": "Leave", "status": "Leave", "time": "", "draft": row.docstatus == 0}
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
    coverage_level = round((assigned_slots / total_slots) * 100) if total_slots else 0

    return {
        "staff": staff,
        "has_draft": has_draft,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": _count_conflicts([
                {"shifts": {d: {"status": c["status"]} for d, c in row["shifts"].items()}}
                for row in staff
            ]),
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
    """Pick a Shift Type to attach to a Leave-status Shift Assignment.

    Preference order:
      1. The shift type already assigned to this employee on this day.
      2. The employee's default_shift, if set.
      3. The first Shift Type that exists in the system.
    """
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
    """Return the Shift Assignment (any docstatus < 2) for this employee
    whose date range covers `date`, if any (as a dict, or None). Open-ended
    assignments (end_date IS NULL) are treated as covering `date` only if
    start_date <= date.
    """
    rows = frappe.db.sql(
        """
        SELECT name, employee, docstatus, shift_type, status, start_date, end_date
        FROM `tabShift Assignment`
        WHERE employee = %(employee)s
          AND docstatus < 2
          AND start_date <= %(date)s
          AND (end_date IS NULL OR end_date >= %(date)s OR end_date < start_date)
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
        # Data left over from an earlier bug: a Shift Assignment with
        # end_date before start_date. Treat it as a single-day assignment on
        # start_date and repair it in the database.
        row.end_date = row.start_date
        frappe.db.set_value("Shift Assignment", row.name, "end_date", row.start_date, update_modified=False)

    return row


def _exclude_date_from_assignment(existing, date, employee_doc=None):
    """Remove `date` from an existing Shift Assignment's coverage.

    - If the assignment covers exactly `date` (single day), remove it
      entirely.
    - If `date` is at the start of the range, shrink the range by one day
      from the front (start_date = date + 1). This also handles open-ended
      assignments (end_date IS NULL) by keeping them open-ended.
    - If `date` is at the end of a *closed* range, shrink by one day from
      the back (end_date = date - 1).
    - If `date` is strictly inside a closed range, split into two
      assignments: one covering the days before `date`, and a new one
      (same shift_type/status/docstatus) covering the days after `date`.
    - If `date` is strictly after the start of an *open-ended* range, split
      into a closed "before" assignment (end_date = date - 1) and a new
      open-ended "after" assignment (start_date = date + 1, end_date = None).

    Submitted (docstatus 1) assignments are amended via cancel + recreate,
    since start_date is not `allow_on_submit`.
    """
    start = existing.start_date
    end = existing.end_date  # None means open-ended

    is_open_ended = end is None
    effective_end = end if end is not None else start

    if not is_open_ended and start == date and end == date:
        _remove_assignment(existing.name, existing.docstatus)
        return

    if start == date:
        # Shrink from the front: new start is the day after `date`.
        # Works for both closed and open-ended ranges.
        _resize_assignment(existing, add_days(date, 1), end)
        return

    if not is_open_ended and effective_end == date:
        # Shrink from the back: new end is the day before `date`.
        _resize_assignment(existing, start, add_days(date, -1))
        return

    # `date` is strictly inside the range (or strictly after start of an
    # open-ended range) -- split into two assignments.
    if not employee_doc:
        employee_doc = frappe.db.get_value(
            "Employee", existing.employee, ["employee_name", "company"], as_dict=1
        )

    before_end = add_days(date, -1)
    after_start = add_days(date, 1)
    after_end = None if is_open_ended else end

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
    """Adjust an existing Shift Assignment's start/end date.

    For submitted (docstatus 1) documents, only end_date is
    `allow_on_submit`, so a start_date change requires cancel + recreate.
    """
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
    """Create/update/delete Shift Assignments for each employee/day cell.

    assignments = { employee: { "YYYY-MM-DD": "OFF" | "Leave" | "<Shift Type>" } }

    If publish is True, every touched Shift Assignment is submitted
    (docstatus 1, status Active/Inactive). Otherwise they are left as drafts
    (docstatus 0).

    By default, only dates within the 7-day week starting at `week_start`
    are applied (matching the Weekly Shift Generator grid). Pass an explicit
    `allowed_dates` iterable of "YYYY-MM-DD" strings to apply changes for
    arbitrary dates instead (used by the shift-swap tool).
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to update the roster."))

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
    """Save the weekly grid as draft (unsubmitted) Shift Assignments."""
    return _apply_draft_assignments(department, week_start, assignments, publish=False)


@frappe.whitelist()
def publish_weekly_draft(department=None, week_start=None, assignments=None):
    """Save and submit the weekly grid as published (Active) Shift Assignments."""
    return _apply_draft_assignments(department, week_start, assignments, publish=True)


# ---------------------------------------------------------------------------
# Add Shift Type
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_shift_type(name, start_time, end_time):
    """Create a new Shift Type document.

    start_time / end_time are accepted as "HH:MM" or "HH:MM:SS" strings; if
    end_time is earlier than start_time the Shift Type spans midnight
    (e.g. Night: 22:00 - 06:00), which Shift Type supports natively.
    """
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


# ---------------------------------------------------------------------------
# Shift Assignment Tool (modal) options
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_assignment_tool_options():
    """Return dropdown options for the Shift Assignment Tool modal, mirroring
    the fields on the 'Shift Assignment Tool' single doctype."""
    companies = frappe.get_all("Company", fields=["name"], order_by="name asc")
    shift_types = frappe.get_all("Shift Type", fields=["name"], order_by="name asc")
    branches = frappe.get_all("Branch", fields=["name"], order_by="name asc")
    designations = frappe.get_all("Designation", fields=["name"], order_by="name asc")
    employment_types = frappe.get_all("Employment Type", fields=["name"], order_by="name asc")
    grades = frappe.get_all("Employee Grade", fields=["name"], order_by="name asc")
    departments = frappe.get_all(
        "Department",
        filters={"disabled": 0},
        fields=["name"],
        order_by="name asc",
    )

    default_company = _get_default_company()

    return {
        "companies": [c.name for c in companies],
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
    """Return employees eligible for shift assignment, mirroring
    ShiftAssignmentTool.get_employees_for_assigning_shift.

    An employee is excluded if they already have an Active, submitted Shift
    Assignment overlapping the requested date range (when status == "Active"),
    matching the original tool's behaviour.
    """
    filters = {"status": "Active"}

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


# ---------------------------------------------------------------------------
# Bulk assign (Shift Assignment Tool -> "Assign Shift")
# ---------------------------------------------------------------------------

@frappe.whitelist()
def bulk_assign_shift(employees, company, shift_type, start_date, end_date=None, status="Active"):
    """Create + submit one Shift Assignment per employee, mirroring
    ShiftAssignmentTool._bulk_assign for the 'Assign Shift' action."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to assign shifts."))

    if isinstance(employees, str):
        import json
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
        try:
            if not frappe.db.exists("Employee", employee):
                failure.append(employee)
                continue

            employee_doc = frappe.db.get_value(
                "Employee", employee, ["employee_name", "department"], as_dict=1
            )

            doc = frappe.get_doc({
                "doctype": "Shift Assignment",
                "employee": employee,
                "employee_name": employee_doc.employee_name if employee_doc else None,
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
                "employee_name": employee_doc.employee_name if employee_doc else employee,
                "name": doc.name,
            })
        except Exception:
            frappe.log_error(
                f"Weekly Shift Generator - bulk assign failed for employee {employee}.",
                reference_doctype="Shift Assignment",
            )
            failure.append(employee)

    return {"success": success, "failure": failure}


# ---------------------------------------------------------------------------
# AI Auto Assign (preview)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def ai_auto_assign(department=None, week_start=None):
    """Return a rules-based weekly shift suggestion for the department, in
    the same shape as get_weekly_roster, for the user to review.

    This is a preview only -- it does not write anything to the database.
    Use bulk_assign_shift (via the Shift Assignment Tool modal) to actually
    create Shift Assignments.
    """
    roster = get_weekly_roster(department=department, week_start=week_start)
    staff = roster["staff"]
    week_dates = _week_dates(week_start)
    day_keys = [cstr(d) for d in week_dates]

    if not staff:
        return roster

    shift_types = frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"], order_by="name asc")
    if not shift_types:
        return roster

    shift_lookup = {s.name: _format_shift_time(s.start_time, s.end_time) for s in shift_types}
    names = [s.name for s in shift_types]

    def pick(*keywords):
        for name in names:
            lowered = name.lower()
            if any(k in lowered for k in keywords):
                return name
        return None

    morning = pick("morning") or names[0]
    afternoon = pick("afternoon", "evening") or (names[1] if len(names) > 1 else morning)
    supervisor = pick("supervisor", "lead")

    rotation = [morning, morning, afternoon, morning, morning, afternoon, None]

    for idx, row in enumerate(staff):
        designation = (row.get("designation") or "").lower()
        existing_leave = {d for d, v in row["shifts"].items() if v["status"] == "Leave"}

        if supervisor and "supervisor" in designation:
            for key in day_keys:
                if key in existing_leave:
                    continue
                row["shifts"][key] = {"shift_type": supervisor, "status": "Active", "time": shift_lookup.get(supervisor, "")}
            continue

        offset = idx % 7
        for i, key in enumerate(day_keys):
            if key in existing_leave:
                continue
            shift_name = rotation[(i + offset) % len(rotation)]
            if shift_name is None:
                row["shifts"][key] = {"shift_type": "OFF", "status": "Off", "time": ""}
            else:
                row["shifts"][key] = {"shift_type": shift_name, "status": "Active", "time": shift_lookup.get(shift_name, "")}

    total_slots = len(staff) * 7
    assigned_slots = sum(
        1
        for row in staff
        for value in row["shifts"].values()
        if value["status"] == "Active"
    )
    coverage_level = round((assigned_slots / total_slots) * 100) if total_slots else 0

    return {
        "staff": staff,
        "stats": {
            "coverage_level": coverage_level,
            "conflict_alerts": _count_conflicts(staff),
            "total_slots": total_slots,
            "assigned_slots": assigned_slots,
        },
    }