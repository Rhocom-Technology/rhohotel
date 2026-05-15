"""
Centralized room availability logic for the Rhohotel application.

All room availability checks across the application (reservations, check-ins,
corporate check-ins, front-desk reservations, online bookings) must use the
functions in this module instead of duplicating overlap-query logic inline.

This module is the *single source of truth* for overlap detection.  It covers
three distinct booking surfaces:

  1. Legacy Hotel Room Reservation
       – Single-room reservation created per room by the front-desk flow.
       – Queried directly: `tabHotel Room Reservation`.

  2. Hotel Room Check In
       – Active stay record created when a guest physically checks in.
       – Queried directly: `tabHotel Room Check In`.

  3. Canonical Hotel Reservation (new)
       – One parent per booking, rooms stored in child table Hotel Reservation Room.
       – Queried via a JOIN: `tabHotel Reservation Room` → `tabHotel Reservation`.

A room must be free in *all three* surfaces before it is considered available.

Public API
----------
check_reservation_conflict(room_number, check_in_dt, check_out_dt, exclude_reservation=None)
    Returns the first conflicting Hotel Room Reservation dict, or None.

check_checkin_conflict(room_number, check_in_dt, check_out_dt, exclude_checkin=None)
    Returns the first conflicting Hotel Room Check In dict, or None.

check_canonical_reservation_conflict(room_number, check_in_dt, check_out_dt, exclude_canonical=None)
    Returns the first conflicting canonical Hotel Reservation (via its room allocation
    child rows) dict, or None.

assert_room_available(room_number, check_in_dt, check_out_dt, *, exclude_reservation=None,
                      exclude_checkin=None, exclude_canonical=None)
    Raises frappe.ValidationError (via frappe.throw) if a conflict is found in any surface.

get_available_rooms(check_in_dt, check_out_dt, room_type=None, require_clean=False,
                    require_vacant=False)
    Returns a list of available room dicts for the given period, with pricing attached.
"""

from datetime import datetime, time

import frappe
from frappe import _
from frappe.utils import date_diff, get_datetime, getdate

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DEFAULT_HOTEL_TIME = time(12, 0)


def _normalize_dt(value):
    """
    Coerce *value* to a datetime object at the hotel's standard 12:00 boundary.

    Accepts:
    - datetime  → returned as-is
    - date      → combined with 12:00
    - str       → parsed as datetime; if that fails, parsed as date + 12:00
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return get_datetime(value)
        except Exception:
            return datetime.combine(getdate(value), _DEFAULT_HOTEL_TIME)
    # Assume date object
    return datetime.combine(value, _DEFAULT_HOTEL_TIME)


# ---------------------------------------------------------------------------
# Core conflict-detection functions
# ---------------------------------------------------------------------------


def check_reservation_conflict(room_number, check_in_dt, check_out_dt, exclude_reservation=None):
    """
    Check for a conflicting Hotel Room Reservation in the given period.

    Overlap formula: existing.from_date < check_out_dt AND existing.to_date > check_in_dt

    When from_date / to_date are DATE fields, MySQL compares them as
    '2024-01-05 00:00:00', so passing 12:00 datetimes correctly handles
    same-day check-out/check-in transitions (no false conflicts).

    Args:
        room_number       : Hotel Room name.
        check_in_dt       : Period start – datetime or date/str (normalized to 12:00).
        check_out_dt      : Period end   – datetime or date/str (normalized to 12:00).
        exclude_reservation: Reservation name to exclude (e.g. the one being validated).

    Returns:
        dict with keys (name, from_date, to_date, guest_name), or None.
    """
    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    filters = {
        "room_number": room_number,
        "docstatus": ["!=", 2],
        "status": ["not in", ["Cancelled", "Completed", "No Show"]],
        "from_date": ["<", check_out_dt],
        "to_date": [">", check_in_dt],
    }

    if exclude_reservation:
        filters["name"] = ["!=", exclude_reservation]

    results = frappe.get_all(
        "Hotel Room Reservation",
        filters=filters,
        fields=["name", "from_date", "to_date", "guest_name"],
        limit=1,
    )
    return results[0] if results else None


def check_checkin_conflict(room_number, check_in_dt, check_out_dt, exclude_checkin=None):
    """
    Check for a conflicting Hotel Room Check In in the given period.

    Overlap formula:
        existing.check_in_datetime < check_out_dt
        AND existing.expected_check_out_datetime > check_in_dt

    Args:
        room_number    : Hotel Room name.
        check_in_dt    : Period start – datetime or date/str (normalized to 12:00).
        check_out_dt   : Period end   – datetime or date/str (normalized to 12:00).
        exclude_checkin: Check-in name to exclude (e.g. the one being extended).

    Returns:
        dict with keys (name, check_in_datetime, expected_check_out_datetime, guest), or None.
    """
    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    filters = {
        "room_number": room_number,
        "status": ["in", ["Draft", "Checked In"]],
        "check_in_datetime": ["<", check_out_dt],
        "expected_check_out_datetime": [">", check_in_dt],
    }

    if exclude_checkin:
        filters["name"] = ["!=", exclude_checkin]

    results = frappe.get_all(
        "Hotel Room Check In",
        filters=filters,
        fields=["name", "check_in_datetime", "expected_check_out_datetime", "guest"],
        limit=1,
    )
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Canonical Hotel Reservation conflict detection
# ---------------------------------------------------------------------------


def check_canonical_reservation_conflict(
    room_number, check_in_dt, check_out_dt, exclude_canonical=None
):
    """
    Check for a conflicting canonical Hotel Reservation for the given room and period.

    Unlike the legacy Hotel Room Reservation (which stores one room per parent
    document), the canonical Hotel Reservation stores rooms in a child table
    (Hotel Reservation Room).  This function queries that child table joined
    against the parent to detect overlapping allocations.

    Overlap formula applied to the *parent* Hotel Reservation:
        parent.from_date < check_out_dt AND parent.to_date > check_in_dt

    Statuses excluded from conflict (reservation is no longer active):
        Cancelled, Checked Out, No Show, Expired

    Args:
        room_number       : Hotel Room name to check.
        check_in_dt       : Period start – datetime or date/str (normalized to 12:00).
        check_out_dt      : Period end   – datetime or date/str (normalized to 12:00).
        exclude_canonical : Name of the canonical Hotel Reservation to exclude
                            (pass self.name when validating the document being saved
                            so it does not self-conflict on re-save).

    Returns:
        dict with keys (name, from_date, to_date, primary_guest_name), or None.
    """
    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    check_in_str = check_in_dt.strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Build optional exclusion clause
    exclude_clause = ""
    params: tuple = (room_number, check_out_str, check_in_str)
    if exclude_canonical:
        exclude_clause = "AND hr.name != %s"
        params = (room_number, check_out_str, check_in_str, exclude_canonical)

    results = frappe.db.sql(
        f"""
        SELECT hr.name, hr.from_date, hr.to_date, hr.primary_guest_name
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        WHERE rr.room_number = %s
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN
              ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND hr.from_date < %s
          AND hr.to_date   > %s
          {exclude_clause}
        LIMIT 1
        """,
        params,
        as_dict=True,
    )
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Assertion helper (throws on conflict – checks all three booking surfaces)
# ---------------------------------------------------------------------------


def assert_room_available(
    room_number,
    check_in_dt,
    check_out_dt,
    *,
    exclude_reservation=None,
    exclude_checkin=None,
    exclude_canonical=None,
    reservation_type=None,
):
    """
    Assert that *room_number* has no conflicting booking in any active surface
    for the period [check_in_dt, check_out_dt).

    Raises frappe.ValidationError (via frappe.throw) on the first conflict found.

    Three booking surfaces are checked in order:
      1. Legacy Hotel Room Reservation  – via check_reservation_conflict()
      2. Hotel Room Check In            – via check_checkin_conflict()
      3. Canonical Hotel Reservation    – via check_canonical_reservation_conflict()

    Additionally, for non-Group reservation types, a room block protection guard
    checks whether the room's type is fully blocked by a Group reservation block
    for the requested period.

    Args:
        room_number        : Hotel Room name.
        check_in_dt        : Period start – datetime or date/str.
        check_out_dt       : Period end   – datetime or date/str.
        exclude_reservation: Legacy Hotel Room Reservation name to ignore.
        exclude_checkin    : Hotel Room Check In name to ignore.
        exclude_canonical  : Canonical Hotel Reservation name to ignore
                             (pass self.name when validating the reservation being saved).
        reservation_type   : The type of the reservation being validated. When set to
                             'Group', the block protection guard is bypassed so the group
                             can pick up its own blocked rooms freely.
    """
    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    # --- Surface 1: legacy Hotel Room Reservation ---
    res_conflict = check_reservation_conflict(
        room_number, check_in_dt, check_out_dt, exclude_reservation
    )
    if res_conflict:
        frappe.throw(
            _("{0} is already reserved from {1} to {2} (Reservation: {3}).").format(
                room_number,
                res_conflict.from_date,
                res_conflict.to_date,
                res_conflict.name,
            )
        )

    # --- Surface 2: Hotel Room Check In ---
    ci_conflict = check_checkin_conflict(
        room_number, check_in_dt, check_out_dt, exclude_checkin
    )
    if ci_conflict:
        frappe.throw(
            _("{0} is already checked in from {1} to {2} (Check In: {3}).").format(
                room_number,
                ci_conflict.check_in_datetime,
                ci_conflict.expected_check_out_datetime,
                ci_conflict.name,
            )
        )

    # --- Surface 3: canonical Hotel Reservation (room allocation child table) ---
    canonical_conflict = check_canonical_reservation_conflict(
        room_number, check_in_dt, check_out_dt, exclude_canonical
    )
    if canonical_conflict:
        frappe.throw(
            _(
                "{0} is already allocated in reservation {3} from {1} to {2}."
            ).format(
                room_number,
                canonical_conflict.from_date,
                canonical_conflict.to_date,
                canonical_conflict.name,
            )
        )

    # --- Surface 4: Room block protection guard (non-Group bookings only) ---
    if reservation_type != "Group":
        room_type = frappe.db.get_value("Hotel Room", room_number, "room_type")
        if room_type and is_room_type_blocked_for_period(
            room_type, check_in_dt, check_out_dt, context_reservation=exclude_canonical
        ):
            frappe.throw(
                _(
                    "{0} ({1}) is fully allocated to a group block for {2} to {3} "
                    "and cannot be added to individual or non-group reservations."
                ).format(
                    room_number,
                    room_type,
                    check_in_dt.strftime("%Y-%m-%d"),
                    check_out_dt.strftime("%Y-%m-%d"),
                )
            )


# ---------------------------------------------------------------------------
# Available-rooms query
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_available_rooms(
    check_in_dt, check_out_dt, room_type=None, require_clean=False, require_vacant=False
):
    """
    Return all rooms that are available for the given period, with pricing attached.

    Excludes rooms that are:
    - Not in service / flagged for maintenance
    - Under an active Temporary Booking hold
    - Overlapping an active Hotel Room Reservation (legacy)
    - Overlapping an active Hotel Room Check In
    - Allocated in an active canonical Hotel Reservation (via Hotel Reservation Room child table)

    Args:
        check_in_dt   : Check-in  datetime / date / str.
        check_out_dt  : Check-out datetime / date / str.
        room_type     : Optional Hotel Room Type filter.
        require_clean : When True, only rooms with housekeeping_status = 'Clean' are returned.
        require_vacant: When True, only rooms with status = 'Vacant' are returned.

    Returns:
        list[dict] – each dict has name, room_type, floor, capacity,
                     rate_per_night, total_amount.
    """
    from rhohotel.api import get_room_rate

    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    if check_out_dt <= check_in_dt:
        frappe.throw(_("Check-out must be after check-in"))

    # ------------------------------------------------------------------
    # 1. Candidate rooms – pass basic operational filters
    # ------------------------------------------------------------------
    filters = {"operational_status": "In Service", "maintenance_flag": 0}
    if room_type:
        filters["room_type"] = room_type
    if require_clean:
        filters["housekeeping_status"] = "Clean"
    if require_vacant:
        filters["status"] = "Vacant"

    all_rooms = frappe.get_all(
        "Hotel Room",
        filters=filters,
        fields=["name", "room_type", "floor", "capacity"],
    )

    if not all_rooms:
        return []

    room_numbers = [r.name for r in all_rooms]
    placeholders = ", ".join(["%s"] * len(room_numbers))

    # ------------------------------------------------------------------
    # 2. Bulk-exclude unavailable rooms via SQL (single pass each)
    # ------------------------------------------------------------------
    check_in_str = check_in_dt.strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M:%S")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Active Temporary Booking holds
    held_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT tbr.room_number
        FROM `tabTemporary Booking` tb
        INNER JOIN `tabTemporary Booking Room` tbr ON tb.name = tbr.parent
        WHERE tbr.room_number IN ({placeholders})
          AND tb.status IN ('Hold', 'Payment Link Generated')
          AND tb.payment_status = 'Pending'
          AND tb.booking_status = 'Held'
          AND tb.hold_expires_at > %s
        """,
        tuple(room_numbers) + (now_str,),
        as_dict=True,
    )

    # Overlapping confirmed reservations
    booked_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT room_number
        FROM `tabHotel Room Reservation`
        WHERE room_number IN ({placeholders})
          AND docstatus != 2
          AND status NOT IN ('Cancelled', 'Completed', 'No Show')
          AND from_date < %s
          AND to_date > %s
        """,
        tuple(room_numbers) + (check_out_str, check_in_str),
        as_dict=True,
    )

    # Overlapping active check-ins
    checkin_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT room_number
        FROM `tabHotel Room Check In`
        WHERE room_number IN ({placeholders})
          AND status IN ('Draft', 'Checked In')
          AND check_in_datetime < %s
          AND expected_check_out_datetime > %s
        """,
        tuple(room_numbers) + (check_out_str, check_in_str),
        as_dict=True,
    )

    # Rooms allocated in a canonical Hotel Reservation for an overlapping period.
    # Hotel Reservation stores rooms in the Hotel Reservation Room child table, so
    # we JOIN child → parent to apply status and date filters on the parent.
    canonical_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT rr.room_number
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        WHERE rr.room_number IN ({placeholders})
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN
              ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND hr.from_date < %s
          AND hr.to_date   > %s
        """,
        tuple(room_numbers) + (check_out_str, check_in_str),
        as_dict=True,
    )

    unavailable = set(
        [r.room_number for r in held_rows]
        + [r.room_number for r in booked_rows]
        + [r.room_number for r in checkin_rows]
        + [r.room_number for r in canonical_rows]   # canonical reservation allocations
    )

    available = [r for r in all_rooms if r.name not in unavailable]

    # ------------------------------------------------------------------
    # 3. Attach pricing
    # ------------------------------------------------------------------
    from_date_str = check_in_dt.strftime("%Y-%m-%d")
    nights = date_diff(getdate(check_out_dt), getdate(check_in_dt)) or 1

    for room in available:
        rate = get_room_rate(room.room_type, check_in_date=from_date_str)
        room["rate_per_night"] = rate
        room["total_amount"] = rate * nights

    return available


# ---------------------------------------------------------------------------
# Room block protection helpers
# ---------------------------------------------------------------------------


def get_protected_block_count(room_type, check_in_dt, check_out_dt, context_reservation=None):
    """
    Return the total number of rooms of *room_type* that are currently protected
    by active Group reservation room blocks for the given period.

    A room block on a Group reservation withholds inventory from all non-group
    bookings so that the group can pick up rooms without encountering conflicts.

    Args:
        room_type            : Hotel Room Type name.
        check_in_dt          : Period start (datetime / date / str).
        check_out_dt         : Period end   (datetime / date / str).
        context_reservation  : When set (a Group reservation name), the protected
                               count for THAT reservation's own blocks is excluded so
                               that pickup into the same group doesn't count against
                               itself.

    Returns:
        int – total protected (blocked) room count from other active Group reservations.
    """
    check_in_dt = _normalize_dt(check_in_dt)
    check_out_dt = _normalize_dt(check_out_dt)

    check_in_str = check_in_dt.strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M:%S")

    exclude_clause = ""
    params: tuple = (room_type, check_out_str, check_in_str)
    if context_reservation:
        exclude_clause = "AND hr.name != %s"
        params = (room_type, check_out_str, check_in_str, context_reservation)

    result = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(rb.quantity), 0) AS protected_count
        FROM `tabHotel Reservation Room Block` rb
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rb.parent
        WHERE rb.room_type = %s
          AND hr.docstatus != 2
          AND hr.reservation_type = 'Group'
          AND hr.reservation_status NOT IN
              ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND hr.from_date < %s
          AND hr.to_date   > %s
          {exclude_clause}
        """,
        params,
        as_dict=True,
    )
    return int((result[0].protected_count) if result else 0)


def get_total_room_count(room_type):
    """Return the total count of in-service rooms of the given room type."""
    return frappe.db.count(
        "Hotel Room",
        {"room_type": room_type, "operational_status": "In Service", "maintenance_flag": 0},
    )


def is_room_type_blocked_for_period(
    room_type, check_in_dt, check_out_dt, context_reservation=None
):
    """
    Return True if protected block count >= available room count for *room_type*,
    meaning individual/non-group bookings should not be able to take any more
    rooms of this type.

    This is a soft guard – it checks type-level protection, not specific rooms.
    assert_room_type_unblocked() raises the actual error.
    """
    protected = get_protected_block_count(
        room_type, check_in_dt, check_out_dt, context_reservation
    )
    if protected <= 0:
        return False

    # Count already-booked rooms of this type for the period (non-group bookings)
    check_in_str = _normalize_dt(check_in_dt).strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = _normalize_dt(check_out_dt).strftime("%Y-%m-%d %H:%M:%S")

    booked = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT rr.room_number) AS booked_count
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        INNER JOIN `tabHotel Room` room ON room.name = rr.room_number
        WHERE room.room_type = %s
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND hr.from_date < %s
          AND hr.to_date   > %s
        """,
        (room_type, check_out_str, check_in_str),
        as_dict=True,
    )
    already_booked = int((booked[0].booked_count) if booked else 0)
    total = get_total_room_count(room_type)

    # Available to non-group = total - protected - already_booked
    return (total - protected - already_booked) <= 0

