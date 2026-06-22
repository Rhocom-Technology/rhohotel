<template>
  <div class="space-y-5">

    <!-- Loading / Error States -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl px-6 py-10 text-center">
      <p class="text-sm font-semibold text-red-500 mb-2">{{ loadError }}</p>
      <button @click="loadRooms" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Retry</button>
    </div>

    <template v-else>

    <!-- Breadcrumb -->
    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">Rooms • room inventory and occupancy view</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Room Inventory Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ rooms.length }} rooms • {{ occupiedCount }} occupied • {{ vacantCount }} vacant • {{ unavailableCount }} out of service
        </p>
      </div>
      <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
        <button @click="loadRooms" class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">Refresh</button>
        <button class="w-full px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto">Export List</button>
        <button class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors sm:w-auto"
          @click="$router.push('/rooms/new')">Add New Room</button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Rooms</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Inventory</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ rooms.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Occupied</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ occupiedCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Vacant</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-500 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ vacantCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Out of Service</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ unavailableCount }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div class="w-full sm:min-w-[180px]">
          <p class="text-xs text-gray-500 mb-1.5">Search room</p>
          <input v-model="search" type="text" placeholder="Room no., type, floor..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div class="w-full sm:min-w-[140px]">
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select v-model="filterType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Types</option>
            <option v-for="rt in roomTypeOptions" :key="rt" :value="rt">{{ rt }}</option>
          </select>
        </div>
        <div class="w-full sm:min-w-[140px]">
          <p class="text-xs text-gray-500 mb-1.5">Occupancy</p>
          <select v-model="filterOccupancy" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Rooms</option>
            <option>Occupied</option>
            <option>Vacant</option>
            <option>Unavailable</option>
          </select>
        </div>
        <div class="w-full sm:min-w-[140px]">
          <p class="text-xs text-gray-500 mb-1.5">Floor</p>
          <select v-model="filterFloor" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Floors</option>
            <option v-for="f in floorOptions" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
        <button @click="search='';filterType='';filterOccupancy='';filterFloor='';currentPage=1"
          class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">Reset</button>
        <button class="w-full px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors sm:w-auto">Apply Filter</button>
      </div>
    </div>

    <!-- Room Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-4 py-4 border-b border-gray-100 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h3 class="text-sm font-bold text-gray-900">Room Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} rooms</p>
      </div>
      <div class="overflow-x-auto">
      <table class="w-full min-w-[820px]">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Room No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Floor</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Rate</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Occupancy</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Current Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in paged" :key="r.no" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.no }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.floor }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ formatCurrency(r.rate) }}</td>
            <td class="px-4 py-4 text-xs font-semibold" :class="occupancyClass(r.occupancy)">{{ r.occupancy }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.guest || '—' }}</td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push('/rooms/' + r.no)">View</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <div class="px-4 py-4 border-t border-gray-100 flex flex-col gap-3 bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex flex-wrap items-center gap-1">
          <button v-for="p in visiblePages" :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="p === currentPage ? 'bg-blue-600 text-white font-semibold' : p === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages && currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const search = ref('')
const filterType = ref('')
const filterOccupancy = ref('')
const filterFloor = ref('')
const currentPage = ref(1)
const loading = ref(true)
const loadError = ref('')
const perPage = 25

const rooms = ref([])
const roomTypeOptions = ref([])
const floorOptions = ref([])

onMounted(loadRooms)

async function loadRooms() {
  loading.value = true
  loadError.value = ''
  try {
    const msg = await callMethod('rhohotel.rhocom_hotel.api.room.get_room_inventory') || {}
    rooms.value = msg.rooms || []
    roomTypeOptions.value = msg.room_types || []
    floorOptions.value = msg.floors || []
  } catch (e) {
    loadError.value = 'Network error — please check connection.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const occupiedCount = computed(() => rooms.value.filter(r => r.occupancy === 'Occupied').length)
const vacantCount = computed(() => rooms.value.filter(r => r.occupancy === 'Vacant').length)
const unavailableCount = computed(() => rooms.value.filter(r => r.occupancy === 'Unavailable').length)

function formatCurrency(val) {
  if (!val) return '₦0.00'
  return `₦${Number(val).toLocaleString('en-NG', { minimumFractionDigits: 0 })}`
}

const filtered = computed(() => {
  let list = rooms.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r => r.no.includes(q) || r.type.toLowerCase().includes(q))
  }
  if (filterType.value) list = list.filter(r => r.type === filterType.value)
  if (filterOccupancy.value) list = list.filter(r => r.occupancy === filterOccupancy.value)
  if (filterFloor.value) list = list.filter(r => r.floor === filterFloor.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total-4, total-3, total-2, total-1, total]
  return [1, '...', cur-1, cur, cur+1, '...', total]
})

function occupancyClass(o) {
  return {
    'Occupied':    'text-green-600',
    'Vacant':      'text-blue-500',
    'Unavailable': 'text-red-500',
  }[o] || 'text-gray-500'
}
</script>
