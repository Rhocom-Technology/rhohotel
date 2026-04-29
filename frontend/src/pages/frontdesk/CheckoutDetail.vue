<template>
  <div class="space-y-5">

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl px-6 py-10 text-center">
      <p class="text-sm font-semibold text-red-500 mb-2">{{ loadError }}</p>
      <button @click="$router.back()" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">← Back</button>
    </div>

    <template v-if="!loading && !loadError">

    <!-- Guest Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-start gap-3 mb-2 flex-wrap justify-between">
        <div class="flex items-start gap-3 flex-wrap">
          <h2 class="text-2xl font-bold text-gray-900">{{ data.guest_name || data.guest || '—' }}</h2>
          <span class="px-3 py-1 text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-200 rounded-full">Room {{ data.room_number }}</span>
          <span v-if="data.total_outstanding > 0"
            class="px-3 py-1 text-xs font-semibold bg-red-50 text-red-500 border border-red-200 rounded-full">
            Balance {{ formatCurrency(data.total_outstanding) }}
          </span>
          <span v-else class="px-3 py-1 text-xs font-semibold bg-green-50 text-green-600 border border-green-200 rounded-full">
            Settled
          </span>
        </div>
        <button @click="$router.push('/check-ins/' + data.name)"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          ← Back to Check-in
        </button>
      </div>
      <p class="text-xs text-gray-400">
        {{ data.room_type }} •
        Check-in {{ formatDateTime(data.check_in_datetime) }} •
        Expected out {{ formatDateTime(data.expected_check_out_datetime) }} •
        {{ data.number_of_nights }} nights •
        {{ data.reservation_source || 'Walk-in' }}
      </p>
    </div>

    <!-- Stat Cards -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Total Charges</p>
        <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(computedTotalCharges) }}</p>
        <p class="text-xs text-blue-500 font-medium mt-1">Room, F&amp;B, incidentals</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Amount Paid</p>
        <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(computedTotalPaid) }}</p>
        <p class="text-xs text-green-600 font-medium mt-1">Payments received</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-2xl font-bold" :class="computedOutstanding > 0 ? 'text-red-500' : 'text-green-500'">
          {{ formatCurrency(computedOutstanding) }}
        </p>
        <p class="text-xs font-medium mt-1" :class="computedOutstanding > 0 ? 'text-red-400' : 'text-green-500'">
          {{ computedOutstanding > 0 ? 'Must settle before departure' : 'Fully paid' }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Folio Reference</p>
        <p class="text-sm font-bold text-gray-900 mt-1">{{ data.name }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ data.status }}</p>
      </div>
    </div>

    <!-- Main Content -->
    <div style="display:grid;grid-template-columns:1fr 380px;gap:12px;">

      <!-- Left: Stay Details + Invoice Breakdown -->
      <div class="space-y-5">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Stay and Settlement Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-5">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ data.guest_name || data.guest }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ data.room_number }} • {{ data.room_type }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-in Time</p>
              <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDateTime(data.check_in_datetime) }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected Check-out</p>
              <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDateTime(data.expected_check_out_datetime) }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Length of Stay</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ data.number_of_nights }} Night{{ data.number_of_nights !== 1 ? 's' : '' }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Payment Status</p>
              <div class="px-3 py-2.5 text-xs font-semibold rounded-lg border"
                :class="computedOutstanding > 0 ? 'text-red-500 bg-red-50 border-red-200' : 'text-green-600 bg-green-50 border-green-200'">
                {{ computedOutstanding > 0 ? 'Outstanding balance remains' : 'Fully settled' }}
              </div>
            </div>
          </div>

          <!-- Invoice Breakdown -->
          <h3 class="text-sm font-bold text-gray-900 mb-3">Invoice Breakdown</h3>
          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 bg-gray-50">
                  <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Invoice</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Date</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Type</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Amount</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Balance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!data.invoices || data.invoices.length === 0">
                  <td colspan="5" class="px-5 py-8 text-center text-xs text-gray-400">No invoices found for this stay</td>
                </tr>
                <tr v-for="inv in data.invoices" :key="inv.invoice_id"
                  class="border-b border-gray-50 last:border-0">
                  <td class="px-5 py-3 text-xs text-gray-700">{{ inv.invoice_id }}</td>
                  <td class="px-4 py-3 text-xs text-gray-500">{{ formatDate(inv.posting_date) }}</td>
                  <td class="px-4 py-3 text-xs text-gray-500">{{ inv.invoice_type }}</td>
                  <td class="px-5 py-3 text-xs text-right text-gray-700">{{ formatCurrency(inv.amount) }}</td>
                  <td class="px-5 py-3 text-xs text-right font-semibold"
                    :class="inv.outstanding_amount > 0 ? 'text-red-500' : 'text-gray-400'">
                    {{ formatCurrency(inv.outstanding_amount) }}
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="data.invoices && data.invoices.length > 0">
                <tr class="border-t border-gray-200 bg-gray-50">
                  <td colspan="3" class="px-5 py-3 text-xs font-bold text-gray-900">Total</td>
                  <td class="px-5 py-3 text-xs font-bold text-right text-gray-900">{{ formatCurrency(computedTotalCharges) }}</td>
                  <td class="px-5 py-3 text-xs font-bold text-right text-red-500">{{ formatCurrency(computedOutstanding) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Departure Notes -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Departure Notes</h3>
          <textarea v-model="remarks" rows="4"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Room status, minibar sign-off, key return, or guest departure note"></textarea>
        </div>
      </div>

      <!-- Right: Checkout Control Panel -->
      <div class="space-y-5">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-5">
          <h3 class="text-sm font-bold text-gray-900">Checkout Control Panel</h3>

          <!-- Balance Alert -->
          <div v-if="computedOutstanding > 0" class="bg-red-50 rounded-xl border border-red-200 px-4 py-4">
            <p class="text-xs font-bold text-red-600 mb-1">Outstanding Balance Alert</p>
            <p class="text-xs text-red-500 leading-relaxed">
              Guest owes {{ formatCurrency(computedOutstanding) }}.
              Receive payment or arrange bill transfer before completing checkout.
            </p>
          </div>
          <div v-else class="bg-green-50 rounded-xl border border-green-200 px-4 py-4">
            <p class="text-xs font-bold text-green-600 mb-1">Folio Settled</p>
            <p class="text-xs text-green-600 leading-relaxed">All charges have been paid. Guest is ready for departure.</p>
          </div>

          <!-- Payment Entries -->
          <div v-if="data.payments && data.payments.length > 0">
            <h4 class="text-xs font-bold text-gray-900 mb-3">Payment Entries</h4>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Reference</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Date</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Paid</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in data.payments" :key="p.payment_id" class="border-b border-gray-50 last:border-0">
                    <td class="px-4 py-3 text-xs text-gray-700">{{ p.payment_id }}</td>
                    <td class="px-3 py-3 text-xs text-gray-500">{{ formatDate(p.posting_date) }}</td>
                    <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">{{ formatCurrency(p.paid_amount) }}</td>
                  </tr>
                  <tr class="border-t border-gray-200">
                    <td class="px-4 py-3 text-xs font-bold text-gray-900">Total Paid</td>
                    <td></td>
                    <td class="px-4 py-3 text-xs text-right font-bold text-gray-900">{{ formatCurrency(data.total_paid) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Departure Checklist -->
          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-3">Departure Checklist</h4>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-3">
              <label v-for="item in checklist" :key="item" class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="checked[item]" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">{{ item }}</span>
              </label>
            </div>
          </div>

          <!-- Checkout Success -->
          <div v-if="checkoutDone" class="bg-green-50 rounded-xl border border-green-200 px-4 py-4 text-center">
            <p class="text-sm font-bold text-green-600 mb-1">✓ Check-out Complete</p>
            <p class="text-xs text-green-500 mb-3">Guest has been checked out successfully.</p>
            <button @click="$router.push('/check-outs')"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              View Check-outs
            </button>
          </div>

          <!-- Error Banner -->
          <div v-if="checkoutError" class="bg-red-50 rounded-xl border border-red-200 px-4 py-3">
            <p class="text-xs font-bold text-red-600 mb-1">Checkout Failed</p>
            <p class="text-xs text-red-500">{{ checkoutError }}</p>
          </div>

          <!-- Quick Actions -->
          <div v-if="!checkoutDone">
            <h4 class="text-xs font-bold text-gray-900 mb-3">Quick Actions</h4>
            <div class="flex items-center gap-2 flex-wrap">
              <button @click="finalizeCheckout"
                :disabled="checkingOut"
                class="flex-1 px-4 py-2.5 text-xs font-semibold text-white rounded-lg transition-colors"
                :class="checkingOut ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'">
                {{ checkingOut ? 'Processing...' : 'Finalize Check-out' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const data = ref({
  invoices: [],
  payments: [],
  total_paid: 0,
  total_outstanding: 0,
  total_invoice: 0,
  total_charges: 0,
})

// Computed values that correctly derive from invoice and payment data
const computedTotalCharges = computed(() => {
  const fromInvoices = (data.value.invoices || []).reduce((sum, inv) => sum + (Number(inv.amount) || 0), 0)
  return fromInvoices || data.value.total_invoice || data.value.total_charges || 0
})

const computedTotalPaid = computed(() => {
  const fromPayments = (data.value.payments || []).reduce((sum, p) => sum + (Number(p.paid_amount) || 0), 0)
  return fromPayments || data.value.total_paid || 0
})

const computedOutstanding = computed(() => {
  const fromInvoices = (data.value.invoices || []).reduce((sum, inv) => sum + (Number(inv.outstanding_amount) || 0), 0)
  return fromInvoices || data.value.total_outstanding || 0
})

const remarks = ref('')
const checkingOut = ref(false)
const checkoutDone = ref(false)
const checkoutError = ref('')

const checklist = [
  'Receive final outstanding payment',
  'Confirm room key returned or deactivated',
  'Confirm housekeeping / minibar / laundry sign-off',
  'Close folio and issue final receipt',
]
const checked = ref({})

async function loadDetail() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_checkout_detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({ check_in_name: route.params.id }),
    })
    const json = await res.json()
    if (json.exc) {
      loadError.value = 'Could not load checkout details.'
      return
    }
    if (json.message) {
      data.value = json.message
    }
  } catch (e) {
    loadError.value = 'Network error — please refresh.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function finalizeCheckout() {
  checkoutError.value = ''
  checkingOut.value = true
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.process_checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({
        check_in_name: route.params.id,
        remarks: remarks.value || '',
      }),
    })
    const json = await res.json()
    if (json.exc) {
      const match = json.exc.match(/frappe\.exceptions\.\w+: (.+)/m)
      checkoutError.value = match ? match[1] : 'Checkout failed. Please try again.'
      return
    }
    if (json.message && json.message.status === 'Checked Out') {
      checkoutDone.value = true
      data.value.status = 'Checked Out'
    } else {
      checkoutError.value = 'Unexpected response from server.'
    }
  } catch (e) {
    checkoutError.value = 'Network error — please try again.'
    console.error(e)
  } finally {
    checkingOut.value = false
  }
}

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

onMounted(() => {
  if (route.params.id) loadDetail()
})
</script>
