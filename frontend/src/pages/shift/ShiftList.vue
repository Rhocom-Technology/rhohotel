<template>
  <div class="space-y-5">
    <div>
      <p class="text-xs text-gray-400">
        Shows published staff shifts for the selected department and week. Switch between list and calendar view.
      </p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Shift Register Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Published shifts by selected week</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:220px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-if="!departmentOptions.length" value="">No department found</option>
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>

        <div style="min-width:190px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors" @click="changeWeek(-1)">
              &lsaquo;
            </button>

            <input v-model="weekStartInput" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />

            <button class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors" @click="changeWeek(1)">
              &rsaquo;
            </button>
          </div>
        </div>

        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Shift Type</p>
          <select v-model="shiftType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="opt in shiftTypeOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="resetFilters">
          Reset
        </button>

        <button class="px-5 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors" @click="exportShifts">
          Export
        </button>

        <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="printShifts">
          Print
        </button>

        <div class="flex-1"></div>

        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors" @click="toggleCalendarView">
          {{ viewMode === 'list' ? 'Calendar View' : 'List View' }}
        </button>
      </div>

      <p v-if="error" class="text-xs text-red-500 mt-3">{{ error }}</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Published Shifts This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.publishedThisWeek }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Shift Type Counts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Split</span>
        </div>

        <div v-if="loading" class="text-3xl font-bold text-gray-900">...</div>

        <div v-else-if="!stats.shiftTypeCounts.length" class="text-sm text-gray-400">
          No shifts
        </div>

        <div v-else class="space-y-1">
          <div v-for="item in stats.shiftTypeCounts" :key="item.shift_type" class="flex items-center justify-between text-sm">
            <span class="text-gray-500 truncate">{{ item.shift_type }}</span>
            <span class="font-bold text-gray-900">{{ item.count }}</span>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Staff Scheduled</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.staffScheduled }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unpublished Items</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Draft</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.unpublished }}</p>
      </div>
    </div>

    <div v-if="viewMode === 'list'" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Published Shift Records</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ weekRangeLabel }}</p>
        </div>

        <p class="text-xs text-gray-400">Showing published shifts for the selected week</p>
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
            <tr v-if="loading">
              <td colspan="8" class="px-3 py-8 text-center text-xs text-gray-400">Loading shifts...</td>
            </tr>

            <tr v-else-if="!shiftRecords.length">
              <td colspan="8" class="px-3 py-8 text-center text-xs text-gray-400">No published shifts found for this week.</td>
            </tr>

            <template v-else>
              <tr v-for="row in shiftRecords" :key="row.id" class="border-b border-gray-100">
                <td class="px-3 py-3.5 text-sm font-bold text-gray-900">{{ row.id }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-700">{{ row.staff }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.roleStation }}</td>
                <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.day }}</td>
                <td class="px-3 py-3.5">
                  <span :class="['px-2.5 py-1 text-xs font-semibold rounded-md', shiftClass(row.shift)]">
                    {{ row.shift }}
                  </span>
                </td>
                <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.time || '—' }}</td>
                <td class="px-3 py-3.5">
                  <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">
                    {{ row.status }}
                  </span>
                </td>
                <td class="px-3 py-3.5">
                  <button class="px-4 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="viewShift(row)">
                    View
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div class="flex items-center gap-6 flex-wrap mt-5 pt-4 border-t border-gray-100">
        <div class="flex-1"></div>

        <p class="text-xs text-gray-400">
          Rows per page: {{ pageSize }} &bull; Total: {{ totalRows }}
        </p>

        <div class="flex items-center gap-2">
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50" :disabled="currentPage === 1" @click="prevPage">
            Prev
          </button>

          <button v-for="page in pageNumbers" :key="page" :class="['w-7 h-7 text-xs font-medium rounded-lg transition-colors', currentPage === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100']" @click="currentPage = page">
            {{ page }}
          </button>

          <button class="px-4 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50" :disabled="currentPage >= totalPages" @click="nextPage">
            Next
          </button>
        </div>
      </div>
    </div>

    <div v-else class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Shift Calendar View</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ weekRangeLabel }}</p>
        </div>

        <p class="text-xs text-gray-400">Published shifts only</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1100px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Staff / Role</th>
              <th v-for="day in calendarDays" :key="day.date" class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">
                <p>{{ day.label }}</p>
                <p class="text-gray-400">{{ day.dateLabel }}</p>
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="px-3 py-8 text-center text-xs text-gray-400">Loading calendar...</td>
            </tr>

            <tr v-else-if="!calendarStaff.length">
              <td colspan="8" class="px-3 py-8 text-center text-xs text-gray-400">No active staff found for this department.</td>
            </tr>

            <template v-else>
              <tr v-for="staff in calendarStaff" :key="staff.id" class="border-b border-gray-100">
                <td class="px-3 py-3 align-top">
                  <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                  <p class="text-xs text-gray-400">{{ staff.role }}</p>
                </td>

                <td v-for="day in calendarDays" :key="day.date" class="px-3 py-3 align-top">
                  <div v-if="staff.shifts && staff.shifts[day.date]" :class="['rounded-lg px-3 py-2 text-xs font-semibold', shiftClass(staff.shifts[day.date].shift)]">
                    <p>{{ staff.shifts[day.date].shift }}</p>
                    <p class="font-normal mt-0.5">{{ staff.shifts[day.date].time || '—' }}</p>
                  </div>

                  <div v-else class="rounded-lg px-3 py-2 text-xs text-gray-400 bg-gray-50">
                    OFF
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const departmentOptions = ref([])
const department = ref('')

const shiftTypeOptions = ref(['All Shifts'])
const shiftType = ref('All Shifts')

const viewMode = ref('list')
const loading = ref(false)
const error = ref('')

const stats = reactive({
  publishedThisWeek: 0,
  staffScheduled: 0,
  unpublished: 0,
  shiftTypeCounts: [],
})

const shiftRecords = ref([])
const calendarDays = ref([])
const calendarStaff = ref([])

const currentPage = ref(1)
const pageSize = ref(15)
const totalPages = ref(1)
const totalRows = ref(0)

const FULL_DATE_FORMAT = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

function isoDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfWeek(date) {
  const d = new Date(date)
  d.setDate(d.getDate() - d.getDay() + 1)
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

const weekRangeLabel = computed(() => {
  const start = new Date(weekStart.value)
  const end = new Date(weekStart.value)
  end.setDate(end.getDate() + 6)

  return `${FULL_DATE_FORMAT.format(start)} - ${FULL_DATE_FORMAT.format(end)}`
})

const pageNumbers = computed(() => {
  const pages = []
  const maxButtons = 7

  let start = Math.max(1, currentPage.value - 3)
  let end = Math.min(totalPages.value, start + maxButtons - 1)

  if (end - start < maxButtons - 1) {
    start = Math.max(1, end - maxButtons + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

function shiftClass(value) {
  const lowered = String(value || '').toLowerCase()

  if (lowered.includes('morning')) return 'bg-blue-100 text-blue-700'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'bg-amber-100 text-amber-700'
  if (lowered.includes('night')) return 'bg-indigo-100 text-indigo-700'
  if (lowered.includes('day')) return 'bg-gray-100 text-gray-700'

  return 'bg-gray-100 text-gray-600'
}

function changeWeek(deltaWeeks) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + deltaWeeks * 7)
  weekStart.value = startOfWeek(d)
}

async function loadDepartments() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_list.get_departments')
    departmentOptions.value = result || []

    if (!department.value && departmentOptions.value.length) {
      department.value = departmentOptions.value[0]
    }
  } catch (err) {
    error.value = err.message || 'Failed to load departments.'
  }
}

async function loadShiftTypes() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_list.get_shift_types')
    shiftTypeOptions.value = result || ['All Shifts']

    if (!shiftTypeOptions.value.includes(shiftType.value)) {
      shiftType.value = 'All Shifts'
    }
  } catch (err) {
    shiftTypeOptions.value = ['All Shifts']
  }
}

function resetStats(newStats) {
  Object.assign(stats, {
    publishedThisWeek: 0,
    staffScheduled: 0,
    unpublished: 0,
    shiftTypeCounts: [],
    ...(newStats || {}),
  })
}

async function loadList() {
  if (!department.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_list.get_shift_list', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      shift_type: shiftType.value,
      page: currentPage.value,
      page_size: pageSize.value,
    })

    shiftRecords.value = result.records || []
    resetStats(result.stats)

    totalRows.value = result.pagination?.total || 0
    totalPages.value = result.pagination?.total_pages || 1
  } catch (err) {
    error.value = err.message || 'Failed to load shift list.'
    shiftRecords.value = []
    resetStats()
  } finally {
    loading.value = false
  }
}

async function loadCalendar() {
  if (!department.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_list.get_shift_calendar', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      shift_type: shiftType.value,
    })

    calendarDays.value = result.days || []
    calendarStaff.value = result.staff || []

    const statsResult = await callMethod('rhohotel.rhocom_hotel.api.shift_list.get_shift_stats', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      shift_type: shiftType.value,
    })

    resetStats(statsResult)
  } catch (err) {
    error.value = err.message || 'Failed to load calendar.'
    calendarDays.value = []
    calendarStaff.value = []
    resetStats()
  } finally {
    loading.value = false
  }
}

function refreshData() {
  if (viewMode.value === 'calendar') {
    loadCalendar()
  } else {
    loadList()
  }
}

function resetFilters() {
  weekStart.value = startOfWeek(new Date())
  shiftType.value = 'All Shifts'
  currentPage.value = 1

  if (departmentOptions.value.length) {
    department.value = departmentOptions.value[0]
  }

  refreshData()
}

function toggleCalendarView() {
  viewMode.value = viewMode.value === 'list' ? 'calendar' : 'list'
  refreshData()
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value -= 1
  }
}

function exportShifts() {
  const headers = ['Shift ID', 'Staff', 'Role / Station', 'Day', 'Shift', 'Time', 'Status']

  const csvRows = [
    headers.join(','),
    ...shiftRecords.value.map(row => [
      row.id || '',
      row.staff || '',
      row.roleStation || '',
      row.day || '',
      row.shift || '',
      row.time || '',
      row.status || '',
    ].map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')),
  ]

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `shift-list-${isoDate(weekStart.value)}.csv`
  link.click()

  URL.revokeObjectURL(url)
}

function printShifts() {
  const params = new URLSearchParams({
    department: department.value || '',
    week_start: isoDate(weekStart.value),
    shift_type: shiftType.value || '',
  })

  window.open(
    `/api/method/rhohotel.rhocom_hotel.api.shift_list.download_shift_list_report?${params.toString()}`,
    '_blank'
  )
}

function newShift() {
  window.location.href = '/app/shift-assignment/new-shift-assignment'
}

function viewShift(row) {
  window.location.href = `/app/shift-assignment/${row.id}`
}

watch([department, weekStart, shiftType], () => {
  currentPage.value = 1
  refreshData()
})

watch(currentPage, () => {
  if (viewMode.value === 'list') {
    loadList()
  }
})

onMounted(async () => {
  await loadDepartments()
  await loadShiftTypes()
  await refreshData()
})
</script>