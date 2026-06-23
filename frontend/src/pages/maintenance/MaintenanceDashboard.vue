<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex flex-col gap-3 mb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 class="text-base font-bold text-gray-900">Maintenance Control Center</h2>
          <p class="text-xs text-gray-400 mt-0.5">Monitor corrective and preventive tasks, assign technicians, review due work, and access maintenance history quickly.</p>
        </div>
        <button @click="loadDashboard"
          class="w-full px-3 py-1.5 text-xs font-medium text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-1.5 sm:w-auto">
          <svg :class="loading ? 'animate-spin' : ''" class="w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          Refresh
        </button>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
        <router-link to="/maintenance/list">
          <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">
            Maintenance List
          </button>
        </router-link>
        <router-link to="/maintenance/technicians">
          <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">
            Technicians
          </button>
        </router-link>
        <router-link to="/maintenance/request">
          <button class="w-full px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto">
            Request List
          </button>
        </router-link>
        <router-link to="/maintenance/new-request">
          <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">
            New Request
          </button>
        </router-link>
        <!-- <router-link to="/maintenance/new-task">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors">
            Create Maintenance Task
          </button>
        </router-link> -->
      </div>
    </div>

    <!-- Stats skeleton -->
    <div v-if="loading" class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
      <div v-for="n in 5" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
        <div class="h-2 bg-gray-100 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Stats -->
    <div v-else-if="data" class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Pending Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">New</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ data.stats.pending_requests }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ data.stats.urgent_pending_requests }} urgent</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Open Tasks</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ data.stats.open }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ data.stats.in_progress }} in progress</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Urgent Repairs</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">High</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ data.stats.urgent_open }}</p>
        <p class="text-xs text-gray-400 mt-1">High priority, not done</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Closed This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ data.stats.done_this_week }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ data.stats.done }} all time</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Avg Resolution</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ data.stats.avg_resolution_hrs }}<span class="text-base font-medium text-gray-400 ml-1">hrs</span></p>
        <p class="text-xs text-gray-400 mt-1">{{ data.stats.hold }} on hold</p>
      </div>
    </div>

    <!-- AI Maintenance Triage -->
    <AIInsightPanel
      v-if="data"
      title="AI Maintenance Triage"
      context-type="maintenance_triage_summary"
      :context-data="maintenanceAiContext"
      :auto-load="false"
      panel-id="maintenance-dashboard"
    />

    <!-- Analytics Row -->
    <div v-if="data" class="grid grid-cols-1 gap-3 lg:grid-cols-3">

      <!-- Task Status Chart -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Task Status Analytics</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Current distribution by workflow status.</p>
        <div class="flex items-end justify-around gap-2">
          <div v-for="bar in taskBars" :key="bar.label" class="flex flex-col items-center gap-1.5">
            <span class="text-xs font-semibold text-gray-600">{{ bar.value }}</span>
            <div class="w-10 rounded-t-md transition-all duration-500"
              :style="{ height: barHeight(bar.value) + 'px', backgroundColor: bar.color }"></div>
            <span class="text-xs text-gray-400">{{ bar.label }}</span>
          </div>
        </div>
      </div>

      <!-- Type Mix -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Type Mix</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Corrective vs preventive work concentration.</p>
        <div class="flex items-center gap-5">
          <div class="relative w-24 h-24 flex-shrink-0">
            <svg viewBox="0 0 36 36" class="w-24 h-24 -rotate-90">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3.5" />
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#3b82f6" stroke-width="3.5"
                :stroke-dasharray="`${data.corrective_pct} ${100 - data.corrective_pct}`"
                stroke-linecap="round" />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-sm font-bold text-gray-900">{{ data.corrective_pct }}%</span>
            </div>
          </div>
          <div class="space-y-2">
            <div v-for="(pct, type) in data.type_mix" :key="type" class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: typeColor(type) }"></div>
              <span class="text-xs text-gray-600">{{ pct }}% {{ type }}</span>
            </div>
            <div v-if="Object.keys(data.type_mix).length === 0" class="text-xs text-gray-400 italic">No data yet</div>
          </div>
        </div>
      </div>

      <!-- Top Locations by Open Tasks -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Top Locations — Open Tasks</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Locations with the most unresolved maintenance work.</p>
        <div class="space-y-3">
          <div v-for="item in data.top_locations" :key="item.location">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700 font-medium truncate max-w-[140px]">{{ item.location }}</span>
              <span class="text-xs text-gray-400">{{ item.open_tasks }} tasks</span>
            </div>
            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-blue-500 transition-all duration-500"
                :style="{ width: locationBarPct(item.open_tasks) + '%' }"></div>
            </div>
          </div>
          <div v-if="data.top_locations.length === 0" class="text-xs text-gray-400 italic text-center py-4">
            No open tasks
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Row -->
    <div v-if="data" class="grid grid-cols-1 gap-3 xl:grid-cols-2">

      <!-- Recent Activity -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Recent Maintenance Activity</h3>
          <router-link to="/maintenance/list">
            <span class="text-xs text-blue-600 hover:underline">View all →</span>
          </router-link>
        </div>
        <div class="divide-y divide-gray-50">
          <div v-for="task in data.recent_activity" :key="task.name"
            class="px-5 py-3.5 flex items-start justify-between hover:bg-gray-50 transition-colors cursor-pointer"
            @click="router.push({ name: 'MaintenanceTask', params: { id: task.name } })">
            <div class="flex-1 min-w-0 pr-3">
              <p class="text-xs font-semibold text-gray-900 font-mono leading-snug">{{ task.name }}</p>
              <p class="text-xs text-gray-500 mt-0.5">
                {{ task.location || '—' }} •
                {{ task.technician_name }}
                <span v-if="task.task_type" class="text-gray-400"> • {{ task.task_type }}</span>
              </p>
            </div>
            <span class="flex-shrink-0 px-2.5 py-1 text-xs font-medium rounded-full"
              :class="statusBadge(task.status)">
              {{ task.status }}
            </span>
          </div>
          <div v-if="data.recent_activity.length === 0" class="px-5 py-6 text-center text-xs text-gray-400">
            No recent activity
          </div>
        </div>
      </div>

      <!-- Insights -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Maintenance Insights</h3>
        </div>
        <div class="p-5 space-y-3">
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Open vs In Progress</h4>
            <p class="text-xs text-gray-500">
              {{ data.stats.open }} tasks awaiting assignment,
              {{ data.stats.in_progress }} currently being worked on.
            </p>
          </div>
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Urgent Load</h4>
            <p class="text-xs text-gray-500">
              {{ data.stats.urgent_open }} high-priority tasks are still open.
              <span v-if="data.stats.urgent_open > 5" class="text-red-500 font-medium"> Action required.</span>
            </p>
          </div>
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Weekly Throughput</h4>
            <p class="text-xs text-gray-500">
              {{ data.stats.done_this_week }} tasks completed this week.
              Average resolution: {{ data.stats.avg_resolution_hrs }} hrs.
            </p>
          </div>
          <router-link to="/maintenance/list?filter_priority=High">
            <button class="w-full py-2.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors border border-red-100">
              View urgent repairs →
            </button>
          </router-link>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const router = useRouter()
const loading = ref(true)
const data = ref(null)

const dashResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_dashboard_summary',
  auto: false
})

async function loadDashboard() {
  loading.value = true
  try {
    const res = await dashResource.fetch()
    console.log('[MaintenanceDashboard]', res)
    data.value = res
  } catch (e) {
    console.error('[MaintenanceDashboard] error:', e)
  } finally {
    loading.value = false
  }
}

// ─── Bar chart helpers ────────────────────────────────────────────────────────
const taskBars = computed(() => {
  if (!data.value) return []
  const s = data.value.stats
  return [
    { label: 'Open',     value: s.open,        color: '#f59e0b' },
    { label: 'Progress', value: s.in_progress,  color: '#3b82f6' },
    { label: 'Done',     value: s.done,         color: '#22c55e' },
    { label: 'Hold',     value: s.hold,         color: '#9ca3af' },
  ]
})

function barHeight(value) {
  if (!data.value) return 10
  const s = data.value.stats
  const max = Math.max(s.open, s.in_progress, s.done, s.hold, 1)
  return Math.max(8, Math.round((value / max) * 80))
}

function locationBarPct(count) {
  if (!data.value?.top_locations?.length) return 0
  const max = Math.max(...data.value.top_locations.map(a => a.open_tasks), 1)
  return Math.round((count / max) * 100)
}

function typeColor(type) {
  return {
    Corrective: '#3b82f6',
    Preventive: '#22c55e',
    Routine:    '#f59e0b',
    Inspection: '#a855f7',
  }[type] || '#9ca3af'
}

function statusBadge(s) {
  return {
    'Open':        'bg-yellow-50 text-yellow-600',
    'In Progress': 'bg-blue-50 text-blue-600',
    'Done':        'bg-green-50 text-green-600',
    'Hold':        'bg-gray-100 text-gray-500',
    'Cancelled':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

// ── AI context ────────────────────────────────────────────────────────
const maintenanceAiContext = computed(() => {
  if (!data.value?.stats) return null
  const s = data.value.stats
  return {
    pending_requests: s.pending_requests,
    urgent_pending_requests: s.urgent_pending_requests,
    open_tasks: s.open,
    in_progress: s.in_progress,
    urgent_open: s.urgent_open,
    done_this_week: s.done_this_week,
    avg_resolution_hrs: s.avg_resolution_hrs,
    on_hold: s.hold,
    top_locations: (data.value.top_locations || []).slice(0, 5).map(
      l => ({ location: l.location || l.name, open_tasks: l.open_tasks })
    ),
  }
})

onMounted(loadDashboard)
</script>