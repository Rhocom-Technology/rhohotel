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
      
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/assets-mgmt/list')">Asset List</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Assets</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Submitted</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.submitted }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">In Maintenance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.in_maintenance }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Draft</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashboard.draft }}</p>
      </div>
    </div>

    <!-- Analytics Row -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">

      <!-- Asset Category Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Asset Category Analytics</h3>
        <p class="text-xs text-gray-400 mb-4">Distribution of assets by category.</p>
        <div v-if="dashboard.categories && dashboard.categories.length" class="space-y-3">
          <div v-for="(c, i) in dashboard.categories" :key="c.label">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700">{{ c.label }}</span>
              <span class="text-xs font-semibold text-gray-900">{{ c.count }} ({{ c.pct }}%)</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div class="h-2 rounded-full" :style="{ width: c.pct + '%', background: barColors[i % barColors.length] }"></div>
            </div>
          </div>
        </div>
        <p v-else class="text-xs text-gray-400">No category data available.</p>
      </div>

      <!-- Asset Location Analytics -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Top Asset Locations</h3>
        <p class="text-xs text-gray-400 mb-4">Locations with the highest asset count.</p>
        <div v-if="dashboard.locations && dashboard.locations.length" class="space-y-3">
          <div v-for="(loc, i) in dashboard.locations" :key="loc.label">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700">{{ loc.label }}</span>
              <span class="text-xs font-semibold text-gray-900">{{ loc.count }}</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div class="h-2 rounded-full" :style="{ width: loc.pct + '%', background: locColors[i % locColors.length] }"></div>
            </div>
          </div>
        </div>
        <p v-else class="text-xs text-gray-400">No location data available.</p>
      </div>

      <!-- Assets with Highest Activity -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Most Active Assets</h3>
        <p class="text-xs text-gray-400 mb-4">Assets with the highest recorded activity.</p>
        <div v-if="dashboard.top_active_assets && dashboard.top_active_assets.length" class="space-y-3">
          <div v-for="(a, i) in dashboard.top_active_assets" :key="a.asset">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-700 truncate" style="max-width:70%;">{{ a.asset_name }}</span>
              <span class="text-xs font-semibold text-gray-900">{{ a.count }}</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div class="h-2 rounded-full" :style="{ width: a.pct + '%', background: actColors[i % actColors.length] }"></div>
            </div>
          </div>
        </div>
        <p v-else class="text-xs text-gray-400">No activity data available.</p>
      </div>
    </div>

    <!-- Recent Activity + Insights -->
    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Recent Asset Activity -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Recent Asset Activity</h3>
        </div>
        <div v-if="dashboard.recent_activities && dashboard.recent_activities.length" class="divide-y divide-gray-50">
          <div v-for="(a, idx) in dashboard.recent_activities" :key="idx"
            class="px-6 py-4 flex items-start justify-between cursor-pointer hover:bg-gray-50 transition-colors"
            @click="$router.push(`/assets-mgmt/asset/${a.asset}`)">
            <div class="flex-1 min-w-0">
              <p class="text-xs font-semibold text-gray-900 mb-0.5 truncate">{{ a.asset_name }} ({{ a.asset }})</p>
              <p class="text-xs text-gray-400 truncate">{{ a.subject }}</p>
            </div>
            <div class="flex-shrink-0 ml-4 text-right">
              <p class="text-xs text-gray-500">{{ formatDate(a.date) }}</p>
              <p class="text-xs text-gray-400">{{ a.user }}</p>
            </div>
          </div>
        </div>
        <div v-else class="px-6 py-8 text-center">
          <p class="text-xs text-gray-400">No recent activity recorded.</p>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="space-y-3">
        <h3 class="text-sm font-bold text-gray-900">Quick Links</h3>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-blue-300 transition-colors"
          @click="$router.push('/assets-mgmt/list')">
          <p class="text-xs font-bold text-gray-900 mb-1">Asset List</p>
          <p class="text-xs text-gray-500">View and manage all registered assets.</p>
        </div>
       
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 cursor-pointer hover:border-blue-300 transition-colors"
          @click="$router.push('/maintenance/list')">
          <p class="text-xs font-bold text-gray-900 mb-1">Maintenance Tasks</p>
          <p class="text-xs text-gray-500">View all maintenance task records.</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'

const barColors = ['#3b82f6', '#f59e0b', '#f97316', '#10b981', '#8b5cf6', '#ef4444']
const locColors = ['#6366f1', '#14b8a6', '#f43f5e', '#eab308', '#0ea5e9', '#a855f7']
const actColors = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed']

const dashboard = ref({
  total: 0,
  submitted: 0,
  in_maintenance: 0,
  scrapped: 0,
  draft: 0,
  categories: [],
  locations: [],
  top_active_assets: [],
  recent_activities: [],
})

createResource({
  url: 'rhohotel.rhocom_hotel.api.assets.get_asset_dashboard',
  auto: true,
  onSuccess(data) { dashboard.value = data }
})

function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>