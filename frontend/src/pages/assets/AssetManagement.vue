<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Operations • asset inventory, maintenance, lifecycle, and utilization monitoring</p>
    </div>

    <!-- Asset Control Center -->
    <div class="bg-white rounded-xl border-2 border-blue-400 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-1">Asset Control Center</h3>
      <p class="text-xs text-gray-400 mb-4">Manage all physical assets, track maintenance history, monitor asset conditions, and access related operational records quickly.</p>
      <div class="flex items-center justify-end gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/maintenance/request')">Maintenance Request List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/maintenance/list')">Maintenance Task List</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="$router.push('/assets-mgmt/list')">Asset List</button>
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
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">21</p>
      </div>
    </div>

    <!-- Analytics Row -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">

      <!-- Asset Category Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Asset Category Analytics</h3>
        <p class="text-xs text-gray-400 mb-4">Distribution of active assets by major operational category.</p>
        <div class="space-y-3">
          <div v-for="c in categories" :key="c.label">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700">{{ c.label }}</span>
              <span class="text-xs font-semibold text-gray-900">{{ c.pct }}%</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div class="h-2 rounded-full" :style="{ width: c.pct + '%', background: c.color }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Maintenance Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Maintenance Analytics</h3>
        <p class="text-xs text-gray-400 mb-4">Open, in-progress, and completed maintenance tasks this month.</p>
        <div class="flex items-end justify-around h-32 mt-4">
          <div class="flex flex-col items-center gap-1">
            <span class="text-xs font-bold text-gray-700">18</span>
            <div class="w-12 rounded-t-md" style="height:50px;background:#f59e0b;"></div>
            <span class="text-xs text-gray-400">Open</span>
          </div>
          <div class="flex flex-col items-center gap-1">
            <span class="text-xs font-bold text-gray-700">26</span>
            <div class="w-12 rounded-t-md" style="height:70px;background:#3b82f6;"></div>
            <span class="text-xs text-gray-400">Active</span>
          </div>
          <div class="flex flex-col items-center gap-1">
            <span class="text-xs font-bold text-gray-700">41</span>
            <div class="w-12 rounded-t-md" style="height:100px;background:#22c55e;"></div>
            <span class="text-xs text-gray-400">Closed</span>
          </div>
        </div>
      </div>

      <!-- Lifecycle Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Lifecycle Analytics</h3>
        <p class="text-xs text-gray-400 mb-4">Replacement age, warranty coverage, and retirement planning overview.</p>
        <div class="flex items-center gap-5 mt-4">
          <!-- Donut -->
          <div class="relative flex-shrink-0" style="width:80px;height:80px;">
            <svg viewBox="0 0 36 36" class="w-20 h-20 -rotate-90">
              <circle cx="18" cy="18" r="14" fill="none" stroke="#e5e7eb" stroke-width="4"/>
              <circle cx="18" cy="18" r="14" fill="none" stroke="#3b82f6" stroke-width="4"
                stroke-dasharray="87.96 100" stroke-linecap="round"/>
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-sm font-bold text-gray-900">68%</span>
            </div>
          </div>
          <div class="space-y-1.5">
            <p class="text-xs text-gray-600">Within warranty</p>
            <p class="text-xs text-gray-600">9 due for replacement</p>
            <p class="text-xs text-gray-600">14 expiring soon</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity + Insights -->
    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Recent Asset Activity -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Recent Asset Activity</h3>
        </div>
        <div class="divide-y divide-gray-50">
          <div v-for="a in recentActivity" :key="a.id" class="px-6 py-4 flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold text-gray-900 mb-0.5">{{ a.title }}</p>
              <p class="text-xs text-gray-400">{{ a.desc }}</p>
            </div>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full flex-shrink-0 ml-4"
              :class="activityStatusClass(a.status)">{{ a.status }}</span>
          </div>
        </div>
      </div>

      <!-- Asset Insights -->
      <div class="space-y-3">
        <h3 class="text-sm font-bold text-gray-900">Asset Insights</h3>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Top Asset Category</p>
          <p class="text-xs text-gray-500">Room electronics remain the largest active category.</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Maintenance Exposure</p>
          <p class="text-xs text-gray-500">12 assets have repeated service calls in the last 60 days.</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Replacement Planning</p>
          <p class="text-xs text-gray-500">9 assets are nearing replacement age this quarter.</p>
        </div>
        <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-3 text-center">
          <button class="text-xs font-semibold text-blue-600 hover:underline">Review expiring warranties this week</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
const categories = [
  { label: 'Room Electronics',     pct: 46, color: '#3b82f6' },
  { label: 'Housekeeping Equipment',pct: 33, color: '#f59e0b' },
  { label: 'Kitchen / Laundry',    pct: 21, color: '#f97316' },
]

const recentActivity = [
  { id: 1, title: 'Asset AST-004821 assigned to Room 305',                   desc: 'Smart TV • assigned by Operations Admin • 18 Apr 2026',      status: 'Assigned' },
  { id: 2, title: 'Maintenance ticket MNT-000219 opened for Laundry Dryer', desc: 'Corrective maintenance • Engineering team notified',           status: 'Pending' },
  { id: 3, title: 'Warranty alert raised for generator battery bank',        desc: 'Expires in 12 days • vendor review required',                  status: 'Urgent' },
  { id: 4, title: 'Request REQ-000118 approved for vacuum cleaner replacement',desc:'Housekeeping request • approved by Operations Manager',       status: 'Approved' },
  { id: 5, title: 'Asset AST-003176 marked retired and archived',            desc: 'Old minibar unit • removed from active inventory',             status: 'Closed' },
]

function activityStatusClass(s) {
  return {
    'Assigned': 'bg-blue-50 text-blue-600',
    'Pending':  'bg-yellow-50 text-yellow-600',
    'Urgent':   'bg-red-50 text-red-500',
    'Approved': 'bg-green-50 text-green-600',
    'Closed':   'bg-gray-100 text-gray-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>