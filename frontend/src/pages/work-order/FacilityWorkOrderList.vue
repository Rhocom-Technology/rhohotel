<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Facility Work Orders</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track, filter, and manage facility work orders across all departments and workflow stages.</p>
      </div>
      <div class="flex items-center gap-3">
        <router-link to="/work-order/dashboard">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Dashboard</button>
        </router-link>
        <router-link to="/work-order/new">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">New Work Order</button>
        </router-link>
      </div>
    </div>

    <!-- Stats skeleton -->
    <div v-if="statsLoading" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div v-for="n in 8" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-2 bg-gray-100 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Stats -->
    <template v-else-if="stats">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Active Orders</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Open</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.active }}</p>
          <p class="text-xs text-gray-400 mt-1">In workflow pipeline</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Emergency</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Critical</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.emergency }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ stats.urgent }} urgent</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Overdue</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-600 rounded-full">Late</span>
          </div>
          <p class="text-3xl font-bold" :class="stats.overdue > 0 ? 'text-orange-600' : 'text-gray-900'">{{ stats.overdue }}</p>
          <p class="text-xs text-gray-400 mt-1">Past expected date</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Closed This Week</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.closed_this_week }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ stats.closed }} total closed</p>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Unassigned</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Pending</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.unassigned }}</p>
          <p class="text-xs text-gray-400 mt-1">No technician</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Rejected</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-red-50 text-red-400 rounded-full">Denied</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.rejected }}</p>
          <p class="text-xs text-gray-400 mt-1">All-time rejected</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 col-span-2">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Quick Filters</p>
          </div>
          <div class="flex items-center gap-2 flex-wrap mt-1">
            <button @click="filterStatus = 'Draft'; fetchOrders(1)"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
              Drafts
            </button>
            <button @click="filterPriority = 'Emergency'; fetchOrders(1)"
              class="px-3 py-1.5 text-xs font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50">
              Emergency
            </button>
            <button @click="filterStatus = 'Pending Facility Supervisor Approval'; fetchOrders(1)"
              class="px-3 py-1.5 text-xs font-medium text-yellow-700 border border-yellow-200 rounded-lg hover:bg-yellow-50">
              Awaiting Supervisor
            </button>
            <button @click="filterStatus = 'Pending Department Head Signature'; fetchOrders(1)"
              class="px-3 py-1.5 text-xs font-medium text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50">
              Awaiting Dept Head
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="relative" style="flex:1;min-width:180px;">
          <input v-model="search" @input="debouncedFetch" type="text"
            placeholder="Search WO ID, department, category, location..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterPriority" @change="fetchOrders(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Priorities</option>
          <option value="Emergency">Emergency</option>
          <option value="Urgent">Urgent</option>
          <option value="Routine">Routine</option>
        </select>
        <select v-model="filterStatus" @change="fetchOrders(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Statuses</option>
          <option value="Draft">Draft</option>
          <option value="Pending Requesting Officer Approval">Pending Req. Approval</option>
          <option value="Pending Facility Supervisor Approval">Pending Supervisor</option>
          <option value="Pending Department Head Signature">Pending Dept Head</option>
          <option value="Closed">Closed</option>
          <option value="Rejected">Rejected</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <select v-model="filterCategory" @change="fetchOrders(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Categories</option>
          <option value="Electrical">Electrical</option>
          <option value="Plumbing">Plumbing</option>
          <option value="HVAC">HVAC</option>
          <option value="Civil">Civil</option>
          <option value="Other">Other</option>
        </select>
        <select v-model="filterDepartment" @change="fetchOrders(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Departments</option>
          <option v-for="d in departments" :key="d.name" :value="d.name">{{ d.name }}</option>
        </select>
        <select v-model="filterTechnician" @change="fetchOrders(1)" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Technicians</option>
          <option v-for="t in technicians" :key="t.name" :value="t.name">{{ t.technician_name }}</option>
        </select>
        <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Work Order Records</h3>
        <p class="text-xs text-gray-400" v-if="!listLoading">
          Showing {{ total === 0 ? 0 : ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, total) }} of {{ total }} orders
        </p>
      </div>

      <!-- Loading -->
      <div v-if="listLoading" class="flex items-center justify-center py-16 gap-3">
        <svg class="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        <p class="text-sm text-gray-400">Loading work orders...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">WO ID</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Department</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Category</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Location</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Technician</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Reported</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in orders" :key="item.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="router.push({ name: 'FacilityWorkOrderDetail', params: { id: item.name } })">
              <td class="px-6 py-4 text-xs font-bold text-gray-900 font-mono">{{ item.name }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.requesting_department || '—' }}</td>
              <td class="px-4 py-4">
                <span v-if="item.category" class="px-2 py-0.5 text-xs font-medium rounded"
                  :class="categoryClass(item.category)">{{ item.category }}</span>
                <span v-else class="text-xs text-gray-400">—</span>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.location_display }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.technician_name }}</td>
              <td class="px-4 py-4 text-xs text-gray-500">{{ formatDate(item.date_reported) }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(item.priority)">
                  {{ item.priority }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2 py-1 text-[10px] font-medium rounded-full" :class="statusClass(item.workflow_state)">
                  {{ shortState(item.workflow_state) }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button
                  @click.stop="router.push({ name: 'FacilityWorkOrderDetail', params: { id: item.name } })"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                  View
                </button>
              </td>
            </tr>
            <tr v-if="orders.length === 0 && !listLoading">
              <td colspan="9" class="text-center py-12 text-xs text-gray-400">No work orders found</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <p class="text-xs text-gray-400">Rows per page:</p>
          <select v-model="pageSize" @change="fetchOrders(1)"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button @click="fetchOrders(page - 1)" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Previous
          </button>
          <span class="text-xs text-gray-600">Page {{ page }} of {{ totalPages }}</span>
          <button @click="fetchOrders(page + 1)" :disabled="page >= totalPages"
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
const filterPriority = ref('')
const filterStatus = ref('')
const filterCategory = ref('')
const filterDepartment = ref('')
const filterTechnician = ref('')
const page = ref(1)
const pageSize = ref(25)
const totalPages = ref(1)
const total = ref(0)

const statsLoading = ref(true)
const listLoading = ref(true)
const stats = ref(null)
const orders = ref([])
const technicians = ref([])
const departments = ref([])

// ─── Resources ────────────────────────────────────────────────────────────────
const statsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_facility_work_order_stats',
  auto: false
})

const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_facility_work_order_list',
  auto: false
})

const filtersResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_facility_work_order_filters',
  auto: false
})

// ─── Fetch stats ──────────────────────────────────────────────────────────────
async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await statsResource.fetch()
    stats.value = res
  } catch (e) {
    console.error('[FacilityWorkOrderList] stats error:', e)
  } finally {
    statsLoading.value = false
  }
}

// ─── Fetch list ───────────────────────────────────────────────────────────────
async function fetchOrders(newPage = 1) {
  page.value = newPage
  listLoading.value = true
  try {
    const res = await listResource.fetch({
      search: search.value || null,
      filter_priority: filterPriority.value || null,
      filter_status: filterStatus.value || null,
      filter_category: filterCategory.value || null,
      filter_department: filterDepartment.value || null,
      filter_technician: filterTechnician.value || null,
      page: page.value,
      page_size: pageSize.value
    })
    orders.value = res?.orders || []
    total.value = res?.total || 0
    totalPages.value = res?.total_pages || 1
  } catch (e) {
    console.error('[FacilityWorkOrderList] list error:', e)
    orders.value = []
  } finally {
    listLoading.value = false
  }
}

// ─── Debounce search ──────────────────────────────────────────────────────────
let searchTimer = null
function debouncedFetch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchOrders(1), 350)
}

// ─── Filters ──────────────────────────────────────────────────────────────────
function clearFilters() {
  search.value = ''
  filterPriority.value = ''
  filterStatus.value = ''
  filterCategory.value = ''
  filterDepartment.value = ''
  filterTechnician.value = ''
  fetchOrders(1)
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
    'Emergency': 'bg-red-100 text-red-600',
    'Urgent':    'bg-yellow-100 text-yellow-600',
    'Routine':   'bg-green-100 text-green-600',
  }[p] || 'bg-gray-100 text-gray-500'
}

function categoryClass(c) {
  return {
    'Electrical': 'bg-blue-50 text-blue-600',
    'Plumbing':   'bg-cyan-50 text-cyan-600',
    'HVAC':       'bg-yellow-50 text-yellow-700',
    'Civil':      'bg-purple-50 text-purple-600',
    'Other':      'bg-gray-50 text-gray-600',
  }[c] || 'bg-gray-50 text-gray-500'
}

function statusClass(s) {
  return {
    'Draft':                                  'bg-gray-100 text-gray-600',
    'Pending Requesting Officer Approval':    'bg-blue-50 text-blue-600',
    'Pending Facility Supervisor Approval':   'bg-yellow-50 text-yellow-700',
    'Pending Department Head Signature':      'bg-purple-50 text-purple-600',
    'Closed':                                 'bg-green-50 text-green-600',
    'Rejected':                               'bg-red-50 text-red-500',
    'Cancelled':                              'bg-red-50 text-red-400',
  }[s] || 'bg-gray-100 text-gray-500'
}

function shortState(state) {
  return {
    'Draft': 'Draft',
    'Pending Requesting Officer Approval': 'Req. Approval',
    'Pending Facility Supervisor Approval': 'Supervisor',
    'Pending Department Head Signature': 'Dept Head',
    'Closed': 'Closed',
    'Rejected': 'Rejected',
    'Cancelled': 'Cancelled',
  }[state] || state
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  const [, filtersRes] = await Promise.all([
    fetchStats(),
    filtersResource.fetch()
  ])
  technicians.value = filtersRes?.technicians || []
  departments.value = filtersRes?.departments || []
  fetchOrders(1)
})
</script>
