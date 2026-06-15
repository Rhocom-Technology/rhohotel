<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Command center for weekly staff planning, preference collection, published shifts, swap approvals, attendance monitoring, and department coverage control.</p>
    </div>

    <!-- Roaster Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Roaster Control Center</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Plan the week, use AI Auto Assign, publish shifts, review staff preferences, manage swap requests, and monitor daily shift readiness.</p>

      <div class="flex items-center justify-center gap-2 flex-wrap">
        <button
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="goTo('shift-generator')">Shift Generator</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('calendar-view')">Calendar View</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('published-shifts')">Published Shifts</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('shift-preference')">Shift Preference</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('swap-requests')">Swap Requests</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goTo('attendance')">Attendance</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Published Shifts Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.publishedToday }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Weekly Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Good</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.weeklyCoverage }}%</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preference Submitted</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.preferenceSubmitted }} / {{ stats.preferenceTotal }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Swap Requests Pending</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.swapRequestsPending }}</p>
      </div>
    </div>

    <!-- Weekly Planning Health / Today's Shift Split / Attendance Readiness -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">

      <!-- Weekly Planning Health -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900">Weekly Planning Health</h3>
        <p class="text-xs text-gray-400 mb-4">{{ department }} &bull; {{ weekRange }}</p>

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
          <p class="text-xs text-gray-400">AI Auto Assign used staff preferences, availability, leave days, overtime rules, and weekend rotation.</p>
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

      <!-- Attendance Readiness -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900">Attendance Readiness</h3>
        <p class="text-xs text-gray-400 mb-4">Expected clock-ins vs confirmed staff readiness.</p>

        <div class="flex items-center gap-5">
          <div class="relative flex-shrink-0" style="width:96px;height:96px;">
            <svg viewBox="0 0 100 100" width="96" height="96">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" stroke-width="12" />
              <circle cx="50" cy="50" r="42" fill="none" stroke="#16a34a" stroke-width="12"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="dashOffset"
                transform="rotate(-90 50 50)" />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-lg font-bold text-gray-900">{{ attendance.readinessPct }}%</span>
            </div>
          </div>
          <div class="space-y-1.5">
            <p class="text-xs text-gray-600">{{ attendance.confirmed }} confirmed out of {{ attendance.expected }}</p>
            <p class="text-xs text-gray-600">{{ attendance.pending }} pending check-in</p>
            <p class="text-xs text-gray-600">{{ attendance.lateRisk }} late-risk alert</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Today's Published Shift Overview / Weekly Workflow / Roaster Alerts -->
    <div style="display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:12px;">

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
            </tbody>
          </table>
        </div>

        <button
          class="w-full mt-4 px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors"
          @click="goTo('published-shifts')">Open Published Shift List</button>
      </div>

      <!-- Weekly Workflow -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Weekly Workflow</h3>
        <div class="space-y-2.5">
          <div v-for="(step, idx) in workflowSteps" :key="idx"
            :class="['rounded-xl px-4 py-3', step.active ? 'bg-blue-50 border border-blue-100' : 'bg-green-50']">
            <p class="text-sm font-bold" :class="step.active ? 'text-blue-700' : 'text-green-700'">{{ step.title }}</p>
            <p class="text-xs mt-0.5" :class="step.active ? 'text-blue-600' : 'text-green-600'">{{ step.detail }}</p>
          </div>
          <div class="px-1 pt-1">
            <p class="text-sm font-bold text-purple-600">Next: Monitor Attendance</p>
            <p class="text-xs text-purple-500 mt-0.5">Track check-ins and late alerts</p>
          </div>
        </div>
      </div>

      <!-- Roaster Alerts -->
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Roaster Alerts</h3>
        <div class="space-y-3">
          <div v-for="(alert, idx) in roasterAlerts" :key="idx">
            <p class="text-sm font-bold text-gray-900">{{ alert.title }}</p>
            <p class="text-xs text-gray-400">{{ alert.detail }}</p>
          </div>
        </div>
        <button
          class="w-full mt-4 px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors"
          @click="goTo('swap-requests')">Open Swap Request List</button>
      </div>
    </div>

    <!-- Improved Shift Intelligence -->
    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">Improved Shift Intelligence</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">Dashboard now connects weekly generator, AI auto assign, staff preferences, published shift list, specific-date views, night shifts, swap reviews, and attendance readiness into one roaster control center.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const department = ref('Housekeeping')
const weekRange = ref('12 Apr - 18 Apr 2026')
const todayLabel = ref('Saturday, 18 Apr 2026')
const todayDate = ref('18 Apr 2026')

const stats = reactive({
  publishedToday: 18,
  weeklyCoverage: 92,
  preferenceSubmitted: 31,
  preferenceTotal: 42,
  swapRequestsPending: 7,
})

const preferenceCollectionPct = computed(() => Math.round((stats.preferenceSubmitted / stats.preferenceTotal) * 100))

const shiftSplit = reactive({
  morning: 9,
  afternoon: 6,
  night: 3,
})

const attendance = reactive({
  readinessPct: 88,
  confirmed: 16,
  expected: 18,
  pending: 2,
  lateRisk: 1,
})

const radius = 42
const circumference = 2 * Math.PI * radius
const dashOffset = computed(() => circumference * (1 - attendance.readinessPct / 100))

const deptOverview = reactive([
  { department: 'Housekeeping', morning: 9, afternoon: 6, night: 3, coverage: 'Covered' },
  { department: 'Front Desk', morning: 6, afternoon: 5, night: 2, coverage: 'Covered' },
  { department: 'POS / Restaurant', morning: 4, afternoon: 6, night: 1, coverage: 'Watch' },
  { department: 'Security', morning: 2, afternoon: 2, night: 8, coverage: 'Covered' },
])

const workflowSteps = reactive([
  { title: '1. Preferences Collected', detail: '31 submitted • 11 pending', active: false },
  { title: '2. AI Auto Assign Run', detail: 'Rules applied successfully', active: false },
  { title: '3. Manager Reviewed', detail: '3 conflicts resolved', active: false },
  { title: '4. Published', detail: '109 shifts published', active: true },
])

const roasterAlerts = reactive([
  { title: 'Pending Swap Reviews', detail: '7 swap requests require manager action.' },
  { title: 'Preference Deadline', detail: '11 staff have not submitted preferences.' },
  { title: 'Night Shift Coverage', detail: '3 night shift staff published today.' },
  { title: 'Late Check-in Risk', detail: '1 staff member flagged for late risk.' },
])

function coverageClass(value) {
  switch (value) {
    case 'Covered':
      return 'bg-green-100 text-green-600'
    case 'Watch':
      return 'bg-amber-100 text-amber-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function goTo(target) {
  // No backend connected — placeholder for navigation
}
</script>