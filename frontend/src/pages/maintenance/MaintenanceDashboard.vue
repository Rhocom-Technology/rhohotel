<template>
  <div class="space-y-4">

    <!-- Top Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-gray-900">Maintenance Control Center</h2>
          <p class="text-xs text-gray-400 mt-0.5">Monitor corrective and preventive tasks, assign technicians, review due work, and access maintenance history quickly.</p>
        </div>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <router-link to="/maintenance/list">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Maintenance List
          </button>
        </router-link>
        <router-link to="/maintenance/technicians">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Technicians
          </button>
        </router-link>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Service History
        </button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Preventive Plan
        </button>
        <router-link to="/maintenance/request">
          <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
            Maintenance Request List
          </button>
        </router-link>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors">
          Create Maintenance Task
        </button>
      </div>
    </div>

    <!-- Stats Row -->
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
          <p class="text-xs text-gray-400">Urgent Repairs</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Urgent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">12</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Due Preventive Work</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Due</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">17</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Avg Resolution Time</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Stable</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">18 hrs</p>
      </div>
    </div>

    <!-- Analytics Row -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">

      <!-- Task Status Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Task Status Analytics</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Current distribution of maintenance tasks by workflow status.</p>
        <div class="flex items-end justify-around gap-2">
          <div v-for="bar in taskBars" :key="bar.label" class="flex flex-col items-center gap-1.5">
            <span class="text-xs font-semibold text-gray-600">{{ bar.value }}</span>
            <div class="w-10 rounded-t-md" :style="{ height: bar.height + 'px', backgroundColor: bar.color }"></div>
            <span class="text-xs text-gray-400">{{ bar.label }}</span>
          </div>
        </div>
      </div>

      <!-- Maintenance Type Mix -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Maintenance Type Mix</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Corrective versus preventive work concentration this month.</p>
        <div class="flex items-center gap-5">
          <div class="relative w-24 h-24 flex-shrink-0">
            <svg viewBox="0 0 36 36" class="w-24 h-24 -rotate-90">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3.5" />
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#3b82f6" stroke-width="3.5"
                stroke-dasharray="61 39" stroke-linecap="round" />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-sm font-bold text-gray-900">61%</span>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
              <span class="text-xs text-gray-600">Corrective tasks</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full bg-gray-200"></div>
              <span class="text-xs text-gray-600">39% preventive</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full bg-orange-400"></div>
              <span class="text-xs text-gray-600">8 repeat issues</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Downtime Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
        <h3 class="text-sm font-bold text-gray-900">Downtime Analytics</h3>
        <p class="text-xs text-gray-400 mt-0.5 mb-5">Assets causing the highest operational downtime this week.</p>
        <div class="space-y-3">
          <div v-for="item in downtimeItems" :key="item.label">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700 font-medium">{{ item.label }}</span>
              <span class="text-xs text-gray-400">{{ item.hrs }} hrs</span>
            </div>
            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full" :style="{ width: item.pct + '%', backgroundColor: item.color }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Row -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- Recent Activity -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Recent Maintenance Activity</h3>
        </div>
        <div class="divide-y divide-gray-50">
          <div
            v-for="item in recentActivity"
            :key="item.name"
            class="px-5 py-3.5 flex items-start justify-between hover:bg-gray-50 transition-colors"
          >
            <div class="flex-1 min-w-0 pr-3">
              <p class="text-xs font-semibold text-gray-900 leading-snug">{{ item.title }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ item.subtitle }}</p>
            </div>
            <span class="flex-shrink-0 px-2.5 py-1 text-xs font-medium rounded-full" :class="activityBadge(item.status)">
              {{ item.status }}
            </span>
          </div>
        </div>
      </div>

      <!-- Maintenance Insights -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Maintenance Insights</h3>
        </div>
        <div class="p-5 space-y-3">
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Top Repeat Issue</h4>
            <p class="text-xs text-gray-500">HVAC-related calls remain the highest repeat maintenance source.</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Technician Load</h4>
            <p class="text-xs text-gray-500">Engineering Team B currently carries the highest active assignment load.</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 mb-1">Preventive Compliance</h4>
            <p class="text-xs text-gray-500">86% of scheduled preventive work has been completed this month.</p>
          </div>
          <button class="w-full py-2.5 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors border border-blue-100">
            Prioritize urgent repairs before end of shift
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
const taskBars = [
  { label: 'Open', value: 12, height: 60, color: '#f59e0b' },
  { label: 'Active', value: 15, height: 75, color: '#3b82f6' },
  { label: 'Done', value: 38, height: 80, color: '#22c55e' },
  { label: 'Hold', value: 4, height: 20, color: '#9ca3af' },
]

const downtimeItems = [
  { label: 'Laundry Dryer', hrs: 19, pct: 95, color: '#f59e0b' },
  { label: 'Generator Bank', hrs: 13, pct: 65, color: '#3b82f6' },
  { label: 'Booster Pump', hrs: 9, pct: 45, color: '#22c55e' },
]

const recentActivity = [
  { name: 'MNT-000219', title: 'MNT-000219 assigned to Engr. Paul for Laundry Dryer', subtitle: 'Corrective repair • Laundry Room • assigned 18 Apr 2026', status: 'Assigned' },
  { name: 'MNT-000218', title: 'Preventive service due for generator battery bank', subtitle: 'Power House • service window today at 4:00 PM', status: 'Due' },
  { name: 'MNT-000201', title: 'MNT-000201 completed for Room 305 Smart TV', subtitle: 'Screen firmware updated • closed by technician team', status: 'Closed' },
  { name: 'MNT-000216', title: 'Escalation raised for repeated AC issue in Room 214', subtitle: 'Repeat incident within 7 days • requires supervisor review', status: 'Urgent' },
  { name: 'MNT-000215', title: 'Vendor visit scheduled for boiler inspection', subtitle: 'External vendor • expected arrival tomorrow 9:00 AM', status: 'Scheduled' },
]

function activityBadge(status) {
  return {
    'Assigned': 'bg-blue-50 text-blue-600',
    'Due': 'bg-yellow-50 text-yellow-600',
    'Closed': 'bg-green-50 text-green-600',
    'Urgent': 'bg-red-50 text-red-500',
    'Scheduled': 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}
</script>