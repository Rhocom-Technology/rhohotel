<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Shows only published staff shifts for the selected department and specific date. Draft, unpublished, and source-tracking columns are excluded.</p>
    </div>

    <!-- Published Shift Register Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Published Shift Register Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Published shifts only</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Date</p>
          <input v-model="selectedDate" type="text" readonly
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Shift Type</p>
          <select v-model="shiftType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="opt in shiftTypeOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="resetFilters">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="exportShifts">Export</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="printShifts">Print</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="newShift">New Shift</button>

        <div class="flex-1"></div>

        <button
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="toggleCalendarView">Calendar View</button>
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
          <p class="text-xs text-gray-400">Morning / Afternoon / Night</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Split</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.morning }} / {{ stats.afternoon }} / {{ stats.night }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Staff Scheduled</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.staffScheduled }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unpublished Items</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Hidden</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.unpublished }}</p>
      </div>
    </div>

    <!-- Published Shift Records -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="text-sm font-bold text-gray-900">Published Shift Records for {{ selectedDate }}</h3>
        <p class="text-xs text-gray-400">Morning, Afternoon and Night shifts included</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1100px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Shift ID</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Staff</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Role / Station</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Day</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Shift</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Time</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-r-lg">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in shiftRecords" :key="row.id" class="border-b border-gray-100">
              <td class="px-3 py-3.5 text-sm font-bold text-gray-900">{{ row.id }}</td>
              <td class="px-3 py-3.5 text-sm text-gray-700">{{ row.staff }}</td>
              <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.roleStation }}</td>
              <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.day }}</td>
              <td class="px-3 py-3.5">
                <span :class="['px-2.5 py-1 text-xs font-semibold rounded-md', shiftClass(row.shift)]">{{ row.shift }}</span>
              </td>
              <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.time }}</td>
              <td class="px-3 py-3.5">
                <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">{{ row.status }}</span>
              </td>
              <td class="px-3 py-3.5">
                <button
                  class="px-4 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  @click="viewShift(row)">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer: legend + pagination -->
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

        <div class="flex-1"></div>

        <p class="text-xs text-gray-400">Rows per page: 25 &bull; Published shifts only &bull; Source column removed</p>

        <div class="flex items-center gap-2">
          <button
            v-for="page in pageNumbers"
            :key="page"
            :class="['w-7 h-7 text-xs font-medium rounded-lg transition-colors', currentPage === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100']"
            @click="currentPage = page">{{ page }}</button>
          <button
            class="px-4 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="nextPage">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const departmentOptions = ['Housekeeping', 'Front Desk', 'Restaurant', 'Maintenance', 'Security']
const department = ref('Housekeeping')
const selectedDate = ref('18 Apr 2026')

const shiftTypeOptions = ['All Shifts', 'Morning', 'Afternoon', 'Night', 'Supervisor']
const shiftType = ref('All Shifts')

const stats = reactive({
  publishedToday: 18,
  morning: 9,
  afternoon: 6,
  night: 3,
  staffScheduled: 18,
  unpublished: 0,
})

const shiftRecords = reactive([
  { id: 'SFT-PUB-001021', staff: 'Mary Bello', roleStation: 'Room Attendant • Floor 3', day: 'Saturday', shift: 'Morning', time: '8:00 AM - 4:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001022', staff: 'Blessing Eze', roleStation: 'Room Attendant • Floor 2', day: 'Saturday', shift: 'Morning', time: '8:00 AM - 4:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001023', staff: 'Aisha Lawal', roleStation: 'Supervisor • All Floors', day: 'Saturday', shift: 'Supervisor', time: '7:00 AM - 5:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001024', staff: 'John Ude', roleStation: 'Laundry Attendant • Laundry', day: 'Saturday', shift: 'Morning', time: '8:00 AM - 4:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001025', staff: 'Tina Okafor', roleStation: 'Public Area Cleaner • Lobby', day: 'Saturday', shift: 'Afternoon', time: '12:00 PM - 8:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001026', staff: 'Kemi Yusuf', roleStation: 'Room Attendant • Floor 5', day: 'Saturday', shift: 'Afternoon', time: '12:00 PM - 8:00 PM', status: 'Published' },
  { id: 'SFT-PUB-001027', staff: 'Chinedu Nwosu', roleStation: 'Night Cleaner • Public Area', day: 'Saturday', shift: 'Night', time: '8:00 PM - 8:00 AM', status: 'Published' },
  { id: 'SFT-PUB-001028', staff: 'Sarah Musa', roleStation: 'Night Room Support • Floors 2-4', day: 'Saturday', shift: 'Night', time: '8:00 PM - 8:00 AM', status: 'Published' },
])

const currentPage = ref(1)
const pageNumbers = [1, 2, 3]

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
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function resetFilters() {
  department.value = 'Housekeeping'
  selectedDate.value = '18 Apr 2026'
  shiftType.value = 'All Shifts'
}

function exportShifts() {
  // No backend connected — placeholder for export action
}

function printShifts() {
  // No backend connected — placeholder for print action
}

function newShift() {
  // No backend connected — placeholder for new shift action
}

function toggleCalendarView() {
  // No backend connected — placeholder for calendar view toggle
}

function viewShift(row) {
  // No backend connected — placeholder for view shift detail
}

function nextPage() {
  if (currentPage.value < pageNumbers.length) currentPage.value += 1
}
</script>