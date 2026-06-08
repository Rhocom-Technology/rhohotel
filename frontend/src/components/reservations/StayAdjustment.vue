<template>
  <div class="p-6">

    <!-- Header -->
    <div class="flex items-start justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Stay Adjustment</h2>
        <p class="text-xs text-gray-400 mt-1">Adjust stay dates, nights, room continuity, and billing effect while preserving the standard reservation layout.</p>
      </div>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
    </div>

    <!-- Reservation Snapshot -->
    <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6">
      <h3 class="text-xs font-bold text-gray-900 mb-3">Reservation Snapshot</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
        <div>
          <p class="text-xs text-gray-400 mb-1">Reservation ID</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.name }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Guest</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.primary_guest_name || reservation.customer || '—' }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Current Stay</p>
          <p class="text-sm font-bold text-gray-900">{{ formatDate(reservation.from_date) }} → {{ formatDate(reservation.to_date) }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Current Room</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.room_number || 'Pending assignment' }}</p>
        </div>
      </div>
    </div>

    <!-- Invoice Status Banner -->
    <div v-if="reservation.sales_invoice" class="mb-5 rounded-xl border px-5 py-4"
      :class="invoiceIsPaid ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs font-bold" :class="invoiceIsPaid ? 'text-green-700' : 'text-amber-700'">
          Invoice {{ reservation.sales_invoice }} —
          <span v-if="invoiceIsPaid">Fully/Partially Paid (₦{{ Number(invoicePaidAmount).toLocaleString('en-NG', { minimumFractionDigits: 2 }) }} paid)</span>
          <span v-else>Unpaid</span>
        </span>
      </div>
      <p class="text-xs" :class="invoiceIsPaid ? 'text-green-600' : 'text-amber-600'">
        <span v-if="totalImpact > 0.01">After applying this adjustment, an <strong>additional charge invoice</strong> of {{ formatCurrency(totalImpact) }} will be created to cover the extended stay.</span>
        <span v-else-if="totalImpact < -0.01">After applying this adjustment, a <strong>credit note</strong> will be created for the reduced stay amount.</span>
        <span v-else>The invoice total matches the new stay amount — no invoice change required.</span>
      </p>
    </div>

    <!-- Invoice Adjust Result -->
    <div v-if="invoiceResult" class="mb-5 rounded-xl border px-5 py-4"
      :class="invoiceResult.status === 'cancelled_and_recreated' || invoiceResult.status === 'recreated' || invoiceResult.status === 'adjustment_created' || invoiceResult.status === 'credit_note_created' ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'">
      <p class="text-xs font-bold mb-1"
        :class="['cancelled_and_recreated','recreated','adjustment_created','credit_note_created'].includes(invoiceResult.status) ? 'text-green-700' : 'text-gray-700'">
        Invoice Update: {{ invoiceResultLabel }}
      </p>
      <p v-if="invoiceResult.sales_invoice" class="text-xs text-green-600">New invoice created: <strong>{{ invoiceResult.sales_invoice }}</strong></p>
      <p v-if="invoiceResult.cancelled_invoice" class="text-xs text-gray-500">Previous invoice cancelled: {{ invoiceResult.cancelled_invoice }}</p>
      <p v-if="invoiceResult.adjustment_invoice" class="text-xs text-green-600">Adjustment invoice created: <strong>{{ invoiceResult.adjustment_invoice }}</strong> ({{ formatCurrency(invoiceResult.difference) }})</p>
      <p v-if="invoiceResult.credit_note" class="text-xs text-green-600">Credit note created: <strong>{{ invoiceResult.credit_note }}</strong> ({{ formatCurrency(Math.abs(invoiceResult.difference)) }})</p>
      <p v-if="invoiceResult.message" class="text-xs text-gray-600">{{ invoiceResult.message }}</p>
    </div>

    <!-- Body -->
      <div v-if="reservation.docstatus !== 1" class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-xs text-yellow-700">
        ⚠️ This reservation must be submitted before adjusting the stay.
      </div>
      <div v-else style="display:grid;grid-template-columns:1fr 320px;gap:24px;">

      <!-- Left: Adjustment Details -->
      <div>
        <h3 class="text-sm font-bold text-gray-900 mb-4">Adjustment Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Adjustment Type</p>
            <select v-model="adjustmentType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
              <option>Extend Stay</option>
              <option>Reduce Stay</option>
              <option>Change Dates</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Adjustment Reason</p>
            <select v-model="adjustmentReason" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
              <option>Guest Request</option>
              <option>Hotel Request</option>
              <option>Operational</option>
            </select>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-in Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDate(reservation.from_date) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-out Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDate(reservation.to_date) }}</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">New Check-in Date/Time</p>
            <input v-model="newCheckinDate" type="datetime-local"
              class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">New Check-out Date/Time</p>
            <input v-model="newCheckoutDate" type="datetime-local"
              :min="minCheckoutDate"
              class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Additional Nights</p>
            <div class="flex items-center gap-2">
              <div class="flex-1 px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ additionalNights }}</div>
              <span class="text-xs text-blue-500 cursor-pointer">Auto Calculated</span>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Preferred Room Option</p>
          <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
            <option>Keep Current Room ({{ reservation.room_number || 'Pending assignment' }})</option>
            <option>Request New Room</option>
          </select>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Adjustment Notes</p>
          <textarea v-model="adjustmentNotes" rows="3"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Guest requested extension due to delayed travel plan."></textarea>
          <p class="text-xs text-gray-400 mt-1">This note will appear in the reservation activity timeline and audit history.</p>
        </div>


        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
          <select v-model="discountType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
            <option value="Percentage">Percentage (%)</option>
            <option value="Fixed Amount">Fixed Amount</option>
          </select>
        </div>
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Discount Value</p>
          <input v-model.number="discountValue" type="number" min="0" step="0.01"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="discountType === 'Percentage' ? 'e.g. 10 for 10%' : 'e.g. 5000'" />
          <p class="text-xs text-gray-400 mt-1.5">{{ discountHelpText }}</p>
        </div>

        <p class="text-xs text-gray-400 mt-4 pt-4 border-t border-gray-100">
          Updating the stay will recalculate reservation totals, occupancy, room availability, and activity history.
        </p>
      </div>

      <!-- Right: Rate Impact & Controls -->
      <div class="space-y-4">

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Rate Impact</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Current Rate / Night</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(ratePerNight) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Extra Nights</span>
              <span class="text-xs font-semibold text-gray-900">{{ additionalNights }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Additional Room Charges</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatSignedCurrency(subtotalImpact) }}</span>
            </div>
            <div v-if="discountImpact !== 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Discount Impact</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatSignedCurrency(-discountImpact) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Taxes & Fees</span>
              <span class="text-xs font-semibold text-gray-900">₦0</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Current Net Total</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(currentNetTotal) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">New Net Total</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(newNetTotal) }}</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">New Balance Impact</span>
              <span class="text-xs font-bold text-gray-900">{{ formatSignedCurrency(totalImpact) }}</span>
            </div>
          </div>
          <div class="mt-2">
            <span class="px-2.5 py-1 text-xs font-medium bg-yellow-50 text-yellow-600 rounded-full">Pending Payment</span>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-2">Availability Check</h4>
          <span class="px-2.5 py-1 text-xs font-semibold bg-green-100 text-green-600 rounded-full">Available</span>
          <p class="text-xs text-gray-400 mt-2">Current room remains available for the selected extension period.</p>
        </div>

        <div v-if="isCreditAdjustment" class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-1">Link Credit Note To Invoice</h4>
          <p class="text-xs text-gray-400 mb-3">Select the invoice this reduction should reconcile against.</p>
          <div v-if="chargeableInvoices.length === 0" class="bg-yellow-50 border border-yellow-100 rounded-lg px-3 py-2.5">
            <p class="text-xs text-yellow-700">No submitted charge invoice found for this reservation.</p>
          </div>
          <div v-else class="rounded-xl border border-gray-200 overflow-hidden">
            <table class="w-full">
              <thead>
                <tr class="bg-gray-50 border-b border-gray-100">
                  <th class="w-6 px-2 py-2"></th>
                  <th class="text-left text-xs font-medium text-gray-500 px-2 py-2">Invoice</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Outstanding</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="inv in chargeableInvoices"
                  :key="inv.name"
                  class="border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
                  :class="selectedInvoice?.name === inv.name ? 'bg-blue-50 hover:bg-blue-50' : 'hover:bg-gray-50'"
                  @click="selectedInvoice = inv"
                >
                  <td class="px-2 py-2.5 text-center">
                    <div
                      class="w-3.5 h-3.5 rounded-full border-2 mx-auto flex items-center justify-center"
                      :class="selectedInvoice?.name === inv.name ? 'border-blue-600 bg-blue-600' : 'border-gray-300'"
                    >
                      <div v-if="selectedInvoice?.name === inv.name" class="w-1 h-1 rounded-full bg-white"></div>
                    </div>
                  </td>
                  <td class="px-2 py-2.5 text-xs font-medium text-blue-600">{{ inv.name }}</td>
                  <td class="px-3 py-2.5 text-xs text-right font-semibold text-red-500">{{ formatCurrency(inv.outstanding_amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-2">Approval & Audit</h4>
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Adjusted by</span>
            <span class="text-xs font-semibold text-gray-900">Front Desk Admin</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
      <div v-if="errorMsg" class="flex-1 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{{ errorMsg }}</div>
      <button @click="$emit('close')" class="px-5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
      <button :disabled="submitting || !canApply" @click="apply"
        class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">
        {{ submitting ? 'Applying…' : (reservation.sales_invoice ? 'Apply & Update Invoice' : 'Apply Stay Adjustment') }}
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const props = defineProps({ reservation: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const adjustmentType = ref('Extend Stay')
const adjustmentReason = ref('Guest Request')
const defaultCheckoutTime = ref('12:00')
const newCheckoutDate = ref(asDateTimeLocal(props.reservation.to_date))
const newCheckinDate = ref(asDateTimeLocal(props.reservation.from_date))
const discountType = ref(props.reservation.discount_type || 'Percentage')
const discountValue = ref(Number(props.reservation.discount || 0))
const adjustmentNotes = ref('')
const submitting = ref(false)
const errorMsg = ref('')
const selectedInvoice = ref(null)

// Invoice status
const invoiceGrandTotal = ref(0)
const invoiceOutstanding = ref(0)
const invoiceResult = ref(null)

const invoicePaidAmount = computed(() => invoiceGrandTotal.value - invoiceOutstanding.value)
const invoiceIsPaid = computed(() => invoicePaidAmount.value > 0.01)
const isSplitGroup = computed(() => {
  const reservationType = String(props.reservation?.reservation_type || '').trim().toLowerCase()
  const billingMode = String(props.reservation?.group_billing_mode || '').trim().toLowerCase()
  return reservationType === 'group' && billingMode.startsWith('split')
})
const discountHelpText = computed(() => {
  if (!isSplitGroup.value) {
    return 'This discount is applied to the adjusted reservation total before the adjustment invoice is created.'
  }
  if (discountType.value === 'Fixed Amount') {
    return 'For split billing, a fixed discount is divided equally across the new room adjustment invoices.'
  }
  return 'For split billing, a percentage discount is applied according to each room adjustment value.'
})

const invoiceResultLabel = computed(() => {
  if (!invoiceResult.value) return ''
  const map = {
    cancelled_and_recreated: 'Previous invoice cancelled — new invoice created',
    recreated: 'Invoice recreated with updated amount',
    adjustment_created: 'Adjustment invoice created for extension charge',
    credit_note_created: 'Credit note created for reduced stay',
    no_change: 'No invoice change needed',
    no_invoice: 'No invoice was linked',
  }
  return map[invoiceResult.value.status] || invoiceResult.value.status
})

async function fetchInvoiceStatus() {
  if (!props.reservation.sales_invoice) return
  try {
    const inv = await callMethodForm('frappe.client.get_value', {
      doctype: 'Sales Invoice',
      filters: { name: props.reservation.sales_invoice },
      fieldname: JSON.stringify(['grand_total', 'outstanding_amount']),
    })
    if (inv) {
      invoiceGrandTotal.value = parseFloat(inv.grand_total || 0)
      invoiceOutstanding.value = parseFloat(inv.outstanding_amount || 0)
    }
  } catch { /* ignore — display fallback */ }
}

onMounted(() => {
  fetchInvoiceStatus()
  fetchDefaultCheckoutTime()
})

async function fetchDefaultCheckoutTime() {
  try {
    const serverTime = await callMethodForm(
      'rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings.get_default_check_out_time',
      {},
    )
    const normalized = normalizeServerTime(serverTime)
    if (normalized) {
      defaultCheckoutTime.value = normalized
      newCheckinDate.value = applyTimeToDate(newCheckinDate.value, normalized)
      newCheckoutDate.value = applyTimeToDate(newCheckoutDate.value, normalized)
    }
  } catch {
    // Fall back to local default when settings are unavailable
    newCheckinDate.value = applyTimeToDate(newCheckinDate.value, defaultCheckoutTime.value)
    newCheckoutDate.value = applyTimeToDate(newCheckoutDate.value, defaultCheckoutTime.value)
  }
}

// Earliest valid checkout: one day after check-in
const minCheckoutDate = computed(() => {
  if (!newCheckinDate.value) return ''
  const d = parseDateOnly(newCheckinDate.value)
  d.setDate(d.getDate() + 1)
  return `${formatISODate(d)}T${defaultCheckoutTime.value}`
})

// Correct rate per night: subtotal / number_of_nights
const ratePerNight = computed(() => {
  const nights = Number(props.reservation.number_of_nights) || 1
  return Number(props.reservation.subtotal || 0) / nights
})

const currentNights = computed(() => {
  const fromDate = asISODate(props.reservation.from_date)
  const toDate = asISODate(props.reservation.to_date)
  if (!fromDate || !toDate) return Number(props.reservation.number_of_nights) || 0
  return Math.max(1, Math.round((parseDateOnly(toDate) - parseDateOnly(fromDate)) / (1000 * 60 * 60 * 24)))
})

const newNights = computed(() => {
  if (!newCheckinDate.value || !newCheckoutDate.value) return 0
  return Math.max(1, Math.round((parseDateOnly(newCheckoutDate.value) - parseDateOnly(newCheckinDate.value)) / (1000 * 60 * 60 * 24)))
})

const additionalNights = computed(() => {
  if (!newCheckinDate.value || !newCheckoutDate.value) return 0
  return newNights.value - currentNights.value
})

const currentSubtotalAmount = computed(() => Number(props.reservation.subtotal || (ratePerNight.value * currentNights.value) || 0))
const currentDiscountAmount = computed(() => Number(props.reservation.discount_amount || 0))
const currentNetTotal = computed(() => Number(props.reservation.total_amount || (currentSubtotalAmount.value - currentDiscountAmount.value) || 0))

const newSubtotalAmount = computed(() => {
  if (newNights.value < 1) return 0
  return Number(ratePerNight.value || 0) * newNights.value
})

const computedNewDiscountAmount = computed(() => {
  // Calculate new discount based on type and value
  if (discountType.value === 'Percentage') {
    const pct = Math.min(Math.max(Number(discountValue.value) || 0, 0), 100)
    return round2(newSubtotalAmount.value * pct / 100)
  } else if (discountType.value === 'Fixed Amount') {
    return Math.min(Number(discountValue.value) || 0, newSubtotalAmount.value)
  }
  return 0
})

const newNetTotal = computed(() => round2(Math.max(0, Number(newSubtotalAmount.value || 0) - Number(computedNewDiscountAmount.value || 0))))
const totalImpact = computed(() => round2(newNetTotal.value - currentNetTotal.value))
const subtotalImpact = computed(() => round2(newSubtotalAmount.value - currentSubtotalAmount.value))
const discountImpact = computed(() => round2(computedNewDiscountAmount.value - currentDiscountAmount.value))
const isCreditAdjustment = computed(() => totalImpact.value < -0.01)
const chargeableInvoices = computed(() => {
  const rows = Array.isArray(props.reservation.reservation_invoices)
    ? props.reservation.reservation_invoices
    : Array.isArray(props.reservation.linked_invoices)
      ? props.reservation.linked_invoices
      : []
  return rows
    .map((row) => ({
      name: row?.name || row?.invoice || '',
      outstanding_amount: Number(row?.outstanding_amount || 0),
      grand_total: Number(row?.grand_total ?? row?.amount ?? 0),
      is_return: Number(row?.is_return || 0),
      status: row?.status || '',
    }))
    .filter((row) => row.name && !row.is_return && row.grand_total > 0 && row.outstanding_amount > 0)
})

const hasDateChanges = computed(() => {
  return (
    newCheckinDate.value !== asISODate(props.reservation.from_date) ||
    newCheckoutDate.value !== asISODate(props.reservation.to_date)
  )
})

const isRangeValid = computed(() => {
  if (!newCheckinDate.value || !newCheckoutDate.value) return false
  return parseDateOnly(newCheckoutDate.value) > parseDateOnly(newCheckinDate.value)
})

const canApply = computed(() => hasDateChanges.value && isRangeValid.value)

watch(
  [chargeableInvoices, isCreditAdjustment],
  () => {
    if (!isCreditAdjustment.value || chargeableInvoices.value.length === 0) {
      selectedInvoice.value = null
      return
    }
    if (!selectedInvoice.value || !chargeableInvoices.value.some((row) => row.name === selectedInvoice.value?.name)) {
      selectedInvoice.value = chargeableInvoices.value[0]
    }
  },
  { immediate: true },
)

async function apply() {
  if (!canApply.value) return
  submitting.value = true; errorMsg.value = ''; invoiceResult.value = null
  try {
    const params = {
      reservation_name: props.reservation.name,
      new_check_in: asISODate(newCheckinDate.value),
      new_checkout: asISODate(newCheckoutDate.value),
      new_discount_type: discountType.value,
      new_discount: discountValue.value,
      ...(isCreditAdjustment.value && selectedInvoice.value ? { source_invoice: selectedInvoice.value.name } : {}),
    }
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.adjust_reservation',
      params,
    )
    invoiceResult.value = result?.invoice_adjustment || null

    emit('done'); emit('close')
  } catch (error) {
    errorMsg.value = String(error?.message || 'Adjustment failed.')
  } finally { submitting.value = false }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function formatSignedCurrency(amount) {
  const value = Number(amount || 0)
  if (value === 0) return '₦0.00'
  const sign = value > 0 ? '+' : '-'
  return `${sign}${formatCurrency(Math.abs(value))}`
}

function asISODate(value) {
  if (!value) return ''
  if (typeof value === 'string') return value.slice(0, 10)
  return formatISODate(value)
}

function asDateTimeLocal(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    const cleaned = value.trim().replace(' ', 'T')
    if (cleaned.includes('T')) return cleaned.slice(0, 16)
    return `${cleaned.slice(0, 10)}T${defaultCheckoutTime.value}`
  }
  return `${formatISODate(value)}T${defaultCheckoutTime.value}`
}

function applyTimeToDate(value, hhmm) {
  if (!value) return ''
  return `${asISODate(value)}T${hhmm}`
}

function normalizeServerTime(value) {
  if (!value) return ''
  const text = String(value).trim()
  const parts = text.split(':')
  if (parts.length < 2) return ''
  const hh = String(parts[0]).padStart(2, '0')
  const mm = String(parts[1]).padStart(2, '0')
  return `${hh}:${mm}`
}

function parseDateOnly(value) {
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(year, (month || 1) - 1, day || 1)
}

function formatISODate(value) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function round2(value) {
  return Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100
}
</script>
