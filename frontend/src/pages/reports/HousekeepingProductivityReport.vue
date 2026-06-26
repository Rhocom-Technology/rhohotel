<template>
  <div class="space-y-5">
    <!-- Page Header -->
    <div>
      <!-- <h1 class="text-2xl font-bold text-gray-900">Housekeeping Productivity Report</h1> -->

      <div class="flex justify-between items-center gap-3 flex-wrap">
          
        <h1 class="text-2xl font-bold text-gray-900">Housekeeping Productivity Report</h1>
       <button
          @click="downloadReport"
          class="bg-green-600 text-white px-4 py-2 rounded-lg">
          Download
        </button>
  
    </div>
      <p class="text-xs text-gray-400 mt-1">
        Comprehensive room cleaning, inspection, attendant productivity, floor performance and maintenance overview.
      </p>
    </div>

    

    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <p class="text-xs font-bold text-red-700">Unable to load report</p>
      <p class="text-xs text-red-600 mt-1">{{ errorMessage }}</p>
    </div>

    <!-- Filters Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input v-model="filters.date_from" type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>

        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input v-model="filters.date_to" type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Housekeeper</p>
          <select v-model="filters.housekeeper"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Housekeepers</option>
            <option v-for="person in housekeepers" :key="person" :value="person">{{ person }}</option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Floor</p>
          <select v-model="filters.floor"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Floors</option>
            <option v-for="floor in floors" :key="floor" :value="floor">{{ floor }}</option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
          <select v-model="filters.status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option>Cleaned</option>
            <option>Inspected</option>
            <option>Released</option>
            <option>Pending</option>
            <option>Maintenance</option>
          </select>
        </div>

        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400"
              fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input v-model="searchQuery" type="text" placeholder="Search room, attendant, inspector, issue..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Reset
        </button>

        <button @click="fetchReport" :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
          {{ loading ? 'Loading...' : 'Apply' }}
        </button>
      </div>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Rooms Assigned</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.rooms_assigned) }}</p>
        <p class="text-[10px] text-blue-600 mt-1">total workload</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Rooms Cleaned</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.rooms_cleaned) }}</p>
        <p class="text-[10px] text-green-600 mt-1">completed cleaning</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Rooms Inspected</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.rooms_inspected) }}</p>
        <p class="text-[10px] text-purple-600 mt-1">quality checked</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Avg Cleaning Time</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.avg_cleaning_time }}m</p>
        <p class="text-[10px] text-indigo-600 mt-1">per room</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Guest Requests</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.guest_requests) }}</p>
        <p class="text-[10px] text-amber-600 mt-1">handled requests</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Maintenance Issues</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.maintenance_issues) }}</p>
        <p class="text-[10px] text-red-600 mt-1">reported issues</p>
      </div>
    </div>

    <!-- Status + Productivity -->
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Room Status Distribution</h3>

        <div class="space-y-4">
          <div v-for="row in statusBreakdown" :key="row.status">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-medium text-gray-700">{{ row.status }}</span>
              <span class="text-xs font-bold text-gray-900">{{ row.count }}</span>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all"
                :class="statusBarColor(row.status)"
                :style="{ width: getPercent(row.count, maxStatusCount) + '%' }">
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Housekeeper Productivity</h3>
          <p class="text-xs text-gray-400">Cleaning speed, inspection pass rate and workload output</p>
        </div>

        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Housekeeper</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Assigned</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Cleaned</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Avg Time</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Requests</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Score</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="person in housekeeperPerformance" :key="person.housekeeper"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
              <td class="px-5 py-3.5 text-xs font-bold text-gray-900">{{ person.housekeeper }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ person.assigned }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ person.cleaned }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ person.avg_time }}m</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ person.requests }}</td>
              <td class="px-5 py-3.5 text-xs text-right font-bold" :class="scoreTextColor(person.score)">
                {{ person.score }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Floor Performance + Inspection -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Floor Performance</h3>

        <div class="space-y-4">
          <div v-for="floor in floorPerformance" :key="floor.floor">
            <div class="flex items-center justify-between mb-1.5">
              <div>
                <p class="text-xs font-bold text-gray-900">{{ floor.floor }}</p>
                <p class="text-[10px] text-gray-400 mt-0.5">
                  {{ floor.cleaned }} cleaned out of {{ floor.assigned }} assigned
                </p>
              </div>
              <p class="text-xs font-bold text-gray-900">{{ floor.completion }}%</p>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all"
                :class="floorBarColor(floor.completion)"
                :style="{ width: floor.completion + '%' }">
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Inspection Summary</h3>
          <p class="text-xs text-gray-400 mt-0.5">Inspector approval, rejection and release status</p>
        </div>

        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Inspector</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Inspected</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Released</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Rejected</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="inspector in inspectorSummary" :key="inspector.inspector"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
              <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ inspector.inspector }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ inspector.inspected }}</td>
              <td class="px-4 py-3.5 text-xs text-right font-bold text-green-600">{{ inspector.released }}</td>
              <td class="px-5 py-3.5 text-xs text-right font-bold text-red-600">{{ inspector.rejected }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detailed Housekeeping Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Detailed Room Cleaning Log</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Room-level assignment, cleaning time, inspection, guest request and maintenance details.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedRooms.length }} of {{ filteredRooms.length }} records
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1300px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10 min-w-[160px]">Id</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700" @click="sortBy('room')">
                Room<span v-if="sortKey === 'room'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[120px]">Floor</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Housekeeper</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Start</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">End</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Duration</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Inspector</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Requests</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issue</th>
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-28">Status</th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="paginatedRooms.length === 0">
              <td colspan="11" class="text-center py-12 text-xs text-gray-400">
                No housekeeping records found.
              </td>
            </tr>

            <tr v-for="(room, index) in paginatedRooms" :key="room.id"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * pageSize + index + 1 }}
              </td>

              <td class="px-4 py-3.5  ">
                <span class="min-w-[160px] px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                  {{ room.id }}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                  {{ room.room }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-600">{{ room.floor || '—' }}</td>
              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ room.housekeeper }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ room.start_time || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ room.end_time || '—' }}</td>

              <td class="px-4 py-3.5 text-xs text-right font-bold text-gray-900">
                {{ room.duration ? room.duration + 'm' : '—' }}
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-700">{{ room.inspector || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ room.guest_requests }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ room.issue || 'None' }}</td>

              <!-- <td class="px-5 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="roomStatusClass(room.status)">
                  {{ room.status }}
                </span>
              </td> -->
              <td class="px-5 py-3.5">
                <div class="flex flex-col">
                  <span class="text-xs text-gray-400">
                    {{ (currentPage - 1) * pageSize + index + 1 }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="6" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">
                {{ formatNumber(totals.duration) }}m
              </td>
              <td></td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">
                {{ formatNumber(totals.guest_requests) }}
              </td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">
          Page {{ currentPage }} of {{ totalPages }}
        </p>

        <div class="flex items-center gap-1">
          <button @click="currentPage = 1" :disabled="currentPage === 1"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">
            «
          </button>

          <button @click="currentPage--" :disabled="currentPage === 1"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">
            ‹
          </button>

          <button v-for="page in visiblePages" :key="page" @click="page !== '...' && (currentPage = page)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="page === currentPage ? 'bg-blue-600 text-white font-semibold' : page === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-gray-50 border border-gray-200'">
            {{ page }}
          </button>

          <button @click="currentPage++" :disabled="currentPage === totalPages"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">
            ›
          </button>

          <button @click="currentPage = totalPages" :disabled="currentPage === totalPages"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors">
            »
          </button>

          <select v-model="pageSize" @change="currentPage = 1"
            class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        Housekeeping note: Monitor room turnaround time, inspection failures, pending rooms, guest requests and maintenance reports.
      </p>
      <p class="text-xs text-gray-400">Execution Time: {{ executionTime }} sec</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')
const executionTime = ref('0.0')

const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)

const todayDate = new Date()
const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 7)

const today = todayDate.toISOString().slice(0, 10)
const weekAgo = fromDate.toISOString().slice(0, 10)

const filters = ref({
  date_from: weekAgo,
  date_to: today,
  housekeeper: '',
  floor: '',
  status: '',
})

const rooms = ref([])
const housekeepers = ref([])
const floors = ref([])

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''
  const start = performance.now()

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.housekeeping_productivity_report.get_housekeeping_productivity_report',
      {
        date_from: filters.value.date_from,
        date_to: filters.value.date_to,
        housekeeper: filters.value.housekeeper,
        floor: filters.value.floor,
        status: filters.value.status,
        search: searchQuery.value,
      }
    )

    rooms.value = result?.rows || []
    housekeepers.value = result?.housekeepers || []
    floors.value = result?.floors || []
    executionTime.value = ((performance.now() - start) / 1000).toFixed(1)
    currentPage.value = 1
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading housekeeping productivity report.'
    rooms.value = []
  } finally {
    loading.value = false
  }
}

const filteredRooms = computed(() => {
  let rows = rooms.value || []

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

const summary = computed(() => {
  const assigned = filteredRooms.value.length

  const cleaned = filteredRooms.value.filter(row =>
    ['Cleaned', 'Inspected', 'Released', 'Completed'].includes(row.status)
  ).length

  const inspected = filteredRooms.value.filter(row =>
    ['Inspected', 'Released'].includes(row.status)
  ).length

  const completedRows = filteredRooms.value.filter(row => Number(row.duration || 0) > 0)
  const totalDuration = completedRows.reduce((sum, row) => sum + Number(row.duration || 0), 0)

  return {
    rooms_assigned: assigned,
    rooms_cleaned: cleaned,
    rooms_inspected: inspected,
    avg_cleaning_time: completedRows.length ? Math.round(totalDuration / completedRows.length) : 0,
    guest_requests: filteredRooms.value.reduce((sum, row) => sum + Number(row.guest_requests || 0), 0),
    maintenance_issues: filteredRooms.value.filter(row => row.status === 'Maintenance' || row.issue).length,
  }
})

const totals = computed(() => ({
  duration: filteredRooms.value.reduce((sum, row) => sum + Number(row.duration || 0), 0),
  guest_requests: filteredRooms.value.reduce((sum, row) => sum + Number(row.guest_requests || 0), 0),
}))

const statusBreakdown = computed(() => {
  const map = {}

  filteredRooms.value.forEach(row => {
    const status = row.status || 'Unknown'
    map[status] = (map[status] || 0) + 1
  })

  return Object.entries(map)
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => b.count - a.count)
})

const maxStatusCount = computed(() => {
  return Math.max(...statusBreakdown.value.map(row => row.count), 1)
})

const housekeeperPerformance = computed(() => {
  const map = {}

  filteredRooms.value.forEach(row => {
    const name = row.housekeeper || 'Unknown'

    if (!map[name]) {
      map[name] = {
        housekeeper: name,
        assigned: 0,
        cleaned: 0,
        duration: 0,
        duration_count: 0,
        requests: 0,
      }
    }

    map[name].assigned += 1

    if (['Cleaned', 'Inspected', 'Released', 'Completed'].includes(row.status)) {
      map[name].cleaned += 1
    }

    if (Number(row.duration || 0) > 0) {
      map[name].duration += Number(row.duration || 0)
      map[name].duration_count += 1
    }

    map[name].requests += Number(row.guest_requests || 0)
  })

  return Object.values(map)
    .map(row => {
      const completionRate = row.assigned ? (row.cleaned / row.assigned) * 100 : 0
      const avgTime = row.duration_count ? Math.round(row.duration / row.duration_count) : 0
      const speedScore = avgTime ? Math.max(0, 100 - Math.max(0, avgTime - 25) * 2) : 0
      const score = Math.round((completionRate * 0.7) + (speedScore * 0.3))

      return {
        ...row,
        avg_time: avgTime,
        score,
      }
    })
    .sort((a, b) => b.score - a.score)
})

const floorPerformance = computed(() => {
  const map = {}

  filteredRooms.value.forEach(row => {
    const floor = row.floor || 'Unknown'

    if (!map[floor]) {
      map[floor] = {
        floor,
        assigned: 0,
        cleaned: 0,
      }
    }

    map[floor].assigned += 1

    if (['Cleaned', 'Inspected', 'Released', 'Completed'].includes(row.status)) {
      map[floor].cleaned += 1
    }
  })

  return Object.values(map)
    .map(row => ({
      ...row,
      completion: row.assigned ? Math.round((row.cleaned / row.assigned) * 100) : 0,
    }))
    .sort((a, b) => String(a.floor).localeCompare(String(b.floor)))
})

const inspectorSummary = computed(() => {
  const map = {}

  filteredRooms.value
    .filter(row => row.inspector)
    .forEach(row => {
      const inspector = row.inspector

      if (!map[inspector]) {
        map[inspector] = {
          inspector,
          inspected: 0,
          released: 0,
          rejected: 0,
        }
      }

      if (['Inspected', 'Released', 'Maintenance'].includes(row.status)) {
        map[inspector].inspected += 1
      }

      if (row.status === 'Released') {
        map[inspector].released += 1
      }

      if (row.status === 'Maintenance') {
        map[inspector].rejected += 1
      }
    })

  return Object.values(map).sort((a, b) => b.inspected - a.inspected)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRooms.value.length / Number(pageSize.value)))
})

const paginatedRooms = computed(() => {
  const start = (currentPage.value - 1) * Number(pageSize.value)
  return filteredRooms.value.slice(start, start + Number(pageSize.value))
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(filteredRooms, () => {
  currentPage.value = 1
})

watch(
  () => [filters.value.housekeeper, filters.value.floor, filters.value.status],
  () => fetchReport()
)

let searchTimer = null
watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchReport()
  }, 450)
})

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function resetFilters() {
  filters.value = {
    date_from: weekAgo,
    date_to: today,
    housekeeper: '',
    floor: '',
    status: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
  fetchReport()
}

function getPercent(value, max) {
  if (!max) return 0
  return Math.min(100, Math.round((Number(value || 0) / Number(max)) * 100))
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-NG', {
    maximumFractionDigits: 0,
  })
}

function roomStatusClass(status) {
  return {
    Released: 'bg-green-100 text-green-700',
    Inspected: 'bg-blue-100 text-blue-700',
    Cleaned: 'bg-purple-100 text-purple-700',
    Pending: 'bg-yellow-100 text-yellow-700',
    Maintenance: 'bg-red-100 text-red-600',
    Completed: 'bg-green-100 text-green-700',
    Open: 'bg-yellow-100 text-yellow-700',
    Working: 'bg-blue-100 text-blue-700',
    Cancelled: 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

function statusBarColor(status) {
  return {
    Released: 'bg-green-500',
    Inspected: 'bg-blue-500',
    Cleaned: 'bg-purple-500',
    Pending: 'bg-yellow-500',
    Maintenance: 'bg-red-500',
    Completed: 'bg-green-500',
    Open: 'bg-yellow-500',
    Working: 'bg-blue-500',
    Cancelled: 'bg-gray-500',
  }[status] || 'bg-gray-500'
}

function floorBarColor(completion) {
  if (completion >= 90) return 'bg-green-500'
  if (completion >= 70) return 'bg-blue-500'
  if (completion >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

function scoreTextColor(score) {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-blue-600'
  if (score >= 50) return 'text-yellow-600'
  return 'text-red-600'
}

onMounted(() => {
  fetchReport()
})

async function downloadReport() {
  const params = new URLSearchParams({
    date_from: filters.value.date_from || '',
    date_to: filters.value.date_to || '',
    housekeeper: filters.value.housekeeper || '',
    floor: filters.value.floor || '',
    status: filters.value.status || '',
    search: searchQuery.value || '',
  })

  await printPdf(`/api/method/rhohotel.rhocom_hotel.api.reports.download_housekeeping_productivity_report?${params.toString()}`)
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