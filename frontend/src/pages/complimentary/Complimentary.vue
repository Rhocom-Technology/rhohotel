<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Manage complimentary room nights, food vouchers, airport transfers, upgrades, amenities, approvals, and usage tracking.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Complimentary Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ controlBarText }}</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/complimentary/list')">Complimentary List</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Register</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/complimentary/new')">New Complimentary</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Issued Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.issued_today }}</p>
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
          <p class="text-xs text-gray-400">Consumed Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Used</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.consumed_today }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Budget Impact</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatValue(stats.budget_impact_today) }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search guest, voucher, approval..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Types</option>
          <option>Food Voucher</option>
          <option>Airport Transfer</option>
          <option>Room Upgrade</option>
          <option>Amenity</option>
          <option>Late Checkout</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Approved</option>
          <option>Pending</option>
          <option>In Progress</option>
          <option>Consumed</option>
        </select>
        <select v-model="filterDept" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Departments</option>
          <option>Restaurant</option>
          <option>Front Desk</option>
          <option>Housekeeping</option>
          <option>GM Office</option>
        </select>
        <button @click="resetFilters()"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showPendingOnly ? 'text-white bg-yellow-500 hover:bg-yellow-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showPendingOnly = !showPendingOnly">
          {{ showPendingOnly ? 'Show All' : 'Show Pending Approvals Only' }}
        </button>
      </div>
    </div>

    <!-- Register + Insights -->
    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Complimentary Register -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Complimentary Register</h3>
        </div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Complimentary Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Value</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Approver</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="listResource.loading" class="border-b border-gray-50">
              <td colspan="6" class="px-6 py-8 text-xs text-center text-gray-400">Loading...</td>
            </tr>
            <tr v-else-if="!records.length" class="border-b border-gray-50">
              <td colspan="6" class="px-6 py-8 text-xs text-center text-gray-400">No complimentary records found.</td>
            </tr>
            <tr v-for="r in records" v-else :key="r.name"
              class="border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
              :class="selectedRecord === r.name ? 'bg-blue-50 border border-blue-300' : 'hover:bg-gray-50'"
              @click="selectedRecord = r.name; $router.push('/complimentary/' + r.name)">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.guest }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.room || '—' }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.complimentary_type }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r.status)">{{ r.status }}</span>
              </td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900">{{ formatValue(r.value) }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.approval_level }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Approval & Usage Insights -->
      <div class="space-y-3">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Top Complimentary Types</p>
          <p class="text-sm font-bold text-gray-900 mb-1">Late Checkout • Food Voucher • Amenity Basket</p>
          <p class="text-xs text-gray-400">Most issued across VIP and service-recovery cases</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-3">Pending Approval Queue</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">• 2 food vouchers awaiting GM approval</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">• 1 room upgrade pending availability</p>
          <p class="text-xs text-gray-600 py-1">• 3 transport requests pending dispatch</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-2">Consumption Summary</p>
          <p class="text-xs text-gray-500 leading-relaxed">4 complimentary items consumed today. Usage rate this week is 78% of issued benefits.</p>
        </div>
        <div class="bg-blue-50 rounded-xl border border-blue-200 px-5 py-4">
          <p class="text-sm font-bold text-blue-700 mb-2">Suggested Action</p>
          <p class="text-xs text-blue-600 leading-relaxed">Review pending dinner voucher for Room 511 and close consumed items awaiting confirmation.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">Complimentary management page for approvals, issuance, consumption, and control.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterDept = ref('')
const showPendingOnly = ref(false)
const selectedRecord = ref(null)

// ── Stats ─────────────────────────────────────────────────────────────────────
const stats = ref({ issued_today: 0, pending_approval: 0, consumed_today: 0, active_count: 0, expired_unused: 0, budget_impact_today: 0 })

const dashboardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_complimentary_dashboard',
  onSuccess(data) {
    stats.value = data
  },
})

// ── Register List ─────────────────────────────────────────────────────────────
const records = ref([])
const totalRecords = ref(0)

const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_complimentary_list',
  onSuccess(data) {
    records.value = data.records || []
    totalRecords.value = data.total || 0
    if (records.value.length && !selectedRecord.value) {
      selectedRecord.value = records.value[0].name
    }
  },
  onError() {
    records.value = []
  },
})

function fetchList() {
  listResource.fetch({
    search: search.value || null,
    filter_type: filterType.value || null,
    filter_status: showPendingOnly.value ? 'Pending' : (filterStatus.value || null),
    filter_approver: filterDept.value || null,
    page: 1,
    page_size: 10,
  })
}

watch([search, filterType, filterStatus, filterDept], fetchList)
watch(showPendingOnly, fetchList)

const controlBarText = computed(() => {
  const active = stats.value.active_count
  const pending = stats.value.pending_approval
  const consumed = stats.value.consumed_today
  const expired = stats.value.expired_unused
  return `${active} active complimentary items • ${pending} pending approvals • ${consumed} consumed today • ${expired} expired unused`
})

function formatValue(v) {
  if (!v && v !== 0) return '—'
  return '₦' + Number(v).toLocaleString()
}

function resetFilters() {
  search.value = ''
  filterType.value = ''
  filterStatus.value = ''
  filterDept.value = ''
  showPendingOnly.value = false
}

function statusClass(s) {
  return {
    'Approved':    'bg-green-50 text-green-600',
    'In Progress': 'bg-blue-50 text-blue-600',
    'Consumed':    'bg-green-100 text-green-700',
    'Pending':     'bg-yellow-50 text-yellow-600',
    'Expired':     'bg-gray-100 text-gray-500',
    'Cancelled':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

onMounted(() => {
  dashboardResource.fetch()
  fetchList()
})
</script>