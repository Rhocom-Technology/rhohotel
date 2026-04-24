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
        <p class="text-xs text-gray-400 mt-0.5">Current week scheduling for 12 POS staff across 3 active outlets and 2 daily shifts.</p>
      </div>
      <div class="flex items-center gap-2">
        <button v-if="viewMode==='calendar'" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Prev Week</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">This Week</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Roaster</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">{{ viewMode === 'calendar' ? 'New Plan' : 'Create Shift Plan' }}</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Scheduled POS Staff</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Week</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">12</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Morning Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Good</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">100%</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Evening Coverage</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">83%</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Staff Off / Leave</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Info</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">2</p>
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
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>All Roles</option>
              <option>Cashier</option>
              <option>Supervisor</option>
            </select>
          </div>
        </template>
        <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
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
        <p class="text-xs text-gray-400">Week: 15 Apr – 21 Apr 2026</p>
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
          <tr v-for="s in paginatedStaff" :key="s.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
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
          <button v-for="p in totalPages" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <span class="text-xs text-gray-400 px-1">...</span>
          <span class="w-7 h-7 flex items-center justify-center text-xs text-gray-600 border border-gray-200 rounded-lg">8</span>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

    <!-- Calendar View -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Weekly Roaster Calendar</h3>
        <p class="text-xs text-gray-400">Week: 15 Apr – 21 Apr 2026</p>
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
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const viewMode = ref(route.query.view === 'list' ? 'list' : 'calendar')
const searchText = ref('')
const filterOutlet = ref('')
const filterShift = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const pageSize = 5

const staffList = [
  { name: 'Adaeze Okafor',    role: 'Cashier',    outlet: 'Main Restaurant', shift: 'Morning',     start: '07:00 AM', end: '03:00 PM', offDay: 'Sunday',    status: 'Scheduled' },
  { name: 'Ifeoma Nnaji',     role: 'Cashier',    outlet: 'Bar Lounge',      shift: 'Morning',     start: '07:00 AM', end: '03:00 PM', offDay: 'Wednesday', status: 'Scheduled' },
  { name: 'Boma Eze',         role: 'Cashier',    outlet: 'Retail Corner',   shift: 'Evening',     start: '03:00 PM', end: '11:00 PM', offDay: 'Tuesday',   status: 'Review' },
  { name: 'Ngozi Umeh',       role: 'Supervisor', outlet: 'Main Restaurant', shift: 'Split Shift', start: '10:00 AM', end: '08:00 PM', offDay: 'Friday',    status: 'Scheduled' },
  { name: 'Daniel Bassey',    role: 'Cashier',    outlet: 'Bar Lounge',      shift: 'Evening',     start: '03:00 PM', end: '11:00 PM', offDay: 'Monday',    status: 'Leave' },
  { name: 'Chukwuemeka Eze',  role: 'Cashier',    outlet: 'Main Restaurant', shift: 'Morning',     start: '07:00 AM', end: '03:00 PM', offDay: 'Thursday',  status: 'Scheduled' },
  { name: 'Fatima Abubakar',  role: 'Supervisor', outlet: 'Bar Lounge',      shift: 'Morning',     start: '07:00 AM', end: '03:00 PM', offDay: 'Saturday',  status: 'Scheduled' },
  { name: 'Seun Adeyemi',     role: 'Cashier',    outlet: 'Retail Corner',   shift: 'Morning',     start: '07:00 AM', end: '03:00 PM', offDay: 'Sunday',    status: 'Scheduled' },
]

const totalPages = computed(() => Math.ceil(staffList.length / pageSize))
const paginatedStaff = computed(() => staffList.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))

const timeSlots = ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00']

const calDays = [
  { date: '15', label: 'Mon 15', outlet: 'Restaurant', slots: [
    { id: 1, title: 'Morning Shift', name: 'Adaeze Okafor', role: 'Cashier', time: '07:00 AM – 03:00 PM', outlet: 'Main Restaurant', color: 'ev-blue', top: 50, height: 130 },
    { id: 2, title: 'Evening Shift', name: 'Daniel Bassey', role: 'Cashier', time: '03:00 PM – 11:00 PM', outlet: 'Backup Cover', color: 'ev-blue-light', top: 220, height: 130 },
  ]},
  { date: '16', label: 'Tue 16', outlet: 'Bar Lounge', slots: [
    { id: 3, title: 'Morning Shift', name: 'Ifeoma Nnaji', role: 'Cashier', time: '07:00 AM – 03:00 PM', outlet: 'Bar Lounge', color: 'ev-purple', top: 50, height: 130 },
    { id: 4, title: '', name: 'Off Day', role: '', time: '', outlet: '', color: 'ev-offday', top: 330, height: 50 },
  ]},
  { date: '17', label: 'Wed 17', outlet: 'Retail Corner', slots: [
    { id: 5, title: '', name: 'Relief Slot', role: '', time: '', outlet: '', color: 'ev-gray', top: 50, height: 80 },
    { id: 6, title: 'Evening Shift', name: 'Boma Eze', role: 'Cashier', time: '03:00 PM – 11:00 PM', outlet: 'Retail Corner', color: 'ev-yellow', top: 220, height: 130 },
  ]},
  { date: '18', label: 'Thu 18', outlet: 'Restaurant', slots: [
    { id: 7, title: 'Supervisor Split', name: 'Ngozi Umeh', role: 'Supervisor', time: '10:00 AM – 08:00 PM', outlet: 'Restaurant Oversight', color: 'ev-green', top: 90, height: 170 },
  ]},
  { date: '19', label: 'Fri 19', outlet: 'Bar Lounge', slots: [
    { id: 8, title: 'Morning Shift', name: 'Adaeze Okafor', role: 'Cashier', time: '07:00 AM – 03:00 PM', outlet: 'Bar Lounge Cover', color: 'ev-blue', top: 50, height: 130 },
    { id: 9, title: 'Evening Shift', name: 'Daniel Bassey', role: 'Cashier', time: '03:00 PM – 11:00 PM', outlet: 'Bar Lounge', color: 'ev-blue-light', top: 220, height: 130 },
  ]},
  { date: '20', label: 'Sat 20', outlet: 'Restaurant', slots: [
    { id: 10, title: 'Morning Shift', name: 'Adaeze Okafor', role: 'Cashier', time: '07:00 AM – 03:00 PM', outlet: 'Weekend Rush', color: 'ev-blue', top: 50, height: 130 },
    { id: 11, title: 'Evening Shift', name: 'Ifeoma Nnaji', role: 'Cashier', time: '03:00 PM – 11:00 PM', outlet: 'Weekend Cover', color: 'ev-purple', top: 220, height: 130 },
  ]},
  { date: '21', label: 'Sun 21', outlet: 'Mixed', slots: [
    { id: 12, title: '', name: 'Off / Leave', role: '', time: '', outlet: '', color: 'ev-offday', top: 50, height: 60 },
    { id: 13, title: 'Skeleton Team', name: '2 Cashiers', role: '', time: '10:00 AM – 06:00 PM', outlet: 'Restaurant / Bar', color: 'ev-green', top: 150, height: 120 },
  ]},
]
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