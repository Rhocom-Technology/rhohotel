# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

"""
hotel_reservation_room.py – Child table for canonical Hotel Reservation.

Each row represents one room allocation within a single Hotel Reservation.
This replaces the individual-row pattern from the legacy Hotel Room Reservation
(one parent per room) with a child-table pattern (one parent, N room rows).

Field responsibilities
----------------------
  room_number       – The specific Hotel Room being allocated.
  room_type         – Fetched automatically from room_number.room_type.
  rate_type         – Rate category (Standard, Corporate, etc.) from the tariff lookup.
  season_type       – Active season at check-in date from Hotel Season records.
  rate_per_night    – Resolved nightly tariff; set by the parent on_validate or UI fetch.
  number_of_nights  – Copied from parent (to_date - from_date); used for room_total.
  discount          – Optional per-room discount (fixed amount).
  room_total        – (rate_per_night × number_of_nights) - discount; feeds parent subtotal.

  Occupant fields   – Who is physically staying in this room.  Optional; falls back
                      to parent's primary_guest_name when blank.

  check_in_reference  – Populated by check-in workflow pointing to Hotel Room Check In.
  checkout_reference  – Populated by checkout workflow pointing to Hotel Room Check Out.

Room availability
-----------------
Availability for this row's room_number over the parent's date range is validated
by the centralized utility in room_availability.py.  The utility now checks the
`tabHotel Reservation Room` child table (joined to `tabHotel Reservation`) so that
any room allocated in a canonical reservation is correctly excluded from availability
results for overlapping periods.
"""

from frappe.model.document import Document


class HotelReservationRoom(Document):
    """
    Child row of Hotel Reservation representing one room allocation.

    Business rules enforced at the parent level (HotelReservation.validate):
      - room_number must be available for parent.from_date → parent.to_date.
      - room_total is computed from rate_per_night, number_of_nights, and discount.
      - number_of_nights is inherited from the parent document.
    """
    pass
