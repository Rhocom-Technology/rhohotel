<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Billing / Payment List</p>
      <h1 class="text-2xl font-bold text-gray-900">Payment List</h1>
      <p class="text-xs text-gray-400 mt-1">Track all front desk payment transactions, balances, methods, references, and posting status.</p>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
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
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search payment</p>
          <input
            v-model="search"
            type="text"
            placeholder="Receipt no., guest, reservation..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Method</p>
          <select v-model="filterMethod" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Methods</option>
            <option value="Cash">Cash</option>
            <option value="Card">Card</option>
            <option value="POS">POS</option>
            <option value="Bank Transfer">Bank Transfer</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Posting Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="Posted">Posted</option>
            <option value="Pending">Pending</option>
            <option value="Reversed">Reversed</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
          <input v-model="filterDate" type="date" placeholder="Today"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600" />
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Receive Payment</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
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
        <table class="w-full">
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
                <button class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors">
                  Open
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
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

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const search = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const filterDate = ref('')
const page = ref(1)
const pageSize = 10

const paymentResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Payment Entry',
    fields: [
      'name',
      'posting_date',
      'posting_time',
      'mode_of_payment',
      'reference_no',
      'party',
      'party_name',
      'paid_amount',
      'received_amount',
      'custom_hotel_room_check_in',
      'docstatus',
    ],
    order_by: 'posting_date desc, modified desc',
    limit_page_length: 500,
  },
  auto: true,
})

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
  return {
    paymentsToday: todayPosted.length,
    totalCollectedToday: todayPosted.reduce((sum, p) => sum + p.amount, 0),
    unallocated: pending.length,
    pendingAmount: pending.reduce((sum, p) => sum + p.amount, 0),
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

watch([search, filterMethod, filterStatus, filterDate], () => {
  page.value = 1
})
</script>