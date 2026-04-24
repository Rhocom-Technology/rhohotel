<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Operations • central asset register for rooms, facilities, and equipment</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Asset Register Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Search assets, track assignments, review service status, and access maintenance or warranty details from one page.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/maintenance/list')">Maintenance List</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Asset</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Assets</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">1,284</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Assigned Assets</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">846</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Under Maintenance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">38</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Warranty Expiring</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search asset tag, name, serial..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterCategory" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Categories</option>
          <option>Electronics</option>
          <option>Laundry</option>
          <option>Room Appliance</option>
          <option>Power</option>
          <option>Housekeeping</option>
        </select>
        <select v-model="filterLocation" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Locations</option>
          <option>Room 305</option>
          <option>Laundry Room</option>
          <option>Room 214</option>
          <option>Power House</option>
          <option>Store Room</option>
          <option>Archive</option>
        </select>
        <select v-model="filterCondition" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Conditions</option>
          <option>Excellent</option>
          <option>Good</option>
          <option>Fair</option>
          <option>Poor</option>
        </select>
        <button @click="search='';filterCategory='';filterLocation='';filterCondition='';showMaintenance=false;currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showMaintenance ? 'text-white bg-yellow-500 hover:bg-yellow-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showMaintenance = !showMaintenance">
          {{ showMaintenance ? 'Show All Assets' : 'Show Maintenance Assets' }}
        </button>
      </div>
    </div>

    <!-- Asset Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Asset Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} assets</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Asset Tag</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Asset Name</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Category</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Location</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Assigned To</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Condition</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Warranty</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in paged" :key="a.tag" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ a.tag }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ a.name }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.category }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.location }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.assignedTo }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.condition }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ a.warranty }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="assetStatusClass(a.status)">{{ a.status }}</span>
            </td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">View</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
          <button v-for="p in totalPages" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const search = ref('')
const filterCategory = ref('')
const filterLocation = ref('')
const filterCondition = ref('')
const showMaintenance = ref(false)
const currentPage = ref(1)
const perPage = 25

const assets = [
  { tag: 'AST-004821', name: 'Samsung Smart TV 55"', category: 'Electronics',    location: 'Room 305',    assignedTo: 'Executive Suite', condition: 'Good',      warranty: '12 Feb 2027', status: 'Active' },
  { tag: 'AST-003761', name: 'Industrial Laundry Dryer', category: 'Laundry',   location: 'Laundry Room',assignedTo: 'Ops Team',        condition: 'Fair',      warranty: '05 Sep 2026', status: 'Maintenance' },
  { tag: 'AST-002990', name: 'Kettle',                category: 'Room Appliance',location: 'Room 214',    assignedTo: 'Standard Room',   condition: 'Excellent', warranty: '18 Dec 2026', status: 'Active' },
  { tag: 'AST-001884', name: 'Generator Battery Bank', category: 'Power',       location: 'Power House', assignedTo: 'Engineering',     condition: 'Fair',      warranty: '30 Apr 2026', status: 'Alert' },
  { tag: 'AST-004118', name: 'Vacuum Cleaner Pro',    category: 'Housekeeping', location: 'Store Room',  assignedTo: 'Housekeeping',    condition: 'Good',      warranty: '22 Jan 2028', status: 'In Store' },
  { tag: 'AST-003176', name: 'Old Minibar Unit',      category: 'Room Appliance',location: 'Archive',    assignedTo: 'Retired',         condition: 'Poor',      warranty: 'Expired',     status: 'Retired' },
  { tag: 'AST-004510', name: 'Air Conditioner Split Unit', category: 'Electronics', location: 'Room 401', assignedTo: 'Presidential Suite', condition: 'Good',  warranty: '14 Mar 2028', status: 'Active' },
  { tag: 'AST-003902', name: 'Commercial Dishwasher', category: 'Laundry',      location: 'Kitchen',     assignedTo: 'F&B Team',        condition: 'Fair',      warranty: '08 Jun 2026', status: 'Maintenance' },
]

const filtered = computed(() => {
  let list = assets
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(a => a.tag.toLowerCase().includes(q) || a.name.toLowerCase().includes(q))
  }
  if (filterCategory.value) list = list.filter(a => a.category === filterCategory.value)
  if (filterLocation.value) list = list.filter(a => a.location === filterLocation.value)
  if (filterCondition.value) list = list.filter(a => a.condition === filterCondition.value)
  if (showMaintenance.value) list = list.filter(a => a.status === 'Maintenance')
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function assetStatusClass(s) {
  return {
    'Active':      'bg-green-50 text-green-600',
    'Maintenance': 'bg-yellow-50 text-yellow-600',
    'Alert':       'bg-red-50 text-red-500',
    'In Store':    'bg-blue-50 text-blue-600',
    'Retired':     'bg-gray-100 text-gray-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>