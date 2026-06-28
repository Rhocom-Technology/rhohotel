<template>
  <div class="space-y-5">
    <div>

      <div class="flex justify-between items-center gap-3 flex-wrap">

        <h1 class="text-2xl font-bold text-gray-900">Guest Stay History</h1>
       <button
          @click="downloadReport"
          class="bg-green-600 text-white px-4 py-2 rounded-lg">
          Download
        </button>
  
    </div>
      <p class="text-xs text-gray-400 mt-1">
        Track guest stay records, repeat visits, revenue, balances, source channels, and guest preferences.
      </p>
    </div>

    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <p class="text-xs font-bold text-red-700">Unable to load report</p>
      <p class="text-xs text-red-600 mt-1">{{ errorMessage }}</p>
    </div>

    <!-- Filters Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input
            v-model="filters.dateFrom"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input
            v-model="filters.dateTo"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
          <select
            v-model="filters.guestType"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Guests</option>
            <option>New</option>
            <option>Repeat</option>
            <option>VIP</option>
            <option>Corporate</option>
            <option>Long Stay</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select
            v-model="filters.roomType"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Rooms</option>
            <option v-for="roomType in roomTypes" :key="roomType" :value="roomType">{{ roomType }}</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment</p>
          <select
            v-model="filters.payment"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Status</option>
            <option>Settled</option>
            <option>Part Paid</option>
            <option>Outstanding</option>
            <option>Corporate Credit</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Source</p>
          <select
            v-model="filters.source"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Channels</option>
            <option v-for="src in sources" :key="src" :value="src">{{ src }}</option>
          </select>
        </div>

        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search Guest</p>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Name, phone, guest ID..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          @click="fetchReport"
          :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Loading...' : 'Apply Filter' }}
        </button>

        <button
          @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Stays</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.totalStays }}</p>
        <p class="text-[10px] text-gray-400 mt-1">Within selected date range</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Unique Guests</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.uniqueGuests }}</p>
        <p class="text-[10px] text-gray-400 mt-1">Guests captured in history</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Repeat Guests</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.repeatGuests }}</p>
        <p class="text-[10px] text-gray-400 mt-1">{{ stats.repeatRatio }} Repeat ratio</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Room Nights</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.roomNights }}</p>
        <p class="text-[10px] text-gray-400 mt-1">Occupied guest nights</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Revenue</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatCompact(stats.totalRevenue) }}</p>
        <p class="text-[10px] text-gray-400 mt-1">Room + stay charges</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Avg Stay</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.avgStay }} Nights</p>
        <p class="text-[10px] text-gray-400 mt-1">Average length of stay</p>
      </div>
    </div>

    <!-- Data Table Card -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Guest Stay Records</h3>

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
        <p class="text-xs text-gray-400">Loading guest stay history...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full" style="min-width:1200px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-8">No</th>

              <th class="min-w-[120px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('guestId')">
                Guest ID<span v-if="sortKey === 'guestId'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>

              <th class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('guestName')">
                Guest Name<span v-if="sortKey === 'guestName'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>

              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Phone / Class</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>

              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('checkin')">
                Check-In<span v-if="sortKey === 'checkin'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>

              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Check-Out</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Nights</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Total Spend</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Balance</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Source</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Last Visit</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Preference / Notes</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
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
              :key="row.id"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>

              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 text-[10px] font-medium bg-blue-50 text-blue-700 rounded">
                  {{ row.guestId || '—' }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ row.guestName }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600 whitespace-nowrap">{{ row.phone }}</td>
              <td class="px-4 py-3.5 text-xs font-bold text-gray-900">{{ row.room }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.checkin }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.checkout }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.nights }}</td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="typeClass(row.type)">
                  {{ row.type }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs font-bold text-gray-900 whitespace-nowrap">
                ₦{{ formatNumber(row.totalSpend) }}
              </td>

              <td class="px-4 py-3.5 text-xs font-semibold whitespace-nowrap" :class="row.balance > 0 ? 'text-red-600' : 'text-gray-400'">
                ₦{{ formatNumber(row.balance) }}
              </td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="statusClass(row.status)">
                  {{ row.status }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.source }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.lastVisit }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 max-w-[220px] truncate">{{ row.notes }}</td>

              <td class="px-4 py-3.5">
                <button
                  @click="openCheckIn(row)"
                  class="px-3 py-1.5 text-[10px] font-semibold text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100"
                >
                  View
                </button>
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="9" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ formatNumber(totals.spend) }}</td>
              <td class="px-4 py-4 text-xs font-bold text-red-600">₦{{ formatNumber(totals.balance) }}</td>
              <td colspan="5" class="px-4 py-4 text-xs font-bold text-amber-600">
                {{ totals.needFollowup }} items need follow-up
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">
          Showing {{ filteredRows.length ? (currentPage - 1) * pageSize + 1 : 0 }}–{{ Math.min(currentPage * pageSize, filteredRows.length) }} of {{ filteredRows.length }} records
        </p>

        <div class="flex items-center gap-1">
          <button @click="currentPage = 1" :disabled="currentPage === 1" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">«</button>
          <button @click="currentPage--" :disabled="currentPage === 1" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">‹</button>

          <button
            v-for="p in visiblePages"
            :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="p === currentPage ? 'bg-blue-600 text-white font-semibold' : p === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-gray-50 border border-gray-200'"
          >
            {{ p }}
          </button>

          <button @click="currentPage++" :disabled="currentPage === totalPages" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">›</button>
          <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">»</button>

          <select v-model="pageSize" @change="currentPage = 1" class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Insights Bar -->
    <div class="flex items-center gap-3">
      <div class="flex-1 bg-blue-50 border border-blue-200 rounded-xl px-5 py-3">
        <p class="text-xs text-blue-700 font-medium">
          <span class="font-bold">Insight:</span> Repeat guests represent {{ stats.repeatRatio }} of the selected stay records.
        </p>
      </div>

      <div class="flex-1 bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-3">
        <p class="text-xs text-yellow-700 font-medium">
          <span class="font-bold">Follow-up:</span> {{ totals.needFollowup }} stays have unpaid or credit balances.
        </p>
      </div>
    </div>

    <div class="text-right">
      <p class="text-xs text-gray-400">Generated: {{ generatedAt || '—' }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { callMethodForm } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)
const generatedAt = ref('')

const todayDate = new Date()
const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 7)

const today = todayDate.toISOString().slice(0, 10)
const weekAgo = fromDate.toISOString().slice(0, 10)

const filters = ref({
  dateFrom: weekAgo,
  dateTo: today,
  guestType: '',
  roomType: '',
  payment: '',
  source: '',
})

const allRows = ref([])
const roomTypes = ref([])
const sources = ref([])

const stats = ref({
  totalStays: 0,
  uniqueGuests: 0,
  repeatGuests: 0,
  repeatRatio: '0%',
  roomNights: 0,
  totalRevenue: 0,
  avgStay: 0,
})

const totals = ref({
  spend: 0,
  balance: 0,
  needFollowup: 0,
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
  () => [
    filters.value.guestType,
    filters.value.roomType,
    filters.value.payment,
    filters.value.source,
  ],
  () => fetchReport()
)

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  try {
    const result = await callMethodForm('rhohotel.rhocom_hotel.api.guest_stay_history_report.get_guest_stay_history', {
      date_from: filters.value.dateFrom,
      date_to: filters.value.dateTo,
      guest_type: filters.value.guestType,
      room_type: filters.value.roomType,
      payment: filters.value.payment,
      source: filters.value.source,
      search: searchQuery.value,
    })

    allRows.value = result?.rows || []
    stats.value = result?.stats || stats.value
    totals.value = result?.totals || totals.value
    roomTypes.value = result?.room_types || []
    sources.value = result?.sources || []
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
    dateFrom: weekAgo,
    dateTo: today,
    guestType: '',
    roomType: '',
    payment: '',
    source: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
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

function typeClass(type) {
  return {
    Repeat: 'bg-blue-50 text-blue-600',
    New: 'bg-gray-100 text-gray-500',
    VIP: 'bg-yellow-50 text-yellow-600',
    Corporate: 'bg-purple-50 text-purple-600',
    'Long Stay': 'bg-green-50 text-green-600',
  }[type] || 'bg-gray-100 text-gray-500'
}

function statusClass(status) {
  return {
    Settled: 'bg-green-50 text-green-600',
    'Part Paid': 'bg-yellow-50 text-yellow-600',
    Outstanding: 'bg-red-50 text-red-500',
    'Corporate Credit': 'bg-blue-50 text-blue-600',
  }[status] || 'bg-gray-100 text-gray-500'
}

function formatNumber(n) {
  if (n === null || n === undefined || n === '') return '0'
  return Number(n || 0).toLocaleString('en-NG')
}

function formatCompact(n) {
  const value = Number(n || 0)

  if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
  if (value >= 1000) return (value / 1000).toFixed(0) + 'K'

  return String(value)
}

function openCheckIn(row) {
  if (!row?.id) return
  // Navigate within the Vue SPA – avoids being redirected to raw Frappe desk
  router.push({ name: 'CheckInDetail', params: { id: row.id } })
}

function exportReport() {
  const headers = [
    'Guest ID',
    'Guest Name',
    'Phone',
    'Room',
    'Room Type',
    'Check-In',
    'Check-Out',
    'Nights',
    'Type',
    'Total Spend',
    'Balance',
    'Status',
    'Source',
    'Last Visit',
    'Notes',
  ]

  const csvRows = [
    headers.join(','),
    ...filteredRows.value.map(row => [
      row.guestId || '',
      row.guestName || '',
      row.phone || '',
      row.room || '',
      row.roomType || '',
      row.checkin || '',
      row.checkout || '',
      row.nights || '',
      row.type || '',
      row.totalSpend || 0,
      row.balance || 0,
      row.status || '',
      row.source || '',
      row.lastVisit || '',
      row.notes || '',
    ].map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')),
  ]

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `guest-stay-history-${filters.value.dateFrom}-to-${filters.value.dateTo}.csv`
  link.click()

  URL.revokeObjectURL(url)
}

function printReport() {
  window.print()
}


async function downloadReport() {
  const params = new URLSearchParams({
    date_from: filters.value.dateFrom || '',
    date_to: filters.value.dateTo || '',
    guest_type: filters.value.guestType || '',
    room_type: filters.value.roomType || '',
    payment: filters.value.payment || '',
    source: filters.value.source || '',
    search: searchQuery.value || '',
  })

  await printPdf(`/api/method/rhohotel.rhocom_hotel.api.reports.download_guest_stay_history_report?${params.toString()}`)
}

async function printPdf(url) {
  try {
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error('Failed to fetch PDF')
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;top:0;left:0;width:0;height:0;border:0;visibility:hidden;'
    iframe.src = objectUrl
    document.body.appendChild(iframe)
    iframe.onload = () => {
      setTimeout(() => {
        iframe.contentWindow.focus()
        iframe.contentWindow.print()
        setTimeout(() => {
          document.body.removeChild(iframe)
          URL.revokeObjectURL(objectUrl)
        }, 1000)
      }, 300)
    }
  } catch (err) {
    console.error('Print error:', err)
  }
}
</script>