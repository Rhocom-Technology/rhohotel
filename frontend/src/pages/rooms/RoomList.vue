<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Front desk • room inventory and occupancy view</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Room Inventory Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">124 rooms • 41 occupied • 58 vacant clean • 12 vacant dirty • 7 out of service</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/rooms/new')">Add New Room</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Rooms</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Inventory</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">124</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Occupied</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">41</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Vacant</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-500 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">70</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Out of Service</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">7</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search room</p>
          <input v-model="search" type="text" placeholder="Room no., type, floor..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select v-model="filterType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Types</option>
            <option>Standard Room</option>
            <option>Deluxe Room</option>
            <option>Executive Suite</option>
            <option>Standard Twin</option>
            <option>Junior Suite</option>
            <option>Presidential Suite</option>
          </select>
        </div>
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">Occupancy</p>
          <select v-model="filterOccupancy" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Rooms</option>
            <option>Occupied</option>
            <option>Vacant</option>
            <option>Unavailable</option>
          </select>
        </div>
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">Floor</p>
          <select v-model="filterFloor" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Floors</option>
            <option v-for="f in 6" :key="f" :value="String(f)">Floor {{ f }}</option>
          </select>
        </div>
        <button @click="search='';filterType='';filterOccupancy='';filterFloor='';currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply Filter</button>
      </div>
    </div>

    <!-- Room Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Room Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} rooms</p>
      </div>
      <table class="w-full">
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
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ r.rate }}</td>
            <td class="px-4 py-4 text-xs font-semibold" :class="occupancyClass(r.occupancy)">{{ r.occupancy }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.guest || '—' }}</td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push('/rooms/' + r.no)">View</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
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

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const search = ref('')
const filterType = ref('')
const filterOccupancy = ref('')
const filterFloor = ref('')
const currentPage = ref(1)
const perPage = 25

const rooms = [
  { no: '101', type: 'Standard Room',     floor: '1', rate: '₦42,000',  occupancy: 'Occupied',     guest: 'Sarah Johnson' },
  { no: '102', type: 'Standard Room',     floor: '1', rate: '₦42,000',  occupancy: 'Vacant',       guest: '' },
  { no: '103', type: 'Standard Room',     floor: '1', rate: '₦42,000',  occupancy: 'Vacant',       guest: '' },
  { no: '104', type: 'Deluxe Room',       floor: '1', rate: '₦68,000',  occupancy: 'Occupied',     guest: 'Emeka Adeyemi' },
  { no: '105', type: 'Deluxe Room',       floor: '1', rate: '₦68,000',  occupancy: 'Vacant',       guest: '' },
  { no: '106', type: 'Standard Room',     floor: '1', rate: '₦42,000',  occupancy: 'Vacant',       guest: '' },
  { no: '201', type: 'Executive Suite',   floor: '2', rate: '₦120,000', occupancy: 'Occupied',     guest: 'Daniel Ayo' },
  { no: '202', type: 'Executive Suite',   floor: '2', rate: '₦120,000', occupancy: 'Vacant',       guest: '' },
  { no: '214', type: 'Deluxe Room',       floor: '2', rate: '₦68,000',  occupancy: 'Vacant',       guest: '' },
  { no: '215', type: 'Deluxe Room',       floor: '2', rate: '₦68,000',  occupancy: 'Occupied',     guest: 'Fatima Ahmed' },
  { no: '305', type: 'Executive Suite',   floor: '3', rate: '₦120,000', occupancy: 'Occupied',     guest: 'Michael Duke' },
  { no: '306', type: 'Executive Suite',   floor: '3', rate: '₦120,000', occupancy: 'Vacant',       guest: '' },
  { no: '402', type: 'Standard Twin',     floor: '4', rate: '₦48,000',  occupancy: 'Vacant',       guest: '' },
  { no: '403', type: 'Standard Twin',     floor: '4', rate: '₦48,000',  occupancy: 'Occupied',     guest: 'Ngozi Cole' },
  { no: '404', type: 'Standard Twin',     floor: '4', rate: '₦48,000',  occupancy: 'Vacant',       guest: '' },
  { no: '501', type: 'Junior Suite',      floor: '5', rate: '₦95,000',  occupancy: 'Vacant',       guest: '' },
  { no: '502', type: 'Junior Suite',      floor: '5', rate: '₦95,000',  occupancy: 'Occupied',     guest: 'Grace Kelvin' },
  { no: '511', type: 'Junior Suite',      floor: '5', rate: '₦95,000',  occupancy: 'Vacant',       guest: '' },
  { no: '601', type: 'Presidential Suite',floor: '6', rate: '₦250,000', occupancy: 'Vacant',       guest: '' },
  { no: '603', type: 'Presidential Suite',floor: '6', rate: '₦250,000', occupancy: 'Unavailable',  guest: '' },
]

const filtered = computed(() => {
  let list = rooms
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