<template>
  <div class="space-y-5">
    <div>
      <p class="text-xs text-gray-400">
        Department managers can view staff-submitted weekly preferences, compare availability, identify gaps, and use preferences during weekly shift planning.
      </p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900">Preference Review Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">
        Review submitted preferences for the selected department and week. Managers cannot edit staff submissions.
      </p>

      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div class="w-full sm:min-w-[170px]">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select
            v-model="department"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option v-if="!departmentOptions.length" value="">No department found</option>
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">
              {{ dept }}
            </option>
          </select>
        </div>

        <div class="w-full sm:min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="changeWeek(-1)"
            >
              &lsaquo;
            </button>

            <input
              v-model="weekStartInput"
              type="date"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white"
            />

            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="changeWeek(1)"
            >
              &rsaquo;
            </button>
          </div>
        </div>

        <div class="w-full sm:min-w-[170px]">
          <p class="text-xs text-gray-500 mb-1.5">Submission Status</p>
          <select
            v-model="submissionStatus"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option v-for="opt in submissionStatusOptions" :key="opt" :value="opt">
              {{ opt }}
            </option>
          </select>
        </div>

        <div class="w-full sm:min-w-[200px] sm:flex-1">
          <p class="text-xs text-gray-500 mb-1.5">&nbsp;</p>
          <input
            v-model="searchText"
            type="text"
            placeholder="Search staff name..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="hidden flex-1 sm:block"></div>

        <button
          class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
          @click="resetFilters"
        >
          Reset
        </button>

        <button
          class="w-full px-5 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto"
          @click="printSummary"
        >
          Print
        </button>
      </div>

      <p v-if="error" class="text-xs text-red-500 mt-3">{{ error }}</p>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Department Staff</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.departmentStaff }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Submitted Preferences</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Status</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">
          {{ loading ? '...' : `${stats.submittedPreferences} / ${stats.departmentStaff}` }}
        </p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unavailable Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.unavailableRequests }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Most Preferred Shift</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">
            {{ stats.mostPreferredPct }}%
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.mostPreferredShift }}</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Staff Weekly Preference Summary</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ weekRangeLabel }}</p>
        </div>

        <p class="text-xs text-gray-400">Manager review &bull; read-only staff submissions</p>
      </div>

      <div v-if="loading" class="py-12 text-center text-xs text-gray-400">
        Loading preferences...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1200px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:170px;">
                Staff / Role
              </th>

              <th
                v-for="day in days"
                :key="day.date"
                class="text-left px-3 py-2.5"
                style="min-width:130px;"
              >
                <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                <p class="text-xs text-gray-400">{{ day.dateLabel }}</p>
              </th>

              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-r-lg" style="min-width:90px;">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="!staffList.length">
              <td :colspan="days.length + 2" class="px-3 py-8 text-center text-xs text-gray-400">
                No staff preferences found.
              </td>
            </tr>

            <tr v-for="staff in staffList" :key="staff.id" class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                <p class="text-xs text-gray-400">{{ staff.role }} &bull; {{ staff.area }}</p>
              </td>

              <template v-if="staff.submitted">
                <td v-for="day in days" :key="day.date" class="px-3 py-3.5 align-top">
                  <span
                    :title="staff.notes?.[day.date] || ''"
                    :class="['inline-flex w-full justify-center px-3 py-1.5 text-xs font-semibold rounded-lg', shiftClass(staff.shifts?.[day.date])]"
                  >
                    {{ staff.shifts?.[day.date] || 'No Preference' }}
                  </span>
                </td>
              </template>

              <template v-else>
                <td :colspan="days.length" class="px-3 py-3.5 align-top">
                  <div class="w-full text-center px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:#fef3c7; color:#b45309;">
                    Preference not submitted yet
                  </div>
                </td>
              </template>

              <td class="px-3 py-3.5 align-top">
                <span
                  :class="[
                    'px-2.5 py-0.5 text-xs font-medium rounded-full',
                    staff.submitted ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'
                  ]"
                >
                  {{ staff.submitted ? 'Sent' : 'Pending' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

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
          <span class="text-xs text-gray-500">No Preference</span>
        </div>

        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#fee2e2;"></span>
          <span class="text-xs text-gray-500">Unavailable</span>
        </div>

        <div class="flex-1"></div>

        <p class="text-xs text-gray-400">Read-only manager view</p>
      </div>
    </div>

    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">Manager Planning Guidance</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">
        Submitted preferences are used as guidance only. Final roster decisions remain controlled by manager coverage rules, fairness, leave, and overtime limits.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const departmentOptions = ref([])
const department = ref('')

const submissionStatusOptions = ['All Staff', 'Submitted', 'Pending']
const submissionStatus = ref('All Staff')
const searchText = ref('')

const loading = ref(false)
const error = ref('')

const stats = reactive({
  departmentStaff: 0,
  submittedPreferences: 0,
  unavailableRequests: 0,
  mostPreferredShift: '—',
  mostPreferredPct: 0,
})

const days = ref([])
const staffList = ref([])

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

function changeWeek(deltaWeeks) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + deltaWeeks * 7)
  weekStart.value = startOfWeek(d)
}

async function loadDepartments() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_preference_manager.get_departments')
    departmentOptions.value = result || []

    if (!department.value && departmentOptions.value.length) {
      department.value = departmentOptions.value[0]
    }
  } catch (err) {
    error.value = err.message || 'Failed to load departments.'
  }
}

async function loadReview() {
  if (!department.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_preference_manager.get_preference_review', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      submission_status: submissionStatus.value,
      search_text: searchText.value,
    })

    days.value = result.days || []
    staffList.value = result.staff || []

    Object.assign(stats, {
      departmentStaff: 0,
      submittedPreferences: 0,
      unavailableRequests: 0,
      mostPreferredShift: '—',
      mostPreferredPct: 0,
      ...(result.stats || {}),
    })
  } catch (err) {
    error.value = err.message || 'Failed to load preference review.'
    days.value = []
    staffList.value = []
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  submissionStatus.value = 'All Staff'
  searchText.value = ''
  weekStart.value = startOfWeek(new Date())

  if (departmentOptions.value.length) {
    department.value = departmentOptions.value[0]
  }

  loadReview()
}

async function printSummary() {
  const params = new URLSearchParams({
    department: department.value || '',
    week_start: isoDate(weekStart.value),
    submission_status: submissionStatus.value || '',
    search_text: searchText.value || '',
  })

  await printPdf(`/api/method/rhohotel.rhocom_hotel.api.shift_preference_manager.download_preference_review_report?${params.toString()}`)
}

function shiftClass(value) {
  const lowered = String(value || '').toLowerCase()

  if (lowered.includes('morning')) return 'bg-blue-100 text-blue-700'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'bg-amber-100 text-amber-700'
  if (lowered.includes('night')) return 'bg-indigo-100 text-indigo-700'
  if (lowered.includes('supervisor') || lowered.includes('lead')) return 'bg-cyan-100 text-cyan-700'
  if (lowered.includes('leave') || lowered.includes('unavailable')) return 'bg-red-100 text-red-700'
  return 'bg-gray-50 text-gray-500'
}

let searchTimer = null

watch([department, weekStart, submissionStatus], () => {
  loadReview()
})

watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadReview()
  }, 350)
})

onMounted(async () => {
  await loadDepartments()
  await loadReview()
})

async function printPdf(url) {
  try {
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error('Failed to fetch PDF')
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;top:0;left:0;width:0;height:0;border:0;visibility:hidden;'
    iframe.src = objectUrl
    document.body.appendChild(iframe)
    iframe.onload = () => {
      setTimeout(() => {
        iframe.contentWindow.focus()
        iframe.contentWindow.print()
        setTimeout(() => {
          document.body.removeChild(iframe)
          URL.revokeObjectURL(objectUrl)
        }, 1000)
      }, 300)
    }
  } catch (err) {
    console.error('Print error:', err)
  }
}
</script>