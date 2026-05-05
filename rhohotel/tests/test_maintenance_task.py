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


if __name__ == "__main__":
    unittest.main()