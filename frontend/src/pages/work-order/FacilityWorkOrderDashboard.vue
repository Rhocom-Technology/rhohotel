<template>
  <div class="space-y-4">

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-gray-900">Facility Work Orders Dashboard</h2>
          <p class="text-xs text-gray-400 mt-0.5">
            Monitor hotel facility requests, approvals, urgent work orders, technician workload, and closure performance.
          </p>
        </div>

        <button
          @click="loadDashboard"
          class="px-3 py-1.5 text-xs font-medium text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1.5"
        >
          <svg :class="loading ? 'animate-spin' : ''" class="w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          Refresh
        </button>
      </div>

      <div class="flex items-center gap-3 flex-wrap">
        <router-link to="/facilities/work-orders">
          <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
            Work Orders
          </button>
        </router-link>

        <router-link to="/facilities/work-orders/new">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors">
            New Work Order
          </button>
        </router-link>

        <router-link to="/facilities/equipment-repair-authorizations">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Repair Authorizations
          </button>
        </router-link>
      </div>
    </div>

    <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <p class="text-sm font-semibold text-red-700">Unable to load dashboard</p>
      <p class="text-xs text-red-500 mt-1">{{ error }}</p>
    </div>

    <div v-if="loading" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div v-for="n in 8" :key="n" class="bg-white rounded-xl border border-gray-200 px-5 py-4 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
        <div class="h-2 bg-gray-100 rounded w-2/3"></div>
      </div>
    </div>

    <template v-else-if="data">
      
        <!-- Top Stats Row -->
<div v-if="data" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs text-gray-400">Active Orders</p>
      <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Open</span>
    </div>
    <p class="text-3xl font-bold text-gray-900">{{ data.stats.active }}</p>
    <p class="text-xs text-gray-400 mt-1">{{ data.stats.total }} total all-time</p>
  </div>

  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs text-gray-400">Emergency</p>
      <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Critical</span>
    </div>
    <p class="text-3xl font-bold text-gray-900">{{ data.stats.emergency_active }}</p>
    <p class="text-xs text-gray-400 mt-1">{{ data.stats.urgent_active }} urgent active</p>
  </div>

  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs text-gray-400">Closed This Week</p>
      <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
    </div>
    <p class="text-3xl font-bold text-gray-900">{{ data.stats.closed_this_week }}</p>
    <p class="text-xs text-gray-400 mt-1">{{ data.stats.closed_this_month }} this month</p>
  </div>

  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs text-gray-400">Avg Resolution</p>
      <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Time</span>
    </div>
    <p class="text-3xl font-bold text-gray-900">
      {{ data.stats.avg_resolution_hrs }}<span class="text-base font-medium text-gray-400 ml-1">hrs</span>
    </p>
    <p class="text-xs text-gray-400 mt-1">Last 30 days average</p>
  </div>
</div>

      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <StatCard label="Overdue" :value="data.secondary_cards.overdue" badge="Late" badge-class="bg-orange-100 text-orange-600" subtext="Past expected completion" />
        <StatCard label="Unassigned" :value="data.secondary_cards.unassigned" badge="Pending" badge-class="bg-gray-100 text-gray-500" subtext="No technician assigned" />
        <StatCard label="Closed" :value="data.secondary_cards.closed" badge="Total" badge-class="bg-green-100 text-green-600" :subtext="`${data.secondary_cards.rejected} rejected`" />
        <StatCard label="Cancelled" :value="data.secondary_cards.cancelled" badge="Void" badge-class="bg-red-50 text-red-400" subtext="All-time cancelled" />
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Workflow Status</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Current distribution by workflow state.</p>

          <div class="flex items-end justify-around gap-2 min-h-[150px]">
            <div v-for="item in statusBars" :key="item.label" class="flex flex-col items-center gap-1.5">
              <span class="text-xs font-semibold text-gray-600">{{ item.value }}</span>
              <div
                class="w-9 rounded-t-md transition-all duration-500"
                :style="{ height: barHeight(item.value, maxStatusValue) + 'px', backgroundColor: item.color }"
              ></div>
              <span class="text-[10px] text-gray-400 text-center max-w-[70px] leading-tight">{{ shortStatus(item.label) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">SLA Health</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Emergency: 1 day, Urgent: 2 days, Routine: 7 days.</p>

          <div class="flex items-center gap-5">
            <div class="relative w-28 h-28 flex-shrink-0">
              <svg viewBox="0 0 36 36" class="w-28 h-28 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3.5" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.9"
                  fill="none"
                  stroke="#22c55e"
                  stroke-width="3.5"
                  :stroke-dasharray="`${slaHealthyPct} ${100 - slaHealthyPct}`"
                  stroke-linecap="round"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-lg font-bold text-gray-900">{{ slaHealthyPct }}%</span>
                <span class="text-[10px] text-gray-400">healthy</span>
              </div>
            </div>

            <div class="space-y-2 flex-1">
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-600">Healthy</span>
                <span class="text-xs font-semibold text-green-600">{{ data.sla.healthy }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-600">Due Today</span>
                <span class="text-xs font-semibold text-yellow-600">{{ data.sla.warning }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-600">Breached</span>
                <span class="text-xs font-semibold text-red-500">{{ data.sla.breached }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Active Priority Levels</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Priority distribution of open work orders.</p>

          <div class="space-y-4">
            <div v-for="p in activePriorityBars" :key="p.label">
              <div class="flex items-center justify-between mb-1.5">
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: p.color }"></div>
                  <span class="text-xs font-medium text-gray-700">{{ p.label }}</span>
                </div>
                <span class="text-xs font-bold text-gray-900">{{ p.value }}</span>
              </div>

              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: percent(p.value, maxActivePriorityValue) + '%', backgroundColor: p.color }"
                ></div>
              </div>
            </div>

            <div v-if="activePriorityBars.length === 0" class="text-xs text-gray-400 italic text-center py-8">
              No active priority data.
            </div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Open Work Order Aging</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">How long unresolved work orders have been open.</p>

          <div class="space-y-3">
            <div v-for="item in data.aging" :key="item.label">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-700 font-medium">{{ item.label }}</span>
                <span class="text-xs text-gray-400">{{ item.value }}</span>
              </div>
              <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full bg-blue-500 transition-all duration-500"
                  :style="{ width: percent(item.value, maxAgingValue) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Location Type Breakdown</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Where facility work orders originate.</p>

          <div class="space-y-3">
            <div v-for="loc in data.location_type_breakdown" :key="loc.label">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-700 font-medium">{{ loc.label }}</span>
                <span class="text-xs text-gray-400">{{ loc.value }}</span>
              </div>

              <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  :style="{ width: percent(loc.value, maxLocationTypeValue) + '%' }"
                ></div>
              </div>
            </div>

            <div v-if="data.location_type_breakdown.length === 0" class="text-xs text-gray-400 italic text-center py-4">
              No location type data.
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">Top Open Locations</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Locations with unresolved work.</p>

          <div class="space-y-3">
            <div v-for="item in data.top_locations" :key="item.location">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-700 font-medium truncate max-w-[160px]">{{ item.location }}</span>
                <span class="text-xs text-gray-400">{{ item.open_work_orders }}</span>
              </div>
              <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full bg-blue-500 transition-all duration-500"
                  :style="{ width: percent(item.open_work_orders, maxLocationValue) + '%' }"
                ></div>
              </div>
            </div>

            <div v-if="data.top_locations.length === 0" class="text-xs text-gray-400 italic text-center py-5">
              No open locations.
            </div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:2fr 1fr;gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
          <h3 class="text-sm font-bold text-gray-900">30-Day Work Order Trend</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">New work orders and closures by date.</p>

          <div class="flex items-end gap-1 h-44 border-b border-gray-100 pb-2">
            <div v-for="day in data.daily_trend" :key="day.date" class="flex-1 flex flex-col items-center justify-end gap-0.5">
              <div class="w-full flex items-end justify-center gap-0.5">
                <div
                  class="w-2 rounded-t-sm bg-blue-500"
                  :style="{ height: barHeight(day.total, maxDailyValue, 120) + 'px' }"
                  :title="`${day.label}: ${day.total} created`"
                ></div>
                <div
                  class="w-2 rounded-t-sm bg-green-500"
                  :style="{ height: barHeight(day.closed, maxDailyValue, 120) + 'px' }"
                  :title="`${day.label}: ${day.closed} closed`"
                ></div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-4 mt-3">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              <span class="text-xs text-gray-500">Created</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-green-500"></span>
              <span class="text-xs text-gray-500">Closed</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Technician Workload</h3>
            <p class="text-xs text-gray-400 mt-0.5">Active orders assigned per technician.</p>
          </div>

          <div class="divide-y divide-gray-50">
            <div
              v-for="tech in data.technician_workload"
              :key="tech.assigned_technician"
              class="px-5 py-3 flex items-center justify-between"
            >
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-900">{{ tech.technician_name }}</p>
                <p class="text-[10px] text-gray-400 mt-0.5">
                  {{ tech.total_assigned }} total • {{ tech.closed_orders }} closed
                </p>
              </div>

              <div class="flex items-center gap-2">
                <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full bg-blue-500 transition-all duration-500"
                    :style="{ width: percent(tech.active_orders, maxTechnicianWorkload) + '%' }"
                  ></div>
                </div>
                <span class="text-xs font-bold text-gray-900 w-6 text-right">{{ tech.active_orders }}</span>
              </div>
            </div>

            <div v-if="data.technician_workload.length === 0" class="px-5 py-6 text-center text-xs text-gray-400">
              No technician workload data.
            </div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Urgent Open Work Orders</h3>
            <p class="text-xs text-gray-400 mt-0.5">Emergency and urgent requests still open.</p>
          </div>

          <div class="divide-y divide-gray-50">
            <div v-for="wo in data.urgent_work_orders" :key="wo.name" class="px-5 py-3.5 hover:bg-gray-50">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-xs font-semibold text-gray-900 font-mono">{{ wo.name }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">
                    {{ wo.location_display }} • {{ wo.requesting_department || 'No department' }}
                  </p>
                </div>
                <div class="text-right flex-shrink-0">
                  <span :class="priorityClass(wo.priority)" class="px-2.5 py-1 text-xs font-medium rounded-full">
                    {{ wo.priority || 'Routine' }}
                  </span>
                  <p class="text-[10px] text-gray-400 mt-1">{{ wo.age_days }} days old</p>
                </div>
              </div>
            </div>

            <div v-if="data.urgent_work_orders.length === 0" class="px-5 py-8 text-center text-xs text-gray-400 italic">
              No urgent open work orders.
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Linked Operational Documents</h3>
            <p class="text-xs text-gray-400 mt-0.5">Documents created from work order execution.</p>
          </div>

          <div class="divide-y divide-gray-50">
            <div v-for="doc in data.linked_documents" :key="doc.doctype" class="px-5 py-3.5">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-xs font-semibold text-gray-900">{{ doc.doctype }}</p>
                  <p class="text-[10px] text-gray-400 mt-0.5">
                    {{ doc.submitted }} submitted • {{ doc.draft }} draft
                  </p>
                </div>
                <p class="text-xl font-bold text-gray-900">{{ doc.total }}</p>
              </div>
            </div>

            <div v-if="data.linked_documents.length === 0" class="px-5 py-8 text-center text-xs text-gray-400 italic">
              No linked document types found.
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Recent Facility Work Orders</h3>
            <p class="text-xs text-gray-400 mt-0.5">Latest activity across facility operations.</p>
          </div>
          <router-link to="/facilities/work-orders">
            <span class="text-xs text-blue-600 hover:underline">View all →</span>
          </router-link>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full text-xs">
            <thead class="bg-gray-50 border-b border-gray-100">
              <tr>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Work Order</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Location</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Department</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Technician</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Category</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Priority</th>
                <th class="text-left px-5 py-3 font-semibold text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="wo in data.recent_work_orders" :key="wo.name" class="hover:bg-gray-50">
                <td class="px-5 py-3 font-mono font-semibold text-gray-900">{{ wo.name }}</td>
                <td class="px-5 py-3 text-gray-600">{{ wo.location_display }}</td>
                <td class="px-5 py-3 text-gray-600">{{ wo.requesting_department || '—' }}</td>
                <td class="px-5 py-3 text-gray-600">{{ wo.technician_name || 'Unassigned' }}</td>
                <td class="px-5 py-3 text-gray-600">{{ wo.category || '—' }}</td>
                <td class="px-5 py-3">
                  <span :class="priorityClass(wo.priority)" class="px-2.5 py-1 text-xs font-medium rounded-full">
                    {{ wo.priority || 'Routine' }}
                  </span>
                </td>
                <td class="px-5 py-3">
                  <span :class="statusClass(wo.workflow_state)" class="px-2.5 py-1 text-xs font-medium rounded-full">
                    {{ wo.workflow_state || 'Draft' }}
                  </span>
                </td>
              </tr>

              <tr v-if="data.recent_work_orders.length === 0">
                <td colspan="7" class="px-5 py-8 text-center text-xs text-gray-400 italic">
                  No work orders found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { callMethod } from '@/lib/api'

const loading = ref(true)
const error = ref('')
const data = ref(null)

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    data.value = await callMethod(
      'rhohotel.rhocom_hotel.api.facility_work_order_dashboard.get_facility_work_order_dashboard',
      { days: 30 }
    )
  } catch (err) {
    error.value = err?.message || 'Failed to load facility work order dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)

const maxStatusValue = computed(() => {
  return Math.max(...(data.value?.status_breakdown || []).map(item => item.value), 1)
})

const maxAgingValue = computed(() => {
  return Math.max(...(data.value?.aging || []).map(item => item.value), 1)
})

const maxDailyValue = computed(() => {
  return Math.max(...(data.value?.daily_trend || []).map(item => Math.max(item.total, item.closed)), 1)
})

const maxLocationValue = computed(() => {
  return Math.max(...(data.value?.top_locations || []).map(item => item.open_work_orders), 1)
})

const maxTechnicianWorkload = computed(() => {
  return Math.max(...(data.value?.technician_workload || []).map(item => item.active_orders), 1)
})

const maxLocationTypeValue = computed(() => {
  return Math.max(...(data.value?.location_type_breakdown || []).map(item => item.value), 1)
})

const statusBars = computed(() => {
  const colors = {
    Draft: '#9ca3af',
    'Pending Requesting Officer Approval': '#3b82f6',
    'Pending Facility Supervisor Approval': '#f59e0b',
    'Pending Department Head Signature': '#8b5cf6',
    Closed: '#22c55e',
    Rejected: '#ef4444',
    Cancelled: '#6b7280'
  }

  return (data.value?.status_breakdown || []).map(item => ({
    ...item,
    color: colors[item.label] || '#3b82f6'
  }))
})

const activePriorityBars = computed(() => {
  const colors = {
    Emergency: '#ef4444',
    Urgent: '#f59e0b',
    Routine: '#22c55e',
    'Not Set': '#9ca3af'
  }

  return (data.value?.active_priority_levels || []).map(item => ({
    ...item,
    color: colors[item.label] || '#9ca3af'
  }))
})

const maxActivePriorityValue = computed(() => {
  return Math.max(...activePriorityBars.value.map(item => item.value), 1)
})

const slaHealthyPct = computed(() => {
  if (!data.value) return 0

  const total = data.value.sla.healthy + data.value.sla.warning + data.value.sla.breached
  if (!total) return 100

  return Math.round((data.value.sla.healthy / total) * 100)
})

function barHeight(value, max, height = 115) {
  if (!max) return 8
  return Math.max(8, Math.round((Number(value || 0) / max) * height))
}

function percent(value, max) {
  if (!max) return 0
  return Math.max(4, Math.round((Number(value || 0) / max) * 100))
}

function shortStatus(status) {
  const map = {
    'Pending Requesting Officer Approval': 'Req. Officer',
    'Pending Facility Supervisor Approval': 'Supervisor',
    'Pending Department Head Signature': 'Head Sign'
  }

  return map[status] || status
}

function priorityClass(priority) {
  if (priority === 'Emergency') return 'bg-red-100 text-red-600'
  if (priority === 'Urgent') return 'bg-orange-100 text-orange-600'
  return 'bg-gray-100 text-gray-600'
}

function statusClass(status) {
  if (status === 'Closed') return 'bg-green-100 text-green-600'
  if (status === 'Rejected' || status === 'Cancelled') return 'bg-red-100 text-red-500'
  if (status === 'Pending Department Head Signature') return 'bg-purple-100 text-purple-600'
  if (status === 'Pending Facility Supervisor Approval') return 'bg-yellow-100 text-yellow-600'
  return 'bg-blue-100 text-blue-600'
}
</script>

<script>
export default {
  components: {
    StatCard: {
      props: {
        label: String,
        value: [String, Number],
        suffix: String,
        badge: String,
        badgeClass: String,
        subtext: String
      },
      template: `
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">{{ label }}</p>
            <span :class="badgeClass" class="px-2.5 py-0.5 text-xs font-medium rounded-full">{{ badge }}</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">
            {{ value }}<span v-if="suffix" class="text-base font-medium text-gray-400 ml-1">{{ suffix }}</span>
          </p>
          <p class="text-xs text-gray-400 mt-1">{{ subtext }}</p>
        </div>
      `
    }
  }
}
</script>