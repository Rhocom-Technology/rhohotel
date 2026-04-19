<template>
  <div class="space-y-4">

    <!-- Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Maintenance Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Manage corrective, preventive, urgent, and scheduled tasks with quick access to technicians, service history, and reporting.</p>
      </div>
      <div class="flex items-center gap-3">
        <router-link to="/maintenance/technicians">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Technicians</button>
        </router-link>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Export Tasks</button>
        <router-link to="/maintenance/new-task">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">New Maintenance</button>
        </router-link>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Tasks</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">38</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Maintenance Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Urgent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">12</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Scheduled Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Due</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">9</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Closed This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">41</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="relative" style="flex:1;min-width:180px;">
          <input v-model="search" type="text" placeholder="Search task ID, asset, location..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Types</option>
          <option value="Corrective">Corrective</option>
          <option value="Preventive">Preventive</option>
          <option value="Inspection">Inspection</option>
        </select>
        <select v-model="filterPriority" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Priorities</option>
          <option value="Urgent">Urgent</option>
          <option value="Due">Due</option>
          <option value="Normal">Normal</option>
        </select>
        <select v-model="filterTech" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Technicians</option>
          <option value="Engr. Paul">Engr. Paul</option>
          <option value="Tech Team B">Tech Team B</option>
          <option value="Engr. Musa">Engr. Musa</option>
        </select>
        <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
        <button @click="filterPriority = 'Urgent'" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Show Urgent Tasks Only</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ paginatedList.length }} of {{ filteredList.length }} tasks</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Task ID</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Asset / Issue</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Type</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Location</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Technician</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Due Date</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in paginatedList" :key="item.id" class="hover:bg-gray-50 transition-colors cursor-pointer" @click="openTask(item)">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ item.id }}</td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.asset }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.subtitle }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.type }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.location }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.technician }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.dueDate }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(item.priority)">{{ item.priority }}</span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border" :class="statusClass(item.status)">{{ item.status }}</span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="openTask(item)" class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button v-for="p in Math.min(totalPages, 4)" :key="p" @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'">{{ p }}</button>
          </div>
          <button @click="page = Math.min(page + 1, totalPages)" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const search = ref('')
const filterType = ref('')
const filterPriority = ref('')
const filterTech = ref('')
const page = ref(1)
const pageSize = 25

const tasks = [
  { id: 'MNT-000219', asset: 'Laundry Dryer motor failure', subtitle: 'Corrective repair', type: 'Corrective', location: 'Laundry Room', technician: 'Engr. Paul', dueDate: '18 Apr 2026', priority: 'Urgent', status: 'Assigned' },
  { id: 'MNT-000218', asset: 'Generator battery bank inspection', subtitle: 'Preventive service', type: 'Preventive', location: 'Power House', technician: 'Tech Team B', dueDate: '18 Apr 2026', priority: 'Due', status: 'Scheduled' },
  { id: 'MNT-000217', asset: 'Room 305 Smart TV firmware update', subtitle: 'Electronics service', type: 'Corrective', location: 'Room 305', technician: 'Engr. Musa', dueDate: '17 Apr 2026', priority: 'Normal', status: 'Closed' },
  { id: 'MNT-000216', asset: 'AC repeat issue on Room 214', subtitle: 'Cooling failure escalated', type: 'Corrective', location: 'Room 214', technician: 'Senior HVAC Team', dueDate: '18 Apr 2026', priority: 'Urgent', status: 'Escalated' },
  { id: 'MNT-000215', asset: 'Boiler vendor inspection visit', subtitle: 'External service appointment', type: 'Inspection', location: 'Boiler Room', technician: 'Vendor - HeatPro', dueDate: '19 Apr 2026', priority: 'Normal', status: 'Scheduled' },
  { id: 'MNT-000214', asset: 'Water booster pump service', subtitle: 'Routine pressure maintenance', type: 'Preventive', location: 'Pump House', technician: 'Tech Team A', dueDate: '20 Apr 2026', priority: 'Normal', status: 'Assigned' },
  { id: 'MNT-000213', asset: 'Elevator B annual inspection', subtitle: 'Safety compliance check', type: 'Inspection', location: 'Main Block', technician: 'Engr. Paul', dueDate: '21 Apr 2026', priority: 'Due', status: 'Scheduled' },
  { id: 'MNT-000212', asset: 'Swimming pool pump failure', subtitle: 'Water circulation issue', type: 'Corrective', location: 'Pool Area', technician: 'Tech Team A', dueDate: '18 Apr 2026', priority: 'Urgent', status: 'In Progress' },
]

const filteredList = computed(() => {
  let list = tasks
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r => r.id.toLowerCase().includes(q) || r.asset.toLowerCase().includes(q) || r.location.toLowerCase().includes(q))
  }
  if (filterType.value) list = list.filter(r => r.type === filterType.value)
  if (filterPriority.value) list = list.filter(r => r.priority === filterPriority.value)
  if (filterTech.value) list = list.filter(r => r.technician === filterTech.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterPriority.value = ''
  filterTech.value = ''
  page.value = 1
}

function priorityClass(p) {
  return { 'Urgent': 'bg-red-100 text-red-500', 'Due': 'bg-yellow-100 text-yellow-600', 'Normal': 'bg-blue-50 text-blue-500' }[p] || 'bg-gray-100 text-gray-500'
}

function statusClass(s) {
  return {
    'Assigned': 'bg-blue-50 text-blue-600 border-blue-200',
    'Scheduled': 'bg-gray-50 text-gray-600 border-gray-200',
    'Closed': 'bg-green-50 text-green-600 border-green-200',
    'Escalated': 'bg-yellow-50 text-yellow-600 border-yellow-200',
    'In Progress': 'bg-purple-50 text-purple-600 border-purple-200',
  }[s] || 'bg-gray-50 text-gray-500 border-gray-200'
}

function openTask(item) {
  router.push({ name: 'MaintenanceTask', params: { id: item.id } })
}
</script>