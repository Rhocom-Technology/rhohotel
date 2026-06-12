"""
Centralized room availability logic for the Rhohotel application.

All room availability checks across the application (reservations, check-ins,
corporate check-ins, online bookings) must use the functions in this module
instead of duplicating overlap-query logic inline.

This module is the *single source of truth* for overlap detection.  It covers
two booking surfaces:

  1. Hotel Room Check In
       – Active stay record created when a guest physically checks in.
       – Queried directly: `tabHotel Room Check In`.

  2. Canonical Hotel Reservation (current)
       – One parent per booking, rooms stored in child table Hotel Reservation Room.
       – Queried via a JOIN: `tabHotel Reservation Room` → `tabHotel Reservation`.

A room must be free in both surfaces before it is considered available.

Public API
----------
check_checkin_conflict(room_number, check_in_dt, check_out_dt, exclude_checkin=None)
    Returns the first conflicting Hotel Room Check In dict, or None.

check_canonical_reservation_conflict(room_number, check_in_dt, check_out_dt, exclude_canonical=None)
    Returns the first conflicting canonical Hotel Reservation (via its room allocation
    child rows) dict, or None.

assert_room_available(room_number, check_in_dt, check_out_dt, *, exclude_checkin=None,
                      exclude_canonical=None)
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

_DEFAULT_CHECK_IN_TIME = time(13, 0)
_DEFAULT_CHECK_OUT_TIME = time(11, 0)


def _get_hotel_time_strings():
    """
    Return (check_in_time_str, check_out_time_str) read from Hotel Settings.

    Falls back to ('13:00:00', '11:00:00') if settings are not accessible.
    The strings are in 'HH:MM:SS' format as expected by MariaDB TIMESTAMP().
    """
    try:
        settings = frappe.get_single("Hotel Settings")
        ci = str(settings.default_check_in_time or "").split(".")[0].strip()
        co = str(settings.default_check_out_time or "").split(".")[0].strip()
        if len(ci) == 5:
            ci += ":00"
        if len(co) == 5:
            co += ":00"
        if not ci:
            ci = "13:00:00"
        if not co:
            co = "11:00:00"
        return ci, co
    except Exception:
        return "13:00:00", "11:00:00"


def _parse_hotel_time_str(time_str, fallback):
    """Parse a HH:MM:SS or HH:MM string into a :class:`datetime.time` object."""
    value = str(time_str or "").split(".")[0].strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return fallback


def _normalize_checkin_dt(value):
    """
    Coerce *value* to a datetime using the hotel's default check-in time for
    date-only inputs.  Full datetime values are returned as-is.
    """
    if isinstance(value, datetime):
        return value
    ci_str, _ = _get_hotel_time_strings()
    ci_time = _parse_hotel_time_str(ci_str, _DEFAULT_CHECK_IN_TIME)
    if isinstance(value, str):
        value = value.strip()
        if len(value) == 10 and "T" not in value and " " not in value:
            return datetime.combine(getdate(value), ci_time)
        try:
            return get_datetime(value)
        except Exception:
            return datetime.combine(getdate(value), ci_time)
    return datetime.combine(value, ci_time)


def _normalize_checkout_dt(value):
    """
    Coerce *value* to a datetime using the hotel's default check-out time for
    date-only inputs.  Full datetime values are returned as-is.
    """
    if isinstance(value, datetime):
        return value
    _, co_str = _get_hotel_time_strings()
    co_time = _parse_hotel_time_str(co_str, _DEFAULT_CHECK_OUT_TIME)
    if isinstance(value, str):
        value = value.strip()
        if len(value) == 10 and "T" not in value and " " not in value:
            return datetime.combine(getdate(value), co_time)
        try:
            return get_datetime(value)
        except Exception:
            return datetime.combine(getdate(value), co_time)
    return datetime.combine(value, co_time)


# Kept for backward compatibility – defaults to check-in time boundary.
def _normalize_dt(value):
    return _normalize_checkin_dt(value)


# ---------------------------------------------------------------------------
# Core conflict-detection functions
# ---------------------------------------------------------------------------

def check_checkin_conflict(room_number, check_in_dt, check_out_dt, exclude_checkin=None):
    """
    Check for a conflicting Hotel Room Check In in the given period.

    Two passes are made:

    Pass 1 – Standard time-overlap:
        existing.check_in_datetime < check_out_dt
        AND existing.expected_check_out_datetime > check_in_dt

    Pass 2 – Overdue-checkout guard:
        A guest whose expected checkout has already passed but whose record is
        still in "Checked In" status is physically still in the room.  Their
        expected_check_out_datetime ≤ check_in_dt would cause Pass 1 to miss
        them, so Pass 2 catches that edge case explicitly.
        Condition: status = 'Checked In'
                   AND check_in_datetime < check_out_dt   (started before our checkout)
                   AND expected_check_out_datetime <= check_in_dt  (should have left already)

    Args:
        room_number    : Hotel Room name.
        check_in_dt    : Period start – datetime or date/str (normalized to 12:00).
        check_out_dt   : Period end   – datetime or date/str (normalized to 12:00).
        exclude_checkin: Check-in name to exclude (e.g. the one being extended).

    Returns:
        dict with keys (name, check_in_datetime, expected_check_out_datetime, guest), or None.
    """
    check_in_dt = _normalize_checkin_dt(check_in_dt)
    check_out_dt = _normalize_checkout_dt(check_out_dt)

    base_filters = {
        "room_number": room_number,
        "docstatus": ["in", [0, 1]],  # Draft or Submitted – explicitly exclude Cancelled
    }
    if exclude_checkin:
        base_filters["name"] = ["!=", exclude_checkin]

    # Pass 1: standard time-overlap
    overlap_filters = {
        **base_filters,
        "status": ["in", ["Draft", "Checked In"]],
        "check_in_datetime": ["<", check_out_dt],
        "expected_check_out_datetime": [">", check_in_dt],
    }
    results = frappe.get_all(
        "Hotel Room Check In",
        filters=overlap_filters,
        fields=["name", "check_in_datetime", "expected_check_out_datetime", "guest"],
        limit=1,
    )
    if results:
        return results[0]

    # Pass 2: overdue-checkout guard for current arrivals only.
    # A guest still "Checked In" whose expected checkout has passed is still in
    # the room today, but that transient status should not block future searches
    # after the expected checkout date.
    if getdate(check_in_dt) <= getdate(datetime.now()):
        overdue_filters = {
            **base_filters,
            "status": "Checked In",
            "check_in_datetime": ["<", check_out_dt],
            "expected_check_out_datetime": ["<=", check_in_dt],
        }
        overdue_results = frappe.get_all(
            "Hotel Room Check In",
            filters=overdue_filters,
            fields=["name", "check_in_datetime", "expected_check_out_datetime", "guest"],
            limit=1,
        )
        return overdue_results[0] if overdue_results else None

    return None


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

    Child rows that have already produced a Hotel Room Check In are also excluded.
    After check-in, the live check-in record is the source of truth for the guest's
    current room, including room transfers.

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
    check_in_dt = _normalize_checkin_dt(check_in_dt)
    check_out_dt = _normalize_checkout_dt(check_out_dt)

    check_in_str = check_in_dt.strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M:%S")
    ci_time_str, co_time_str = _get_hotel_time_strings()

    # Build optional exclusion clause
    exclude_clause = ""
    params: tuple = (room_number, ci_time_str, check_out_str, co_time_str, check_in_str)
    if exclude_canonical:
        exclude_clause = "AND hr.name != %s"
        params = (room_number, ci_time_str, check_out_str, co_time_str, check_in_str, exclude_canonical)

    results = frappe.db.sql(
        f"""
        SELECT hr.name, hr.from_date, hr.to_date, hr.primary_guest_name
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        WHERE rr.room_number = %s
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN
              ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND COALESCE(rr.check_in_reference, '') = ''
          AND COALESCE(rr.status, 'Reserved') NOT IN
              ('Checked In', 'Checked Out', 'Cancelled')
          AND TIMESTAMP(hr.from_date, %s) < %s
          AND TIMESTAMP(hr.to_date,   %s) > %s
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

    Two booking surfaces are checked in order:
      1. Hotel Room Check In            – via check_checkin_conflict()
      2. Canonical Hotel Reservation    – via check_canonical_reservation_conflict()

    Additionally, for non-Group reservation types, a room block protection guard
    checks whether the room's type is fully blocked by a Group reservation block
    for the requested period.

    Args:
        room_number        : Hotel Room name.
        check_in_dt        : Period start – datetime or date/str.
        check_out_dt       : Period end   – datetime or date/str.
        exclude_reservation: Ignored (kept for backward compatibility).
        exclude_checkin    : Hotel Room Check In name to ignore.
        exclude_canonical  : Canonical Hotel Reservation name to ignore
                             (pass self.name when validating the reservation being saved).
        reservation_type   : The type of the reservation being validated. When set to
                             'Group', the block protection guard is bypassed so the group
                             can pick up its own blocked rooms freely.
    """
    check_in_dt = _normalize_checkin_dt(check_in_dt)
    check_out_dt = _normalize_checkout_dt(check_out_dt)

    # --- Surface 1: Hotel Room Check In ---
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

    # --- Surface 2: canonical Hotel Reservation (room allocation child table) ---
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

    # --- Defensive guard: Hotel Room.status ---
    # If the room is marked "Occupied" in the Hotel Room record but no active
    # check-in record was found (stale data or race condition), block only
    # immediate/current arrivals. Future reservations should not be rejected
    # solely from a transient occupied status snapshot.
    room_status = frappe.db.get_value("Hotel Room", room_number, "status")
    if room_status == "Occupied" and check_in_dt <= datetime.now():
        frappe.throw(
            _(
                "{0} is currently occupied. Please check out the current guest "
                "before creating a new reservation or check-in."
            ).format(room_number)
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
    check_in_dt, check_out_dt, room_type=None, require_clean=False, require_vacant=False,
    rate_code=None
):
    """
    Return all rooms that are available for the given period, with pricing attached.

    Excludes rooms that are:
    - Not in service / flagged for maintenance
    - Overlapping an active Hotel Room Check In
    - Allocated in an active canonical Hotel Reservation (via Hotel Reservation Room child table)

    Args:
        check_in_dt   : Check-in  datetime / date / str.
        check_out_dt  : Check-out datetime / date / str.
        room_type     : Optional Hotel Room Type filter.
        require_clean : When True, only rooms with housekeeping_status = 'Clean' are returned.
        require_vacant: When True, only rooms with status = 'Vacant' are returned.
        rate_code     : Optional Hotel Room Rate name to price returned rooms with.

    Returns:
        list[dict] – each dict has name, room_type, floor, capacity,
                     rate_per_night, total_amount.
    """
    from rhohotel.api import get_room_rate

    check_in_dt = _normalize_checkin_dt(check_in_dt)
    check_out_dt = _normalize_checkout_dt(check_out_dt)

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
    ci_time_str, co_time_str = _get_hotel_time_strings()

    # Overlapping active check-ins (standard time-overlap)
    checkin_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT room_number
        FROM `tabHotel Room Check In`
        WHERE room_number IN ({placeholders})
          AND docstatus != 2
          AND status IN ('Draft', 'Checked In')
          AND check_in_datetime < %s
          AND expected_check_out_datetime > %s
        """,
        tuple(room_numbers) + (check_out_str, check_in_str),
        as_dict=True,
    )

    overdue_rows = []
    if getdate(check_in_dt) <= getdate(datetime.now()):
        # Overdue-checkout guard: guests still "Checked In" past their expected
        # checkout block current arrivals, but not future availability searches.
        overdue_rows = frappe.db.sql(
            f"""
            SELECT DISTINCT room_number
            FROM `tabHotel Room Check In`
            WHERE room_number IN ({placeholders})
              AND docstatus != 2
              AND status = 'Checked In'
              AND check_in_datetime < %s
              AND expected_check_out_datetime <= %s
            """,
            tuple(room_numbers) + (check_out_str, check_in_str),
            as_dict=True,
        )

    # Rooms allocated in a canonical Hotel Reservation for an overlapping period.
    # Hotel Reservation stores rooms in the Hotel Reservation Room child table, so
    # we JOIN child → parent to apply status and date filters on the parent.
    # Checked-in reservation rows are excluded because the live Hotel Room Check In
    # record becomes the operational occupancy source, including after transfers.
    canonical_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT rr.room_number
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        WHERE rr.room_number IN ({placeholders})
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN
              ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND COALESCE(rr.check_in_reference, '') = ''
          AND COALESCE(rr.status, 'Reserved') NOT IN
              ('Checked In', 'Checked Out', 'Cancelled')
          AND TIMESTAMP(hr.from_date, %s) < %s
          AND TIMESTAMP(hr.to_date,   %s) > %s
        """,
        tuple(room_numbers) + (ci_time_str, check_out_str, co_time_str, check_in_str),
        as_dict=True,
    )

    unavailable = set(
        [r.room_number for r in checkin_rows]
        + [r.room_number for r in overdue_rows]     # overdue / never-checked-out guests
        + [r.room_number for r in canonical_rows]   # canonical reservation allocations
    )

    available = [r for r in all_rooms if r.name not in unavailable]

    # ------------------------------------------------------------------
    # 3. Attach pricing
    # ------------------------------------------------------------------
    from_date_str = check_in_dt.strftime("%Y-%m-%d")
    nights = date_diff(getdate(check_out_dt), getdate(check_in_dt)) or 1

    for room in available:
        rate = get_room_rate(room.room_type, rate_type=rate_code, check_in_date=from_date_str)
        room["rate_per_night"] = rate
        room["total_amount"] = rate * nights
        if rate_code:
            room["rate_code"] = rate_code

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
    if not frappe.db.get_single_value("Hotel Settings", "enable_group_room_blocks"):
        return 0

    check_in_dt = _normalize_checkin_dt(check_in_dt)
    check_out_dt = _normalize_checkout_dt(check_out_dt)

    check_in_str = check_in_dt.strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M:%S")
    ci_time_str, co_time_str = _get_hotel_time_strings()

    exclude_clause = ""
    params: tuple = (room_type, ci_time_str, check_out_str, co_time_str, check_in_str)
    if context_reservation:
        exclude_clause = "AND hr.name != %s"
        params = (room_type, ci_time_str, check_out_str, co_time_str, check_in_str, context_reservation)

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
          AND TIMESTAMP(hr.from_date, %s) < %s
          AND TIMESTAMP(hr.to_date,   %s) > %s
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
    ci_time_str, co_time_str = _get_hotel_time_strings()
    check_in_str = _normalize_checkin_dt(check_in_dt).strftime("%Y-%m-%d %H:%M:%S")
    check_out_str = _normalize_checkout_dt(check_out_dt).strftime("%Y-%m-%d %H:%M:%S")

    booked = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT rr.room_number) AS booked_count
        FROM `tabHotel Reservation Room` rr
        INNER JOIN `tabHotel Reservation` hr ON hr.name = rr.parent
        INNER JOIN `tabHotel Room` room ON room.name = rr.room_number
        WHERE room.room_type = %s
          AND hr.docstatus != 2
          AND hr.reservation_status NOT IN ('Cancelled', 'Checked Out', 'No Show', 'Expired')
          AND COALESCE(rr.check_in_reference, '') = ''
          AND COALESCE(rr.status, 'Reserved') NOT IN ('Checked In', 'Checked Out', 'Cancelled')
          AND TIMESTAMP(hr.from_date, %s) < %s
          AND TIMESTAMP(hr.to_date,   %s) > %s
        """,
        (room_type, ci_time_str, check_out_str, co_time_str, check_in_str),
        as_dict=True,
    )
    already_booked = int((booked[0].booked_count) if booked else 0)
    total = get_total_room_count(room_type)

    # Available to non-group = total - protected - already_booked
    return (total - protected - already_booked) <= 0
