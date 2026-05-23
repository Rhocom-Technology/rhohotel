<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Request Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track open, approved, and resolved requests with quick access to view, approve, and convert into maintenance tasks.</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="router.push('/maintenance/new-request')"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">
          New Request
        </button>
      </div>
    </div>

    <!-- Stats skeleton -->
    <div v-if="statsLoading" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div v-for="n in 4" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3"></div>
      </div>
    </div>

    <!-- Stats -->
    <div v-else-if="stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Pending Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.pending }}</p>
        <p class="text-xs text-gray-400 mt-1">Awaiting action</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Urgent / Critical</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">High</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.urgent_pending }}</p>
        <p class="text-xs text-gray-400 mt-1">High or Critical priority</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Approved & Pending</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Approved</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.approved_pending }}</p>
        <p class="text-xs text-gray-400 mt-1">Ready for task creation</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Resolved This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.resolved_this_week }}</p>
        <p class="text-xs text-gray-400 mt-1">Completed since Monday</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div style="flex:1;min-width:180px;">
          <input v-model="search" @input="debouncedFetch" type="text"
            placeholder="Search request ID, room, location..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterIssueType" @change="fetchRequests(1)"
          class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Issue Types</option>
          <option value="Plumbing">Plumbing</option>
          <option value="Electrical">Electrical</option>
          <option value="HVAC">HVAC</option>
          <option value="Furniture">Furniture</option>
          <option value="Appliance">Appliance</option>
          <option value="Electronics">Electronics</option>
          <option value="Structural">Structural</option>
          <option value="Other">Other</option>
        </select>
        <select v-model="filterPriority" @change="fetchRequests(1)"
          class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select v-model="filterStatus" @change="fetchRequests(1)"
          class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Approved">Approved</option>
          <option value="In Progress">In Progress</option>
          <option value="Completed">Completed</option>
          <option value="Rejected">Rejected</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <button @click="clearFilters"
          class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
          Reset
        </button>
        <button @click="filterPriority = 'Critical'; fetchRequests(1)"
          class="px-4 py-2 text-xs font-semibold text-white bg-red-500 rounded-lg hover:bg-red-600">
          Critical Only
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Request Records</h3>
        <p class="text-xs text-gray-400" v-if="!listLoading">
          Showing {{ total === 0 ? 0 : ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, total) }} of {{ total }}
        </p>
      </div>

      <div v-if="listLoading" class="flex items-center justify-center py-16 gap-3">
        <svg class="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        <p class="text-sm text-gray-400">Loading requests...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Request ID</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Location</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Issue Type</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Reported By</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Reported At</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Approved</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="req in requests" :key="req.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="router.push({ name: 'SavedMaintenanceRequest', params: { id: req.name } })">
              <td class="px-6 py-4 text-xs font-bold text-gray-900 font-mono">{{ req.name }}</td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ req.location_display || '—' }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ req.location_type || '—' }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ req.issue_type }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ req.reported_by_name || req.reported_by || '—' }}</td>
              <td class="px-4 py-4 text-xs text-gray-500">{{ formatDate(req.reported_at) }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(req.priority)">
                  {{ req.priority }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span class="text-xs font-semibold" :class="approvedClass(req.approved)">
                  {{ req.approved || 'Pending' }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border" :class="statusClass(req.status)">
                  {{ req.status }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="router.push({ name: 'SavedMaintenanceRequest', params: { id: req.name } })"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                  View
                </button>
              </td>
            </tr>
            <tr v-if="requests.length === 0">
              <td colspan="9" class="text-center py-12 text-xs text-gray-400">No maintenance requests found</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <p class="text-xs text-gray-400">Rows per page:</p>
          <select v-model="pageSize" @change="fetchRequests(1)"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button @click="fetchRequests(page - 1)" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Previous
          </button>
          <span class="text-xs text-gray-600">Page {{ page }} of {{ totalPages }}</span>
          <button @click="fetchRequests(page + 1)" :disabled="page >= totalPages"
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

const statsLoading = ref(true)
const listLoading = ref(true)
const stats = ref(null)
const requests = ref([])
const search = ref('')
const filterIssueType = ref('')
const filterPriority = ref('')
const filterStatus = ref('')
const page = ref(1)
const pageSize = ref(25)
const total = ref(0)
const totalPages = ref(1)

const statsResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_request_dashboard', auto: false })
const listResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_request_list', auto: false })

async function fetchStats() {
  statsLoading.value = true
  try {
    stats.value = await statsResource.fetch()
  } catch (e) {
    console.error('[MRList] stats error:', e)
  } finally {
    statsLoading.value = false
  }
}

async function fetchRequests(newPage = 1) {
  page.value = newPage
  listLoading.value = true
  try {
    const res = await listResource.fetch({
      search: search.value || null,
      filter_priority: filterPriority.value || null,
      filter_status: filterStatus.value || null,
      filter_issue_type: filterIssueType.value || null,
      page: page.value,
      page_size: pageSize.value
    })
    requests.value = res?.requests || []
    total.value = res?.total || 0
    totalPages.value = res?.total_pages || 1
  } catch (e) {
    console.error('[MRList] list error:', e)
    requests.value = []
  } finally {
    listLoading.value = false
  }
}

let searchTimer = null
function debouncedFetch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchRequests(1), 350)
}

function clearFilters() {
  search.value = ''
  filterIssueType.value = ''
  filterPriority.value = ''
  filterStatus.value = ''
  fetchRequests(1)
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function priorityClass(p) {
  return {
    'Critical': 'bg-red-100 text-red-600',
    'High':     'bg-orange-100 text-orange-500',
    'Medium':   'bg-yellow-100 text-yellow-600',
    'Low':      'bg-blue-50 text-blue-500',
  }[p] || 'bg-gray-100 text-gray-500'
}

function statusClass(s) {
  return {
    'Pending':     'bg-blue-50 text-blue-600 border-blue-200',
    'Approved':    'bg-green-50 text-green-600 border-green-200',
    'In Progress': 'bg-purple-50 text-purple-600 border-purple-200',
    'Completed':   'bg-green-50 text-green-600 border-green-200',
    'Rejected':    'bg-red-50 text-red-500 border-red-200',
    'Cancelled':   'bg-red-50 text-red-500 border-red-200',
  }[s] || 'bg-gray-50 text-gray-500 border-gray-200'
}

function approvedClass(a) {
  return {
    'Approved': 'text-green-600',
    'Rejected': 'text-red-500',
    'Pending':  'text-gray-400',
  }[a] || 'text-gray-400'
}

onMounted(() => {
  fetchStats()
  fetchRequests(1)
})
</script>