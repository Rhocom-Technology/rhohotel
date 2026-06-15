<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">This page is visible only to the logged-in staff member. Staff can submit preferred shifts for the week, but cannot enter preferences for another staff member.</p>
    </div>

    <!-- Preference Submission Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Preference Submission Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Preferences guide the department manager during weekly shift planning. Final shift allocation remains subject to operational coverage and approval.</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Logged-in Staff</p>
          <div class="flex items-center justify-between gap-2 px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-medium">
            <span>{{ staffName }}</span>
            <span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Self</span>
          </div>
        </div>
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <div class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-medium">
            {{ department }}
          </div>
        </div>
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <input v-model="weekStarting" type="text" readonly
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
        </div>

        <div class="flex-1"></div>

        <div class="flex items-center gap-2 flex-wrap">
          <button
            class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="resetPreferences">Reset</button>
          <button
            class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="saveDraft">Save Draft</button>
          <button
            class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            @click="submitPreference">Submit Preference</button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preference Status</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Not Sent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">Draft</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preferred Work Days</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ preferredWorkDays }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unavailable Days</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ unavailableDays }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Manager Visibility</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Private</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">After Submit</p>
      </div>
    </div>

    <!-- Weekly Shift Preference Table -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="text-sm font-bold text-gray-900">Weekly Shift Preference - {{ staffName }}</h3>
        <p class="text-xs text-gray-400">Only current staff profile is editable</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1100px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:170px;">Preference Item</th>
              <th v-for="day in days" :key="day.label" class="text-left px-3 py-2.5" style="min-width:150px;">
                <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                <p class="text-xs text-gray-400">{{ day.date }}</p>
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Preferred Shift -->
            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Preferred Shift</p>
                <p class="text-xs text-gray-400">Select one option per day</p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.label].preferredShift"
                    :class="['w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200 cursor-pointer', shiftClass(preferences[day.label].preferredShift)]"
                  >
                    <option v-for="opt in preferredShiftOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                  <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" :class="chevronClass(preferences[day.label].preferredShift)" />
                </div>
              </td>
            </tr>

            <!-- Alternative Shift -->
            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Alternative Shift</p>
                <p class="text-xs text-gray-400">Optional backup preference</p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.label].alternativeShift"
                    :class="['w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200 cursor-pointer', altShiftClass(preferences[day.label].alternativeShift)]"
                  >
                    <option v-for="opt in alternativeShiftOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                  <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" :class="altChevronClass(preferences[day.label].alternativeShift)" />
                </div>
              </td>
            </tr>

            <!-- Availability -->
            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Availability</p>
                <p class="text-xs text-gray-400">Available / unavailable</p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.label].availability"
                    :class="['w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200 cursor-pointer', availabilityClass(preferences[day.label].availability)]"
                  >
                    <option v-for="opt in availabilityOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                  <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" :class="availabilityChevronClass(preferences[day.label].availability)" />
                </div>
              </td>
            </tr>

            <!-- Daily Notes -->
            <tr>
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Daily Notes</p>
                <p class="text-xs text-gray-400">Optional reason / guidance to manager</p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-3 py-3 align-top">
                <input
                  v-model="preferences[day.label].note"
                  type="text"
                  :placeholder="notePlaceholders[day.label]"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-6 flex-wrap mt-5 pt-4 border-t border-gray-100">
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#dbeafe;"></span>
          <span class="text-xs text-gray-500">Morning</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#fef3c7;"></span>
          <span class="text-xs text-gray-500">Afternoon</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#e0e7ff;"></span>
          <span class="text-xs text-gray-500">Night</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded border border-gray-300" style="background:#f9fafb;"></span>
          <span class="text-xs text-gray-500">Off</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#fee2e2;"></span>
          <span class="text-xs text-gray-500">Leave / Unavailable</span>
        </div>
        <div class="flex-1"></div>
        <p class="text-xs text-gray-400">Preferences are guidance only, not final schedule</p>
      </div>
    </div>

    <!-- Access Rule / Manager Guidance -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Access Rule</h3>
        <div class="space-y-3">
          <div v-for="(rule, idx) in accessRules" :key="idx" class="flex items-start gap-3">
            <span class="w-4 h-4 mt-0.5 rounded flex-shrink-0" style="background:#16a34a;"></span>
            <p class="text-xs text-gray-600">{{ rule }}</p>
          </div>
        </div>
      </div>
      <div class="rounded-xl border px-6 py-5" style="background:#f5f3ff; border-color:#e9d5ff;">
        <h3 class="text-sm font-bold mb-3" style="color:#7c3aed;">How It Guides the Department Manager</h3>
        <div class="space-y-2">
          <p v-for="(line, idx) in managerGuidance" :key="idx" class="text-xs" style="color:#8b5cf6;">{{ line }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const staffName = ref('Mary Bello')
const department = ref('Housekeeping')
const weekStarting = ref('Sunday, 12 Apr 2026')

const days = [
  { label: 'Sunday', date: '12 Apr' },
  { label: 'Monday', date: '13 Apr' },
  { label: 'Tuesday', date: '14 Apr' },
  { label: 'Wednesday', date: '15 Apr' },
  { label: 'Thursday', date: '16 Apr' },
  { label: 'Friday', date: '17 Apr' },
  { label: 'Saturday', date: '18 Apr' },
]

const preferredShiftOptions = ['Morning', 'Afternoon', 'Night', 'OFF', 'Leave']
const alternativeShiftOptions = ['Any Shift', 'Morning', 'Afternoon', 'Night', 'N/A']
const availabilityOptions = ['Available', 'Unavailable']

const preferences = reactive({
  Sunday:    { preferredShift: 'OFF',       alternativeShift: 'Any Shift', availability: 'Available',   note: '' },
  Monday:    { preferredShift: 'Morning',   alternativeShift: 'Afternoon', availability: 'Available',   note: '' },
  Tuesday:   { preferredShift: 'Morning',   alternativeShift: 'Any Shift', availability: 'Available',   note: '' },
  Wednesday: { preferredShift: 'Afternoon', alternativeShift: 'Any Shift', availability: 'Available',   note: '' },
  Thursday:  { preferredShift: 'Morning',   alternativeShift: 'Afternoon', availability: 'Available',   note: '' },
  Friday:    { preferredShift: 'Morning',   alternativeShift: 'Any Shift', availability: 'Available',   note: '' },
  Saturday:  { preferredShift: 'Leave',     alternativeShift: 'N/A',       availability: 'Unavailable', note: '' },
})

const notePlaceholders = {
  Sunday: 'Can work if needed',
  Monday: 'Prefer morning',
  Tuesday: 'School run',
  Wednesday: 'Prefer after noon',
  Thursday: 'Morning best',
  Friday: 'Flexible',
  Saturday: 'Family event',
}

const preferredWorkDays = ref(5)
const unavailableDays = ref(1)

const accessRules = [
  'Staff can only edit their own preference record.',
  'Department and staff name are locked from login profile.',
  'Manager sees submitted preferences during weekly generator planning.',
]

const managerGuidance = [
  'Submitted preferences feed into the Weekly Shift Generator and AI Auto Assign rules.',
  'Manager can still override preferences based on coverage, fairness, leave, and overtime rules.',
  'Audit trail records when the staff submitted or edited the preference.',
]

function shiftClass(value) {
  switch (value) {
    case 'Morning':
      return 'bg-blue-100 text-blue-700 border-blue-200'
    case 'Afternoon':
      return 'bg-amber-100 text-amber-700 border-amber-200'
    case 'Night':
      return 'bg-indigo-100 text-indigo-700 border-indigo-200'
    case 'Leave':
      return 'bg-red-100 text-red-700 border-red-200'
    default:
      return 'bg-gray-50 text-gray-500 border-gray-200'
  }
}

function chevronClass(value) {
  switch (value) {
    case 'Morning':
      return 'text-blue-500'
    case 'Afternoon':
      return 'text-amber-500'
    case 'Night':
      return 'text-indigo-500'
    case 'Leave':
      return 'text-red-500'
    default:
      return 'text-gray-400'
  }
}

function altShiftClass(value) {
  switch (value) {
    case 'Morning':
      return 'bg-blue-100 text-blue-700 border-blue-200'
    case 'Afternoon':
      return 'bg-amber-100 text-amber-700 border-amber-200'
    case 'Night':
      return 'bg-indigo-100 text-indigo-700 border-indigo-200'
    case 'Any Shift':
      return 'bg-white text-gray-700 border-gray-200'
    default:
      return 'bg-gray-50 text-gray-500 border-gray-200'
  }
}

function altChevronClass(value) {
  switch (value) {
    case 'Morning':
      return 'text-blue-500'
    case 'Afternoon':
      return 'text-amber-500'
    case 'Night':
      return 'text-indigo-500'
    default:
      return 'text-gray-400'
  }
}

function availabilityClass(value) {
  return value === 'Available'
    ? 'bg-green-100 text-green-700 border-green-200'
    : 'bg-red-100 text-red-700 border-red-200'
}

function availabilityChevronClass(value) {
  return value === 'Available' ? 'text-green-500' : 'text-red-500'
}

function resetPreferences() {
  // No backend connected — placeholder for reset action
}

function saveDraft() {
  // No backend connected — placeholder for save draft action
}

function submitPreference() {
  // No backend connected — placeholder for submit preference action
}
</script>