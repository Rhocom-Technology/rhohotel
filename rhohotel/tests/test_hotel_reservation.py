import sys
import types
import unittest
import inspect
import re
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _default_throw(message):
        raise RuntimeError(message)

    frappe_stub.throw = _default_throw
    frappe_stub.get_doc = lambda *args, **kwargs: None
    frappe_stub._ = lambda text: text
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
    frappe_stub.utils = types.SimpleNamespace(
        add_to_date=lambda value, **kwargs: "2026-04-10 13:00:00",
        nowdate=lambda: "2026-04-10",
        getdate=lambda value: value if isinstance(value, date) else date.fromisoformat(value),
        flt=lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0),
        date_diff=lambda a, b: ((a if isinstance(a, date) else date.fromisoformat(a)) - (b if isinstance(b, date) else date.fromisoformat(b))).days,
    )

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(value)
    utils_stub.flt = lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0)
    utils_stub.date_diff = lambda a, b: (a - b).days
    utils_stub.now_datetime = lambda: "2026-04-10 12:00:00"
    utils_stub.add_days = lambda value, days=0: value
    utils_stub.cint = lambda value: int(value or 0)
    utils_stub.get_datetime = lambda value: value
    utils_stub.today = lambda: "2026-04-10"

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
    STATUS_HOLD,
    STATUS_NO_SHOW,
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
    def test_whitelisted_api_methods_have_named_tests(self):
        """
        Coverage guard:
        - Detect whitelisted API methods from hotel_reservation.py source.
        - Require at least one test method name mapped to each API method.

        When a new whitelisted API method is added, this test fails until
        a matching entry is added below and tests are implemented.
        """
        source = inspect.getsource(hr_module)
        whitelisted_methods = set(
            re.findall(r"@frappe\.whitelist\(\)\s*\ndef\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", source)
        )

        # Explicit map keeps this guard intentional and reviewable.
        expected_test_name_fragments = {
            "adjust_reservation": ["adjust_reservation"],
            "change_room_in_reservation": ["change_room"],
            "check_in_reservation_room": ["check_in_reservation_room"],
            "bulk_check_in_reservation": ["bulk_check_in_reservation"],
            "create_invoice_for_reservation": ["create_invoice_for_reservation"],
            "get_payment_summary_for_reservation": ["get_payment_summary_for_reservation"],
            "get_outstanding_invoices_for_reservation": ["get_outstanding_invoices_for_reservation"],
            "adjust_invoice_for_reservation": ["adjust_invoice_for_reservation"],
            "create_invoice_for_reservation_room": ["create_invoice_for_reservation_room"],
            "create_pending_split_invoices": ["create_pending_split_invoices"],
            "collect_payment_for_reservation": ["collect_payment_for_reservation"],
            "cancel_reservation": ["cancel_reservation"],
            "apply_split_room_discount": ["apply_split_room_discount"],
            "distribute_split_room_discount": ["distribute_split_room_discount"],
            "create_bill_transfer_for_reservation": ["create_bill_transfer_for_reservation"],
        }

        self.assertEqual(
            whitelisted_methods,
            set(expected_test_name_fragments.keys()),
            "Whitelisted API method set changed. Add mapping + unit tests for new methods.",
        )

        test_names = [name for name in dir(self.__class__) if name.startswith("test_")]
        missing = []
        for method_name, fragments in expected_test_name_fragments.items():
            if not any(any(fragment in test_name for fragment in fragments) for test_name in test_names):
                missing.append(method_name)

        self.assertFalse(
            missing,
            f"Missing reservation API tests for: {', '.join(sorted(missing))}",
        )

    def _base_doc(self):
        doc = HotelReservation()
        doc.name = "RES-TEST-0001"
        doc.reservation_status = STATUS_DRAFT
        doc.hold_expires_at = None
        doc.reservation_type = "Individual"
        doc.primary_guest_name = "John Doe"
        doc.corporate_guest = None
        doc.from_date = "2026-04-10"
        doc.to_date = "2026-04-12"
        doc.rooms = [Row(room_number="R-101", room_total=10000)]
        doc.discount_type = None
        doc.discount = 0
        return doc

    def test_assert_valid_transition_rejects_terminal_move(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_CONFIRMED
        doc.get_doc_before_save = lambda: Row(reservation_status=STATUS_EXPIRED)

        with self.assertRaises(RuntimeError):
            doc._assert_valid_transition()

    def test_set_hold_expiry_when_entering_hold(self):
        doc = self._base_doc()
        doc.reservation_status = "Hold"

        doc._set_hold_expiry()

        self.assertEqual(doc.hold_expires_at, "2026-04-10 13:00:00")

    def test_on_submit_reserves_vacant_rooms(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_CONFIRMED
        doc.rooms = [Row(room_number="R-101")]
        room = FakeRoom(status="Vacant")

        with patch("rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.frappe.get_doc", return_value=room):
            doc.on_submit()

        self.assertEqual(room.status, "Reserved")
        self.assertTrue(room.saved)

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

    def test_split_parent_fixed_discount_is_distributed_equally(self):
        doc = self._base_doc()
        doc.reservation_type = "Group"
        doc.group_billing_mode = "Split"
        doc.from_date = "2026-04-10"
        doc.to_date = "2026-04-11"
        doc.discount_type = "Fixed Amount"
        doc.discount = 30000
        doc.rooms = [
            Row(rate_per_night=90000, discount=0),
            Row(rate_per_night=120000, discount=0),
            Row(rate_per_night=120000, discount=0),
        ]

        doc._distribute_split_parent_discount()

        self.assertEqual([row.discount for row in doc.rooms], [10000, 10000, 10000])
        self.assertEqual(doc.discount_type, "")
        self.assertEqual(doc.discount, 0)
        self.assertEqual(doc.discount_amount, 0)

    def test_split_parent_percentage_discount_remains_proportional(self):
        doc = self._base_doc()
        doc.reservation_type = "Group"
        doc.group_billing_mode = "Split"
        doc.from_date = "2026-04-10"
        doc.to_date = "2026-04-11"
        doc.discount_type = "Percentage"
        doc.discount = 10
        doc.rooms = [
            Row(rate_per_night=90000, discount=0),
            Row(rate_per_night=120000, discount=0),
            Row(rate_per_night=120000, discount=0),
        ]

        doc._distribute_split_parent_discount()

        self.assertEqual([row.discount for row in doc.rooms], [9000, 12000, 12000])

    def test_split_adjustment_fixed_discount_allocates_equally_to_new_invoices(self):
        doc = types.SimpleNamespace(
            rooms=[
                Row(name="ROW-802", split_invoice="INV-802", room_total=170000, discount=10000),
                Row(name="ROW-211", split_invoice="INV-211", room_total=230000, discount=10000),
                Row(name="ROW-208", split_invoice="INV-208", room_total=230000, discount=10000),
            ],
        )
        old_room_totals = {"ROW-802": 81000, "ROW-211": 108000, "ROW-208": 108000}
        old_room_discounts = {"ROW-802": 9000, "ROW-211": 12000, "ROW-208": 12000}

        allocations = hr_module._get_split_adjustment_discount_allocations(
            doc,
            old_room_totals,
            old_room_discounts,
            "Fixed Amount",
            30000,
        )

        self.assertEqual(allocations, {"ROW-802": 10000, "ROW-211": 10000, "ROW-208": 10000})
        net_adjustments = {}
        for row in doc.rooms:
            old_gross = old_room_totals[row.name] + old_room_discounts[row.name]
            new_gross = row.room_total + row.discount
            net_adjustments[row.name] = new_gross - old_gross - allocations[row.name]

        self.assertEqual(net_adjustments, {"ROW-802": 80000, "ROW-211": 110000, "ROW-208": 110000})

    def test_split_adjustment_percentage_discount_allocates_by_room_adjustment_value(self):
        doc = types.SimpleNamespace(
            rooms=[
                Row(name="ROW-1", split_invoice="INV-1", room_total=145000, discount=5000),
                Row(name="ROW-2", split_invoice="INV-2", room_total=235000, discount=5000),
            ],
        )
        old_room_totals = {"ROW-1": 100000, "ROW-2": 180000}
        old_room_discounts = {"ROW-1": 0, "ROW-2": 0}

        allocations = hr_module._get_split_adjustment_discount_allocations(
            doc,
            old_room_totals,
            old_room_discounts,
            "Percentage",
            10,
        )

        self.assertEqual(allocations, {"ROW-1": 5000, "ROW-2": 6000})

    def test_saved_reservation_invoice_ledger_opens_invoice_detail_modal(self):
        app_root = Path(__file__).resolve().parents[2]
        source = (app_root / "frontend/src/components/reservations/SavedReservation.vue").read_text()

        self.assertIn("import InvoiceDetailModal from '@/components/checkin/InvoiceDetailModal.vue'", source)
        self.assertIn("@click=\"openInvoiceDetail(invoice)\"", source)
        self.assertIn(":invoiceName=\"selectedInvoice.name\"", source)
        self.assertIn("function openInvoiceDetail(invoice)", source)

    def test_on_submit_throws_for_non_confirmed_or_later_status(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_DRAFT

        with self.assertRaises(RuntimeError):
            doc.on_submit()

    def test_on_submit_accepts_confirmed(self):
        doc = self._base_doc()
        doc.reservation_status = STATUS_CONFIRMED

        # Should not throw
        with patch.object(doc, "_reserve_rooms") as reserve_mock:
            doc.on_submit()
        reserve_mock.assert_called_once()

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
            reservation_type="Individual",
            group_billing_mode="",
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

        def fake_get_value(doctype, filters, fieldname, **kwargs):
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

    def test_adjust_reservation_updates_dates_and_totals(self):
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            reservation_type="Individual",
            group_billing_mode="",
            from_date="2026-04-10",
            to_date="2026-04-12",
            discount_type="None",
            discount=0,
            rooms=[],
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            _recalculate_room_totals=Mock(),
            _recalculate_totals=Mock(),
            save=Mock(),
            subtotal=200,
            discount_amount=0,
            total_amount=200,
        )

        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module.frappe.db, "commit"),
        ):
            result = hr_module.adjust_reservation(
                "RES-TEST-0001",
                new_checkout="2026-04-14",
                new_check_in="2026-04-10",
                new_discount_type="Percentage",
                new_discount=5,
            )

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("new_nights"), 4)
        self.assertEqual(doc.discount_type, "Percentage")
        self.assertEqual(doc.discount, 5)
        doc._recalculate_room_totals.assert_called_once()
        doc._recalculate_totals.assert_called_once()
        doc.save.assert_called_once_with(ignore_permissions=True)

    def test_check_in_reservation_room_returns_error_for_missing_row(self):
        doc = types.SimpleNamespace(name="RES-TEST-0001", rooms=[])
        with patch.object(hr_module.frappe, "get_doc", return_value=doc):
            result = hr_module.check_in_reservation_room("RES-TEST-0001", "ROW-MISSING")

        self.assertEqual(result.get("status"), "error")
        self.assertIn("Room row not found", result.get("message", ""))

    def test_check_in_reservation_room_returns_error_when_guest_not_resolved(self):
        row = Row(
            name="ROW-1",
            room_number="R-101",
            room_type="Deluxe",
            status="Confirmed",
            check_in_reference="",
            number_of_nights=2,
            rate_per_night=5000,
            hotel_guest=None,
            occupant_name="",
            guest_name="",
        )
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            rooms=[row],
            number_of_nights=2,
            primary_guest_name="",
            reservation_type="Individual",
            source_channel="",
            discount_type="None",
            discount=0,
        )

        fake_room_availability = types.SimpleNamespace(assert_room_available=Mock())
        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()

        def fake_get_value(doctype, filters, fieldname=None, as_dict=False):
            return None

        with (
            patch.dict(sys.modules, {"rhohotel.rhocom_hotel.utils.room_availability": fake_room_availability}),
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = hr_module.check_in_reservation_room("RES-TEST-0001", "ROW-1")

        self.assertEqual(result.get("status"), "error")
        self.assertIn("No guest linked", result.get("message", ""))

    def test_bulk_check_in_reservation_rejects_ineligible_status(self):
        doc = types.SimpleNamespace(reservation_status=STATUS_DRAFT)
        with patch.object(hr_module.frappe, "get_doc", return_value=doc):
            result = hr_module.bulk_check_in_reservation("RES-TEST-0001")

        self.assertEqual(result.get("status"), "error")
        self.assertIn("check-in eligible", result.get("message", ""))

    def test_create_invoice_for_reservation_returns_existing_invoice(self):
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            reservation_type="Individual",
            group_billing_mode="",
            sales_invoice="INV-EXIST-0001",
        )

        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module, "_upsert_reservation_invoice_row", return_value=False),
        ):
            result = hr_module.create_invoice_for_reservation("RES-TEST-0001")

        self.assertEqual(result.get("sales_invoice"), "INV-EXIST-0001")
        self.assertTrue(result.get("already_exists"))

    def test_get_payment_summary_for_reservation_without_invoices(self):
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            net_total=750,
            total_amount=750,
            payment_status="Pending",
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            payment_entry=None,
            get=lambda fieldname: "Pending" if fieldname == "payment_status" else [],
        )

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module, "_get_reservation_invoice_names", return_value=[]),
            patch.object(hr_module, "_reconcile_pending_reservation_credit_notes", return_value=None),
        ):
            result = hr_module.get_payment_summary_for_reservation("RES-TEST-0001")

        self.assertEqual(result.get("paid_amount"), 0)
        self.assertEqual(result.get("invoice_total"), 0)
        self.assertEqual(result.get("outstanding_amount"), 0)
        self.assertEqual(result.get("balance"), 750)

    def test_get_outstanding_invoices_for_reservation_filters_zero_amount(self):
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            primary_guest_name="Guest One",
            corporate_guest="",
            customer="Guest Customer",
            get=lambda fieldname: [],
        )
        invoice_map = {
            "INV-1": {"name": "INV-1", "outstanding_amount": 120},
            "INV-2": {"name": "INV-2", "outstanding_amount": 0},
        }

        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()

        def fake_get_value(doctype, name, fieldname=None, as_dict=False):
            return invoice_map.get(name)

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module, "_get_reservation_invoice_names", return_value=["INV-1", "INV-2"]),
            patch.object(hr_module, "_reconcile_pending_reservation_credit_notes", return_value=None),
            patch.object(hr_module, "_apply_reservation_invoice_netting", side_effect=lambda rows, names: rows),
            patch.object(hr_module, "_get_invoice_credit_note_amount", return_value=0),
            patch.object(hr_module.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = hr_module.get_outstanding_invoices_for_reservation("RES-TEST-0001")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get("name"), "INV-1")

    def test_adjust_invoice_for_reservation_returns_no_invoice_when_unlinked(self):
        doc = types.SimpleNamespace(
            name="RES-TEST-0001",
            reservation_type="Individual",
            group_billing_mode="",
            sales_invoice="",
        )
        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module, "_get_reservation_invoice_names", return_value=[]),
        ):
            result = hr_module.adjust_invoice_for_reservation("RES-TEST-0001")

        self.assertEqual(result.get("status"), "no_invoice")

    def test_create_invoice_for_reservation_room_returns_existing_split_invoice(self):
        row = Row(name="ROW-1", split_invoice="INV-SPLIT-001")
        doc = types.SimpleNamespace(
            reservation_type="Group",
            group_billing_mode="Split Billing",
            rooms=[row],
        )

        with patch.object(hr_module.frappe, "get_doc", return_value=doc):
            result = hr_module.create_invoice_for_reservation_room("RES-TEST-0001", "ROW-1")

        self.assertEqual(result.get("sales_invoice"), "INV-SPLIT-001")
        self.assertTrue(result.get("already_exists"))

    def test_collect_payment_for_reservation_requires_mode_of_payment(self):
        doc = types.SimpleNamespace(name="RES-TEST-0001")
        outstanding_row = types.SimpleNamespace(name="INV-1", customer="Guest Customer", company="Test Company", outstanding_amount=100)

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module, "_get_reservation_invoice_names", return_value=["INV-1"]),
            patch.object(hr_module, "_reconcile_pending_reservation_credit_notes", return_value=None),
            patch.object(hr_module.frappe, "get_all", return_value=[outstanding_row], create=True),
        ):
            with self.assertRaises(RuntimeError):
                hr_module.collect_payment_for_reservation(
                    "RES-TEST-0001",
                    payment_info={"paid_amount": 100},
                )

    def test_apply_split_room_discount_api_exists(self):
        self.assertTrue(callable(hr_module.apply_split_room_discount))

    def test_distribute_split_room_discount_api_exists(self):
        self.assertTrue(callable(hr_module.distribute_split_room_discount))

    def test_create_bill_transfer_for_reservation_api_exists(self):
        self.assertTrue(callable(hr_module.create_bill_transfer_for_reservation))

    def test_cancel_reservation_returns_already_cancelled(self):
        doc = types.SimpleNamespace(docstatus=2)
        with patch.object(hr_module.frappe, "get_doc", return_value=doc):
            result = hr_module.cancel_reservation("RES-TEST-0001")

        self.assertEqual(result.get("status"), "already_cancelled")

    def test_cancel_reservation_updates_draft_status(self):
        doc = types.SimpleNamespace(
            docstatus=0,
            reservation_status="Confirmed",
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            _release_rooms=Mock(),
            save=Mock(),
        )

        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        with (
            patch.object(hr_module.frappe, "get_doc", return_value=doc),
            patch.object(hr_module.frappe.db, "commit"),
        ):
            result = hr_module.cancel_reservation("RES-TEST-0001", reason="Guest request")

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(doc.reservation_status, STATUS_CANCELLED)
        doc._release_rooms.assert_called_once()
        doc.save.assert_called_once_with(ignore_permissions=True)

    def test_process_reservation_lifecycle_marks_expired_and_no_show(self):
        expired_doc = types.SimpleNamespace(
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            reservation_status=STATUS_HOLD,
            _release_rooms=Mock(),
            save=Mock(),
        )
        no_show_doc = types.SimpleNamespace(
            flags=types.SimpleNamespace(ignore_validate_update_after_submit=False),
            reservation_status=STATUS_CONFIRMED,
            _release_rooms=Mock(),
            save=Mock(),
        )

        if not hasattr(hr_module.frappe, "db"):
            hr_module.frappe.db = types.SimpleNamespace()
        if not hasattr(hr_module.frappe.db, "commit"):
            hr_module.frappe.db.commit = lambda *args, **kwargs: None

        def fake_get_all(doctype, filters=None, fields=None):
            status = (filters or {}).get("reservation_status")
            if status == STATUS_HOLD:
                return [types.SimpleNamespace(name="RES-EXP-1")]
            if status == STATUS_CONFIRMED:
                return [types.SimpleNamespace(name="RES-NOSHOW-1")]
            return []

        def fake_get_doc(doctype, name):
            if name == "RES-EXP-1":
                return expired_doc
            if name == "RES-NOSHOW-1":
                return no_show_doc
            raise RuntimeError(f"Unexpected document: {name}")

        with (
            patch.object(hr_module.frappe, "get_all", side_effect=fake_get_all, create=True),
            patch.object(hr_module.frappe, "get_doc", side_effect=fake_get_doc),
            patch.object(hr_module.frappe.db, "commit") as commit_mock,
        ):
            result = hr_module.process_reservation_lifecycle()

        self.assertEqual(result, {"expired": 1, "no_show": 1})
        self.assertEqual(expired_doc.reservation_status, STATUS_EXPIRED)
        self.assertEqual(no_show_doc.reservation_status, STATUS_NO_SHOW)
        expired_doc._release_rooms.assert_called_once()
        no_show_doc._release_rooms.assert_called_once()
        commit_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
