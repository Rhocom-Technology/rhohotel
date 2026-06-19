<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">
        Command center for weekly staff planning, preference collection, published shifts, swap approvals, and department coverage control.
      </p>
    </div>

    <!-- Roaster Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Roaster Control Center</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">
        Plan the week, publish shifts, review staff preferences, and manage swap requests.
      </p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:220px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="loading"
              @click="changeWeek(-1)">&lsaquo;</button>

            <input
              v-model="weekStartInput"
              type="date"
              :disabled="loading"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-600 bg-white disabled:bg-gray-50"
            />

            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="loading"
              @click="changeWeek(1)">&rsaquo;</button>
          </div>
        </div>

      </div>

      <div class="flex items-center gap-2 flex-wrap mt-4">
        <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="goTo('/weekly-shift-generator')">
          Shift Generator
        </button>

        <button class="px-4 py-2.5 text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="goTo('/shift-list')">
          Published Shifts
        </button>

        <button class="px-4 py-2.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="goTo('/shift-preference-manager')">
          Shift Preference
        </button>

        <button class="px-4 py-2.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="goTo('/swap-requests')">
          Swap Requests
        </button>

        <button
          class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="loadDashboard"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- STATS -->
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Published Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.publishedToday }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Published This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.publishedThisWeek }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Weekly Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="coverageBadgeClass">{{ coverageLabel }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.weeklyCoverage }}%</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preference Submitted</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="preferencesBadgeClass">{{ preferencesBadgeLabel }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">
          {{ stats.preferenceSubmitted }} / {{ stats.preferenceTotal }}
        </p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Swap Requests Pending</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="stats.swapRequestsPending > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'">{{ stats.swapRequestsPending > 0 ? 'Review' : 'Clear' }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.swapRequestsPending }}</p>
      </div>
    </div>

    <!-- SHIFT SPLIT -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- TODAY -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-3">Today's Shift Split</h3>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
          <div
            v-for="(count, name) in shiftSplit"
            :key="name"
            class="rounded-xl px-3 py-4 text-center"
            :style="getShiftCardStyle(name)"
          >
            <p class="text-3xl font-bold" :style="{ color: getShiftTextColor(name) }">{{ count }}</p>
            <p class="text-xs font-semibold mt-2" :style="{ color: getShiftTextColor(name) }">{{ name }}</p>
          </div>
        </div>
      </div>

      <!-- WEEK -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-3">This Week's Shift Split</h3>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
          <div
            v-for="(count, name) in weekShiftSplit"
            :key="name"
            class="rounded-xl px-3 py-4 text-center"
            :style="getShiftCardStyle(name)"
          >
            <p class="text-3xl font-bold" :style="{ color: getShiftTextColor(name) }">{{ count }}</p>
            <p class="text-xs font-semibold mt-2" :style="{ color: getShiftTextColor(name) }">{{ name }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- DEPT TODAY -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Today's Published Shift Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">All departments and their active shift types for today.</p>
      </div>

      <div class="px-5 py-4 overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Department</th>
              <th v-for="name in shiftTypeNames" :key="name" class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">
                {{ name }}
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in deptOverview" :key="row.department" class="border-b border-gray-100">
              <td class="px-3 py-2.5 text-xs font-bold text-gray-900">{{ row.department }}</td>
              <td v-for="name in shiftTypeNames" :key="name" class="px-3 py-2.5 text-xs">
                <span v-if="row.shift_types?.includes(name)" class="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">1</span>
                <span v-else class="text-gray-300">&mdash;</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- WEEK DEPT -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Weekly Department Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">Staff with published shift assignments per department for each day of the selected week.</p>
      </div>

      <div class="px-5 py-4 overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Department</th>
              <th v-for="d in weekDates" :key="d" class="text-center px-3 py-2.5 text-xs font-semibold text-gray-500">
                {{ shortDayLabel(d) }}
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in deptOverviewWeek" :key="row.department" class="border-b border-gray-100">
              <td class="px-3 py-2.5 text-xs font-bold text-gray-900">{{ row.department }}</td>
              <td v-for="d in weekDates" :key="d" class="text-center px-3 py-2.5 text-xs">
                <span v-if="row.days[d]?.length" class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">{{ row.days[d].length }}</span>
                <span v-else class="text-gray-300">&mdash;</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- WEEKLY DEPARTMENT SHIFT COUNTS -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Weekly Department Shift Counts</h3>
        <p class="text-xs text-gray-400 mt-0.5">Number of published shifts per department for each day of the selected week.</p>
      </div>

      <div class="px-5 py-4 overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Department</th>
              <th v-for="d in weekDates" :key="`shift-count-${d}`" class="text-center px-3 py-2.5 text-xs font-semibold text-gray-500">
                {{ shortDayLabel(d) }}
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in deptShiftCountWeek" :key="`shift-count-row-${row.department}`" class="border-b border-gray-100">
              <td class="px-3 py-2.5 text-xs font-bold text-gray-900">{{ row.department }}</td>
              <td v-for="d in weekDates" :key="`shift-count-cell-${row.department}-${d}`" class="text-center px-3 py-2.5 text-xs">
                <span v-if="row.days[d]" class="px-2 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-700 rounded-full">{{ row.days[d] }}</span>
                <span v-else class="text-gray-300">&mdash;</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Roaster Intelligence -->
    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">Roaster Intelligence</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">Use the Shift Generator for AI Auto Assign and Shift Assignment Tool workflows, while this dashboard tracks weekly coverage, preferences, and swap requests.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { callMethod } from '@/lib/api'

const router = useRouter()
const loading = ref(false)

const stats = reactive({
  publishedToday: 0,
  publishedThisWeek: 0,
  weeklyCoverage: 0,
  preferenceSubmitted: 0,
  preferenceTotal: 0,
  swapRequestsPending: 0,
})

const shiftSplit = reactive({})
const weekShiftSplit = reactive({})
const deptOverview = ref([])
const deptOverviewWeek = ref([])
const deptShiftCountWeek = ref([])
const weekDates = ref([])
const shiftTypeNames = ref([])

// Color mapping for each shift type
// Each shift type gets: background color, text color
const shiftColorMap = {
  'Day Shift': {
    bg: '#d1fae5',    // Light green
    text: '#065f46'   // Dark green
  },
  'Evening Shift': {
    bg: '#fef3c7',    // Light amber
    text: '#92400e'   // Dark amber
  },
  'Night Shift': {
    bg: '#fee2e2',    // Light red
    text: '#991b1b'   // Dark red
  },
  'Good': {
    bg: '#dbeafe',    // Light blue
    text: '#1e40af'   // Dark blue
  },
  'Morning': {
    bg: '#fce7f3',    // Light pink
    text: '#9d174d'   // Dark pink
  },
  'Afternoon': {
    bg: '#fef3c7',    // Light amber
    text: '#92400e'   // Dark amber
  },
  'Weekend': {
    bg: '#ede9fe',    // Light purple
    text: '#5b21b6'   // Dark purple
  },
  'Holiday': {
    bg: '#fce4ec',    // Light red/pink
    text: '#b71c1c'   // Dark red
  },
  'On-Call': {
    bg: '#f3e8ff',    // Light violet
    text: '#5b21b6'   // Dark violet
  },
  'Swing': {
    bg: '#fce4ec',    // Light red/pink
    text: '#b71c1c'   // Dark red
  },
  'Split': {
    bg: '#e8f5e9',    // Light green
    text: '#2e7d32'   // Dark green
  },
  'Rotation': {
    bg: '#fff3e0',    // Light orange
    text: '#e65100'   // Dark orange
  },
  'Float': {
    bg: '#e3f2fd',    // Light blue
    text: '#0d47a1'   // Dark blue
  },
}

// Default colors for any shift type not defined above
const defaultColors = {
  bg: '#f3f4f6',     // Light gray
  text: '#374151'    // Dark gray
}

function getShiftCardStyle(shiftName) {
  const colors = shiftColorMap[shiftName] || defaultColors
  return {
    backgroundColor: colors.bg
  }
}

function getShiftTextColor(shiftName) {
  const colors = shiftColorMap[shiftName] || defaultColors
  return colors.text
}

function isoDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfWeek(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + diff)
  return d
}

const weekStart = ref(startOfWeek(new Date()))

const weekStartInput = computed({
  get: () => isoDate(weekStart.value),
  set: (v) => weekStart.value = startOfWeek(new Date(v))
})

const coverageBadgeClass = computed(() => {
  const v = Number(stats.weeklyCoverage || 0)
  if (v >= 80) return 'bg-green-100 text-green-600'
  if (v >= 50) return 'bg-amber-100 text-amber-600'
  return 'bg-red-100 text-red-600'
})

const coverageLabel = computed(() => {
  const v = Number(stats.weeklyCoverage || 0)
  if (v >= 80) return 'Good'
  if (v >= 50) return 'Watch'
  return 'Low'
})

const preferencesBadgeClass = computed(() => {
  if (!stats.preferenceTotal) return 'bg-gray-100 text-gray-500'
  const ratio = stats.preferenceSubmitted / stats.preferenceTotal
  if (ratio >= 0.8) return 'bg-green-100 text-green-600'
  if (ratio >= 0.5) return 'bg-amber-100 text-amber-600'
  return 'bg-red-100 text-red-600'
})

const preferencesBadgeLabel = computed(() => {
  if (!stats.preferenceTotal) return 'None'
  const ratio = stats.preferenceSubmitted / stats.preferenceTotal
  if (ratio >= 0.8) return 'Good'
  if (ratio >= 0.5) return 'Partial'
  return 'Low'
})

function changeWeek(delta) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + delta * 7)
  weekStart.value = startOfWeek(d)
  loadDashboard()
}

async function loadDashboard() {
  loading.value = true
  try {
    const res = await callMethod(
      'rhohotel.rhocom_hotel.api.staff_roaster_dashboard.get_dashboard',
      { week_start: isoDate(weekStart.value) }
    )

    Object.assign(stats, res.stats || {})
    Object.assign(shiftSplit, res.shiftSplitToday || {})
    Object.assign(weekShiftSplit, res.shiftSplitWeek || {})

    deptOverview.value = res.deptOverview || []
    deptOverviewWeek.value = res.deptOverviewWeek || []
    deptShiftCountWeek.value = res.deptShiftCountWeek || []
    weekDates.value = res.week_dates || []
    shiftTypeNames.value = res.shift_type_names || []

  } finally {
    loading.value = false
  }
}

function shortDayLabel(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'short' })
}

function coverageClass(v) {
  if (v === 'Covered') return 'bg-green-100 text-green-600'
  if (v === 'Watch') return 'bg-amber-100 text-amber-600'
  return 'bg-red-100 text-red-600'
}

function goTo(path) {
  router.push(path)
}

loadDashboard()
</script>