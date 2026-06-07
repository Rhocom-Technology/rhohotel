import sys
import types
import unittest
from unittest.mock import patch


if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")

    def _default_throw(message):
        raise RuntimeError(message)

    frappe_stub.throw = _default_throw
    frappe_stub._ = lambda text: text
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
    frappe_stub.get_cached_doc = lambda *args, **kwargs: None
    frappe_stub.get_meta = lambda *args, **kwargs: types.SimpleNamespace(has_field=lambda *_: False)
    frappe_stub.new_doc = lambda *args, **kwargs: None
    frappe_stub.db = types.SimpleNamespace(
        exists=lambda *args, **kwargs: False,
        get_value=lambda *args, **kwargs: None,
        set_value=lambda *args, **kwargs: None,
    )
    frappe_stub.get_all = lambda *args, **kwargs: []

    sys.modules["frappe"] = frappe_stub


from rhohotel.rhocom_hotel.utils import billing_routing as br


class TestBillingRouting(unittest.TestCase):
    def test_resolve_payer_group_central_accepts_customer_name_hint(self):
        reservation = types.SimpleNamespace(
            reservation_type="Group",
            group_billing_mode="Central",
            group_master_customer="Acme Holdings",
            internal_cost_center=None,
            customer=None,
            ota_channel=None,
            ota_collection_model=None,
            ota_virtual_card_ref=None,
            corporate_guest=None,
        )

        def fake_exists(doctype, name):
            if doctype == "Customer" and name == "Acme Holdings":
                return False
            return False

        def fake_get_value(doctype, filters, fieldname):
            if doctype == "Customer" and isinstance(filters, dict):
                if filters.get("customer_name") == "Acme Holdings" and fieldname == "name":
                    return "CUST-ACME"
            return None

        with (
            patch.object(br, "_get_reservation", return_value=reservation),
            patch.object(br, "_matching_rules", return_value=[]),
            patch.object(br.frappe.db, "exists", side_effect=fake_exists),
            patch.object(br.frappe.db, "get_value", side_effect=fake_get_value),
        ):
            result = br.resolve_payer("RES-0001", charge_category="Room")

        self.assertEqual(result["payer_type"], "Group Master")
        self.assertEqual(result["customer"], "CUST-ACME")

    def test_resolve_or_create_customer_creates_and_links_guest_customer(self):
        class FakeCustomerDoc:
            def __init__(self):
                self.customer_name = None
                self.custom_guest_id = None
                self.name = "CUST-NEW-001"

            def insert(self, ignore_permissions=False):
                return self

        def fake_exists(doctype, name):
            if doctype == "Hotel Guest" and name == "HG-001":
                return True
            return False

        def fake_get_value(doctype, filters, fieldname):
            if doctype == "Hotel Guest" and filters == "HG-001" and fieldname == "customer":
                return None
            if doctype == "Hotel Guest" and filters == "HG-001" and fieldname == "hotel_guest_name":
                return "New Group Payer"
            return None

        set_calls = []

        with (
            patch.object(br.frappe.db, "exists", side_effect=fake_exists),
            patch.object(br.frappe.db, "get_value", side_effect=fake_get_value),
            patch.object(br.frappe.db, "set_value", side_effect=lambda *args, **kwargs: set_calls.append((args, kwargs))),
            patch.object(br.frappe, "new_doc", return_value=FakeCustomerDoc()),
            patch.object(br.frappe, "get_meta", return_value=types.SimpleNamespace(has_field=lambda f: f == "custom_guest_id")),
            patch.object(br, "get_leaf_customer_group", return_value="Individual"),
        ):
            customer = br.resolve_or_create_customer(customer_hint="", hotel_guest="HG-001")

        self.assertEqual(customer, "CUST-NEW-001")
        self.assertTrue(any(call[0][0] == "Hotel Guest" and call[0][1] == "HG-001" for call in set_calls))


if __name__ == "__main__":
    unittest.main()
