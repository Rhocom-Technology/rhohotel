<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:780px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2 mb-1.5 flex-wrap">
              <h2 class="text-2xl font-bold text-gray-900">{{ invoiceName }}</h2>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="typeBadge">{{ typeLabel }}</span>
              <span v-if="invoice" class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="statusBadge">
                {{ invoice.status || '—' }}
              </span>
            </div>
            <p class="text-xs text-gray-400">{{ invoice?.customer || '—' }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Loading -->
          <div v-if="loading" class="py-12 text-center">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p class="text-xs text-gray-400">Loading invoice…</p>
          </div>

          <template v-else-if="invoice">

            <!-- Header Info -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-400 mb-1">Posting Date</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ invoice.posting_date || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Due Date</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ invoice.due_date || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Customer</p>
                <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg truncate">{{ invoice.customer || '—' }}</div>
              </div>
            </div>

            <!-- Line Items -->
            <div>
              <h3 class="text-sm font-bold text-gray-900 mb-3">Items</h3>
              <div class="rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="bg-gray-50 border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Item</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Description</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Qty</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Rate</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in invoice.items" :key="idx"
                      class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3 text-xs text-gray-700">{{ item.item_code || item.item_name || '—' }}</td>
                      <td class="px-4 py-3 text-xs text-gray-500 max-w-xs">
                        <span class="line-clamp-2">{{ item.description || '—' }}</span>
                      </td>
                      <td class="px-4 py-3 text-xs text-right text-gray-700">{{ item.qty }}</td>
                      <td class="px-4 py-3 text-xs text-right text-gray-700">{{ fmt(item.rate) }}</td>
                      <td class="px-4 py-3 text-xs text-right font-semibold"
                        :class="(item.amount || 0) < 0 ? 'text-red-500' : 'text-gray-900'">
                        {{ fmt(item.amount) }}
                      </td>
                    </tr>
                    <tr v-if="!invoice.items || invoice.items.length === 0">
                      <td colspan="5" class="px-4 py-8 text-center text-xs text-gray-400">No items</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Tax Breakdown -->
            <div v-if="invoice.taxes && invoice.taxes.length">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Taxes</h3>
              <div class="rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="bg-gray-50 border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Account</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Rate</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(tax, i) in invoice.taxes" :key="i"
                      class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3 text-xs text-gray-700">{{ tax.account_head }}</td>
                      <td class="px-4 py-3 text-xs text-right text-gray-500">{{ tax.rate }}%</td>
                      <td class="px-4 py-3 text-xs text-right text-gray-700">{{ fmt(tax.tax_amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Totals Summary -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Net Total</span>
                <span class="text-xs text-gray-700">{{ fmt(invoice.net_total) }}</span>
              </div>
              <div v-if="invoice.total_taxes_and_charges" class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Taxes &amp; Charges</span>
                <span class="text-xs text-gray-700">{{ fmt(invoice.total_taxes_and_charges) }}</span>
              </div>
              <div v-if="invoice.discount_amount" class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Discount</span>
                <span class="text-xs text-red-500">- {{ fmt(invoice.discount_amount) }}</span>
              </div>
              <div class="flex items-center justify-between pt-2 border-t border-gray-200">
                <span class="text-xs font-bold text-gray-900">Grand Total</span>
                <span class="text-xs font-bold text-gray-900">{{ fmt(invoice.grand_total) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold text-gray-700">Amount Paid</span>
                <span class="text-xs font-semibold text-green-600">
                  {{ fmt((invoice.grand_total || 0) - (invoice.outstanding_amount || 0)) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-gray-900">Outstanding</span>
                <span class="text-xs font-bold"
                  :class="(invoice.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-green-500'">
                  {{ fmt(invoice.outstanding_amount) }}
                </span>
              </div>
            </div>

            <!-- Remarks -->
            <div v-if="invoice.remarks">
              <p class="text-xs text-gray-400 mb-1.5">Remarks</p>
              <div class="px-4 py-3 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-xl">{{ invoice.remarks }}</div>
            </div>

          </template>

          <!-- Error -->
          <div v-else class="py-12 text-center">
            <p class="text-sm text-gray-400">Could not load invoice details.</p>
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
  invoiceName: { type: String, required: true },
  invoiceType: { type: String, default: 'Room Invoice' },
})
defineEmits(['close'])

const invoice = ref(null)
const loading = ref(true)

const doctype = computed(() =>
  props.invoiceType === 'POS Invoice' ? 'POS Invoice' : 'Sales Invoice'
)
const typeLabel = computed(() => {
  if (props.invoiceType === 'POS Invoice') return 'Restaurant'
  if (props.invoiceType === 'Credit Note') return 'Credit Note'
  return props.invoiceType || 'Room Charge'
})
const typeBadge = computed(() => {
  if (props.invoiceType === 'POS Invoice') return 'bg-purple-50 text-purple-600 border-purple-200'
  if (props.invoiceType === 'Credit Note') return 'bg-orange-50 text-orange-500 border-orange-200'
  return 'bg-blue-50 text-blue-600 border-blue-200'
})
const statusBadge = computed(() => {
  const s = invoice.value?.status
  if (s === 'Paid') return 'bg-green-50 text-green-600 border-green-200'
  if (s === 'Unpaid' || s === 'Overdue') return 'bg-red-50 text-red-500 border-red-200'
  if (s === 'Return') return 'bg-orange-50 text-orange-500 border-orange-200'
  return 'bg-gray-50 text-gray-500 border-gray-200'
})

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

async function loadInvoice() {
  loading.value = true
  try {
    const r = await fetch(
      `/api/method/frappe.client.get?doctype=${encodeURIComponent(doctype.value)}&name=${encodeURIComponent(props.invoiceName)}`,
      { headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' } }
    )
    const data = await r.json()
    invoice.value = data.message || null
  } catch {
    invoice.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadInvoice)
</script>
