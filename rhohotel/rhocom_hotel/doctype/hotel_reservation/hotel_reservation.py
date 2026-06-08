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
from frappe.utils import date_diff, flt, getdate, now_datetime

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


def _is_cancelled_reservation(doc):
    return int(getattr(doc, "docstatus", 0) or 0) == 2 or (getattr(doc, "reservation_status", "") or "") == STATUS_CANCELLED


def _assert_reservation_mutable(doc, action=None):
    if _is_cancelled_reservation(doc):
        frappe.throw(_("{0} is cancelled and cannot be edited.").format(doc.name))

# Statuses that mean a room is no longer occupied / unavailable
STATUS_COMPLETED = STATUS_CHECKED_OUT   # alias for readability in queries
_TERMINAL_STATUSES = {STATUS_CANCELLED, STATUS_COMPLETED, STATUS_NO_SHOW, STATUS_EXPIRED}
_DEFAULT_HOLD_HOURS = 1


def _mark_reservation_room_checked_in(row_name, check_in_reference, check_in_time):
    frappe.db.set_value(
        "Hotel Reservation Room",
        row_name,
        {
            "status": STATUS_CHECKED_IN,
            "check_in_time": check_in_time,
            "check_in_reference": check_in_reference,
        },
        update_modified=False,
    )


def link_reservation_invoices_to_check_in(reservation_name, check_in_name, room_row_name=None):
    """Back-link submitted reservation invoices to a Hotel Room Check In.

    Split group reservations have one invoice per room, so only the checked-in
    room row's invoice and row-specific adjustment invoices should move into
    that check-in folio. Central/non-split reservations use the reservation
    invoice ledger.
    """
    if not reservation_name or not check_in_name:
        return []
    if not frappe.db.exists("Hotel Reservation", reservation_name):
        return []
    if not frappe.db.exists("Hotel Room Check In", check_in_name):
        return []
    if not frappe.db.has_column("Sales Invoice", "custom_hotel_room_check_in"):
        return []

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoice_names = []
    if _is_group_split_billing(doc) and room_row_name:
        room_row = next((row for row in doc.rooms or [] if row.name == room_row_name), None)
        if room_row:
            if getattr(room_row, "split_invoice", None):
                invoice_names.append(room_row.split_invoice)
            invoice_names.extend(_get_split_room_adjustment_invoice_names(doc, room_row))
    else:
        invoice_names.extend(_get_reservation_invoice_names(doc))

    linked = []
    for invoice_name in dict.fromkeys([name for name in invoice_names if name]):
        existing_check_in = frappe.db.get_value("Sales Invoice", invoice_name, "custom_hotel_room_check_in")
        if existing_check_in and existing_check_in != check_in_name:
            continue
        frappe.db.set_value(
            "Sales Invoice",
            invoice_name,
            "custom_hotel_room_check_in",
            check_in_name,
            update_modified=False,
        )
        linked.append(invoice_name)

    if linked:
        try:
            from rhohotel.rhocom_hotel.utils.folio import sync_checkin_folio_totals

            sync_checkin_folio_totals(check_in_name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Check-in folio sync failed after reservation invoice link")

    return linked


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
        self._distribute_split_parent_discount()
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
        _cancel_reservation_invoices(self)
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
            room_blocks = self._child_rows("room_blocks")
            room_blocks_enabled = bool(frappe.db.get_single_value("Hotel Settings", "enable_group_room_blocks"))
            if room_blocks and not room_blocks_enabled:
                frappe.throw(
                    _(
                        "Room Blocks are disabled in Hotel Settings. "
                        "Enable Group Room Blocks or remove the room block rows."
                    )
                )
            if not self.rooms and (not room_blocks_enabled or not room_blocks):
                frappe.throw(
                    _(
                        "Group reservations require at least one reserved room. "
                        "Enable Group Room Blocks in Hotel Settings if you want to create block-only group reservations."
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

    def _distribute_split_parent_discount(self):
        """Move a split-group parent discount into room-level discounts."""
        reservation_type = (self.reservation_type or "").strip().lower()
        billing_mode = (self.group_billing_mode or "").strip().lower()
        if reservation_type != "group" or not billing_mode.startswith("split"):
            return
        if not self.rooms or not self.discount_type or not flt(self.discount or 0):
            return

        nights = date_diff(getdate(self.to_date), getdate(self.from_date)) if self.from_date and self.to_date else 0
        gross_rows = []
        for row in self.rooms:
            gross = max(flt(row.rate_per_night or 0) * nights, 0)
            gross_rows.append((row, gross))

        total_gross = sum(gross for _row, gross in gross_rows)
        if total_gross <= 0:
            return

        if self.discount_type == "Percentage":
            total_discount = total_gross * min(max(flt(self.discount or 0), 0), 100) / 100
        elif self.discount_type == "Fixed Amount":
            total_discount = min(flt(self.discount or 0), total_gross)
        else:
            total_discount = 0
        total_discount = flt(total_discount, 2)

        allocated = 0
        if self.discount_type == "Fixed Amount":
            eligible_rows = [(row, gross) for row, gross in gross_rows if gross > 0]
            if not eligible_rows:
                return
            equal_share = flt(total_discount / len(eligible_rows), 2)
            for idx, (row, gross) in enumerate(eligible_rows):
                if idx == len(eligible_rows) - 1:
                    row_discount = total_discount - allocated
                else:
                    row_discount = equal_share
                row.discount = min(max(flt(row_discount, 2), 0), gross)
                allocated += flt(row.discount or 0)
        else:
            for idx, (row, gross) in enumerate(gross_rows):
                if idx == len(gross_rows) - 1:
                    row_discount = total_discount - allocated
                else:
                    row_discount = flt((total_discount * gross / total_gross) if total_gross else 0, 2)
                row.discount = min(max(flt(row_discount, 2), 0), gross)
                allocated += flt(row.discount or 0)

        self.discount_type = ""
        self.discount = 0
        self.discount_amount = 0

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
    source_invoice=None,
):
    """
    Adjust the arrival and/or departure dates of a submitted Hotel Reservation.
    Recalculates nights and totals; saves the document in-place.
    """
    from frappe.utils import getdate, date_diff, flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)
    old_room_totals = {row.name: flt(row.room_total or 0) for row in doc.rooms or []}
    old_room_discounts = {row.name: flt(row.discount or 0) for row in doc.rooms or []}
    old_subtotal = flt(doc.subtotal or 0)
    old_discount_amount = flt(doc.discount_amount or 0)

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
    if _is_group_split_billing(doc):
        doc._distribute_split_parent_discount()
    doc._recalculate_room_totals()
    doc._recalculate_totals()
    doc.save(ignore_permissions=True)

    invoice_adjustment = None
    linked_invoice_names = [
        name for name in _get_reservation_invoice_names(doc) if name
    ]
    has_submitted_invoice = any(
        frappe.db.get_value(
            "Sales Invoice",
            {"name": invoice_name, "docstatus": 1},
            "name",
        )
        for invoice_name in set(linked_invoice_names)
    )

    if has_submitted_invoice:
        if _is_group_split_billing(doc):
            created = _adjust_split_invoices_for_reservation(
                doc,
                old_room_totals=old_room_totals,
                old_room_discounts=old_room_discounts,
                adjustment_discount_type=new_discount_type,
                adjustment_discount=new_discount,
                reason="Stay adjustment",
            )
            invoice_adjustment = {
                "status": "split_adjustments_created" if created else "no_change",
                "adjustments": [
                    {
                        "sales_invoice": inv.name,
                        "is_return": int(inv.is_return or 0),
                        "grand_total": flt(inv.grand_total),
                    }
                    for inv in created
                ],
            }
        else:
            invoice_adjustment = adjust_invoice_for_reservation(
                reservation_name,
                source_invoice=source_invoice,
                old_subtotal=old_subtotal,
                old_discount_amount=old_discount_amount,
            )

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
        "invoice_adjustment": invoice_adjustment,
    }


@frappe.whitelist()
def change_room_in_reservation(reservation_name, old_room_number, new_room_number, reason=None):
    """
    Swap a room row in a submitted Hotel Reservation.
    Validates the new room is not already reserved for the same period.
    """
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)

    if any(getattr(row, "check_in_reference", None) or getattr(row, "status", None) == STATUS_CHECKED_IN for row in doc.rooms or []):
        frappe.throw(_("Cannot change room on a reservation that has already been checked in. Use room transfer from Check In Details."))

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

    old_room_total = float(target_row.room_total or 0)

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
        if _is_group_split_billing(doc):
            adjustment_doc = _adjust_split_invoice_for_room(
                doc,
                target_row,
                difference=float(target_row.room_total or 0) - old_room_total,
                reason=reason or "Room change",
            )
            if adjustment_doc:
                doc.flags.ignore_validate_update_after_submit = True
                doc.save(ignore_permissions=True)
                adjustment = {
                    "status": "split_adjustment_created",
                    "sales_invoice": adjustment_doc.name,
                    "is_return": int(adjustment_doc.is_return or 0),
                    "difference": float(adjustment_doc.grand_total or 0),
                }
            else:
                adjustment = {"status": "no_change"}
        else:
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
    _assert_reservation_mutable(doc)
    row = next((r for r in doc.rooms if r.name == room_row_name), None)
    if not row:
        return {"status": "error", "message": f"Room row not found: {room_row_name}"}
    if getattr(row, 'status', None) == STATUS_CHECKED_IN or row.check_in_reference:
        return {"status": "success", "message": f"Room {row.room_number} already checked in.",
                "check_in_reference": row.check_in_reference}

    try:
        from rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings import get_default_check_in_datetime

        ci_dt = get_default_check_in_datetime()
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
            _mark_reservation_room_checked_in(row.name, existing_ci, ci_dt)
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
        ci_doc.reservation_source = _valid_marketplace_source(doc.source_channel)
        ci_doc.discount_type = doc.discount_type or "None"
        ci_doc.discount = flt(doc.discount or 0)
        ci_doc.flags.skip_availability_check = True
        ci_doc.insert(ignore_permissions=True)
        ci_doc.submit()

        _mark_reservation_room_checked_in(row.name, ci_doc.name, ci_dt)
        link_reservation_invoices_to_check_in(reservation_name, ci_doc.name, row.name)
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
        message = str(e) or "Could not check in room. Please try again."
        if any(token in message.lower() for token in ["traceback", "frappe.", "pymysql", "line ", "sql", "doctype", "\n"]):
            message = "Could not check in room. Please try again or contact front desk support."
        return {"status": "error", "message": message}


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
    from rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings import get_default_check_in_datetime

    ci_dt = get_default_check_in_datetime()

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
                _mark_reservation_room_checked_in(row.name, existing_ci, ci_dt)
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
            ci_doc.reservation_source = _valid_marketplace_source(doc.source_channel)
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
            row.status = STATUS_CHECKED_IN
            row.check_in_time = ci_dt
            _mark_reservation_room_checked_in(row.name, ci_doc.name, ci_dt)
            link_reservation_invoices_to_check_in(reservation_name, ci_doc.name, row.name)
            checked_in_count += 1
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"bulk_check_in: room {room_label}")
            errors.append(f"Room {room_label}: {str(e)}")

    if checked_in_count > 0 or already_checked_in > 0:
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
            "customer_group": selling_settings.customer_group,
            "territory": selling_settings.territory,
            "mobile_number": doc.primary_guest_phone or "",
            "email_id": doc.primary_guest_email or "",
        }
    )
    customer_doc.insert(ignore_permissions=True)
    doc.db_set("customer", customer_doc.name, update_modified=False)
    return customer_doc.name


def _valid_marketplace_source(source):
    source = (source or "").strip()
    if source and frappe.db.exists("Market Place", source):
        return source
    return ""


def _get_room_item_code(room_number):
    item_code = frappe.db.get_value("Hotel Room", room_number, "erpnext_item") or room_number
    if item_code and frappe.db.exists("Item", item_code):
        return item_code
    return None


def _get_source_invoice_item_code(source_invoice):
    for item in getattr(source_invoice, "items", []) or []:
        if item.item_code and frappe.db.exists("Item", item.item_code):
            return item.item_code
    return None


def _resolve_customer_for_reservation_room(doc, room_row):
    """Resolve the payer/customer for one room row in a split group reservation."""
    customer = None

    if getattr(room_row, "hotel_guest", None):
        customer = frappe.db.get_value("Hotel Guest", room_row.hotel_guest, "customer")

    if not customer:
        guest_name = getattr(room_row, "occupant_name", None) or getattr(room_row, "guest_name", None) or ""
        if guest_name:
            existing_guest = frappe.db.get_value(
                "Hotel Guest", {"hotel_guest_name": guest_name}, "name"
            )
            if existing_guest:
                customer = frappe.db.get_value("Hotel Guest", existing_guest, "customer")

    return customer or doc.customer or _find_or_create_customer_for_reservation(doc)


def _get_split_room_adjustment_invoice_names(doc, room_row):
    """Find adjustment invoices already created for one split-billed room row."""
    try:
        rows = frappe.db.sql(
            """
            SELECT DISTINCT si.name
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE si.docstatus = 1
              AND sii.description LIKE %(reservation)s
              AND sii.description LIKE %(row_name)s
            """,
            {
                "reservation": f"%{doc.name}%",
                "row_name": f"%row {room_row.name}%",
            },
            as_dict=True,
        )
        return [row.name for row in rows]
    except Exception:
        return []


def _get_split_room_billed_total(doc, room_row):
    invoice_names = []
    if getattr(room_row, "split_invoice", None):
        invoice_names.append(room_row.split_invoice)
    invoice_names.extend(_get_split_room_adjustment_invoice_names(doc, room_row))
    invoice_names = list(dict.fromkeys([name for name in invoice_names if name]))
    if not invoice_names:
        return 0

    return frappe.utils.flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabSales Invoice`
            WHERE name IN %(invoice_names)s
              AND docstatus = 1
            """,
            {"invoice_names": tuple(invoice_names)},
        )[0][0]
        or 0
    )


def _create_reservation_adjustment_invoice(
    doc,
    source_invoice,
    difference,
    item_code,
    description,
    invoice_source="Reservation Adjustment",
    gross_difference=None,
    discount_amount=0,
):
    from frappe.utils import flt

    difference = flt(difference)
    if abs(difference) < 0.01:
        return None

    if not source_invoice or int(source_invoice.docstatus or 0) != 1:
        frappe.throw(_("Cannot create adjustment invoice: source invoice must be submitted."))
    if not source_invoice.customer:
        frappe.throw(_("Cannot create adjustment invoice: no customer on source invoice."))
    if difference < 0:
        item_code = _get_source_invoice_item_code(source_invoice) or item_code

    if not item_code or not frappe.db.exists("Item", item_code):
        frappe.throw(_("Cannot create adjustment invoice: no valid item is configured for the room."))

    invoice_data = {
        "doctype": "Sales Invoice",
        "customer": source_invoice.customer,
        "company": source_invoice.company,
        "posting_date": frappe.utils.today(),
        "due_date": frappe.utils.today(),
        "update_stock": 0,
    }

    if difference > 0:
        charge_amount = flt(gross_difference) if gross_difference is not None else flt(abs(difference))
        invoice_discount = min(max(flt(discount_amount), 0), charge_amount)
        if charge_amount <= 0:
            charge_amount = flt(abs(difference))
            invoice_discount = 0
        invoice_data["is_return"] = 0
        invoice_data["items"] = [
            {
                "item_code": item_code,
                "qty": 1,
                "rate": charge_amount,
                "description": description,
            }
        ]
        if invoice_discount:
            invoice_data["apply_discount_on"] = "Grand Total"
            invoice_data["discount_amount"] = invoice_discount
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
                "description": description,
            }
        ]

    adjustment_doc = frappe.get_doc(invoice_data)
    if frappe.db.has_column("Sales Invoice", "custom_invoice_source"):
        adjustment_doc.custom_invoice_source = invoice_source
    adjustment_doc.set_taxes()
    adjustment_doc.insert(ignore_permissions=True)
    adjustment_doc.submit()
    if int(adjustment_doc.is_return or 0) and adjustment_doc.return_against:
        from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import enqueue_credit_note_reconciliation

        enqueue_credit_note_reconciliation(
            adjustment_doc.name,
            source_invoice=adjustment_doc.return_against,
            reservation=doc.name,
        )
    return adjustment_doc


def _adjust_split_invoice_for_room(doc, room_row, difference=None, reason=None, gross_difference=None, discount_amount=0):
    from frappe.utils import flt

    if not getattr(room_row, "split_invoice", None):
        return None

    source_invoice = frappe.get_doc("Sales Invoice", room_row.split_invoice)
    if int(source_invoice.docstatus or 0) != 1:
        return None

    if difference is None:
        difference = flt(room_row.room_total or 0) - _get_split_room_billed_total(doc, room_row)
    difference = flt(difference)
    if abs(difference) < 0.01:
        return None

    item_code = _get_room_item_code(room_row.room_number)
    room_number = room_row.room_number or "Unassigned"
    label = "charge" if difference > 0 else "credit"
    description = _(
        "Split reservation {0} {1} for room {2}, row {3} ({4} night(s), {5} to {6})."
    ).format(
        doc.name,
        label,
        room_number,
        room_row.name,
        room_row.number_of_nights or doc.number_of_nights or 0,
        doc.from_date,
        doc.to_date,
    )
    if reason:
        description = f"{description} Reason: {reason}"

    adjustment_doc = _create_reservation_adjustment_invoice(
        doc,
        source_invoice,
        difference,
        item_code,
        description,
        invoice_source="Reservation Split Adjustment",
        gross_difference=gross_difference,
        discount_amount=discount_amount,
    )
    if not adjustment_doc:
        return None

    _upsert_reservation_invoice_row(
        doc,
        adjustment_doc.name,
        invoice_type="Credit Note" if int(adjustment_doc.is_return or 0) else "Split Adjustment",
    )
    return adjustment_doc


def _get_split_adjustment_discount_allocations(doc, old_room_totals, old_room_discounts, discount_type=None, discount_value=0):
    from frappe.utils import flt

    discount_type = (discount_type or "").strip()
    discount_value = flt(discount_value or 0)
    if not discount_type or discount_value <= 0 or not old_room_totals:
        return {}

    positive_rows = []
    for room_row in doc.rooms or []:
        if not getattr(room_row, "split_invoice", None) or room_row.name not in old_room_totals:
            continue

        old_gross = flt(old_room_totals.get(room_row.name)) + flt(old_room_discounts.get(room_row.name))
        new_gross = flt(room_row.room_total or 0) + flt(room_row.discount or 0)
        gross_difference = flt(new_gross - old_gross)
        if gross_difference > 0:
            positive_rows.append((room_row.name, gross_difference))

    if not positive_rows:
        return {}

    allocations = {}
    if discount_type == "Percentage":
        pct = min(max(discount_value, 0), 100)
        for row_name, gross_difference in positive_rows:
            allocations[row_name] = min(flt(gross_difference * pct / 100, 2), gross_difference)
        return allocations

    if discount_type == "Fixed Amount":
        total_discount = min(discount_value, sum(gross for _row_name, gross in positive_rows))
        equal_share = flt(total_discount / len(positive_rows), 2)
        allocated = 0
        for idx, (row_name, gross_difference) in enumerate(positive_rows):
            row_discount = total_discount - allocated if idx == len(positive_rows) - 1 else equal_share
            allocations[row_name] = min(max(flt(row_discount, 2), 0), gross_difference)
            allocated += flt(allocations[row_name])

    return allocations


def _adjust_split_invoices_for_reservation(
    doc,
    old_room_totals=None,
    old_room_discounts=None,
    adjustment_discount_type=None,
    adjustment_discount=0,
    reason=None,
):
    from frappe.utils import flt

    created = []
    old_room_totals = old_room_totals or {}
    old_room_discounts = old_room_discounts or {}
    adjustment_discount_allocations = _get_split_adjustment_discount_allocations(
        doc,
        old_room_totals,
        old_room_discounts,
        adjustment_discount_type,
        adjustment_discount,
    )
    for room_row in doc.rooms or []:
        if not getattr(room_row, "split_invoice", None):
            continue

        gross_difference = None
        discount_difference = 0
        if room_row.name in old_room_totals:
            difference = flt(room_row.room_total or 0) - flt(old_room_totals.get(room_row.name))
            old_gross = flt(old_room_totals.get(room_row.name)) + flt(old_room_discounts.get(room_row.name))
            new_gross = flt(room_row.room_total or 0) + flt(room_row.discount or 0)
            gross_difference = flt(new_gross - old_gross)
            discount_difference = flt(room_row.discount or 0) - flt(old_room_discounts.get(room_row.name))
            adjustment_discount_amount = flt(adjustment_discount_allocations.get(room_row.name))
            if gross_difference > 0 and adjustment_discount_amount > 0:
                difference = flt(gross_difference - adjustment_discount_amount)
                discount_difference = adjustment_discount_amount
        else:
            difference = None

        adjustment_doc = _adjust_split_invoice_for_room(
            doc,
            room_row,
            difference=difference,
            reason=reason,
            gross_difference=gross_difference if gross_difference and gross_difference > 0 and discount_difference >= 0 else None,
            discount_amount=discount_difference if discount_difference > 0 else 0,
        )
        if adjustment_doc:
            created.append(adjustment_doc)

    if created:
        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)

    return created


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
    _assert_reservation_mutable(doc)

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

    get_value = getattr(doc, "get", None)
    reservation_invoices = get_value("reservation_invoices") if callable(get_value) else getattr(doc, "reservation_invoices", None)
    for row in reservation_invoices or []:
        invoice = row.get("invoice") if hasattr(row, "get") else getattr(row, "invoice", None)
        if invoice:
            invoice_names.append(invoice)

    if getattr(doc, "sales_invoice", None):
        invoice_names.append(doc.sales_invoice)

    rooms = get_value("rooms") if callable(get_value) else getattr(doc, "rooms", None)
    for row in rooms or []:
        if getattr(row, "split_invoice", None):
            invoice_names.append(row.split_invoice)
        invoice_names.extend(_get_split_room_adjustment_invoice_names(doc, row))

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


def _get_reservation_invoice_context(doc, invoice_name):
    for row in doc.get("rooms") or []:
        if getattr(row, "split_invoice", None) == invoice_name:
            return {
                "room_row": row.name,
                "room_number": row.room_number,
                "occupant_name": row.occupant_name or row.guest_name or doc.primary_guest_name,
                "hotel_guest": row.hotel_guest,
                "invoice_scope": "Room",
            }

        if invoice_name in _get_split_room_adjustment_invoice_names(doc, row):
            return {
                "room_row": row.name,
                "room_number": row.room_number,
                "occupant_name": row.occupant_name or row.guest_name or doc.primary_guest_name,
                "hotel_guest": row.hotel_guest,
                "invoice_scope": "Room Adjustment",
            }

    return {
        "room_row": "",
        "room_number": "",
        "occupant_name": doc.primary_guest_name or doc.corporate_guest or doc.customer or "",
        "hotel_guest": "",
        "invoice_scope": "Reservation",
    }


def _get_approved_bill_transfer_totals(invoice_names):
    if not invoice_names or not frappe.db.exists("DocType", "Bill Transfer"):
        return {}

    rows = frappe.db.sql(
        """
        SELECT source_invoice, COALESCE(SUM(total_amount), 0) AS total
        FROM `tabBill Transfer`
        WHERE source_invoice IN %(invoice_names)s
          AND status = 'Approved'
          AND docstatus = 1
        GROUP BY source_invoice
        """,
        {"invoice_names": tuple(invoice_names)},
        as_dict=True,
    ) or []
    return {row.source_invoice: flt(row.total) for row in rows}


def _get_invoice_payment_allocations(invoice_names):
    if not invoice_names:
        return {}

    rows = frappe.db.sql(
        """
        SELECT
            per.reference_name,
            COALESCE(SUM(ABS(per.allocated_amount)), 0) AS allocated
        FROM `tabPayment Entry Reference` per
        INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE per.reference_doctype = 'Sales Invoice'
          AND per.reference_name IN %(invoice_names)s
          AND pe.docstatus = 1
          AND pe.payment_type = 'Receive'
        GROUP BY per.reference_name
        """,
        {"invoice_names": tuple(invoice_names)},
        as_dict=True,
    ) or []
    return {row.reference_name: flt(row.allocated) for row in rows}


def _apply_reservation_invoice_netting(invoices, invoice_names=None):
    """Net reservation invoices for payments, credit notes, and bill transfers."""
    invoices = invoices or []
    invoice_names = list(dict.fromkeys(invoice_names or [inv.name for inv in invoices if inv.get("name")]))
    if not invoices or not invoice_names:
        return invoices

    transfer_totals = _get_approved_bill_transfer_totals(invoice_names)
    payment_allocations = _get_invoice_payment_allocations(invoice_names)
    linked_credits = {}
    for inv in invoices:
        if int(inv.get("is_return") or 0) and inv.get("return_against"):
            linked_credits[inv.return_against] = linked_credits.get(inv.return_against, 0) + abs(flt(inv.get("grand_total")))

    for inv in invoices:
        raw_outstanding = flt(inv.get("outstanding_amount"))
        inv["raw_outstanding_amount"] = raw_outstanding
        inv["source_transfer_amount"] = flt(transfer_totals.get(inv.name))

        if int(inv.get("is_return") or 0):
            continue

        gross = abs(flt(inv.get("grand_total")))
        expected_after_adjustments = max(
            0,
            gross
            - flt(payment_allocations.get(inv.name))
            - flt(linked_credits.get(inv.name))
            - flt(transfer_totals.get(inv.name)),
        )
        inv["outstanding_amount"] = min(max(0, raw_outstanding), expected_after_adjustments)

    return invoices


def _get_reservation_payment_entry_names(doc, invoice_names=None):
    payment_entries = set()
    if getattr(doc, "payment_entry", None):
        payment_entries.add(doc.payment_entry)

    get_value = getattr(doc, "get", None)
    reservation_payments = get_value("reservation_payments") if callable(get_value) else getattr(doc, "reservation_payments", None)
    for row in reservation_payments or []:
        payment_entry = row.get("payment_entry") if hasattr(row, "get") else getattr(row, "payment_entry", None)
        if payment_entry:
            payment_entries.add(payment_entry)

    if invoice_names:
        rows = frappe.db.sql(
            """
            SELECT DISTINCT pe.name
            FROM `tabPayment Entry Reference` per
            INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE pe.docstatus = 1
              AND per.reference_doctype = 'Sales Invoice'
              AND per.reference_name IN %(invoice_names)s
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        ) or []
        payment_entries.update(row.name for row in rows if row.name)

    if not payment_entries:
        return []

    submitted = frappe.get_all(
        "Payment Entry",
        filters={"name": ["in", list(payment_entries)], "docstatus": 1},
        pluck="name",
    )
    return list(dict.fromkeys(submitted or []))


def _assert_reservation_has_no_payments(doc, invoice_names=None):
    payment_entries = _get_reservation_payment_entry_names(doc, invoice_names)
    if payment_entries:
        frappe.throw(
            _(
                "Reservation {0} cannot be cancelled because payment has already been recorded: {1}. "
                "Cancel or refund the payment before cancelling the reservation."
            ).format(doc.name, ", ".join(payment_entries))
        )


def _cancel_reservation_invoices(doc):
    invoice_names = _get_reservation_invoice_names(doc)
    _assert_reservation_has_no_payments(doc, invoice_names)
    if not invoice_names:
        return []

    invoice_rows = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", invoice_names], "docstatus": 1},
        fields=["name", "is_return", "return_against", "posting_date", "creation"],
        order_by="posting_date desc, creation desc",
    )
    linked_returns = {
        row.return_against
        for row in invoice_rows
        if int(row.get("is_return") or 0) and row.get("return_against")
    }
    ordered_invoice_names = [
        row.name
        for row in sorted(
            invoice_rows,
            key=lambda row: (
                0 if int(row.get("is_return") or 0) else 1,
                0 if row.name in linked_returns else 1,
                str(row.get("posting_date") or ""),
                str(row.get("creation") or ""),
            ),
        )
    ]

    cancelled = []
    failed = []
    current_user = frappe.session.user
    for invoice_name in ordered_invoice_names:
        try:
            try:
                if current_user != "Administrator":
                    frappe.set_user("Administrator")
                invoice = frappe.get_doc("Sales Invoice", invoice_name)
                invoice.flags.ignore_permissions = True
                invoice.cancel()
            finally:
                if frappe.session.user != current_user:
                    frappe.set_user(current_user)
            cancelled.append(invoice_name)
        except Exception:
            failed.append(invoice_name)
            frappe.log_error(
                frappe.get_traceback(),
                _("Reservation invoice cancellation failed for {0}").format(invoice_name),
            )

    if failed:
        frappe.throw(
            _(
                "Reservation {0} was not cancelled because these submitted invoice(s) "
                "could not be cancelled: {1}. Please cancel dependent payments, credit notes, "
                "or bill transfers first."
            ).format(doc.name, ", ".join(failed))
        )

    for invoice_name in cancelled:
        get_value = getattr(doc, "get", None)
        reservation_invoices = get_value("reservation_invoices") if callable(get_value) else getattr(doc, "reservation_invoices", None)
        row = next((item for item in (reservation_invoices or []) if getattr(item, "invoice", None) == invoice_name), None)
        if row:
            row.status = "Cancelled"
            row.outstanding_amount = 0
        elif invoice_name == getattr(doc, "sales_invoice", None):
            _upsert_reservation_invoice_row(doc, invoice_name)

    return cancelled


def _reconcile_pending_reservation_credit_notes(reservation_name):
    """Apply open reservation credit notes before reading payable balances."""
    if not reservation_name:
        return []

    from rhohotel.rhocom_hotel.utils.credit_note_reconciliation import (
        reconcile_credit_notes_for_reservation,
    )

    return reconcile_credit_notes_for_reservation(reservation_name, sync_folio=False)


def _get_payment_status_from_amounts(paid_amount, outstanding_amount, invoice_total=0):
    from frappe.utils import flt

    paid_amount = flt(paid_amount)
    outstanding_amount = flt(outstanding_amount)
    invoice_total = flt(invoice_total)

    if invoice_total <= 0 and paid_amount <= 0:
        return "Pending"
    if outstanding_amount <= 0:
        return "Paid"
    if paid_amount > 0:
        return "Partly Paid"
    return "Pending"


@frappe.whitelist()
def get_payment_summary_for_reservation(reservation_name):
    """Return paid amount, balance, invoices and payment entries from submitted ledger docs."""
    from frappe.utils import flt

    _reconcile_pending_reservation_credit_notes(reservation_name)

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoice_names = _get_reservation_invoice_names(doc)
    invoices = []

    if invoice_names:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", invoice_names], "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "status", "is_return", "return_against"],
            order_by="posting_date asc",
        )
        invoices = _apply_reservation_invoice_netting(invoices, invoice_names)

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
        invoice.update(_get_reservation_invoice_context(doc, invoice.name))
        row_type = "Credit Note" if int(invoice.get("is_return") or 0) else "Invoice"
        ledger_changed = _upsert_reservation_invoice_row(doc, invoice.name, row_type) or ledger_changed
    for payment in payments:
        ledger_changed = _upsert_reservation_payment_row(doc, payment.name, amount=flt(payment.amount or 0)) or ledger_changed

    paid_amount = sum(flt(payment.amount) for payment in payments)
    reservation_total = flt(doc.net_total or doc.total_amount or 0)
    balance = outstanding_total if invoices else max(0, reservation_total - paid_amount)
    payment_status = _get_payment_status_from_amounts(paid_amount, balance, invoice_total)
    if doc.get("payment_status") != payment_status:
        doc.flags.ignore_validate_update_after_submit = True
        doc.payment_status = payment_status
        ledger_changed = True

    if ledger_changed:
        _persist_reservation_ledger_updates(doc)
        frappe.db.commit()

    return {
        "paid_amount": paid_amount,
        "balance": max(0, flt(balance)),
        "invoice_total": invoice_total,
        "outstanding_amount": outstanding_total,
        "payment_status": payment_status,
        "invoices": invoices,
        "payment_entries": payments,
    }


@frappe.whitelist()
def get_outstanding_invoices_for_reservation(reservation_name):
    _reconcile_pending_reservation_credit_notes(reservation_name)

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoices = []
    invoice_names = _get_reservation_invoice_names(doc)
    invoice_rows = []

    for invoice_name in invoice_names:
        inv = frappe.db.get_value(
            "Sales Invoice",
            invoice_name,
            ["name", "customer", "customer_name", "posting_date", "grand_total", "outstanding_amount", "is_return", "return_against"],
            as_dict=True,
        )
        if inv:
            invoice_rows.append(inv)

    _apply_reservation_invoice_netting(invoice_rows, invoice_names)

    for inv in invoice_rows:
        if float(inv.get("outstanding_amount") or 0) > 0:
            invoice_name = inv.get("name")
            inv.update(_get_reservation_invoice_context(doc, invoice_name))
            inv["credit_note_amount"] = _get_invoice_credit_note_amount(invoice_name)
            inv["amount_due"] = inv.get("outstanding_amount")
            invoices.append(inv)

    return invoices


def _get_invoice_credit_note_amount(invoice_name):
    if not invoice_name:
        return 0

    from frappe.utils import flt

    return flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(ABS(grand_total)), 0)
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND is_return = 1
              AND return_against = %s
            """,
            invoice_name,
        )[0][0]
        or 0
    )


@frappe.whitelist()
def create_bill_transfer_for_reservation(reservation_name, to_guest, invoices, reason="", note=""):
    """Create Bill Transfer document(s) for outstanding reservation invoices."""
    import json
    from frappe.utils import flt, cint

    if isinstance(invoices, str):
        try:
            invoices = json.loads(invoices)
        except Exception:
            invoices = [name.strip() for name in invoices.split(",") if name.strip()]
    invoices = [str(name).strip() for name in (invoices or []) if str(name).strip()]
    if not invoices:
        frappe.throw(_("Please select at least one invoice to transfer."))

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)
    reservation_invoice_names = set(_get_reservation_invoice_names(doc))
    invalid = [name for name in invoices if name not in reservation_invoice_names]
    if invalid:
        frappe.throw(_("Selected invoice(s) do not belong to reservation {0}: {1}").format(
            reservation_name,
            ", ".join(invalid),
        ))

    if not frappe.db.exists("Hotel Guest", to_guest):
        frappe.throw(_("Target corporate account {0} was not found.").format(to_guest))

    to_guest_doc = frappe.db.get_value(
        "Hotel Guest", to_guest, ["hotel_guest_name", "guest_type", "customer"], as_dict=True
    ) or {}
    if (to_guest_doc.get("guest_type") or "").lower() != "corporate":
        frappe.throw(_("Reservation bill transfer target must be a Corporate guest/account."))
    if not to_guest_doc.get("customer"):
        frappe.throw(
            _("Corporate account {0} does not have a linked Customer record.").format(
                to_guest_doc.get("hotel_guest_name") or to_guest
            )
        )

    full_reason = reason
    if note:
        full_reason = f"{reason} — {note}" if reason else note

    created = []
    for inv_name in invoices:
        inv_doc = frappe.get_doc("Sales Invoice", inv_name)
        if int(inv_doc.docstatus or 0) != 1 or cint(inv_doc.is_return):
            continue

        total_amount = flt(inv_doc.outstanding_amount)
        if total_amount <= 0:
            continue

        from_guest = _resolve_reservation_invoice_guest(doc, inv_doc)
        from_customer = frappe.db.get_value("Hotel Guest", from_guest, "customer")
        if from_customer == to_guest_doc.get("customer"):
            frappe.throw(_("Invoice {0} is already billed to the selected corporate account.").format(inv_name))

        bt = frappe.new_doc("Bill Transfer")
        bt.from_guest = from_guest
        bt.to_guest = to_guest
        bt.source_invoice = inv_name
        bt.total_amount = total_amount
        bt.reason = full_reason
        bt.status = "Pending Approval"
        bt.append("items", {
            "description": _("Reservation {0} invoice transfer").format(reservation_name),
            "amount": total_amount,
            "reference_document": inv_name,
        })
        bt.insert(ignore_permissions=True)

        created.append({
            "name": bt.name,
            "invoice": inv_name,
            "amount": total_amount,
        })

    if not created:
        frappe.throw(_("No eligible outstanding Sales Invoices found for this reservation."))

    return created


def _resolve_reservation_invoice_guest(doc, invoice_doc):
    context = _get_reservation_invoice_context(doc, invoice_doc.name)
    if context.get("hotel_guest") and frappe.db.exists("Hotel Guest", context.get("hotel_guest")):
        return context.get("hotel_guest")

    for guest_name in [doc.get("corporate_guest")]:
        if guest_name and frappe.db.exists("Hotel Guest", guest_name):
            customer = frappe.db.get_value("Hotel Guest", guest_name, "customer")
            if customer == invoice_doc.customer:
                return guest_name

    for row in doc.get("rooms") or []:
        guest_name = getattr(row, "hotel_guest", None)
        if guest_name and frappe.db.exists("Hotel Guest", guest_name):
            customer = frappe.db.get_value("Hotel Guest", guest_name, "customer")
            if customer == invoice_doc.customer:
                return guest_name

    guest_name = frappe.db.get_value("Hotel Guest", {"customer": invoice_doc.customer}, "name")
    if guest_name:
        return guest_name

    return _get_or_create_transfer_guest_for_customer(invoice_doc.customer)


def _get_or_create_transfer_guest_for_customer(customer):
    if not customer or not frappe.db.exists("Customer", customer):
        frappe.throw(_("Invoice customer {0} was not found.").format(customer))

    guest_name = frappe.db.get_value("Hotel Guest", {"customer": customer}, "name")
    if guest_name:
        return guest_name

    customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
    candidate_name = customer_name
    if frappe.db.exists("Hotel Guest", candidate_name):
        candidate_name = f"{customer_name} Billing"

    doc = frappe.new_doc("Hotel Guest")
    doc.hotel_guest_name = candidate_name
    doc.guest_type = "Individual"
    doc.phone_number = "+2340000000000"
    doc.customer = customer
    doc.notes = _("Auto-created as reservation bill-transfer source for Customer {0}.").format(customer)
    doc.insert(ignore_permissions=True)

    return doc.name


@frappe.whitelist()
def adjust_invoice_for_reservation(reservation_name, source_invoice=None, old_subtotal=None, old_discount_amount=None):
    """
    Reconcile the linked Sales Invoice after a stay adjustment.

    Rules:
    - Compute net billed amount across all linked submitted invoices.
    - If new reservation total is higher, create a positive adjustment invoice.
    - If new reservation total is lower, create a credit note.
    """
    from frappe.utils import flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)

    if _is_group_split_billing(doc):
        created = _adjust_split_invoices_for_reservation(doc)
        if created:
            frappe.db.commit()
            return {
                "status": "split_adjustments_created",
                "adjustments": [
                    {
                        "sales_invoice": inv.name,
                        "is_return": int(inv.is_return or 0),
                        "grand_total": flt(inv.grand_total),
                    }
                    for inv in created
                ],
            }
        return {"status": "no_change", "message": "Split room invoices already match room totals."}

    invoice_names = _get_reservation_invoice_names(doc)
    source_invoice_name = source_invoice or doc.sales_invoice
    if not source_invoice_name:
        if invoice_names:
            source_invoice_name = invoice_names[0]

    if not source_invoice_name:
        return {"status": "no_invoice", "message": "No invoice linked to this reservation."}
    if source_invoice_name not in set(invoice_names):
        frappe.throw(_("Source invoice {0} is not linked to this reservation.").format(source_invoice_name))

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
    if int(source_invoice.is_return or 0):
        frappe.throw(_("Source invoice {0} is already a credit note.").format(source_invoice.name))

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
    gross_difference = None
    discount_difference = 0
    if old_subtotal is not None:
        gross_difference = flt(doc.subtotal or 0) - flt(old_subtotal)
    if old_discount_amount is not None:
        discount_difference = flt(doc.discount_amount or 0) - flt(old_discount_amount)

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
        item_code = _get_room_item_code(room.room_number)
        if item_code:
            break

    if not item_code:
        frappe.throw(_("Cannot create adjustment invoice: no valid Item found for this reservation's rooms."))

    description = (
        _("Stay extension charge for reservation {0} ({1} to {2}, {3} night(s)).")
        if difference > 0
        else _("Stay reduction credit for reservation {0} ({1} to {2}, {3} night(s)).")
    ).format(doc.name, doc.from_date, doc.to_date, doc.number_of_nights)

    adjustment_doc = _create_reservation_adjustment_invoice(
        doc,
        source_invoice,
        difference,
        item_code,
        description,
        invoice_source="Reservation Stay Adjustment",
        gross_difference=gross_difference if gross_difference and gross_difference > 0 and discount_difference >= 0 else None,
        discount_amount=discount_difference if discount_difference > 0 else 0,
    )

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
    _assert_reservation_mutable(doc)

    if not _is_group_split_billing(doc):
        frappe.throw(_("Per-room invoicing is only available for Group reservations with Split billing mode."))

    room_row = next((r for r in doc.rooms if r.name == room_row_name), None)
    if not room_row:
        frappe.throw(_("Room row {0} not found in reservation {1}.").format(room_row_name, reservation_name))

    if room_row.split_invoice:
        updated = _upsert_reservation_invoice_row(doc, room_row.split_invoice, invoice_type="Split")
        if updated:
            _persist_reservation_ledger_updates(doc)
            frappe.db.commit()
        return {"sales_invoice": room_row.split_invoice, "already_exists": True}

    customer = _resolve_customer_for_reservation_room(doc, room_row)
    if not customer:
        frappe.throw(_("Cannot create invoice: no customer resolved for room {0}. Assign a guest to this room first.").format(room_row.room_number))

    room_number = room_row.room_number
    item_code = _get_room_item_code(room_number)
    if not item_code:
        frappe.throw(_("No billable Item found for room {0}. Configure Hotel Room.erpnext_item.").format(room_number))

    nights = int(room_row.number_of_nights or doc.number_of_nights or 0)
    gross_room_charge = flt(room_row.rate_per_night or 0) * nights
    if gross_room_charge <= 0:
        gross_room_charge = flt(room_row.room_total or 0) + flt(room_row.discount or 0)
    room_discount = min(max(flt(room_row.discount or 0), 0), gross_room_charge)

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "posting_date": frappe.utils.today(),
        "due_date": getdate(doc.to_date),
        "update_stock": 0,
        "items": [{
            "item_code": item_code,
            "qty": 1,
            "rate": gross_room_charge,
            "description": _("Reservation charge for {0}, room {1} ({2} night(s), {3} to {4})").format(
                doc.name, room_number, nights,
                doc.from_date, doc.to_date,
            ),
        }],
    })
    if room_discount:
        si.discount_amount = room_discount
        si.apply_discount_on = "Net Total"
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
def apply_split_room_discount(reservation_name, room_row_name, discount=0, reason=None):
    """Apply an individual room discount on a split-billing group reservation."""
    from frappe.utils import flt

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)
    if not _is_group_split_billing(doc):
        frappe.throw(_("Individual room discounts are only available for Group reservations with Split billing mode."))

    room_row = next((row for row in (doc.rooms or []) if row.name == room_row_name), None)
    if not room_row:
        frappe.throw(_("Room row {0} not found in reservation {1}.").format(room_row_name, reservation_name))
    if getattr(room_row, "split_invoice", None):
        frappe.throw(_("Discount cannot be changed after invoice {0} has been created for this room.").format(room_row.split_invoice))

    nights = int(room_row.number_of_nights or doc.number_of_nights or 0)
    base_total = flt(room_row.rate_per_night or 0) * nights
    requested_discount = flt(discount or 0)
    if requested_discount < 0:
        frappe.throw(_("Discount cannot be negative."))
    if requested_discount > base_total:
        frappe.throw(_("Discount cannot be greater than the room charge."))

    old_room_total = flt(room_row.room_total or 0)
    room_row.discount = requested_discount
    room_row.room_total = max(flt(base_total - requested_discount), 0)

    doc.flags.ignore_validate_update_after_submit = True
    doc._recalculate_totals()
    doc.save(ignore_permissions=True)

    adjustment_doc = _adjust_split_invoice_for_room(
        doc,
        room_row,
        difference=flt(room_row.room_total or 0) - old_room_total,
        reason=reason or _("Individual room discount adjustment"),
    )

    if adjustment_doc:
        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "reservation": doc.name,
        "room_row": room_row.name,
        "discount": room_row.discount,
        "room_total": room_row.room_total,
        "split_invoice": room_row.split_invoice,
        "adjustment_invoice": adjustment_doc.name if adjustment_doc else None,
        "is_return": int(adjustment_doc.is_return or 0) if adjustment_doc else 0,
    }


@frappe.whitelist()
def distribute_split_room_discount(reservation_name, discount=0, discount_type="Fixed Amount", room_row_names=None, reason=None):
    """Distribute a discount across selected split-billing room rows."""
    import json
    from frappe.utils import flt

    if isinstance(room_row_names, str):
        try:
            room_row_names = json.loads(room_row_names)
        except Exception:
            room_row_names = [name.strip() for name in room_row_names.split(",") if name.strip()]
    room_row_names = [str(name).strip() for name in (room_row_names or []) if str(name).strip()]

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)
    if not _is_group_split_billing(doc):
        frappe.throw(_("Discount distribution is only available for Group reservations with Split billing mode."))

    target_rows = [row for row in (doc.rooms or []) if not room_row_names or row.name in room_row_names]
    if not target_rows:
        frappe.throw(_("Select at least one reservation room row."))
    invoiced_rows = [row for row in target_rows if getattr(row, "split_invoice", None)]
    if invoiced_rows:
        room_labels = ", ".join(row.room_number or row.name for row in invoiced_rows)
        frappe.throw(_("Discount cannot be changed after invoice has been created for room(s): {0}.").format(room_labels))

    nights = int(doc.number_of_nights or 0)
    if not nights and doc.from_date and doc.to_date:
        nights = date_diff(getdate(doc.to_date), getdate(doc.from_date))

    gross_rows = []
    for row in target_rows:
        gross_rows.append((row, max(flt(row.rate_per_night or 0) * nights, 0)))

    total_gross = sum(gross for _row, gross in gross_rows)
    if total_gross <= 0:
        frappe.throw(_("Selected rooms do not have a billable room charge."))

    requested_discount = flt(discount or 0)
    if requested_discount < 0:
        frappe.throw(_("Discount cannot be negative."))

    discount_type = discount_type or "Fixed Amount"
    if discount_type == "Percentage":
        total_discount = total_gross * min(max(requested_discount, 0), 100) / 100
    elif discount_type == "Fixed Amount":
        total_discount = min(requested_discount, total_gross)
    else:
        total_discount = 0
    total_discount = flt(total_discount, 2)

    old_room_totals = {row.name: flt(row.room_total or 0) for row in target_rows}
    allocated = 0
    updated_rows = []
    for idx, (row, gross) in enumerate(gross_rows):
        if idx == len(gross_rows) - 1:
            row_discount = total_discount - allocated
        else:
            row_discount = flt((total_discount * gross / total_gross) if total_gross else 0, 2)
        row.discount = min(max(flt(row_discount, 2), 0), gross)
        row.room_total = max(flt(gross - row.discount, 2), 0)
        allocated += flt(row.discount or 0)
        updated_rows.append(row)

    doc.discount_type = "None"
    doc.discount = 0
    doc.discount_amount = 0
    doc.flags.ignore_validate_update_after_submit = True
    doc._recalculate_totals()
    doc.save(ignore_permissions=True)

    adjustments = []
    for row in updated_rows:
        adjustment_doc = _adjust_split_invoice_for_room(
            doc,
            row,
            difference=flt(row.room_total or 0) - old_room_totals.get(row.name, 0),
            reason=reason or _("Split room discount distribution"),
        )
        if adjustment_doc:
            adjustments.append(adjustment_doc)

    if adjustments:
        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "reservation": doc.name,
        "discount_amount": total_discount,
        "rooms": [
            {
                "room_row": row.name,
                "room_number": row.room_number,
                "discount": flt(row.discount or 0),
                "room_total": flt(row.room_total or 0),
                "split_invoice": row.split_invoice,
            }
            for row in updated_rows
        ],
        "adjustment_invoices": [invoice.name for invoice in adjustments],
    }


@frappe.whitelist()
def create_pending_split_invoices(reservation_name):
    """Create invoices only for split-group room rows that do not yet have split_invoice."""
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)

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

    _reconcile_pending_reservation_credit_notes(reservation_name)

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    _assert_reservation_mutable(doc)
    selected_invoice_names = payment_info.get("selected_invoices") or payment_info.get("invoice_names") or []
    if isinstance(selected_invoice_names, str):
        try:
            selected_invoice_names = json.loads(selected_invoice_names)
        except Exception:
            selected_invoice_names = [name.strip() for name in selected_invoice_names.split(",") if name.strip()]
    selected_invoice_names = [str(name).strip() for name in (selected_invoice_names or []) if str(name).strip()]

    # Collect ALL outstanding invoices, ordered oldest first
    invoice_names = _get_reservation_invoice_names(doc)
    if not invoice_names:
        frappe.throw(_("No outstanding Sales Invoice found for this reservation."))

    if selected_invoice_names:
        invalid = [name for name in selected_invoice_names if name not in invoice_names]
        if invalid:
            frappe.throw(_("Selected invoice(s) do not belong to this reservation: {0}").format(", ".join(invalid)))
        invoice_names = selected_invoice_names

    outstanding_rows = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", invoice_names], "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "customer", "company", "outstanding_amount"],
        order_by="posting_date asc, creation asc",
    )
    if not outstanding_rows:
        frappe.throw(_("No outstanding Sales Invoice found for this reservation."))

    invoice_customers = {row.customer for row in outstanding_rows if row.customer}
    if len(invoice_customers) > 1:
        frappe.throw(
            _(
                "Selected invoices belong to different customers. "
                "Please receive payment for one guest/customer at a time."
            )
        )

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

    return {
        "payment_entry": pe.name,
        "allocated_invoices": len(allocations),
        "invoice_names": [name for name, _amount in allocations],
    }


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
        _cancel_reservation_invoices(doc)
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
