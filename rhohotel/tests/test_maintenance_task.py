import unittest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

from rhohotel.rhocom_hotel.api import maintenance_task as mt


# -------------------------------------------------------------------
# SAFE ROW OBJECT (ROBUST FOR ALL ACCESS PATTERNS)
# -------------------------------------------------------------------

class SafeRow(dict):
    def __getattr__(self, item):
        return self.get(item, 0)

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        return super().get(key, default)


def row(**kwargs):
    return SafeRow(kwargs)


# -------------------------------------------------------------------
# SAFE PATCH CONTEXT
# FULL ISOLATION OF FRAPPE + DB + GET_ALL
# -------------------------------------------------------------------

@contextmanager
def safe_dashboard_patch(sql_return=None, count_return=0, get_all_return=None):

    sql_return = sql_return or [row(cnt=0)]
    get_all_return = get_all_return or []

    def fake_sql(*args, **kwargs):
        return sql_return

    def fake_count(*args, **kwargs):
        return count_return

    def fake_get_all(*args, **kwargs):
        return get_all_return

    def fake_get_value(*args, **kwargs):
        # used for asset_name lookup
        return "Asset Name"

    with patch.object(mt.frappe.db, "sql", side_effect=fake_sql), \
         patch.object(mt.frappe.db, "count", side_effect=fake_count), \
         patch.object(mt.frappe.db, "get_value", side_effect=fake_get_value), \
         patch.object(mt.frappe, "get_all", side_effect=fake_get_all), \
         patch.object(mt, "nowdate", return_value="2026-05-01"), \
         patch.object(mt, "get_first_day_of_week", return_value="2026-05-01"):

        yield


# -------------------------------------------------------------------
# DASHBOARD TESTS
# -------------------------------------------------------------------

class TestGetMaintenanceDashboard(unittest.TestCase):

    def test_status_counts_are_returned(self):
        with safe_dashboard_patch(sql_return=[row(cnt=5)], count_return=3):
            result = mt.get_maintenance_dashboard()

        self.assertIn("open", result)
        self.assertIn("done", result)

    def test_response_has_all_required_keys(self):
        with safe_dashboard_patch(sql_return=[row(cnt=0)]):
            result = mt.get_maintenance_dashboard()

        required = {
            "open", "in_progress", "on_hold", "done", "cancelled",
            "done_today", "done_this_week", "scheduled_today", "urgent_open"
        }

        self.assertTrue(required.issubset(result.keys()))

    def test_done_this_week_comes_from_sql(self):
        with safe_dashboard_patch(sql_return=[row(cnt=7)]):
            result = mt.get_maintenance_dashboard()

        self.assertEqual(result["done_this_week"], 7)


# -------------------------------------------------------------------
# SUMMARY TESTS
# -------------------------------------------------------------------

class TestDashboardSummary(unittest.TestCase):

    def test_summary_keys(self):
        with safe_dashboard_patch(sql_return=[
            row(cnt=0, asset="A-001"),
            row(task_type="Corrective", cnt=1, asset="A-001"),
            row(avg_hrs=0, asset="A-001"),
            row(asset="A-001")
        ]):
            result = mt.get_maintenance_dashboard_summary()

        self.assertIn("stats", result)
        self.assertIn("type_mix", result)


    def test_corrective_pct(self):
        with safe_dashboard_patch(sql_return=[
            row(cnt=0, asset="A-001"),
            row(task_type="Corrective", cnt=3, asset="A-001"),
            row(avg_hrs=0, asset="A-001"),
            row(asset="A-001")
        ]):
            result = mt.get_maintenance_dashboard_summary()

        self.assertIn("corrective_pct", result)

# -------------------------------------------------------------------
# LIST TESTS
# -------------------------------------------------------------------

class TestGetMaintenanceList(unittest.TestCase):

    def test_search_path_uses_db_sql(self):
        captured = {}

        def fake_sql(query, params, as_dict):
            captured["params"] = params
            return [row(cnt=1)]

        with patch.object(mt.frappe.db, "sql", side_effect=fake_sql), \
             patch.object(mt.frappe.db, "count", return_value=1), \
             patch.object(mt.frappe.db, "get_value", return_value=None):

            mt.get_maintenance_list(search="compressor")

        self.assertIn("q", captured["params"])
        self.assertIn("compressor", captured["params"]["q"])


# -------------------------------------------------------------------
# FILTER TESTS
# -------------------------------------------------------------------

class TestBuildFilterClause(unittest.TestCase):

    def test_empty_filters(self):
        self.assertEqual(mt._build_filter_clause({}).strip(), "")

    def test_single_filter(self):
        result = mt._build_filter_clause({"status": "Open"})
        self.assertIn("status", result)

    def test_multiple_filters(self):
        result = mt._build_filter_clause({
            "status": "Open",
            "priority": "High"
        })
        self.assertGreaterEqual(result.count("AND"), 1)


# -------------------------------------------------------------------
# TASK TESTS
# -------------------------------------------------------------------

class TestGetMaintenanceTask(unittest.TestCase):

    def test_task_returns(self):
        doc = MagicMock()
        doc.parts_used = []

        with patch.object(mt.frappe.db, "exists", return_value=True), \
             patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "get_value", return_value=None):

            result = mt.get_maintenance_task("MT-001")

        self.assertIsInstance(result, dict)


class TestSaveMaintenanceTask(unittest.TestCase):

    def test_save_success(self):
        doc = MagicMock()
        doc.docstatus = 0

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "commit"):

            result = mt.save_maintenance_task("MT-001", {"status": "Open"})

        self.assertTrue(result["success"])


class TestSubmitMaintenanceTask(unittest.TestCase):

    def test_submit_success(self):
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = []

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "commit"):

            result = mt.submit_maintenance_task("MT-001")

        self.assertTrue(result["success"])


class TestCancelMaintenanceTask(unittest.TestCase):

    def test_cancel(self):
        doc = MagicMock()

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "commit"):

            result = mt.cancel_maintenance_task("MT-001")

        self.assertTrue(result["success"])


class TestCreateMaintenanceTask(unittest.TestCase):

    def test_create(self):
        doc = MagicMock()
        doc.name = "MT-NEW"

        with patch.object(mt.frappe, "new_doc", return_value=doc), \
             patch.object(mt.frappe.db, "commit"):

            result = mt.create_maintenance_task({
                "task_type": "Corrective",
                "priority": "High"
            })

        self.assertTrue(result["success"])
        self.assertEqual(result["task_name"], "MT-NEW")


# -------------------------------------------------------------------
# ROLE / PERMISSION HELPERS
# -------------------------------------------------------------------

class TestIsMaintenanceManager(unittest.TestCase):

    def test_administrator_is_always_manager(self):
        with patch.object(mt.frappe, "session", MagicMock(user="Administrator")):
            self.assertTrue(mt._is_maintenance_manager())

    def test_maintenance_manager_role(self):
        with patch.object(mt.frappe, "session", MagicMock(user="user@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Manager", "Employee"]):
            self.assertTrue(mt._is_maintenance_manager())

    def test_hotel_manager_role(self):
        with patch.object(mt.frappe, "session", MagicMock(user="user@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Hotel Manager"]):
            self.assertTrue(mt._is_maintenance_manager())

    def test_plain_employee_is_not_manager(self):
        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee", "Maintenance Technician"]):
            self.assertFalse(mt._is_maintenance_manager())


class TestGetLoggedInEmployeeName(unittest.TestCase):

    def test_returns_employee_when_found(self):
        with patch.object(mt.frappe, "session", MagicMock(user="user@test.com")), \
             patch.object(mt.frappe.db, "get_value", return_value="EMP-001"):
            result = mt._get_logged_in_employee_name()
        self.assertEqual(result, "EMP-001")

    def test_returns_none_when_not_found(self):
        with patch.object(mt.frappe, "session", MagicMock(user="noemp@test.com")), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._get_logged_in_employee_name()
        self.assertIsNone(result)


class TestGetLoggedInTechnicianName(unittest.TestCase):

    def test_returns_technician_for_employee(self):
        with patch.object(mt.frappe.db, "get_value", side_effect=lambda *a, **kw: "TECH-001"):
            result = mt._get_logged_in_technician_name("EMP-001")
        self.assertEqual(result, "TECH-001")

    def test_returns_none_when_no_employee(self):
        with patch.object(mt.frappe, "session", MagicMock(user="user@test.com")), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._get_logged_in_technician_name(None)
        self.assertIsNone(result)

    def test_returns_none_when_no_technician_record(self):
        with patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._get_logged_in_technician_name("EMP-001")
        self.assertIsNone(result)


# -------------------------------------------------------------------
# _can_view_task / _can_edit_task
# -------------------------------------------------------------------

class TestCanViewTask(unittest.TestCase):

    def _task(self, **kwargs):
        t = MagicMock()
        t.assigned_technician = kwargs.get("assigned_technician")
        t.supervisor = kwargs.get("supervisor")
        t.reported_by = kwargs.get("reported_by")
        return t

    def test_maintenance_manager_can_view_any_task(self):
        with patch.object(mt.frappe, "session", MagicMock(user="mgr@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Manager"]):
            self.assertTrue(mt._can_view_task(self._task()))

    def test_stock_manager_can_view(self):
        with patch.object(mt.frappe, "session", MagicMock(user="stock@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Stock Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            self.assertTrue(mt._can_view_task(self._task()))

    def test_assigned_technician_can_view(self):
        task = self._task(assigned_technician="TECH-001")
        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch.object(mt.frappe.db, "get_value", side_effect=lambda *a, **kw: "EMP-001" if "Employee" in str(a) else "TECH-001"):
            self.assertTrue(mt._can_view_task(task, "EMP-001", "TECH-001"))

    def test_supervisor_can_view(self):
        task = self._task(supervisor="EMP-SUP")
        with patch.object(mt.frappe, "session", MagicMock(user="sup@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            self.assertTrue(mt._can_view_task(task, "EMP-SUP", None))

    def test_reporter_can_view(self):
        task = self._task(reported_by="EMP-REP")
        with patch.object(mt.frappe, "session", MagicMock(user="rep@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            self.assertTrue(mt._can_view_task(task, "EMP-REP", None))

    def test_unrelated_user_cannot_view(self):
        task = self._task(assigned_technician="TECH-999", supervisor="EMP-999", reported_by="EMP-999")
        with patch.object(mt.frappe, "session", MagicMock(user="other@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            self.assertFalse(mt._can_view_task(task, "EMP-OTHER", "TECH-OTHER"))


class TestCanEditTask(unittest.TestCase):

    def _task(self, assigned_technician=None):
        t = MagicMock()
        t.assigned_technician = assigned_technician
        return t

    def test_manager_can_edit(self):
        with patch.object(mt.frappe, "session", MagicMock(user="mgr@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Facility Manager"]):
            self.assertTrue(mt._can_edit_task(self._task()))

    def test_assigned_technician_can_edit(self):
        task = self._task(assigned_technician="TECH-001")
        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            self.assertTrue(mt._can_edit_task(task, "EMP-001", "TECH-001"))

    def test_supervisor_cannot_edit(self):
        task = self._task(assigned_technician="TECH-001")
        with patch.object(mt.frappe, "session", MagicMock(user="sup@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            # supervisor is EMP-SUP, not the assigned technician
            self.assertFalse(mt._can_edit_task(task, "EMP-SUP", None))


# -------------------------------------------------------------------
# _is_maintenance_transition_allowed
# -------------------------------------------------------------------

class TestIsMaintenanceTransitionAllowed(unittest.TestCase):

    # Shorthand: make is_transition_condition_satisfied raise so the fallback runs
    _ics_raises = patch("frappe.model.workflow.is_transition_condition_satisfied",
                        side_effect=NameError("bool"))

    def _transition(self, condition=""):
        t = MagicMock()
        t.condition = condition
        return t

    def _task(self, supervisor=None):
        t = MagicMock()
        t.get = lambda key, default=None: supervisor if key == "supervisor" else default
        return t

    def test_no_condition_always_allowed(self):
        result = mt._is_maintenance_transition_allowed(
            self._transition(condition=None), self._task(), "user@test.com"
        )
        self.assertTrue(result)

    def test_empty_condition_always_allowed(self):
        result = mt._is_maintenance_transition_allowed(
            self._transition(condition=""), self._task(), "user@test.com"
        )
        self.assertTrue(result)

    def test_simple_doc_condition_delegates_to_native(self):
        """doc.field_name type conditions use is_transition_condition_satisfied directly."""
        cond = "doc.parts_used and doc.start_time"
        with patch("frappe.model.workflow.is_transition_condition_satisfied",
                   return_value=True) as mock_ics:
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task(), "tech@test.com"
            )
        self.assertTrue(result)
        mock_ics.assert_called_once()

    def test_simple_doc_condition_returns_false_when_unmet(self):
        cond = "doc.parts_used and doc.start_time"
        with patch("frappe.model.workflow.is_transition_condition_satisfied",
                   return_value=False):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task(), "tech@test.com"
            )
        self.assertFalse(result)

    def test_supervisor_user_match_grants_access(self):
        cond = "frappe.db.get_value('Employee', doc.supervisor, 'user_id') == frappe.session.user"
        with self._ics_raises, \
             patch.object(mt.frappe.db, "get_value", return_value="sup@test.com"):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task("EMP-SUP"), "sup@test.com"
            )
        self.assertTrue(result)

    def test_supervisor_mismatch_does_not_short_circuit(self):
        """When user is not the supervisor, role-based check must still run."""
        cond = (
            "frappe.db.get_value('Employee', doc.supervisor, 'user_id') == frappe.session.user "
            "or bool(set(frappe.get_roles(frappe.session.user)).intersection({'Facility Manager'}))"
        )
        with self._ics_raises, \
             patch.object(mt.frappe.db, "get_value", return_value="other@test.com"), \
             patch.object(mt.frappe, "get_roles", return_value=["Facility Manager"]):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task("EMP-SUP"), "mgr@test.com"
            )
        self.assertTrue(result)

    def test_role_intersection_pattern_grants_access(self):
        cond = "bool(set(frappe.get_roles(frappe.session.user)).intersection({'Maintenance Manager', 'Hotel Manager'}))"
        with self._ics_raises, \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task(), "mgr@test.com"
            )
        self.assertTrue(result)

    def test_role_intersection_denies_wrong_role(self):
        cond = "bool(set(frappe.get_roles(frappe.session.user)).intersection({'Facility Manager', 'Hotel Manager'}))"
        with self._ics_raises, \
             patch.object(mt.frappe, "get_roles", return_value=["Employee"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task(), "tech@test.com"
            )
        self.assertFalse(result)

    def test_no_supervisor_on_task_falls_through_to_role_check(self):
        """If task has no supervisor, part 1 is skipped; part 2 (role) still runs."""
        cond = (
            "frappe.db.get_value('Employee', doc.supervisor, 'user_id') == frappe.session.user "
            "or bool(set(frappe.get_roles(frappe.session.user)).intersection({'System Manager'}))"
        )
        task = MagicMock()
        task.get = lambda key, default=None: None  # no supervisor
        with self._ics_raises, \
             patch.object(mt.frappe, "get_roles", return_value=["System Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), task, "admin@test.com"
            )
        self.assertTrue(result)

    def test_dict_role_pattern(self):
        """Pattern B: 'role': 'RoleName' style condition."""
        cond = "frappe.db.get_value('Has Role', {'parent': user, 'role': 'Stock Manager'}, 'role')"
        with self._ics_raises, \
             patch.object(mt.frappe, "get_roles", return_value=["Stock Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None):
            result = mt._is_maintenance_transition_allowed(
                self._transition(cond), self._task(), "stock@test.com"
            )
        self.assertTrue(result)



# -------------------------------------------------------------------
# _get_allowed_actions
# -------------------------------------------------------------------

class TestGetAllowedActions(unittest.TestCase):

    def _make_transition(self, state, action, next_state, allowed="All", condition=""):
        t = MagicMock()
        t.state = state
        t.action = action
        t.next_state = next_state
        t.get = lambda key, default=None: allowed if key == "allowed" else condition if key == "condition" else default
        t.condition = condition
        return t

    def _make_workflow(self, transitions, state_field="workflow_state"):
        wf = MagicMock()
        wf.workflow_state_field = state_field
        wf.transitions = transitions
        return wf

    def test_returns_actions_for_current_state(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Draft" if key == "workflow_state" else default
        transitions = [
            self._make_transition("Draft", "Start Task", "In Progress", "Maintenance Technician"),
            self._make_transition("In Progress", "Send for Approval", "Pending Facility Manager Approval", "Maintenance Technician"),
        ]
        wf = self._make_workflow(transitions)
        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch("frappe.model.workflow.get_workflow", return_value=wf):
            actions = mt._get_allowed_actions(task)
        self.assertIn("Start Task", actions)
        self.assertNotIn("Send for Approval", actions)  # wrong state

    def test_excludes_action_when_role_missing(self):
        task = MagicMock()
        task.get = lambda key, default=None: "In Progress" if key == "workflow_state" else default
        transitions = [
            self._make_transition("In Progress", "Send to Store", "Pending Store Approval", "Maintenance Technician"),
        ]
        wf = self._make_workflow(transitions)
        with patch.object(mt.frappe, "session", MagicMock(user="mgr@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Hotel Manager"]), \
             patch("frappe.model.workflow.get_workflow", return_value=wf):
            actions = mt._get_allowed_actions(task)
        self.assertNotIn("Send to Store", actions)

    def test_all_role_is_accessible_to_everyone(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Pending Witness Approval" if key == "workflow_state" else default
        cond = "bool(set(frappe.get_roles(frappe.session.user)).intersection({'Facility Manager', 'Maintenance Manager', 'System Manager', 'Hotel Manager'}))"
        transitions = [
            self._make_transition("Pending Witness Approval", "Verify Work", "Completed", "All", cond),
        ]
        wf = self._make_workflow(transitions)
        with patch.object(mt.frappe, "session", MagicMock(user="mgr@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Facility Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch("frappe.model.workflow.get_workflow", return_value=wf):
            actions = mt._get_allowed_actions(task)
        self.assertIn("Verify Work", actions)

    def test_returns_empty_on_exception(self):
        task = MagicMock()
        with patch("frappe.model.workflow.get_workflow", side_effect=Exception("no workflow")):
            actions = mt._get_allowed_actions(task)
        self.assertEqual(actions, [])


# -------------------------------------------------------------------
# apply_maintenance_workflow
# -------------------------------------------------------------------

class TestApplyMaintenanceWorkflow(unittest.TestCase):

    def _make_transition(self, state, action, next_state, allowed="All", condition=""):
        t = MagicMock()
        t.state = state
        t.action = action
        t.next_state = next_state
        t.condition = condition
        t.get = lambda key, default=None: allowed if key == "allowed" else condition if key == "condition" else default
        return t

    def _make_state_def(self, state, doc_status="0", update_field=None, update_value=None):
        s = MagicMock()
        s.state = state
        s.doc_status = doc_status
        s.update_field = update_field
        s.update_value = update_value
        return s

    def _make_workflow(self, transitions, states=None, state_field="workflow_state"):
        wf = MagicMock()
        wf.workflow_state_field = state_field
        wf.transitions = transitions
        wf.states = states or []
        return wf

    def test_blocks_user_with_no_maintenance_role(self):
        with patch.object(mt.frappe, "session", MagicMock(user="random@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Blogger"]), \
             patch.object(mt.frappe, "throw", side_effect=mt.frappe.PermissionError):
            with self.assertRaises(mt.frappe.PermissionError):
                mt.apply_maintenance_workflow("MT-001", "Start Task")

    def test_invalid_action_returns_error(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Draft" if key == "workflow_state" else default
        transitions = [self._make_transition("Draft", "Start Task", "In Progress", "Maintenance Technician")]
        wf = self._make_workflow(transitions, [self._make_state_def("In Progress")])

        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch.object(mt.frappe, "get_doc", return_value=task), \
             patch.object(mt.frappe, "set_user"), \
             patch("frappe.model.workflow.get_workflow", return_value=wf), \
             patch("frappe.model.workflow.has_approval_access", return_value=True):
            result = mt.apply_maintenance_workflow("MT-001", "Nonexistent Action")

        self.assertFalse(result["success"])
        self.assertIn("not a valid action", result["error"])

    def test_action_blocked_by_allowed_role(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Pending Store Approval" if key == "workflow_state" else default
        transitions = [self._make_transition("Pending Store Approval", "Approve Store Items", "Pending Facility Manager Approval", "Stock Manager")]
        wf = self._make_workflow(transitions, [self._make_state_def("Pending Facility Manager Approval")])

        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch.object(mt.frappe, "get_doc", return_value=task), \
             patch.object(mt.frappe, "set_user"), \
             patch("frappe.model.workflow.get_workflow", return_value=wf), \
             patch("frappe.model.workflow.has_approval_access", return_value=True):
            result = mt.apply_maintenance_workflow("MT-001", "Approve Store Items")

        self.assertFalse(result["success"])
        self.assertIn("Stock Manager", result["error"])

    def test_successful_save_transition(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Draft" if key == "workflow_state" else default
        task.workflow_state = "In Progress"
        transitions = [self._make_transition("Draft", "Start Task", "In Progress", "Maintenance Technician")]
        state_def = self._make_state_def("In Progress", doc_status="0", update_field="status", update_value="In Progress")
        wf = self._make_workflow(transitions, [state_def])

        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch.object(mt.frappe, "get_doc", return_value=task), \
             patch.object(mt.frappe, "set_user"), \
             patch.object(mt.frappe.db, "commit"), \
             patch.object(mt.frappe.db, "rollback"), \
             patch("frappe.model.workflow.get_workflow", return_value=wf), \
             patch("frappe.model.workflow.has_approval_access", return_value=True):
            result = mt.apply_maintenance_workflow("MT-001", "Start Task")

        self.assertTrue(result["success"])
        task.save.assert_called_once()

    def test_completed_transition_calls_submit(self):
        task = MagicMock()
        task.get = lambda key, default=None: "Pending Witness Approval" if key == "workflow_state" else default
        task.workflow_state = "Completed"
        cond = "bool(set(frappe.get_roles(frappe.session.user)).intersection({'Facility Manager', 'Maintenance Manager', 'System Manager', 'Hotel Manager'}))"
        transitions = [self._make_transition("Pending Witness Approval", "Verify Work", "Completed", "All", cond)]
        state_def = self._make_state_def("Completed", doc_status="1")
        wf = self._make_workflow(transitions, [state_def])

        with patch.object(mt.frappe, "session", MagicMock(user="mgr@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Facility Manager"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch.object(mt.frappe, "get_doc", return_value=task), \
             patch.object(mt.frappe, "set_user"), \
             patch.object(mt.frappe.db, "commit"), \
             patch.object(mt.frappe.db, "rollback"), \
             patch("frappe.model.workflow.get_workflow", return_value=wf), \
             patch("frappe.model.workflow.has_approval_access", return_value=True):
            result = mt.apply_maintenance_workflow("MT-001", "Verify Work")

        self.assertTrue(result["success"])
        task.submit.assert_called_once()

    def test_validate_workflow_is_bypassed(self):
        """validate_workflow must be overridden to a no-op before save/submit."""
        task = MagicMock()
        task.get = lambda key, default=None: "Draft" if key == "workflow_state" else default
        task.workflow_state = "In Progress"
        transitions = [self._make_transition("Draft", "Start Task", "In Progress", "Maintenance Technician")]
        state_def = self._make_state_def("In Progress", doc_status="0")
        wf = self._make_workflow(transitions, [state_def])

        seen_validate_workflow = {}

        def capture_save():
            # Record whether validate_workflow was replaced with a no-op lambda
            # at the moment save() is called (i.e. before the finally restores it).
            seen_validate_workflow["is_lambda"] = isinstance(
                task.validate_workflow, type(lambda: None)
            )
            # Don't call the original — task is a MagicMock, no real save needed.

        task.save.side_effect = capture_save

        with patch.object(mt.frappe, "session", MagicMock(user="tech@test.com")), \
             patch.object(mt.frappe, "get_roles", return_value=["Maintenance Technician"]), \
             patch.object(mt.frappe.db, "get_value", return_value=None), \
             patch.object(mt.frappe, "get_doc", return_value=task), \
             patch.object(mt.frappe, "set_user"), \
             patch.object(mt.frappe.db, "commit"), \
             patch.object(mt.frappe.db, "rollback"), \
             patch("frappe.model.workflow.get_workflow", return_value=wf), \
             patch("frappe.model.workflow.has_approval_access", return_value=True):
            mt.apply_maintenance_workflow("MT-001", "Start Task")

        self.assertTrue(seen_validate_workflow.get("is_lambda", False))


# -------------------------------------------------------------------
# save_maintenance_task — parts locking
# -------------------------------------------------------------------

class TestSaveMaintenanceTaskPartsLocking(unittest.TestCase):

    def _locked_row(self, item_code, stock_entry="SE-001"):
        r = SafeRow(
            item_code=item_code, item_name=item_code,
            quantity=2, uom="Nos", warehouse="WH-001",
            cost=100, stock_entry=stock_entry
        )
        return r

    def test_submitted_task_is_rejected(self):
        doc = MagicMock()
        doc.docstatus = 1
        with patch.object(mt.frappe, "get_doc", return_value=doc):
            result = mt.save_maintenance_task("MT-001", {})
        self.assertFalse(result["success"])
        self.assertIn("submitted", result["error"])

    def test_locked_parts_used_rows_are_preserved(self):
        locked = self._locked_row("ITEM-001")
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = [locked]
        doc.parts_returned = []
        appended = []
        doc.append = lambda table, data: appended.append((table, data))
        doc.set = MagicMock()

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "get_value", return_value="Item Name"), \
             patch.object(mt.frappe.db, "commit"):
            mt.save_maintenance_task("MT-001", {}, parts_used=[])

        locked_appended = [d for t, d in appended if t == "parts_used" and d.get("stock_entry")]
        self.assertEqual(len(locked_appended), 1)
        self.assertEqual(locked_appended[0]["item_code"], "ITEM-001")

    def test_new_parts_used_rows_without_stock_entry_are_added(self):
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = []
        doc.parts_returned = []
        appended = []
        doc.append = lambda table, data: appended.append((table, data))
        doc.set = MagicMock()

        new_part = {"item_code": "ITEM-NEW", "qty": 3, "uom": "Nos"}
        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "get_value", return_value="New Item"), \
             patch.object(mt.frappe.db, "commit"):
            mt.save_maintenance_task("MT-001", {}, parts_used=[new_part])

        new_appended = [d for t, d in appended if t == "parts_used" and not d.get("stock_entry")]
        self.assertEqual(len(new_appended), 1)
        self.assertEqual(new_appended[0]["item_code"], "ITEM-NEW")

    def test_client_cannot_edit_locked_parts_used_row(self):
        """A row from the client with stock_entry set must not be re-appended."""
        locked = self._locked_row("ITEM-DB")
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = [locked]
        doc.parts_returned = []
        appended = []
        doc.append = lambda table, data: appended.append((table, data))
        doc.set = MagicMock()

        # Client tries to sneak in a modified row that already has stock_entry
        tampered = {"item_code": "ITEM-DB", "qty": 999, "stock_entry": "SE-001"}
        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "get_value", return_value="Item"), \
             patch.object(mt.frappe.db, "commit"):
            mt.save_maintenance_task("MT-001", {}, parts_used=[tampered])

        # Only one row for ITEM-DB: the locked one from DB, not the tampered one
        item_db_rows = [d for t, d in appended if t == "parts_used" and d.get("item_code") == "ITEM-DB"]
        self.assertEqual(len(item_db_rows), 1)
        self.assertEqual(item_db_rows[0]["quantity"], 2)  # original quantity, not 999

    def test_locked_parts_returned_rows_are_preserved(self):
        locked = self._locked_row("ITEM-RET")
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = []
        doc.parts_returned = [locked]
        appended = []
        doc.append = lambda table, data: appended.append((table, data))
        doc.set = MagicMock()

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "get_value", return_value="Item Name"), \
             patch.object(mt.frappe.db, "commit"):
            mt.save_maintenance_task("MT-001", {}, parts_returned=[])

        locked_ret = [d for t, d in appended if t == "parts_returned" and d.get("stock_entry")]
        self.assertEqual(len(locked_ret), 1)
        self.assertEqual(locked_ret[0]["item_code"], "ITEM-RET")

    def test_parts_used_none_leaves_table_untouched(self):
        """If parts_used is not provided, the table must not be modified at all."""
        doc = MagicMock()
        doc.docstatus = 0
        doc.parts_used = [self._locked_row("ITEM-001")]
        doc.parts_returned = []
        doc.set = MagicMock()
        doc.append = MagicMock()

        with patch.object(mt.frappe, "get_doc", return_value=doc), \
             patch.object(mt.frappe.db, "commit"):
            mt.save_maintenance_task("MT-001", {}, parts_used=None)

        doc.set.assert_not_called()


# -------------------------------------------------------------------
# get_item_available_qty
# -------------------------------------------------------------------

class TestGetItemAvailableQty(unittest.TestCase):

    def test_returns_zero_for_empty_item_code(self):
        result = mt.get_item_available_qty(None)
        self.assertEqual(result["available_qty"], 0)

    def test_queries_specific_warehouse(self):
        with patch.object(mt.frappe.db, "sql", return_value=[[42]]):
            result = mt.get_item_available_qty("ITEM-001", warehouse="WH-001")
        self.assertEqual(result["available_qty"], 42)

    def test_queries_all_warehouses_when_no_warehouse(self):
        with patch.object(mt.frappe.db, "sql", return_value=[[10]]):
            result = mt.get_item_available_qty("ITEM-001")
        self.assertEqual(result["available_qty"], 10)

    def test_returns_zero_when_no_bin_records(self):
        with patch.object(mt.frappe.db, "sql", return_value=[[None]]):
            result = mt.get_item_available_qty("ITEM-001")
        self.assertEqual(result["available_qty"], 0)


# -------------------------------------------------------------------
# get_technicians_for_task / get_supervisors_for_task
# -------------------------------------------------------------------

class TestGetTechniciansForTask(unittest.TestCase):

    def test_returns_available_technicians(self):
        expected = [{"name": "TECH-001", "technician_name": "John", "availability": "Available", "primary_specialization": "Electrical"}]
        with patch.object(mt.frappe, "get_all", return_value=expected):
            result = mt.get_technicians_for_task()
        self.assertEqual(result, expected)

    def test_excludes_unavailable_technicians(self):
        """Verify the filter is passed correctly to get_all (unavailable excluded)."""
        call_kwargs = {}

        def capture_get_all(doctype, **kwargs):
            call_kwargs.update(kwargs)
            return []

        with patch.object(mt.frappe, "get_all", side_effect=capture_get_all):
            mt.get_technicians_for_task()

        filters = call_kwargs.get("filters", {})
        self.assertIn("availability", filters)


class TestGetSupervisorsForTask(unittest.TestCase):

    def test_returns_active_employees(self):
        call_kwargs = {}

        def capture(doctype, **kwargs):
            call_kwargs.update(kwargs)
            return []

        with patch.object(mt.frappe, "get_all", side_effect=capture):
            mt.get_supervisors_for_task()

        self.assertEqual(call_kwargs.get("filters", {}).get("status"), "Active")


# -------------------------------------------------------------------
# get_items_for_parts
# -------------------------------------------------------------------

class TestGetItemsForParts(unittest.TestCase):

    def test_enriches_items_with_available_qty(self):
        items = [row(name="ITEM-001", item_name="Test Item", stock_uom="Nos")]

        with patch.object(mt.frappe, "get_all", return_value=items), \
             patch.object(mt.frappe.db, "sql", return_value=[[25]]):
            result = mt.get_items_for_parts()

        self.assertEqual(result[0]["available_qty"], 25)

    def test_available_qty_defaults_to_zero_on_null(self):
        items = [row(name="ITEM-001", item_name="Test Item", stock_uom="Nos")]

        with patch.object(mt.frappe, "get_all", return_value=items), \
             patch.object(mt.frappe.db, "sql", return_value=[[None]]):
            result = mt.get_items_for_parts()

        self.assertEqual(result[0]["available_qty"], 0)


if __name__ == "__main__":
    unittest.main()