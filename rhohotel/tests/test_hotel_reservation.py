import sys
import types
import unittest
from datetime import date
from unittest.mock import Mock, patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _default_throw(message):
        raise RuntimeError(message)

    frappe_stub.throw = _default_throw
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub._ = lambda text: text

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(value)
    utils_stub.flt = lambda value: float(value or 0)
    utils_stub.date_diff = lambda a, b: (a - b).days
    utils_stub.now_datetime = lambda: None

    model_stub = types.ModuleType("frappe.model")
    model_document_stub = types.ModuleType("frappe.model.document")

    class _Document:
        pass

    model_document_stub.Document = _Document

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub
    sys.modules["frappe.model"] = model_stub
    sys.modules["frappe.model.document"] = model_document_stub


from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import (
    HotelReservation,
    STATUS_CANCELLED,
    STATUS_CHECKED_IN,
    STATUS_CONFIRMED,
    STATUS_DRAFT,
    STATUS_EXPIRED,
)
from rhohotel.rhocom_hotel.doctype.hotel_reservation import hotel_reservation as hr_module


class Row(types.SimpleNamespace):
    pass


class FakeRoom:
    def __init__(self, status):
        self.status = status
        self.saved = False

    def save(self, ignore_permissions=False):
        self.saved = ignore_permissions


class TestHotelReservation(unittest.TestCase):
    def _base_doc(self):
        doc = HotelReservation()
        doc.name = "RES-TEST-0001"
        doc.reservation_status = STATUS_DRAFT
        doc.reservation_type = "Individual"
        doc.primary_guest_name = "John Doe"
        doc.corporate_guest = None
        doc.from_date = "2026-04-10"
        doc.to_date = "2026-04-12"
        doc.rooms = [Row(room_number="R-101", room_total=10000)]
        doc.discount_type = None
        doc.discount = 0
        return doc

    def test_validate_dates_sets_number_of_nights(self):
        doc = self._base_doc()
        doc._validate_dates()
        self.assertEqual(doc.number_of_nights, 2)

    def test_validate_dates_throws_when_checkout_not_after_checkin(self):
        doc = self._base_doc()
        doc.to_date = "2026-04-10"
        with self.assertRaises(RuntimeError):
            doc._validate_dates()

    def test_validate_rooms_present_throws_for_empty_rows(self):
        doc = self._base_doc()
        doc.rooms = []
        with self.assertRaises(RuntimeError):
            doc._validate_rooms_present()

    def test_validate_corporate_guest_rules(self):
        doc = self._base_doc()

        doc.reservation_type = "Corporate"
        doc.corporate_guest = None
        with self.assertRaises(RuntimeError):
            doc._validate_corporate_guest()

        doc.reservation_type = "Individual"
        doc.primary_guest_name = ""
        with self.assertRaises(RuntimeError):
            doc._validate_corporate_guest()

    def test_validate_room_availability_calls_assert_for_each_room(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_CONFIRMED
        doc.rooms = [Row(room_number="R-101"), Row(room_number="R-102")]

        fake_room_availability = types.SimpleNamespace(assert_room_available=Mock())

        with patch.dict(
            sys.modules,
            {"rhohotel.rhocom_hotel.utils.room_availability": fake_room_availability},
        ):
            doc._validate_room_availability()

        self.assertEqual(fake_room_availability.assert_room_available.call_count, 2)
        first_call = fake_room_availability.assert_room_available.call_args_list[0]
        self.assertEqual(first_call.args[0], "R-101")
        self.assertEqual(first_call.kwargs["exclude_reservation"], doc.name)
        self.assertEqual(first_call.kwargs["exclude_canonical"], doc.name)

    def test_validate_room_availability_skips_terminal_status(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_EXPIRED

        fake_room_availability = types.SimpleNamespace(assert_room_available=Mock())

        with patch.dict(
            sys.modules,
            {"rhohotel.rhocom_hotel.utils.room_availability": fake_room_availability},
        ):
            doc._validate_room_availability()

        fake_room_availability.assert_room_available.assert_not_called()

    def test_recalculate_totals_percentage_discount(self):
        doc = self._base_doc()
        doc.rooms = [Row(room_total=100), Row(room_total=300)]
        doc.discount_type = "Percentage"
        doc.discount = 10

        doc._recalculate_totals()

        self.assertEqual(doc.subtotal, 400)
        self.assertEqual(doc.discount_amount, 40)
        self.assertEqual(doc.total_amount, 360)
        self.assertEqual(doc.net_total, 360)

    def test_recalculate_totals_fixed_discount_capped_to_subtotal(self):
        doc = self._base_doc()
        doc.rooms = [Row(room_total=100)]
        doc.discount_type = "Fixed Amount"
        doc.discount = 1000

        doc._recalculate_totals()

        self.assertEqual(doc.subtotal, 100)
        self.assertEqual(doc.discount_amount, 100)
        self.assertEqual(doc.total_amount, 0)

    def test_on_submit_throws_for_non_confirmed_or_later_status(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_DRAFT

        with self.assertRaises(RuntimeError):
            doc.on_submit()

    def test_on_submit_accepts_confirmed(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_CONFIRMED

        # Should not throw
        doc.on_submit()

    def test_on_cancel_sets_status_and_releases_rooms(self):
        doc = self._base_doc()
        with patch.object(doc, "_release_rooms") as release_mock:
            doc.on_cancel()

        self.assertEqual(doc.reservation_status, STATUS_CANCELLED)
        release_mock.assert_called_once()

    def test_release_rooms_only_vacates_reserved_rooms(self):
        doc = self._base_doc()
        doc.rooms = [Row(room_number="R-101"), Row(room_number="R-102")]

        room_reserved = FakeRoom(status="Reserved")
        room_occupied = FakeRoom(status="Occupied")

        def fake_get_doc(doctype, name):
            if name == "R-101":
                return room_reserved
            return room_occupied

        with patch("rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.frappe.get_doc", side_effect=fake_get_doc):
            doc._release_rooms()

        self.assertEqual(room_reserved.status, "Vacant")
        self.assertTrue(room_reserved.saved)
        self.assertEqual(room_occupied.status, "Occupied")
        self.assertFalse(room_occupied.saved)

    def test_change_room_creates_adjustment_when_invoice_exists(self):
        reservation_doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            from_date="2026-04-10",
            number_of_nights=2,
            sales_invoice="INV-0001",
            rooms=[Row(room_number="R-101", room_type="Deluxe", rate_code="", rate_per_night=5000, room_total=10000)],
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            _recalculate_totals=Mock(),
            save=Mock(),
            get=lambda fieldname: [],
        )

        new_room = FakeRoom(status="Vacant")
        new_room.room_type = "Suite"
        old_room = FakeRoom(status="Reserved")

        def fake_get_doc(doctype, name):
            if doctype == "Hotel Reservation":
                return reservation_doc
            if doctype == "Hotel Room" and name == "R-101":
                return old_room
            if doctype == "Hotel Room" and name == "R-202":
                return new_room
            raise RuntimeError(f"Unexpected get_doc call: {doctype} {name}")

        def fake_get_value(doctype, filters, fieldname):
            if doctype == "Sales Invoice":
                return "INV-0001"
            return None

        fake_rho_api = types.SimpleNamespace(get_room_rate=Mock(return_value=8000))
        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "get_value"):
            hr_module.frappe.db.get_value = lambda *args, **kwargs: None
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        with (
            patch.dict(sys.modules, {"rhohotel.api": fake_rho_api}),
            patch.object(hr_module.frappe, "get_doc", side_effect=fake_get_doc),
            patch.object(hr_module.frappe.db, "get_value", side_effect=fake_get_value),
            patch.object(hr_module.frappe.db, "commit"),
            patch.object(hr_module, "adjust_invoice_for_reservation", return_value={"status": "adjustment_created"}) as adjust_mock,
        ):
            result = hr_module.change_room_in_reservation("RES-TEST-0001", "R-101", "R-202")

        adjust_mock.assert_called_once_with("RES-TEST-0001")
        self.assertEqual(result.get("invoice_adjustment", {}).get("status"), "adjustment_created")

    def test_change_room_skips_adjustment_when_no_existing_invoice(self):
        reservation_doc = types.SimpleNamespace(
            name="RES-TEST-0002",
            from_date="2026-04-10",
            number_of_nights=2,
            sales_invoice="",
            rooms=[Row(room_number="R-301", room_type="Deluxe", rate_code="", rate_per_night=5000, room_total=10000)],
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            _recalculate_totals=Mock(),
            save=Mock(),
            get=lambda fieldname: [],
        )

        new_room = FakeRoom(status="Vacant")
        new_room.room_type = "Executive"
        old_room = FakeRoom(status="Reserved")

        def fake_get_doc(doctype, name):
            if doctype == "Hotel Reservation":
                return reservation_doc
            if doctype == "Hotel Room" and name == "R-301":
                return old_room
            if doctype == "Hotel Room" and name == "R-302":
                return new_room
            raise RuntimeError(f"Unexpected get_doc call: {doctype} {name}")

        fake_rho_api = types.SimpleNamespace(get_room_rate=Mock(return_value=4000))
        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        with (
            patch.dict(sys.modules, {"rhohotel.api": fake_rho_api}),
            patch.object(hr_module.frappe, "get_doc", side_effect=fake_get_doc),
            patch.object(hr_module.frappe.db, "commit"),
            patch.object(hr_module, "adjust_invoice_for_reservation") as adjust_mock,
        ):
            result = hr_module.change_room_in_reservation("RES-TEST-0002", "R-301", "R-302")

        adjust_mock.assert_not_called()
        self.assertIsNone(result.get("invoice_adjustment"))

    def test_create_invoice_for_reservation_blocks_group_split_variants(self):
        split_doc = types.SimpleNamespace(
            name="RES-SPLIT-0001",
            reservation_type="Group",
            group_billing_mode="Split Billing",
        )

        with patch.object(hr_module.frappe, "get_doc", return_value=split_doc):
            with self.assertRaises(RuntimeError):
                hr_module.create_invoice_for_reservation("RES-SPLIT-0001")

    def test_create_pending_split_invoices_only_creates_for_uninvoiced_rows(self):
        split_doc = types.SimpleNamespace(
            name="RES-SPLIT-0002",
            reservation_type="Group",
            group_billing_mode="Split",
            rooms=[
                Row(name="ROW-1", room_number="R-101", split_invoice=""),
                Row(name="ROW-2", room_number="R-102", split_invoice="INV-EXIST-1"),
                Row(name="ROW-3", room_number="R-103", split_invoice=""),
            ],
        )

        def fake_create_room_invoice(reservation_name, room_row_name):
            return {"sales_invoice": f"INV-{room_row_name}"}

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=split_doc),
            patch.object(hr_module, "create_invoice_for_reservation_room", side_effect=fake_create_room_invoice) as create_row_mock,
        ):
            result = hr_module.create_pending_split_invoices("RES-SPLIT-0002")

        self.assertEqual(create_row_mock.call_count, 2)
        called_rows = {call.args[1] for call in create_row_mock.call_args_list}
        self.assertEqual(called_rows, {"ROW-1", "ROW-3"})
        self.assertEqual(result.get("created_count"), 2)
        self.assertEqual(result.get("already_invoiced_count"), 1)
        self.assertEqual(result.get("failed_count"), 0)


if __name__ == "__main__":
    unittest.main()
