import sys
import types
import unittest
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
    utils_stub.get_datetime = lambda value: value

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


from rhohotel.rhocom_hotel.api import checkin as checkin_api


class FakeCheckinDoc(types.SimpleNamespace):
    def as_dict(self):
        return {
            "name": self.name,
            "reservation": self.reservation,
            "reservation_source": self.reservation_source,
        }


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

        with (
            patch.object(checkin_api.frappe.db, "exists", side_effect=fake_exists),
            patch.object(checkin_api.frappe, "get_doc", return_value=doc),
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

        with (
            patch.object(checkin_api.frappe.db, "exists", side_effect=fake_exists),
            patch.object(checkin_api.frappe, "get_doc", return_value=doc),
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


if __name__ == "__main__":
    unittest.main()
