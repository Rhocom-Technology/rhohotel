<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">{{ viewMode === 'calendar' ? 'Calendar view of cashier assignments, outlet coverage, off-days, and supervisor presence across the week.' : 'Review cashier assignments, outlet coverage, shift timing, off-days, and role distribution across restaurant, bar, and retail POS teams.' }}</p>
    </div>

    <!-- Roaster Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Roaster Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Week scheduling for {{ filteredStaff.length }} POS staff across {{ outletCount }} active outlets and {{ shiftCount }} daily shifts.</p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="changeWeek(-1)">Prev Week</button>
        <button
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="changeWeek(0)">This Week</button>
        <button
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="changeWeek(1)">Next Week</button>
        <button
          class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="filteredStaff.length === 0"
          @click="exportRoster">Export Roaster</button>
        <button
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="openNewPlan">{{ viewMode === 'calendar' ? 'New Plan' : 'Create Shift Plan' }}</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Scheduled POS Staff</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.scheduled_staff }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Morning Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="coverageClass(stats.morning_coverage)">{{ coverageLabel(stats.morning_coverage) }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : `${stats.morning_coverage}%` }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Evening Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="coverageClass(stats.evening_coverage)">{{ coverageLabel(stats.evening_coverage) }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : `${stats.evening_coverage}%` }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Staff Off / Leave</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Info</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : stats.staff_off }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">{{ viewMode === 'calendar' ? 'Calendar Filters' : 'Filters & Search' }}</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">{{ viewMode === 'calendar' ? 'Search staff or outlet' : 'Search staff' }}</p>
          <input v-model="searchText" type="text" :placeholder="viewMode==='calendar' ? 'Search staff or outlet...' : 'Name, role, outlet...'"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Outlet</p>
          <select v-model="filterOutlet" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Outlets</option>
            <option v-for="outlet in outletOptions" :key="outlet" :value="outlet">{{ outlet }}</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Shift</p>
          <select v-model="filterShift" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Shifts</option>
            <option v-for="shift in shiftOptions" :key="shift" :value="shift">{{ shift }}</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Role</p>
          <select v-model="filterRole" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Roles</option>
            <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
          </select>
        </div>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="resetFilters">Reset</button>
        <button
          class="px-4 py-2.5 text-xs font-medium rounded-lg transition-colors"
          :class="viewMode==='list' ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="viewMode='list'">List View</button>
        <button
          class="px-4 py-2.5 text-xs font-medium rounded-lg transition-colors"
          :class="viewMode==='calendar' ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="viewMode='calendar'">Calendar View</button>
      </div>
      <div class="mt-3 flex items-center gap-2 flex-wrap">
        <span class="text-xs text-gray-400">Week:</span>
        <span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">{{ weekRangeLabel }}</span>
        <span v-if="error" class="text-xs text-red-500">{{ error }}</span>
      </div>
    </div>

    <!-- List View -->
    <div v-if="viewMode==='list'" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Weekly Staff Roaster</h3>
        <p class="text-xs text-gray-400">Week: {{ weekRangeLabel }}</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Staff Name</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Role</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outlet</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Shift</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Start</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">End</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Off Day</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="px-6 py-8 text-center text-xs text-gray-400">Loading staff roster...</td>
          </tr>
          <tr v-else-if="error">
            <td colspan="8" class="px-6 py-8 text-center text-xs text-red-500">{{ error }} <button @click="loadRoster" class="ml-2 underline font-semibold">Retry</button></td>
          </tr>
          <tr v-else-if="paginatedStaff.length === 0">
            <td colspan="8" class="px-6 py-8 text-center text-xs text-gray-400">No staff assignments found for this week.</td>
          </tr>
          <tr v-for="s in paginatedStaff" v-else :key="`${s.employee}-${s.start}-${s.shift}`" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ s.name }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.role }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.outlet }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.shift }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ formatDate(s.start) }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ formatDate(s.end) }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.offDay }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="s.status === 'Scheduled' || s.status === 'Active' ? 'bg-green-50 text-green-600' :
                        s.status === 'Review' ? 'bg-yellow-50 text-yellow-600' :
                        s.status === 'Leave' ? 'bg-gray-100 text-gray-500' :
                        'bg-blue-50 text-blue-600'">
                {{ s.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 20</p>
        <div class="flex items-center gap-1">
          <button
            class="px-3 py-1.5 text-xs font-medium border border-gray-200 rounded-lg transition-colors"
            :class="currentPage <= 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-white'"
            :disabled="currentPage <= 1"
            @click="currentPage = Math.max(1, currentPage - 1)">Prev</button>
          <button v-for="p in totalPages" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button
            class="px-3 py-1.5 text-xs font-medium border border-gray-200 rounded-lg transition-colors"
            :class="currentPage >= totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-white'"
            :disabled="currentPage >= totalPages"
            @click="currentPage = Math.min(totalPages, currentPage + 1)">Next</button>
        </div>
      </div>
    </div>

    <!-- Calendar View -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Weekly Roaster Calendar</h3>
        <p class="text-xs text-gray-400">Week: {{ weekRangeLabel }}</p>
      </div>
      <div class="px-6 py-4 overflow-x-auto">
        <div v-if="loading" class="py-12 text-center text-xs text-gray-400">Loading staff roster...</div>
        <div v-else-if="error" class="py-12 text-center text-xs text-red-500">{{ error }} <button @click="loadRoster" class="ml-2 underline font-semibold">Retry</button></div>
        <div v-else-if="filteredStaff.length === 0" class="py-12 text-center text-xs text-gray-400">No staff assignments found for this week.</div>
        <div v-else class="cal-grid">
          <div class="cal-time-col">
            <div class="cal-header-cell"></div>
            <div v-for="t in timeSlots" :key="t" class="cal-time-slot">{{ t }}</div>
          </div>
          <div v-for="day in calDays" :key="day.date" class="cal-day-col">
            <div class="cal-header-cell">
              <div class="text-xs font-semibold text-gray-900">{{ day.label }}</div>
              <div class="text-xs text-gray-400">{{ day.outlet }}</div>
            </div>
            <div class="cal-body">
              <div v-for="slot in day.slots" :key="slot.id"
                class="cal-event"
                :class="slot.color"
                :style="{ top: slot.top + 'px', height: slot.height + 'px' }">
                <div class="text-xs font-semibold leading-tight">{{ slot.title }}</div>
                <div class="text-xs font-bold">{{ slot.name }}</div>
                <div class="text-xs opacity-80">{{ slot.role }}</div>
                <div class="text-xs opacity-75">{{ slot.time }}</div>
                <div class="text-xs opacity-75">{{ slot.outlet }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Legend -->
        <div class="flex items-center gap-5 mt-4 pt-4 border-t border-gray-100 flex-wrap">
          <div class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded bg-blue-100 border border-blue-200 inline-block"></span> Restaurant
          </div>
          <div class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded bg-violet-100 border border-violet-200 inline-block"></span> Bar
          </div>
          <div class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded bg-yellow-100 border border-yellow-200 inline-block"></span> Retail
          </div>
          <div class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded bg-green-100 border border-green-200 inline-block"></span> Supervisor
          </div>
          <div class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded bg-red-50 border border-red-200 inline-block"></span> Off / Leave
          </div>
        </div>
      </div>
    </div>

    <!-- Create Roaster Modal -->
    <div v-if="showPlanModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4 py-6">
      <div class="w-full max-w-2xl bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between gap-4">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Create Staff Roaster</h3>
            <p class="text-xs text-gray-400 mt-0.5">Assign an employee to a shift for the selected week.</p>
          </div>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50"
            :disabled="savingPlan"
            @click="closePlanModal">&times;</button>
        </div>

        <form class="px-6 py-5 space-y-4" @submit.prevent="savePlan">
          <div v-if="planMessage" class="px-3 py-2 text-xs rounded-lg" :class="planMessageType === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'">
            {{ planMessage }}
          </div>

          <div class="grid gap-4" style="grid-template-columns:repeat(2,minmax(0,1fr));">
            <div style="grid-column:span 2;">
              <p class="text-xs text-gray-500 mb-1.5">Employee</p>
              <select v-model="planForm.employee" required class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
                <option value="">Select employee</option>
                <option v-for="employee in employeeOptions" :key="employee.employee" :value="employee.employee">
                  {{ employee.employee_name }}{{ employee.designation ? ` - ${employee.designation}` : '' }}{{ employee.department ? ` (${employee.department})` : '' }}
                </option>
              </select>
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">Shift</p>
              <select v-model="planForm.shift_type" required class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
                <option value="">Select shift</option>
                <option v-for="shift in shiftOptions" :key="shift" :value="shift">{{ shift }}</option>
              </select>
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">Status</p>
              <select v-model="planForm.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </select>
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">Start Date</p>
              <input v-model="planForm.start_date" required type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
            </div>

            <div>
              <p class="text-xs text-gray-500 mb-1.5">End Date</p>
              <input v-model="planForm.end_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
            </div>
          </div>

          <div class="rounded-lg bg-gray-50 border border-gray-100 px-4 py-3">
            <p class="text-xs text-gray-500">Week</p>
            <p class="text-sm font-semibold text-gray-900 mt-0.5">{{ weekRangeLabel }}</p>
          </div>

          <div class="pt-2 flex items-center justify-end gap-2 border-t border-gray-100">
            <button
              type="button"
              class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="savingPlan"
              @click="closePlanModal">Cancel</button>
            <button
              type="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="savingPlan || !canSavePlan">{{ savingPlan ? 'Saving...' : 'Save Roaster' }}</button>
          </div>
        </form>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { callMethod } from '@/lib/api'

const route = useRoute()
const viewMode = ref(route.query.view === 'list' ? 'list' : 'calendar')
const searchText = ref('')
const filterOutlet = ref('')
const filterShift = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const weekOffset = ref(0)
const pageSize = 20

const rosterRows = ref([])
const stats = ref({ scheduled_staff: 0, morning_coverage: 0, evening_coverage: 0, staff_off: 0, outlet_count: 0, shift_count: 0 })
const options = ref({ employees: [], outlets: [], shifts: [], roles: [] })
const loading = ref(false)
const error = ref('')
const showPlanModal = ref(false)
const savingPlan = ref(false)
const planMessage = ref('')
const planMessageType = ref('error')
const planForm = ref({ employee: '', shift_type: '', start_date: '', end_date: '', status: 'Active' })

const WEEKDAY_FORMAT = new Intl.DateTimeFormat('en-GB', { weekday: 'short' })
const DATE_MONTH_FORMAT = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short' })
const FULL_DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

function startOfWeek(date) {
  const d = new Date(date)
  const day = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - day)
  d.setHours(0, 0, 0, 0)
  return d
}

function isoDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function parseDate(value) {
  if (!value || value === '—') return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

function formatDate(value) {
  const d = parseDate(value)
  return d ? FULL_DATE_FORMAT.format(d) : '—'
}

function capitalize(text) {
  if (!text) return ''
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}`
}

function getShiftMeta(shift) {
  const s = (shift || '').toLowerCase()
  if (s.includes('morning')) return { top: 50, height: 130, title: 'Morning Shift', time: '07:00 AM - 03:00 PM' }
  if (s.includes('evening')) return { top: 220, height: 130, title: 'Evening Shift', time: '03:00 PM - 11:00 PM' }
  if (s.includes('split')) return { top: 90, height: 170, title: 'Split Shift', time: '10:00 AM - 08:00 PM' }
  return { top: 120, height: 140, title: 'Shift', time: '09:00 AM - 05:00 PM' }
}

function getSlotColor(outlet, role) {
  const outletText = (outlet || '').toLowerCase()
  const roleText = (role || '').toLowerCase()
  if (roleText.includes('supervisor')) return 'ev-green'
  if (outletText.includes('bar')) return 'ev-purple'
  if (outletText.includes('retail')) return 'ev-yellow'
  return 'ev-blue'
}

function coverageClass(value) {
  if (value >= 85) return 'bg-green-100 text-green-600'
  if (value >= 50) return 'bg-yellow-100 text-yellow-600'
  return 'bg-red-100 text-red-500'
}

function coverageLabel(value) {
  if (value >= 85) return 'Good'
  if (value >= 50) return 'Watch'
  return 'Gap'
}

function resetPlanForm() {
  planForm.value = {
    employee: '',
    shift_type: filterShift.value || '',
    start_date: isoDate(weekStart.value),
    end_date: isoDate(weekEnd.value),
    status: 'Active',
  }
  planMessage.value = ''
  planMessageType.value = 'error'
}

function openNewPlan() {
  resetPlanForm()
  showPlanModal.value = true
}

function closePlanModal() {
  if (savingPlan.value) return
  showPlanModal.value = false
}

async function savePlan() {
  if (!canSavePlan.value) return
  savingPlan.value = true
  planMessage.value = ''
  try {
    await callMethod('rhohotel.rhocom_hotel.api.pos.create_pos_staff_roster', planForm.value)
    planMessageType.value = 'success'
    planMessage.value = 'Staff roaster created.'
    await Promise.all([loadOptions(), loadRoster()])
    showPlanModal.value = false
  } catch (err) {
    planMessageType.value = 'error'
    planMessage.value = err.message || 'Failed to create staff roaster.'
  } finally {
    savingPlan.value = false
  }
}

const weekStart = computed(() => {
  const base = startOfWeek(new Date())
  base.setDate(base.getDate() + weekOffset.value * 7)
  return base
})
const weekDates = computed(() =>
  Array.from({ length: 7 }, (_, index) => {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + index)
    return d
  })
)
const weekEnd = computed(() => weekDates.value[6])
const weekRangeLabel = computed(() => `${FULL_DATE_FORMAT.format(weekDates.value[0])} - ${FULL_DATE_FORMAT.format(weekDates.value[6])}`)

const queryArgs = computed(() => ({
  week_start: isoDate(weekStart.value),
  week_end: isoDate(weekEnd.value),
  search: searchText.value || '',
  outlet: filterOutlet.value || '',
  shift: filterShift.value || '',
  role: filterRole.value || '',
}))

async function loadOptions() {
  try {
    options.value = await callMethod('rhohotel.rhocom_hotel.api.pos.get_pos_staff_roster_options') || { employees: [], outlets: [], shifts: [], roles: [] }
  } catch {
    options.value = { employees: [], outlets: [], shifts: [], roles: [] }
  }
}

async function loadRoster() {
  loading.value = true
  error.value = ''
  try {
    const args = queryArgs.value
    const [rows, statData] = await Promise.all([
      callMethod('rhohotel.rhocom_hotel.api.pos.get_pos_staff_roster', args),
      callMethod('rhohotel.rhocom_hotel.api.pos.get_pos_staff_roster_stats', args),
    ])
    rosterRows.value = rows || []
    stats.value = {
      scheduled_staff: statData?.scheduled_staff ?? 0,
      morning_coverage: statData?.morning_coverage ?? 0,
      evening_coverage: statData?.evening_coverage ?? 0,
      staff_off: statData?.staff_off ?? 0,
      outlet_count: statData?.outlet_count ?? 0,
      shift_count: statData?.shift_count ?? 0,
    }
    currentPage.value = 1
  } catch (err) {
    error.value = err.message || 'Failed to load staff roster.'
  } finally {
    loading.value = false
  }
}

function changeWeek(delta) {
  weekOffset.value = delta === 0 ? 0 : weekOffset.value + delta
}

function resetFilters() {
  searchText.value = ''
  filterOutlet.value = ''
  filterShift.value = ''
  filterRole.value = ''
  currentPage.value = 1
}

function csvEscape(value) {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function exportRoster() {
  const header = ['Staff Name', 'Role', 'Outlet', 'Shift', 'Start', 'End', 'Off Day', 'Status']
  const lines = [header.map(csvEscape).join(',')]
  filteredStaff.value.forEach(row => {
    lines.push([row.name, row.role, row.outlet, row.shift, row.start, row.end, row.offDay, row.status].map(csvEscape).join(','))
  })
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `staff-roaster-${isoDate(weekStart.value)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const allStaff = computed(() =>
  (rosterRows.value || []).map(s => ({
    employee: s.employee,
    name: s.employee_name || s.employee,
    role: s.role || s.designation || '—',
    outlet: s.outlet || s.department || '—',
    shift: s.shift || '—',
    start: s.start_date || '—',
    end: s.end_date || '—',
    offDay: s.off_day || s.offDay || '—',
    status: s.status || 'Scheduled',
  }))
)

const filteredStaff = computed(() => allStaff.value)
const outletCount = computed(() => stats.value.outlet_count || new Set(filteredStaff.value.map(s => s.outlet).filter(Boolean)).size)
const shiftCount = computed(() => stats.value.shift_count || new Set(filteredStaff.value.map(s => s.shift).filter(Boolean)).size)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredStaff.value.length / pageSize)))
const paginatedStaff = computed(() => filteredStaff.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))

const optionFallbacks = computed(() => ({
  outlets: [...new Set(allStaff.value.map(s => s.outlet).filter(v => v && v !== '—'))],
  shifts: [...new Set(allStaff.value.map(s => s.shift).filter(v => v && v !== '—'))],
  roles: [...new Set(allStaff.value.map(s => s.role).filter(v => v && v !== '—'))],
}))
const outletOptions = computed(() => options.value.outlets?.length ? options.value.outlets : optionFallbacks.value.outlets)
const shiftOptions = computed(() => options.value.shifts?.length ? options.value.shifts : optionFallbacks.value.shifts)
const roleOptions = computed(() => options.value.roles?.length ? options.value.roles : optionFallbacks.value.roles)
const employeeOptions = computed(() => options.value.employees || [])
const canSavePlan = computed(() => Boolean(planForm.value.employee && planForm.value.shift_type && planForm.value.start_date))

const timeSlots = ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00']
const calDays = computed(() => {
  let idCounter = 1
  return weekDates.value.map(dayDate => {
    const slots = []
    const outletSet = new Set()

    filteredStaff.value.forEach(staff => {
      const start = parseDate(staff.start) || weekDates.value[0]
      const end = parseDate(staff.end) || weekDates.value[6]
      if (dayDate < start || dayDate > end) return

      const meta = getShiftMeta(staff.shift)
      outletSet.add(staff.outlet)
      slots.push({
        id: idCounter++,
        title: staff.shift && staff.shift !== '—' ? capitalize(staff.shift) : meta.title,
        name: staff.name,
        role: staff.role,
        time: meta.time,
        outlet: staff.outlet,
        color: getSlotColor(staff.outlet, staff.role),
        top: meta.top,
        height: meta.height,
      })
    })

    const outletLabel = outletSet.size === 0 ? 'No coverage' : outletSet.size === 1 ? Array.from(outletSet)[0] : 'Mixed'
    return {
      date: DATE_MONTH_FORMAT.format(dayDate),
      label: `${WEEKDAY_FORMAT.format(dayDate)} ${dayDate.getDate()}`,
      outlet: outletLabel,
      slots,
    }
  })
})

let filterTimer = null
watch([searchText, filterOutlet, filterShift, filterRole, weekOffset], () => {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(loadRoster, 250)
})

onMounted(async () => {
  await loadOptions()
  await loadRoster()
})

onBeforeUnmount(() => clearTimeout(filterTimer))
</script>

<style scoped>
.cal-grid { display: flex; min-width: 700px; }
.cal-time-col { flex-shrink: 0; width: 52px; }
.cal-header-cell { height: 48px; display: flex; flex-direction: column; justify-content: center; padding: 4px 6px; border-bottom: 1px solid #f1f5f9; }
.cal-time-slot { height: 70px; display: flex; align-items: flex-start; padding-top: 4px; font-size: 11px; color: #94a3b8; border-bottom: 1px solid #f8fafc; padding-left: 2px; }
.cal-day-col { flex: 1; min-width: 110px; border-left: 1px solid #f1f5f9; }
.cal-body { position: relative; height: 490px; }
.cal-event { position: absolute; left: 3px; right: 3px; border-radius: 6px; padding: 5px 7px; overflow: hidden; }
.ev-blue       { background: #dbeafe; color: #1e3a8a; }
.ev-blue-light { background: #e0f2fe; color: #0c4a6e; }
.ev-purple     { background: #ede9fe; color: #4c1d95; }
.ev-yellow     { background: #fef9c3; color: #713f12; }
.ev-green      { background: #dcfce7; color: #14532d; }
.ev-gray       { background: #f1f5f9; color: #475569; }
.ev-offday     { background: #fef2f2; color: #991b1b; }
</style>
