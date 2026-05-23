<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Front desk • checked-out guest records</p>
      <p class="text-xs text-gray-500 mt-2">View previous completed departures, folio history, payment settlement, and guest check-out records.</p>
    </div>

    <!-- Overview Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Check-out Record Overview</h2>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ stats.total }} checked-out stays • {{ stats.thisWeek }} this week • {{ stats.thisMonth }} this month • {{ stats.balanceFollowUp }} with balance follow-up
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="refreshData" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Refresh
        </button>
        <button @click="exportCheckOuts" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
          Export List
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Checked Out</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Records</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">Recent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.thisWeek }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">Month</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.thisMonth }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Balance Follow-up</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.balanceFollowUp }}</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search guest / folio</p>
          <input
            v-model="search"
            type="text"
            placeholder="Guest name, folio, room, booking..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Date Range</p>
          <select v-model="filterDateRange" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="month">This Month</option>
            <option value="week">This Week</option>
            <option value="today">Today</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Status</p>
          <select v-model="filterPayment" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Payments</option>
            <option value="settled">Settled</option>
            <option value="balance">Balance Due</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Source</p>
          <select v-model="filterSource" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Sources</option>
            <option value="Walk in">Walk-in</option>
            <option value="Reservation">Reservation</option>
            <option value="Online Booking">Online Booking</option>
            <option value="Corporate">Corporate</option>
          </select>
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Apply Filter</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Checked-out Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ Math.min(pageSize, filteredList.length) }} of {{ filteredList.length }} records</p>
      </div>

      <div v-if="checkOutResource.loading" class="flex items-center justify-center py-14">
        <p class="text-sm text-gray-400">Loading check-outs...</p>
      </div>

      <div v-else-if="checkOutResource.error" class="px-6 py-10 text-center">
        <p class="text-sm font-medium text-red-500">Unable to load check-out records.</p>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredList.length === 0" class="flex flex-col items-center justify-center py-16">
        <LogOut class="w-10 h-10 text-gray-200 mb-3" />
        <p class="text-sm font-medium text-gray-400">No check-out records found</p>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Folio No.</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest Name</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Room</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Check-in Date</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Check-out Date</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Source</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Payment</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="item in paginatedList"
              :key="item.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="$router.push('/check-outs/' + item.name)"
            >
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ item.name }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ item.guest }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-700">{{ item.room_number }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(item.check_in_datetime) }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(item.actual_check_out_datetime || item.expected_check_out_datetime) }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.reservation_source }}</td>
              <td class="px-4 py-4 text-xs font-semibold" :class="(item.total_outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-green-500'">
                {{ (item.total_outstanding_amount || 0) > 0 ? 'Balance Due' : 'Settled' }}
              </td>
              <td class="px-4 py-4">
                <button @click.stop="$router.push('/check-outs/' + item.name)"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  {{ (item.total_outstanding_amount || 0) > 0 ? 'Review' : 'View' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="filteredList.length > 0" class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button v-for="p in Math.min(totalPages, 5)" :key="p" @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center transition-colors"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'">{{ p }}</button>
            <span v-if="totalPages > 5" class="text-xs text-gray-400">... {{ totalPages }}</span>
          </div>
          <button @click="page = Math.min(page + 1, totalPages)" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { LogOut } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'
import { useRouter } from 'vue-router'
const router = useRouter()

const search = ref('')
const filterDateRange = ref('month')
const filterPayment = ref('')
const filterSource = ref('')
const page = ref(1)
const pageSize = 25

const checkOutResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Room Check In',
    fields: [
      'name',
      'guest',
      'room_number',
      'check_in_datetime',
      'actual_check_out_datetime',
      'expected_check_out_datetime',
      'reservation_source',
      'total_outstanding_amount',
      'status',
    ],
    filters: [['status', '=', 'Checked Out']],
    order_by: 'actual_check_out_datetime desc',
    limit_page_length: 500,
  },
  auto: true,
})

const checkouts = computed(() => (checkOutResource.data || []).map((row) => ({
  ...row,
  guest: row.guest || '—',
  reservation_source: row.reservation_source || 'Walk In',
  check_out_date_value: row.actual_check_out_datetime || row.expected_check_out_datetime,
})))

const stats = computed(() => ({
  total: checkouts.value.length,
  thisWeek: checkouts.value.filter((r) => inDateRange(r.check_out_date_value, 'week')).length,
  thisMonth: checkouts.value.filter((r) => inDateRange(r.check_out_date_value, 'month')).length,
  balanceFollowUp: checkouts.value.filter((r) => Number(r.total_outstanding_amount || 0) > 0).length,
}))

const filteredList = computed(() => {
  let list = checkouts.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.guest?.toLowerCase().includes(q) ||
      r.name?.toLowerCase().includes(q) ||
      r.room_number?.toLowerCase().includes(q)
    )
  }
  if (filterPayment.value === 'settled') list = list.filter(r => (r.total_outstanding_amount || 0) === 0)
  if (filterPayment.value === 'balance') list = list.filter(r => (r.total_outstanding_amount || 0) > 0)
  if (filterSource.value) list = list.filter(r => r.reservation_source === filterSource.value)
  list = list.filter((r) => inDateRange(r.check_out_date_value, filterDateRange.value))
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterDateRange.value = 'month'
  filterPayment.value = ''
  filterSource.value = ''
  page.value = 1
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function inDateRange(dateValue, rangeKey) {
  if (!dateValue || rangeKey === 'all') return true
  const value = new Date(dateValue)
  if (Number.isNaN(value.getTime())) return false
  const now = new Date()
  const start = new Date(now)

  if (rangeKey === 'today') {
    start.setHours(0, 0, 0, 0)
    return value >= start
  }
  if (rangeKey === 'week') {
    start.setDate(now.getDate() - 7)
    return value >= start
  }
  if (rangeKey === 'month') {
    start.setMonth(now.getMonth() - 1)
    return value >= start
  }
  return true
}

function refreshData() {
  checkOutResource.reload()
}

function exportCheckOuts() {
  const rows = filteredList.value
  if (!rows.length) return alert('No check-out records to export.')

  const header = ['Folio No.', 'Guest', 'Room', 'Check-in Date', 'Check-out Date', 'Source', 'Payment']
  const csv = [header.join(',')]

  for (const r of rows) {
    csv.push([
      r.name,
      r.guest,
      r.room_number,
      formatDate(r.check_in_datetime),
      formatDate(r.actual_check_out_datetime || r.expected_check_out_datetime),
      r.reservation_source,
      (r.total_outstanding_amount || 0) > 0 ? 'Balance Due' : 'Settled',
    ].map(x => '"' + String(x).replace(/"/g, '""') + '"').join(','))
  }

  const blob = new Blob([csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'checkouts.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

watch([search, filterDateRange, filterPayment, filterSource], () => {
  page.value = 1
})
</script>