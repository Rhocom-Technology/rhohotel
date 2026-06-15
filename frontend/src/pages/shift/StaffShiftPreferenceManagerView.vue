<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Department managers can view staff-submitted weekly preferences, compare availability, identify gaps, and send preferences into the Weekly Shift Generator.</p>
    </div>

    <!-- Preference Review Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Preference Review Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Review only submitted preferences for the selected department and week. Managers cannot edit staff submissions, but may use them for planning.</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <input v-model="weekStarting" type="text" readonly
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
        </div>
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Submission Status</p>
          <select v-model="submissionStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="opt in submissionStatusOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>
        <div class="flex-1" style="min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">&nbsp;</p>
          <input v-model="searchText" type="text" placeholder="Search staff name..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <div class="flex-1"></div>

        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="resetFilters">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="printSummary">Print</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Department Staff</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.departmentStaff }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Submitted Preferences</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.submittedPreferences }} / {{ stats.departmentStaff }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unavailable Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.unavailableRequests }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Most Preferred Shift</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">{{ stats.mostPreferredPct }}%</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.mostPreferredShift }}</p>
      </div>
    </div>

    <!-- Staff Weekly Preference Summary -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="text-sm font-bold text-gray-900">Staff Weekly Preference Summary</h3>
        <p class="text-xs text-gray-400">Manager review &bull; read-only staff submissions</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1200px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:170px;">Staff / Role</th>
              <th v-for="day in days" :key="day.label" class="text-left px-3 py-2.5" style="min-width:130px;">
                <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                <p class="text-xs text-gray-400">{{ day.date }}</p>
              </th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-r-lg" style="min-width:90px;">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="staff in staffList" :key="staff.id" class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                <p class="text-xs text-gray-400">{{ staff.role }} &bull; {{ staff.area }}</p>
              </td>

              <template v-if="staff.submitted">
                <td v-for="day in days" :key="day.label" class="px-3 py-3.5 align-top">
                  <span :class="['inline-flex w-full justify-center px-3 py-1.5 text-xs font-semibold rounded-lg', shiftClass(staff.shifts[day.label])]">{{ staff.shifts[day.label] }}</span>
                </td>
              </template>
              <template v-else>
                <td :colspan="days.length" class="px-3 py-3.5 align-top">
                  <div class="w-full text-center px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:#fef3c7; color:#b45309;">Preference not submitted yet</div>
                </td>
              </template>

              <td class="px-3 py-3.5 align-top">
                <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', staff.submitted ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600']">{{ staff.submitted ? 'Sent' : 'Pending' }}</span>
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
          <span class="text-xs text-gray-500">Afternoon / Pending</span>
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
        <p class="text-xs text-gray-400">Read-only manager view</p>
      </div>
    </div>

    <!-- Manager Planning Guidance -->
    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">Manager Planning Guidance</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">Submitted preferences are passed into the Weekly Generator and AI Auto Assign engine, but final roaster decisions remain controlled by manager coverage rules, fairness, leave, and overtime limits.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const departmentOptions = ['Housekeeping', 'Front Desk', 'Restaurant', 'Maintenance', 'Security']
const department = ref('Housekeeping')
const weekStarting = ref('Sunday, 12 Apr 2026')

const submissionStatusOptions = ['All Staff', 'Submitted', 'Pending']
const submissionStatus = ref('All Staff')

const searchText = ref('')

const stats = reactive({
  departmentStaff: 42,
  submittedPreferences: 31,
  unavailableRequests: 8,
  mostPreferredShift: 'Morning',
  mostPreferredPct: 64,
})

const days = [
  { label: 'Sunday', date: '12 Apr' },
  { label: 'Monday', date: '13 Apr' },
  { label: 'Tuesday', date: '14 Apr' },
  { label: 'Wednesday', date: '15 Apr' },
  { label: 'Thursday', date: '16 Apr' },
  { label: 'Friday', date: '17 Apr' },
  { label: 'Saturday', date: '18 Apr' },
]

const staffList = reactive([
  {
    id: 1,
    name: 'Mary Bello',
    role: 'Room Attendant',
    area: 'Floor 3',
    submitted: true,
    shifts: { Sunday: 'OFF', Monday: 'Morning', Tuesday: 'Morning', Wednesday: 'Afternoon', Thursday: 'Morning', Friday: 'Morning', Saturday: 'Leave' },
  },
  {
    id: 2,
    name: 'Blessing Eze',
    role: 'Room Attendant',
    area: 'Floor 2',
    submitted: true,
    shifts: { Sunday: 'OFF', Monday: 'Morning', Tuesday: 'Morning', Wednesday: 'Morning', Thursday: 'Morning', Friday: 'OFF', Saturday: 'Morning' },
  },
  {
    id: 3,
    name: 'Aisha Lawal',
    role: 'Supervisor',
    area: 'All Floors',
    submitted: true,
    shifts: { Sunday: 'Supervisor', Monday: 'Supervisor', Tuesday: 'Supervisor', Wednesday: 'Supervisor', Thursday: 'Supervisor', Friday: 'Supervisor', Saturday: 'Supervisor' },
  },
  {
    id: 4,
    name: 'John Ude',
    role: 'Laundry Attendant',
    area: 'Laundry',
    submitted: true,
    shifts: { Sunday: 'Morning', Monday: 'OFF', Tuesday: 'Morning', Wednesday: 'Morning', Thursday: 'OFF', Friday: 'Morning', Saturday: 'Afternoon' },
  },
  {
    id: 5,
    name: 'Rita James',
    role: 'Room Attendant',
    area: 'Floor 4',
    submitted: true,
    shifts: { Sunday: 'Afternoon', Monday: 'Morning', Tuesday: 'OFF', Wednesday: 'Morning', Thursday: 'Morning', Friday: 'OFF', Saturday: 'Morning' },
  },
  {
    id: 6,
    name: 'Tina Okafor',
    role: 'Public Area Cleaner',
    area: 'Lobby',
    submitted: false,
    shifts: {},
  },
  {
    id: 7,
    name: 'Kemi Yusuf',
    role: 'Room Attendant',
    area: 'Floor 5',
    submitted: false,
    shifts: {},
  },
])

function shiftClass(value) {
  switch (value) {
    case 'Morning':
      return 'bg-blue-100 text-blue-700'
    case 'Afternoon':
      return 'bg-amber-100 text-amber-700'
    case 'Night':
      return 'bg-indigo-100 text-indigo-700'
    case 'Supervisor':
      return 'bg-cyan-100 text-cyan-700'
    case 'Leave':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-50 text-gray-500'
  }
}

function resetFilters() {
  department.value = 'Housekeeping'
  weekStarting.value = 'Sunday, 12 Apr 2026'
  submissionStatus.value = 'All Staff'
  searchText.value = ''
}

function printSummary() {
  // No backend connected — placeholder for print action
}
</script>