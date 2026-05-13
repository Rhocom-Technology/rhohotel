<template>
  <div class="space-y-5">
    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Housekeeping / Task List</p>
      <h1 class="text-2xl font-bold text-gray-900">Housekeeping List</h1>
      <p class="text-xs text-gray-400 mt-1">Track room cleaning tasks, attendant assignments, and cleaning progress from a single list view.</p>
    </div>

    <!-- Stats Cards (3 per row from dashboard) -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;" v-if="dashboardData.data">
      <div class="rounded-xl px-5 py-4 bg-blue-50 border border-blue-200">
        <p class="text-xs text-blue-600 mb-2">Pending</p>
        <p class="text-2xl font-bold text-blue-900">{{ dashboardData.data.statistics.by_status.Pending || 0 }}</p>
      </div>
      <div class="rounded-xl px-5 py-4 bg-purple-50 border border-purple-200">
        <p class="text-xs text-purple-600 mb-2">Assigned</p>
        <p class="text-2xl font-bold text-purple-900">{{ dashboardData.data.statistics.by_status.Assigned || 0 }}</p>
      </div>
      <div class="rounded-xl px-5 py-4 bg-yellow-50 border border-yellow-200">
        <p class="text-xs text-yellow-600 mb-2">In Progress</p>
        <p class="text-2xl font-bold text-yellow-900">{{ dashboardData.data.statistics.by_status["In Progress"] || 0 }}</p>
      </div>
      <div class="rounded-xl px-5 py-4 bg-green-50 border border-green-200">
        <p class="text-xs text-green-600 mb-2">Completed</p>
        <p class="text-2xl font-bold text-green-900">{{ dashboardData.data.statistics.by_status.Completed || 0 }}</p>
      </div>
      <div class="rounded-xl px-5 py-4 bg-orange-50 border border-orange-200">
        <p class="text-xs text-orange-600 mb-2">Approved</p>
        <p class="text-2xl font-bold text-orange-900">{{ dashboardData.data.statistics.by_status.Approved || 0 }}</p>
      </div>
      <div class="rounded-xl px-5 py-4 bg-gray-50 border border-gray-200">
        <p class="text-xs text-gray-600 mb-2">On Hold</p>
        <p class="text-2xl font-bold text-gray-900">{{ dashboardData.data.statistics.by_status["On Hold"] || 0 }}</p>
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
            <option value="">All Types</option>
            <option value="Checkout Cleaning">Checkout Cleaning</option>
            <option value="Deep Cleaning">Deep Cleaning</option>
            <option value="Turndown Service">Turndown Service</option>
            <option value="Guest Request">Guest Request</option>
            <option value="Emergency Cleaning">Emergency Cleaning</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Approved">Approved</option>
            <option value="Assigned">Assigned</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="On Hold">On Hold</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Priority</p>
          <select v-model="filterPriority" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Urgent">Urgent</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Attendant</p>
          <select v-model="filterAttendant" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Attendants</option>
            <option v-for="emp in employees.data" :key="emp.name" :value="emp.name">
              {{ emp.employee_name || emp.name }}
            </option>
          </select>
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button @click="createNewTask" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Create Task</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Housekeeping Tasks</h3>
        <p class="text-xs text-gray-400" v-if="tasks.data">
          Showing {{ ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, filteredList.length) }} of {{ filteredList.length }} tasks
        </p>
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
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Start Time</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="task in paginatedList" :key="task.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="goToTask(task.name)">
              <td class="px-6 py-4">
                <p class="text-xs font-bold text-gray-900">{{ task.room || 'N/A' }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-700">{{ task.task_type || 'N/A' }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ getEmployeeName(task.employee) || 'Unassigned' }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="priorityClass(task.priority)">
                  {{ task.priority || 'Medium' }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(task.status)">
                  {{ task.status || 'Pending' }}
                </span>
              </td>
              <td class="px-4 py-4 text-xs text-gray-500">{{ formatDate(task.start_time) }}</td>
              <td class="px-4 py-4">
                <button @click.stop="goToTask(task.name)"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100">
                  Open
                </button>
              </td>
            </tr>
            <tr v-if="filteredList.length === 0">
              <td colspan="7" class="text-center py-8 text-gray-400 text-xs">No tasks found</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <p class="text-xs text-gray-400">Rows per page:</p>
          <select v-model="pageSize" @change="page = 1" class="text-xs border border-gray-200 rounded-lg px-2 py-1">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button @click="page = 1" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            First
          </button>
          <button @click="page--" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Previous
          </button>
          <span class="text-xs text-gray-600">
            Page {{ page }} of {{ totalPages }}
          </span>
          <button @click="page++" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Next
          </button>
          <button @click="page = totalPages" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            Last
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()

// Search and filters
const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const filterAttendant = ref('')
const page = ref(1)
const pageSize = ref(10)

// Fetch dashboard data for stats
const dashboardData = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_dashboard',
  cache: ['housekeeping_dashboard_stats'],
  auto: true,
  onError: (error) => {
    console.error('Error fetching dashboard:', error)
  }
})

// Fetch tasks
const tasks = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_task_details',
  auto: true,
  onError: (error) => {
    console.error('Error fetching tasks:', error)
  }
})

// Fetch employees for dropdown
const employees = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_employees',
  auto: true,
  onError: (error) => {
    console.error('Error fetching employees:', error)
  }
})

// Get employee name helper
const getEmployeeName = (employeeId) => {
  if (!employeeId || !employees.data) return null
  const emp = employees.data.find(e => e.name === employeeId)
  return emp ? emp.employee_name : employeeId
}

// Filtered list
const filteredList = computed(() => {
  let list = tasks.data || []
  
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t => 
      (t.room && t.room.toLowerCase().includes(q)) ||
      (t.task_type && t.task_type.toLowerCase().includes(q)) ||
      (t.employee && getEmployeeName(t.employee)?.toLowerCase().includes(q))
    )
  }
  if (filterType.value) list = list.filter(t => t.task_type === filterType.value)
  if (filterStatus.value) list = list.filter(t => t.status === filterStatus.value)
  if (filterPriority.value) list = list.filter(t => t.priority === filterPriority.value)
  if (filterAttendant.value) list = list.filter(t => t.employee === filterAttendant.value)
  
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize.value)))
const paginatedList = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// Reset page when filters change
watch([search, filterType, filterStatus, filterPriority, filterAttendant], () => {
  page.value = 1
})

// Watch pageSize to reset page
watch(pageSize, () => {
  page.value = 1
})

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterStatus.value = ''
  filterPriority.value = ''
  filterAttendant.value = ''
  page.value = 1
}

function createNewTask() {
  router.push('/housekeeping/task/new')
}

function goToTask(taskName) {
  router.push(`/housekeeping/task/${taskName}`)
}

function formatDate(dateString) {
  if (!dateString) return 'Not scheduled'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function priorityClass(priority) {
  const classes = {
    'Urgent': 'bg-red-100 text-red-500',
    'High': 'bg-orange-100 text-orange-500',
    'Medium': 'bg-yellow-100 text-yellow-600',
    'Low': 'bg-green-100 text-green-600'
  }
  return classes[priority] || 'bg-gray-100 text-gray-500'
}

function statusClass(status) {
  const classes = {
    'Pending': 'bg-yellow-100 text-yellow-600',
    'Approved': 'bg-blue-100 text-blue-600',
    'Assigned': 'bg-purple-100 text-purple-600',
    'In Progress': 'bg-blue-100 text-blue-600',
    'Completed': 'bg-green-100 text-green-600',
    'On Hold': 'bg-gray-100 text-gray-500',
    'Cancelled': 'bg-red-100 text-red-500'
  }
  return classes[status] || 'bg-gray-100 text-gray-500'
}
</script>