import datetime
import sys
import types
import unittest
from unittest.mock import Mock, patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _whitelist(*args, **kwargs):
        def _decorator(fn):
            return fn
        return _decorator if not args else args[0]

    def _default_throw(message, *args, **kwargs):
        raise RuntimeError(message)

    frappe_stub._ = lambda text: text
    frappe_stub.whitelist = _whitelist
    frappe_stub.throw = _default_throw
    frappe_stub.PermissionError = PermissionError
    frappe_stub.session = types.SimpleNamespace(user="frontdeskuser2@gmail.com")
    frappe_stub.get_roles = lambda user=None: []
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub.new_doc = lambda *args, **kwargs: None
    frappe_stub.log_error = lambda *args, **kwargs: None
    frappe_stub.defaults = types.SimpleNamespace(get_global_default=lambda key: "")
    frappe_stub.db = types.SimpleNamespace(
        get_value=lambda *args, **kwargs: None,
        exists=lambda *args, **kwargs: True,
        sql=lambda *args, **kwargs: [],
        rollback=lambda: None,
    )

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.cstr = lambda value="": "" if value is None else str(value)
    utils_stub.getdate = lambda value=None: value if isinstance(value, datetime.date) else datetime.date.fromisoformat(str(value))
    utils_stub.now_datetime = lambda: datetime.datetime(2026, 6, 24, 12, 0, 0)
    utils_stub.add_days = lambda value, days: utils_stub.getdate(value) + datetime.timedelta(days=days)
    utils_stub.format_time = lambda value, fmt=None: str(value)

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


from rhohotel.rhocom_hotel.api import swap_request as sr


class DotDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


class TestApproveSwapRequest(unittest.TestCase):
    def test_department_manager_approval_applies_roster_with_request_department(self):
        doc = types.SimpleNamespace(
            name="SWP-2026-00322",
            department="Front Desk - RH",
            swap_date="2026-06-25",
            requesting_employee="EMP-001",
            requesting_employee_name="Requesting Staff",
            requesting_shift="Morning",
            requesting_shift_time="08:00 - 16:00",
            target_employee="EMP-002",
            target_employee_name="Target Staff",
            target_shift="Evening",
            target_shift_time="16:00 - 00:00",
            request_reason="Need coverage",
            manager_note="",
            status="Pending",
            check_status="Clear",
            submitted_by="staff@example.com",
            submitted_on="2026-06-24 09:00:00",
            approved_by="",
            approved_on=None,
            rejected_by="",
            rejected_on=None,
            save=Mock(),
        )

        manager = DotDict(name="EMP-MGR", department="Front Desk - RH")
        check = {
            "ok": True,
            "requesting_employee": {"employee": "EMP-001", "value": "Morning"},
            "target_employee": {"employee": "EMP-002", "value": "Evening"},
        }

        with (
            patch.object(sr, "_is_manager", return_value=True),
            patch.object(sr, "_is_super_manager", return_value=False),
            patch.object(sr, "_get_logged_in_employee", return_value=manager),
            patch.object(sr.frappe, "get_doc", return_value=doc),
            patch.object(sr, "_build_checks", return_value=check),
            patch.object(sr, "_apply_draft_assignments", return_value={"ok": True, "warnings": []}) as apply_assignments,
            patch.object(sr, "_get_employee_shift", side_effect=lambda employee, date: {"employee": employee, "date": str(date)}),
        ):
            result = sr.approve_swap_request("SWP-2026-00322")

        self.assertTrue(result["ok"])
        apply_assignments.assert_called_once()
        self.assertEqual(apply_assignments.call_args.kwargs["department"], "Front Desk - RH")


if __name__ == "__main__":
    unittest.main()
