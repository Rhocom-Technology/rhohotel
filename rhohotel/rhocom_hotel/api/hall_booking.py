import frappe
from frappe.utils import flt, nowdate
import math
import json


@frappe.whitelist()
def get_booking(name):
    doc = frappe.get_doc("Hall Booking", name)
    data = doc.as_dict()

    data["payment_status"] = _payment_status(doc)
    data["outstanding_amount"] = 0.0
    data["invoice_grand_total"] = 0.0
    data["invoices"] = []

    if doc.sales_invoice:
        inv = frappe.get_doc("Sales Invoice", doc.sales_invoice)
        data["invoice_grand_total"] += flt(inv.grand_total)
        data["outstanding_amount"] += flt(inv.outstanding_amount)
        data["invoices"].append({
            "type": "Original",
            "invoice": inv.name,
            "grand_total": flt(inv.grand_total),
            "outstanding_amount": flt(inv.outstanding_amount),
            "status": inv.status,
        })

    data["adjustment_history"] = []

    for r in doc.get("adjustment_history", []):
        invoice_status = None
        invoice_grand_total = 0.0
        invoice_outstanding_amount = 0.0

        if r.adjustment_invoice:
            inv = frappe.get_doc("Sales Invoice", r.adjustment_invoice)
            invoice_status = inv.status
            invoice_grand_total = flt(inv.grand_total)
            invoice_outstanding_amount = flt(inv.outstanding_amount)

            data["invoice_grand_total"] += invoice_grand_total
            data["outstanding_amount"] += invoice_outstanding_amount

        data["adjustment_history"].append({
            "previous_start": str(r.previous_start),
            "previous_end": str(r.previous_end),
            "previous_days": r.previous_days,
            "new_start": str(r.new_start),
            "new_end": str(r.new_end),
            "new_days": r.new_days,
            "adjustment_reason": r.adjustment_reason,
            "adjusted_by": r.adjusted_by,
            "adjusted_on": str(r.adjusted_on),
            "adjustment_invoice": r.adjustment_invoice,
            "invoice_status": invoice_status,
            "invoice_grand_total": invoice_grand_total,
            "invoice_outstanding_amount": invoice_outstanding_amount,
        })

    data["additional_billings"] = [
        {
            "service": r.service,
            "qty": r.qty,
            "rate": flt(r.rate),
            "amount": flt(r.amount),
            "discount_type": r.discount_type,
            "discount_amount": flt(r.discount_amount),
            "discount_value": flt(r.discount_value),
        }
        for r in doc.get("additional_billings", [])
    ]
    
    data["paid_amount"] = max(
        0,
        flt(data["invoice_grand_total"]) - flt(data["outstanding_amount"])
    )
    data["event_status"] = doc.event_status or "Scheduled"

    return data


@frappe.whitelist()
def get_booking_list():
    bookings = frappe.db.get_all(
        "Hall Booking",
        fields=[
            "name", "customer_name", "hall", "event_type",
            "start_datetime", "end_datetime", "total_days",
            "net_total", "docstatus", "sales_invoice", "mobile_number",
        ],
        order_by="start_datetime desc",
        limit=100,
    )

    for b in bookings:
        b["payment_status"] = _get_invoice_payment_status(b.get("sales_invoice"))
        b["status_label"] = _docstatus_label(b["docstatus"])

    return bookings


@frappe.whitelist()
def create_booking(data):
    if isinstance(data, str):
        data = json.loads(data)

    doc = frappe.new_doc("Hall Booking")

    doc.customer_name = data.get("customer_name")
    doc.mobile_number = data.get("mobile_number", "")
    doc.hall = data.get("hall")
    doc.event_type = data.get("event_type")
    doc.start_datetime = data.get("start_datetime")
    doc.end_datetime = data.get("end_datetime")

    doc.rate = flt(get_hall_rate(doc.hall))
    doc.discount_type = data.get("discount_type", "Percentage")
    doc.discount_amount = flt(data.get("discount_amount") or 0)

    for row in data.get("additional_billings", []):
        if row.get("service"):
            doc.append("additional_billings", {
                "service": row.get("service"),
                "qty": int(row.get("qty") or 1),
                "rate": flt(row.get("rate") or 0),
                "discount_type": row.get("discount_type") or "Fixed Amount",
                "discount_amount": flt(row.get("discount_amount") or 0),
                "discount_value": 0,
                "amount": 0,
            })

    _compute_totals(doc)

    doc.insert(ignore_permissions=True)

    if data.get("submit"):
        doc.submit()

    return {"name": doc.name, "docstatus": doc.docstatus}



@frappe.whitelist()
def update_booking(name, data):
    if isinstance(data, str):
        data = json.loads(data)

    doc = frappe.get_doc("Hall Booking", name)

    if doc.docstatus != 0:
        frappe.throw("Only draft bookings can be edited.")

    doc.customer_name = data.get("customer_name")
    doc.mobile_number = data.get("mobile_number", "")
    doc.hall = data.get("hall")
    doc.event_type = data.get("event_type")
    doc.start_datetime = data.get("start_datetime")
    doc.end_datetime = data.get("end_datetime")

    doc.rate = flt(get_hall_rate(doc.hall))
    doc.discount_type = data.get("discount_type", "Percentage")
    doc.discount_amount = flt(data.get("discount_amount") or 0)

    doc.set("additional_billings", [])

    for row in data.get("additional_billings", []):
        if row.get("service"):
            doc.append("additional_billings", {
                "service": row.get("service"),
                "qty": int(row.get("qty") or 1),
                "rate": flt(row.get("rate") or 0),
                "discount_type": row.get("discount_type") or "Fixed Amount",
                "discount_amount": flt(row.get("discount_amount") or 0),
                "discount_value": 0,
                "amount": 0,
            })

    _compute_totals(doc)

    doc.save(ignore_permissions=True)

    return {
        "name": doc.name,
        "docstatus": doc.docstatus
    }
    
     
    
@frappe.whitelist()
def submit_booking(name):
    doc = frappe.get_doc("Hall Booking", name)

    if doc.docstatus != 0:
        frappe.throw("Only draft bookings can be submitted.")

    doc.submit()

    return {
        "name": doc.name,
        "docstatus": doc.docstatus,
        "sales_invoice": doc.sales_invoice
    }


@frappe.whitelist()
def get_hall_rate(hall_name):
    if not hall_name:
        return 0
    return frappe.db.get_value("Hall", hall_name, "rate") or 0


@frappe.whitelist()
def get_services():
    return frappe.db.sql("""
        SELECT
            item_code AS name,
            item_name AS service,
            standard_rate AS rate,
            item_code AS item_name
        FROM `tabItem`
        WHERE disabled = 0
          AND item_group = 'Hall Service'
        ORDER BY item_name ASC
    """, as_dict=True)


@frappe.whitelist()
def get_payment_modes():
    return frappe.db.get_all(
        "Mode of Payment",
        filters={"enabled": 1},
        fields=["name"],
        order_by="name asc",
    )


@frappe.whitelist()
def get_halls():
    return frappe.db.get_all(
        "Hall",
        fields=["name", "hall_name", "hall_type", "capacity", "rate"],
        order_by="hall_name asc",
    )


@frappe.whitelist()
def get_customers():
    return frappe.db.get_all(
        "Customer",
        fields=["name", "customer_name", "mobile_no"],
        order_by="customer_name asc",
        limit_page_length=0,
    )


@frappe.whitelist()
def search_customers(query=""):
    query = query or ""
    like = "%{}%".format(query)

    return frappe.db.sql("""
        SELECT name, customer_name, mobile_no,email_id
        FROM `tabCustomer`
        WHERE disabled = 0
          AND (
              name LIKE %(like)s
              OR customer_name LIKE %(like)s
              OR mobile_no LIKE %(like)s
          )
        ORDER BY customer_name ASC
        LIMIT 20
    """, {"like": like}, as_dict=True)


@frappe.whitelist()
def create_customer(customer_name, mobile_no=None, email_id=None):
    if not customer_name:
        frappe.throw("Customer name is required")

    customer_name = customer_name.strip()

    if frappe.db.exists("Customer", customer_name):
        return frappe.get_doc("Customer", customer_name).as_dict()

    doc = frappe.new_doc("Customer")
    doc.customer_name = customer_name
    doc.customer_type = "Individual"
    doc.customer_group = "Individual"
    doc.territory = "Nigeria"

    if mobile_no:
        doc.mobile_no = mobile_no

    if email_id:
        doc.email_id = email_id

    doc.insert(ignore_permissions=True)

    return {
        "name": doc.name,
        "customer_name": doc.customer_name,
        "mobile_no": doc.mobile_no,
        "email_id": doc.email_id,
    }

@frappe.whitelist()
def create_hall_service(data):
    if isinstance(data, str):
        data = json.loads(data)

    service = (data.get("service") or "").strip()
    rate = flt(data.get("rate") or 0)

    if not service:
        frappe.throw("Service name is required.")

    if not frappe.db.exists("Item Group", "Hall Service"):
        frappe.throw("Item Group 'Hall Service' does not exist. Please create it first.")

    if frappe.db.exists("Item", service):
        frappe.throw("An Item with this name already exists. Please check the Item list.")

    item = frappe.new_doc("Item")
    item.item_code = service
    item.item_name = service
    item.item_group = "Hall Service"
    item.is_stock_item = 0
    item.stock_uom = "Nos"
    item.standard_rate = rate
    item.insert(ignore_permissions=True)

    return {
        "name": item.item_code,
        "service": item.item_name,
        "rate": item.standard_rate,
        "item_name": item.item_code,
    }
    
    
@frappe.whitelist()
def search_items(query=""):
    query = query or ""
    like = "%{}%".format(query)

    return frappe.db.sql("""
        SELECT item_code, item_name, standard_rate
        FROM `tabItem`
        WHERE disabled = 0
          AND item_group = 'Hall Service'
          AND (
              %(query)s = ''
              OR item_name LIKE %(like)s
              OR item_code LIKE %(like)s
          )
        ORDER BY item_name ASC
        LIMIT 20
    """, {
        "query": query,
        "like": like
    }, as_dict=True)

@frappe.whitelist()
def receive_payment(booking_name, data):
    from rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking import create_payment_entry
    return create_payment_entry(booking_name, data)


@frappe.whitelist()
def adjust_booking(
    booking_name,
    start_datetime,
    end_datetime,
    reason=None,
    discount_type=None,
    discount_amount=0,
):
    from rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking import adjust_booking_datetime

    return adjust_booking_datetime(
        booking_name,
        start_datetime,
        end_datetime,
        reason,
        discount_type,
        discount_amount,
    )


def _compute_totals(doc):
    from frappe.utils import get_datetime

    start = get_datetime(doc.start_datetime)
    end = get_datetime(doc.end_datetime)

    if end <= start:
        frappe.throw("End Date must be after Start Date.")

    doc.total_days = max(1, math.ceil((end - start).total_seconds() / 86400))
    doc.total_amount = flt(doc.rate or 0) * doc.total_days

    hall_total = flt(doc.total_amount or 0)
    hall_discount_value = flt(doc.discount_amount or 0)

    if doc.discount_type == "Percentage":
        if hall_discount_value > 100:
            frappe.throw("Hall discount percentage cannot be greater than 100%.")
        hall_discount = hall_total * (hall_discount_value / 100)
    else:
        if hall_discount_value > hall_total:
            frappe.throw("Hall discount amount cannot be greater than hall total.")
        hall_discount = hall_discount_value

    hall_net_total = max(0, hall_total - hall_discount)

    services_total = 0

    for row in doc.get("additional_billings", []):
        row.qty = flt(row.qty or 1)
        row.rate = flt(row.rate or 0)
        row.discount_type = row.discount_type or "Fixed Amount"
        row.discount_amount = flt(row.discount_amount or 0)

        gross = row.qty * row.rate

        if row.discount_type == "Percentage":
            if row.discount_amount > 100:
                frappe.throw(
                    "Discount percentage cannot be greater than 100% for service {0}."
                    .format(row.service)
                )

            row.discount_value = gross * (row.discount_amount / 100)

        else:
            if row.discount_amount > gross:
                frappe.throw(
                    "Discount amount cannot be greater than service amount for {0}."
                    .format(row.service)
                )

            row.discount_value = row.discount_amount

        row.amount = max(0, gross - flt(row.discount_value))
        services_total += flt(row.amount)

    doc.net_total = max(0, hall_net_total + services_total)
    
def _payment_status(doc):
    if doc.docstatus == 0:
        return "Draft"

    invoices = []

    if doc.sales_invoice:
        invoices.append(doc.sales_invoice)

    for row in doc.get("adjustment_history", []):
        if row.adjustment_invoice:
            invoices.append(row.adjustment_invoice)

    if not invoices:
        return "No Invoice"

    outstanding_total = 0
    grand_total = 0

    for inv_name in invoices:
        inv = frappe.get_doc("Sales Invoice", inv_name)
        if inv.docstatus == 1:
            outstanding_total += flt(inv.outstanding_amount)
            grand_total += flt(inv.grand_total)

    if outstanding_total <= 0:
        return "Paid"

    if outstanding_total < grand_total:
        return "Partial"

    return "Unpaid"


def _get_invoice_payment_status(invoice_name):
    if not invoice_name:
        return "No Invoice"

    outstanding = frappe.db.get_value("Sales Invoice", invoice_name, "outstanding_amount")

    if outstanding is None:
        return "No Invoice"

    outstanding = flt(outstanding)
    grand_total = flt(frappe.db.get_value("Sales Invoice", invoice_name, "grand_total") or 0)

    if outstanding <= 0:
        return "Paid"

    if outstanding < grand_total:
        return "Partial"

    return "Unpaid"


def _docstatus_label(docstatus):
    return {0: "Draft", 1: "Confirmed", 2: "Cancelled"}.get(docstatus, "Unknown")


@frappe.whitelist()
def create_invoice(booking_name):
    from rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking import create_invoice_for_booking
    return create_invoice_for_booking(booking_name)

@frappe.whitelist()
def update_customer_contact(customer, mobile_no=None, email_id=None):
    if not customer:
        frappe.throw("Customer is required.")

    if not frappe.db.exists("Customer", customer):
        frappe.throw("Customer does not exist.")

    doc = frappe.get_doc("Customer", customer)

    doc.mobile_no = mobile_no or ""
    doc.email_id = email_id or ""

    doc.save(ignore_permissions=True)

    return {
        "name": doc.name,
        "customer_name": doc.customer_name,
        "mobile_no": doc.mobile_no,
        "email_id": doc.email_id,
    }
    
    
@frappe.whitelist()
def mark_event_status(booking_name, event_status):
    allowed = ["Scheduled", "Completed", "No Show"]

    if event_status not in allowed:
        frappe.throw("Invalid event status.")

    booking = frappe.get_doc("Hall Booking", booking_name)

    if booking.docstatus != 1:
        frappe.throw("Only submitted bookings can be updated.")

    if event_status == "Completed":
        if not booking.sales_invoice:
            frappe.throw("This booking cannot be marked as Completed because no invoice has been created.")

        if _payment_status(booking) != "Paid":
            frappe.throw("This booking cannot be marked as Completed until all invoices are fully paid.")

    booking.event_status = event_status
    booking.flags.ignore_validate_update_after_submit = True
    booking.save(ignore_permissions=True)

    return {
        "name": booking.name,
        "event_status": booking.event_status,
    }


@frappe.whitelist()
def cancel_hall_booking(booking_name):
    booking = frappe.get_doc("Hall Booking", booking_name)

    if booking.docstatus != 1:
        frappe.throw("Only submitted bookings can be cancelled.")

    invoice_names = []

    if booking.sales_invoice:
        invoice_names.append(booking.sales_invoice)

    for row in booking.get("adjustment_history", []):
        if row.adjustment_invoice:
            invoice_names.append(row.adjustment_invoice)

    # Do not allow cancellation if any linked invoice has payment
    for inv_name in invoice_names:
        inv = frappe.get_doc("Sales Invoice", inv_name)

        if inv.docstatus == 1 and flt(inv.outstanding_amount) != flt(inv.grand_total):
            frappe.throw(
                "Cannot cancel booking because invoice {0} has payment entries. Cancel the payment first."
                .format(inv.name)
            )

    # Clear links from Hall Booking -> Sales Invoice first
    booking.sales_invoice = None

    for row in booking.get("adjustment_history", []):
        row.adjustment_invoice = None

    booking.event_status = "Cancelled"
    booking.flags.ignore_validate_update_after_submit = True
    booking.save(ignore_permissions=True)

    # Now cancel invoices after links are removed
    for inv_name in invoice_names:
        inv = frappe.get_doc("Sales Invoice", inv_name)

        if inv.docstatus == 1:
            if hasattr(inv, "custom_hall_booking"):
                inv.db_set("custom_hall_booking", None, update_modified=False)
                inv.reload()

            inv.cancel()

    booking.reload()
    booking.flags.ignore_validate_update_after_submit = True
    booking.cancel()

    return {
        "name": booking.name,
        "docstatus": booking.docstatus,
        "event_status": "Cancelled",
        "cancelled_invoices": invoice_names,
    }