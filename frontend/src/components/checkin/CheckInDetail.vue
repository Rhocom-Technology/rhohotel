<template>
  <div class="p-6">

    <!-- Guest Header -->
    <div class="mb-5">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-2xl font-bold text-gray-900">{{ checkIn.guest || '—' }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg leading-none">✕</button>
      </div>
      <div class="flex items-center gap-2 flex-wrap mb-2">
        <span class="px-2.5 py-1 text-xs font-semibold bg-green-50 text-green-600 rounded-full border border-green-200">
          {{ checkIn.status }}
        </span>
        <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-600 rounded-full border border-blue-200">
          Room {{ checkIn.room_number }}
        </span>
        <span
          v-if="(checkIn.total_outstanding_amount || 0) > 0"
          class="px-2.5 py-1 text-xs font-semibold bg-orange-50 text-orange-600 rounded-full border border-orange-200"
        >
          Balance {{ formatCurrency(checkIn.total_outstanding_amount) }}
        </span>
      </div>
      <p class="text-xs text-gray-400">
        {{ checkIn.room_type }} •
        {{ checkIn.reservation_source || 'Walk-in' }} •
        Check-in {{ formatDateTime(checkIn.check_in_datetime) }} •
        Check-out {{ formatDateTime(checkIn.expected_check_out_datetime) }} •
        {{ checkIn.number_of_nights }} nights
      </p>
    </div>

    <!-- Action Buttons -->
    <div class="flex items-center gap-2 flex-wrap mb-5 pb-5 border-b border-gray-100">
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
        Room Transfer
      </button>
      <div class="relative">
        <button
          @click="showCreateMenu = !showCreateMenu"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-1"
        >
          Create ▾
        </button>
        <div v-if="showCreateMenu" class="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 py-1 min-w-32">
          <button @click="showCreateMenu = false" class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Discount</button>
          <button @click="showCreateMenu = false" class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Refund</button>
        </div>
      </div>
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
        Bill Transfer
      </button>
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
        Adjust Stay
      </button>
      <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
        Receive Payment
      </button>
      <button class="px-4 py-2 text-xs font-semibold text-white bg-gray-900 rounded-lg hover:bg-gray-800">
        Check Out
      </button>
      <button @click="$emit('close')" class="px-4 py-2 text-xs text-gray-400 hover:text-gray-600">
        Cancel
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex items-center gap-4 mb-5 border-b border-gray-100">
      <button
        v-for="tab in ['Details', 'Transfer History']"
        :key="tab"
        @click="activeTab = tab"
        class="pb-2.5 text-xs font-medium transition-colors border-b-2"
        :class="activeTab === tab ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'"
      >
        {{ tab }}
      </button>
    </div>

    <!-- Details Tab -->
    <div v-if="activeTab === 'Details'" style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">

      <!-- Left -->
      <div>
        <p class="text-xs text-gray-400 mb-2">Reservation</p>
        <div class="bg-gray-50 rounded-lg px-3 py-2 text-xs text-gray-400 mb-5">
          {{ checkIn.reservation || 'Walk-in' }}
        </div>

        <h3 class="text-sm font-bold text-gray-900 mb-4">Guest and Stay Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <p class="text-xs text-gray-400 mb-1">Guest</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">{{ checkIn.guest || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Check-in Time</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatDateTime(checkIn.check_in_datetime) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">ID Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.id_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Number of Nights</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.number_of_nights || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Contact Number</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.contact_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Expected Check-out</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold" :class="isOverdue ? 'text-red-500' : 'text-gray-700'">
              {{ formatDateTime(checkIn.expected_check_out_datetime) }}
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">Room {{ checkIn.room_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.room_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Market Place</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.reservation_source || 'Walk in' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Status</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-green-600">{{ checkIn.status || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Rate Amount</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatCurrency(checkIn.rate_amount) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Discount Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ checkIn.discount_type || '—' }}</div>
          </div>
          <div style="grid-column:span 2;">
            <p class="text-xs text-gray-400 mb-1">Total Charges</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-bold text-gray-900">{{ formatCurrency(checkIn.total_charges) }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Bills -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-900">Bills and Payments</h3>
          <button class="px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">View Invoice Details</button>
        </div>

        <table class="w-full mb-5">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-500 pb-2">Invoice</th>
              <th class="text-left text-xs font-semibold text-gray-500 pb-2">Posting Date</th>
              <th class="text-right text-xs font-semibold text-gray-500 pb-2">Grand Total</th>
              <th class="text-right text-xs font-semibold text-gray-500 pb-2">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-if="loading">
              <td colspan="4" class="py-4 text-center">
                <Loader2 class="w-4 h-4 animate-spin text-gray-400 mx-auto" />
              </td>
            </tr>
            <tr v-for="inv in invoices" :key="inv.invoice" class="hover:bg-gray-50">
              <td class="py-2.5 text-xs text-gray-700">{{ inv.invoice || '—' }}</td>
              <td class="py-2.5 text-xs text-gray-500">—</td>
              <td class="py-2.5 text-xs text-right text-gray-700">{{ formatCurrency(inv.amount) }}</td>
              <td class="py-2.5 text-xs text-right font-semibold" :class="(inv.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-gray-400'">
                {{ formatCurrency(inv.outstanding_amount) }}
              </td>
            </tr>
            <tr v-if="!loading && invoices.length === 0">
              <td colspan="4" class="py-6 text-center text-xs text-gray-400">No invoices found</td>
            </tr>
          </tbody>
          <tfoot v-if="invoices.length > 0">
            <tr class="border-t border-gray-200">
              <td colspan="2" class="py-2.5 text-xs font-bold text-gray-900">Invoice Total</td>
              <td class="py-2.5 text-xs font-bold text-right text-gray-900">{{ formatCurrency(invoiceTotal) }}</td>
              <td class="py-2.5 text-xs font-bold text-right text-red-500">{{ formatCurrency(outstandingTotal) }}</td>
            </tr>
          </tfoot>
        </table>

        <div class="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Billing Summary</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700">Total Bill</span>
              <span class="text-xs font-bold text-gray-900">{{ formatCurrency(checkIn.total_charges) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700">Total Payment</span>
              <span class="text-xs font-bold text-green-600">
                {{ formatCurrency((checkIn.total_charges || 0) - (checkIn.total_outstanding_amount || 0)) }}
              </span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-200">
              <span class="text-xs font-bold text-gray-900">Outstanding</span>
              <span class="text-xs font-bold" :class="(checkIn.total_outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-green-500'">
                {{ formatCurrency(checkIn.total_outstanding_amount) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transfer History Tab -->
    <div v-if="activeTab === 'Transfer History'" class="py-12 text-center">
      <p class="text-sm text-gray-400">No transfer history available</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const props = defineProps({ checkIn: { type: Object, required: true } })
defineEmits(['close'])

const activeTab = ref('Details')
const showCreateMenu = ref(false)
const invoices = ref([])
const loading = ref(false)

onMounted(async () => {
  if (!props.checkIn?.name) return
  try {
    loading.value = true
    const res = await fetch(
      `/api/method/frappe.client.get?doctype=Hotel%20Room%20Check%20In&name=${encodeURIComponent(props.checkIn.name)}`,
      { credentials: 'include' }
    )
    const data = await res.json()
    invoices.value = data?.message?.invoices || []
  } catch (e) {
    console.error('Failed to load check-in detail', e)
  } finally {
    loading.value = false
  }
})

const invoiceTotal = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (inv.amount || 0), 0)
)

const outstandingTotal = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (inv.outstanding_amount || 0), 0)
)

const isOverdue = computed(() => {
  if (!props.checkIn?.expected_check_out_datetime) return false
  return new Date(props.checkIn.expected_check_out_datetime) < new Date()
})

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>