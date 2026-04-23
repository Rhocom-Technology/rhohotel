<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Review POS invoices across outlets, monitor payment method usage, and trace posted room charges, drafts, and settlement records.</p>
    </div>

    <!-- Invoice Overview -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Invoice Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">1,284 invoices this month • 3 outlets • invoices from restaurant, bar, mini-mart, and room-posting transactions</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Invoices</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Create POS Invoice</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Invoices Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">98</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Invoice Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦3.86M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Room-Posted Invoices</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Track</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">24</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Voided / Cancelled</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">6</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search invoice</p>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            <input v-model="search" type="text" placeholder="Invoice no., guest, cashier, room..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Outlet</p>
          <select v-model="filterOutlet" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Outlets</option>
            <option>Restaurant</option>
            <option>Bar Lounge</option>
            <option>Retail Corner</option>
            <option>Room Service</option>
          </select>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Method</p>
          <select v-model="filterMethod" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Methods</option>
            <option>Cash</option>
            <option>POS</option>
            <option>Post to Room</option>
            <option>Split</option>
            <option>Transfer</option>
          </select>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Invoice Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option>Posted</option>
            <option>Paid</option>
            <option>Pending</option>
            <option>Void</option>
          </select>
        </div>
        <button @click="resetFilters" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply Filter</button>
      </div>
    </div>

    <!-- Invoice Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Invoice Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} invoices</p>
      </div>

      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date / Time</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outlet</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Customer / Target</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Method</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paged.length === 0">
            <td colspan="8" class="text-center py-12 text-xs text-gray-400">No invoices match your filters</td>
          </tr>
          <tr v-for="inv in paged" :key="inv.id"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors cursor-pointer">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ inv.no }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.datetime }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.outlet }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.cashier }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ inv.customer }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.method }}</td>
            <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ inv.amount.toLocaleString() }}</td>
            <td class="px-4 py-4">
              <span class="px-3 py-1 text-xs font-semibold rounded-full"
                :class="statusClass(inv.status)">
                {{ inv.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: {{ perPage }}</p>
        <div class="flex items-center gap-1">
          <button v-for="p in visiblePages" :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="p === currentPage
              ? 'bg-blue-600 text-white font-semibold'
              : p === '...'
                ? 'text-gray-400 cursor-default'
                : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages && currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed ml-1 transition-colors">
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// ── Filters ────────────────────────────────────────────────────────
const search = ref('')
const filterOutlet = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 10

function resetFilters() {
  search.value = ''
  filterOutlet.value = ''
  filterMethod.value = ''
  filterStatus.value = ''
  currentPage.value = 1
}

// ── Dummy Data ─────────────────────────────────────────────────────
const invoices = [
  { id: 1,  no: 'POS-2026-00184', datetime: '15 Apr • 10:46 AM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 305 • Sarah Johnson',        method: 'Post to Room', amount: 40365,  status: 'Posted' },
  { id: 2,  no: 'POS-2026-00183', datetime: '15 Apr • 10:38 AM', outlet: 'Bar Lounge',    cashier: 'Ifeoma', customer: 'Walk In',                          method: 'POS',          amount: 18000,  status: 'Paid' },
  { id: 3,  no: 'POS-2026-00182', datetime: '15 Apr • 10:20 AM', outlet: 'Restaurant',    cashier: 'Boma',   customer: 'Table 02 • Guest 2',               method: 'Split',        amount: 62800,  status: 'Paid' },
  { id: 4,  no: 'POS-2026-00181', datetime: '15 Apr • 10:12 AM', outlet: 'Retail Corner', cashier: 'Boma',   customer: 'Walk In',                          method: 'Cash',         amount: 9500,   status: 'Paid' },
  { id: 5,  no: 'POS-2026-00180', datetime: '15 Apr • 10:03 AM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Draft Conversion • Room 511',       method: 'Post to Room', amount: 27500,  status: 'Pending' },
  { id: 6,  no: 'POS-2026-00179', datetime: '15 Apr • 09:56 AM', outlet: 'Bar Lounge',    cashier: 'Ifeoma', customer: 'Walk In',                          method: 'POS',          amount: 15500,  status: 'Void' },
  { id: 7,  no: 'POS-2026-00178', datetime: '15 Apr • 09:44 AM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 214 • Chinedu Okafor',         method: 'Post to Room', amount: 33000,  status: 'Posted' },
  { id: 8,  no: 'POS-2026-00177', datetime: '15 Apr • 09:31 AM', outlet: 'Bar Lounge',    cashier: 'Boma',   customer: 'Table 04 • Guest 3',               method: 'Cash',         amount: 22500,  status: 'Paid' },
  { id: 9,  no: 'POS-2026-00176', datetime: '15 Apr • 09:18 AM', outlet: 'Restaurant',    cashier: 'Ifeoma', customer: 'Walk In',                          method: 'POS',          amount: 14000,  status: 'Paid' },
  { id: 10, no: 'POS-2026-00175', datetime: '15 Apr • 09:05 AM', outlet: 'Retail Corner', cashier: 'Boma',   customer: 'Walk In',                          method: 'Cash',         amount: 7500,   status: 'Paid' },
  { id: 11, no: 'POS-2026-00174', datetime: '15 Apr • 08:58 AM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 402 • Uche Bassey',            method: 'Post to Room', amount: 48500,  status: 'Posted' },
  { id: 12, no: 'POS-2026-00173', datetime: '15 Apr • 08:45 AM', outlet: 'Bar Lounge',    cashier: 'Ifeoma', customer: 'Table 06 • Guest 5',               method: 'Split',        amount: 72500,  status: 'Paid' },
  { id: 13, no: 'POS-2026-00172', datetime: '15 Apr • 08:30 AM', outlet: 'Restaurant',    cashier: 'Boma',   customer: 'Walk In',                          method: 'Cash',         amount: 11000,  status: 'Paid' },
  { id: 14, no: 'POS-2026-00171', datetime: '15 Apr • 08:17 AM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 118 • Daniel Ayo',             method: 'Post to Room', amount: 19500,  status: 'Pending' },
  { id: 15, no: 'POS-2026-00170', datetime: '15 Apr • 08:04 AM', outlet: 'Bar Lounge',    cashier: 'Boma',   customer: 'Walk In',                          method: 'POS',          amount: 8500,   status: 'Void' },
  { id: 16, no: 'POS-2026-00169', datetime: '14 Apr • 11:52 PM', outlet: 'Restaurant',    cashier: 'Ngozi',  customer: 'Table 01 • Guest 4',               method: 'Cash',         amount: 55000,  status: 'Paid' },
  { id: 17, no: 'POS-2026-00168', datetime: '14 Apr • 11:35 PM', outlet: 'Bar Lounge',    cashier: 'Ngozi',  customer: 'Walk In',                          method: 'POS',          amount: 31000,  status: 'Paid' },
  { id: 18, no: 'POS-2026-00167', datetime: '14 Apr • 11:18 PM', outlet: 'Restaurant',    cashier: 'Ngozi',  customer: 'Room 511 • Ngozi Cole',             method: 'Post to Room', amount: 22000,  status: 'Posted' },
  { id: 19, no: 'POS-2026-00166', datetime: '14 Apr • 10:55 PM', outlet: 'Retail Corner', cashier: 'Adaeze', customer: 'Walk In',                          method: 'Cash',         amount: 5500,   status: 'Paid' },
  { id: 20, no: 'POS-2026-00165', datetime: '14 Apr • 10:40 PM', outlet: 'Restaurant',    cashier: 'Boma',   customer: 'Table 08 • Guest 2',               method: 'Split',        amount: 44000,  status: 'Paid' },
  { id: 21, no: 'POS-2026-00164', datetime: '14 Apr • 10:22 PM', outlet: 'Bar Lounge',    cashier: 'Ifeoma', customer: 'Walk In',                          method: 'POS',          amount: 17500,  status: 'Paid' },
  { id: 22, no: 'POS-2026-00163', datetime: '14 Apr • 10:05 PM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 305 • Sarah Johnson',          method: 'Post to Room', amount: 29000,  status: 'Posted' },
  { id: 23, no: 'POS-2026-00162', datetime: '14 Apr • 09:48 PM', outlet: 'Restaurant',    cashier: 'Ngozi',  customer: 'Walk In',                          method: 'Cash',         amount: 13500,  status: 'Paid' },
  { id: 24, no: 'POS-2026-00161', datetime: '14 Apr • 09:30 PM', outlet: 'Bar Lounge',    cashier: 'Boma',   customer: 'Table 04 • Guest 3',               method: 'Transfer',     amount: 38500,  status: 'Paid' },
  { id: 25, no: 'POS-2026-00160', datetime: '14 Apr • 09:12 PM', outlet: 'Restaurant',    cashier: 'Ifeoma', customer: 'Walk In',                          method: 'POS',          amount: 21000,  status: 'Void' },
  { id: 26, no: 'POS-2026-00159', datetime: '14 Apr • 08:55 PM', outlet: 'Room Service',  cashier: 'Adaeze', customer: 'Room 401 • Fatima Ahmed',           method: 'Post to Room', amount: 16500,  status: 'Posted' },
  { id: 27, no: 'POS-2026-00158', datetime: '14 Apr • 08:38 PM', outlet: 'Restaurant',    cashier: 'Boma',   customer: 'Table 02 • Guest 6',               method: 'Cash',         amount: 47000,  status: 'Paid' },
  { id: 28, no: 'POS-2026-00157', datetime: '14 Apr • 08:20 PM', outlet: 'Bar Lounge',    cashier: 'Ngozi',  customer: 'Walk In',                          method: 'POS',          amount: 9000,   status: 'Paid' },
  { id: 29, no: 'POS-2026-00156', datetime: '14 Apr • 08:05 PM', outlet: 'Restaurant',    cashier: 'Adaeze', customer: 'Room 214 • Chinedu Okafor',         method: 'Post to Room', amount: 34500,  status: 'Posted' },
  { id: 30, no: 'POS-2026-00155', datetime: '14 Apr • 07:48 PM', outlet: 'Retail Corner', cashier: 'Ifeoma', customer: 'Walk In',                          method: 'Cash',         amount: 6800,   status: 'Paid' },
]

// ── Computed ───────────────────────────────────────────────────────
const filtered = computed(() => {
  let data = invoices
  if (search.value) {
    const q = search.value.toLowerCase()
    data = data.filter(i =>
      i.no.toLowerCase().includes(q) ||
      i.cashier.toLowerCase().includes(q) ||
      i.customer.toLowerCase().includes(q) ||
      i.outlet.toLowerCase().includes(q)
    )
  }
  if (filterOutlet.value) data = data.filter(i => i.outlet === filterOutlet.value)
  if (filterMethod.value) data = data.filter(i => i.method === filterMethod.value)
  if (filterStatus.value) data = data.filter(i => i.status === filterStatus.value)
  return data
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(filtered, () => { currentPage.value = 1 })

// ── Helpers ────────────────────────────────────────────────────────
function statusClass(status) {
  return {
    'Posted':  'bg-blue-50 text-blue-600',
    'Paid':    'bg-green-50 text-green-600',
    'Pending': 'bg-yellow-50 text-yellow-600',
    'Void':    'bg-red-50 text-red-500',
  }[status] || 'bg-gray-100 text-gray-500'
}
</script>