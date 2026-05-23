<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Daily Occupancy Report</h1>
      <p class="text-xs text-gray-400 mt-1">
        Report-style page with operational, billing, payment status, and creator tracking columns.
      </p>
    </div>

    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <p class="text-xs font-bold text-red-700">Unable to load report</p>
      <p class="text-xs text-red-600 mt-1">{{ errorMessage }}</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Occupancy Rate</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.occupancyRate }}%</p>
        <p class="text-[10px] text-gray-400 mt-1">current utilization</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Occupied Rooms</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.occupiedRooms }}</p>
        <p class="text-[10px] text-gray-400 mt-1">active guests</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Vacant Rooms</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.vacantRooms }}</p>
        <p class="text-[10px] text-gray-400 mt-1">available for sale</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Arrivals / Departures</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.arrivals }} / {{ stats.departures }}</p>
        <p class="text-[10px] text-gray-400 mt-1">today's movement</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(stats.outstanding) }}</p>
        <p class="text-[10px] text-gray-400 mt-1">unpaid balances</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-orange-500">
        <p class="text-xs text-gray-400 mb-1">Overdue Check-Out</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.overdueCheckOut }}</p>
        <p class="text-[10px] text-gray-400 mt-1">needs follow-up</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input
            v-model="filters.dateFrom"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input
            v-model="filters.dateTo"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Room</p>
          <select
            v-model="filters.room"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Rooms</option>
            <option v-for="r in uniqueRooms" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Floor</p>
          <select
            v-model="filters.floor"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Floors</option>
            <option value="8">Floor 8</option>
            <option value="7">Floor 7</option>
            <option value="6">Floor 6</option>
            <option value="5">Floor 5</option>
            <option value="4">Floor 4</option>
            <option value="3">Floor 3</option>
            <option value="2">Floor 2</option>
            <option value="1">Floor 1</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
          <select
            v-model="filters.status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Status</option>
            <option>Occupied</option>
            <option>Vacant Clean</option>
            <option>Vacant Dirty</option>
            <option>Overdue Check-Out</option>
            <option>Maintenance</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment</p>
          <select
            v-model="filters.payment"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Payment</option>
            <option>Paid</option>
            <option>Part Payment</option>
            <option>Unpaid</option>
          </select>
        </div>

        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search guest, room, check-in ID..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          @click="fetchReport"
          :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Loading...' : 'Apply' }}
        </button>

        <button
          @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>

        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="toggleOverdueOnly"
        >
          {{ showOverdueOnly ? 'Show All' : 'Show Overdue Only' }}
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Occupancy Records</h3>

        <div class="flex items-center gap-3">
          <p class="text-xs text-gray-400">{{ filteredRows.length }} records</p>

          <button
            @click="exportReport"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Export
          </button>

          <button
            @click="printReport"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Print
          </button>
        </div>
      </div>

      <div v-if="loading" class="py-12 text-center">
        <p class="text-xs text-gray-400">Loading occupancy report...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full" style="min-width:1200px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>
              <th class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('checkin_id')">
                Check In ID<span v-if="sortKey === 'checkin_id'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('room_number')">
                Room<span v-if="sortKey === 'room_number'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
              <th class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('status')">
                Status<span v-if="sortKey === 'status'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Check-In</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Check-Out</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Nights</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Rate</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Discount</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Paid</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outstanding</th>
              <th class="min-w-[120px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('payment_status')">
                Payment<span v-if="sortKey === 'payment_status'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="min-w-[120px] text-left text-xs font-medium text-gray-500 px-4 py-3.5">Created By</th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="paginatedRows.length === 0">
              <td colspan="16" class="text-center py-12 text-xs text-gray-400">
                No records match your filters.
              </td>
            </tr>

            <tr
              v-for="(row, idx) in paginatedRows"
              :key="row.checkin_id || row.room_number"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
              :class="row.status === 'Overdue Check-Out' ? 'bg-red-50/30 hover:bg-red-50/50' : ''"
            >
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>

              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                  {{ row.checkin_id || '—' }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs font-bold text-gray-900">{{ row.room_number }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.room_type || '—' }}</td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="roomStatusClass(row.status)">
                  {{ row.status }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-700 font-medium">{{ row.guest || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.checkin || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.checkout || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700 text-center">{{ row.nights || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700 whitespace-nowrap">{{ row.rate ? '₦' + formatNumber(row.rate) : '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.discount ? '₦' + formatNumber(row.discount) : '—' }}</td>
              <td class="px-4 py-3.5 text-xs font-bold text-gray-900 whitespace-nowrap">{{ row.amount ? '₦' + formatNumber(row.amount) : '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-green-600 font-semibold whitespace-nowrap">{{ row.paid_amount ? '₦' + formatNumber(row.paid_amount) : '—' }}</td>

              <td class="px-4 py-3.5 text-xs font-semibold whitespace-nowrap" :class="row.outstanding > 0 ? 'text-red-600' : 'text-gray-400'">
                {{ row.outstanding ? '₦' + formatNumber(row.outstanding) : '₦0' }}
              </td>

              <td class="px-4 py-3.5">
                <span
                  v-if="row.payment_status"
                  class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full"
                  :class="paymentClass(row.payment_status)"
                >
                  {{ row.payment_status }}
                </span>
                <span v-else class="text-gray-300 text-[10px]">—</span>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-500">{{ row.created_by || '—' }}</td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="8" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900 text-center">{{ totals.nights }}</td>
              <td class="px-4 py-4"></td>
              <td class="px-4 py-4 text-xs font-bold text-gray-500">₦{{ formatNumber(totals.discount) }}</td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ formatNumber(totals.amount) }}</td>
              <td class="px-4 py-4 text-xs font-bold text-green-700">₦{{ formatNumber(totals.paid_amount) }}</td>
              <td class="px-4 py-4 text-xs font-bold text-red-600">₦{{ formatNumber(totals.outstanding) }}</td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">
          Showing {{ filteredRows.length ? (currentPage - 1) * pageSize + 1 : 0 }}–{{ Math.min(currentPage * pageSize, filteredRows.length) }} of {{ filteredRows.length }} records
        </p>

        <div class="flex items-center gap-1">
          <button @click="currentPage = 1" :disabled="currentPage === 1" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">«</button>
          <button @click="currentPage--" :disabled="currentPage === 1" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">‹</button>

          <button
            v-for="p in visiblePages"
            :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="p === currentPage ? 'bg-blue-600 text-white font-semibold' : p === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-gray-50 border border-gray-200'"
          >
            {{ p }}
          </button>

          <button @click="currentPage++" :disabled="currentPage === totalPages" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">›</button>
          <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">»</button>

          <select v-model="pageSize" @change="currentPage = 1" class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        Front office note: Overdue departures and unpaid rooms are highlighted for follow-up, extension handling, and settlement.
      </p>
      <p class="text-xs text-gray-400">Generated: {{ generatedAt || '—' }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { callMethodForm } from '@/lib/api'

const route = useRoute()

const loading = ref(false)
const errorMessage = ref('')
const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)
const showOverdueOnly = ref(false)
const generatedAt = ref('')

const today = new Date().toISOString().slice(0, 10)

const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 7)

const filters = ref({
  dateFrom: fromDate.toISOString().slice(0, 10),
  dateTo: today,
  room: '',
  floor: '',
  status: '',
  payment: '',
})

const allRows = ref([])
const uniqueRooms = ref([])

const stats = ref({
  occupancyRate: 0,
  occupiedRooms: 0,
  vacantRooms: 0,
  arrivals: 0,
  departures: 0,
  outstanding: 0,
  overdueCheckOut: 0,
})

const totals = ref({
  nights: 0,
  discount: 0,
  amount: 0,
  paid_amount: 0,
  outstanding: 0,
})

let searchTimer = null

onMounted(async () => {
  await fetchReport()

  if (route.query.action === 'print') {
    setTimeout(() => window.print(), 300)
  }

  if (route.query.action === 'download') {
    setTimeout(() => exportReport(), 300)
  }
})

watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchReport()
  }, 450)
})

watch(
  () => [filters.value.room, filters.value.floor, filters.value.status, filters.value.payment],
  () => fetchReport()
)

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  try {
    const result = await callMethodForm('rhohotel.rhocom_hotel.api.daily_occupany_report.get_daily_occupancy_report', {
      date_from: filters.value.dateFrom,
      date_to: filters.value.dateTo,
      room: filters.value.room,
      floor: filters.value.floor,
      status: filters.value.status,
      payment: filters.value.payment,
      search: searchQuery.value,
      overdue_only: showOverdueOnly.value ? 1 : 0,
    })

    allRows.value = result?.rows || []
    uniqueRooms.value = result?.rooms || []
    stats.value = result?.stats || stats.value
    totals.value = result?.totals || totals.value
    generatedAt.value = result?.generated_at || ''
    currentPage.value = 1
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading this report.'
    allRows.value = []
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    dateFrom: today,
    dateTo: today,
    room: '',
    floor: '',
    status: '',
    payment: '',
  }

  searchQuery.value = ''
  showOverdueOnly.value = false
  currentPage.value = 1
  fetchReport()
}

function toggleOverdueOnly() {
  showOverdueOnly.value = !showOverdueOnly.value
  fetchReport()
}

const filteredRows = computed(() => {
  let rows = allRows.value || []

  if (sortKey.value) {
    rows = [...rows].sort((a, b) => {
      const av = a[sortKey.value] ?? ''
      const bv = b[sortKey.value] ?? ''

      const aNum = Number(av)
      const bNum = Number(bv)

      if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
        return sortDir.value === 'asc' ? aNum - bNum : bNum - aNum
      }

      return sortDir.value === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
  }

  return rows
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / Number(pageSize.value))))

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * Number(pageSize.value)
  return filteredRows.value.slice(start, start + Number(pageSize.value))
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(filteredRows, () => {
  currentPage.value = 1
})

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function roomStatusClass(status) {
  return {
    Occupied: 'bg-green-50 text-green-700',
    'Vacant Clean': 'bg-blue-50 text-blue-600',
    'Vacant Dirty': 'bg-gray-100 text-gray-500',
    'Overdue Check-Out': 'bg-red-50 text-red-600',
    Maintenance: 'bg-orange-50 text-orange-600',
  }[status] || 'bg-gray-100 text-gray-500'
}

function paymentClass(status) {
  return {
    Paid: 'bg-green-100 text-green-700',
    'Part Payment': 'bg-yellow-100 text-yellow-700',
    Unpaid: 'bg-red-100 text-red-600',
  }[status] || 'bg-gray-100 text-gray-500'
}

function formatNumber(n) {
  if (n === null || n === undefined || n === '') return '0'
  return Number(n || 0).toLocaleString('en-NG')
}

function exportReport() {
  const headers = [
    'Check In ID',
    'Room',
    'Type',
    'Status',
    'Guest',
    'Check-In',
    'Check-Out',
    'Nights',
    'Rate',
    'Discount',
    'Amount',
    'Paid',
    'Outstanding',
    'Payment',
    'Created By',
  ]

  const csvRows = [
    headers.join(','),
    ...filteredRows.value.map(row => [
      row.checkin_id || '',
      row.room_number || '',
      row.room_type || '',
      row.status || '',
      row.guest || '',
      row.checkin || '',
      row.checkout || '',
      row.nights || '',
      row.rate || 0,
      row.discount || 0,
      row.amount || 0,
      row.paid_amount || 0,
      row.outstanding || 0,
      row.payment_status || '',
      row.created_by || '',
    ].map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')),
  ]

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `daily-occupancy-report-${filters.value.dateFrom}-to-${filters.value.dateTo}.csv`
  link.click()

  URL.revokeObjectURL(url)
}

function printReport() {
  window.print()
}
</script>