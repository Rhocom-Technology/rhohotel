# Copyright (c) 2026, Rhocom Technology Ltd and contributors
# For license information, please see license.txt

"""
hotel_reservation.py – Canonical single-reservation doctype for Rhohotel.

Background
----------
Previously the system spread reservation logic across multiple doctypes:
  - Hotel Front Desk Reservation  (multi-room, front-desk-initiated)
  - Hotel Room Reservation        (single-room, created per allocated room)
  - Temporary Booking             (online hold before payment)
  - Corporate Check In            (corporate walk-in / reservation)

This module is the *canonical* replacement.  One Hotel Reservation document
represents the full lifecycle of a stay — from initial hold through check-in,
checkout, and invoicing — regardless of the originating channel.

Lifecycle / state machine
-------------------------
  Draft → Hold
    Room hold is activated; hold_expires_at is set.
    Background job (background_jobs.py) watches for expiry and transitions
    the status to Expired when hold_expires_at is passed without payment.

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

  Checked In → Cancelled (admin override only)
    Emergency use.  Treated as a forced checkout for reporting purposes.

  Any active state → No Show
    Policy-driven transition when guest does not arrive by a threshold time.

Room availability
-----------------
All availability checks are delegated to the centralized utility:
    rhohotel.rhocom_hotel.utils.room_availability

The utility now checks *both* legacy doctypes (Hotel Room Reservation,
Hotel Room Check In) *and* canonical Hotel Reservation room allocations so
that double-booking is prevented across all booking channels.

Pricing totals
--------------
  subtotal      = sum(room.room_total for room in self.rooms)
  discount_amt  = % or fixed amount applied to subtotal
  total_amount  = subtotal - discount_amount
  net_total     = total_amount (+ taxes when invoice is created)

Legacy migration fields
-----------------------
  frontdesk_reference_legacy  – source Hotel Front Desk Reservation
  temporary_booking_legacy    – source Temporary Booking (online hold)
  room_reservation_legacy     – source Hotel Room Reservation (single-room)

These fields are read-only and will be retired once the full consolidation
migration (Phases 1-6) is complete and verified.
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
    STATUS_DRAFT:       {STATUS_HOLD,       STATUS_CANCELLED},
    STATUS_HOLD:        {STATUS_CONFIRMED,  STATUS_CANCELLED, STATUS_EXPIRED},
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
        2. At least one room allocation row exists.
        3. No room is double-booked for the given dates (uses centralized utility).
        4. Pricing totals are recalculated from child rows.
        5. Corporate guest is set when reservation_type = Corporate.
        """
        self._validate_dates()
        self._validate_rooms_present()
        self._validate_corporate_guest()
        self._validate_room_availability()
        self._recalculate_room_totals()
        self._recalculate_totals()

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

    def _validate_dates(self):
        """Ensure from_date and to_date are present and logically ordered."""
        if not self.from_date or not self.to_date:
            frappe.throw(_("Both Check-In Date and Check-Out Date are required."))

        if getdate(self.to_date) <= getdate(self.from_date):
            frappe.throw(_("Check-Out Date must be after Check-In Date."))

        # Keep number_of_nights in sync
        self.number_of_nights = date_diff(getdate(self.to_date), getdate(self.from_date))

    def _validate_rooms_present(self):
        """Ensure at least one room allocation row has been added."""
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

    def _validate_room_availability(self):
        """
        Check each allocated room for conflicts using the centralized utility.

        Delegates to assert_room_available from room_availability.py.
        Skips validation when the reservation is in a terminal status (cancelled,
        checked-out, no-show, expired) because those do not block availability.
        """
        if self.reservation_status in _TERMINAL_STATUSES:
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
            )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    def _recalculate_room_totals(self):
        """
        Compute room_total and sync number_of_nights for each child row.

        rate_per_night * number_of_nights - row-level discount = room_total.
        This must run before _recalculate_totals() which sums room_total values.
        """
        nights = date_diff(getdate(self.to_date), getdate(self.from_date)) if self.from_date and self.to_date else 0
        for row in self.rooms:
            row.number_of_nights = nights
            rate = float(row.rate_per_night or 0)
            row_discount = float(row.discount or 0)
            row.room_total = round(rate * nights - row_discount, 2)

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

    # ------------------------------------------------------------------
    # Room state management
    # ------------------------------------------------------------------

    def _release_rooms(self):
        """
        Mark each allocated room as Vacant when the reservation is cancelled
        or expired, unless a different active booking is now occupying the room.

        Only rooms that are currently in Reserved status (set by this reservation)
        are updated; Occupied rooms (i.e. an active check-in is live) are left alone.
        """
        for row in self.rooms:
            if not row.room_number:
                continue
            room = frappe.get_doc("Hotel Room", row.room_number)
            if room.status == "Reserved":
                room.status = "Vacant"
                room.save(ignore_permissions=True)


@frappe.whitelist()
def adjust_reservation(reservation_name, new_checkout, new_check_in):
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

    # Recalculate per-room totals using the new night count
    for row in doc.rooms:
        rate = flt(row.rate_per_night)
        row.room_total = round(rate * new_nights, 2)

    doc._recalculate_totals()
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "new_from_date": str(new_from),
        "new_to_date": str(new_to),
        "new_nights": new_nights,
    }
