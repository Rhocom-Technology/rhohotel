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

    # Update the old room status back to Reserved (if not occupied)
    try:
        old_room = frappe.get_doc("Hotel Room", old_room_number)
        if old_room.status == "Reserved":
            old_room.status = "Vacant"
            old_room.save(ignore_permissions=True)
    except Exception:
        pass

    # Mark new room as Reserved
    new_room.status = "Reserved"
    new_room.save(ignore_permissions=True)

    doc._recalculate_totals()
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "new_room": new_room_number}


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


@frappe.whitelist()
def create_invoice_for_reservation(reservation_name):
    from frappe.utils import getdate, flt
    from rhohotel.rhocom_hotel.utils.billing_routing import resolve_payer

    doc = frappe.get_doc("Hotel Reservation", reservation_name)

    if doc.sales_invoice:
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
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"sales_invoice": si.name}


@frappe.whitelist()
def get_outstanding_invoices_for_reservation(reservation_name):
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    invoices = []

    if doc.sales_invoice:
        inv = frappe.db.get_value(
            "Sales Invoice",
            doc.sales_invoice,
            ["name", "posting_date", "grand_total", "outstanding_amount"],
            as_dict=True,
        )
        if inv and float(inv.get("outstanding_amount") or 0) > 0:
            invoices.append(inv)

    return invoices


@frappe.whitelist()
def collect_payment_for_reservation(reservation_name, payment_info=None):
    import json

    if payment_info and isinstance(payment_info, str):
        payment_info = json.loads(payment_info)
    payment_info = payment_info or {}

    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    if not doc.sales_invoice:
        frappe.throw(_("No Sales Invoice is linked to this reservation."))

    invoice = frappe.get_doc("Sales Invoice", doc.sales_invoice)
    outstanding = float(invoice.outstanding_amount or 0)
    paid_amount = float(payment_info.get("paid_amount") or 0)
    if paid_amount <= 0:
        frappe.throw(_("Paid amount must be greater than zero."))

    company = invoice.company or frappe.db.get_single_value("Global Defaults", "default_company")
    mode_of_payment = payment_info.get("mode_of_payment")
    if not mode_of_payment:
        frappe.throw(_("Mode of Payment is required."))

    mop = frappe.get_doc("Mode of Payment", mode_of_payment)
    mop_account = next((a.default_account for a in mop.accounts if a.company == company), None)
    if not mop_account:
        frappe.throw(_("No account found for selected Mode of Payment in company {0}.").format(company))

    allocated_amount = min(paid_amount, outstanding)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.company = company
    pe.party_type = "Customer"
    pe.party = invoice.customer
    pe.posting_date = payment_info.get("payment_date") or frappe.utils.today()
    pe.mode_of_payment = mode_of_payment
    pe.paid_to = mop_account
    pe.paid_amount = allocated_amount
    pe.received_amount = allocated_amount
    pe.source_exchange_rate = 1
    pe.target_exchange_rate = 1
    if payment_info.get("reference_no"):
        pe.reference_no = payment_info.get("reference_no")
    if payment_info.get("reference_date"):
        pe.reference_date = payment_info.get("reference_date")
    if payment_info.get("remarks"):
        pe.remarks = payment_info.get("remarks")

    pe.append(
        "references",
        {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "allocated_amount": allocated_amount,
        },
    )

    pe.insert(ignore_permissions=True)
    pe.submit()

    doc.flags.ignore_validate_update_after_submit = True
    doc.payment_entry = pe.name
    if allocated_amount >= outstanding and outstanding > 0:
        doc.payment_status = "Paid"
    elif allocated_amount > 0:
        doc.payment_status = "Partly Paid"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"payment_entry": pe.name}


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
