<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Operations / <span class="text-gray-600">Complimentary Management</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Complimentary List</h1>
      <p class="text-xs text-gray-400 mt-1">Review all complimentary entries, approval states, issue dates, values, consumers, and redemption or usage progress in one register.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Complimentary Register Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ total }} total records • {{ stats.active_count }} active • {{ stats.pending_approval }} pending approval</p>
      </div>
      <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
        <button class="w-full px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto"
          @click="$router.push('/complimentary')">Complimentary Dashboard</button>
        <button class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors sm:w-auto"
          @click="$router.push('/complimentary/new')">New Complimentary</button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Records</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All Time</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Active Benefits</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.active_count }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Approval</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Waiting</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.pending_approval }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Budget Impact Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatValue(stats.budget_impact_today) }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div class="w-full sm:min-w-[180px] sm:flex-1">
          <input v-model="search" type="text" placeholder="Search guest, code, benefit..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Types</option>
          <option>Food Voucher</option>
          <option>Room Voucher</option>
          <option>Airport Transfer</option>
          <option>Room Upgrade</option>
          <option>Amenity Basket</option>
          <option>Laundry / Amenity</option>
        </select>
        <select v-model="filterStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Statuses</option>
          <option>Draft</option>
          <option>Pending</option>
          <option>Approved</option>
          <option>In Progress</option>
          <option>Consumed</option>
          <option>Expired</option>
          <option>Cancelled</option>
        </select>
        <select v-model="filterApprover" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Approvers</option>
          <option>General Manager</option>
          <option>Duty Manager</option>
          <option>Front Desk Supervisor</option>
          <option>Operations Lead</option>
        </select>
        <select v-model="filterDepartment" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Departments</option>
          <option>Restaurant</option>
          <option>Front Desk</option>
          <option>Housekeeping</option>
          <option>Laundry</option>
          <option>GM Office</option>
          <option>Operations</option>
        </select>
        <button @click="resetFilters()"
          class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">Reset</button>
        <button
          class="w-full px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors sm:w-auto"
          :class="showConsumedOnly ? 'text-white bg-green-600 hover:bg-green-700' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showConsumedOnly = !showConsumedOnly">
          {{ showConsumedOnly ? 'Show All Records' : 'Show Consumed Benefits Only' }}
        </button>
      </div>
    </div>

    <!-- Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-4 py-4 border-b border-gray-100 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h3 class="text-sm font-bold text-gray-900">Complimentary Records</h3>
        <p class="text-xs text-gray-400">{{ showingText }}</p>
      </div>
      <div class="overflow-x-auto">
      <table class="w-full min-w-[980px]">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Code</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issued On</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Value</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Approver</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="listResource.loading" class="border-b border-gray-50">
            <td colspan="9" class="px-6 py-8 text-xs text-center text-gray-400">Loading...</td>
          </tr>
          <tr v-else-if="!records.length" class="border-b border-gray-50">
            <td colspan="9" class="px-6 py-8 text-xs text-center text-gray-400">No records found.</td>
          </tr>
          <tr v-for="r in records" v-else :key="r.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.name }}</td>
            <td class="px-4 py-4">
              <div class="text-xs font-bold text-gray-900">{{ r.guest }}</div>
              <div class="text-xs text-gray-400">{{ r.note || r.reason || '' }}</div>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.room || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.complimentary_type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.issue_date }}</td>
            <td class="px-4 py-4 text-xs font-bold text-gray-900">{{ formatValue(r.value) }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r.status)">{{ r.status }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.approval_level }}</td>
            <td class="px-4 py-4">
              <button
                class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push('/complimentary/' + r.name)">
                {{ actionLabel(r.status) }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- Pagination -->
      <div class="px-4 py-4 border-t border-gray-100 flex flex-col gap-3 bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex flex-wrap items-center gap-1">
          <button v-for="p in pageNumbers" :key="p" @click="currentPage = p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button v-if="currentPage < totalPages" @click="currentPage++"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource } from 'frappe-ui'

const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterApprover = ref('')
const filterDepartment = ref('')
const showConsumedOnly = ref(false)
const currentPage = ref(1)
const PAGE_SIZE = 25

// ── Stats ─────────────────────────────────────────────────────────────────────
const stats = ref({ issued_today: 0, pending_approval: 0, active_count: 0, budget_impact_today: 0 })

const dashboardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_complimentary_dashboard',
  onSuccess(data) { stats.value = data },
})

// ── List ──────────────────────────────────────────────────────────────────────
const records = ref([])
const total = ref(0)
const totalPages = ref(1)

const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_complimentary_list',
  onSuccess(data) {
    records.value = data.records || []
    total.value = data.total || 0
    totalPages.value = data.total_pages || 1
  },
  onError() { records.value = [] },
})

function fetchList() {
  listResource.fetch({
    search: search.value || null,
    filter_type: filterType.value || null,
    filter_status: showConsumedOnly.value ? 'Consumed' : (filterStatus.value || null),
    filter_approver: filterApprover.value || null,
    filter_department: filterDepartment.value || null,
    page: currentPage.value,
    page_size: PAGE_SIZE,
  })
}

watch([search, filterType, filterStatus, filterApprover, filterDepartment], () => {
  currentPage.value = 1
  fetchList()
})
watch(showConsumedOnly, () => {
  currentPage.value = 1
  fetchList()
})
watch(currentPage, fetchList)

function resetFilters() {
  search.value = ''
  filterType.value = ''
  filterStatus.value = ''
  filterApprover.value = ''
  filterDepartment.value = ''
  showConsumedOnly.value = false
  currentPage.value = 1
}

const showingText = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE + 1
  const end = Math.min(currentPage.value * PAGE_SIZE, total.value)
  return total.value ? `Showing ${start}–${end} of ${total.value} records` : 'No records'
})

function formatValue(v) {
  if (!v && v !== 0) return '—'
  return '₦' + Number(v).toLocaleString()
}

function actionLabel(status) {
  if (status === 'Pending') return 'Review'
  if (status === 'Approved' || status === 'In Progress') return 'Update'
  return 'View'
}

function statusClass(s) {
  return {
    'Draft':       'bg-gray-100 text-gray-500',
    'Approved':    'bg-green-50 text-green-600',
    'In Progress': 'bg-blue-50 text-blue-600',
    'Consumed':    'bg-green-100 text-green-700',
    'Pending':     'bg-yellow-50 text-yellow-600',
    'Expired':     'bg-gray-100 text-gray-500',
    'Cancelled':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

const pageNumbers = computed(() => {
  const pages = []
  for (let i = 1; i <= Math.min(totalPages.value, 4); i++) pages.push(i)
  return pages
})

onMounted(() => {
  dashboardResource.fetch()
  fetchList()
})
</script>
