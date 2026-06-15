<template>
  <div class="space-y-5">
    <div>
      <p class="text-xs text-gray-400">
        This page is visible only to the logged-in staff member. Staff can submit preferred shifts for the week, but cannot enter preferences for another staff member.
      </p>
    </div>

    <div
      v-if="showToast"
      class="fixed top-5 right-5 z-[60] text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg"
      :class="toastType === 'error' ? 'bg-red-600' : 'bg-green-600'"
    >
      {{ toastMessage }}
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Preference Submission Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">
        Preferences guide the department manager during weekly shift planning. Final allocation remains subject to coverage and approval.
      </p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Logged-in Staff</p>
          <div class="flex items-center justify-between gap-2 px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-medium">
            <span>{{ staffName || '...' }}</span>
            <span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Self</span>
          </div>
        </div>

        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <div class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-medium">
            {{ department || '...' }}
          </div>
        </div>

        <div style="min-width:220px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              :disabled="isLocked || loading"
              @click="changeWeek(-1)"
            >
              &lsaquo;
            </button>

            <input
              v-model="weekStartInput"
              type="date"
              :disabled="isLocked || loading"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white disabled:bg-gray-50 disabled:cursor-not-allowed"
            />

            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              :disabled="isLocked || loading"
              @click="changeWeek(1)"
            >
              &rsaquo;
            </button>
          </div>
        </div>

        <div class="flex-1"></div>

        <div class="flex items-center gap-2 flex-wrap">
          <button
            class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isLocked || loading || Boolean(saving)"
            @click="resetPreferences"
          >
            Reset
          </button>

          <button
            class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isLocked || loading || Boolean(saving)"
            @click="saveDraft"
          >
            {{ saving === 'draft' ? 'Saving...' : 'Save Draft' }}
          </button>

          <button
            class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isLocked || loading || Boolean(saving) || !canSubmit"
            @click="submitPreference"
          >
            {{ saving === 'submit' ? 'Submitting...' : 'Submit Preference' }}
          </button>
        </div>
      </div>

      <p v-if="error" class="text-xs text-red-500 mt-3">{{ error }}</p>

      <div
        v-if="isLocked && lockReason"
        class="mt-4 px-4 py-3 text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg"
      >
        {{ lockReason }}
      </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preference Status</p>
          <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', statusBadgeClass]">
            {{ statusBadgeLabel }}
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : preferenceStatus }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Preferred Work Days</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : preferredWorkDays }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unavailable Days</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : unavailableDays }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Manager Visibility</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">
            {{ preferenceStatus === 'Submitted' ? 'Visible' : 'Private' }}
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">
          {{ preferenceStatus === 'Submitted' ? 'Visible' : 'After Submit' }}
        </p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">
            Weekly Shift Preference - {{ staffName || '...' }}
          </h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ weekRangeLabel }}</p>
        </div>

        <p class="text-xs text-gray-400">Only current staff profile is editable</p>
      </div>

      <div v-if="loading" class="py-12 text-center text-xs text-gray-400">
        Loading preference...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1100px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:170px;">
                Preference Item
              </th>
              <th
                v-for="day in days"
                :key="day.date"
                class="text-left px-3 py-2.5"
                style="min-width:150px;"
              >
                <p class="text-xs font-semibold text-gray-700">{{ day.day }}</p>
                <p class="text-xs text-gray-400">{{ day.dateLabel }}</p>
              </th>
            </tr>
          </thead>

          <tbody>
            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Preferred Shift</p>
                <p class="text-xs text-gray-400">Select one option per day</p>
              </td>

              <td v-for="day in days" :key="day.date" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.date].preferred_shift"
                    :disabled="isLocked"
                    :class="[
                      'w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200',
                      isLocked ? 'cursor-not-allowed opacity-75' : 'cursor-pointer',
                      shiftClass(preferences[day.date].preferred_shift)
                    ]"
                  >
                    <option value="">No Preference</option>
                    <option v-for="opt in shiftTypes" :key="opt" :value="opt">
                      {{ opt }}
                    </option>
                  </select>

                  <ChevronDown
                    class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                    :class="chevronClass(preferences[day.date].preferred_shift)"
                  />
                </div>
              </td>
            </tr>

            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Alternative Shift</p>
                <p class="text-xs text-gray-400">Optional backup preference</p>
              </td>

              <td v-for="day in days" :key="day.date" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.date].alternative_shift"
                    :disabled="isLocked"
                    :class="[
                      'w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200',
                      isLocked ? 'cursor-not-allowed opacity-75' : 'cursor-pointer',
                      altShiftClass(preferences[day.date].alternative_shift)
                    ]"
                  >
                    <option value="">N/A</option>
                    <option
                      v-for="opt in alternativeOptionsForDay(day.date)"
                      :key="opt"
                      :value="opt"
                    >
                      {{ opt }}
                    </option>
                  </select>

                  <ChevronDown
                    class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                    :class="altChevronClass(preferences[day.date].alternative_shift)"
                  />
                </div>
              </td>
            </tr>

            <tr class="border-b border-gray-100">
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Availability</p>
                <p class="text-xs text-gray-400">Available / unavailable</p>
              </td>

              <td v-for="day in days" :key="day.date" class="px-3 py-3 align-top">
                <div class="relative">
                  <select
                    v-model="preferences[day.date].availability"
                    :disabled="isLocked"
                    :class="[
                      'w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200',
                      isLocked ? 'cursor-not-allowed opacity-75' : 'cursor-pointer',
                      availabilityClass(preferences[day.date].availability)
                    ]"
                  >
                    <option value="Available">Available</option>
                    <option value="Unavailable">Unavailable</option>
                  </select>

                  <ChevronDown
                    class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                    :class="availabilityChevronClass(preferences[day.date].availability)"
                  />
                </div>
              </td>
            </tr>

            <tr>
              <td class="px-3 py-3.5 align-top">
                <p class="text-sm font-bold text-gray-900">Daily Notes</p>
                <p class="text-xs text-gray-400">Optional reason / guidance to manager</p>
              </td>

              <td v-for="day in days" :key="day.date" class="px-3 py-3 align-top">
                <input
                  v-model="preferences[day.date].note"
                  :disabled="isLocked"
                  type="text"
                  placeholder="Optional note"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:bg-gray-50 disabled:cursor-not-allowed"
                />
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
          <span class="text-xs text-gray-500">Afternoon / Evening</span>
        </div>

        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded" style="background:#e0e7ff;"></span>
          <span class="text-xs text-gray-500">Night</span>
        </div>

        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded border border-gray-300" style="background:#f9fafb;"></span>
          <span class="text-xs text-gray-500">No Preference / Any Shift</span>
        </div>

        <div class="flex-1"></div>

        <p class="text-xs text-gray-400">Preferences are guidance only, not final schedule</p>
      </div>
    </div>

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
        <h3 class="text-sm font-bold mb-3" style="color:#7c3aed;">
          How It Guides the Department Manager
        </h3>

        <div class="space-y-2">
          <p v-for="(line, idx) in managerGuidance" :key="idx" class="text-xs" style="color:#8b5cf6;">
            {{ line }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'

const loading = ref(false)
const saving = ref('')
const error = ref('')

const staffName = ref('')
const department = ref('')
const company = ref('')
const preferenceStatus = ref('Not Started')
const isLocked = ref(false)
const lockReason = ref('')

const days = ref([])
const shiftTypes = ref([])
const preferences = reactive({})

const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer = null

const FULL_DATE_FORMAT = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

const DATE_LABEL_FORMAT = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
})

function showToastMessage(message, type = 'success') {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true

  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    showToast.value = false
  }, 3200)
}

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

const preferredWorkDays = computed(() => {
  return Object.values(preferences).filter((row) => {
    return row.availability === 'Available' && Boolean(row.preferred_shift)
  }).length
})

const unavailableDays = computed(() => {
  return Object.values(preferences).filter((row) => row.availability === 'Unavailable').length
})

const hasAnyPreference = computed(() => {
  return Object.values(preferences).some((row) => {
    return Boolean(row.preferred_shift) ||
      Boolean(row.alternative_shift) ||
      row.availability === 'Unavailable' ||
      Boolean(row.note)
  })
})

const canSubmit = computed(() => {
  return hasAnyPreference.value
})

const statusBadgeLabel = computed(() => {
  if (preferenceStatus.value === 'Submitted') return 'Sent'
  if (preferenceStatus.value === 'Draft') return 'Not Sent'
  return 'New'
})

const statusBadgeClass = computed(() => {
  if (preferenceStatus.value === 'Submitted') return 'bg-green-100 text-green-600'
  if (preferenceStatus.value === 'Draft') return 'bg-amber-100 text-amber-600'
  return 'bg-gray-100 text-gray-500'
})

const accessRules = [
  'Staff can only edit their own preference record.',
  'Department and staff name are locked from the logged-in Employee profile.',
  'If a Shift Assignment already exists for the employee department and selected week, preference submission is disabled.',
  'Once submitted, the preference cannot be changed.',
]

const managerGuidance = [
  'Submitted preferences guide the manager during weekly roster planning.',
  'Manager can still override preferences based on coverage, fairness, leave, and overtime rules.',
  'Preferences are not Shift Assignments and do not create final schedules.',
]

function normaliseDay(dateString, dayName) {
  const date = new Date(dateString)

  return {
    date: dateString,
    day: dayName,
    dateLabel: DATE_LABEL_FORMAT.format(date),
  }
}

function initialisePreferences(dayRows, savedRows = []) {
  Object.keys(preferences).forEach((key) => {
    delete preferences[key]
  })

  const savedByDate = {}

  savedRows.forEach((row) => {
    savedByDate[row.date] = row
  })

  dayRows.forEach((day) => {
    const saved = savedByDate[day.date] || {}

    preferences[day.date] = {
      date: day.date,
      day: day.day,
      preferred_shift: saved.preferred_shift || '',
      alternative_shift: saved.alternative_shift || '',
      availability: saved.availability || 'Available',
      note: saved.note || '',
    }
  })
}

function alternativeOptionsForDay(dayDate) {
  const preferred = preferences[dayDate]?.preferred_shift || ''

  return shiftTypes.value.filter((shift) => shift !== preferred)
}

function cleanAlternativeDuplicates() {
  Object.values(preferences).forEach((row) => {
    if (row.preferred_shift && row.alternative_shift === row.preferred_shift) {
      row.alternative_shift = ''
    }
  })
}

function buildPayload() {
  cleanAlternativeDuplicates()

  return days.value.map((day) => {
    const row = preferences[day.date] || {}

    return {
      date: day.date,
      day: day.day,
      preferred_shift: row.preferred_shift || '',
      alternative_shift: row.alternative_shift === 'Any Shift' ? '' : (row.alternative_shift || ''),
      availability: row.availability || 'Available',
      note: row.note || '',
    }
  })
}

async function loadShiftTypes() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_preference.get_shift_types')
    shiftTypes.value = result || []
  } catch (err) {
    shiftTypes.value = []
  }
}

async function loadPreference() {
  loading.value = true
  error.value = ''

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.shift_preference.get_my_preference', {
      week_start: isoDate(weekStart.value),
    })

    staffName.value = result.employee_name || ''
    department.value = result.department || ''
    company.value = result.company || ''
    preferenceStatus.value = result.status || 'Not Started'
    isLocked.value = Boolean(result.locked)
    lockReason.value = result.lock_reason || ''

    const dayRows = (result.days || []).map((day) => normaliseDay(day.date, day.day))
    days.value = dayRows

    initialisePreferences(dayRows, result.preferences || [])
  } catch (err) {
    error.value = err.message || 'Failed to load preference.'
  } finally {
    loading.value = false
  }
}

function changeWeek(deltaWeeks) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + deltaWeeks * 7)
  weekStart.value = startOfWeek(d)
}

function resetPreferences() {
  if (isLocked.value) return

  days.value.forEach((day) => {
    preferences[day.date] = {
      date: day.date,
      day: day.day,
      preferred_shift: '',
      alternative_shift: '',
      availability: 'Available',
      note: '',
    }
  })
}

async function saveDraft() {
  if (isLocked.value) return

  saving.value = 'draft'
  error.value = ''

  try {
    await callMethod('rhohotel.rhocom_hotel.api.shift_preference.save_draft', {
      week_start: isoDate(weekStart.value),
      preferences: buildPayload(),
    })

    showToastMessage('Draft saved.', 'success')
    await loadPreference()
  } catch (err) {
    showToastMessage(err.message || 'Failed to save draft.', 'error')
  } finally {
    saving.value = ''
  }
}

async function submitPreference() {
  if (isLocked.value || !canSubmit.value) return

  saving.value = 'submit'
  error.value = ''

  try {
    await callMethod('rhohotel.rhocom_hotel.api.shift_preference.submit_preference', {
      week_start: isoDate(weekStart.value),
      preferences: buildPayload(),
    })

    showToastMessage('Preference submitted.', 'success')
    await loadPreference()
  } catch (err) {
    showToastMessage(err.message || 'Failed to submit preference.', 'error')
  } finally {
    saving.value = ''
  }
}

function shiftClass(value) {
  const lowered = String(value || '').toLowerCase()

  if (lowered.includes('morning')) return 'bg-blue-100 text-blue-700 border-blue-200'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'bg-amber-100 text-amber-700 border-amber-200'
  if (lowered.includes('night')) return 'bg-indigo-100 text-indigo-700 border-indigo-200'
  if (lowered.includes('leave')) return 'bg-red-100 text-red-700 border-red-200'
  if (lowered.includes('day')) return 'bg-gray-100 text-gray-700 border-gray-200'

  return 'bg-gray-50 text-gray-500 border-gray-200'
}

function chevronClass(value) {
  const lowered = String(value || '').toLowerCase()

  if (lowered.includes('morning')) return 'text-blue-500'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'text-amber-500'
  if (lowered.includes('night')) return 'text-indigo-500'
  if (lowered.includes('leave')) return 'text-red-500'

  return 'text-gray-400'
}

function altShiftClass(value) {
  if (value === 'Any Shift') return 'bg-white text-gray-700 border-gray-200'
  return shiftClass(value)
}

function altChevronClass(value) {
  if (value === 'Any Shift') return 'text-gray-400'
  return chevronClass(value)
}

function availabilityClass(value) {
  return value === 'Available'
    ? 'bg-green-100 text-green-700 border-green-200'
    : 'bg-red-100 text-red-700 border-red-200'
}

function availabilityChevronClass(value) {
  return value === 'Available' ? 'text-green-500' : 'text-red-500'
}

watch(weekStart, () => {
  loadPreference()
})

watch(
  preferences,
  () => {
    cleanAlternativeDuplicates()
  },
  { deep: true }
)

onMounted(async () => {
  await loadShiftTypes()
  await loadPreference()
})
</script>