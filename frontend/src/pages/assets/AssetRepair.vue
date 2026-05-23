<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Operations • Asset Repair Management</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Asset Repair</h3>
        <p class="text-xs text-gray-400 mt-0.5">Track asset repairs, review approval status, and manage repair requests.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/maintenance/list')">Maintenance List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/assets-mgmt/repair/new')">Create New Asset Repair</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Repairs</p>
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
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-blue-300 transition-colors" @click="setFilter('Completed')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Completed</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Done</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.completed }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-red-300 transition-colors" @click="setFilter('Cancelled')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Rejected</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Cancelled</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.rejected }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search repair ID, asset name, description..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="debouncedFetch" />
        </div>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          @change="fetchRepairs">
          <option value="">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/assets-mgmt/repair/new')">
          Create New Asset Repair
        </button>
      </div>
    </div>

    <!-- Asset Repair Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Asset Repairs</h3>
        <p class="text-xs text-gray-400">Showing {{ repairs.length }} of {{ totalRepairs }} repairs</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="px-6 py-12 text-center">
        <p class="text-xs text-gray-400">Loading asset repairs...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="repairs.length === 0" class="px-6 py-12 text-center">
        <p class="text-sm text-gray-500">No asset repairs found.</p>
        <button class="mt-3 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          @click="$router.push('/assets-mgmt/repair/new')">Create First Repair</button>
      </div>

      <!-- Table -->
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Repair ID</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Asset</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Description</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Failure Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cost</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Created By</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in repairs" :key="r.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.name }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">
              <span class="font-semibold">{{ r.asset_name || r.asset }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600 max-w-[200px] truncate">{{ r.description || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(r.failure_date) }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ formatCurrency(r.total_repair_cost) }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.created_by }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r)">{{ statusLabel(r) }}</span>
            </td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push(`/assets-mgmt/repair/${r.name}`)">View</button>
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
const repairs = ref([])
const totalRepairs = ref(0)
const totalPages = ref(1)

const dashboard = ref({
  total: 0,
  pending: 0,
  approved: 0,
  completed: 0,
  rejected: 0,
})

// Dashboard stats
const dashboardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.asset_repair.get_repair_dashboard',
  auto: true,
  onSuccess(data) {
    dashboard.value = data
  }
})

// Repair list
function fetchRepairs() {
  loading.value = true
  const listResource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.get_repair_list',
    params: {
      search: search.value || null,
      filter_status: filterStatus.value || null,
      page: currentPage.value,
      page_size: perPage,
    },
    onSuccess(data) {
      repairs.value = data.repairs
      totalRepairs.value = data.total
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
    fetchRepairs()
  }, 300)
}

function setFilter(status) {
  if (status === 'Approved') {
    // Approved is a virtual status mapped from docstatus
    filterStatus.value = ''
    // We'll just reload to show all and let the user see
  } else {
    filterStatus.value = status
  }
  currentPage.value = 1
  fetchRepairs()
}

function resetFilters() {
  search.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  fetchRepairs()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchRepairs()
}

const displayPages = computed(() => {
  const pages = []
  const max = Math.min(totalPages.value, 7)
  for (let i = 1; i <= max; i++) pages.push(i)
  return pages
})

function statusLabel(r) {
  if (r.rh_approved === 'Rejected' || r.repair_status === 'Cancelled') return 'Rejected'
  if (r.repair_status === 'Completed') return 'Completed'
  if (r.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
}

function statusClass(r) {
  const label = statusLabel(r)
  return {
    'Pending':   'bg-yellow-50 text-yellow-600',
    'Approved':  'bg-green-50 text-green-600',
    'Completed': 'bg-blue-50 text-blue-600',
    'Rejected':  'bg-red-50 text-red-500',
    'Cancelled': 'bg-red-50 text-red-500',
  }[label] || 'bg-gray-100 text-gray-500'
}

function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(val) {
  if (!val && val !== 0) return '—'
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(val)
}

onMounted(() => {
  fetchRepairs()
})
</script>