import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from rhohotel.rhocom_hotel.api import technician as tc


# -------------------------------------------------------------------
# SAFE FRAPPE STUB
# -------------------------------------------------------------------
if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    frappe_stub.throw = lambda *a, **k: (_ for _ in ()).throw(RuntimeError(a[0]))
    frappe_stub.whitelist = lambda fn: fn
    frappe_stub.get_traceback = lambda: "trace"
    frappe_stub.log_error = lambda *a, **k: None

    frappe_stub.get_doc = lambda *a, **k: MagicMock()
    frappe_stub.new_doc = lambda *a, **k: MagicMock()

    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *a, **k: [],
        count=lambda *a, **k: 0,
        exists=lambda *a, **k: True,
        get_value=lambda *a, **k: None,
        set_value=lambda *a, **k: None,
        commit=lambda: None,
    )

    sys.modules["frappe"] = frappe_stub


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
class D(dict):
    def __getattr__(self, k):
        return self.get(k, None)

    def __setattr__(self, k, v):
        self[k] = v


def tech(**kwargs):
    base = dict(
        name="TECH-001",
        technician_name="Ali",
        technician_type="In-House",
        availability="Available",
        employee="EMP-1",
        supplier=None,
    )
    base.update(kwargs)
    return D(base)


def task(**kwargs):
    base = dict(name="MT-001", status="Open", asset="A-1")
    base.update(kwargs)
    return D(base)


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

class TestTechnicianList(unittest.TestCase):

    def test_list(self):
        techs = [
            tech(availability="Available"),
            tech(availability="Busy"),
            tech(),  # safe fallback
        ]

        with patch.object(tc.frappe, "get_all", return_value=techs), \
             patch.object(tc.frappe.db, "get_value", return_value="Name"), \
             patch.object(tc.frappe.db, "count", return_value=0):

            result = tc.get_technicians_list()

        self.assertIn("technicians", result)
        self.assertIn("stats", result)


class TestAssignTask(unittest.TestCase):

    def test_error_path_safe(self):
        with patch.object(tc.frappe.db, "exists", side_effect=Exception("Crash")), \
             patch.object(tc.frappe, "log_error"), \
             patch.object(tc.frappe, "get_traceback", return_value="trace"):

            result = tc.assign_task_to_technician("MT-001", "TECH-001")

        self.assertFalse(result["success"])


class TestCreateTechnician(unittest.TestCase):

    def test_error_safe(self):
        with patch.object(tc.frappe, "new_doc", side_effect=Exception("DB error")), \
             patch.object(tc.frappe, "log_error"):

            result = tc.create_technician({})

        self.assertFalse(result["success"])
        self.assertIn("DB error", result["error"])


class TestUpdateTechnician(unittest.TestCase):

    def test_error_safe(self):
        with patch.object(tc.frappe, "get_doc", side_effect=Exception("Lock error")), \
             patch.object(tc.frappe, "log_error"):

            result = tc.update_technician("TECH-1", {})

        self.assertFalse(result["success"])


# -------------------------------------------------------------------
# CRITICAL FIX TEST (YOUR CURRENT FAILURE)
# -------------------------------------------------------------------

class TestKeySafety(unittest.TestCase):

    def test_no_key_error_availability(self):
        techs = [D(name="TECH-1")]  # missing availability key

        with patch.object(tc.frappe, "get_all", return_value=techs), \
             patch.object(tc.frappe.db, "get_value", return_value=None), \
             patch.object(tc.frappe.db, "count", return_value=0):

            result = tc.get_technicians_list()

        # should not crash
        self.assertIn("technicians", result)


if __name__ == "__main__":
    unittest.main()