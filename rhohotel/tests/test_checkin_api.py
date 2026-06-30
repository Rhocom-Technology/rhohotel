import sys
import types
import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _whitelist(*args, **kwargs):
        def _decorator(fn):
            return fn

        return _decorator

    frappe_stub._ = lambda text: text
    frappe_stub.throw = lambda message: (_ for _ in ()).throw(RuntimeError(message))
    frappe_stub.whitelist = _whitelist
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub.log_error = lambda *args, **kwargs: None
    frappe_stub.get_traceback = lambda: ""
    frappe_stub.db = types.SimpleNamespace(
        exists=lambda *args, **kwargs: False,
        sql=lambda *args, **kwargs: [],
        get_value=lambda *args, **kwargs: None,
    )

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.now_datetime = lambda: "2026-05-23 12:00:00"
    utils_stub.add_days = lambda dt, days: dt
    utils_stub.flt = lambda value: float(value or 0)
    utils_stub.cint = lambda value: int(value or 0)
    utils_stub.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    utils_stub.getdate = lambda value: value if isinstance(value, date) and not isinstance(value, datetime) else utils_stub.get_datetime(value).date()
    utils_stub.today = lambda: "2026-05-23"

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub
    sys.modules["frappe.model"] = types.ModuleType("frappe.model")
    document_stub = types.ModuleType("frappe.model.document")
    document_stub.Document = object
    sys.modules["frappe.model.document"] = document_stub


from rhohotel.rhocom_hotel.api import checkin as checkin_api
from rhohotel.rhocom_hotel.doctype.hotel_settings import hotel_settings as hotel_settings_api


class FakeCheckinDoc(types.SimpleNamespace):
    def as_dict(self):
        return {
            "name": self.name,
            "reservation": self.reservation,
            "reservation_source": self.reservation_source,
        }


class FakeReservationDoc(types.SimpleNamespace):
    pass


class TestCheckinApi(unittest.TestCase):
    def test_get_checkin_detail_skips_reservation_ledger_for_corporate(self):
        doc = FakeCheckinDoc(
            name="CHK-0001",
            reservation="",
            canonical_reservation="RES-CORP-0001",
            reservation_source="Reservation",
        )

        payment_summary_fn = Mock(return_value={
            "invoices": [{"name": "INV-RES-1", "grand_total": 1000, "outstanding_amount": 200}],
            "payment_entries": [{"name": "PAY-RES-1", "amount": 800}],
        })
        fake_reservation_module = types.ModuleType("hotel_reservation")
        fake_reservation_module.get_payment_summary_for_reservation = payment_summary_fn

        def fake_exists(doctype, name):
            if doctype == "Hotel Room Check In":
                return True
            if doctype == "Hotel Reservation" and name == "RES-CORP-0001":
                return True
            return False

        def fake_get_doc(doctype, name):
            if doctype == "Hotel Reservation" and name == "RES-CORP-0001":
                return FakeReservationDoc(name=name, reservation_type="Corporate", rooms=[])
            return doc

        with (
            patch.object(checkin_api.frappe.db, "exists", side_effect=fake_exists),
            patch.object(checkin_api.frappe, "get_doc", side_effect=fake_get_doc),
            patch.object(checkin_api.frappe.db, "sql", return_value=[]),
            patch.object(checkin_api.frappe.db, "get_value", return_value="Corporate"),
            patch.dict(
                sys.modules,
                {
                    "rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation": fake_reservation_module,
                },
            ),
        ):
            result = checkin_api.get_checkin_detail("CHK-0001")

        payment_summary_fn.assert_not_called()
        self.assertEqual(result.get("invoices"), [])
        self.assertEqual(result.get("payments"), [])

    def test_get_checkin_detail_keeps_reservation_ledger_for_non_corporate(self):
        doc = FakeCheckinDoc(
            name="CHK-0002",
            reservation="",
            canonical_reservation="RES-IND-0001",
            reservation_source="Reservation",
        )

        payment_summary_fn = Mock(return_value={
            "invoices": [
                {
                    "name": "INV-RES-2",
                    "grand_total": 1500,
                    "outstanding_amount": 300,
                    "is_return": 0,
                    "posting_date": "2026-05-23",
                    "status": "Unpaid",
                }
            ],
            "payment_entries": [
                {
                    "name": "PAY-RES-2",
                    "amount": 1200,
                    "posting_date": "2026-05-23",
                    "mode_of_payment": "Cash",
                    "remarks": "Reservation payment",
                }
            ],
        })
        fake_reservation_module = types.ModuleType("hotel_reservation")
        fake_reservation_module.get_payment_summary_for_reservation = payment_summary_fn

        def fake_exists(doctype, name):
            if doctype == "Hotel Room Check In":
                return True
            if doctype == "Hotel Reservation" and name == "RES-IND-0001":
                return True
            return False

        def fake_get_doc(doctype, name):
            if doctype == "Hotel Reservation" and name == "RES-IND-0001":
                return FakeReservationDoc(name=name, reservation_type="Individual", rooms=[])
            return doc

        with (
            patch.object(checkin_api.frappe.db, "exists", side_effect=fake_exists),
            patch.object(checkin_api.frappe, "get_doc", side_effect=fake_get_doc),
            patch.object(checkin_api.frappe.db, "sql", return_value=[]),
            patch.object(checkin_api.frappe.db, "get_value", return_value="Individual"),
            patch.dict(
                sys.modules,
                {
                    "rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation": fake_reservation_module,
                },
            ),
        ):
            result = checkin_api.get_checkin_detail("CHK-0002")

        payment_summary_fn.assert_called_once_with("RES-IND-0001")
        self.assertEqual(len(result.get("invoices") or []), 1)
        self.assertEqual(result["invoices"][0]["invoice"], "INV-RES-2")
        self.assertEqual(result["invoices"][0]["invoice_type"], "Reservation Invoice")
        self.assertEqual(len(result.get("payments") or []), 1)
        self.assertEqual(result["payments"][0]["payment_id"], "PAY-RES-2")


class TestHotelSettingsCheckInTime(unittest.TestCase):
    def test_default_check_in_datetime_moves_noon_to_configured_check_in_time(self):
        settings = types.SimpleNamespace(
            default_check_in_time="13:00:00",
            default_check_out_time="12:00:00",
        )

        with patch.object(hotel_settings_api, "_get_hotel_settings", return_value=settings):
            result = hotel_settings_api.get_default_check_in_datetime("2026-06-08 12:00:00")

        self.assertEqual(result, datetime(2026, 6, 8, 13, 0, 0))

    def test_default_check_in_datetime_keeps_late_arrival_time(self):
        settings = types.SimpleNamespace(
            default_check_in_time="13:00:00",
            default_check_out_time="12:00:00",
        )

        with patch.object(hotel_settings_api, "_get_hotel_settings", return_value=settings):
            result = hotel_settings_api.get_default_check_in_datetime("2026-06-08 16:30:00")

        self.assertEqual(result, datetime(2026, 6, 8, 16, 30, 0))


class TestLateCheckoutSkipPermission(unittest.TestCase):
    def test_late_checkout_skip_requires_front_desk_manager(self):
        with (
            patch.object(checkin_api, "_get_late_checkout_charge_preview", return_value={"amount": 1500}),
            patch.object(checkin_api.frappe, "session", types.SimpleNamespace(user="agent.com"), create=True),
            patch.object(checkin_api.frappe, "get_roles", return_value=["Front Desk Agent"], create=True),
        ):
            with self.assertRaisesRegex(RuntimeError, "Only Front Desk Manager"):
                checkin_api._enforce_late_checkout_skip_permission("CHK-LATE-DUE")

    def test_late_checkout_skip_allows_front_desk_manager(self):
        with (
            patch.object(checkin_api, "_get_late_checkout_charge_preview", return_value={"amount": 1500}),
            patch.object(checkin_api.frappe, "session", types.SimpleNamespace(user="manager.com"), create=True),
            patch.object(checkin_api.frappe, "get_roles", return_value=["Front Desk Manager"], create=True),
        ):
            checkin_api._enforce_late_checkout_skip_permission("CHK-LATE-DUE")


class TestLateCheckoutApproval(unittest.TestCase):
    def test_approved_late_checkout_does_not_return_charge(self):
        with patch.object(
            hotel_settings_api.frappe.db,
            "get_value",
            return_value=1,
        ):
            result = hotel_settings_api.check_late_checkout("CHK-LATE-APPROVED")

        self.assertEqual(result, {"late": False, "approved": True})


if __name__ == "__main__":
    unittest.main()
