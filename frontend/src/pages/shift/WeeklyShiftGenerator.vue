<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Assign weekly shifts manually for every staff member in the selected department, or use AI Auto Assign to generate a balanced roaster.</p>
    </div>

    <!-- Weekly Assignment Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Weekly Assignment Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Selected department staff are listed below. Department managers can assign Morning, Afternoon, Night, Off, or Leave for each day.</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <input v-model="weekStarting" type="text" readonly
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
        </div>

        <div class="flex-1"></div>

        <div class="flex items-center gap-2 flex-wrap">
          <button
            class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="cancelChanges">Cancel</button>
          <button
            class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="saveDraft">Save Draft</button>
          <button
            class="px-4 py-2.5 text-xs font-semibold text-white rounded-lg hover:opacity-90 transition-opacity"
            style="background: linear-gradient(90deg, #8b5cf6, #6366f1);"
            @click="aiAutoAssign">AI Auto Assign</button>
          <button
            class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            @click="publishRoster">Publish</button>
        </div>
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
          <p class="text-xs text-gray-400">Assigned Slots</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Draft</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ assignedSlots }} / {{ totalSlots }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Coverage Level</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Good</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ coverageLevel }}%</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Conflict Alerts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.conflictAlerts }}</p>
      </div>
    </div>

    <!-- Weekly Manual Assignment Table -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="text-sm font-bold text-gray-900">All {{ department }} Staff - Weekly Manual Assignment</h3>
        <p class="text-xs text-gray-400">Assign shifts manually per day &bull; Sunday to Saturday</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1100px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:180px;">Staff / Role</th>
              <th v-for="day in days" :key="day.label" class="text-left px-3 py-2.5" style="min-width:140px;">
                <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                <p class="text-xs text-gray-400">{{ day.date }}</p>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="staff in staffList" :key="staff.id" class="border-b border-gray-100">
              <td class="px-3 py-3 align-top">
                <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                <p class="text-xs text-gray-400">{{ staff.role }} &bull; {{ staff.area }}</p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-3 py-2.5 align-top">
                <div class="relative">
                  <select
                    v-model="staff.shifts[day.label]"
                    :class="['w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200 cursor-pointer', shiftClass(staff.shifts[day.label])]"
                  >
                    <option v-for="opt in shiftOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                  <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" :class="chevronClass(staff.shifts[day.label])" />
                </div>
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
          <span class="w-4 h-4 rounded" style="background:#cffafe;"></span>
          <span class="text-xs text-gray-500">Supervisor</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded border border-gray-300" style="background:#f9fafb;"></span>
          <span class="text-xs text-gray-500">Off</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#fee2e2;"></span>
          <span class="text-xs text-gray-500">Leave / Alert</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#e0e7ff;"></span>
          <span class="text-xs text-gray-500">Night</span>
        </div>
        <div class="flex-1"></div>
        <p class="text-xs text-gray-400">Each daily cell is manually selectable</p>
      </div>
    </div>

    <!-- AI Auto Assign Intelligence -->
    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">AI Auto Assign Intelligence</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">Uses staff availability, leave days, previous shifts, overtime rules, weekend rotation, department coverage rules, and conflict detection to auto-fill the weekly roaster.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const departmentOptions = ['Housekeeping', 'Front Desk', 'Restaurant', 'Maintenance', 'Security']
const department = ref('Housekeeping')
const weekStarting = ref('Sunday, 12 Apr 2026')

const shiftOptions = ['Morning', 'Afternoon', 'Night', 'Supervisor', 'OFF', 'Leave']

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
    shifts: { Sunday: 'Morning', Monday: 'Morning', Tuesday: 'Morning', Wednesday: 'OFF', Thursday: 'Morning', Friday: 'Morning', Saturday: 'Afternoon' },
  },
  {
    id: 2,
    name: 'Blessing Eze',
    role: 'Room Attendant',
    area: 'Floor 2',
    shifts: { Sunday: 'OFF', Monday: 'Morning', Tuesday: 'Morning', Wednesday: 'Morning', Thursday: 'Morning', Friday: 'OFF', Saturday: 'Morning' },
  },
  {
    id: 3,
    name: 'Aisha Lawal',
    role: 'Supervisor',
    area: 'All Floors',
    shifts: { Sunday: 'Supervisor', Monday: 'Supervisor', Tuesday: 'Supervisor', Wednesday: 'Supervisor', Thursday: 'Supervisor', Friday: 'Supervisor', Saturday: 'Supervisor' },
  },
  {
    id: 4,
    name: 'John Ude',
    role: 'Laundry Attendant',
    area: 'Laundry',
    shifts: { Sunday: 'Morning', Monday: 'OFF', Tuesday: 'Morning', Wednesday: 'Morning', Thursday: 'OFF', Friday: 'Morning', Saturday: 'Morning' },
  },
  {
    id: 5,
    name: 'Rita James',
    role: 'Room Attendant',
    area: 'Floor 4',
    shifts: { Sunday: 'Afternoon', Monday: 'Morning', Tuesday: 'OFF', Wednesday: 'Morning', Thursday: 'Morning', Friday: 'OFF', Saturday: 'Morning' },
  },
  {
    id: 6,
    name: 'Tina Okafor',
    role: 'Public Area Cleaner',
    area: 'Lobby',
    shifts: { Sunday: 'OFF', Monday: 'Afternoon', Tuesday: 'Afternoon', Wednesday: 'Afternoon', Thursday: 'Afternoon', Friday: 'Afternoon', Saturday: 'Afternoon' },
  },
  {
    id: 7,
    name: 'Kemi Yusuf',
    role: 'Room Attendant',
    area: 'Floor 5',
    shifts: { Sunday: 'Afternoon', Monday: 'OFF', Tuesday: 'Afternoon', Wednesday: 'OFF', Thursday: 'Afternoon', Friday: 'Afternoon', Saturday: 'Leave' },
  },
])

const stats = reactive({
  departmentStaff: 42,
  conflictAlerts: 3,
})

const totalSlots = computed(() => staffList.length * days.length + 76) // mimic 109/118 ratio at 7 staff
const assignedSlots = computed(() => {
  return staffList.reduce((total, staff) => {
    return total + days.filter((d) => staff.shifts[d.label] !== 'OFF').length
  }, 0) + 76
})

const coverageLevel = ref(92)

function shiftClass(value) {
  switch (value) {
    case 'Morning':
      return 'bg-blue-100 text-blue-700 border-blue-200'
    case 'Afternoon':
      return 'bg-amber-100 text-amber-700 border-amber-200'
    case 'Night':
      return 'bg-indigo-100 text-indigo-700 border-indigo-200'
    case 'Supervisor':
      return 'bg-cyan-100 text-cyan-700 border-cyan-200'
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
    case 'Supervisor':
      return 'text-cyan-500'
    case 'Leave':
      return 'text-red-500'
    default:
      return 'text-gray-400'
  }
}

function cancelChanges() {
  // No backend connected — placeholder for cancel action
}

function saveDraft() {
  // No backend connected — placeholder for save draft action
}

function aiAutoAssign() {
  // No backend connected — placeholder for AI auto assign action
}

function publishRoster() {
  // No backend connected — placeholder for publish action
}
</script>