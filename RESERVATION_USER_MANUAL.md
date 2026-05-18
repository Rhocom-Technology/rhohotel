# Rhohotel – Reservation Module User Manual

**Version:** 2.0 (May 2026)  
**Applies to:** Front Desk, Reservations, Hotel Manager roles

---

## Table of Contents

1. [Overview of Reservation Types](#1-overview-of-reservation-types)
2. [Creating a New Reservation](#2-creating-a-new-reservation)
   - 2.1 [Individual Reservation](#21-individual-reservation)
   - 2.2 [Corporate Reservation](#22-corporate-reservation)
   - 2.3 [Group Reservation](#23-group-reservation)
   - 2.4 [OTA Reservation](#24-ota-reservation)
   - 2.5 [House Use Reservation](#25-house-use-reservation)
   - 2.6 [Complimentary Reservation](#26-complimentary-reservation)
3. [Rooms & Pricing Panel](#3-rooms--pricing-panel)
   - 3.1 [Selecting a Rate Code](#31-selecting-a-rate-code)
   - 3.2 [Adding Rooms](#32-adding-rooms)
   - 3.3 [Applying a Discount](#33-applying-a-discount)
4. [Saving and Submitting a Reservation](#4-saving-and-submitting-a-reservation)
5. [Viewing a Saved Reservation](#5-viewing-a-saved-reservation)
   - 5.1 [Reservation Header & Status](#51-reservation-header--status)
   - 5.2 [Financial Summary](#52-financial-summary)
   - 5.3 [Reserved Rooms Table](#53-reserved-rooms-table)
   - 5.4 [Group Room Blocks Panel](#54-group-room-blocks-panel)
   - 5.5 [OTA Details Panel](#55-ota-details-panel)
   - 5.6 [House Use / Complimentary Details Panel](#56-house-use--complimentary-details-panel)
6. [Check-In Workflow](#6-check-in-workflow)
7. [Billing Routing](#7-billing-routing)
8. [Managing Rate Codes](#8-managing-rate-codes)
   - 8.1 [What is a Rate Code?](#81-what-is-a-rate-code)
   - 8.2 [Adding a New Rate Code](#82-adding-a-new-rate-code)
   - 8.3 [Rate Code Field Reference](#83-rate-code-field-reference)
   - 8.4 [Common Rate Code Examples](#84-common-rate-code-examples)
   - 8.5 [Setting a Default Rate](#85-setting-a-default-rate)
   - 8.6 [Deactivating a Rate Code](#86-deactivating-a-rate-code)
9. [Billing Routing Rules](#9-billing-routing-rules)
10. [Tips & Troubleshooting](#10-tips--troubleshooting)

---

## 1. Overview of Reservation Types

The system supports six reservation types. Each type unlocks a dedicated details panel and controls how billing is routed.

| Type | Typical Use | Billing Default |
|------|-------------|-----------------|
| **Individual** | Walk-in or direct guest booking | Guest pays own folio |
| **Corporate** | Guest linked to a company account | Corporate customer billed |
| **Group** | Wedding parties, tour groups, conferences | Central (master payer) or Split per room |
| **OTA** | Booking.com, Expedia, Airbnb, etc. | Hotel Collect or OTA Collect/Prepaid |
| **House Use** | Staff rooms, showrooms, maintenance | Internal cost centre (zero revenue) |
| **Complimentary** | Gifted nights, loyalty awards | Internal cost centre (zero revenue) |

---

## 2. Creating a New Reservation

From the **Front Desk** dashboard, click **New Reservation** (or the equivalent button in the Reservations page).

### 2.1 Individual Reservation

1. **Reservation Type** → select **Individual**.
2. Fill in **Arrival Date** and **Departure Date**. The **Nights** counter updates automatically.
3. Under **Guest / Booker**, select an existing guest from the dropdown or click **+ New Guest** to create one.
4. Fill in **Guest/Contact Name**, **Contact Phone**, and **Contact Email** as needed.
5. Proceed to the **Rooms & Pricing** panel (see [Section 3](#3-rooms--pricing-panel)).

### 2.2 Corporate Reservation

1. **Reservation Type** → select **Corporate**.
2. Fill in arrival and departure dates.
3. Under **Guest / Booker**, use the **Corporate Guest** dropdown to select a guest who is linked to a company.
4. The system will route billing to the corporate account automatically.
5. Choose a corporate-eligible rate code in the **Rooms & Pricing** panel.

### 2.3 Group Reservation

1. **Reservation Type** → select **Group**.
2. Fill in arrival and departure dates.
3. The amber **Group Details** panel appears:
   - **Group Name** – descriptive label (e.g. *Dangote Wedding Party*).
   - **Billing Mode** – choose:
     - **Central** – all room charges consolidated to a single master payer. A **Master Payer (Customer)** field appears; enter the company or individual footing the bill.
     - **Split** – each room's guest pays individually.
4. Under **Rooms & Pricing**, use the **Room Blocks** sub-table (visible after you add rooms) to allocate room type quotas. Each block row holds:
   - Room Type, Quantity blocked, Rate Code.
   - The **Picked Up** and **Remaining** columns are auto-maintained as individual rooms are assigned.
5. Add individual rooms as usual; the system validates against the block quotas.

### 2.4 OTA Reservation

1. **Reservation Type** → select **OTA**.
2. Fill in arrival and departure dates.
3. The purple **OTA Details** panel appears:
   - **OTA Channel** – select the channel (e.g. *Booking.com*, *Expedia*). Channels are maintained in the OTA Channel master list.
   - **Collection Model** – choose:
     - **Hotel Collect** – the hotel charges the guest's card on arrival.
     - **OTA Collect / Prepaid** – the OTA collects payment. A **Virtual Card Reference** field appears; enter the virtual card number provided by the OTA.
   - **Commission Amount (₦)** – enter the OTA commission to be tracked.
4. Choose an OTA-channel-eligible rate code in the **Rooms & Pricing** panel. Rate codes that do not have **OTA** channel enabled will not appear in the dropdown.

### 2.5 House Use Reservation

1. **Reservation Type** → select **House Use**.
2. Fill in arrival and departure dates.
3. The green **House Use Details** panel appears:
   - **Reason / Authorisation** *(required)* – briefly state who authorised the room and for what purpose (e.g. *GM approval – maintenance team inspection*).
   - **Cost Centre** – enter the department cost centre code. This is used for internal accounting.
4. Add rooms in the **Rooms & Pricing** panel. Room charges are posted to the cost centre; no guest folio is generated.

> **Note:** The system automatically computes a **Theoretical Revenue** figure for reporting purposes, even though no guest is billed.

### 2.6 Complimentary Reservation

1. **Reservation Type** → select **Complimentary**.
2. The workflow is identical to House Use:
   - **Reason / Authorisation** is mandatory.
   - **Cost Centre** is recommended for tracking.
3. Complimentary reservations generate a zero-charge folio and track the foregone revenue as theoretical income.

---

## 3. Rooms & Pricing Panel

This panel is present for all reservation types and is where rooms and rates are assigned.

### 3.1 Selecting a Rate Code

| Field | Purpose |
|-------|---------|
| **Rate Code** dropdown | Filters to rates that are active, within their validity dates, and eligible for the chosen booking channel (e.g. Front Desk, OTA, Corporate). Displays as `CODE – Rate Type Name`. Leave blank to use the room's default rate. |

When you change the rate code, the following happen automatically:
- The **rate per night** for each room in the table is updated.
- The **Meal Plan** column is pre-filled from the rate's Meal Plan setting.
- The **Cancellation Policy** is snapshotted onto each room row (visible in the saved reservation).

### 3.2 Adding Rooms

1. Optionally filter by **Room Type** to narrow the available rooms list.
2. Click the **Available Rooms** search box. A dropdown lists all vacant rooms for the chosen dates.
3. Click one or more room numbers to select them (checkmarks appear). Use the search box to filter by room number.
4. Click **Add Room**. Selected rooms appear in the rooms table below, showing: Room, Type, Rate Code, Meal Plan, Rate/Night, Nights, Total.
5. To remove a room, click the **×** button in its table row.

### 3.3 Applying a Discount

| Field | Behaviour |
|-------|-----------|
| **Discount Type** | `None`, `Percentage`, or `Fixed Amount` |
| **Discount** | Numeric value. For Percentage, enter `10` for 10%. For Fixed Amount, enter the ₦ value. |

The discount is applied to the reservation subtotal. The **Grand Total** and **Balance** recalculate live.

---

## 4. Saving and Submitting a Reservation

| Button | Effect |
|--------|--------|
| **Save Draft** | Saves a Draft (docstatus = 0). Rooms are soft-held but the reservation is not yet confirmed. |
| **Submit** | Submits the reservation (docstatus = 1). Rooms are firmly reserved. The reservation appears in the Front Desk room view as **Confirmed**. |
| **Cancel** | Available from the saved reservation view. Releases all rooms back to availability. |

> **Tip:** Always **Submit** before directing a guest to their room. A Draft reservation does not lock the room against double-booking in the same way.

---

## 5. Viewing a Saved Reservation

Open any reservation from the Reservations list or the Front Desk room view.

### 5.1 Reservation Header & Status

The header shows:
- **Reservation number** (e.g. `RES-2026-00042`)
- **Status badge** – Draft / Confirmed / Checked In / Checked Out / Cancelled
- **Type badge** – the reservation type in blue
- **Guest name, arrival, departure, nights**

Action buttons available:
| Button | When Visible | Effect |
|--------|-------------|--------|
| **Submit Reservation** | Status = Draft | Confirms the reservation |
| **Receive Payment** | Always | Opens payment modal |
| **Adjust Reservation** | Always | Modify dates or room rate |
| **Change Room** | Always | Reassign to a different room |
| **Create Invoice** | Submitted, no invoice yet | Generates a Sales Invoice |
| **Check In Guest** | Submitted | Opens check-in screen |
| **Cancel Reservation** | Always | Voids the reservation |
| **Print** | Always | Opens print/confirmation slip |

### 5.2 Financial Summary

A five-column summary bar shows:
- **Subtotal** – sum of all room totals before discount
- **Discount** – ₦ amount deducted
- **Grand Total** – net payable
- **Linked Payment** – payment entry reference if already settled
- **Balance** – outstanding amount

### 5.3 Reserved Rooms Table

Columns: Room · Type · Rate / Plan · Guest · Rate/Night · Total · Actions

- **Rate / Plan** column shows two coloured badges: the **Rate Code** (blue) and the **Meal Plan** (green), both snapshotted at booking time.
- **Guest** column contains an inline guest selector to assign a specific occupant per room (useful for Group reservations).
- **Actions** column shows a **Check In** button for each room, or a **Checked In** badge once the guest is checked in.

### 5.4 Group Room Blocks Panel

Visible only for **Group** reservations that have room blocks defined.

Shows group metadata (group name, billing mode, master payer) and a block allocation table:

| Column | Meaning |
|--------|---------|
| Room Type | The category blocked for the group |
| Blocked | Total rooms reserved for the group in that category |
| Picked Up | Rooms that have been individually assigned so far |
| Remaining | Blocked minus Picked Up; highlighted amber if > 0 |
| Rate Code | The negotiated rate for that block |

### 5.5 OTA Details Panel

Visible only for **OTA** reservations. Displays the channel, collection model, commission amount, and virtual card reference in a read-only summary.

### 5.6 House Use / Complimentary Details Panel

Visible only for **House Use** or **Complimentary** reservations. Displays the authorisation reason, cost centre, and theoretical room revenue foregone.

---

## 6. Check-In Workflow

1. From the saved reservation, click **Check In Guest** (or individual room's **Check In** button).
2. The system opens the Check-In screen pre-filled with the reservation details.
3. The check-in record is automatically linked back to the reservation via the **Canonical Reservation** field — this ensures subsequent POS bills are routed to the correct payer.
4. After check-in, the room view badge changes from **Confirmed** to **Checked In**.

**Bulk Check In** (Group reservations only): When multiple rooms on a group reservation are all in Confirmed status, a **Bulk Check In** button appears at the top of the Reserved Rooms table to check in all rooms simultaneously.

---

## 7. Billing Routing

When a charge is posted to a room (restaurant bill, bar tab, etc.), the system automatically determines who pays using the **Billing Routing Engine**.

The engine evaluates **Hotel Billing Routing Rule** documents in priority order and returns the first matching rule.

| Reservation Type | Default Payer |
|-----------------|---------------|
| Individual | Guest's own customer account |
| Corporate | Corporate customer on the reservation |
| Group (Central) | Group Master Customer |
| Group (Split) | Individual guest per room |
| OTA (Hotel Collect) | Guest's customer account |
| OTA (OTA Collect/Prepaid) | OTA Virtual Card / account |
| House Use | Internal Cost Centre (no revenue) |
| Complimentary | Internal Cost Centre (no revenue) |

Custom rules can be added in **Hotel Billing Routing Rule** to override defaults for specific corporate customers, OTA channels, or charge categories. See [Section 9](#9-billing-routing-rules).

---

## 8. Managing Rate Codes

### 8.1 What is a Rate Code?

A **Rate Code** is a short alphanumeric identifier for a pricing plan (e.g. `BAR`, `CORP-ACME`, `WKD-PKG`). Each rate code stores:
- The nightly rate or pricing basis
- Which booking channels can use it
- Meal plan inclusions
- Stay restrictions (min/max nights, validity dates)
- Cancellation policy terms

When a rate code is selected during reservation, its meal plan and cancellation policy are **snapshotted** onto each room row. This means future changes to the rate code do not alter confirmed bookings.

### 8.2 Adding a New Rate Code

> **Required Role:** System Manager or Hotel Manager

**Path:** ERPNext → Rhocom Hotel → Hotel Room Rate → New

1. Navigate to **Rhocom Hotel → Hotel Room Rate** in the ERPNext sidebar.
2. Click **New**.
3. Fill in the fields (see the reference table below).
4. Click **Save**.

The new rate code becomes immediately available in the reservation form's Rate Code dropdown, subject to its channel eligibility and validity dates.

### 8.3 Rate Code Field Reference

#### Identity

| Field | Required | Description |
|-------|----------|-------------|
| **Rate Code** | Yes | Short unique code (e.g. `BAR`, `CORP-ACME`). Used for lookups and snapshots. |
| **Rate Type** | Yes | Human-readable category name (e.g. *Best Available Rate*, *Weekend Package*). Shown on folios and reports. |
| **Description** | No | Brief note for front-desk reference. |
| **Market Segment** | No | One of: BAR, Corporate, OTA, Government, Weekend, Promo, Negotiated, House Use, Complimentary. Used for revenue analysis. |
| **Charge Plan** | No | `Daily` (per night) or `Hourly`. Default: Daily. |
| **Default Rate** | No | If checked, this rate is the fallback for its market segment when no specific code is chosen. |
| **Active** | No | Only active rates are offered during reservation creation. Default: on. |

#### Stay Restrictions *(collapsible)*

| Field | Description |
|-------|-------------|
| **Minimum Stay (Nights)** | Fewest nights a guest must book to use this rate. `0` = no minimum. |
| **Maximum Stay (Nights)** | Most nights allowed at this rate. `0` = no maximum. |
| **Valid From** | First date the rate is applicable. Blank = no start restriction. |
| **Valid To** | Last date the rate is applicable. Blank = no end restriction. |

#### Inclusions & Policy *(collapsible)*

| Field | Description |
|-------|-------------|
| **Meal Plan** | Meals included: Room Only, Bed & Breakfast, Half Board, Full Board. Snapshotted on reservations. |
| **Cancellation Policy** | Free-text terms, e.g. *Free cancellation up to 24 h before arrival; 1-night penalty thereafter.* Snapshotted on reservations. |

#### Channel Eligibility *(collapsible)*

Controls which booking channels can offer this rate. **All unchecked = no channel restrictions (rate is available everywhere).**

| Field | Default | Meaning |
|-------|---------|---------|
| **Front Desk** | On | Available for staff-initiated and walk-in bookings |
| **Corporate** | On | Available for corporate account reservations |
| **OTA** | Off | Loadable by online travel agencies |
| **Walk In** | On | Available for same-day walk-in bookings |

> **Important:** If you create an OTA-specific rate (e.g. `OTA-NET`), enable **OTA** and disable **Front Desk** / **Walk In** so the rate only appears in OTA reservation forms.

### 8.4 Common Rate Code Examples

| Rate Code | Rate Type | Market Segment | Meal Plan | Channels |
|-----------|-----------|---------------|-----------|---------|
| `BAR` | Best Available Rate | BAR | Room Only | Front Desk, Walk In |
| `BB-STD` | Bed & Breakfast Standard | BAR | Bed & Breakfast | Front Desk, Walk In |
| `CORP-ACME` | ACME Corp Negotiated | Corporate | Room Only | Front Desk, Corporate |
| `OTA-NET` | OTA Net Rate | OTA | Room Only | OTA |
| `WKD-PKG` | Weekend Getaway Package | Weekend | Half Board | Front Desk, Walk In |
| `GOV-FED` | Federal Government Rate | Government | Room Only | Front Desk, Corporate |
| `COMP` | Complimentary | Complimentary | Full Board | Front Desk |
| `HU-MAINT` | House Use – Maintenance | House Use | Room Only | Front Desk |

### 8.5 Setting a Default Rate

When a reservation is created without choosing a specific rate code (the dropdown is left at *"Default rate"*), the system uses the room type's built-in nightly rate. If you want a specific rate code to serve as the segment fallback instead:

1. Open the rate code in **Hotel Room Rate**.
2. Check **Default Rate**.
3. Save.

Only one rate per market segment should be marked as default to avoid ambiguity.

### 8.6 Deactivating a Rate Code

To stop a rate from appearing in new reservations without deleting it:

1. Open the rate code in **Hotel Room Rate**.
2. Uncheck **Active**.
3. Save.

Historical reservations that were booked under this rate are unaffected — the rate code and meal plan are already snapshotted on the room rows.

---

## 9. Billing Routing Rules

**Path:** ERPNext → Rhocom Hotel → Hotel Billing Routing Rule → New

Routing rules let you override default billing behaviour for specific scenarios.

| Field | Description |
|-------|-------------|
| **Reservation Type** | Blank = applies to all types; or select one specific type |
| **Charge Category** | Blank = all charge types; or select Room / Restaurant / Bar / etc. |
| **Payer** | Who pays: Guest, Corporate Account, Group Master, OTA Virtual Card, Internal (Cost Centre) |
| **Priority** | Lower number = evaluated first |
| **Corporate Customer** | Narrow the rule to one specific corporate account |
| **OTA Channel** | Narrow the rule to one specific OTA |
| **Is Active** | Uncheck to temporarily disable a rule without deleting it |

**Example:** Route all restaurant charges for *Booking.com* reservations to the OTA's virtual card:

| Field | Value |
|-------|-------|
| Reservation Type | OTA |
| Charge Category | Restaurant |
| OTA Channel | Booking.com |
| Payer | OTA Virtual Card |
| Priority | 10 |

---

## 10. Tips & Troubleshooting

**Rate code not appearing in the dropdown**
- Check that **Active** is on and today's date is within the **Valid From / Valid To** range.
- Verify that the correct **Channel Eligibility** checkbox is enabled for the reservation type you are creating (e.g. OTA checkbox for OTA reservations).

**Room not appearing in the Available Rooms dropdown**
- The room may already be reserved for the selected date range. Check the Room View on the Front Desk dashboard.
- If the room is part of a Group block for another group reservation, it may be protected. Adjust the block quantity or re-assign dates.

**Theoretical Revenue showing ₦0 on House Use / Complimentary**
- Ensure the room has a nightly rate configured in its Room Type master. Theoretical revenue is derived from the standard rate even though no guest is charged.

**OTA commission not appearing on reports**
- Enter the commission amount in the **Commission Amount (₦)** field on the OTA Details panel before submitting the reservation.

**Meal plan missing on reservation room rows**
- The meal plan is snapshotted at the time rooms are added. If you change the rate code after adding rooms, remove and re-add the rooms to trigger a fresh snapshot.

**Cancellation policy not visible on printed confirmation**
- Confirm that a **Cancellation Policy** text has been entered on the selected Rate Code in Hotel Room Rate.

---

*For technical issues, contact your system administrator or the Rhocom Technology support team.*
