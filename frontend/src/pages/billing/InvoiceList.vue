<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Invoice List</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Invoice List</h1>
      <p class="text-xs text-gray-400 mt-1">All individual guest invoices — view outstanding balances, payment status, folio charges, and issue quick actions or prints.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Invoice Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ filtered.length }}<template v-if="filtered.length !== invoices.length"> of {{ invoices.length }}</template>
          invoice{{ invoices.length === 1 ? '' : 's' }} • {{ unpaidCount }} unpaid • {{ overdueCount }} overdue
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing')">Billing Dashboard</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing/payments')">Payment List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Invoice</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Invoices</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">{{ fromDate || toDate ? 'Period' : 'All' }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ filtered.length }}</p>
        <p v-if="fromDate || toDate" class="text-xs text-gray-400 mt-1.5">{{ fmtDate(fromDate) || 'Any' }} – {{ fmtDate(toDate) || 'Any' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unpaid</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ unpaidCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ overdueCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Outstanding</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Balance</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ fmtAmount(totalOutstanding) }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search invoice no., guest, room..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <!-- Date range (issue date) -->
        <div class="flex items-center gap-1.5">
          <label class="text-xs text-gray-500 font-medium">From</label>
          <input v-model="fromDate" type="date"
            class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>
        <div class="flex items-center gap-1.5">
          <label class="text-xs text-gray-500 font-medium">To</label>
          <input v-model="toDate" type="date"
            class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Unpaid</option>
          <option>Part Paid</option>
          <option>Paid</option>
          <option>Overdue</option>
          <option>Credit Note</option>
        </select>
        <select v-model="filterType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Types</option>
          <option>Room</option>
          <option>Restaurant</option>
          <option>Minibar</option>
          <option>Laundry</option>
          <option>Misc</option>
          <option>Credit Note</option>
        </select>
        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showOverdueOnly = !showOverdueOnly; currentPage = 1">
          {{ showOverdueOnly ? 'Show All' : 'Overdue Only' }}
        </button>
      </div>
      <!-- Active date range indicator -->
      <div v-if="fromDate || toDate" class="mt-3 flex items-center gap-2">
        <span class="text-xs text-gray-400">Issue date range:</span>
        <span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
          {{ fmtDate(fromDate) || 'Any' }} → {{ fmtDate(toDate) || 'Any' }}
        </span>
        <span class="text-xs text-gray-400">· {{ filtered.length }} result{{ filtered.length === 1 ? '' : 's' }}</span>
      </div>
    </div>

    <!-- Invoice Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Invoice Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} invoices</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issue Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Due Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Balance</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="px-6 py-8 text-center text-xs text-gray-400">Loading invoice records...</td>
          </tr>
          <tr v-else-if="error">
            <td colspan="10" class="px-6 py-8 text-center text-xs text-red-500">{{ error }} <button @click="load" class="ml-2 underline font-semibold">Retry</button></td>
          </tr>
          <tr v-else-if="paged.length === 0">
            <td colspan="10" class="px-6 py-8 text-center text-xs text-gray-400">No invoice records found.</td>
          </tr>
          <tr v-for="inv in paged" v-else :key="inv.invoiceNo"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ inv.invoiceNo }}</td>
            <td class="px-4 py-4">
              <p class="text-xs font-bold text-gray-900">{{ inv.guest }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ inv.guestNote }}</p>
            </td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-700">{{ inv.room }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ fmtDate(inv.issueDate) }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.dueDate ? fmtDate(inv.dueDate) : '-' }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ fmtAmount(inv.amount) }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ fmtAmount(inv.balance) }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="invoiceStatusClass(inv.status)">{{ inv.status }}</span>
            </td>
            <td class="px-4 py-4">
              <div class="flex items-center gap-1.5">
                <button @click="openInvoiceDetail(inv)"
                  class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  View
                </button>
                <button v-if="inv.status === 'Unpaid' || inv.status === 'Part Paid' || inv.status === 'Overdue'"
                  @click="openPaymentModal(inv)"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                  Settle
                </button>
                <button v-if="inv.status === 'Paid'"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  Print
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
          <button v-for="p in totalPages" :key="p" @click="currentPage = p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages ? currentPage++ : null"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>

  <!-- Receive Payment Modal -->
  <Teleport to="body">
    <div v-if="showPaymentModal" class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="closePaymentModal">
      <div class="bg-white rounded-2xl w-full shadow-2xl" style="max-width:520px;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Receive Payment</h2>
            <p class="text-xs text-gray-400 mt-1">
              {{ selectedInvoice?.invoiceNo }} · Balance: {{ fmtAmount(selectedInvoice?.balance || 0) }}
            </p>
          </div>
          <button @click="closePaymentModal"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">✕</button>
        </div>

        <div class="px-8 py-6 space-y-4">
          <div v-if="paymentError" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-600">{{ paymentError }}</div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Mode of Payment <span class="text-red-400">*</span></p>
              <select v-model="paymentForm.mode_of_payment"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select mode</option>
                <option v-for="m in paymentModes" :key="m.name" :value="m.name">{{ m.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Amount Received <span class="text-red-400">*</span></p>
              <input type="number" v-model.number="paymentForm.paid_amount" min="0.01" step="0.01"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
              <input type="date" v-model="paymentForm.payment_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference No</p>
              <input type="text" v-model="paymentForm.reference_no" placeholder="Bank / terminal reference"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference Date</p>
              <input type="date" v-model="paymentForm.reference_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Remarks</p>
              <input type="text" v-model="paymentForm.remarks" placeholder="Optional note"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="closePaymentModal">Cancel</button>
            <button
              :disabled="paymentSubmitting || !paymentForm.mode_of_payment || !(paymentForm.paid_amount > 0)"
              @click="submitPayment"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ paymentSubmitting ? 'Processing…' : 'Confirm Payment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <InvoiceDetailModal
    v-if="detailInvoice"
    :invoice-name="detailInvoice.invoiceNo"
    :invoice-type="detailInvoice.type"
    @close="detailInvoice = null"
  />
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'
import InvoiceDetailModal from '@/components/checkin/InvoiceDetailModal.vue'

const search = ref('')
const fromDate = ref('')
const toDate = ref('')
const filterStatus = ref('')
const filterType = ref('')
const showOverdueOnly = ref(false)
const currentPage = ref(1)
const perPage = 25
const invoices = ref([])
const loading = ref(false)
const error = ref(null)
const showPaymentModal = ref(false)
const selectedInvoice = ref(null)
const detailInvoice = ref(null)
const paymentModes = ref([])
const paymentSubmitting = ref(false)
const paymentError = ref('')
const today = new Date().toISOString().slice(0, 10)
const paymentForm = reactive({
  mode_of_payment: '',
  paid_amount: 0,
  payment_date: today,
  reference_no: '',
  reference_date: '',
  remarks: '',
})

function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function fmtAmount(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `₦${+(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `₦${+(n / 1_000).toFixed(1)}K`
  return `₦${n.toLocaleString()}`
}

function resetFilters() {
  search.value = ''
  fromDate.value = ''
  toDate.value = ''
  filterStatus.value = ''
  filterType.value = ''
  showOverdueOnly.value = false
  currentPage.value = 1
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.get_invoice_register', {
      from_date: fromDate.value,
      to_date: toDate.value,
    })
    invoices.value = data?.invoices || []
    currentPage.value = 1
  } catch (err) {
    error.value = err.message || 'Failed to load invoice records.'
  } finally {
    loading.value = false
  }
}

async function loadPaymentModes() {
  try {
    paymentModes.value = await callMethod('rhohotel.rhocom_hotel.api.corporate_billing.get_payment_modes') || []
  } catch {
    paymentModes.value = []
  }
}

function openPaymentModal(invoice) {
  selectedInvoice.value = invoice
  paymentError.value = ''
  paymentForm.mode_of_payment = ''
  paymentForm.paid_amount = Math.max(0, Number(invoice.balance) || 0)
  paymentForm.payment_date = today
  paymentForm.reference_no = ''
  paymentForm.reference_date = ''
  paymentForm.remarks = ''
  showPaymentModal.value = true
  if (!paymentModes.value.length) loadPaymentModes()
}

function closePaymentModal() {
  showPaymentModal.value = false
  selectedInvoice.value = null
  paymentError.value = ''
}

function openInvoiceDetail(invoice) {
  detailInvoice.value = invoice
}

async function submitPayment() {
  if (!selectedInvoice.value || !paymentForm.mode_of_payment || !(paymentForm.paid_amount > 0)) return
  paymentSubmitting.value = true
  paymentError.value = ''
  try {
    await callMethod('rhohotel.rhocom_hotel.api.corporate_billing.record_corporate_payment', {
      invoice_name: selectedInvoice.value.invoiceNo,
      mode_of_payment: paymentForm.mode_of_payment,
      paid_amount: paymentForm.paid_amount,
      payment_date: paymentForm.payment_date,
      reference_no: paymentForm.reference_no,
      reference_date: paymentForm.reference_date,
      remarks: paymentForm.remarks,
    })
    closePaymentModal()
    await load()
  } catch (err) {
    paymentError.value = err.message || 'Failed to receive payment.'
  } finally {
    paymentSubmitting.value = false
  }
}

const filtered = computed(() => {
  let list = invoices.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(i =>
      String(i.invoiceNo || '').toLowerCase().includes(q) ||
      String(i.guest || '').toLowerCase().includes(q) ||
      String(i.room || '').toLowerCase().includes(q)
    )
  }
  if (filterStatus.value) list = list.filter(i => i.status === filterStatus.value)
  if (filterType.value) list = list.filter(i => i.type === filterType.value)
  if (showOverdueOnly.value) list = list.filter(i => i.status === 'Overdue')
  return list
})

const unpaidCount = computed(() => filtered.value.filter(i => i.status === 'Unpaid' || i.status === 'Part Paid').length)
const overdueCount = computed(() => filtered.value.filter(i => i.status === 'Overdue').length)
const totalOutstanding = computed(() => filtered.value.reduce((sum, i) => sum + (Number(i.balance) || 0), 0))
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function invoiceStatusClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Part Paid': 'bg-blue-50 text-blue-600',
    'Paid':      'bg-green-50 text-green-600',
    'Overdue':   'bg-red-50 text-red-500',
    'Credit Note': 'bg-purple-50 text-purple-600',
  }[s] || 'bg-gray-100 text-gray-500'
}

let debounceTimer = null
watch([fromDate, toDate], () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 250)
})
watch([search, filterStatus, filterType, showOverdueOnly], () => { currentPage.value = 1 })
onMounted(() => {
  load()
  loadPaymentModes()
})
</script>
