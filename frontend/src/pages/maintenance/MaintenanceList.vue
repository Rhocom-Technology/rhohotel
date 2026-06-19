<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Maintenance Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Manage corrective, preventive, urgent, and scheduled tasks with quick access to technicians, service history, and reporting.</p>
      </div>
      <div class="flex items-center gap-3">
        <router-link to="/maintenance/technicians">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Technicians</button>
        </router-link>
        <!-- <router-link to="/maintenance/new-task">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">New Maintenance</button>
        </router-link> -->
      </div>
    </div>

    <!-- Stats skeleton -->
    <div v-if="statsLoading" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div v-for="n in 4" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-2 bg-gray-100 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Stats: 2 rows -->
    <template v-else-if="stats">
      <!-- Row 1: Live status counts -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Open Tasks</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.open }}</p>
          <p class="text-xs text-gray-400 mt-1">Awaiting assignment</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">In Progress</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">Running</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.in_progress }}</p>
          <p class="text-xs text-gray-400 mt-1">Currently being worked on</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">On Hold</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Paused</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.on_hold }}</p>
          <p class="text-xs text-gray-400 mt-1">Pending parts or approval</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Urgent Open</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">High</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.urgent_open }}</p>
          <p class="text-xs text-gray-400 mt-1">High priority, not done</p>
        </div>
      </div>

      <!-- Row 2: Time-bounded counts -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Completed Today</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.done_today }}</p>
          <p class="text-xs text-gray-400 mt-1">Closed since midnight</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Closed This Week</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Week</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.done_this_week }}</p>
          <p class="text-xs text-gray-400 mt-1">Since Monday</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Scheduled Today</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Due</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.scheduled_today }}</p>
          <p class="text-xs text-gray-400 mt-1">Start time is today</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">All Completed</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Total</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.done }}</p>
          <p class="text-xs text-gray-400 mt-1">All time</p>
        </div>
      </div>
    </template>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="relative" style="flex:1;min-width:180px;">
          <input v-model="search" @input="debouncedFetch" type="text"
            placeholder="Search task ID, location, description..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" @change="fetchTasks(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Types</option>
          <option value="Corrective">Corrective</option>
          <option value="Preventive">Preventive</option>
          <option value="Routine">Routine</option>
          <option value="Inspection">Inspection</option>
        </select>
        <select v-model="filterPriority" @change="fetchTasks(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Priorities</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select v-model="filterStatus" @change="fetchTasks(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Statuses</option>
          <option value="Open">Open</option>
          <option value="In Progress">In Progress</option>
          <option value="Hold">On Hold</option>
          <option value="Done">Done</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <select v-model="filterTech" @change="fetchTasks(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Technicians</option>
          <option v-for="t in technicians" :key="t.name" :value="t.name">
            {{ t.technician_name }}
          </option>
        </select>
        <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
        <button @click="filterPriority = 'High'; fetchTasks(1)"
          class="px-4 py-2 text-xs font-semibold text-white bg-red-500 rounded-lg hover:bg-red-600">
          Urgent Only
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Records</h3>
        <p class="text-xs text-gray-400" v-if="!listLoading">
          Showing {{ total === 0 ? 0 : ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, total) }} of {{ total }} tasks
        </p>
      </div>

      <!-- Table loading -->
      <div v-if="listLoading" class="flex items-center justify-center py-16 gap-3">
        <svg class="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        <p class="text-sm text-gray-400">Loading tasks...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Task ID</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Description</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Type</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Location</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Technician</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Start Time</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in tasks" :key="item.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="router.push({ name: 'MaintenanceTask', params: { id: item.name } })">
              <td class="px-6 py-4 text-xs font-bold text-gray-900 font-mono">{{ item.name }}</td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.task_description || '—' }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.task_type }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.location || '—' }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.technician_name }}</td>
              <td class="px-4 py-4 text-xs text-gray-500">{{ formatDate(item.start_time) }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(item.priority)">
                  {{ item.priority }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border" :class="statusClass(item.status)">
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button
                  @click.stop="router.push({ name: 'MaintenanceTask', params: { id: item.name } })"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                  View
                </button>
              </td>
            </tr>
            <tr v-if="tasks.length === 0 && !listLoading">
              <td colspan="9" class="text-center py-12 text-xs text-gray-400">No maintenance tasks found</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <p class="text-xs text-gray-400">Rows per page:</p>
          <select v-model="pageSize" @change="fetchTasks(1)"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button @click="fetchTasks(page - 1)" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Previous
          </button>
          <span class="text-xs text-gray-600">Page {{ page }} of {{ totalPages }}</span>
          <button @click="fetchTasks(page + 1)" :disabled="page >= totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()

// ─── State ────────────────────────────────────────────────────────────────────
const search = ref('')
const filterType = ref('')
const filterPriority = ref('')
const filterStatus = ref('')
const filterTech = ref('')
const page = ref(1)
const pageSize = ref(25)
const totalPages = ref(1)
const total = ref(0)

const statsLoading = ref(true)
const listLoading = ref(true)
const stats = ref(null)
const tasks = ref([])
const technicians = ref([])

// ─── Resources ────────────────────────────────────────────────────────────────
const statsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_dashboard',
  auto: false
})

const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_list',
  auto: false
})

const techResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_technicians_filter',
  auto: false
})

// ─── Fetch stats ──────────────────────────────────────────────────────────────
async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await statsResource.fetch()
    console.log('[MaintenanceList] stats:', res)
    stats.value = res
  } catch (e) {
    console.error('[MaintenanceList] stats error:', e)
  } finally {
    statsLoading.value = false
  }
}

// ─── Fetch task list ──────────────────────────────────────────────────────────
async function fetchTasks(newPage = 1) {
  page.value = newPage
  listLoading.value = true
  try {
    const res = await listResource.fetch({
      search: search.value || null,
      filter_type: filterType.value || null,
      filter_priority: filterPriority.value || null,
      filter_status: filterStatus.value || null,
      filter_technician: filterTech.value || null,
      page: page.value,
      page_size: pageSize.value
    })
    console.log('[MaintenanceList] list:', res)
    tasks.value = res?.tasks || []
    total.value = res?.total || 0
    totalPages.value = res?.total_pages || 1
  } catch (e) {
    console.error('[MaintenanceList] list error:', e)
    tasks.value = []
  } finally {
    listLoading.value = false
  }
}

// ─── Debounce search ──────────────────────────────────────────────────────────
let searchTimer = null
function debouncedFetch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchTasks(1), 350)
}

// ─── Filters ──────────────────────────────────────────────────────────────────
function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterPriority.value = ''
  filterStatus.value = ''
  filterTech.value = ''
  fetchTasks(1)
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}

function priorityClass(p) {
  return {
    'High':   'bg-red-100 text-red-500',
    'Medium': 'bg-yellow-100 text-yellow-600',
    'Low':    'bg-blue-50 text-blue-500',
  }[p] || 'bg-gray-100 text-gray-500'
}

function statusClass(s) {
  return {
    'Open':        'bg-blue-50 text-blue-600 border-blue-200',
    'In Progress': 'bg-purple-50 text-purple-600 border-purple-200',
    'Done':        'bg-green-50 text-green-600 border-green-200',
    'Hold':        'bg-yellow-50 text-yellow-600 border-yellow-200',
    'Cancelled':   'bg-red-50 text-red-500 border-red-200',
  }[s] || 'bg-gray-50 text-gray-500 border-gray-200'
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  const [, techRes] = await Promise.all([
    fetchStats(),
    techResource.fetch()
  ])
  technicians.value = techRes || []
  fetchTasks(1)
})
</script>