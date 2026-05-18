<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:720px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2 mb-1.5 flex-wrap">
              <h2 class="text-2xl font-bold text-gray-900">{{ paymentId }}</h2>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="typeBadge">{{ typeLabel }}</span>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="statusBadge">
                {{ payment ? (payment.docstatus === 1 ? 'Submitted' : 'Draft') : '—' }}
              </span>
            </div>
            <p class="text-xs text-gray-400">{{ payment?.party_name || payment?.party || '—' }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Loading -->
          <div v-if="loading" class="py-12 text-center">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p class="text-xs text-gray-400">Loading payment…</p>
          </div>

          <template v-else-if="payment">

            <!-- Header Info -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-400 mb-1">Posting Date</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ payment.posting_date || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Mode of Payment</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ payment.mode_of_payment || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Party</p>
                <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg truncate">{{ payment.party_name || payment.party || '—' }}</div>
              </div>
              <div v-if="payment.reference_no">
                <p class="text-xs text-gray-400 mb-1">Reference No</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ payment.reference_no }}</div>
              </div>
              <div v-if="payment.reference_date">
                <p class="text-xs text-gray-400 mb-1">Reference Date</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ payment.reference_date }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Paid From</p>
                <div class="px-3 py-2.5 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-lg truncate">{{ payment.paid_from || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Paid To</p>
                <div class="px-3 py-2.5 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-lg truncate">{{ payment.paid_to || '—' }}</div>
              </div>
            </div>

            <!-- Invoice References -->
            <div v-if="payment.references && payment.references.length">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Applied To</h3>
              <div class="rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="bg-gray-50 border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Document Type</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Reference</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Allocated</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(ref, idx) in payment.references" :key="idx"
                      class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3 text-xs text-gray-500">{{ ref.reference_doctype || '—' }}</td>
                      <td class="px-4 py-3 text-xs font-medium text-blue-600">{{ ref.reference_name || '—' }}</td>
                      <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">{{ fmt(ref.allocated_amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Totals Summary -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Paid Amount</span>
                <span class="text-xs text-gray-700">{{ fmt(payment.paid_amount) }}</span>
              </div>
              <div v-if="payment.received_amount && payment.received_amount !== payment.paid_amount" class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Received Amount</span>
                <span class="text-xs text-gray-700">{{ fmt(payment.received_amount) }}</span>
              </div>
              <div class="flex items-center justify-between pt-2 border-t border-gray-200">
                <span class="text-xs font-bold text-gray-900">Total</span>
                <span class="text-xs font-bold" :class="payment.payment_type === 'Receive' ? 'text-green-600' : 'text-orange-500'">
                  {{ fmt(payment.paid_amount) }}
                </span>
              </div>
            </div>

            <!-- Remarks -->
            <div v-if="payment.remarks">
              <p class="text-xs text-gray-400 mb-1.5">Remarks</p>
              <div class="px-4 py-3 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-xl">{{ payment.remarks }}</div>
            </div>

          </template>

          <!-- Error -->
          <div v-else class="py-12 text-center">
            <p class="text-sm text-gray-400">Could not load payment details.</p>
          </div>

        </div>

        <div class="px-8 pb-6 flex justify-end">
          <button @click="$emit('close')"
            class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  paymentId: { type: String, required: true },
  paymentType: { type: String, default: 'Receive' },
})
defineEmits(['close'])

const payment = ref(null)
const loading = ref(true)

const typeLabel = computed(() =>
  props.paymentType === 'Receive' ? 'Receipt' : (props.paymentType || 'Payment')
)
const typeBadge = computed(() =>
  props.paymentType === 'Receive'
    ? 'bg-green-50 text-green-600 border-green-200'
    : 'bg-orange-50 text-orange-600 border-orange-200'
)
const statusBadge = computed(() => {
  if (!payment.value) return 'bg-gray-50 text-gray-500 border-gray-200'
  return payment.value.docstatus === 1
    ? 'bg-green-50 text-green-600 border-green-200'
    : 'bg-yellow-50 text-yellow-600 border-yellow-200'
})

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

async function loadPayment() {
  loading.value = true
  try {
    const r = await fetch(
      `/api/method/frappe.client.get?doctype=Payment%20Entry&name=${encodeURIComponent(props.paymentId)}`,
      { headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' } }
    )
    const data = await r.json()
    payment.value = data.message || null
  } catch {
    payment.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadPayment)
</script>
