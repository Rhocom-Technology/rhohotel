import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _whitelist(*args, **kwargs):
        def _decorator(fn):
            return fn

        return _decorator

    frappe_stub._ = lambda text: text
    frappe_stub.throw = lambda message, *args, **kwargs: (_ for _ in ()).throw(RuntimeError(message))
    frappe_stub.whitelist = _whitelist
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub.get_all = lambda *args, **kwargs: []
    frappe_stub.db = types.SimpleNamespace(
        exists=lambda *args, **kwargs: False,
        get_value=lambda *args, **kwargs: None,
        sql=lambda *args, **kwargs: [],
        get_table_columns=lambda *args, **kwargs: [],
    )
    frappe_stub.DoesNotExistError = RuntimeError

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.cstr = lambda value: "" if value is None else str(value)
    utils_stub.flt = lambda value: float(value or 0)
    utils_stub.nowdate = lambda: "2026-06-15"

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


from rhohotel.rhocom_hotel.api import guest as guest_api


class FakeGuestDoc(types.SimpleNamespace):
    pass


class TestGuestApi(unittest.TestCase):
    def _build_guest_doc(self, guest_name="Adisa Modakeke"):
        return FakeGuestDoc(
            name="GST-0001",
            hotel_guest_name=guest_name,
            guest_type="Individual",
            title="Mr",
            gender="Male",
            phone_number="08000000000",
            email="guest@example.com",
            nationality="Nigerian",
            date_of_birth=None,
            address="Lagos",
            id_type="NIN",
            id_number="12345",
            contact_number="08000000000",
            contact_person_name="",
            preference="",
            loyalty_tier="Gold",
            notes="",
            passport_photo="",
            id_document_scan="/files/id.png",
        )

    def test_get_guest_lifetime_spend_uses_settled_invoice_value(self):
        stays = [
            {
                "name": "CHK-0001",
                "room_number": "101",
                "room_type": "Deluxe",
                "check_in_datetime": datetime(2026, 6, 1, 12, 0, 0),
                "expected_check_out_datetime": datetime(2026, 6, 3, 12, 0, 0),
                "actual_check_out_datetime": datetime(2026, 6, 3, 11, 40, 0),
                "status": "Checked Out",
                "total_charges": 1500,
                "total_outstanding_amount": 0,
                "number_of_nights": 2,
                "reservation_source": "Walk-in",
            }
        ]

        with (
            patch.object(guest_api.frappe.db, "exists", return_value=True),
            patch.object(guest_api.frappe, "get_doc", return_value=self._build_guest_doc()),
            patch.object(guest_api.frappe.db, "get_value", return_value=None),
            patch.object(guest_api.frappe, "get_all", return_value=stays),
            patch.object(guest_api, "_has_column", side_effect=lambda doctype, col: doctype == "Sales Invoice"),
            patch.object(
                guest_api.frappe.db,
                "sql",
                return_value=[{"checkin": "CHK-0001", "amount": 1500, "outstanding": 0}],
            ),
        ):
            result = guest_api.get_guest("GST-0001")

        self.assertEqual(result["lifetime_spend"], 1500)

    def test_get_guest_lifetime_spend_falls_back_to_checkin_totals(self):
        stays = [
            {
                "name": "CHK-OLD-1",
                "room_number": "103",
                "room_type": "Standard",
                "check_in_datetime": datetime(2026, 5, 1, 12, 0, 0),
                "expected_check_out_datetime": datetime(2026, 5, 2, 12, 0, 0),
                "actual_check_out_datetime": datetime(2026, 5, 2, 11, 50, 0),
                "status": "Checked Out",
                "total_charges": 1200,
                "total_outstanding_amount": 200,
                "number_of_nights": 1,
                "reservation_source": "Walk-in",
            }
        ]

        with (
            patch.object(guest_api.frappe.db, "exists", return_value=True),
            patch.object(guest_api.frappe, "get_doc", return_value=self._build_guest_doc("Legacy Guest")),
            patch.object(guest_api.frappe.db, "get_value", return_value=None),
            patch.object(guest_api.frappe, "get_all", return_value=stays),
            patch.object(guest_api, "_has_column", return_value=False),
        ):
            result = guest_api.get_guest("GST-LEGACY")

        self.assertEqual(result["lifetime_spend"], 1000)


    def test_get_guest_lifetime_spend_counts_submitted_checkin_payments(self):
        stays = [
            {
                "name": "PMS-CHK-2026-0105",
                "room_number": "105",
                "room_type": "Deluxe",
                "check_in_datetime": datetime(2026, 6, 10, 12, 0, 0),
                "expected_check_out_datetime": datetime(2026, 6, 12, 12, 0, 0),
                "actual_check_out_datetime": None,
                "status": "Checked In",
                "total_charges": 0,
                "total_outstanding_amount": 0,
                "number_of_nights": 2,
                "reservation_source": "Walk-in",
            }
        ]

        with (
            patch.object(guest_api.frappe.db, "exists", return_value=True),
            patch.object(guest_api.frappe, "get_doc", return_value=self._build_guest_doc()),
            patch.object(guest_api.frappe.db, "get_value", return_value=None),
            patch.object(guest_api.frappe, "get_all", return_value=stays),
            patch.object(guest_api, "_has_column", side_effect=lambda doctype, col: doctype == "Payment Entry"),
            patch.object(
                guest_api.frappe.db,
                "sql",
                return_value=[{"checkin": "PMS-CHK-2026-0105", "paid_amount": 147000}],
            ),
        ):
            result = guest_api.get_guest("GST-0001")

        self.assertEqual(result["lifetime_spend"], 147000)


if __name__ == "__main__":
    unittest.main()
