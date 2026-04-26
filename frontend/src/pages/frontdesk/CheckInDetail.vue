<template>
  <div class="space-y-5">

    <!-- Loading / Error States -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl px-6 py-10 text-center">
      <p class="text-sm font-semibold text-red-500 mb-2">{{ loadError }}</p>
      <button @click="$router.back()" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">← Back</button>
    </div>

    <template v-if="!loading && !loadError">
    <!-- Guest Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-start justify-between mb-2">
        <h2 class="text-2xl font-bold text-gray-900">{{ checkIn.guest || '—' }}</h2>
        <button @click="$router.back()"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          ← Back
        </button>
      </div>
      <div class="flex items-center gap-2 flex-wrap mb-2">
        <span class="px-2.5 py-1 text-xs font-semibold bg-green-50 text-green-600 rounded-full border border-green-200">
          {{ checkIn.status || 'Checked In' }}
        </span>
        <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-600 rounded-full border border-blue-200">
          Room {{ checkIn.room_number || '—' }}
        </span>
        <span v-if="(checkIn.total_outstanding_amount || 0) > 0"
          class="px-2.5 py-1 text-xs font-semibold bg-orange-50 text-orange-600 rounded-full border border-orange-200">
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
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center gap-2 flex-wrap">
      <button @click="showRoomTransfer = true"
        class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Room Transfer
      </button>
      <div class="relative create-menu-container">
        <button @click="showCreateMenu = !showCreateMenu"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
          Create ▾
        </button>
        <div v-if="showCreateMenu"
          class="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 py-1 min-w-32">
          <button @click="showDiscount = true; showCreateMenu = false"
            class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Discount</button>
          <button @click="showRefund = true; showCreateMenu = false"
            class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Refund</button>
        </div>
      </div>
      <button @click="showBillTransfer = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Bill Transfer
      </button>
      <button @click="showStayAdjustment = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Adjust Stay
      </button>
      <button @click="showPayment = true" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
        Receive Payment
      </button>
      <button 
      class="px-4 py-2 text-xs font-semibold text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
      @click="$router.push('/check-outs/' + checkIn.name)">
      Check Out
    </button>
      <button @click="$router.back()"
        class="px-4 py-2 text-xs text-gray-400 hover:text-gray-600 transition-colors">
        Cancel
      </button>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-xl border border-gray-200 px-6">
      <div class="flex items-center gap-4 border-b border-gray-100">
        <button v-for="tab in ['Details', 'Transfer History']" :key="tab"
          @click="activeTab = tab"
          class="py-3.5 text-xs font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === tab ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'">
          {{ tab }}
        </button>
      </div>
    </div>

    <!-- Details Tab -->
    <div v-if="activeTab === 'Details'" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- Left: Guest and Stay Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <p class="text-xs text-gray-400 mb-1.5">Reservation</p>
        <div class="px-3 py-2.5 text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-lg mb-5">
          {{ checkIn.reservation || 'Walk-in' }}
        </div>

        <h3 class="text-sm font-bold text-gray-900 mb-4">Guest and Stay Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <p class="text-xs text-gray-400 mb-1">Guest</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.guest || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Check-in Time</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDateTime(checkIn.check_in_datetime) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">ID Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.id_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Number of Nights</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.number_of_nights || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Contact Number</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.contact_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Expected Check-out</p>
            <div class="px-3 py-2.5 text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg"
              :class="isOverdue ? 'text-red-500' : 'text-gray-700'">
              {{ formatDateTime(checkIn.expected_check_out_datetime) }}
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Room {{ checkIn.room_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.room_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Market Place</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.reservation_source || 'Walk in' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Status</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-green-600 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.status || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Rate Amount</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatCurrency(checkIn.rate_amount) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Discount Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.discount_type || '—' }}</div>
          </div>
          <div style="grid-column:span 2;">
            <p class="text-xs text-gray-400 mb-1">Total Charges</p>
            <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ formatCurrency(checkIn.total_charges) }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Bills and Payments -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-900">Bills and Payments</h3>
          <button class="px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">View Invoice Details</button>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden mb-5">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Invoice</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Posting Date</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Grand Total</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="4" class="py-6 text-center">
                  <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                </td>
              </tr>
              <tr v-for="inv in invoices" :key="inv.invoice"
                class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-xs text-gray-700">{{ inv.invoice || '—' }}</td>
                <td class="px-3 py-3 text-xs text-gray-500">—</td>
                <td class="px-4 py-3 text-xs text-right text-gray-700">{{ formatCurrency(inv.amount) }}</td>
                <td class="px-4 py-3 text-xs text-right font-semibold"
                  :class="(inv.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-gray-400'">
                  {{ formatCurrency(inv.outstanding_amount) }}
                </td>
              </tr>
              <tr v-if="!loading && invoices.length === 0">
                <td colspan="4" class="py-8 text-center text-xs text-gray-400">No invoices found</td>
              </tr>
            </tbody>
            <tfoot v-if="invoices.length > 0">
              <tr class="border-t border-gray-200">
                <td colspan="2" class="px-4 py-3 text-xs font-bold text-gray-900">Invoice Total</td>
                <td class="px-4 py-3 text-xs font-bold text-right text-gray-900">{{ formatCurrency(invoiceTotal) }}</td>
                <td class="px-4 py-3 text-xs font-bold text-right text-red-500">{{ formatCurrency(outstandingTotal) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4">
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
              <span class="text-xs font-bold"
                :class="(checkIn.total_outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-green-500'">
                {{ formatCurrency(checkIn.total_outstanding_amount) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transfer History Tab -->
    <div v-if="activeTab === 'Transfer History'"
      class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-sm text-gray-400">No transfer history available</p>
    </div>

    <!-- Modals -->
    <RoomTransferModal v-if="showRoomTransfer" :checkIn="checkIn" @close="showRoomTransfer = false" @done="onActionDone" />
    <StayAdjustmentModal v-if="showStayAdjustment" :checkIn="checkIn" @close="showStayAdjustment = false" @done="onActionDone" />
    <RefundRequestModal v-if="showRefund" :checkIn="checkIn" @close="showRefund = false" @done="onActionDone" />
    <BillTransferModal v-if="showBillTransfer" :checkIn="checkIn" @close="showBillTransfer = false" @done="onActionDone" />
    <ReceivePaymentModal v-if="showPayment" :checkIn="checkIn" @close="showPayment = false" @done="onActionDone" />
    <DiscountModal v-if="showDiscount" :checkIn="checkIn" @close="showDiscount = false" @done="onActionDone" />

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import RoomTransferModal from '@/components/checkin/RoomTransferModal.vue'
import StayAdjustmentModal from '@/components/checkin/StayAdjustmentModal.vue'
import RefundRequestModal from '@/components/checkin/RefundRequestModal.vue'
import BillTransferModal from '@/components/checkin/BillTransferModal.vue'
import ReceivePaymentModal from '@/components/checkin/ReceivePaymentModal.vue'
import DiscountModal from '@/components/checkin/DiscountModal.vue'

const showRoomTransfer = ref(false)
const showStayAdjustment = ref(false)
const showRefund = ref(false)
const showBillTransfer = ref(false)
const showPayment = ref(false)
const showDiscount = ref(false)


const route = useRoute()
const activeTab = ref('Details')
const showCreateMenu = ref(false)
const invoices = ref([])
const loading = ref(true)
const loadError = ref('')

const checkIn = ref({
  name: route.params.id,
})

onMounted(async () => {
  if (!route.params.id) return
  await loadCheckIn()
})

async function loadCheckIn(silent = false) {
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_checkin_detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({ name: route.params.id }),
    })
    const data = await res.json()
    if (data.exc) {
      loadError.value = 'Could not load check-in details.'
      return
    }
    if (data.message) {
      checkIn.value = data.message
      invoices.value = data.message.invoices || []
    }
  } catch (e) {
    loadError.value = 'Network error — please refresh.'
    console.error('Failed to load check-in detail', e)
  } finally {
    if (!silent) loading.value = false
  }
}

// Close the "Create" menu when clicking outside
const closeCreateMenu = (e) => {
  if (showCreateMenu.value && !e.target.closest('.create-menu-container')) {
    showCreateMenu.value = false
  }
}

watch(showCreateMenu, (val) => {
  if (val) {
    setTimeout(() => window.addEventListener('click', closeCreateMenu), 0)
  } else {
    window.removeEventListener('click', closeCreateMenu)
  }
})

onUnmounted(() => {
  window.removeEventListener('click', closeCreateMenu)
})

watch(() => route.params.id, (newId) => {
  if (newId) loadCheckIn()
})

async function onActionDone() {
  await loadCheckIn(true)
}

const invoiceTotal = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (inv.amount || 0), 0)
)
const outstandingTotal = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (inv.outstanding_amount || 0), 0)
)
const isOverdue = computed(() => {
  if (!checkIn.value?.expected_check_out_datetime) return false
  return new Date(checkIn.value.expected_check_out_datetime) < new Date()
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