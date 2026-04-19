<template>
  <div class="space-y-4">

    <!-- Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Request Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track open, assigned, escalated, and resolved requests with quick access to view, route, and convert requests into maintenance tasks.</p>
      </div>
      <div class="flex items-center gap-3">
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Export Requests</button>
        <button @click="router.push('/maintenance/new-request')" class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">New Request</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">29</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Urgent Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Urgent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">8</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Assigned to Team</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">In Queue</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Resolved This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Closed</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">18</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="relative" style="flex:1;min-width:180px;">
          <input v-model="search" type="text" placeholder="Search request ID, room, asset, requester..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Types</option>
          <option value="Corrective">Corrective</option>
          <option value="Inspection">Inspection</option>
          <option value="Preventive">Preventive</option>
        </select>
        <select v-model="filterPriority" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Priorities</option>
          <option value="Urgent">Urgent</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
        </select>
        <select v-model="filterStatus" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Statuses</option>
          <option value="Open">Open</option>
          <option value="Assigned">Assigned</option>
          <option value="Review">Review</option>
          <option value="Converted">Converted</option>
          <option value="Escalated">Escalated</option>
          <option value="Closed">Closed</option>
        </select>
        <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
        <button @click="filterPriority = 'Urgent'" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Show Urgent Requests</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Request Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ paginatedList.length }} of {{ filteredList.length }} requests</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Request ID</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Issue / Target</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Requester</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Department</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Type</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Submitted</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in paginatedList" :key="item.id"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="router.push({ name: 'SavedMaintenanceRequest', params: { id: item.id } })">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ item.id }}</td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.issue }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.target }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.requester }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.department }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.type }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(item.priority)">{{ item.priority }}</span>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.submitted }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border" :class="statusClass(item.status)">{{ item.status }}</span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="router.push({ name: 'SavedMaintenanceRequest', params: { id: item.id } })"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button v-for="p in 3" :key="p" @click="page = p"
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
const filterStatus = ref('')
const page = ref(1)
const pageSize = 25

const requests = [
  { id: 'REQ-000184', issue: 'AC not cooling - Room 305', target: 'Room target • guest impacted', requester: 'Mary Bello', department: 'Housekeeping', type: 'Corrective', priority: 'Urgent', submitted: '18 Apr 2026', status: 'Open' },
  { id: 'REQ-000183', issue: 'Laundry dryer vibration issue', target: 'Asset target • AST-003761', requester: 'John Ude', department: 'Laundry', type: 'Corrective', priority: 'High', submitted: '18 Apr 2026', status: 'Assigned' },
  { id: 'REQ-000182', issue: 'Generator battery warning alert', target: 'Power House location', requester: 'Segun Ade', department: 'Engineering', type: 'Inspection', priority: 'Urgent', submitted: '17 Apr 2026', status: 'Review' },
  { id: 'REQ-000181', issue: 'Smart TV no signal - Room 214', target: 'Room target • guest waiting', requester: 'Rita James', department: 'Front Desk', type: 'Corrective', priority: 'High', submitted: '17 Apr 2026', status: 'Converted' },
  { id: 'REQ-000180', issue: 'Water leak behind boiler room', target: 'Location target • possible plumbing issue', requester: 'Tunde Obi', department: 'Security', type: 'Corrective', priority: 'Urgent', submitted: '16 Apr 2026', status: 'Escalated' },
  { id: 'REQ-000179', issue: 'Minibar not cooling - Room 112', target: 'Asset target • guest complaint resolved', requester: 'Blessing Eze', department: 'Housekeeping', type: 'Corrective', priority: 'Medium', submitted: '15 Apr 2026', status: 'Closed' },
]

const filteredList = computed(() => {
  let list = requests
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r => r.id.toLowerCase().includes(q) || r.issue.toLowerCase().includes(q) || r.requester.toLowerCase().includes(q))
  }
  if (filterType.value) list = list.filter(r => r.type === filterType.value)
  if (filterPriority.value) list = list.filter(r => r.priority === filterPriority.value)
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterPriority.value = ''
  filterStatus.value = ''
  page.value = 1
}

function priorityClass(p) {
  return {
    'Urgent': 'bg-red-100 text-red-500',
    'High': 'bg-yellow-100 text-yellow-600',
    'Medium': 'bg-blue-50 text-blue-500',
  }[p] || 'bg-gray-100 text-gray-500'
}

function statusClass(s) {
  return {
    'Open': 'bg-blue-50 text-blue-600 border-blue-200',
    'Assigned': 'bg-yellow-50 text-yellow-600 border-yellow-200',
    'Review': 'bg-gray-50 text-gray-600 border-gray-200',
    'Converted': 'bg-purple-50 text-purple-600 border-purple-200',
    'Escalated': 'bg-orange-50 text-orange-600 border-orange-200',
    'Closed': 'bg-green-50 text-green-600 border-green-200',
  }[s] || 'bg-gray-50 text-gray-500 border-gray-200'
}
</script>