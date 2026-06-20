<template>
  <div class="space-y-5">
    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Housekeeping / Dashboard</p>
      <h1 class="text-2xl font-bold text-gray-900">Housekeeping Dashboard</h1>
      <p class="text-xs text-gray-400 mt-1">Monitor housekeeping tasks, attendant workload, and cleaning activity.</p>
    </div>

    <div v-if="dashboardError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
      <p class="text-xs text-red-600">{{ dashboardError }}</p>
    </div>

    <!-- Header Stats -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-bold text-gray-900">{{ formattedDate }}</h2>
        <div class="flex items-center gap-2">
          <button @click="refreshData" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Refresh
          </button>
          <router-link to="/housekeeping">
            <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
              All Tasks
            </button>
          </router-link>
        </div>
      </div>
      <p class="text-xs text-gray-400" v-if="dashboardData.data">
        Total Tasks: {{ dashboardData.data.statistics.total_tasks }} • 
        Active: {{ dashboardData.data.statistics.active_tasks }} • 
        Completion Rate: {{ dashboardData.data.statistics.completion_rate }}%
      </p>
    </div>

    <!-- Task Status Cards (3 per row) -->
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

    <!-- AI Dispatch Priority Plan -->
    <AIInsightPanel
      title="AI Dispatch Priority Plan"
      context-type="housekeeping_dispatch_summary"
      :context-data="housekeepingAiContext"
      :auto-load="false"
      panel-id="housekeeping-dashboard"
    />

    <!-- Main Grid -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;" v-if="dashboardData.data">
      <!-- Left Column -->
      <div class="space-y-4">
        
        <!-- High Priority Tasks -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">High Priority Tasks</h3>
          </div>
          <div class="p-4 space-y-2">
            <div v-for="task in dashboardData.data.priority_tasks.slice(0, 5)" :key="task.name"
              class="flex items-center justify-between bg-red-50 rounded-lg border border-red-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room {{ task.room }} • {{ task.task_type }}</p>
                <p class="text-xs text-gray-500">Status: {{ task.status }} • Priority: {{ task.priority }}</p>
              </div>
              <span class="px-2 py-1 text-xs font-semibold rounded-full" 
                :class="task.priority === 'Urgent' ? 'bg-red-200 text-red-700' : 'bg-orange-200 text-orange-700'">
                {{ task.priority }}
              </span>
            </div>
            <div v-if="dashboardData.data.priority_tasks.length === 0" class="text-center py-4 text-gray-400 text-xs">
              No high priority tasks
            </div>
          </div>
        </div>

        <!-- RECENT TASKS (with View buttons) -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Recent Tasks</h3>
          </div>
          <div class="p-4 space-y-2">
            <div v-for="task in dashboardData.data.recent_room_updates.slice(0, 5)" :key="task.name"
              class="rounded-xl px-4 py-3"
              :class="getTaskCardClass(task)">
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="flex items-center justify-between mb-1">
                    <p class="text-xs font-bold text-gray-900">Room {{ task.room }} • {{ getTaskDisplayName(task) }}</p>
                    <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                      :class="getBadgeClass(task)">
                      {{ getBadgeText(task) }}
                    </span>
                  </div>
                  <p class="text-xs text-gray-500 mt-1">{{ getTaskSubtitle(task) }}</p>
                </div>
                
              </div>
            </div>
            <div v-if="dashboardData.data.recent_room_updates.length === 0" class="text-center py-4 text-gray-400 text-xs">
              No recent tasks
            </div>
          </div>
        </div>

        <!-- ATTENDANT WORKLOAD (no View button, just summary text) -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Attendant Workload</h3>
          </div>
          <div class="p-4 space-y-3">
            <div v-for="attendant in dashboardData.data.attendants.slice(0, 5)" :key="attendant.employee"
  class="bg-gray-50 rounded-lg border border-gray-100 px-4 py-3">
  <div class="flex items-center justify-between">
    <p class="text-xs font-bold text-gray-900">{{ attendant.name }}</p>
    <router-link :to="`/housekeeping?employee=${attendant.employee}`">
      <button class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 whitespace-nowrap">
        View Tasks
      </button>
    </router-link>
  </div>
  <p class="text-xs text-gray-500 mt-1">{{ getAttendantSummary(attendant) }}</p>
</div>
            <div v-if="dashboardData.data.attendants.length === 0" class="text-center py-4 text-gray-400 text-xs">
              No active attendants
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="space-y-4">
        
        <!-- Task Type Distribution -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Task Types</h3>
          <div class="space-y-2">
            <div v-for="type in dashboardData.data.statistics.by_task_type" :key="type.task_type" 
              class="flex items-center justify-between">
              <span class="text-xs text-gray-600">{{ type.task_type }}</span>
              <span class="text-xs font-bold text-gray-900">{{ type.count }}</span>
            </div>
          </div>
        </div>

        <!-- Priority Distribution -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Task Priorities</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Urgent</span>
              <span class="text-xs font-bold text-red-600">{{ dashboardData.data.statistics.by_priority.Urgent || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">High</span>
              <span class="text-xs font-bold text-orange-600">{{ dashboardData.data.statistics.by_priority.High || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Medium</span>
              <span class="text-xs font-bold text-blue-600">{{ dashboardData.data.statistics.by_priority.Medium || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Low</span>
              <span class="text-xs font-bold text-gray-600">{{ dashboardData.data.statistics.by_priority.Low || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Inventory Summary -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Inventory Activity</h3>
          <div class="space-y-2">
            <div v-if="dashboardData.data.inventory_summary.Added.quantity > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Added</span>
              <span class="text-xs font-bold text-green-600">{{ dashboardData.data.inventory_summary.Added.quantity }} units</span>
            </div>
            <div v-if="dashboardData.data.inventory_summary.Removed.quantity > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Removed</span>
              <span class="text-xs font-bold text-red-600">{{ dashboardData.data.inventory_summary.Removed.quantity }} units</span>
            </div>
            <div v-if="dashboardData.data.inventory_summary.Replaced.quantity > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Replaced</span>
              <span class="text-xs font-bold text-blue-600">{{ dashboardData.data.inventory_summary.Replaced.quantity }} units</span>
            </div>
          </div>
        </div>

        <!-- Today's Tasks -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Today's Schedule</h3>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div v-for="task in dashboardData.data.today_tasks.slice(0, 5)" :key="task.name" class="border-b border-gray-100 pb-2 last:border-0">
              <p class="text-xs font-medium text-gray-900">{{ task.task_type }} - Room {{ task.room }}</p>
              <p class="text-xs text-gray-500">Status: {{ task.status }} • Priority: {{ task.priority }}</p>
            </div>
            <div v-if="dashboardData.data.today_tasks.length === 0" class="text-center py-4 text-gray-400 text-xs">
              No tasks scheduled for today
            </div>
          </div>
        </div>

        <!-- Recent Notes -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Recent Notes</h3>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div v-for="note in dashboardData.data.recent_notes.slice(0, 3)" :key="note.name" class="border-b border-gray-100 pb-2 last:border-0">
              <p class="text-xs text-gray-600">Room {{ note.room }}</p>
              <p class="text-xs text-gray-500 mt-1">{{ truncate(note.notes, 80) }}</p>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <button @click="createNewTask" 
            class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            Create New Task
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="dashboardData.loading" class="flex justify-center items-center h-64">
      <div class="text-gray-400">Loading dashboard data...</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const router = useRouter()
const dashboardError = ref('')

function notifyError(message) {
  dashboardError.value = message
  console.error(message)
}

// Create resource for dashboard data
const dashboardData = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_dashboard',
  cache: ['housekeeping_dashboard'],
  auto: true,
  onError: (error) => {
    console.error('Error fetching dashboard data:', error)
    notifyError('Failed to load dashboard data')
  },
  onSuccess: () => {
    dashboardError.value = ''
  }
})

const formattedDate = computed(() => {
  const date = new Date()
  return date.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
})

const refreshData = () => {
  dashboardError.value = ''
  dashboardData.reload()
}

const createNewTask = () => {
  router.push('/housekeeping/task/new')
}

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// Helper function for Attendant Workload summary text
const getAttendantSummary = (attendant) => {
  return `${attendant.total_tasks} rooms assigned • ${attendant.completed} completed • ${attendant.in_progress} in progress • ${attendant.pending} pending`
}

// ── AI context ────────────────────────────────────────────────────────
const housekeepingAiContext = computed(() => {
  const d = dashboardData.data
  if (!d?.statistics) return null
  const s = d.statistics
  return {
    total_tasks: s.total_tasks,
    active_tasks: s.active_tasks,
    completion_rate_pct: s.completion_rate,
    pending: s.by_status?.Pending || 0,
    assigned: s.by_status?.Assigned || 0,
    in_progress: s.by_status?.['In Progress'] || 0,
    completed: s.by_status?.Completed || 0,
    on_hold: s.by_status?.['On Hold'] || 0,
    high_priority_tasks: (d.priority_tasks || []).slice(0, 5).map(
      t => ({ room: t.room, type: t.task_type, status: t.status, priority: t.priority })
    ),
  }
})

// Helper functions for Recent Tasks
const getTaskDisplayName = (task) => {
  if (task.priority === 'Urgent') return 'Dirty'
  if (task.priority === 'High') return 'High Priority'
  if (task.status === 'In Progress') return 'Cleaning in Progress'
  if (task.status === 'Completed') return 'Clean & Ready'
  if (task.status === 'Pending') return 'Pending'
  if (task.status === 'Assigned') return 'Assigned'
  if (task.status === 'On Hold') return 'On Hold'
  return task.task_type
}

const getTaskCardClass = (task) => {
  if (task.priority === 'Urgent') return 'bg-red-50 border border-red-100'
  if (task.priority === 'High') return 'bg-orange-50 border border-orange-100'
  if (task.status === 'In Progress') return 'bg-blue-50 border border-blue-100'
  if (task.status === 'Completed') return 'bg-green-50 border border-green-100'
  if (task.status === 'Pending') return 'bg-yellow-50 border border-yellow-100'
  if (task.status === 'Assigned') return 'bg-purple-50 border border-purple-100'
  if (task.status === 'On Hold') return 'bg-gray-50 border border-gray-100'
  return 'bg-gray-50 border border-gray-100'
}

const getBadgeText = (task) => {
  if (task.priority === 'Urgent') return 'Urgent'
  if (task.priority === 'High') return 'High Priority'
  if (task.status === 'In Progress') return 'In Progress'
  if (task.status === 'Completed') return 'Released'
  if (task.status === 'Pending') return 'Pending'
  if (task.status === 'Assigned') return 'Assigned'
  if (task.status === 'On Hold') return 'On Hold'
  return task.status
}

const getBadgeClass = (task) => {
  if (task.priority === 'Urgent') return 'bg-red-100 text-red-500'
  if (task.priority === 'High') return 'bg-orange-100 text-orange-600'
  if (task.status === 'In Progress') return 'bg-blue-100 text-blue-600'
  if (task.status === 'Completed') return 'bg-green-100 text-green-600'
  if (task.status === 'Pending') return 'bg-yellow-100 text-yellow-600'
  if (task.status === 'Assigned') return 'bg-purple-100 text-purple-600'
  if (task.status === 'On Hold') return 'bg-gray-100 text-gray-600'
  return 'bg-gray-100 text-gray-600'
}

const getTaskSubtitle = (task) => {
  if (task.priority === 'Urgent') return 'Due-out room • high priority • VIP arrival scheduled'
  if (task.priority === 'High') return 'High priority task • needs immediate attention'
  if (task.status === 'In Progress' && task.employee) return `Assigned to ${task.employee} • in progress`
  if (task.status === 'Completed') return 'Inspected and ready for release'
  if (task.status === 'Pending') return 'Awaiting assignment • needs attention'
  if (task.status === 'Assigned' && task.employee) return `Assigned to ${task.employee} • pending start`
  return task.notes || `${task.task_type} task for room ${task.room}`
}
</script>