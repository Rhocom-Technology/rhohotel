import frappe


PRINT_FORMAT_NAME = "Rhocom POS Thermal Receipt"


HTML = """
{% set company = frappe.get_cached_doc("Company", doc.company) if doc.company else None %}
{% set check_in = None %}
{% if doc.get("custom_hotel_room_check_in") and frappe.db.exists("Hotel Room Check In", doc.custom_hotel_room_check_in) %}
  {% set check_in = frappe.get_doc("Hotel Room Check In", doc.custom_hotel_room_check_in) %}
{% endif %}

<div class="pos-thermal-receipt">
  <div class="receipt-header">
    <div class="company-name">{{ company.company_name if company else doc.company }}</div>
    {% if company and company.tax_id %}<div>TIN: {{ company.tax_id }}</div>{% endif %}
    <div class="receipt-title">POS RECEIPT</div>
  </div>

  <div class="receipt-lines">
    <div class="row"><span>Invoice</span><span>{{ doc.name }}</span></div>
    <div class="row"><span>Date</span><span>{{ frappe.utils.format_datetime(doc.posting_date|string + " " + (doc.posting_time|string if doc.posting_time else "00:00:00"), "dd-MM-yyyy HH:mm") }}</span></div>
    {% if doc.pos_profile %}<div class="row"><span>Outlet</span><span>{{ doc.pos_profile }}</span></div>{% endif %}
    <div class="row"><span>Cashier</span><span>{{ doc.owner }}</span></div>
    <div class="row"><span>Customer</span><span>{{ doc.customer_name or doc.customer or "Walk In" }}</span></div>
    {% if check_in %}
      <div class="row"><span>Room</span><span>{{ check_in.room_number }}</span></div>
      <div class="row"><span>Check-in</span><span>{{ check_in.name }}</span></div>
    {% endif %}
  </div>

  <div class="rule"></div>

  <table class="items">
    <thead>
      <tr>
        <th class="item-name">Item</th>
        <th class="qty">Qty</th>
        <th class="amount">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for item in doc.items %}
      <tr>
        <td class="item-name">
          <div>{{ item.item_name or item.item_code }}</div>
          <div class="muted">{{ frappe.utils.fmt_money(item.rate, currency=doc.currency) }} each</div>
        </td>
        <td class="qty">{{ frappe.utils.flt(item.qty, 2) }}</td>
        <td class="amount">{{ frappe.utils.fmt_money(item.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="rule"></div>

  <div class="totals">
    <div class="row"><span>Subtotal</span><span>{{ frappe.utils.fmt_money(doc.total, currency=doc.currency) }}</span></div>
    {% if doc.discount_amount %}
      <div class="row"><span>Discount</span><span>-{{ frappe.utils.fmt_money(doc.discount_amount, currency=doc.currency) }}</span></div>
    {% endif %}
    {% if doc.total_taxes_and_charges %}
      <div class="row"><span>Taxes/Charges</span><span>{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</span></div>
    {% endif %}
    <div class="row grand"><span>Total</span><span>{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</span></div>
    {% if doc.rounded_total and doc.rounded_total != doc.grand_total %}
      <div class="row"><span>Rounded</span><span>{{ frappe.utils.fmt_money(doc.rounded_total, currency=doc.currency) }}</span></div>
    {% endif %}
    <div class="row"><span>Paid</span><span>{{ frappe.utils.fmt_money(doc.paid_amount, currency=doc.currency) }}</span></div>
    {% if doc.change_amount %}<div class="row"><span>Change</span><span>{{ frappe.utils.fmt_money(doc.change_amount, currency=doc.currency) }}</span></div>{% endif %}
    {% if doc.outstanding_amount %}<div class="row"><span>Outstanding</span><span>{{ frappe.utils.fmt_money(doc.outstanding_amount, currency=doc.currency) }}</span></div>{% endif %}
  </div>

  {% if doc.payments %}
  <div class="rule"></div>
  <div class="payments">
    <div class="section-title">Payments</div>
    {% for payment in doc.payments %}
      {% if payment.amount %}
        <div class="row"><span>{{ payment.mode_of_payment }}</span><span>{{ frappe.utils.fmt_money(payment.amount, currency=doc.currency) }}</span></div>
      {% endif %}
    {% endfor %}
  </div>
  {% endif %}

  {% if doc.remarks %}
  <div class="rule"></div>
  <div class="remarks">{{ doc.remarks }}</div>
  {% endif %}

  <div class="rule"></div>
  <div class="receipt-footer">
    <div>Thank you for your patronage.</div>
    <div>Please keep this receipt.</div>
  </div>
</div>
"""


CSS = """
@page {
  size: 58mm auto;
  margin: 1.5mm;
}

html,
body,
.print-format {
  width: 58mm;
  margin: 0;
  padding: 0 !important;
  background: #fff;
}

.pos-thermal-receipt {
  width: 48mm;
  margin: 0 auto;
  color: #000;
  font-family: "Courier New", Courier, monospace;
  font-size: 8.8px;
  line-height: 1.18;
}

.receipt-header,
.receipt-footer {
  text-align: center;
}

.company-name {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
}

.receipt-title,
.section-title {
  font-weight: 700;
  text-transform: uppercase;
  margin-top: 3px;
}

.receipt-lines,
.totals,
.payments {
  margin-top: 4px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  break-inside: avoid;
}

.row span:first-child {
  flex: 0 0 auto;
}

.row span:last-child {
  text-align: right;
  overflow-wrap: anywhere;
}

.rule {
  border-top: 1px dashed #000;
  margin: 4px 0;
}

.items {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.items th,
.items td {
  padding: 1.5px 0;
  vertical-align: top;
}

.items th {
  border-bottom: 1px solid #000;
  font-weight: 700;
}

.item-name {
  width: 48%;
  text-align: left;
  overflow-wrap: anywhere;
}

.qty {
  width: 14%;
  text-align: center;
}

.amount {
  width: 38%;
  text-align: right;
}

.muted,
.remarks {
  font-size: 8px;
}

.grand {
  font-size: 10px;
  font-weight: 700;
  border-top: 1px solid #000;
  border-bottom: 1px solid #000;
  padding: 2px 0;
  margin-top: 2px;
}

@media print {
  html,
  body,
  .print-format {
    width: 58mm;
  }

  .pos-thermal-receipt {
    width: 48mm;
  }
}
"""


def execute():
    values = {
        "doctype": "Print Format",
        "name": PRINT_FORMAT_NAME,
        "doc_type": "POS Invoice",
        "module": "Rhocom Hotel",
        "standard": "Yes",
        "custom_format": 1,
        "print_format_type": "Jinja",
        "print_format_builder": 0,
        "disabled": 0,
        "raw_printing": 0,
        "html": HTML,
        "css": CSS,
    }

    if frappe.db.exists("Print Format", PRINT_FORMAT_NAME):
        print_format = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
        print_format.update(values)
        print_format.save(ignore_permissions=True)
    else:
        frappe.get_doc(values).insert(ignore_permissions=True)

    if frappe.db.has_column("POS Profile", "print_format"):
      for profile in frappe.get_all("POS Profile", fields=["name", "print_format"]):
        if not profile.get("print_format"):
          frappe.db.set_value(
            "POS Profile",
            profile.name,
            "print_format",
            PRINT_FORMAT_NAME,
            update_modified=False,
          )

    frappe.db.commit()