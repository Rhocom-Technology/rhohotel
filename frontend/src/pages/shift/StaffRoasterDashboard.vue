<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Command center for weekly staff planning, preference collection, published shifts, swap approvals, and department coverage control.</p>
    </div>

    <!-- Roaster Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Roaster Control Center</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Plan the week, use AI Auto Assign, publish shifts, review staff preferences, and manage swap requests.</p>

      <div class="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div style="min-width:220px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="loading"
              @click="changeWeek(-1)">&lsaquo;</button>
            <input v-model="weekStartInput" type="date" :disabled="loading"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white disabled:bg-gray-50" />
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="loading"
              @click="changeWeek(1)">&rsaquo;</button>
          </div>
        </div>
        <button
          class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          :disabled="loading"
          @click="loadDashboard">Refresh</button>
      </div>

      <div class="flex items-center justify-center gap-2 flex-wrap">
        <button
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="goTo('/weekly-shift-generator')">Shift Generator</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('/shift-list')">Published Shifts</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('/shift-preference-manager')">Shift Preference</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('/swap-requests')">Swap Requests</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Published Shifts Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.publishedToday }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Weekly Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="coverageBadgeClass">{{ coverageBadgeLabel }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.weeklyCoverage }}%</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preference Submitted</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : `${stats.preferenceSubmitted} / ${stats.preferenceTotal}` }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Swap Requests Pending</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.swapRequestsPending }}</p>
      </div>
    </div>

    <!-- Weekly Planning Health / Today's Shift Split -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- Weekly Planning Health -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900">Weekly Planning Health</h3>
        <p class="text-xs text-gray-400 mb-4">{{ weekLabel }}</p>

        <div class="mb-4">
          <div class="w-full h-2 rounded-full bg-gray-100 overflow-hidden mb-2">
            <div class="h-full rounded-full bg-green-500" :style="{ width: stats.weeklyCoverage + '%' }"></div>
          </div>
          <div class="flex items-center justify-between">
            <p class="text-xs text-gray-500">Published coverage</p>
            <p class="text-xs font-bold text-gray-700">{{ stats.weeklyCoverage }}%</p>
          </div>
        </div>

        <div>
          <div class="w-full h-2 rounded-full bg-gray-100 overflow-hidden mb-2">
            <div class="h-full rounded-full bg-amber-500" :style="{ width: preferenceCollectionPct + '%' }"></div>
          </div>
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500">Preference collection</p>
            <p class="text-xs font-bold text-gray-700">{{ preferenceCollectionPct }}%</p>
          </div>
          <p class="text-xs text-gray-400">AI Auto Assign uses staff preferences, availability, leave days, overtime rules, and weekend rotation.</p>
        </div>
      </div>

      <!-- Today's Shift Split -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900">Today&rsquo;s Shift Split</h3>
        <p class="text-xs text-gray-400 mb-4">{{ todayLabel }} &bull; published shifts only</p>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
          <div class="rounded-xl px-3 py-4 text-center" style="background:#dbeafe;">
            <p class="text-3xl font-bold text-blue-700">{{ shiftSplit.morning }}</p>
            <p class="text-xs font-semibold text-blue-700 mt-2">Morning</p>
          </div>
          <div class="rounded-xl px-3 py-4 text-center" style="background:#fef3c7;">
            <p class="text-3xl font-bold text-amber-700">{{ shiftSplit.afternoon }}</p>
            <p class="text-xs font-semibold text-amber-700 mt-2">Afternoon</p>
          </div>
          <div class="rounded-xl px-3 py-4 text-center" style="background:#e0e7ff;">
            <p class="text-3xl font-bold text-indigo-700">{{ shiftSplit.night }}</p>
            <p class="text-xs font-semibold text-indigo-700 mt-2">Night</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Today's Published Shift Overview / Roaster Alerts -->
    <div style="display:grid;grid-template-columns:1.6fr 1fr;gap:12px;">

      <!-- Today's Published Shift Overview -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 class="text-sm font-bold text-gray-900">Today&rsquo;s Published Shift Overview</h3>
          <p class="text-xs text-gray-400">{{ todayDate }}</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr class="bg-gray-50">
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Department</th>
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Morning</th>
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Afternoon</th>
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Night</th>
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-r-lg">Coverage</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in deptOverview" :key="row.department" class="border-b border-gray-100">
                <td class="px-3 py-3.5 text-sm font-bold text-gray-900">{{ row.department }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-600">{{ row.morning }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-600">{{ row.afternoon }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-600">{{ row.night }}</td>
                <td class="px-3 py-3.5">
                  <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', coverageClass(row.coverage)]">{{ row.coverage }}</span>
                </td>
              </tr>
              <tr v-if="!deptOverview.length">
                <td colspan="5" class="px-3 py-6 text-center text-xs text-gray-400">No published shifts today.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <button
          class="w-full mt-4 px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors"
          @click="goTo('/shift-list')">Open Published Shift List</button>
      </div>

      <!-- Roaster Alerts -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Roaster Alerts</h3>
        <div class="space-y-3">
          <div v-if="stats.swapRequestsPending">
            <p class="text-sm font-bold text-gray-900">Pending Swap Reviews</p>
            <p class="text-xs text-gray-400">{{ stats.swapRequestsPending }} swap request(s) require manager action.</p>
          </div>
          <div v-if="preferencePending > 0">
            <p class="text-sm font-bold text-gray-900">Preference Deadline</p>
            <p class="text-xs text-gray-400">{{ preferencePending }} staff have not submitted preferences for this week.</p>
          </div>
          <div v-if="shiftSplit.night">
            <p class="text-sm font-bold text-gray-900">Night Shift Coverage</p>
            <p class="text-xs text-gray-400">{{ shiftSplit.night }} night shift staff published today.</p>
          </div>
          <div v-if="!stats.swapRequestsPending && preferencePending === 0 && !shiftSplit.night">
            <p class="text-xs text-gray-400">No alerts right now.</p>
          </div>
        </div>
        <button
          class="w-full mt-4 px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors"
          @click="goTo('/swap-requests')">Open Swap Request List</button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { callMethod } from '@/lib/api'

const router = useRouter()

const loading = ref(false)

function isoDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfWeek(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day // Monday-based week
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

const weekStart = ref(startOfWeek(new Date()))
const weekStartInput = computed({
  get: () => isoDate(weekStart.value),
  set: (val) => {
    if (!val) return
    weekStart.value = startOfWeek(new Date(val))
  },
})

function changeWeek(deltaWeeks) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + deltaWeeks * 7)
  weekStart.value = startOfWeek(d)
  loadDashboard()
}

const weekLabel = ref('')
const todayLabel = ref('')
const todayDate = ref('')

const stats = reactive({
  publishedToday: 0,
  weeklyCoverage: 0,
  preferenceSubmitted: 0,
  preferenceTotal: 0,
  swapRequestsPending: 0,
})

const shiftSplit = reactive({ morning: 0, afternoon: 0, night: 0 })
const deptOverview = ref([])

const preferenceCollectionPct = computed(() => {
  if (!stats.preferenceTotal) return 0
  return Math.round((stats.preferenceSubmitted / stats.preferenceTotal) * 100)
})

const preferencePending = computed(() => Math.max(0, stats.preferenceTotal - stats.preferenceSubmitted))

const coverageBadgeLabel = computed(() => {
  if (stats.weeklyCoverage >= 85) return 'Good'
  if (stats.weeklyCoverage >= 60) return 'Watch'
  return 'Gap'
})

const coverageBadgeClass = computed(() => {
  if (stats.weeklyCoverage >= 85) return 'bg-green-100 text-green-600'
  if (stats.weeklyCoverage >= 60) return 'bg-amber-100 text-amber-600'
  return 'bg-red-100 text-red-600'
})

async function loadDashboard() {
  loading.value = true
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.staff_roaster_dashboard.get_dashboard', {
      week_start: isoDate(weekStart.value),
    })

    weekLabel.value = result?.week_label || ''
    todayLabel.value = result?.today_label || ''
    todayDate.value = result?.today_date || ''

    Object.assign(stats, result?.stats || {})
    Object.assign(shiftSplit, result?.shiftSplit || {})
    deptOverview.value = result?.deptOverview || []
  } catch (err) {
    // Leave previous values in place on failure; the page still renders.
  } finally {
    loading.value = false
  }
}

function coverageClass(value) {
  switch (value) {
    case 'Covered':
      return 'bg-green-100 text-green-600'
    case 'Watch':
      return 'bg-amber-100 text-amber-600'
    case 'Gap':
      return 'bg-red-100 text-red-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function goTo(target) {
  if (!target) return
  router.push(target)
}

loadDashboard()
</script>