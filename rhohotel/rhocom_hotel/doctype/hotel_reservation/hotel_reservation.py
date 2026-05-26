# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

"""
hotel_reservation.py – Canonical single-reservation doctype for Rhohotel.

Background
----------
This module is the *canonical* reservation doctype.  One Hotel Reservation
document represents the full lifecycle of a stay — from initial hold through
check-in, checkout, and invoicing — regardless of the originating channel
(Individual, Corporate, Group, OTA, House Use, or Complimentary).

Lifecycle / state machine
-------------------------
  Draft → Hold
    Room hold is activated; hold_expires_at is set.

  Hold → Confirmed
    Payment received (or front-desk confirm override).
    Rooms are firm-booked; room status on Hotel Room changes to Reserved.

  Hold → Cancelled | Expired
    Rooms released back to Vacant; no invoice created.

  Confirmed → Checked In
    Guest has arrived.  check_in_time is stamped.
    Hotel Room status changes to Occupied.

  Confirmed → Cancelled
    Staff cancels before check-in.  Refund logic triggered if payment collected.

  Checked In → Checked Out
    Guest departs.  check_out_time is stamped.
    Hotel Room reverts to Vacant (housekeeping task auto-created).

  Any active state → No Show
    Policy-driven transition when guest does not arrive by a threshold time.

Room availability
-----------------
All availability checks are delegated to the centralized utility:
    rhohotel.rhocom_hotel.utils.room_availability

The utility checks Hotel Room Check In and canonical Hotel Reservation room
allocations so that double-booking is prevented across all booking channels.

Pricing totals
--------------
  subtotal      = sum(room.room_total for room in self.rooms)
  discount_amt  = % or fixed amount applied to subtotal
  total_amount  = subtotal - discount_amount
  net_total     = total_amount (+ taxes when invoice is created)
"""

from frappe.model.document import Document
from frappe.utils import date_diff, getdate, now_datetime

import frappe
from frappe import _

# ---------------------------------------------------------------------------
# Status constants – centralise string literals to avoid typos
# ---------------------------------------------------------------------------

# Reservation status values (must match field options in hotel_reservation.json)
STATUS_DRAFT      = "Draft"
STATUS_HOLD       = "Hold"
STATUS_CONFIRMED  = "Confirmed"
STATUS_CHECKED_IN = "Checked In"
STATUS_CHECKED_OUT= "Checked Out"
STATUS_CANCELLED  = "Cancelled"
STATUS_NO_SHOW    = "No Show"
STATUS_EXPIRED    = "Expired"

# Valid forward-transition map: maps current status → set of allowed next statuses
# Used by _assert_valid_transition() to prevent illegal state changes.
_ALLOWED_TRANSITIONS = {
    STATUS_DRAFT:       {STATUS_HOLD,       STATUS_CONFIRMED, STATUS_CANCELLED},
    STATUS_HOLD:        {STATUS_CONFIRMED,  STATUS_CHECKED_IN, STATUS_CANCELLED, STATUS_EXPIRED},
    STATUS_CONFIRMED:   {STATUS_CHECKED_IN, STATUS_CANCELLED, STATUS_NO_SHOW},
    STATUS_CHECKED_IN:  {STATUS_CHECKED_OUT, STATUS_CANCELLED},  # CANCELLED requires admin
    STATUS_CHECKED_OUT: set(),          # terminal state
    STATUS_CANCELLED:   set(),          # terminal state
    STATUS_NO_SHOW:     set(),          # terminal state
    STATUS_EXPIRED:     set(),          # terminal state
}

# Statuses where room allocation conflicts must be validated
_CONFLICT_CHECK_STATUSES = {STATUS_HOLD, STATUS_CONFIRMED, STATUS_CHECKED_IN}

# Statuses that mean a room is no longer occupied / unavailable
STATUS_COMPLETED = STATUS_CHECKED_OUT   # alias for readability in queries
_TERMINAL_STATUSES = {STATUS_CANCELLED, STATUS_COMPLETED, STATUS_NO_SHOW, STATUS_EXPIRED}
_DEFAULT_HOLD_HOURS = 1


# ---------------------------------------------------------------------------
# Doctype class
# ---------------------------------------------------------------------------

class HotelReservation(Document):
    """Canonical reservation document – handles the full guest booking lifecycle."""

    # ------------------------------------------------------------------
    # Frappe lifecycle hooks
    # ------------------------------------------------------------------

    def validate(self):
        """
        Run on Save (draft) and on submit.

        Checks performed:
        1. Dates are logically valid (check-out after check-in).
        2. At least one room allocation row exists (relaxed for Group with room_blocks).
        3. No room is double-booked for the given dates (uses centralized utility).
        4. Pricing totals are recalculated from child rows.
        5. Corporate guest is set when reservation_type = Corporate.
        6. Group: either rooms or room_blocks must be present.
        7. House Use / Complimentary: comp_reason is mandatory.
        8. Room block pickup counts are recalculated.
        9. Theoretical revenue is computed for House Use / Complimentary.
        """
        self._assert_valid_transition()
        self._set_hold_expiry()
        self._validate_dates()
        self._validate_rooms_present()
        self._validate_corporate_guest()
        self._validate_house_use_comp()
        self._validate_room_availability()
        self._recalculate_room_totals()
        self._recalculate_totals()
        self._recalculate_block_pickup_counts()
        self._compute_theoretical_revenue()

    def on_submit(self):
        """
        Triggered when the document is submitted (docstatus changes to 1).

        A submitted Hotel Reservation is in a legally-committed state.
        Submission is only meaningful once the reservation reaches Confirmed
        or a later active status.
        """
        if self.reservation_status not in (
            STATUS_CONFIRMED, STATUS_CHECKED_IN, STATUS_CHECKED_OUT
        ):
            frappe.throw(
                _(
                    "Only a Confirmed or later reservation can be submitted. "
                    "Current status: {0}."
                ).format(self.reservation_status)
            )
        self._reserve_rooms()

    def on_cancel(self):
        """
        Triggered on document cancellation (docstatus → 2).

        Forces reservation_status to Cancelled and releases rooms.
        """
        self.reservation_status = STATUS_CANCELLED
        self._release_rooms()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _child_rows(self, fieldname):
        """Return a child-table list while remaining friendly to lightweight tests."""
        getter = getattr(self, "get", None)
        if callable(getter):
            return getter(fieldname) or []
        return getattr(self, fieldname, None) or []

    def _previous_reservation_status(self):
        """Return the reservation status from the previous saved version, if any."""
        get_doc_before_save = getattr(self, "get_doc_before_save", None)
        if not callable(get_doc_before_save):
            return None
        previous = get_doc_before_save()
        return getattr(previous, "reservation_status", None) if previous else None

    def _assert_valid_transition(self):
        """
        Prevent accidental backward or terminal-state transitions.

        New documents are allowed to start in Draft, Hold, or Confirmed because
        front-desk users may directly submit a confirmed booking.
        """
        current = self.reservation_status or STATUS_DRAFT
        previous = self._previous_reservation_status()
        if not previous or previous == current:
            return

        allowed = _ALLOWED_TRANSITIONS.get(previous, set())
        if current not in allowed:
            frappe.throw(
                _("Reservation status cannot move from {0} to {1}.").format(
                    previous, current
                )
            )

    def _set_hold_expiry(self):
        """Stamp hold expiry when a reservation enters Hold."""
        if self.reservation_status == STATUS_HOLD and not self.hold_expires_at:
            self.hold_expires_at = frappe.utils.add_to_date(
                now_datetime(), hours=_DEFAULT_HOLD_HOURS
            )
        elif self.reservation_status in (STATUS_CONFIRMED, STATUS_CHECKED_IN, STATUS_CHECKED_OUT):
            self.hold_expires_at = None

    def _validate_dates(self):
        """Ensure from_date and to_date are present and logically ordered."""
        if not self.from_date or not self.to_date:
            frappe.throw(_("Both Check-In Date and Check-Out Date are required."))

        if getdate(self.to_date) <= getdate(self.from_date):
            frappe.throw(_("Check-Out Date must be after Check-In Date."))

        # Keep number_of_nights in sync
        self.number_of_nights = date_diff(getdate(self.to_date), getdate(self.from_date))

    def _validate_rooms_present(self):
        """
        Ensure at least one room allocation row OR a room block (for Group) has been added.

        Group reservations may be created with only room blocks (no individual rooms
        picked up yet). For all other types, at least one room row is required.
        House Use and Complimentary may also operate with only a room block,
        but in practice they typically have explicit room rows.
        """
        if self.reservation_type == "Group":
            if not self.rooms and not self._child_rows("room_blocks"):
                frappe.throw(
                    _(
                        "Group reservations require at least one Room Allocation or one Room Block. "
                        "Add rooms to the Rooms table or define room blocks."
                    )
                )
        else:
            if not self.rooms:
                frappe.throw(
                    _(
                        "At least one room allocation is required. "
                        "Add a room in the Rooms table."
                    )
                )

    def _validate_corporate_guest(self):
        """
        When reservation_type = Corporate, the corporate_guest link is mandatory.
        For individual reservations, primary_guest_name is mandatory.
        """
        if self.reservation_type == "Corporate" and not self.corporate_guest:
            frappe.throw(
                _(
                    "Corporate reservations require a Corporate Guest. "
                    "Please select the Hotel Guest (type = Corporate)."
                )
            )
        if self.reservation_type == "Individual" and not self.primary_guest_name:
            frappe.throw(_("Primary Guest Name is required for individual reservations."))

    def _validate_house_use_comp(self):
        """
        House Use and Complimentary reservations must have a reason / authorisation.
        This is a hard requirement for audit compliance.
        """
        if self.reservation_type in ("House Use", "Complimentary") and not self.comp_reason:
            frappe.throw(
                _(
                    "A reason and authorisation is required for {0} reservations. "
                    "Please fill in the 'Reason / Authorisation' field."
                ).format(self.reservation_type)
            )

    def _validate_room_availability(self):
        """
        Check each allocated room for conflicts using the centralized utility.

        Delegates to assert_room_available from room_availability.py.
        Skips validation when the reservation is in a terminal status (cancelled,
        checked-out, no-show, expired) because those do not block availability.
        Also skips for STATUS_CHECKED_IN: rooms are already occupied by this
        reservation's own check-ins so re-validating would raise false conflicts
        and risk orphaning check-in documents inside the outer try/except.
        """
        if self.reservation_status in _TERMINAL_STATUSES:
            return
        if self.reservation_status == STATUS_CHECKED_IN:
            return

        from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available

        for row in self.rooms:
            if not row.room_number:
                continue
            # Exclude this reservation's own rows from conflict detection so
            # re-saving an existing confirmed reservation does not self-conflict.
            assert_room_available(
                row.room_number,
                self.from_date,
                self.to_date,
                exclude_reservation=self.name,   # legacy Hotel Room Reservation exclusion
                exclude_canonical=self.name,      # canonical Hotel Reservation exclusion
                reservation_type=self.reservation_type,  # pass type for block-guard bypass
            )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    def _recalculate_room_totals(self):
        """
        Compute room_total and sync number_of_nights for each child row.

        rate_per_night * number_of_nights - row-level discount = room_total.
        Also snapshots the rate code's meal_plan and cancellation_policy onto the row
        when a rate_code is linked.
        This must run before _recalculate_totals() which sums room_total values.
        """
        nights = date_diff(getdate(self.to_date), getdate(self.from_date)) if self.from_date and self.to_date else 0
        for row in self.rooms:
            row.number_of_nights = nights
            rate = float(row.rate_per_night or 0)
            row_discount = float(row.discount or 0)
            row.room_total = round(rate * nights - row_discount, 2)
            # Snapshot rate plan details when a rate_code is linked
            if row.rate_code:
                try:
                    rate_doc = frappe.get_cached_doc("Hotel Room Rate", row.rate_code)
                    if not row.meal_plan_snapshot:
                        row.meal_plan_snapshot = rate_doc.meal_plan or ""
                    if not row.cancellation_policy_snapshot:
                        row.cancellation_policy_snapshot = rate_doc.cancellation_policy or ""
                    if not row.rate_type:
                        row.rate_type = rate_doc.rate_type or ""
                except Exception:
                    pass

    def _recalculate_totals(self):
        """
        Derive pricing totals from child room allocation rows.

        subtotal     = Σ row.room_total
        discount_amt = % or fixed deduction
        total_amount = subtotal - discount_amount
        net_total    = total_amount (taxes applied by the Sales Invoice)
        """
        subtotal = sum(row.room_total or 0.0 for row in self.rooms)
        self.subtotal = subtotal

        if self.discount_type == "Percentage":
            pct = min(max(float(self.discount or 0), 0), 100)
            self.discount_amount = round(subtotal * pct / 100, 2)
        elif self.discount_type == "Fixed Amount":
            self.discount_amount = min(float(self.discount or 0), subtotal)
        else:
            self.discount_amount = 0.0

        self.total_amount = round(subtotal - self.discount_amount, 2)
        # net_total is kept equal to total_amount until an invoice applies taxes
        self.net_total = self.total_amount

    def _recalculate_block_pickup_counts(self):
        """
        For Group reservations, compute picked_up and remaining for each room_block row.

        picked_up  = count of rooms rows whose room_type matches the block's room_type.
        remaining  = quantity - picked_up (floor at 0).
        """
        if self.reservation_type != "Group":
            return
        for block in self._child_rows("room_blocks"):
            picked = sum(
                1 for r in self.rooms if r.room_type == block.room_type
            )
            block.picked_up = picked
            block.remaining = max(int(block.quantity or 0) - picked, 0)

    def _compute_theoretical_revenue(self):
        """
        For House Use and Complimentary reservations, compute theoretical_room_revenue
        using the standard rack tariff for each allocated room.

        No actual revenue is recognised; this is for RevPAR and occupancy reporting.
        """
        if self.reservation_type not in ("House Use", "Complimentary"):
            return

        from rhohotel.api import get_room_rate
        nights = int(self.number_of_nights or 0)
        if nights <= 0 or not self.rooms:
            self.theoretical_room_revenue = 0.0
            return

        total = 0.0
        for row in self.rooms:
            if not row.room_type:
                continue
            rack_rate = get_room_rate(row.room_type, check_in_date=str(self.from_date)) or 0.0
            total += float(rack_rate) * nights

        self.theoretical_room_revenue = round(total, 2)

    # ------------------------------------------------------------------
    # Room state management
    # ------------------------------------------------------------------

    def _reserve_rooms(self):
        """Mark explicitly allocated rooms as Reserved once the reservation is submitted."""
        if self.reservation_status not in (STATUS_CONFIRMED, STATUS_CHECKED_IN):
            return
        for row in self.rooms:
            if not row.room_number:
                continue
            room = frappe.get_doc("Hotel Room", row.room_number)
            if room.status == "Vacant":
                room.status = "Reserved"
                room.save(ignore_permissions=True)

    def _release_rooms(self):
        """
        Mark each allocated room as Vacant when the reservation is cancelled
        or expired, unless a different active booking is now occupying the room.

        Only rooms that are currently in Reserved status (set by this reservation)
        are updated; Occupied rooms (i.e. an active check-in is live) are left alone.
        Also resets block pickup counts so inventory is cleanly returned.
        """
        for row in self.rooms:
            if not row.room_number:
                continue
            room = frappe.get_doc("Hotel Room", row.room_number)
            if room.status == "Reserved":
                room.status = "Vacant"
                room.save(ignore_permissions=True)

        # Reset block pickup/remaining counts so freed inventory is visible
        for block in self._child_rows("room_blocks"):
            block.picked_up = 0
            block.remaining = int(block.quantity or 0)


@frappe.whitelist()
def adjust_reservation(
    reservation_name,
    new_checkout,
    new_check_in,
    new_discount_type=None,
    new_discount=None,
):
    """
    Adjust the arrival and/or departure dates of a submitted Hotel Reservation.
    Recalculates nights and totals; saves the document in-place.
    """
    from frappe.utils import getdate, date_diff, flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    new_from = getdate(new_check_in)
    new_to = getdate(new_checkout)

    if new_to <= new_from:
        frappe.throw("Departure date must be after arrival date.")

    current_from = getdate(doc.from_date)
    current_to = getdate(doc.to_date)

    if new_from == current_from and new_to == current_to:
        frappe.throw("No change detected – dates are the same as the current stay.")

    new_nights = date_diff(new_to, new_from)
    if new_nights < 1:
        new_nights = 1

    doc.flags.ignore_validate_update_after_submit = True
    doc.from_date = new_from
    doc.to_date = new_to
    doc.number_of_nights = new_nights


    # Allow discount to be changed during stay adjustment if provided
    if new_discount_type is not None:
        doc.discount_type = new_discount_type
    if new_discount is not None:
        doc.discount = new_discount

    # Recalculate per-room totals and reservation totals using the new night count
    doc._recalculate_room_totals()
    doc._recalculate_totals()
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "new_from_date": str(new_from),
        "new_to_date": str(new_to),
        "new_nights": new_nights,
        "discount_type": doc.discount_type,
        "discount": flt(doc.discount),
        "discount_amount": flt(doc.discount_amount),
        "total_amount": flt(doc.total_amount),
    }


@frappe.whitelist()
def change_room_in_reservation(reservation_name, old_room_number, new_room_number, reason=None):
    """
    Swap a room row in a submitted Hotel Reservation.
    Validates the new room is not already reserved for the same period.
    """
    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    # Find the row to replace
    target_row = None
    for row in doc.rooms:
        if row.room_number == old_room_number:
            target_row = row
            break

    if not target_row:
        frappe.throw(f"Room {old_room_number} is not part of this reservation.")

    if old_room_number == new_room_number:
        frappe.throw("New room is the same as the current room.")

    # Fetch new room details
    new_room = frappe.get_doc("Hotel Room", new_room_number)

    doc.flags.ignore_validate_update_after_submit = True

    # Update the room row
    target_row.room_number = new_room_number
    target_row.room_type = new_room.room_type or target_row.room_type
    from rhohotel.api import get_room_rate
    target_row.rate_per_night = get_room_rate(
        new_room.room_type,
        rate_type=target_row.rate_code or None,
        check_in_date=str(doc.from_date),
    )
    target_row.room_total = round(float(target_row.rate_per_night or 0) * float(doc.number_of_nights or 0), 2)

    # Check if this room row has an active check-in
    linked_check_in = frappe.db.get_value(
        "Hotel Room Check In",
        {
            "canonical_reservation": reservation_name,
            "room_number": old_room_number,
            "status": ["in", ["Checked In", "Draft"]],
        },
        ["name", "docstatus"],
        as_dict=True,
    )
    is_checked_in = bool(linked_check_in)

    # Update the old room status back to Vacant
    try:
        old_room = frappe.get_doc("Hotel Room", old_room_number)
        if old_room.status in ("Reserved", "Occupied"):
            old_room.status = "Vacant"
            old_room.save(ignore_permissions=True)
    except Exception:
        pass

    # Mark new room as Occupied (if guest is transferring mid-stay) or Reserved
    new_room.status = "Occupied" if is_checked_in else "Reserved"
    new_room.save(ignore_permissions=True)

    # Sync the linked check-in document to reflect the new room
    if linked_check_in:
        frappe.db.set_value(
            "Hotel Room Check In",
            linked_check_in.name,
            {
                "room_number": new_room_number,
                "room_type": new_room.room_type or target_row.room_type,
                "rate_amount": target_row.rate_per_night,
            },
            update_modified=True,
        )

    doc._recalculate_totals()
    doc.save(ignore_permissions=True)

    adjustment = None
    linked_invoice_names = [
        name for name in [doc.sales_invoice] if name
    ] + [
        row.invoice for row in (doc.get("reservation_invoices") or []) if row.invoice
    ]

    has_submitted_invoice = any(
        frappe.db.get_value(
            "Sales Invoice",
            {"name": invoice_name, "docstatus": 1},
            "name",
        )
        for invoice_name in set(linked_invoice_names)
    )

    # Adjustment invoice/credit note is created only when reservation already has invoice(s).
    if has_submitted_invoice:
        adjustment = adjust_invoice_for_reservation(reservation_name)

    frappe.db.commit()

    return {
        "status": "success",
        "new_room": new_room_number,
        "invoice_adjustment": adjustment,
    }


@frappe.whitelist()
def check_in_reservation_room(reservation_name, room_row_name):
    """
    Check in a single room row in a reservation.
    Creates a Hotel Room Check In document so the check-in appears in the list.
    Returns a summary for frontend notification.
    """
    from frappe.utils import add_days, cint, flt, get_datetime
    from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    row = next((r for r in doc.rooms if r.name == room_row_name), None)
    if not row:
        return {"status": "error", "message": f"Room row not found: {room_row_name}"}
    if getattr(row, 'status', None) == STATUS_CHECKED_IN or row.check_in_reference:
        return {"status": "success", "message": f"Room {row.room_number} already checked in.",
                "check_in_reference": row.check_in_reference}

    try:
        ci_dt = now_datetime()
        nights = cint(row.number_of_nights or doc.number_of_nights or 1)
        expected_out = add_days(get_datetime(ci_dt), nights)

        existing_ci = frappe.db.get_value(
            "Hotel Room Check In",
            {
                "canonical_reservation": reservation_name,
                "room_number": row.room_number,
                "status": ["in", ["Draft", "Checked In"]],
            },
            "name",
        )
        if existing_ci:
            frappe.db.set_value(
                "Hotel Reservation Room",
                row.name,
                "check_in_reference",
                existing_ci,
                update_modified=False,
            )
            frappe.clear_document_cache("Hotel Reservation", reservation_name)
            frappe.db.commit()
            return {
                "status": "success",
                "message": f"Room {row.room_number} already checked in.",
                "check_in_reference": existing_ci,
            }

        # Resolve guest: prefer per-room guest, then occupant/guest name lookup, then primary guest.
        guest = row.hotel_guest or None
        if not guest and (row.occupant_name or row.guest_name):
            guest = frappe.db.get_value(
                "Hotel Guest",
                {"hotel_guest_name": row.occupant_name or row.guest_name},
                "name",
            )
        if not guest and doc.primary_guest_name:
            guest = frappe.db.get_value(
                "Hotel Guest",
                {"hotel_guest_name": doc.primary_guest_name},
                "name",
            )
        if not guest:
            return {"status": "error", "message": "No guest linked to this room row. Please assign a guest first."}

        # Use the centralised availability guard from room_availability.py.
        # assert_room_available raises frappe.ValidationError on conflict,
        # which propagates to the outer except block as a clean error response.
        assert_room_available(
            row.room_number,
            ci_dt,
            expected_out,
            exclude_canonical=reservation_name,
            reservation_type=doc.reservation_type,
        )

        ci_doc = frappe.new_doc("Hotel Room Check In")
        ci_doc.guest = guest
        ci_doc.room_number = row.room_number
        ci_doc.room_type = row.room_type or ""
        ci_doc.rate_amount = flt(row.rate_per_night or 0)
        ci_doc.number_of_nights = nights
        ci_doc.check_in_datetime = ci_dt
        ci_doc.expected_check_out_datetime = expected_out
        ci_doc.reservation = reservation_name
        ci_doc.canonical_reservation = reservation_name
        _source = doc.source_channel or ""
        ci_doc.reservation_source = _source if (_source and frappe.db.exists("Market Place", _source)) else "Reservation"
        ci_doc.discount_type = doc.discount_type or "None"
        ci_doc.discount = flt(doc.discount or 0)
        ci_doc.flags.skip_availability_check = True
        ci_doc.insert(ignore_permissions=True)
        ci_doc.submit()

        frappe.db.set_value(
            "Hotel Reservation Room",
            row.name,
            "check_in_reference",
            ci_doc.name,
            update_modified=False,
        )
        # Update reservation-level status atomically without loading the full doc
        current_res_status = frappe.db.get_value("Hotel Reservation", reservation_name, "reservation_status")
        if current_res_status not in (STATUS_CHECKED_IN, STATUS_CHECKED_OUT):
            frappe.db.set_value(
                "Hotel Reservation",
                reservation_name,
                {"reservation_status": STATUS_CHECKED_IN, "check_in_time": ci_dt},
                update_modified=False,
            )
        frappe.clear_document_cache("Hotel Reservation", reservation_name)
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Checked in room {row.room_number}.",
            "check_in_reference": ci_doc.name,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_in_reservation_room failed")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def bulk_check_in_reservation(reservation_name):
    """
    Bulk check-in all pending rooms in a reservation.
    Creates a Hotel Room Check In document per room so they appear in the list.
    Returns a summary for frontend notification.
    """
    from frappe.utils import add_days, cint, flt, get_datetime
    from rhohotel.rhocom_hotel.utils.room_availability import assert_room_available

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    if doc.reservation_status not in (STATUS_CONFIRMED, STATUS_HOLD):
        return {
            "status": "error",
            "message": f"Reservation is not in a check-in eligible state: {doc.reservation_status}"
        }

    checked_in_count = 0
    already_checked_in = 0
    errors = []
    ci_dt = now_datetime()

    for row in doc.rooms:
        room_label = getattr(row, 'room_number', '?')
        try:
            if row.status == STATUS_CHECKED_IN or row.check_in_reference:
                already_checked_in += 1
                continue

            nights = cint(row.number_of_nights or doc.number_of_nights or 1)
            expected_out = add_days(get_datetime(ci_dt), nights)

            # Resolve guest: prefer per-room guest, then occupant/guest name lookup, then primary guest.
            guest = row.hotel_guest or None
            if not guest and (row.occupant_name or row.guest_name):
                guest = frappe.db.get_value(
                    "Hotel Guest",
                    {"hotel_guest_name": row.occupant_name or row.guest_name},
                    "name",
                )
            if not guest and doc.primary_guest_name:
                guest = frappe.db.get_value(
                    "Hotel Guest",
                    {"hotel_guest_name": doc.primary_guest_name},
                    "name",
                )
            if not guest:
                errors.append(f"Room {room_label}: no guest assigned, skipped.")
                continue

            existing_ci = frappe.db.get_value(
                "Hotel Room Check In",
                {
                    "canonical_reservation": reservation_name,
                    "room_number": row.room_number,
                    "status": ["in", ["Draft", "Checked In"]],
                },
                "name",
            )
            if existing_ci:
                row.status = STATUS_CHECKED_IN
                row.check_in_time = ci_dt
                row.check_in_reference = existing_ci
                already_checked_in += 1
                continue

            # Use the centralised availability guard from room_availability.py.
            try:
                assert_room_available(
                    row.room_number,
                    ci_dt,
                    expected_out,
                    exclude_canonical=reservation_name,
                    reservation_type=doc.reservation_type,
                )
            except frappe.ValidationError as avail_err:
                errors.append(f"Room {room_label}: {str(avail_err)}")
                continue

            ci_doc = frappe.new_doc("Hotel Room Check In")
            ci_doc.guest = guest
            ci_doc.room_number = row.room_number
            ci_doc.room_type = row.room_type or ""

            # Resolve rate: use per-room rate, fall back to active tariff
            rate_amount = flt(row.rate_per_night or 0)
            if not rate_amount:
                tariff = frappe.get_all(
                    "Hotel Room Tariff",
                    filters={"room_type": row.room_type or "", "is_active": 1},
                    fields=["rate_amount"],
                    limit=1,
                )
                if tariff:
                    rate_amount = flt(tariff[0].rate_amount)
            ci_doc.rate_amount = rate_amount

            ci_doc.number_of_nights = nights
            ci_doc.check_in_datetime = ci_dt
            ci_doc.expected_check_out_datetime = expected_out
            ci_doc.reservation = reservation_name
            ci_doc.canonical_reservation = reservation_name
            _source = doc.source_channel or ""
            ci_doc.reservation_source = _source if (_source and frappe.db.exists("Market Place", _source)) else "Reservation"
            ci_doc.discount_type = doc.discount_type or "None"
            ci_doc.discount = flt(doc.discount or 0)
            ci_doc.flags.skip_availability_check = True

            try:
                ci_doc.insert(ignore_permissions=True)
            except Exception as insert_exc:
                frappe.log_error(frappe.get_traceback(), f"bulk_check_in insert: room {room_label}")
                errors.append(f"Room {room_label}: {str(insert_exc)}")
                continue

            try:
                ci_doc.submit()
            except Exception as submit_exc:
                frappe.log_error(frappe.get_traceback(), f"bulk_check_in submit: room {room_label}")
                # Clean up orphaned draft so it does not clutter the database
                try:
                    frappe.delete_doc("Hotel Room Check In", ci_doc.name, force=True, ignore_permissions=True)
                except Exception:
                    pass
                errors.append(f"Room {room_label}: {str(submit_exc)}")
                continue

            row.check_in_reference = ci_doc.name
            checked_in_count += 1
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"bulk_check_in: room {room_label}")
            errors.append(f"Room {room_label}: {str(e)}")

    if checked_in_count > 0:
        doc.reservation_status = STATUS_CHECKED_IN
        doc.check_in_time = ci_dt
        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)
        frappe.clear_document_cache("Hotel Reservation", reservation_name)
        frappe.db.commit()

    return {
        "status": "success",
        "checked_in": checked_in_count,
        "already_checked_in": already_checked_in,
        "errors": errors,
        "message": (
            f"Checked in {checked_in_count} room(s)."
            + (f" {already_checked_in} already checked in." if already_checked_in else "")
            + (f" {len(errors)} error(s)." if errors else "")
        ) if checked_in_count > 0 else (
            ("No rooms checked in. " + "; ".join(errors)) if errors
            else (f"All {already_checked_in} room(s) already checked in." if already_checked_in
                  else "No rooms checked in.")
        )
    }


def _find_or_create_customer_for_reservation(doc):
    if doc.customer:
        return doc.customer

    customer = frappe.db.get_value(
        "Customer",
        {"customer_name": ["like", f"{doc.primary_guest_name or ''}%"]},
        "name",
    )
    if customer:
        doc.db_set("customer", customer, update_modified=False)
        return customer

    selling_settings = frappe.get_cached_doc("Selling Settings")
    customer_doc = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": doc.primary_guest_name or doc.corporate_guest or doc.name,
            "customer_type": "Company" if doc.reservation_type == "Corporate" else "Individual",
            "customer_group": selling_settings.default_customer_group,
            "territory": selling_settings.default_territory,
            "mobile_number": doc.primary_guest_phone or "",
            "email_id": doc.primary_guest_email or "",
        }
    )
    customer_doc.insert(ignore_permissions=True)
    doc.db_set("customer", customer_doc.name, update_modified=False)
    return customer_doc.name


def _upsert_reservation_invoice_row(doc, invoice_name, invoice_type=None):
    """Upsert a child row in reservation_invoices for a Sales Invoice."""
    if not invoice_name:
        return False

    invoice = frappe.db.get_value(
        "Sales Invoice",
        invoice_name,
        ["name", "posting_date", "grand_total", "outstanding_amount", "status", "is_return"],
        as_dict=True,
    )
    if not invoice:
        return False

    ledger = doc.get("reservation_invoices") or []
    existing = next((row for row in ledger if row.invoice == invoice.name), None)
    row_payload = {
        "invoice": invoice.name,
        "invoice_type": invoice_type or ("Credit Note" if int(invoice.is_return or 0) else "Invoice"),
        "is_return": int(invoice.is_return or 0),
        "posting_date": invoice.posting_date,
        "amount": invoice.grand_total,
        "outstanding_amount": invoice.outstanding_amount,
        "status": invoice.status,
    }

    if existing:
        changed = False
        for key, value in row_payload.items():
            if existing.get(key) != value:
                existing.set(key, value)
                changed = True
        return changed
    else:
        doc.append("reservation_invoices", row_payload)
        return True


def _upsert_reservation_payment_row(doc, payment_entry_name, amount=None):
    """Upsert a child row in reservation_payments for a Payment Entry."""
    if not payment_entry_name:
        return False

    payment = frappe.db.get_value(
        "Payment Entry",
        {"name": payment_entry_name, "docstatus": 1, "payment_type": "Receive"},
        ["name", "posting_date", "mode_of_payment", "reference_no", "remarks", "paid_amount"],
        as_dict=True,
    )
    if not payment:
        return False

    ledger = doc.get("reservation_payments") or []
    existing = next((row for row in ledger if row.payment_entry == payment.name), None)
    row_payload = {
        "payment_entry": payment.name,
        "posting_date": payment.posting_date,
        "mode_of_payment": payment.mode_of_payment,
        "reference_no": payment.reference_no,
        "amount": amount if amount is not None else payment.paid_amount,
        "remarks": payment.remarks,
    }

    if existing:
        changed = False
        for key, value in row_payload.items():
            if existing.get(key) != value:
                existing.set(key, value)
                changed = True
        return changed
    else:
        doc.append("reservation_payments", row_payload)
        return True


def _persist_reservation_ledger_updates(doc):
    """Persist child ledger updates on submitted/draft reservation safely."""
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)


def _get_open_invoice_for_payment(doc):
    """Return an outstanding invoice doc suitable for receiving payment."""
    invoice_names = _get_reservation_invoice_names(doc)
    if not invoice_names:
        return None

    outstanding_rows = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", invoice_names], "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name"],
        order_by="posting_date asc, creation asc",
        limit=1,
    )
    if not outstanding_rows:
        return None
    return frappe.get_doc("Sales Invoice", outstanding_rows[0].name)


@frappe.whitelist()
def create_invoice_for_reservation(reservation_name):
    from frappe.utils import getdate, flt
    from rhohotel.rhocom_hotel.utils.billing_routing import resolve_payer

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    if _is_group_split_billing(doc):
        frappe.throw(
            _(
                "Group Split billing requires per-room invoicing. "
                "Use 'Create Invoice' on each room row instead of the top-level invoice action."
            )
        )

    if doc.sales_invoice:
        updated = _upsert_reservation_invoice_row(doc, doc.sales_invoice, invoice_type="Primary")
        if updated:
            _persist_reservation_ledger_updates(doc)
            frappe.db.commit()
        return {"sales_invoice": doc.sales_invoice, "already_exists": True}

    if not doc.rooms:
        frappe.throw(_("Cannot create invoice without reserved rooms."))

    payer_info = resolve_payer(reservation_name, charge_category="Room")
    if payer_info.get("payer_type") == "Internal (Cost Centre)":
        doc.flags.ignore_validate_update_after_submit = True
        doc.payment_status = "Paid"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"sales_invoice": None, "internal": True, "payer_type": payer_info.get("payer_type")}

    customer = payer_info.get("customer") or _find_or_create_customer_for_reservation(doc)
    if not customer:
        frappe.throw(_("Cannot create invoice: no customer could be resolved for this reservation."))

    items = []
    for room in doc.rooms:
        room_number = room.room_number
        item_code = frappe.db.get_value("Hotel Room", room_number, "erpnext_item") or room_number
        if not frappe.db.exists("Item", item_code):
            frappe.throw(_("No billable Item found for room {0}. Configure Hotel Room.erpnext_item.").format(room_number))
        items.append(
            {
                "item_code": item_code,
                "qty": 1,
                "rate": flt(room.room_total or 0),
                "description": _("Reservation charge for {0}, room {1} ({2} night(s), {3} to {4})").format(
                    doc.name,
                    room_number,
                    room.number_of_nights or doc.number_of_nights or 0,
                    doc.from_date,
                    doc.to_date,
                ),
            }
        )

    si = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "customer": customer,
            "posting_date": frappe.utils.today(),
            "due_date": getdate(doc.to_date),
            "update_stock": 0,
            "items": items,
        }
    )
    si.set_taxes()
    if doc.discount_amount:
        if doc.discount_type == "Percentage":
            si.additional_discount_percentage = flt(doc.discount or 0)
        else:
            si.discount_amount = flt(doc.discount_amount)
    si.insert(ignore_permissions=True)
    si.submit()

    doc.flags.ignore_validate_update_after_submit = True
    doc.sales_invoice = si.name
    doc.payment_status = "Pending"
    doc.net_total = flt(si.grand_total)
    _upsert_reservation_invoice_row(doc, si.name, invoice_type="Primary")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"sales_invoice": si.name}


def _get_reservation_invoice_names(doc):
    invoice_names = []

    for row in doc.get("reservation_invoices") or []:
        if row.invoice:
            invoice_names.append(row.invoice)

    if doc.sales_invoice:
        invoice_names.append(doc.sales_invoice)

    try:
        adjustment_rows = frappe.db.sql(
            """
            SELECT DISTINCT si.name
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE si.docstatus = 1
              AND sii.description LIKE %s
            """,
            (f"%reservation {doc.name}%",),
            as_dict=True,
        )
        invoice_names.extend(row.name for row in adjustment_rows)
    except Exception:
        pass

    return list(dict.fromkeys([name for name in invoice_names if name]))


@frappe.whitelist()
def get_payment_summary_for_reservation(reservation_name):
    """Return paid amount, balance, invoices and payment entries from submitted ledger docs."""
    from frappe.utils import flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoice_names = _get_reservation_invoice_names(doc)
    invoices = []

    if invoice_names:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", invoice_names], "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "status", "is_return"],
            order_by="posting_date asc",
        )

    invoice_total = sum(flt(inv.grand_total) for inv in invoices)
    outstanding_total = sum(flt(inv.outstanding_amount) for inv in invoices)

    payments = []
    if invoice_names:
        payments = frappe.db.sql(
            """
            SELECT
                pe.name,
                pe.posting_date,
                pe.mode_of_payment,
                pe.reference_no,
                pe.remarks,
                SUM(per.allocated_amount) AS amount,
                MAX(pe.creation) AS created_at
            FROM `tabPayment Entry Reference` per
            INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE pe.docstatus = 1
              AND pe.payment_type = 'Receive'
              AND per.reference_doctype = 'Sales Invoice'
              AND per.reference_name IN %(invoice_names)s
            GROUP BY pe.name, pe.posting_date, pe.mode_of_payment, pe.reference_no, pe.remarks
            ORDER BY pe.posting_date DESC, created_at DESC
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        )

    if doc.payment_entry and not any(row.name == doc.payment_entry for row in payments):
        payment = frappe.db.get_value(
            "Payment Entry",
            {"name": doc.payment_entry, "docstatus": 1, "payment_type": "Receive"},
            ["name", "posting_date", "mode_of_payment", "reference_no", "remarks", "paid_amount"],
            as_dict=True,
        )
        if payment:
            payment["amount"] = flt(payment.pop("paid_amount", 0))
            payments.append(payment)

    ledger_changed = False
    for invoice in invoices:
        row_type = "Credit Note" if int(invoice.get("is_return") or 0) else "Invoice"
        ledger_changed = _upsert_reservation_invoice_row(doc, invoice.name, row_type) or ledger_changed
    for payment in payments:
        ledger_changed = _upsert_reservation_payment_row(doc, payment.name, amount=flt(payment.amount or 0)) or ledger_changed

    if ledger_changed:
        _persist_reservation_ledger_updates(doc)
        frappe.db.commit()

    paid_amount = sum(flt(payment.amount) for payment in payments)
    reservation_total = flt(doc.net_total or doc.total_amount or 0)
    balance = outstanding_total if invoices else max(0, reservation_total - paid_amount)

    return {
        "paid_amount": paid_amount,
        "balance": max(0, flt(balance)),
        "invoice_total": invoice_total,
        "outstanding_amount": outstanding_total,
        "invoices": invoices,
        "payment_entries": payments,
    }


@frappe.whitelist()
def get_outstanding_invoices_for_reservation(reservation_name):
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoices = []

    for invoice_name in _get_reservation_invoice_names(doc):
        inv = frappe.db.get_value(
            "Sales Invoice",
            invoice_name,
            ["name", "posting_date", "grand_total", "outstanding_amount"],
            as_dict=True,
        )
        if inv and float(inv.get("outstanding_amount") or 0) > 0:
            invoices.append(inv)

    return invoices


@frappe.whitelist()
def adjust_invoice_for_reservation(reservation_name):
    """
    Reconcile the linked Sales Invoice after a stay adjustment.

    Rules:
    - Compute net billed amount across all linked submitted invoices.
    - If new reservation total is higher, create a positive adjustment invoice.
    - If new reservation total is lower, create a credit note.
    """
    from frappe.utils import flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    source_invoice_name = doc.sales_invoice
    if not source_invoice_name:
        invoice_names = _get_reservation_invoice_names(doc)
        if invoice_names:
            source_invoice_name = invoice_names[0]

    if not source_invoice_name:
        return {"status": "no_invoice", "message": "No invoice linked to this reservation."}

    source_invoice = frappe.get_doc("Sales Invoice", source_invoice_name)
    if int(source_invoice.docstatus) != 1:
        doc.flags.ignore_validate_update_after_submit = True
        doc.sales_invoice = None
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        recreate = create_invoice_for_reservation(reservation_name)
        return {
            "status": "recreated",
            "sales_invoice": recreate.get("sales_invoice"),
            "message": "Linked invoice was not submitted. Recreated the main reservation invoice.",
        }

    invoice_names = _get_reservation_invoice_names(doc)
    invoices = []
    if invoice_names:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", invoice_names], "docstatus": 1},
            fields=["name", "grand_total", "is_return"],
        )

    billed_total = flt(sum(flt(inv.grand_total) for inv in invoices))
    new_total = flt(doc.total_amount or doc.net_total or 0)
    difference = flt(new_total - billed_total)

    if abs(difference) < 0.01:
        return {
            "status": "no_change",
            "message": "Invoice total already matches reservation total.",
            "billed_total": billed_total,
        }

    customer = source_invoice.customer
    if not customer:
        frappe.throw(_("Cannot create adjustment invoice: no customer on existing invoice."))

    item_code = None
    for room in doc.rooms:
        candidate = frappe.db.get_value("Hotel Room", room.room_number, "erpnext_item") or room.room_number
        if frappe.db.exists("Item", candidate):
            item_code = candidate
            break

    if not item_code:
        frappe.throw(_("Cannot create adjustment invoice: no valid Item found for this reservation's rooms."))

    invoice_data = {
        "doctype": "Sales Invoice",
        "customer": customer,
        "company": source_invoice.company,
        "posting_date": frappe.utils.today(),
        "due_date": frappe.utils.today(),
        "update_stock": 0,
    }

    if difference > 0:
        invoice_data["is_return"] = 0
        invoice_data["items"] = [
            {
                "item_code": item_code,
                "qty": 1,
                "rate": flt(abs(difference)),
                "description": _(
                    "Stay extension charge for reservation {0} ({1} to {2}, {3} night(s))."
                ).format(doc.name, doc.from_date, doc.to_date, doc.number_of_nights),
            }
        ]
    else:
        invoice_data["is_return"] = 1
        invoice_data["return_against"] = source_invoice.name
        invoice_data["update_outstanding_for_self"] = 1
        if getattr(source_invoice, "debit_to", None):
            invoice_data["debit_to"] = source_invoice.debit_to
        invoice_data["items"] = [
            {
                "item_code": item_code,
                "qty": -1,
                "rate": flt(abs(difference)),
                "description": _(
                    "Stay reduction credit for reservation {0} ({1} to {2}, {3} night(s))."
                ).format(doc.name, doc.from_date, doc.to_date, doc.number_of_nights),
            }
        ]

    adjustment_doc = frappe.get_doc(invoice_data)
    adjustment_doc.set_taxes()
    adjustment_doc.insert(ignore_permissions=True)
    adjustment_doc.submit()

    # Update net_total on reservation to reflect new combined total
    doc.flags.ignore_validate_update_after_submit = True
    doc.net_total = flt(doc.total_amount)
    _upsert_reservation_invoice_row(
        doc,
        adjustment_doc.name,
        invoice_type="Credit Note" if int(adjustment_doc.is_return or 0) else "Adjustment",
    )
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    if difference > 0:
        return {
            "status": "adjustment_created",
            "original_invoice": source_invoice.name,
            "adjustment_invoice": adjustment_doc.name,
            "difference": flt(difference),
            "billed_total_before": billed_total,
        }

    return {
        "status": "credit_note_created",
        "original_invoice": source_invoice.name,
        "credit_note": adjustment_doc.name,
        "difference": flt(difference),
        "billed_total_before": billed_total,
    }


@frappe.whitelist()
def create_invoice_for_reservation_room(reservation_name, room_row_name):
    """
    Create a Sales Invoice for a single room row in a Split billing Group reservation.
    Each room occupant gets their own invoice billed to that guest's customer.
    """
    from frappe.utils import getdate, flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    if not _is_group_split_billing(doc):
        frappe.throw(_("Per-room invoicing is only available for Group reservations with Split billing mode."))

    room_row = next((r for r in doc.rooms if r.name == room_row_name), None)
    if not room_row:
        frappe.throw(_("Room row {0} not found in reservation {1}.").format(room_row_name, reservation_name))

    if room_row.split_invoice:
        return {"sales_invoice": room_row.split_invoice, "already_exists": True}

    # Resolve customer: prefer hotel_guest link → occupant name lookup → reservation fallback
    customer = None
    if room_row.hotel_guest:
        customer = frappe.db.get_value("Hotel Guest", room_row.hotel_guest, "customer")

    if not customer:
        guest_name = room_row.occupant_name or room_row.guest_name or ""
        if guest_name:
            existing_guest = frappe.db.get_value(
                "Hotel Guest", {"hotel_guest_name": guest_name}, "name"
            )
            if existing_guest:
                customer = frappe.db.get_value("Hotel Guest", existing_guest, "customer")

    if not customer:
        customer = doc.customer or _find_or_create_customer_for_reservation(doc)

    if not customer:
        frappe.throw(_("Cannot create invoice: no customer resolved for room {0}. Assign a guest to this room first.").format(room_row.room_number))

    room_number = room_row.room_number
    item_code = frappe.db.get_value("Hotel Room", room_number, "erpnext_item") or room_number
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("No billable Item found for room {0}. Configure Hotel Room.erpnext_item.").format(room_number))

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "posting_date": frappe.utils.today(),
        "due_date": getdate(doc.to_date),
        "update_stock": 0,
        "items": [{
            "item_code": item_code,
            "qty": 1,
            "rate": flt(room_row.room_total or 0),
            "description": _("Reservation charge for {0}, room {1} ({2} night(s), {3} to {4})").format(
                doc.name, room_number, room_row.number_of_nights or doc.number_of_nights or 0,
                doc.from_date, doc.to_date,
            ),
        }],
    })
    si.set_taxes()
    si.insert(ignore_permissions=True)
    si.submit()

    # Persist invoice reference on the room row.
    # Update both the in-memory row AND the DB so doc.save() does not overwrite
    # the value back to None when it serialises the child table.
    room_row.split_invoice = si.name
    frappe.db.set_value("Hotel Reservation Room", room_row_name, "split_invoice", si.name)

    # Add to reservation invoice ledger
    doc.flags.ignore_validate_update_after_submit = True
    _upsert_reservation_invoice_row(doc, si.name, invoice_type="Split")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"sales_invoice": si.name}


def _is_group_split_billing(doc):
    reservation_type = (doc.reservation_type or "").strip().lower()
    billing_mode = (doc.group_billing_mode or "").strip().lower()
    return reservation_type == "group" and billing_mode.startswith("split")


@frappe.whitelist()
def create_pending_split_invoices(reservation_name):
    """Create invoices only for split-group room rows that do not yet have split_invoice."""
    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    if not _is_group_split_billing(doc):
        frappe.throw(_("Bulk split invoicing is only available for Group reservations with Split billing mode."))

    pending_rows = [row for row in (doc.rooms or []) if not row.split_invoice]
    if not pending_rows:
        return {
            "status": "no_pending_rooms",
            "created_count": 0,
            "already_invoiced_count": len(doc.rooms or []),
            "created": [],
            "failed": [],
        }

    created = []
    failed = []

    for row in pending_rows:
        try:
            result = create_invoice_for_reservation_room(reservation_name, row.name)
            created.append(
                {
                    "room_row_name": row.name,
                    "room_number": row.room_number,
                    "sales_invoice": result.get("sales_invoice"),
                }
            )
        except Exception as exc:
            failed.append(
                {
                    "room_row_name": row.name,
                    "room_number": row.room_number,
                    "error": str(exc),
                }
            )

    status = "success"
    if failed and created:
        status = "partial"
    elif failed and not created:
        status = "failed"

    return {
        "status": status,
        "created_count": len(created),
        "already_invoiced_count": len(doc.rooms or []) - len(pending_rows),
        "pending_count": len(pending_rows),
        "failed_count": len(failed),
        "created": created,
        "failed": failed,
    }


@frappe.whitelist()
def collect_payment_for_reservation(reservation_name, payment_info=None):
    import json

    if payment_info and isinstance(payment_info, str):
        payment_info = json.loads(payment_info)
    payment_info = payment_info or {}

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    # Collect ALL outstanding invoices, ordered oldest first
    invoice_names = _get_reservation_invoice_names(doc)
    if not invoice_names:
        frappe.throw(_("No outstanding Sales Invoice found for this reservation."))

    outstanding_rows = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", invoice_names], "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "customer", "company", "outstanding_amount"],
        order_by="posting_date asc, creation asc",
    )
    if not outstanding_rows:
        frappe.throw(_("No outstanding Sales Invoice found for this reservation."))

    paid_amount = float(payment_info.get("paid_amount") or 0)
    if paid_amount <= 0:
        frappe.throw(_("Paid amount must be greater than zero."))

    mode_of_payment = payment_info.get("mode_of_payment")
    if not mode_of_payment:
        frappe.throw(_("Mode of Payment is required."))

    # Use the first invoice to derive company / customer (all should be the same)
    first_inv = frappe.get_doc("Sales Invoice", outstanding_rows[0].name)
    company = first_inv.company or frappe.db.get_single_value("Global Defaults", "default_company")
    customer = first_inv.customer

    mop = frappe.get_doc("Mode of Payment", mode_of_payment)
    mop_account = next((a.default_account for a in mop.accounts if a.company == company), None)
    if not mop_account:
        frappe.throw(_("No account found for selected Mode of Payment in company {0}.").format(company))

    # Distribute paid_amount across invoices oldest-first
    remaining = paid_amount
    allocations = []  # list of (invoice_name, allocated_amount)
    for row in outstanding_rows:
        if remaining <= 0:
            break
        inv_outstanding = float(row.outstanding_amount or 0)
        alloc = min(remaining, inv_outstanding)
        if alloc > 0:
            allocations.append((row.name, alloc))
            remaining -= alloc

    total_allocated = sum(a for _, a in allocations)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.company = company
    pe.party_type = "Customer"
    pe.party = customer
    pe.posting_date = payment_info.get("payment_date") or frappe.utils.today()
    pe.mode_of_payment = mode_of_payment
    pe.paid_to = mop_account
    pe.paid_amount = total_allocated
    pe.received_amount = total_allocated
    pe.source_exchange_rate = 1
    pe.target_exchange_rate = 1
    if payment_info.get("reference_no"):
        pe.reference_no = payment_info.get("reference_no")
    if payment_info.get("reference_date"):
        pe.reference_date = payment_info.get("reference_date")
    if payment_info.get("remarks"):
        pe.remarks = payment_info.get("remarks")

    for inv_name, alloc in allocations:
        pe.append(
            "references",
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": inv_name,
                "allocated_amount": alloc,
            },
        )
        _upsert_reservation_invoice_row(doc, inv_name, invoice_type="Primary" if inv_name == doc.sales_invoice else "Invoice")

    pe.insert(ignore_permissions=True)
    pe.submit()

    total_outstanding = sum(float(r.outstanding_amount or 0) for r in outstanding_rows)
    doc.flags.ignore_validate_update_after_submit = True
    doc.payment_entry = pe.name
    if total_allocated >= total_outstanding:
        doc.payment_status = "Paid"
    elif total_allocated > 0:
        doc.payment_status = "Partly Paid"
    _upsert_reservation_payment_row(doc, pe.name, amount=total_allocated)
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"payment_entry": pe.name, "allocated_invoices": len(allocations)}


@frappe.whitelist()
def cancel_reservation(reservation_name, reason=None):
    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    if int(doc.docstatus or 0) == 2:
        return {"status": "already_cancelled"}

    if int(doc.docstatus or 0) == 1:
        # Submitted doc -> use cancel workflow
        doc.flags.ignore_permissions = True
        doc.cancel()
    else:
        # Draft/Hold docs can be cancelled in-place
        doc.reservation_status = STATUS_CANCELLED
        doc.flags.ignore_validate_update_after_submit = True
        doc._release_rooms()
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success", "reason": reason or ""}


def process_reservation_lifecycle():
    """
    Scheduled maintenance for canonical reservations.

    - Hold reservations whose hold_expires_at has passed become Expired.
    - Confirmed reservations with an arrival date before today become No Show.
    """
    now_value = now_datetime()
    today = frappe.utils.nowdate()

    expired_holds = frappe.get_all(
        "Hotel Reservation",
        filters={
            "reservation_status": STATUS_HOLD,
            "hold_expires_at": ["<", now_value],
            "docstatus": ["!=", 2],
        },
        fields=["name"],
    )

    no_shows = frappe.get_all(
        "Hotel Reservation",
        filters={
            "reservation_status": STATUS_CONFIRMED,
            "from_date": ["<", today],
            "docstatus": ["!=", 2],
        },
        fields=["name"],
    )

    for row in expired_holds:
        doc = frappe.get_doc("Hotel Reservation", row.name)
        doc.flags.ignore_validate_update_after_submit = True
        doc.reservation_status = STATUS_EXPIRED
        doc._release_rooms()
        doc.save(ignore_permissions=True)

    for row in no_shows:
        doc = frappe.get_doc("Hotel Reservation", row.name)
        doc.flags.ignore_validate_update_after_submit = True
        doc.reservation_status = STATUS_NO_SHOW
        doc._release_rooms()
        doc.save(ignore_permissions=True)

    if expired_holds or no_shows:
        frappe.db.commit()

    return {"expired": len(expired_holds), "no_show": len(no_shows)}
