<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-gray-900">Machine Access Log Dashboard</h2>
          <p class="text-xs text-gray-400 mt-0.5">
            Monitor machine access activities, technician workload, and access trends across the property.
          </p>
        </div>
        <button @click="loadDashboard"
          class="px-3 py-1.5 text-xs font-medium text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1.5">
          <svg :class="loading ? 'animate-spin' : ''" class="w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          Refresh
        </button>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <router-link to="/machine-access-log/new">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors">
            New Access Log
          </button>
        </router-link>
        <router-link to="/work-order/list">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Work Orders
          </button>
        </router-link>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div v-for="n in 8" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
        <div class="h-2 bg-gray-100 rounded w-2/3"></div>
      </div>
    </div>

    <template v-else-if="dashboard">
      <!-- Top Stats Row -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Total Logs</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ dashboard.total }}</p>
          <p class="text-xs text-gray-400 mt-1">All-time access records</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Draft</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Pending</span>
          </div>
          <p class="text-3xl font-bold text-yellow-600">{{ dashboard.draft }}</p>
          <p class="text-xs text-gray-400 mt-1">Not yet submitted</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Submitted</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
          </div>
          <p class="text-3xl font-bold text-green-600">{{ dashboard.submitted }}</p>
          <p class="text-xs text-gray-400 mt-1">Confirmed records</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Cancelled</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-red-50 text-red-400 rounded-full">Void</span>
          </div>
          <p class="text-3xl font-bold text-red-500">{{ dashboard.cancelled }}</p>
          <p class="text-xs text-gray-400 mt-1">All-time cancelled</p>
        </div>
      </div>

      <!-- Secondary Stats Row -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">This Week</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-600 rounded-full">Recent</span>
          </div>
          <p class="text-3xl font-bold text-indigo-600">{{ dashboard.this_week }}</p>
          <p class="text-xs text-gray-400 mt-1">Created this week</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Today</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">New</span>
          </div>
          <p class="text-3xl font-bold text-blue-600">{{ dashboard.today }}</p>
          <p class="text-xs text-gray-400 mt-1">Logged today</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 col-span-2">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Quick Filters</p>
          </div>
          <div class="flex items-center gap-2 flex-wrap mt-1">
            <button @click="filterStatus = '0'; fetchLogs(1)"
              class="px-3 py-1.5 text-xs font-medium text-yellow-700 border border-yellow-200 rounded-lg hover:bg-yellow-50">
              Drafts
            </button>
            <button @click="filterStatus = '1'; fetchLogs(1)"
              class="px-3 py-1.5 text-xs font-medium text-green-700 border border-green-200 rounded-lg hover:bg-green-50">
              Submitted
            </button>
            <router-link to="/machine-access-log/new">
              <button class="px-3 py-1.5 text-xs font-semibold text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
                + New Log
              </button>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <!-- Location Breakdown -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">By Location Type</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Distribution of access by location.</p>
          <div class="flex items-end justify-around gap-2 min-h-[150px]">
            <div v-for="item in dashboard.location_breakdown" :key="item.location_type" class="flex flex-col items-center gap-1.5">
              <span class="text-xs font-semibold text-gray-600">{{ item.count }}</span>
              <div class="w-9 rounded-t-md transition-all duration-500 bg-blue-500"
                :style="{ height: barHeight(item.count) + 'px' }"></div>
              <span class="text-[10px] text-gray-400 text-center max-w-[70px] leading-tight">{{ item.location_type }}</span>
            </div>
          </div>
        </div>

        <!-- Top Machines -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Top Machines</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Most frequently accessed machines.</p>
          <div class="space-y-3">
            <div v-for="(item, idx) in dashboard.top_machines.slice(0, 6)" :key="item.machine_name"
              class="flex items-center gap-3">
              <span class="text-[10px] font-bold text-gray-400 w-4">{{ idx + 1 }}</span>
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-700 truncate max-w-[130px]">{{ item.machine_name }}</span>
                  <span class="text-xs font-semibold text-gray-900">{{ item.count }}</span>
                </div>
                <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-blue-500 rounded-full" :style="{ width: barPercent(item.count, maxMachine) + '%' }"></div>
                </div>
              </div>
            </div>
            <p v-if="!dashboard.top_machines.length" class="text-xs text-gray-400">No data</p>
          </div>
        </div>

        <!-- Top Technicians -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Top Technicians</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Most active technicians by access count.</p>
          <div class="space-y-3">
            <div v-for="(item, idx) in dashboard.top_technicians.slice(0, 6)" :key="item.technician"
              class="flex items-center gap-3">
              <span class="text-[10px] font-bold text-gray-400 w-4">{{ idx + 1 }}</span>
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-700 truncate max-w-[130px]">{{ item.technician }}</span>
                  <span class="text-xs font-semibold text-gray-900">{{ item.count }}</span>
                </div>
                <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-green-500 rounded-full" :style="{ width: barPercent(item.count, maxTechnician) + '%' }"></div>
                </div>
              </div>
            </div>
            <p v-if="!dashboard.top_technicians.length" class="text-xs text-gray-400">No data</p>
          </div>
        </div>
      </div>

      <!-- Monthly Trend -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5" v-if="dashboard.monthly_trend.length">
        <h3 class="text-sm font-bold text-gray-900">Monthly Trend</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Access logs created per month (last 6 months).</p>
        <div class="flex items-end justify-around gap-3 min-h-[150px]">
          <div v-for="m in dashboard.monthly_trend" :key="m.month" class="flex flex-col items-center gap-1.5 flex-1">
            <span class="text-xs font-semibold text-gray-600">{{ m.count }}</span>
            <div class="w-full max-w-[48px] bg-blue-500 rounded-t-md transition-all duration-500"
              :style="{ height: barHeight(m.count) + 'px' }"></div>
            <span class="text-[10px] text-gray-400">{{ formatMonth(m.month) }}</span>
          </div>
        </div>
      </div>

      <!-- Filters & Search -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-3">Filters &amp; Search</h3>
        <div class="flex items-center gap-3 flex-wrap">
          <div class="relative" style="flex:1;min-width:180px;">
            <input v-model="search" @input="debouncedFetch" type="text"
              placeholder="Search log ID, machine name, reason..."
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <select v-model="filterStatus" @change="fetchLogs(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
            <option value="">All Status</option>
            <option value="0">Draft</option>
            <option value="1">Submitted</option>
            <option value="2">Cancelled</option>
          </select>
          <select v-model="filterLocationType" @change="fetchLogs(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
            <option value="">All Location Types</option>
            <option value="Room">Room</option>
            <option value="Asset Location">Asset Location</option>
            <option value="Other Location">Other Location</option>
          </select>
          <input v-model="filterWorkOrder" @keyup.enter="fetchLogs(1)" type="text" placeholder="Work Order ID..."
            class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none" style="width:140px;" />
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
        </div>
      </div>

      <!-- Access Log Records Table -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Access Log Records</h3>
          <p class="text-xs text-gray-400" v-if="!listLoading">
            Showing {{ listTotal === 0 ? 0 : ((listPage - 1) * listPageSize) + 1 }}–{{ Math.min(listPage * listPageSize, listTotal) }} of {{ listTotal }} logs
          </p>
        </div>

        <!-- Loading -->
        <div v-if="listLoading" class="flex items-center justify-center py-16 gap-3">
          <svg class="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <p class="text-sm text-gray-400">Loading access logs...</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Log ID</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Machine</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Date</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Time</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Location</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Technician</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Work Order</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="log in records" :key="log.name"
                class="hover:bg-gray-50 transition-colors cursor-pointer"
                @click="router.push({ name: 'MachineAccessLogDetail', params: { id: log.name } })">
                <td class="px-6 py-4 text-xs font-bold text-gray-900 font-mono">{{ log.name }}</td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ log.machine_name || '—' }}</td>
                <td class="px-4 py-4 text-xs text-gray-500">{{ formatDate(log.date_opened) }}</td>
                <td class="px-4 py-4 text-xs text-gray-500">{{ log.time_opened || '—' }}{{ log.time_closed ? ` → ${log.time_closed}` : '' }}</td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ log.room || log.asset_location || log.location_description || '—' }}</td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ log.technician || '—' }}</td>
                <td class="px-4 py-4 text-xs">
                  <span v-if="log.facility_work_order"
                    @click.stop="router.push({ name: 'FacilityWorkOrderDetail', params: { id: log.facility_work_order } })"
                    class="text-blue-600 hover:underline cursor-pointer">
                    {{ log.facility_work_order }}
                  </span>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-4 py-4">
                  <span class="px-2 py-1 text-[10px] font-medium rounded-full"
                    :class="statusClass(log.docstatus)">
                    {{ statusLabel(log.docstatus) }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <button
                    @click.stop="router.push({ name: 'MachineAccessLogDetail', params: { id: log.name } })"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                    View
                  </button>
                </td>
              </tr>
              <tr v-if="records.length === 0 && !listLoading">
                <td colspan="9" class="text-center py-12 text-xs text-gray-400">No machine access logs found</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <p class="text-xs text-gray-400">Rows per page:</p>
            <select v-model="listPageSize" @change="fetchLogs(1)"
              class="text-xs border border-gray-200 rounded-lg px-2 py-1">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <button @click="fetchLogs(listPage - 1)" :disabled="listPage === 1"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
              Previous
            </button>
            <span class="text-xs text-gray-600">Page {{ listPage }} of {{ listTotalPages }}</span>
            <button @click="fetchLogs(listPage + 1)" :disabled="listPage >= listTotalPages"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
              Next
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const dashboard = ref(null)

// ─── List state ───────────────────────────────────────────────────────────────
const search = ref('')
const filterStatus = ref('')
const filterLocationType = ref('')
const filterWorkOrder = ref('')
const listPage = ref(1)
const listPageSize = ref(25)
const listTotalPages = ref(1)
const listTotal = ref(0)
const listLoading = ref(true)
const records = ref([])

const dashboardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.machine_access_log.get_machine_access_log_dashboard',
  auto: false
})

const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.machine_access_log.get_machine_access_log_list',
  auto: false
})

async function loadDashboard() {
  loading.value = true
  try {
    const res = await dashboardResource.fetch()
    dashboard.value = res
  } finally {
    loading.value = false
  }
}

async function fetchLogs(newPage = 1) {
  listPage.value = newPage
  listLoading.value = true
  try {
    const filters = {}
    if (search.value) filters.search = search.value
    if (filterStatus.value !== '') filters.docstatus = filterStatus.value
    if (filterLocationType.value) filters.location_type = filterLocationType.value
    if (filterWorkOrder.value) filters.facility_work_order = filterWorkOrder.value

    const res = await listResource.fetch({
      page: listPage.value,
      page_size: listPageSize.value,
      filters: JSON.stringify(filters)
    })
    records.value = res?.records || []
    listTotal.value = res?.total || 0
    listTotalPages.value = res?.total_pages || 1
  } catch (e) {
    console.error('[MachineAccessLog] list error:', e)
    records.value = []
  } finally {
    listLoading.value = false
  }
}

let searchTimer = null
function debouncedFetch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchLogs(1), 350)
}

function clearFilters() {
  search.value = ''
  filterStatus.value = ''
  filterLocationType.value = ''
  filterWorkOrder.value = ''
  fetchLogs(1)
}

function statusClass(docstatus) {
  return {
    0: 'bg-yellow-50 text-yellow-700',
    1: 'bg-green-50 text-green-600',
    2: 'bg-red-50 text-red-500',
  }[docstatus] || 'bg-gray-100 text-gray-500'
}

function statusLabel(docstatus) {
  return { 0: 'Draft', 1: 'Submitted', 2: 'Cancelled' }[docstatus] || 'Unknown'
}

onMounted(() => {
  if (route.query.work_order) {
    filterWorkOrder.value = route.query.work_order
  }
  loadDashboard()
  fetchLogs(1)
})

const maxMonthly = computed(() => {
  if (!dashboard.value?.monthly_trend?.length) return 1
  return Math.max(...dashboard.value.monthly_trend.map(m => m.count), 1)
})

const maxMachine = computed(() => {
  if (!dashboard.value?.top_machines?.length) return 1
  return Math.max(...dashboard.value.top_machines.map(m => m.count), 1)
})

const maxTechnician = computed(() => {
  if (!dashboard.value?.top_technicians?.length) return 1
  return Math.max(...dashboard.value.top_technicians.map(m => m.count), 1)
})

const maxLocationCount = computed(() => {
  if (!dashboard.value?.location_breakdown?.length) return 1
  return Math.max(...dashboard.value.location_breakdown.map(m => m.count), 1)
})

function barHeight(value) {
  const max = maxLocationCount.value > maxMonthly.value ? maxLocationCount.value : maxMonthly.value
  if (!max) return 4
  return Math.max(4, Math.round((value / max) * 120))
}

function barPercent(value, total) {
  if (!total) return 0
  return Math.round((value / total) * 100)
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatMonth(m) {
  if (!m) return ''
  const [y, mo] = m.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return months[parseInt(mo) - 1] || mo
}
</script>
