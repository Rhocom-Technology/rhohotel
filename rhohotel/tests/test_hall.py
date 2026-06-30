"""
Tests for rhohotel.rhocom_hotel.api.hall
"""
import sys
import types
import unittest
from unittest.mock import patch, MagicMock

if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")
    frappe_stub._ = lambda t: t
    frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
    frappe_stub.throw = lambda m, *a, **k: (_ for _ in ()).throw(RuntimeError(m))
    frappe_stub.log_error = lambda *a, **k: None
    frappe_stub.get_doc = lambda *a, **k: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    frappe_stub.new_doc = lambda *a, **k: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    frappe_stub.session = types.SimpleNamespace(user="Administrator")
    frappe_stub.db = types.SimpleNamespace(
        sql=lambda *a, **k: [],
        count=lambda *a, **k: 0,
        get_value=lambda *a, **k: None,
        get_all=lambda *a, **k: [],
        exists=lambda *a, **k: False,
        has_column=lambda *a, **k: True,
        commit=lambda: None,
    )
    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.nowdate = lambda: "2026-05-01"
    utils_stub.flt = lambda v, p=2: float(v or 0)
    utils_stub.now_datetime = lambda: __import__("datetime").datetime(2026, 5, 1, 12, 0)
    utils_stub.get_first_day = lambda d: "2026-05-01"
    utils_stub.get_last_day = lambda d: "2026-05-31"
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import hall

# When running under bench run-tests, the real frappe is loaded so frappe.throw
# raises frappe.exceptions.ValidationError instead of RuntimeError.
# We catch the common base Exception to handle both cases.
_THROW_EXC = Exception


class TestCreateHallAmenityItem(unittest.TestCase):
    def test_throws_when_no_item_name(self):
        with self.assertRaises(_THROW_EXC):
            hall.create_hall_amenity_item("")

    def test_throws_when_item_group_missing(self):
        with (
            patch.object(hall.frappe.db, "exists", side_effect=lambda doctype, name=None: False),
            patch.object(hall.frappe, "throw", side_effect=RuntimeError("no item group")),
        ):
            with self.assertRaises(_THROW_EXC):
                hall.create_hall_amenity_item("New Lamp")

    def test_throws_when_item_already_exists(self):
        def fake_exists(doctype, name=None):
            if doctype == "Item Group":
                return True
            if doctype == "Item":
                return True
            return False

        with (
            patch.object(hall.frappe.db, "exists", side_effect=fake_exists),
            patch.object(hall.frappe, "throw", side_effect=RuntimeError("already exists")),
        ):
            with self.assertRaises(_THROW_EXC):
                hall.create_hall_amenity_item("Existing Item")

    def test_creates_new_item(self):
        doc = MagicMock()
        doc.item_code = "New Lamp"
        doc.item_name = "New Lamp"

        def fake_exists(doctype, name=None):
            if doctype == "Item Group":
                return True
            return False

        with (
            patch.object(hall.frappe.db, "exists", side_effect=fake_exists),
            patch.object(hall.frappe, "new_doc", return_value=doc),
        ):
            result = hall.create_hall_amenity_item("New Lamp")

        self.assertEqual(result["item_code"], "New Lamp")
        self.assertFalse(result["exists"])


class TestUpdateHallAvailability(unittest.TestCase):
    def test_throws_when_no_hall(self):
        with self.assertRaises(_THROW_EXC):
            hall.update_hall_availability("", "Available")

    def test_throws_when_invalid_status(self):
        with self.assertRaises(_THROW_EXC):
            hall.update_hall_availability("HALL-001", "Broken")

    def test_sets_available(self):
        doc = MagicMock()
        doc.name = "HALL-001"
        doc.availability_status = "Available"
        doc.unavailable_reason = ""

        with patch.object(hall.frappe, "get_doc", return_value=doc):
            result = hall.update_hall_availability("HALL-001", "Available")

        self.assertEqual(doc.availability_status, "Available")
        self.assertEqual(doc.unavailable_reason, "")
        self.assertEqual(result["name"], "HALL-001")

    def test_sets_unavailable_with_reason(self):
        doc = MagicMock()
        doc.name = "HALL-001"
        doc.availability_status = "Unavailable"
        doc.unavailable_reason = "Maintenance"

        with patch.object(hall.frappe, "get_doc", return_value=doc):
            result = hall.update_hall_availability("HALL-001", "Unavailable", "Maintenance")

        self.assertEqual(doc.availability_status, "Unavailable")
        self.assertEqual(doc.unavailable_reason, "Maintenance")


class TestCreateHallType(unittest.TestCase):
    def test_throws_when_no_name(self):
        with self.assertRaises(_THROW_EXC):
            hall.create_hall_type("")

    def test_returns_existing(self):
        with patch.object(hall.frappe.db, "exists", return_value=True):
            result = hall.create_hall_type("Ballroom")
        self.assertTrue(result["exists"])

    def test_creates_new(self):
        doc = MagicMock()
        doc.name = "Ballroom"
        doc.hall_type_name = "Ballroom"

        with (
            patch.object(hall.frappe.db, "exists", return_value=False),
            patch.object(hall.frappe, "new_doc", return_value=doc),
        ):
            result = hall.create_hall_type("Ballroom")

        self.assertFalse(result["exists"])
        self.assertEqual(result["name"], "Ballroom")


class TestCreateHall(unittest.TestCase):
    def test_creates_hall_from_dict(self):
        doc = MagicMock()
        doc.name = "HALL-001"

        with patch.object(hall.frappe, "new_doc", return_value=doc):
            result = hall.create_hall({
                "hall_name": "Grand Ballroom",
                "hall_type": "Ballroom",
                "capacity": 200,
                "rate": 50000,
            })

        self.assertEqual(doc.hall_name, "Grand Ballroom")
        self.assertEqual(doc.capacity, 200)
        self.assertEqual(result["name"], "HALL-001")

    def test_creates_hall_from_json_string(self):
        import json
        doc = MagicMock()
        doc.name = "HALL-002"

        with patch.object(hall.frappe, "new_doc", return_value=doc):
            result = hall.create_hall(json.dumps({
                "hall_name": "Conference Room",
                "capacity": 50,
                "rate": 10000,
            }))

        self.assertEqual(doc.hall_name, "Conference Room")
        self.assertEqual(result["name"], "HALL-002")


if __name__ == "__main__":
    unittest.main()