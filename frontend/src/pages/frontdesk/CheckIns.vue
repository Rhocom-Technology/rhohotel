<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Front Desk / Check-ins</p>
      <h1 class="text-2xl font-bold text-gray-900">All Check-ins</h1>
      <p class="text-xs text-gray-400 mt-1">View current and previous check-ins, stay history, room movement, payment standing, and guest activity from a single list.</p>
    </div>

    <!-- Overview Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-start justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-900">Check-in Overview</h2>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ stats.total }} total check-ins • {{ stats.inHouse }} currently in house • {{ stats.checkedOut }} past stays • {{ stats.extended }} extended stays • {{ stats.paymentFollowUp }} payment follow-ups
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="refreshData" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Refresh
          </button>
          <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
            Export List
          </button>
          <button @click="router.push('/check-ins/new')" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            New Check-in
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Check-ins</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All Time</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Currently In House</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.inHouse }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Checked Out</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Past</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.checkedOut }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Payment Follow-up</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.paymentFollowUp }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">Search guest / check-in</p>
          <input
            v-model="search"
            type="text"
            placeholder="Guest name, folio, room, reservation..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Stay Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Stays</option>
            <option value="In House">In House</option>
            <option value="Checked Out">Checked Out</option>
            <option value="Extended">Extended</option>
          </select>
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
            <option value="paid">Paid</option>
            <option value="outstanding">Balance Due</option>
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
        <h3 class="text-sm font-bold text-gray-900">Check-in Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ paginatedList.length }} of {{ filteredList.length }} check-ins</p>
      </div>

      <div v-if="checkInResource.loading" class="flex items-center justify-center py-14">
        <p class="text-sm text-gray-400">Loading check-ins...</p>
      </div>

      <div v-else-if="checkInResource.error" class="px-6 py-10 text-center">
        <p class="text-sm font-medium text-red-500">Unable to load check-ins.</p>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredList.length === 0" class="flex flex-col items-center justify-center py-16">
        <UserCheck class="w-10 h-10 text-gray-200 mb-3" />
        <p class="text-sm font-medium text-gray-400">No check-ins found</p>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Check-in No.</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest Name</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Check-in Date</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Check-out Date</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Room</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Source</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Payment</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Stay Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="item in paginatedList"
              :key="item.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="openDetail(item)"
            >
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ item.name }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ item.guest }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.check_in_date }}</td>
              <td class="px-4 py-4 text-xs" :class="item.overdue ? 'text-red-400 line-through' : 'text-gray-600'">
                {{ item.check_out_date }}
              </td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-700">{{ item.room }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.source }}</td>
              <td class="px-4 py-4 text-xs font-semibold" :class="item.payment === 'Balance Due' ? 'text-red-500' : 'text-green-500'">
                {{ item.payment }}
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="stayStatusClass(item.stayStatus)">
                  {{ item.stayStatus }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="openDetail(item)"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  View
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
import { UserCheck } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'
import { useRouter } from 'vue-router'
const router = useRouter()

const search = ref('')
const filterStatus = ref('')
const filterDateRange = ref('month')
const filterPayment = ref('')
const page = ref(1)
const pageSize = 25


const checkInResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Room Check In',
    fields: [
      'name',
      'guest',
      'room_number',
      'check_in_datetime',
      'expected_check_out_datetime',
      'actual_check_out_datetime',
      'status',
      'reservation_source',
      'total_outstanding_amount',
      'number_of_nights',
    ],
    order_by: 'check_in_datetime desc',
    limit_page_length: 500,
  },
  auto: true,
})

const checkins = computed(() => (checkInResource.data || []).map((row) => {
  const overdue = isOverdue(row)
  const stayStatus = mapStayStatus(row.status, overdue)
  const payment = Number(row.total_outstanding_amount || 0) > 0 ? 'Balance Due' : 'Paid'
  return {
    ...row,
    guest: row.guest || '—',
    room: row.room_number || '—',
    source: row.reservation_source || 'Walk In',
    payment,
    stayStatus,
    overdue,
    check_in_date: formatDate(row.check_in_datetime),
    check_out_date: formatDate(row.actual_check_out_datetime || row.expected_check_out_datetime),
  }
}))

const stats = computed(() => {
  const list = checkins.value
  const inHouse = list.filter((r) => r.stayStatus === 'In House').length
  const extended = list.filter((r) => r.stayStatus === 'Extended').length
  return {
    total: list.length,
    inHouse,
    checkedOut: list.filter((r) => r.stayStatus === 'Checked Out').length,
    extended,
    paymentFollowUp: list.filter((r) => Number(r.total_outstanding_amount || 0) > 0).length,
  }
})

const filteredList = computed(() => {
  let list = checkins.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.guest.toLowerCase().includes(q) ||
      r.name.toLowerCase().includes(q) ||
      r.room.toLowerCase().includes(q) ||
      r.source.toLowerCase().includes(q)
    )
  }
  if (filterStatus.value) list = list.filter(r => r.stayStatus === filterStatus.value)
  if (filterPayment.value === 'paid') list = list.filter(r => r.payment === 'Paid' || r.payment === 'Company Bill')
  if (filterPayment.value === 'outstanding') list = list.filter(r => r.payment === 'Balance Due')
  list = list.filter(r => inDateRange(r.check_in_datetime, filterDateRange.value))
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function stayStatusClass(s) {
  return {
    'In House': 'bg-green-100 text-green-600',
    'Checked Out': 'bg-gray-100 text-gray-500',
    'Extended': 'bg-yellow-100 text-yellow-600',
    'Cancelled': 'bg-red-100 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

function clearFilters() {
  search.value = ''
  filterStatus.value = ''
  filterDateRange.value = 'month'
  filterPayment.value = ''
  page.value = 1
}

function openDetail(item) {
  if (!item?.name) return
  router.push('/check-ins/' + item.name)
}
function refreshData() {
  checkInResource.reload()
}

function mapStayStatus(status, overdue) {
  if (status === 'Checked In' && overdue) return 'Extended'
  if (status === 'Checked In') return 'In House'
  if (status === 'Checked Out') return 'Checked Out'
  return status || 'Draft'
}

function isOverdue(item) {
  if (item.status !== 'Checked In' || !item.expected_check_out_datetime) return false
  return new Date(item.expected_check_out_datetime) < new Date()
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
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

watch([search, filterStatus, filterDateRange, filterPayment], () => {
  page.value = 1
})
</script>