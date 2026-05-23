<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">{{ viewMode === 'calendar' ? 'Calendar view of cashier assignments, outlet coverage, off-days, and supervisor presence across the week.' : 'Review cashier assignments, outlet coverage, shift timing, off-days, and role distribution across restaurant, bar, and retail POS teams.' }}</p>
    </div>

    <!-- Roaster Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Roaster Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Current week scheduling for {{ filteredStaff.length }} POS staff across {{ outletCount }} active outlets and {{ shiftCount }} daily shifts.</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="viewMode==='calendar'"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="weekOffset = weekOffset - 1">Prev Week</button>
        <button
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="weekOffset = 0">This Week</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Roaster</button>
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
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : (statsResource.data?.scheduled_staff ?? statsResource.data?.scheduled ?? filteredStaff.length) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Morning Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Good</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : (statsResource.data?.morning_coverage ?? '—') }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Evening Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : (statsResource.data?.evening_coverage ?? '—') }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Staff Off / Leave</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Info</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : (statsResource.data?.staff_off ?? statsResource.data?.on_leave ?? '—') }}</p>
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
        <div style="min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Outlet</p>
          <select v-model="filterOutlet" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Outlets</option>
            <option>Main Restaurant</option>
            <option>Bar Lounge</option>
            <option>Retail Corner</option>
          </select>
        </div>
        <template v-if="viewMode==='list'">
          <div style="min-width:130px;">
            <p class="text-xs text-gray-500 mb-1.5">Shift</p>
            <select v-model="filterShift" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">All Shifts</option>
              <option>Morning</option>
              <option>Evening</option>
              <option>Split Shift</option>
            </select>
          </div>
          <div style="min-width:130px;">
            <p class="text-xs text-gray-500 mb-1.5">Role</p>
            <select v-model="filterRole" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">All Roles</option>
              <option>Cashier</option>
              <option>Supervisor</option>
            </select>
          </div>
        </template>
        <template v-else>
          <div style="min-width:130px;">
            <p class="text-xs text-gray-500 mb-1.5">Role</p>
            <select v-model="filterRole" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">All Roles</option>
              <option>Cashier</option>
              <option>Supervisor</option>
            </select>
          </div>
        </template>
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
          <tr v-for="s in paginatedStaff" :key="`${s.name}-${s.start}-${s.shift}`" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ s.name }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.role }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.outlet }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.shift }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ s.start }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ s.end }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ s.offDay }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="s.status === 'Scheduled' ? 'bg-green-50 text-green-600' :
                        s.status === 'Review'    ? 'bg-yellow-50 text-yellow-600' :
                        s.status === 'Leave'     ? 'bg-gray-100 text-gray-500' :
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
        <div class="cal-grid">
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

  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const viewMode = ref(route.query.view === 'list' ? 'list' : 'calendar')
const searchText = ref('')
const filterOutlet = ref('')
const filterShift = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const weekOffset = ref(0)
const pageSize = 20

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

function parseDate(value) {
  if (!value || value === '—') return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

function isSameDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
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

function openNewPlan() {
  // Open ERPNext Shift Assignment form so managers can create a fresh roster plan.
  window.location.href = '/app/shift-assignment/new-shift-assignment'
}

// ── API: Staff Roster ──────────────────────────────────────────────────────
const rosterResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_staff_roster',
  auto: true,
})

const statsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_staff_roster_stats',
  auto: true,
})

let filterTimer = null
watch([searchText, filterOutlet, filterShift, filterRole], () => {
  currentPage.value = 1
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    rosterResource.params = {
      search: searchText.value || null,
      outlet: filterOutlet.value || null,
      shift: filterShift.value || null,
      role: filterRole.value || null,
    }
    rosterResource.reload()
  }, 300)
})

onBeforeUnmount(() => {
  clearTimeout(filterTimer)
})

// ── Computed: staff list ───────────────────────────────────────────────────
const allStaff = computed(() =>
  (rosterResource.data || []).map(s => ({
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

const filteredStaff = computed(() => {
  let data = allStaff.value
  if (filterOutlet.value) {
    const outlet = filterOutlet.value.toLowerCase()
    data = data.filter(s => (s.outlet || '').toLowerCase().includes(outlet))
  }
  if (filterShift.value) {
    const shift = filterShift.value.toLowerCase()
    data = data.filter(s => (s.shift || '').toLowerCase().includes(shift))
  }
  if (filterRole.value) {
    const role = filterRole.value.toLowerCase()
    data = data.filter(s => (s.role || '').toLowerCase().includes(role))
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    data = data.filter(s =>
      (s.name || '').toLowerCase().includes(q) ||
      (s.outlet || '').toLowerCase().includes(q) ||
      (s.role || '').toLowerCase().includes(q)
    )
  }
  return data
})

const outletCount = computed(() => new Set(filteredStaff.value.map(s => s.outlet).filter(Boolean)).size)
const shiftCount = computed(() => new Set(filteredStaff.value.map(s => s.shift).filter(Boolean)).size)

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

const weekRangeLabel = computed(() => {
  const first = weekDates.value[0]
  const last = weekDates.value[6]
  return `${FULL_DATE_FORMAT.format(first)} - ${FULL_DATE_FORMAT.format(last)}`
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredStaff.value.length / pageSize)))
const paginatedStaff = computed(() =>
  filteredStaff.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize)
)

function resetFilters() {
  searchText.value = ''
  filterOutlet.value = ''
  filterShift.value = ''
  filterRole.value = ''
  currentPage.value = 1
  rosterResource.params = {
    search: null,
    outlet: null,
    shift: null,
    role: null,
  }
  rosterResource.reload()
}

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