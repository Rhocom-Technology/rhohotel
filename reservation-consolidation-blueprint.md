# Reservation Consolidation Blueprint (Single Canonical Reservation)

## Goal

Consolidate booking flows to one canonical reservation model while preserving current operations (front desk, online temporary hold, corporate, check-in, checkout, invoicing, and payment).

## Feasibility Verdict

This is possible in the current codebase.

It is a medium-to-high complexity migration because reservation behavior is split across multiple doctypes and API surfaces, but risk can be controlled with a phased approach and a compatibility facade.

## Current State (Why It Feels Complex)

Reservation lifecycle is currently distributed across:

- Hotel Front Desk Reservation (multi-room aggregate)
- Hotel Room Reservation (single-room reservation records)
- Temporary Booking (online hold and payment initiation)
- Hotel Room Check In and Hotel Room Check Out
- Booking and availability helper modules

Main complexity drivers:

- Multiple status systems with partial overlap
- Conversion chains between doctypes
- Duplicate business rules around lifecycle transitions and payments
- Broad usage in whitelisted methods and frontend/API consumers

## Target Architecture

### 1) Canonical aggregate: Hotel Reservation (new)

Use a single parent doctype as the source of truth.

Suggested parent fields:

- reservation_number (unique)
- source_channel (Front Desk, Online, Corporate, Walk In)
- reservation_type (Individual, Corporate)
- reservation_status (Hold, Confirmed, Checked In, Checked Out, Cancelled, No Show)
- payment_status (Pending, Partly Paid, Paid, Failed, Refunded)
- booking_status (Held, Reserved, Released) [optional transitional field]
- guest_profile_kind (Primary Guest, Corporate Account)
- primary_guest_name, primary_guest_email, primary_guest_phone
- corporate_guest (link, optional)
- customer (link)
- from_date, to_date, number_of_nights
- check_in_time, check_out_time (actual timestamps)
- hold_expires_at
- subtotal, discount_type, discount, discount_amount, total_amount, net_total
- sales_invoice, payment_entry, transaction_id
- frontdesk_reference_legacy, temporary_booking_legacy, room_reservation_legacy (temporary migration fields)

Suggested child tables:

- Reservation Room Allocation (one row per room)
  - room_number, room_type, rate_type, season_type
  - rate_per_night, number_of_nights, room_total
  - occupant details (name, id type, id number, phone, email)
  - check_in_reference, checkout_reference
- Reservation Payment Event (optional if Payment Session remains separate)
  - reference, amount, status, provider, timestamps
- Reservation Lifecycle Event (audit of transitions)
  - event_type, previous_status, new_status, actor, timestamp, notes

### 2) Single service layer for all reservation workflows

Create one backend service module that owns all transitions:

- create_hold
- confirm_reservation
- assign_rooms
- check_in
- extend_stay
- check_out
- cancel
- expire_holds
- recalculate_totals

All whitelisted endpoints should call this layer.

### 3) Keep current room availability utility as the only validator

Continue using existing centralized utility for conflicts and room listing:

- assert_room_available
- check_reservation_conflict
- check_checkin_conflict
- get_available_rooms

## State Machine (Canonical)

Allowed transitions:

- Draft -> Hold
- Hold -> Confirmed
- Hold -> Cancelled
- Hold -> Expired
- Confirmed -> Checked In
- Confirmed -> Cancelled
- Checked In -> Checked Out
- Checked In -> Cancelled (admin override only)
- Any active state -> No Show (policy-driven)

Payment status is orthogonal and should not replace reservation_status.

## Mapping From Existing Doctypes

### Hotel Front Desk Reservation -> Hotel Reservation

- Parent maps directly to parent
- Front Desk Reservation Room rows map to Reservation Room Allocation rows
- Existing subtotal/discount/total fields map 1:1
- reservation_type and corporate fields map 1:1

### Hotel Room Reservation -> Hotel Reservation

- Existing single-room records become one reservation with one room allocation row
- Keep original document name in room_reservation_legacy for traceability

### Temporary Booking -> Hotel Reservation

- Hold records become reservations in Hold state
- hold_expires_at, booking_number, payment/transaction fields map to canonical fields
- rooms child table maps to room allocation rows

### Corporate Check In -> Hotel Reservation

- Corporate parent fields map to canonical parent
- Corporate room rows map to canonical room allocations
- If checked in immediately, create reservation in Checked In state with check_in_time populated

### Hotel Room Check In / Check Out

- These can remain operational transaction doctypes initially
- Canonical reservation stores current state and references transaction docs
- In later phase, you can make check-out a pure event on canonical reservation if business allows

## API Compatibility Strategy

Keep existing API signatures for one release window while rewriting internals to canonical service.

Compatibility facade pattern:

- Existing endpoint receives old args
- Map args to canonical command
- Execute canonical service
- Return legacy-shaped response payload

Deprecation policy:

- Add warning header or response flag: deprecated_api=true
- Publish sunset date
- Remove legacy endpoints only after frontend and external clients are migrated

## Migration Plan (Phased)

### Phase 0: Freeze and Inventory (1 to 2 days)

- Freeze new feature work in reservation area
- Catalog all writes to reservation/check-in doctypes
- Add baseline metrics: total reservations/day, hold expiry count, check-in success rate

Exit criteria:

- Complete endpoint inventory and ownership map

### Phase 1: Canonical schema and service layer (3 to 5 days)

- Add Hotel Reservation doctype + child tables
- Implement service layer with full transition guards
- Reuse centralized room availability utility

Exit criteria:

- Unit tests for transitions and conflict checks pass

### Phase 2: Dual-write with read-from-old (3 to 5 days)

- Keep old flows active
- On create/update in legacy doctypes, also write canonical reservation
- Add idempotency keys to avoid duplicates on retries

Exit criteria:

- Canonical and legacy records reconcile for new traffic

### Phase 3: Read-switch to canonical (3 to 5 days)

- Move search/list/detail APIs to canonical reads
- Keep legacy response shape via facade

Exit criteria:

- Frontend screens operate from canonical reads with no behavior regressions

### Phase 4: Write-switch to canonical (3 to 7 days)

- Route all creation/update/check-in/check-out commands to canonical service
- Legacy doctypes become passive mirrors or are no longer written

Exit criteria:

- No primary writes to legacy reservation doctypes for 1 full business cycle

### Phase 5: Historical backfill and reconciliation (2 to 4 days)

- Backfill old reservations into canonical model
- Reconcile totals, statuses, room occupancy timelines
- Produce discrepancy report and fix scripts

Exit criteria:

- Reconciliation error rate below agreed threshold

### Phase 6: Deprecation and cleanup (2 to 3 days)

- Remove dead legacy code paths
- Archive or hide legacy doctypes from normal operations
- Keep audit links for historical references

Exit criteria:

- Legacy reservation creation endpoints removed

## Data Migration Rules

- Use deterministic mapping IDs so migration can be rerun safely
- Never overwrite immutable financial links without audit event
- Preserve original created_by and creation timestamps where possible
- Status mapping must be explicit and versioned

Example status normalization:

- Temporary Booking Hold -> Hold
- Temporary Booking Payment Completed -> Confirmed
- Hotel Room Reservation Booked -> Confirmed
- Hotel Room Reservation Checked-In -> Checked In
- Hotel Room Reservation Completed -> Checked Out
- Cancelled remains Cancelled

## Testing Strategy

1. Unit tests

- Status transition guards
- Discount and total calculations
- Room conflict checks per transition

2. Integration tests

- Front desk create -> payment -> check-in -> checkout
- Online hold -> payment callback -> confirmation
- Corporate reservation and multi-room allocations

3. Migration tests

- Backfill on sample production-like dataset
- Reconciliation assertions (counts, totals, statuses)

4. Non-functional tests

- Concurrent booking attempts on same room/date
- Idempotent retries for payment callbacks and dual-write flows

## Rollback Strategy

- Keep legacy writes enabled behind feature flags until Phase 4 stabilizes
- Keep dual-read fallback for one release after read-switch
- If severe issue occurs, switch read/write flags back to legacy without schema rollback

Feature flags suggested:

- reservation_use_canonical_read
- reservation_use_canonical_write
- reservation_enable_dual_write

## Recommended Sequence For This Repository

1. Introduce canonical doctype and service module only (no behavior change)
2. Wrap current major endpoints with compatibility facade in:
   - hotel_front_desk_reservation.py
   - hotel_room_reservation.py
   - hotel_booking.py
   - booking_validations.py
3. Enable dual-write for new transactions
4. Move all availability-dependent reads to canonical + existing room utility
5. Switch frontend reservation list/detail APIs to canonical reads
6. Switch write flows and run backfill
7. Deprecate old reservation creation paths

## Estimated Delivery Window

If one engineer handles this continuously: around 3 to 5 weeks including migration hardening.

If two engineers split backend service/migration and frontend/API cutover: around 2 to 3 weeks.

## Immediate Next Implementation Tasks

- Create new doctype: Hotel Reservation and child tables
- Add reservation domain service module with transition commands
- Add feature flags for read/write/dual-write toggles
- Add migration script for initial backfill of latest 30 days
- Add reconciliation command and report output
