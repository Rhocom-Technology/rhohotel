<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Operations • central asset register for rooms, facilities, and equipment</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Asset Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">Search assets, track assignments, review service status, and access asset details.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/assets-mgmt')">Dashboard</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/assets-mgmt/repair')">Asset Repair</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/assets-mgmt/maintenance')">Asset Maintenance</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Assets</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-green-300 transition-colors" @click="setFilter('Submitted')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Submitted</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.submitted }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-yellow-300 transition-colors" @click="setFilter('In Maintenance')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">In Maintenance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.in_maintenance }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-gray-400 transition-colors" @click="setFilter('Draft')">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Draft</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.draft }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search asset ID, name, item, location..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="debouncedFetch" />
        </div>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          @change="fetchAssets">
          <option value="">All Statuses</option>
          <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="filterCategory" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          @change="fetchAssets">
          <option value="">All Categories</option>
          <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="filterLocation" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          @change="fetchAssets">
          <option value="">All Locations</option>
          <option v-for="l in locationOptions" :key="l" :value="l">{{ l }}</option>
        </select>
        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
      </div>
    </div>

    <!-- Asset Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Asset Records</h3>
        <p class="text-xs text-gray-400">Showing {{ assets.length }} of {{ totalAssets }} assets</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="px-6 py-12 text-center">
        <p class="text-xs text-gray-400">Loading assets...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="assets.length === 0" class="px-6 py-12 text-center">
        <p class="text-sm text-gray-500">No assets found.</p>
      </div>

      <!-- Table -->
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Asset ID</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Asset Name</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Category</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Location</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Department</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Purchase Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in assets" :key="a.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ a.name }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ a.asset_name }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.asset_category || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.location || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.department || '—' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ formatDate(a.purchase_date) }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="assetStatusClass(a.status || (a.docstatus === 0 ? 'Draft' : ''))">
                {{ a.status || (a.docstatus === 0 ? 'Draft' : '—') }}
              </span>
            </td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push(`/assets-mgmt/asset/${a.name}`)">View</button>
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
const filterCategory = ref('')
const filterLocation = ref('')
const currentPage = ref(1)
const perPage = 25
const loading = ref(false)
const assets = ref([])
const totalAssets = ref(0)
const totalPages = ref(1)

const categoryOptions = ref([])
const locationOptions = ref([])
const statusOptions = ref([])

const dashboard = ref({
  total: 0,
  submitted: 0,
  in_maintenance: 0,
  scrapped: 0,
  draft: 0,
})

// Dashboard stats
createResource({
  url: 'rhohotel.rhocom_hotel.api.assets.get_asset_dashboard',
  auto: true,
  onSuccess(data) { dashboard.value = data }
})

// Filter options
createResource({ url: 'rhohotel.rhocom_hotel.api.assets.get_asset_categories', auto: true, onSuccess(d) { categoryOptions.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.assets.get_asset_locations', auto: true, onSuccess(d) { locationOptions.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.assets.get_asset_statuses', auto: true, onSuccess(d) { statusOptions.value = d } })

function fetchAssets() {
  loading.value = true
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.assets.get_asset_list',
    params: {
      search: search.value || null,
      filter_status: filterStatus.value || null,
      filter_category: filterCategory.value || null,
      filter_location: filterLocation.value || null,
      page: currentPage.value,
      page_size: perPage,
    },
    onSuccess(data) {
      assets.value = data.assets
      totalAssets.value = data.total
      totalPages.value = data.total_pages
      loading.value = false
    },
    onError() { loading.value = false }
  })
  resource.fetch()
}

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchAssets()
  }, 300)
}

function setFilter(status) {
  filterStatus.value = status
  currentPage.value = 1
  fetchAssets()
}

function resetFilters() {
  search.value = ''
  filterStatus.value = ''
  filterCategory.value = ''
  filterLocation.value = ''
  currentPage.value = 1
  fetchAssets()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchAssets()
}

const displayPages = computed(() => {
  const pages = []
  const max = Math.min(totalPages.value, 7)
  for (let i = 1; i <= max; i++) pages.push(i)
  return pages
})

function assetStatusClass(s) {
  return {
    'Draft':                'bg-gray-100 text-gray-500',
    'Submitted':            'bg-green-50 text-green-600',
    'Partially Depreciated':'bg-blue-50 text-blue-600',
    'Fully Depreciated':    'bg-blue-100 text-blue-700',
    'Sold':                 'bg-purple-50 text-purple-600',
    'Scrapped':             'bg-red-50 text-red-500',
    'In Maintenance':       'bg-yellow-50 text-yellow-600',
    'Out of Order':         'bg-red-100 text-red-600',
    'Capitalized':          'bg-indigo-50 text-indigo-600',
  }[s] || 'bg-gray-100 text-gray-500'
}

function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => {
  fetchAssets()
})
</script>