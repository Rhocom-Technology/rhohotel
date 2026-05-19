<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:640px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Apply Discount</h2>
            <p class="text-xs text-gray-400 mt-1">Select an invoice then enter the discount — a credit note will be created against it</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Error -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-600">{{ error }}</p>
          </div>

          <!-- Context -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
            <p class="text-xs text-blue-700 font-semibold">{{ checkIn.guest }}</p>
            <p class="text-xs text-blue-500 mt-0.5">Room {{ checkIn.room_number }}</p>
          </div>

          <!-- Step 1: Invoice Selector -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-2">1. Select Invoice</h3>
            <div v-if="chargeableInvoices.length === 0"
              class="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
              <p class="text-xs text-yellow-700">No invoices with an outstanding balance found for this check-in.</p>
            </div>
            <div v-else class="rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="bg-gray-50 border-b border-gray-100">
                    <th class="w-8 px-3 py-2.5"></th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Invoice</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Type</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Amount</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="inv in chargeableInvoices" :key="inv.invoice"
                    class="border-b border-gray-50 last:border-0 cursor-pointer hover:bg-gray-50 transition-colors"
                    :class="selectedInvoice?.invoice === inv.invoice ? 'bg-blue-50 hover:bg-blue-50' : ''"
                    @click="selectInvoice(inv)">
                    <td class="px-3 py-2.5 text-center">
                      <div class="w-4 h-4 rounded-full border-2 mx-auto flex items-center justify-center"
                        :class="selectedInvoice?.invoice === inv.invoice ? 'border-blue-600 bg-blue-600' : 'border-gray-300'">
                        <div v-if="selectedInvoice?.invoice === inv.invoice" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                      </div>
                    </td>
                    <td class="px-3 py-2.5 text-xs font-medium text-blue-600">{{ inv.invoice }}</td>
                    <td class="px-3 py-2.5 text-xs text-gray-500">{{ formatType(inv.invoice_type) }}</td>
                    <td class="px-4 py-2.5 text-xs text-right text-gray-700">{{ fmt(inv.amount) }}</td>
                    <td class="px-4 py-2.5 text-xs text-right font-semibold text-red-500">{{ fmt(inv.outstanding_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step 2: Discount details (shown only after invoice is selected) -->
          <template v-if="selectedInvoice">
            <div>
              <h3 class="text-sm font-bold text-gray-900 mb-3">2. Discount Details</h3>

              <div class="space-y-4">
                <!-- Discount Type -->
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Discount Type <span class="text-red-400">*</span></p>
                  <select v-model="discountType"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-600">
                    <option value="fixed">Fixed Amount (₦)</option>
                    <option value="percentage">Percentage (%)</option>
                  </select>
                </div>

                <div v-if="discountType === 'fixed'">
                  <p class="text-xs text-gray-500 mb-1.5">Discount Amount (₦) <span class="text-red-400">*</span></p>
                  <input type="number" v-model.number="discountAmount" min="0.01"
                    :max="selectedInvoice.outstanding_amount" step="0.01"
                    placeholder="Enter amount"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <p class="text-xs text-gray-400 mt-1">Max: {{ fmt(selectedInvoice.outstanding_amount) }}</p>
                </div>
                <div v-else>
                  <p class="text-xs text-gray-500 mb-1.5">Discount Percentage (%) <span class="text-red-400">*</span></p>
                  <input type="number" v-model.number="discountPercent" min="0.01" max="100" step="0.01"
                    placeholder="e.g. 10"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <p v-if="discountPercent > 0" class="text-xs text-blue-600 mt-1">
                    = {{ fmt(computedDiscountAmount) }}
                  </p>
                </div>

                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reason <span class="text-red-400">*</span></p>
                  <textarea v-model="reason" rows="2"
                    placeholder="Explain why the discount is being applied"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
              </div>
            </div>

            <!-- Summary -->
            <div v-if="computedDiscountAmount > 0" class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-3 space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Invoice</span>
                <span class="text-xs font-medium text-gray-700">{{ selectedInvoice.invoice }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Current Outstanding</span>
                <span class="text-xs text-red-500 font-semibold">{{ fmt(selectedInvoice.outstanding_amount) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Discount</span>
                <span class="text-xs text-teal-600 font-semibold">− {{ fmt(computedDiscountAmount) }}</span>
              </div>
              <div class="flex items-center justify-between pt-1.5 border-t border-gray-200">
                <span class="text-xs font-bold text-gray-900">New Outstanding</span>
                <span class="text-xs font-bold"
                  :class="(selectedInvoice.outstanding_amount - computedDiscountAmount) > 0 ? 'text-red-500' : 'text-green-600'">
                  {{ fmt(Math.max(0, selectedInvoice.outstanding_amount - computedDiscountAmount)) }}
                </span>
              </div>
            </div>
          </template>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button
              :disabled="submitting || !selectedInvoice || !(computedDiscountAmount > 0) || !reason.trim()"
              @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Applying…' : 'Apply Discount' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ checkIn: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const discountType = ref('fixed')
const discountAmount = ref(0)
const discountPercent = ref(0)
const reason = ref('')
const submitting = ref(false)
const error = ref('')
const selectedInvoice = ref(null)

// Only positive, non-return invoices with remaining outstanding are valid targets
const chargeableInvoices = computed(() =>
  (props.checkIn.invoices || []).filter(inv =>
    (inv.amount || 0) > 0 && !inv.is_return && (inv.outstanding_amount || 0) > 0
  )
)

const computedDiscountAmount = computed(() => {
  const max = selectedInvoice.value?.outstanding_amount || 0
  if (discountType.value === 'percentage') {
    const pct = Number(discountPercent.value) || 0
    return Math.min(Math.round(((pct / 100) * max) * 100) / 100, max)
  }
  return Math.min(Number(discountAmount.value) || 0, max)
})

function selectInvoice(inv) {
  selectedInvoice.value = inv
  discountAmount.value = 0
  discountPercent.value = 0
}

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function formatType(type) {
  if (type === 'Sales Invoice') return 'Room Charge'
  if (type === 'POS Invoice') return 'Restaurant'
  return type || 'Room Charge'
}

async function submit() {
  if (!selectedInvoice.value || !(computedDiscountAmount.value > 0) || !reason.value.trim()) return
  submitting.value = true
  error.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.apply_discount', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
      body: new URLSearchParams({
        check_in_name: props.checkIn.name,
        discount_amount: computedDiscountAmount.value,
        reason: reason.value,
        source_invoice: selectedInvoice.value.invoice,
      }),
    })
    const data = await res.json()
    if (data.exc) {
      try {
        const msgs = JSON.parse(data._server_messages || '[]')
        error.value = JSON.parse(msgs[0]).message || 'Failed to apply discount.'
      } catch { error.value = 'Failed to apply discount.' }
      return
    }
    emit('done', data.message)
    emit('close')
  } catch {
    error.value = 'Network error. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
