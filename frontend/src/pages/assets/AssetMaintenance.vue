<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Operations • Asset Maintenance Management</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Asset Maintenance</h3>
        <p class="text-xs text-gray-400 mt-0.5">Schedule and manage preventive maintenance for assets.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/assets-mgmt/maintenance/new')">Create New Maintenance</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-yellow-300 transition-colors" @click="setFilter('Pending')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Awaiting</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.pending }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-green-300 transition-colors" @click="setFilter('Approved')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Approved</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.approved }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-red-300 transition-colors" @click="setFilter('Rejected')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Rejected</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Cancelled</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.rejected }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue Tasks</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-600 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.overdue_tasks }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search by asset name, category..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="debouncedFetch" />
        </div>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          @change="fetchList">
          <option value="">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </select>
        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/assets-mgmt/maintenance/new')">
          Create New Maintenance
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Asset Maintenance Records</h3>
        <p class="text-xs text-gray-400">Showing {{ records.length }} of {{ totalRecords }} records</p>
      </div>

      <div v-if="loading" class="px-6 py-12 text-center">
        <p class="text-xs text-gray-400">Loading...</p>
      </div>

      <div v-else-if="records.length === 0" class="px-6 py-12 text-center">
        <p class="text-sm text-gray-500">No asset maintenance records found.</p>
        <button class="mt-3 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          @click="$router.push('/assets-mgmt/maintenance/new')">Create First Maintenance</button>
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Asset</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Category</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Priority</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Technician</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Created</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Approval</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4">
              <p class="text-xs font-bold text-gray-900">{{ r.asset_name }}</p>
              <p class="text-xs text-gray-400">{{ r.item_name || r.item_code || '' }}</p>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.asset_category || '—' }}</td>
            <td class="px-4 py-4">
              <span class="text-xs font-medium" :class="priorityClass(r.rh_priority)">{{ r.rh_priority || '—' }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.rh_assigned_technician || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(r.creation) }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r)">{{ statusLabel(r) }}</span>
            </td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push(`/assets-mgmt/maintenance/${r.name}`)">View</button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Page {{ currentPage }} of {{ totalPages }}</p>
        <div class="flex items-center gap-1">
          <button @click="goToPage(currentPage - 1)" :disabled="currentPage <= 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white transition-colors disabled:opacity-40">Prev</button>
          <button v-for="p in displayPages" :key="p" @click="goToPage(p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="goToPage(currentPage + 1)" :disabled="currentPage >= totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white transition-colors disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'

const search = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 25
const loading = ref(false)
const records = ref([])
const totalRecords = ref(0)
const totalPages = ref(1)

const dashboard = ref({
  total: 0,
  pending: 0,
  approved: 0,
  rejected: 0,
  overdue_tasks: 0,
  planned_tasks: 0,
})

// Dashboard
const dashboardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.asset_maintenance.get_maintenance_dashboard',
  auto: true,
  onSuccess(data) {
    dashboard.value = data
  }
})

// List
function fetchList() {
  loading.value = true
  const listResource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.get_maintenance_list',
    params: {
      search: search.value || null,
      filter_status: filterStatus.value || null,
      page: currentPage.value,
      page_size: perPage,
    },
    onSuccess(data) {
      records.value = data.records
      totalRecords.value = data.total
      totalPages.value = data.total_pages
      loading.value = false
    },
    onError() {
      loading.value = false
    }
  })
  listResource.fetch()
}

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchList()
  }, 300)
}

function setFilter(status) {
  filterStatus.value = filterStatus.value === status ? '' : status
  currentPage.value = 1
  fetchList()
}

function resetFilters() {
  search.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  fetchList()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchList()
}

const displayPages = computed(() => {
  const pages = []
  const max = Math.min(totalPages.value, 7)
  for (let i = 1; i <= max; i++) pages.push(i)
  return pages
})

function statusLabel(r) {
  if (r.rh_approved === 'Rejected') return 'Rejected'
  if (r.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
}

function statusClass(r) {
  const label = statusLabel(r)
  return {
    'Pending':  'bg-yellow-50 text-yellow-600',
    'Approved': 'bg-green-50 text-green-600',
    'Rejected': 'bg-red-50 text-red-500',
  }[label] || 'bg-gray-100 text-gray-500'
}

function priorityClass(p) {
  return {
    'Critical': 'text-red-600 font-bold',
    'High':     'text-orange-600 font-semibold',
    'Medium':   'text-yellow-600',
    'Low':      'text-gray-600',
  }[p] || 'text-gray-900'
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => {
  fetchList()
})
</script>
