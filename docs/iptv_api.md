# IPTV Integration API — Developer Reference

## Overview

The IPTV Integration API allows in-room IPTV systems to:

- Display a personalised welcome message with guest name and stay dates.
- Show the guest's current bill (folio) broken down by charge category.
- Present an interactive room service menu grouped by category.
- Browse named restaurant menus with location-specific pricing.
- Accept and submit room service orders chargeable to the guest folio.

All endpoints are Frappe whitelisted methods exposed over HTTP.  
No session cookie or Frappe user authentication is required — instead, a
shared API key header is used for all requests.

---

## Base URL

```
https://<your-frappe-site>/api/method/rhohotel.rhocom_hotel.api.iptv.<method_name>
```

Replace `<your-frappe-site>` with your actual site domain, e.g. `carlton.rhocom.ng`.

---

## Authentication

Every request **must** include the following HTTP header:

```
X-IPTV-API-Key: <your-configured-key>
```

### Configuring the API Key

1. Open **Hotel Settings** in your Frappe/ERPNext instance.
2. Scroll to the **IPTV Integration** section.
3. Enter a strong random key in the **IPTV API Key** field (minimum 32 characters recommended).
4. Save.

The key is stored encrypted in the database.  
**Never hardcode the key in IPTV firmware or shared config files.** Use your IPTV vendor's secure credential storage.

### Unauthorized Response

If the header is missing, the key does not match, or the key has not been
configured in Hotel Settings, the response is:

```json
{
  "success": false,
  "error": "Unauthorized"
}
```

HTTP status will be 200 (Frappe limitation) — always check `success` first.

> **Configuration note:** If the IPTV API Key field in Hotel Settings is empty,
> or if server-side key decryption fails, every request returns `Unauthorized`
> and an error is written to the Frappe error log. Check the log first when
> debugging authentication problems.

---

## Response Envelope

All responses use the same JSON envelope:

**Success:**
```json
{
  "success": true,
  "data": { }
}
```

**Business/validation error:**
```json
{
  "success": false,
  "error": "Readable error message"
}
```

Stack traces are never returned to IPTV clients.

---

## Endpoints

### 1. Get Guest by Room Number

Retrieve guest information for the currently checked-in guest in a room.

| Property | Value |
|---|---|
| Method name | `get_guest_by_room` |
| HTTP methods | GET, POST |
| URL | `/api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_by_room` |

#### Request Parameters

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `room_number` | string | Yes | max 20 characters | Hotel room number (e.g. `"101"`) |

#### Successful Response

```json
{
  "success": true,
  "data": {
    "guest_name": "John Smith",
    "check_in_date": "2026-06-17",
    "check_out_date": "2026-06-20",
    "room_number": "101",
    "room_type": "Deluxe Room",
    "booking_id": "HOTEL-RESERVATION-00045"
  }
}
```

#### No Active Guest

```json
{
  "success": false,
  "error": "No active guest found for this room"
}
```

> **Implementation note:** Only guests with a **submitted** (`docstatus = 1`)
> Hotel Room Check In in status `Checked In` are considered active. Draft
> check-ins are excluded.

#### curl Example

```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_by_room" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{"room_number": "101"}'
```

---

### 2. Get Guest Folio (Current Bill)

Retrieve the current bill for the guest in a room, broken down by charge category.

| Property | Value |
|---|---|
| Method name | `get_guest_folio` |
| HTTP methods | GET, POST |
| URL | `/api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_folio` |

#### Request Parameters

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `room_number` | string | Yes | max 20 characters | Hotel room number |

#### Successful Response

```json
{
  "success": true,
  "data": {
    "guest_name": "John Smith",
    "room_number": "101",
    "currency": "NGN",
    "accommodation_charges": 150000.00,
    "restaurant_charges": 25000.00,
    "laundry_charges": 10000.00,
    "other_charges": 5000.00,
    "total_charges": 190000.00,
    "total_paid": 100000.00,
    "outstanding_balance": 90000.00
  }
}
```

#### Notes

- Only **submitted** (posted) invoices are included. Cancelled invoices are excluded.
- Charges are grouped by item category:
  - **accommodation** — room rate invoices.
  - **restaurant** — invoices whose items belong to Food / Drinks / Kitchen item groups.
  - **laundry** — invoices whose items belong to Laundry item group.
  - **other** — all remaining charges.
- `outstanding_balance = total_charges - total_paid`.

#### curl Example

```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_guest_folio" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{"room_number": "101"}'
```

---

### 3. Place Room Service Order

Submit a room service order from the IPTV system, chargeable to the guest folio.

| Property | Value |
|---|---|
| Method name | `place_room_service_order` |
| HTTP methods | **POST only** |
| URL | `/api/method/rhohotel.rhocom_hotel.api.iptv.place_room_service_order` |

#### Request Body

```json
{
  "room_number": "101",
  "items": [
    {
      "item_code": "MENU-ITEM-00001",
      "qty": 2
    },
    {
      "item_code": "MENU-ITEM-00002",
      "qty": 1
    }
  ],
  "special_request": "Please deliver quickly, no pepper on sandwich"
}
```

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `room_number` | string | Yes | max 20 characters | Room number of the guest |
| `items` | array | Yes | 1 – 30 items | List of items to order |
| `items[].item_code` | string | Yes | must be a valid `Menu Item` name | Menu Item identifier (from `get_room_service_menu`) |
| `items[].qty` | number | Yes | > 0 | Quantity |
| `special_request` | string | No | max 500 characters, HTML stripped | Free-text delivery instructions |

> **Important:** Item prices are always fetched from the server.
> Any `rate` value sent by the IPTV client is silently ignored.
> HTML tags in `special_request` are stripped before the value is stored.

#### Successful Response

```json
{
  "success": true,
  "data": {
    "order_id": "RES-ORD-00021",
    "status": "Confirmed",
    "room_number": "101",
    "guest_name": "John Smith",
    "total_amount": 12000.00,
    "created_at": "2026-06-17 14:32:10.123456"
  }
}
```

#### Error Examples

```json
{ "success": false, "error": "room_number is too long" }
{ "success": false, "error": "items must be a list" }
{ "success": false, "error": "items list is required and cannot be empty" }
{ "success": false, "error": "Order cannot exceed 30 items" }
{ "success": false, "error": "qty must be greater than 0 for item 'MENU-ITEM-00001'" }
{ "success": false, "error": "Menu item 'INVALID-CODE' not found or unavailable" }
{ "success": false, "error": "No active guest found for this room" }
```

#### curl Example

```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.place_room_service_order" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "room_number": "101",
    "items": [
      {"item_code": "MENU-ITEM-00001", "qty": 2},
      {"item_code": "MENU-ITEM-00002", "qty": 1}
    ],
    "special_request": "Extra napkins please"
  }'
```

---

### 4. Get Room Service Menu

Retrieve available menu items grouped by category. Optionally filter by a single category.

| Property | Value |
|---|---|
| Method name | `get_room_service_menu` |
| HTTP methods | GET, POST |
| URL | `/api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu` |

#### Request Parameters (optional)

| Field | Type | Required | Description |
|---|---|---|---|
| `category` | string | No | Filter by item group name (case-insensitive). Omit for all categories. |

#### Successful Response

```json
{
  "success": true,
  "data": {
    "currency": "NGN",
    "categories": [
      {
        "category": "Food",
        "items": [
          {
            "item_code": "MENU-ITEM-00001",
            "item_name": "Chicken Sandwich",
            "description": "Grilled chicken sandwich with fries",
            "price": 5000.00,
            "available": true,
            "image": "/files/chicken-sandwich.jpg"
          }
        ]
      },
      {
        "category": "Drinks",
        "items": [
          {
            "item_code": "MENU-ITEM-00002",
            "item_name": "Orange Juice",
            "description": "Fresh orange juice",
            "price": 2000.00,
            "available": true,
            "image": "/files/orange-juice.jpg"
          }
        ]
      }
    ]
  }
}
```

#### Notes

- Only `Menu Item` records with a **linked, enabled ERPNext `Item`** are returned.
  Menu items that are not linked to an ERPNext Item are excluded.
- `item_code` values returned here are the `Menu Item` document names — use them
  verbatim as `item_code` when placing orders.
- `image` is a relative path; prepend `https://<your-site>` to get the full URL.
- Category is derived from the linked `Item.item_group` field.

#### curl Examples

**All items:**
```bash
curl -X GET "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE"
```

**Filter by category:**
```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{"category": "Food"}'
```

---

### 5. Get Restaurant Menus

Retrieve named restaurant menus with their items and location-specific prices.

| Property | Value |
|---|---|
| Method name | `get_restaurant_menu` |
| HTTP methods | GET, POST |
| URL | `/api/method/rhohotel.rhocom_hotel.api.iptv.get_restaurant_menu` |

#### Difference from `get_room_service_menu`

| | `get_room_service_menu` | `get_restaurant_menu` |
|---|---|---|
| Source DocType | `Menu Item` | `Restaurant Menu` → `Restaurant Menu Item` → `Menu Item` |
| Structure | Flat items grouped by item_group | Named menus per location |
| Pricing | Global `Menu Item.rate` | Per-menu rate override; falls back to `Menu Item.rate` |
| Use case | Room service ordering from IPTV | Restaurant / bar / pool menu browsing |

#### Request Parameters (all optional)

| Field | Type | Constraints | Description |
|---|---|---|---|
| `menu_name` | string | max 140 characters | Filter to a single named menu (exact match). |
| `location` | string | max 140 characters | Filter by restaurant location (case-insensitive). |

Omit both parameters to return all menus.

#### Successful Response

```json
{
  "success": true,
  "data": {
    "currency": "NGN",
    "menus": [
      {
        "menu_name": "Breakfast Menu",
        "location": "Main Restaurant",
        "items": [
          {
            "item_code": "MENU-ITEM-00001",
            "item_name": "Full English Breakfast",
            "description": "Eggs, bacon, toast, and beans",
            "category": "Food",
            "price": 4500.00,
            "available": true,
            "image": "/files/full-english.jpg"
          }
        ]
      },
      {
        "menu_name": "Pool Bar Menu",
        "location": "Pool Bar",
        "items": [
          {
            "item_code": "MENU-ITEM-00007",
            "item_name": "Club Sandwich",
            "description": "",
            "category": "Food",
            "price": 3500.00,
            "available": true,
            "image": ""
          }
        ]
      }
    ]
  }
}
```

#### Rate Precedence

Each item's `price` is resolved as follows:

1. **`Restaurant Menu Item.rate`** — if this is greater than `0`, it is used (allows the Pool Bar to charge a different price from the Main Restaurant for the same item).
2. **`Menu Item.rate`** — global base rate used as a fallback when the menu-specific rate is `0` or unset.

#### Notes

- Only items whose linked ERPNext `Item` is enabled (`disabled = 0`) are returned.
- Items where the `Menu Item` has no linked ERPNext `Item` are excluded.
- `item_code` values are `Menu Item` document names — use them as `item_code` in `place_room_service_order`.
- `image` is a relative path; prepend `https://<your-site>` for the full URL.

#### curl Examples

**All menus:**
```bash
curl -X GET "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_restaurant_menu" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE"
```

**Filter by menu name:**
```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_restaurant_menu" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{"menu_name": "Breakfast Menu"}'
```

**Filter by location:**
```bash
curl -X POST "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_restaurant_menu" \
  -H "Content-Type: application/json" \
  -H "X-IPTV-API-Key: YOUR_API_KEY_HERE" \
  -d '{"location": "Pool Bar"}'
```

---

## Recommended IPTV Integration Flow

```
1. On channel change or room TV power-on:
   └── GET /get_guest_by_room  →  Display "Welcome, John Smith"

2. Show interactive main menu:
   ├── "Room Service" button:
   │   ├── GET /get_room_service_menu   →  Display all items grouped by category
   │   │   OR
   │   ├── GET /get_restaurant_menu    →  Display named menus (e.g. "Breakfast Menu")
   │   └── Guest selects items, confirms order
   │       └── POST /place_room_service_order  →  Show order confirmation
   │
   └── "My Bill" button:
       └── GET /get_guest_folio  →  Display itemised bill
```

**Which menu endpoint to use?**

- Use `get_room_service_menu` for a simple flat item list grouped by category (item group).
- Use `get_restaurant_menu` when the hotel runs separate named menus per outlet
  (e.g. Breakfast Menu, Pool Bar Menu, Room Service Menu) with potentially different prices per location.

---

## Error Response Reference

| `error` value | Affected endpoints | Cause |
|---|---|---|
| `"Unauthorized"` | All | Missing, wrong, or unconfigured `X-IPTV-API-Key`; or server-side key decryption failure |
| `"room_number is required"` | 1, 2, 3 | Request body missing `room_number` |
| `"room_number is too long"` | 1, 2, 3 | `room_number` exceeds 20 characters |
| `"No active guest found for this room"` | 1, 2, 3 | Room is vacant, guest has checked out, or check-in is not submitted |
| `"items must be a list"` | 3 | `items` field is not a JSON array |
| `"items list is required and cannot be empty"` | 3 | `items` is an empty array |
| `"Order cannot exceed 30 items"` | 3 | More than 30 line items sent in one order |
| `"item_code is required for item at position N"` | 3 | Missing `item_code` in one of the order lines |
| `"qty must be greater than 0 for item '...'"` | 3 | Zero or negative quantity |
| `"Menu item '...' not found or unavailable"` | 3 | `item_code` does not match any `Menu Item` record |
| `"Failed to create order. Please try again."` | 3 | Database error during order creation (see Frappe error log) |
| `"This endpoint requires POST"` | 3 | GET request sent to `place_room_service_order` |
| `"menu_name filter is too long"` | 5 | `menu_name` filter exceeds 140 characters |
| `"location filter is too long"` | 5 | `location` filter exceeds 140 characters |

---

## Security Notes

1. **HTTPS only.** Never deploy this API over plain HTTP. The API key is transmitted in every request header.
2. **Rotate the API key** periodically and whenever IPTV hardware is decommissioned or compromised.
3. **PII protection.** Guest email, phone number, ID document, address, and payment card details are never returned by any IPTV endpoint.
4. **Rate limiting.** Consider adding a reverse-proxy rate limit (e.g. nginx `limit_req`) to prevent brute-force key guessing from within the hotel network.
5. **Hotel network isolation.** IPTV systems should only reach the hotel server on the internal network — do not expose IPTV endpoints to the public internet if avoidable.
6. **Key length.** Use a random key of at least 32 characters (e.g. `openssl rand -hex 32`).
7. **Input limits enforced server-side.** `room_number` is capped at 20 characters, `special_request` at 500 characters, and a single order may not exceed 30 line items. These limits exist to prevent abuse from the hotel network.
8. **XSS prevention.** `special_request` is HTML-stripped before being stored as a comment. Do not render comment content as raw HTML in any UI without additional sanitisation.
9. **Timing-safe key comparison.** The API key is compared using `hmac.compare_digest` to prevent timing-based key enumeration attacks.
10. **Server-side pricing.** Item rates are always fetched from `Menu Item` on the server. Any `rate` value in the order request is ignored.

---

## Testing with curl / Postman

### Generate a test key

```bash
openssl rand -hex 32
# Example output: a3f9b1c2d4e5f6071819202122232425262728293031323334353637383940
```

### Set the key in Hotel Settings

Navigate to **Hotel Settings → IPTV Integration → IPTV API Key** and paste the key.

### Postman setup

1. Create a new collection.
2. Add collection variable `iptv_key` = your key.
3. Add header `X-IPTV-API-Key: {{iptv_key}}` to each request.
4. Set Content-Type to `application/json`.

### Verify authentication works

```bash
# Should return Unauthorized
curl -X GET "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu"

# Should return menu or empty categories list
curl -X GET "https://hotel.example.com/api/method/rhohotel.rhocom_hotel.api.iptv.get_room_service_menu" \
  -H "X-IPTV-API-Key: YOUR_KEY"
```

---

## DocType Mapping

| IPTV Concept | Frappe/ERPNext DocType | Key field(s) |
|---|---|---|
| Active in-house guest | `Hotel Room Check In` | `status = 'Checked In'`, `docstatus = 1` |
| Guest display name | `Hotel Guest` | `hotel_guest_name` |
| Booking/reservation | `Hotel Reservation` | linked via `canonical_reservation` on check-in |
| Room | `Hotel Room` | `name` is the room identifier |
| Room type display name | `Hotel Room Type` | `room_type` (Data field) |
| Guest bill charges | `Sales Invoice` | linked via `Hotel Room Check In Invoice` child table; `docstatus = 1` only |
| Menu categories | `Item Group` | via `Item.item_group` on the linked ERPNext Item |
| Menu items | `Menu Item` | must have a linked, enabled `Item` (`disabled = 0`) |
| Room service order | `Restaurant Order` | `order_type = 'Room Service'` |
| Order line | `Restaurant Order Item` | child table of `Restaurant Order` |

---

*Generated for rhohotel — Rhocom Technology Ltd.*
