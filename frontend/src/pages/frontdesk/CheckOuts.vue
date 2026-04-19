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
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Refresh
        </button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
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

      <!-- Empty -->
      <div v-if="filteredList.length === 0" class="flex flex-col items-center justify-center py-16">
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
            >
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ item.name }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ item.guest }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-700">{{ item.room_number }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(item.check_in_datetime) }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(item.actual_check_out_datetime) }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.reservation_source }}</td>
              <td class="px-4 py-4 text-xs font-semibold" :class="(item.total_outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-green-500'">
                {{ (item.total_outstanding_amount || 0) > 0 ? 'Balance Due' : 'Settled' }}
              </td>
              <td class="px-4 py-4">
                <button class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
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
import { ref, computed } from 'vue'
import { LogOut } from 'lucide-vue-next'

const search = ref('')
const filterDateRange = ref('month')
const filterPayment = ref('')
const filterSource = ref('')
const page = ref(1)
const pageSize = 25

const stats = computed(() => ({
  total: 87,
  thisWeek: 12,
  thisMonth: 38,
  balanceFollowUp: 5,
}))

const checkouts = [
  { name: 'FOL-2026-00431', guest: 'Sarah Johnson', room_number: '305', check_in_datetime: '2026-04-15', actual_check_out_datetime: '2026-04-18', reservation_source: 'Reservation', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00430', guest: 'Daniel Ayo', room_number: '118', check_in_datetime: '2026-04-10', actual_check_out_datetime: '2026-04-14', reservation_source: 'Reservation', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00429', guest: 'Grace Kelvin', room_number: '219', check_in_datetime: '2026-04-09', actual_check_out_datetime: '2026-04-12', reservation_source: 'Online Booking', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00428', guest: 'Ngozi Cole', room_number: '511', check_in_datetime: '2026-04-12', actual_check_out_datetime: '2026-04-13', reservation_source: 'Walk in', total_outstanding_amount: 41000 },
  { name: 'FOL-2026-00427', guest: 'Michael Duke', room_number: '603', check_in_datetime: '2026-04-05', actual_check_out_datetime: '2026-04-08', reservation_source: 'Walk in', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00426', guest: 'Blessing Owen', room_number: '214', check_in_datetime: '2026-04-03', actual_check_out_datetime: '2026-04-06', reservation_source: 'Reservation', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00425', guest: 'Emeka Adeyemi', room_number: '401', check_in_datetime: '2026-04-01', actual_check_out_datetime: '2026-04-05', reservation_source: 'Corporate', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00424', guest: 'Fatima Ahmed', room_number: '312', check_in_datetime: '2026-03-28', actual_check_out_datetime: '2026-04-02', reservation_source: 'Online Booking', total_outstanding_amount: 25000 },
  { name: 'FOL-2026-00423', guest: 'Tunde Balogun', room_number: '205', check_in_datetime: '2026-03-25', actual_check_out_datetime: '2026-03-30', reservation_source: 'Walk in', total_outstanding_amount: 0 },
  { name: 'FOL-2026-00422', guest: 'Amina Yusuf', room_number: '108', check_in_datetime: '2026-03-22', actual_check_out_datetime: '2026-03-26', reservation_source: 'Reservation', total_outstanding_amount: 0 },
]

const filteredList = computed(() => {
  let list = checkouts
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
</script>