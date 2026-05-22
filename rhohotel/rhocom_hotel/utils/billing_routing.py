"""
Billing routing resolver for Rhohotel.

Determines who pays a charge (Room, Restaurant, Bar, etc.) based on the
reservation type, configured routing rules, and any type-specific overrides.

Public API
----------
resolve_payer(reservation_name, charge_category="Room")
    Returns a dict: {"customer": str, "payer_type": str}

    payer_type values:
      "Guest"                 – individual guest customer on the check-in
      "Corporate Account"     – linked corporate customer on the reservation
      "Group Master"          – group master customer on the reservation
      "OTA Virtual Card"      – OTA's virtual card / account (Hotel Room Rate-level)
      "Internal (Cost Centre)"– zero-revenue internal allocation (House Use / Comp)

The resolver evaluates Hotel Billing Routing Rule documents in ascending priority
order and returns the first matching rule.  If no rule matches, it falls back to
the Guest payer type.

Usage
-----
    from rhohotel.rhocom_hotel.utils.billing_routing import resolve_payer

    result = resolve_payer("RES-2026-00001", charge_category="Room")
    customer = result["customer"]
    payer_type = result["payer_type"]
"""

import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_reservation(reservation_name):
    """Fetch reservation doc, raising a clean error if not found."""
    if not frappe.db.exists("Hotel Reservation", reservation_name):
        frappe.throw(
            _("Hotel Reservation {0} does not exist.").format(reservation_name)
        )
    return frappe.get_cached_doc("Hotel Reservation", reservation_name)


def _get_check_in_guest_customer(reservation):
    """
    Return the guest-side ERPNext Customer for this reservation.

    For Individual/Group-Split/OTA-Hotel-Collect, we want the guest's own customer.
    We try: reservation.customer → create/find fallback.
    """
    if reservation.customer:
        return reservation.customer

    # Try to find or create customer from the reservation data
    from rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation import (
        _find_or_create_customer_for_reservation,
    )
    return _find_or_create_customer_for_reservation(reservation)


def _get_marketplace_customer(ota_channel):
    """Return linked Market Place customer when the field exists in this installation."""
    if not ota_channel:
        return None
    try:
        if frappe.get_meta("Market Place").has_field("customer"):
            return frappe.db.get_value("Market Place", ota_channel, "customer")
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def _matching_rules(reservation_type, charge_category, corporate_customer=None, ota_channel=None):
    """
    Fetch active Hotel Billing Routing Rule records ordered by priority,
    filtered to those that match the given reservation type and charge category.

    Rules with a blank reservation_type or blank charge_category act as wildcards.
    """
    filters = {"is_active": 1}
    rules = frappe.get_all(
        "Hotel Billing Routing Rule",
        filters=filters,
        fields=[
            "name", "reservation_type", "charge_category", "payer",
            "priority", "corporate_customer", "ota_channel",
        ],
        order_by="priority asc",
    )

    matched = []
    for rule in rules:
        # Reservation type filter (blank = wildcard)
        if rule.reservation_type and rule.reservation_type != reservation_type:
            continue
        # Charge category filter (blank = wildcard)
        if rule.charge_category and rule.charge_category != charge_category:
            continue
        # Corporate customer narrow-match (optional)
        if rule.corporate_customer and rule.corporate_customer != corporate_customer:
            continue
        # OTA channel narrow-match (optional)
        if rule.ota_channel and rule.ota_channel != ota_channel:
            continue
        matched.append(rule)

    return matched


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

@frappe.whitelist()
def resolve_payer(reservation_name, charge_category="Room"):
    """
    Resolve which customer (payer) should be billed for a charge on this reservation.

    Args:
        reservation_name: Name of the Hotel Reservation document.
        charge_category:  Type of charge (Room, Restaurant, Bar, Laundry, etc.).

    Returns:
        dict with keys:
            customer   (str)  – ERPNext Customer name to bill
            payer_type (str)  – Human-readable payer category
    """
    res = _get_reservation(reservation_name)
    rtype = res.reservation_type or "Individual"
    charge_category = charge_category or "Room"

    # ------------------------------------------------------------------
    # Hard-coded overrides for types that have unambiguous routing.
    # ------------------------------------------------------------------

    if rtype == "House Use":
        # Internal use: route all charges internally unless a future policy says otherwise.
        return {
            "customer": None,
            "payer_type": "Internal (Cost Centre)",
            "cost_center": res.internal_cost_center or None,
        }

    # ------------------------------------------------------------------
    # Rule-based routing for all other types
    # ------------------------------------------------------------------

    corporate_customer = None
    if rtype == "Corporate" and res.corporate_guest:
        # Resolve the corporate ERPNext customer
        corporate_customer = frappe.db.get_value(
            "Hotel Guest", res.corporate_guest, "customer"
        )

    ota_channel = res.ota_channel if rtype == "OTA" else None

    rules = _matching_rules(rtype, charge_category, corporate_customer, ota_channel)

    for rule in rules:
        payer_type = rule.payer

        if payer_type == "Guest":
            return {
                "customer": _get_check_in_guest_customer(res),
                "payer_type": "Guest",
            }

        if payer_type == "Corporate Account":
            if corporate_customer:
                return {
                    "customer": corporate_customer,
                    "payer_type": "Corporate Account",
                }
            # Fall through if no corporate customer is linked

        if payer_type == "Group Master":
            if res.group_master_customer:
                return {
                    "customer": res.group_master_customer,
                    "payer_type": "Group Master",
                }
            # Fall through if no master customer

        if payer_type == "OTA Virtual Card":
            # For OTA Collect model, we bill to the OTA's own customer account.
            # Look up the Market Place's linked customer if available.
            ota_customer = _get_marketplace_customer(res.ota_channel)
            return {
                "customer": ota_customer or _get_check_in_guest_customer(res),
                "payer_type": "OTA Virtual Card",
                "ota_virtual_card_ref": res.ota_virtual_card_ref or None,
            }

        if payer_type == "Internal (Cost Centre)":
            return {
                "customer": None,
                "payer_type": "Internal (Cost Centre)",
                "cost_center": res.internal_cost_center or None,
            }

    # ------------------------------------------------------------------
    # Operational defaults when no explicit routing rule is configured.
    # ------------------------------------------------------------------
    if rtype == "Complimentary" and charge_category == "Room":
        return {
            "customer": None,
            "payer_type": "Internal (Cost Centre)",
            "cost_center": res.internal_cost_center or None,
        }

    if rtype == "Corporate" and charge_category == "Room" and corporate_customer:
        return {
            "customer": corporate_customer,
            "payer_type": "Corporate Account",
        }

    if rtype == "Group":
        if res.group_billing_mode == "Central" and res.group_master_customer:
            return {
                "customer": res.group_master_customer,
                "payer_type": "Group Master",
            }
        if charge_category == "Room" and res.group_master_customer:
            return {
                "customer": res.group_master_customer,
                "payer_type": "Group Master",
            }

    if rtype == "OTA" and charge_category == "Room" and res.ota_collection_model == "OTA Collect / Prepaid":
        ota_customer = _get_marketplace_customer(res.ota_channel)
        return {
            "customer": ota_customer or _get_check_in_guest_customer(res),
            "payer_type": "OTA Virtual Card",
            "ota_virtual_card_ref": res.ota_virtual_card_ref or None,
        }

    # Default fallback: guest pays.
    return {
        "customer": _get_check_in_guest_customer(res),
        "payer_type": "Guest",
    }


@frappe.whitelist()
def get_eligible_rate_codes(reservation_type, check_in_date=None, room_type=None, nights=None):
    """
    Return Hotel Room Rate records eligible for the given reservation type / source channel.

    Args:
        reservation_type: Individual, Corporate, Group, OTA, House Use, Complimentary
        check_in_date:    Date string for validity window filtering (optional)
        room_type:        Optional Hotel Room Type to require a tariff for
        nights:           Optional stay length for min/max stay checks

    Returns:
        list[dict] with rate_code, market_segment, meal_plan, description
    """
    from frappe.utils import getdate, nowdate

    today = getdate(check_in_date or nowdate())
    stay_nights = int(nights or 0)

    # Map reservation type to channel eligibility field
    channel_field_map = {
        "Individual":    "channel_front_desk",
        "Corporate":     "channel_corporate",
        "Group":         "channel_front_desk",
        "OTA":           "channel_ota",
        "House Use":     "channel_front_desk",
        "Complimentary": "channel_front_desk",
    }
    channel_field = channel_field_map.get(reservation_type, "channel_front_desk")

    # Market segments that correspond to House Use / Complimentary
    internal_segments = {"House Use", "Complimentary"}

    filters = {"is_active": 1, channel_field: 1}

    # For internal types, restrict to matching segment; for others exclude internal segments
    if reservation_type in ("House Use", "Complimentary"):
        filters["market_segment"] = reservation_type
    else:
        filters["market_segment"] = ["not in", list(internal_segments)]

    rates = frappe.get_all(
        "Hotel Room Rate",
        filters=filters,
        fields=["name", "rate_code", "market_segment", "meal_plan",
                "description", "valid_from", "valid_to", "cancellation_policy",
                "min_stay", "max_stay", "room_type", "rate_amount"],
        order_by="rate_code asc",
    )

    # Filter by validity window and room type
    eligible = []
    for r in rates:
        if r.valid_from and getdate(r.valid_from) > today:
            continue
        if r.valid_to and getdate(r.valid_to) < today:
            continue
        if stay_nights and r.min_stay and stay_nights < int(r.min_stay):
            continue
        if stay_nights and r.max_stay and stay_nights > int(r.max_stay):
            continue
        # If the rate is bound to a specific room type, only include it when it matches
        if room_type and r.room_type and r.room_type != room_type:
            continue
        eligible.append(r)

    return eligible
