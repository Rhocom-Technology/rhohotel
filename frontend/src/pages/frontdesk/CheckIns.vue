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
            128 total check-ins • 41 currently in house • 87 past stays • 6 extended stays • 4 payment follow-ups
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Refresh
          </button>
          <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
            Export List
          </button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
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
        <p class="text-3xl font-bold text-gray-900">128</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Currently In House</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">41</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Checked Out</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Past</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">87</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Payment Follow-up</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">4</p>
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

      <!-- Empty -->
      <div v-if="filteredList.length === 0" class="flex flex-col items-center justify-center py-16">
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

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedCheckIn" class="fixed inset-0 z-50 flex items-center justify-center"
        style="background:rgba(0,0,0,0.55);" @click.self="selectedCheckIn = null">
        <div class="bg-white rounded-2xl shadow-2xl w-full overflow-y-auto mx-4" style="max-width:1000px;max-height:90vh;">
          <CheckInDetail v-if="selectedCheckIn" :check-in="selectedCheckIn" @close="selectedCheckIn = null" />
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { UserCheck } from 'lucide-vue-next'
import CheckInDetail from '@/components/checkin/CheckInDetail.vue'

const search = ref('')
const filterStatus = ref('')
const filterDateRange = ref('month')
const filterPayment = ref('')
const page = ref(1)
const pageSize = 25
const selectedCheckIn = ref(null)

const checkins = [
  { name: 'CHK-2026-000421', guest: 'Sarah Johnson', check_in_date: '15 Apr 2026', check_out_date: '18 Apr 2026', room: '305', source: 'Reservation', payment: 'Paid', stayStatus: 'In House', overdue: false, room_number: '305', check_in_datetime: '2026-04-15', expected_check_out_datetime: '2026-04-18', total_outstanding_amount: 0, reservation_source: 'Reservation', number_of_nights: 3 },
  { name: 'CHK-2026-000420', guest: 'Uche Bassey', check_in_date: '14 Apr 2026', check_out_date: '16 Apr 2026', room: '402', source: 'Corporate', payment: 'Company Bill', stayStatus: 'In House', overdue: false, room_number: '402', check_in_datetime: '2026-04-14', expected_check_out_datetime: '2026-04-16', total_outstanding_amount: 0, reservation_source: 'Corporate', number_of_nights: 2 },
  { name: 'CHK-2026-000419', guest: 'Ngozi Cole', check_in_date: '12 Apr 2026', check_out_date: '13 Apr 2026', room: '511', source: 'Walk-in', payment: 'Balance Due', stayStatus: 'Checked Out', overdue: false, room_number: '511', check_in_datetime: '2026-04-12', expected_check_out_datetime: '2026-04-13', total_outstanding_amount: 41000, reservation_source: 'Walk in', number_of_nights: 1 },
  { name: 'CHK-2026-000418', guest: 'Daniel Ayo', check_in_date: '10 Apr 2026', check_out_date: '14 Apr 2026', room: '118', source: 'Reservation', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '118', check_in_datetime: '2026-04-10', expected_check_out_datetime: '2026-04-14', total_outstanding_amount: 0, reservation_source: 'Reservation', number_of_nights: 4 },
  { name: 'CHK-2026-000417', guest: 'Grace Kelvin', check_in_date: '09 Apr 2026', check_out_date: '12 Apr 2026', room: '219', source: 'Online Booking', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '219', check_in_datetime: '2026-04-09', expected_check_out_datetime: '2026-04-12', total_outstanding_amount: 0, reservation_source: 'Online Booking', number_of_nights: 3 },
  { name: 'CHK-2026-000416', guest: 'Michael Duke', check_in_date: '08 Apr 2026', check_out_date: '13 Apr 2026', room: '603', source: 'Walk-in', payment: 'Balance Due', stayStatus: 'Extended', overdue: true, room_number: '603', check_in_datetime: '2026-04-08', expected_check_out_datetime: '2026-04-13', total_outstanding_amount: 65000, reservation_source: 'Walk in', number_of_nights: 5 },
  { name: 'CHK-2026-000415', guest: 'Blessing Owen', check_in_date: '07 Apr 2026', check_out_date: '10 Apr 2026', room: '214', source: 'Reservation', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '214', check_in_datetime: '2026-04-07', expected_check_out_datetime: '2026-04-10', total_outstanding_amount: 0, reservation_source: 'Reservation', number_of_nights: 3 },
  { name: 'CHK-2026-000414', guest: 'Emeka Adeyemi', check_in_date: '06 Apr 2026', check_out_date: '09 Apr 2026', room: '401', source: 'Corporate', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '401', check_in_datetime: '2026-04-06', expected_check_out_datetime: '2026-04-09', total_outstanding_amount: 0, reservation_source: 'Corporate', number_of_nights: 3 },
  { name: 'CHK-2026-000413', guest: 'Fatima Ahmed', check_in_date: '05 Apr 2026', check_out_date: '08 Apr 2026', room: '312', source: 'Online Booking', payment: 'Balance Due', stayStatus: 'Checked Out', overdue: false, room_number: '312', check_in_datetime: '2026-04-05', expected_check_out_datetime: '2026-04-08', total_outstanding_amount: 28000, reservation_source: 'Online Booking', number_of_nights: 3 },
  { name: 'CHK-2026-000412', guest: 'Tunde Balogun', check_in_date: '04 Apr 2026', check_out_date: '07 Apr 2026', room: '205', source: 'Walk-in', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '205', check_in_datetime: '2026-04-04', expected_check_out_datetime: '2026-04-07', total_outstanding_amount: 0, reservation_source: 'Walk in', number_of_nights: 3 },
  { name: 'CHK-2026-000411', guest: 'Amina Yusuf', check_in_date: '03 Apr 2026', check_out_date: '06 Apr 2026', room: '108', source: 'Reservation', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '108', check_in_datetime: '2026-04-03', expected_check_out_datetime: '2026-04-06', total_outstanding_amount: 0, reservation_source: 'Reservation', number_of_nights: 3 },
  { name: 'CHK-2026-000410', guest: 'Chibuzor Nweke', check_in_date: '02 Apr 2026', check_out_date: '05 Apr 2026', room: '507', source: 'Walk-in', payment: 'Paid', stayStatus: 'Checked Out', overdue: false, room_number: '507', check_in_datetime: '2026-04-02', expected_check_out_datetime: '2026-04-05', total_outstanding_amount: 0, reservation_source: 'Walk in', number_of_nights: 3 },
]

const filteredList = computed(() => {
  let list = checkins
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
  if (!item) return
  selectedCheckIn.value = { ...item }
}
</script>