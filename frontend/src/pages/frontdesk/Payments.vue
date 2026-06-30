<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Billing / Payment List</p>
      <h1 class="text-2xl font-bold text-gray-900">Payment List</h1>
      <p class="text-xs text-gray-400 mt-1">Track all front desk payment transactions, balances, methods, references, and posting status.</p>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Payments Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Posted</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.paymentsToday }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Collected</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(stats.totalCollectedToday) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unallocated</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.unallocated }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Amount</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Due</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(stats.pendingAmount) }}</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
        <div class="w-full sm:min-w-[180px] sm:flex-[2]">
          <p class="text-xs text-gray-500 mb-1.5">Search payment</p>
          <input
            v-model="search"
            type="text"
            placeholder="Receipt no., guest, reservation..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="w-full sm:min-w-[120px] sm:flex-1">
          <p class="text-xs text-gray-500 mb-1.5">Method</p>
          <select v-model="filterMethod" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Methods</option>
            <option v-for="mode in paymentModes" :key="mode.name" :value="mode.name">{{ mode.name }}</option>
          </select>
        </div>
        <div class="w-full sm:min-w-[120px] sm:flex-1">
          <p class="text-xs text-gray-500 mb-1.5">Posting Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="Posted">Posted</option>
            <option value="Pending">Pending</option>
            <option value="Reversed">Reversed</option>
          </select>
        </div>
        <div class="w-full sm:min-w-[120px] sm:flex-1">
          <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
          <input v-model="filterDate" type="date" placeholder="Today"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600" />
        </div>
        <div class="flex w-full flex-col gap-2 pb-0.5 sm:w-auto sm:flex-row sm:items-center">
          <button @click="clearFilters" class="w-full px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 sm:w-auto">Reset</button>
          <button @click="openReceivePayment" class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 sm:w-auto">Receive Payment</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-4 py-4 flex flex-col gap-1 border-b border-gray-100 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h3 class="text-sm font-bold text-gray-900">All Payments</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ Math.min(pageSize, filteredList.length) }} of {{ filteredList.length.toLocaleString() }} payments</p>
      </div>

      <div v-if="paymentResource.loading" class="flex items-center justify-center py-14">
        <p class="text-sm text-gray-400">Loading payments...</p>
      </div>

      <div v-else-if="paymentResource.error" class="px-6 py-10 text-center">
        <p class="text-sm font-medium text-red-500">Unable to load payments.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[780px]">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Receipt</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest / Reservation</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Method</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Reference</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Amount</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Posting Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="item in paginatedList"
              :key="item.id"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <td class="px-6 py-4">
                <p class="text-xs font-bold text-gray-900">{{ item.id }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.date }}</p>
              </td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.guest }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.reservation }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.method }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.reference }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ formatCurrency(item.amount) }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(item.status)">
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="openPayment(item)" class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors">
                  Open
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-4 py-3 border-t border-gray-100 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex flex-wrap items-center gap-1">
            <button
              v-for="p in Math.min(totalPages, 5)"
              :key="p"
              @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center transition-colors"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            >{{ p }}</button>
            <span v-if="totalPages > 5" class="text-xs text-gray-400">... {{ totalPages }}</span>
          </div>
          <button
            @click="page = Math.min(page + 1, totalPages)"
            :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
          >Next</button>
        </div>
      </div>
    </div>

    <!-- Payment Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedPayment" class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background:rgba(15,23,42,0.6);" @click.self="closePaymentDetails">
        <div class="bg-white rounded-2xl border border-gray-200 shadow-2xl w-full overflow-hidden" style="max-width:640px;">
          <div class="px-4 py-4 border-b border-gray-100 flex items-center justify-between sm:px-6">
            <div>
              <p class="text-xs text-gray-400 mb-1">Payment Receipt</p>
              <h3 class="text-sm font-bold text-gray-900">{{ selectedPayment.id }}</h3>
            </div>
            <button @click="closePaymentDetails" class="w-7 h-7 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100">✕</button>
          </div>

          <div class="px-4 py-5 space-y-5 sm:px-6">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
              <div>
                <p class="text-xs text-gray-400 mb-1">Amount Received</p>
                <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(selectedPayment.amount) }}</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(selectedPayment.status)">
                {{ selectedPayment.status }}
              </span>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div class="border border-gray-100 rounded-xl px-4 py-3 bg-gray-50">
                <p class="text-xs text-gray-400 mb-1">Guest / Party</p>
                <p class="text-sm font-semibold text-gray-900">{{ selectedPayment.guest }}</p>
              </div>
              <div class="border border-gray-100 rounded-xl px-4 py-3 bg-gray-50">
                <p class="text-xs text-gray-400 mb-1">Check-in / Folio</p>
                <p class="text-sm font-semibold text-gray-900">{{ selectedPayment.reservation }}</p>
              </div>
              <div class="border border-gray-100 rounded-xl px-4 py-3 bg-gray-50">
                <p class="text-xs text-gray-400 mb-1">Payment Method</p>
                <p class="text-sm font-semibold text-gray-900">{{ selectedPayment.method }}</p>
              </div>
              <div class="border border-gray-100 rounded-xl px-4 py-3 bg-gray-50">
                <p class="text-xs text-gray-400 mb-1">Reference No.</p>
                <p class="text-sm font-semibold text-gray-900">{{ selectedPayment.reference }}</p>
              </div>
            </div>

            <div class="border-t border-gray-100 pt-4">
              <div class="flex items-center justify-between py-2">
                <p class="text-xs text-gray-400">Posting Date</p>
                <p class="text-xs font-semibold text-gray-700">{{ selectedPayment.date }}</p>
              </div>
              <div class="flex items-center justify-between py-2">
                <p class="text-xs text-gray-400">Receipt ID</p>
                <p class="text-xs font-semibold text-gray-700">{{ selectedPayment.id }}</p>
              </div>
            </div>
          </div>

          <div class="px-4 py-4 border-t border-gray-100 flex items-center justify-end sm:px-6">
            <button @click="closePaymentDetails" class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 sm:w-auto">Close</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Receive Payment Modal -->
    <Teleport to="body">
      <div v-if="showReceiveModal" class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background:rgba(15,23,42,0.6);" @click.self="closeReceivePaymentModal">
        <div class="bg-white rounded-2xl border border-gray-200 shadow-2xl w-full" style="max-width:560px;">
          <div class="px-4 py-4 border-b border-gray-100 flex items-center justify-between sm:px-6">
            <h3 class="text-sm font-bold text-gray-900">Receive Payment</h3>
            <button @click="closeReceivePaymentModal" class="w-7 h-7 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100">✕</button>
          </div>

          <div class="px-4 py-5 space-y-4 sm:px-6">
            <div v-if="receiveError" class="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p class="text-xs text-red-600 font-medium">{{ receiveError }}</p>
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-in / Folio <span class="text-red-500">*</span></p>
              <select v-model="receiveForm.check_in" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
                <option value="">Select check-in</option>
                <option v-for="c in checkinOptions" :key="c.name" :value="c.name">
                  {{ c.name }} • {{ c.guest || '—' }} • Room {{ c.room_number || '—' }}
                </option>
              </select>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Amount <span class="text-red-500">*</span></p>
                <input v-model.number="receiveForm.paid_amount" type="number" min="0" step="0.01"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" placeholder="0.00" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Mode of Payment <span class="text-red-500">*</span></p>
                <select v-model="receiveForm.mode_of_payment" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
                  <option value="">Select mode</option>
                  <option v-for="mode in paymentModes" :key="mode.name" :value="mode.name">{{ mode.name }}</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Reference No.</p>
                <input v-model="receiveForm.reference_no" type="text"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" placeholder="Optional" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
                <input v-model="receiveForm.payment_date" type="date"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
              </div>
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">Remarks</p>
              <textarea v-model="receiveForm.remarks" rows="3"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"
                placeholder="Optional note"></textarea>
            </div>
          </div>

          <div class="px-4 py-4 border-t border-gray-100 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end sm:px-6">
            <button @click="closeReceivePaymentModal" class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 sm:w-auto">Cancel</button>
            <button @click="submitReceivePayment" :disabled="receivingPayment"
              class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 sm:w-auto">
              {{ receivingPayment ? 'Processing...' : 'Submit Payment' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { callMethod } from '@/lib/api'

const search = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const filterDate = ref('')
const page = ref(1)
const pageSize = 10
const selectedPayment = ref(null)
const showReceiveModal = ref(false)
const receivingPayment = ref(false)
const receiveError = ref('')
const paymentModes = ref([])
const receiveForm = ref({
  check_in: '',
  paid_amount: '',
  mode_of_payment: '',
  reference_no: '',
  payment_date: new Date().toISOString().slice(0, 10),
  remarks: '',
})

const paymentResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.front_desk.get_payment_list',
  params: { limit: 500 },
  auto: true,
})

const checkInResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.checkin.get_checkin_list',
  params: { limit: 500 },
  auto: true,
})

const checkins = computed(() => checkInResource.data || [])
const checkinOptions = computed(() => checkins.value)

async function loadPaymentModes() {
  const args = {
    doctype: 'Mode of Payment',
    fields: ['name'],
    filters: { enabled: 1 },
    order_by: 'name asc',
    limit_page_length: 500,
  }

  try {
    paymentModes.value = await callMethod('frappe.client.get_list', args) || []
  } catch {
    try {
      const { filters, ...fallbackArgs } = args
      paymentModes.value = await callMethod('frappe.client.get_list', fallbackArgs) || []
    } catch {
      paymentModes.value = []
    }
  }
}

const payments = computed(() => (paymentResource.data || []).map((row) => {
  const amount = Number(row.received_amount || row.paid_amount || 0)
  return {
    id: row.name,
    date: formatPaymentDate(row.posting_date, row.posting_time),
    paymentDate: row.posting_date,
    guest: row.party_name || row.party || '—',
    reservation: row.custom_hotel_room_check_in || '—',
    method: row.mode_of_payment || '—',
    reference: row.reference_no || '—',
    amount,
    status: mapDocstatus(row.docstatus),
  }
}))

const stats = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  const todayPosted = payments.value.filter((p) => p.paymentDate === today && p.status === 'Posted')
  const pending = payments.value.filter((p) => p.status === 'Pending')
  const pendingAmount = checkins.value.reduce((sum, row) => {
    const outstanding = Number(row.total_outstanding ?? row.total_outstanding_amount ?? 0)
    return outstanding > 0 ? sum + outstanding : sum
  }, 0)
  return {
    paymentsToday: todayPosted.length,
    totalCollectedToday: todayPosted.reduce((sum, p) => sum + p.amount, 0),
    unallocated: pending.length,
    pendingAmount,
  }
})

const filteredList = computed(() => {
  let list = payments.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.id.toLowerCase().includes(q) ||
      r.guest.toLowerCase().includes(q) ||
      r.reservation.toLowerCase().includes(q) ||
      r.reference.toLowerCase().includes(q)
    )
  }
  if (filterMethod.value) list = list.filter(r => r.method === filterMethod.value)
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  if (filterDate.value) list = list.filter(r => r.paymentDate === filterDate.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterMethod.value = ''
  filterStatus.value = ''
  filterDate.value = ''
  page.value = 1
}

function statusClass(status) {
  return {
    'Posted': 'bg-green-100 text-green-600',
    'Pending': 'bg-yellow-100 text-yellow-600',
    'Reversed': 'bg-red-100 text-red-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

function formatCurrency(amount) {
  return `₦${Number(amount).toLocaleString('en-NG')}`
}

function mapDocstatus(docstatus) {
  if (Number(docstatus) === 1) return 'Posted'
  if (Number(docstatus) === 2) return 'Reversed'
  return 'Pending'
}

function formatPaymentDate(dateValue, timeValue) {
  if (!dateValue) return '—'
  const baseDate = new Date(dateValue)
  const dateLabel = baseDate.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  if (!timeValue) return dateLabel
  return `${dateLabel} • ${String(timeValue).slice(0, 5)}`
}

function openReceivePayment() {
  receiveError.value = ''
  if (!paymentModes.value.length) loadPaymentModes()
  showReceiveModal.value = true
}

function closeReceivePaymentModal() {
  showReceiveModal.value = false
  receivingPayment.value = false
  receiveError.value = ''
  receiveForm.value = {
    check_in: '',
    paid_amount: '',
    mode_of_payment: '',
    reference_no: '',
    payment_date: new Date().toISOString().slice(0, 10),
    remarks: '',
  }
}

function openPayment(item) {
  if (!item?.id) return
  selectedPayment.value = item
}

function closePaymentDetails() {
  selectedPayment.value = null
}

async function submitReceivePayment() {
  receiveError.value = ''
  const amount = Number(receiveForm.value.paid_amount || 0)
  if (!receiveForm.value.check_in) {
    receiveError.value = 'Please select a check-in / folio.'
    return
  }
  if (amount <= 0) {
    receiveError.value = 'Payment amount must be greater than zero.'
    return
  }
  if (!receiveForm.value.mode_of_payment) {
    receiveError.value = 'Please choose a mode of payment.'
    return
  }

  receivingPayment.value = true
  try {
    await callMethod('rhohotel.rhocom_hotel.api.front_desk.collect_payment_for_checkin', {
      check_in: receiveForm.value.check_in,
      allocations: [],
      payment_info: {
        mode_of_payment: receiveForm.value.mode_of_payment,
        paid_amount: amount,
        reference_no: receiveForm.value.reference_no || '',
        payment_date: receiveForm.value.payment_date || '',
        remarks: receiveForm.value.remarks || '',
      },
    })
    paymentResource.reload()
    checkInResource.reload()
    closeReceivePaymentModal()
  } catch (e) {
    receiveError.value = String(e?.message || 'Failed to receive payment.')
  } finally {
    receivingPayment.value = false
  }
}

watch([search, filterMethod, filterStatus, filterDate], () => {
  page.value = 1
})

onMounted(() => {
  loadPaymentModes()
})
</script>
