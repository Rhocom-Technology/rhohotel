<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:900px;max-height:92vh;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Stay Adjustment</h2>
            <p class="text-xs text-gray-400 mt-1">Extend or reduce stay and optionally apply a discount on adjusted days</p>
          </div>
          <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3">
            <p class="text-xs font-bold text-red-600 mb-1">Error</p>
            <p class="text-xs text-red-500">{{ error }}</p>
          </div>

          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">Current Stay</p>
            <p class="text-xs text-blue-600">{{ checkIn.guest }} • Room {{ checkIn.room_number }} • {{ checkIn.number_of_nights }} nights • Checkout {{ fmtDt(checkIn.expected_check_out_datetime) }}</p>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div class="space-y-5">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Adjustment Setup</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Check-in</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtDt(checkIn.check_in_datetime) }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Current Nights</p>
                    <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.number_of_nights }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Current Checkout</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtDt(checkIn.expected_check_out_datetime) }}</div>
                  </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">New Checkout Date/Time <span class="text-red-400">*</span></p>
                    <input type="datetime-local" v-model="newCheckout"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">New Nights</p>
                    <div class="px-3 py-2.5 text-xs font-bold bg-gray-50 border border-gray-200 rounded-lg"
                      :class="newNights > checkIn.number_of_nights ? 'text-green-600' : newNights < checkIn.number_of_nights ? 'text-red-500' : 'text-gray-700'">{{ newNights || '—' }}</div>
                  </div>
                </div>
              </div>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Discount on Adjusted Days</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
                    <select v-model="discountType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option value="None">None</option>
                      <option value="Percentage">Percentage</option>
                      <option value="Fixed Amount">Fixed Amount</option>
                    </select>
                  </div>
                  <div v-if="discountType !== 'None'">
                    <p class="text-xs text-gray-500 mb-1.5">{{ discountType === 'Percentage' ? 'Discount %' : 'Discount Amount (₦)' }}</p>
                    <input type="number" v-model.number="newDiscount" min="0"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <p class="text-xs font-bold text-blue-700 mb-3">Adjustment Preview</p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                  <div class="text-xs text-gray-600">Current nights: {{ checkIn.number_of_nights }}</div>
                  <div class="text-xs font-bold" :class="newNights > checkIn.number_of_nights ? 'text-green-600' : 'text-red-500'">New nights: {{ newNights || '—' }}</div>
                  <div class="text-xs text-gray-600">Rate/night: {{ fmt(checkIn.rate_amount) }}</div>
                  <div class="text-xs font-bold text-gray-900">Type: {{ adjustmentType }}</div>
                </div>
              </div>
              <div v-if="adjustmentType === 'Extension'" class="bg-green-50 rounded-xl border border-green-200 px-5 py-4">
                <p class="text-xs font-bold text-green-700 mb-1">Extension</p>
                <p class="text-xs text-green-600">A new invoice will be created for the additional {{ newNights - checkIn.number_of_nights }} night(s).</p>
              </div>
              <div v-else-if="adjustmentType === 'Reduction'" class="bg-yellow-50 rounded-xl border border-yellow-200 px-5 py-4">
                <p class="text-xs font-bold text-yellow-700 mb-1">Reduction</p>
                <p class="text-xs text-yellow-600">A credit note will be created for {{ checkIn.number_of_nights - newNights }} reduced night(s). Select the invoice below to link it for proper reconciliation.</p>
              </div>
              <div v-if="adjustmentType === 'Reduction'" class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-xs font-bold text-gray-900 mb-1">Link to Invoice <span class="text-gray-400 font-normal">(recommended)</span></h3>
                <p class="text-xs text-gray-400 mb-2.5">Select the invoice the credit note should reconcile against.</p>
                <div v-if="chargeableInvoices.length === 0" class="bg-yellow-50 border border-yellow-100 rounded-lg px-3 py-2.5">
                  <p class="text-xs text-yellow-700">No invoices with outstanding balance available.</p>
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
                      <tr v-for="inv in chargeableInvoices" :key="inv.invoice"
                        class="border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
                        :class="selectedInvoice?.invoice === inv.invoice ? 'bg-blue-50 hover:bg-blue-50' : 'hover:bg-gray-50'"
                        @click="selectedInvoice = inv">
                        <td class="px-2 py-2.5 text-center">
                          <div class="w-3.5 h-3.5 rounded-full border-2 mx-auto flex items-center justify-center"
                            :class="selectedInvoice?.invoice === inv.invoice ? 'border-blue-600 bg-blue-600' : 'border-gray-300'">
                            <div v-if="selectedInvoice?.invoice === inv.invoice" class="w-1 h-1 rounded-full bg-white"></div>
                          </div>
                        </td>
                        <td class="px-2 py-2.5 text-xs font-medium text-blue-600">{{ inv.invoice }}</td>
                        <td class="px-3 py-2.5 text-xs text-right font-semibold text-red-500">{{ fmt(inv.outstanding_amount) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
                <p class="text-xs font-bold text-blue-700 mb-1">Note</p>
                <p class="text-xs text-blue-600">Stay continuity and existing invoices are preserved. Only the adjustment difference is invoiced.</p>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50" @click="$emit('close')">Cancel</button>
            <button :disabled="submitting || !newCheckout || adjustmentType === 'Same'" @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Applying…' : 'Apply Stay Adjustment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { callMethodForm } from '@/lib/api'
const props = defineProps({ checkIn: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])
const newCheckout = ref('')
const defaultCheckoutTime = ref('12:00')
const discountType = ref('None')
const newDiscount = ref(0)
const submitting = ref(false)
const error = ref('')
const selectedInvoice = ref(null)
const chargeableInvoices = computed(() =>
  (props.checkIn.invoices || []).filter(inv =>
    (inv.amount || 0) > 0 && !inv.is_return && (inv.outstanding_amount || 0) > 0
  )
)
function fmt(v) { return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00' }
function fmtDt(dt) { if (!dt) return '—'; return new Date(dt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }
const newNights = computed(() => {
  if (!newCheckout.value || !props.checkIn.check_in_datetime) return 0
  // Use date-only diff (same as backend date_diff) to avoid time-of-day rounding errors
  const ciDate = new Date(props.checkIn.check_in_datetime)
  const coDate = new Date(newCheckout.value)
  const ciDay = new Date(ciDate.getFullYear(), ciDate.getMonth(), ciDate.getDate())
  const coDay = new Date(coDate.getFullYear(), coDate.getMonth(), coDate.getDate())
  return Math.max(0, Math.round((coDay - ciDay) / 86400000))
})
const adjustmentType = computed(() => {
  if (!newNights.value) return 'Same'
  if (newNights.value > props.checkIn.number_of_nights) return 'Extension'
  if (newNights.value < props.checkIn.number_of_nights) return 'Reduction'
  return 'Same'
})

onMounted(async () => {
  await fetchDefaultCheckoutTime()
  newCheckout.value = applyDefaultTime(props.checkIn.expected_check_out_datetime)
})

async function fetchDefaultCheckoutTime() {
  try {
    const serverTime = await callMethodForm(
      'rhohotel.rhocom_hotel.doctype.hotel_settings.hotel_settings.get_default_check_out_time',
      {},
    )
    const normalized = normalizeServerTime(serverTime)
    if (normalized) defaultCheckoutTime.value = normalized
  } catch {
    // Keep fallback time when settings fetch fails
  }
}

function applyDefaultTime(value) {
  const datePart = asISODate(value)
  if (!datePart) return ''
  return `${datePart}T${defaultCheckoutTime.value}`
}

function asISODate(value) {
  if (!value) return ''
  const cleaned = String(value).trim().replace(' ', 'T')
  return cleaned.slice(0, 10)
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

async function submit() {
  if (!newCheckout.value || adjustmentType.value === 'Same') return
  submitting.value = true; error.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.adjust_stay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({
        check_in_name: props.checkIn.name,
        new_checkout: newCheckout.value.replace('T', ' ') + ':00',
        discount_type: discountType.value,
        new_discount: discountType.value !== 'None' ? newDiscount.value : 0,
        ...(adjustmentType.value === 'Reduction' && selectedInvoice.value ? { source_invoice: selectedInvoice.value.invoice } : {}),
      })
    })
    const data = await res.json()
    if (data.exc) {
      try { error.value = JSON.parse(JSON.parse(data._server_messages || '[]')[0]).message } catch { error.value = 'Adjustment failed.' }
      return
    }
    emit('done', data.message); emit('close')
  } catch { error.value = 'Network error.' } finally { submitting.value = false }
}
</script>
