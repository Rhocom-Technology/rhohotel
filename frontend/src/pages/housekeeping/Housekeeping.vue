<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Housekeeping / Task List</p>
      <h1 class="text-2xl font-bold text-gray-900">Housekeeping List</h1>
      <p class="text-xs text-gray-400 mt-1">Track room cleaning tasks, attendant assignments, inspection progress, and room readiness from a single list view.</p>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Tasks</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">63</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Cleaning In Progress</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Ongoing</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Awaiting Inspection</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">QA</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">11</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Ready Rooms</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Released</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">64</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search room / task</p>
          <input v-model="search" type="text" placeholder="Room no., attendant, task..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
          <select v-model="filterType" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Tasks</option>
            <option value="Checkout Cleaning">Checkout Cleaning</option>
            <option value="Daily Cleaning">Daily Cleaning</option>
            <option value="Inspection Review">Inspection Review</option>
            <option value="Linen Refill">Linen Refill</option>
            <option value="Guest Request">Guest Request</option>
            <option value="Maintenance Hold">Maintenance Hold</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="In Progress">In Progress</option>
            <option value="Inspection">Inspection</option>
            <option value="Released">Released</option>
            <option value="Suspended">Suspended</option>
            <option value="Queued">Queued</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Attendant</p>
          <select v-model="filterAttendant" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Attendants</option>
            <option value="Blessing Okoro">Blessing Okoro</option>
            <option value="Ifeoma Nnadi">Ifeoma Nnadi</option>
            <option value="Boma Eze">Boma Eze</option>
            <option value="Supervisor Desk">Supervisor Desk</option>
            <option value="Engineering Team">Engineering Team</option>
            <option value="Store Control">Store Control</option>
          </select>
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button @click="router.push('/housekeeping/task/new')" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Create Task</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Housekeeping Tasks</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ paginatedList.length }} of {{ filteredList.length }} room tasks</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Room</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Task Type</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Attendant</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Priority</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Updated</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in paginatedList" :key="item.id"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="router.push({ name: 'HousekeepingTask', params: { id: item.id } })">
              <td class="px-6 py-4">
                <p class="text-xs font-bold text-gray-900">{{ item.room }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.roomStatus }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-700">{{ item.taskType }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.attendant }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(item.priority)">{{ item.priority }}</span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(item.status)">{{ item.status }}</span>
              </td>
              <td class="px-4 py-4 text-xs text-gray-500">{{ item.updated }}</td>
              <td class="px-4 py-4">
                <button @click.stop="router.push({ name: 'HousekeepingTask', params: { id: item.id } })"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100">Open</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button v-for="p in Math.min(totalPages, 5)" :key="p" @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'">{{ p }}</button>
            <span v-if="totalPages > 5" class="text-xs text-gray-400">... {{ totalPages }}</span>
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
const filterStatus = ref('')
const filterAttendant = ref('')
const page = ref(1)
const pageSize = 10

const tasks = [
  { id: 'HKT-001', room: '402', roomStatus: 'VIP Arrival', taskType: 'Checkout Cleaning', attendant: 'Blessing Okoro', priority: 'Urgent', status: 'In Progress', updated: '10:12 AM' },
  { id: 'HKT-002', room: '214', roomStatus: 'Vacant', taskType: 'Inspection Review', attendant: 'Supervisor Desk', priority: 'Medium', status: 'Inspection', updated: '10:25 AM' },
  { id: 'HKT-003', room: '118', roomStatus: 'Occupied', taskType: 'Daily Cleaning', attendant: 'Ifeoma Nnadi', priority: 'Low', status: 'Released', updated: '10:31 AM' },
  { id: 'HKT-004', room: '511', roomStatus: 'Blocked', taskType: 'Maintenance Hold', attendant: 'Engineering Team', priority: 'Blocked', status: 'Suspended', updated: '10:44 AM' },
  { id: 'HKT-005', room: '305', roomStatus: 'Occupied', taskType: 'Linen Refill', attendant: 'Boma Eze', priority: 'Medium', status: 'In Progress', updated: '10:53 AM' },
  { id: 'HKT-006', room: '409', roomStatus: 'Due Out', taskType: 'Checkout Cleaning', attendant: 'Blessing Okoro', priority: 'High', status: 'Queued', updated: '11:08 AM' },
  { id: 'HKT-007', room: '227', roomStatus: 'Vacant', taskType: 'Guest Request', attendant: 'Ifeoma Nnadi', priority: 'Medium', status: 'In Progress', updated: '11:16 AM' },
  { id: 'HKT-008', room: '118', roomStatus: 'Occupied', taskType: 'Daily Cleaning', attendant: 'Store Control', priority: 'Low', status: 'Released', updated: '11:28 AM' },
  { id: 'HKT-009', room: '310', roomStatus: 'Vacant', taskType: 'Checkout Cleaning', attendant: 'Boma Eze', priority: 'High', status: 'In Progress', updated: '11:35 AM' },
  { id: 'HKT-010', room: '502', roomStatus: 'Occupied', taskType: 'Daily Cleaning', attendant: 'Ifeoma Nnadi', priority: 'Low', status: 'Queued', updated: '11:42 AM' },
]

const filteredList = computed(() => {
  let list = tasks
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t => t.room.includes(q) || t.taskType.toLowerCase().includes(q) || t.attendant.toLowerCase().includes(q))
  }
  if (filterType.value) list = list.filter(t => t.taskType === filterType.value)
  if (filterStatus.value) list = list.filter(t => t.status === filterStatus.value)
  if (filterAttendant.value) list = list.filter(t => t.attendant === filterAttendant.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterStatus.value = ''
  filterAttendant.value = ''
  page.value = 1
}

function priorityClass(p) {
  return {
    'Urgent': 'bg-red-100 text-red-500',
    'High': 'bg-orange-100 text-orange-500',
    'Medium': 'bg-yellow-100 text-yellow-600',
    'Low': 'bg-green-100 text-green-600',
    'Blocked': 'bg-purple-100 text-purple-600',
  }[p] || 'bg-gray-100 text-gray-500'
}

function statusClass(s) {
  return {
    'In Progress': 'bg-blue-100 text-blue-600',
    'Inspection': 'bg-purple-100 text-purple-600',
    'Released': 'bg-green-100 text-green-600',
    'Suspended': 'bg-gray-100 text-gray-500',
    'Queued': 'bg-yellow-100 text-yellow-600',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>