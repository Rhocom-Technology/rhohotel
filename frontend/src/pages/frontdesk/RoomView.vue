<template>
  <div class="space-y-4">

    <!-- AI Briefing Banner -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-center gap-2 mb-1.5">
        <span class="text-xs text-gray-400">AI front desk briefing</span>
        <span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">AI On</span>
        <span class="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Urgent</span>
      </div>
      <h2 class="text-base font-bold text-gray-900 leading-snug">
        {{ stats.overdue + stats.dirty }} rooms need immediate attention:
        {{ stats.overdue }} overdue check-outs, {{ stats.unpaid }} unpaid folios, and {{ stats.vip }} VIP arrival not yet pre-assigned.
      </h2>
      <p class="text-xs text-gray-400 mt-1">
        Recommended action order: clear the longest overdue rooms first, isolate unpaid departures, then release cleaned rooms back to sale.
      </p>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div v-for="stat in statCards" :key="stat.label" class="bg-white rounded-xl border border-gray-200 px-4 py-4">
        <p class="text-xs text-gray-400 mb-1">{{ stat.label }}</p>
        <p class="text-3xl font-bold text-gray-900">{{ stat.value }}</p>
        <p class="text-xs mt-1 font-medium" :style="{ color: stat.hexColor }">{{ stat.subtitle }}</p>
      </div>
    </div>

    <!-- Page Tabs -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-2 flex items-center gap-1 overflow-x-auto">
      <router-link
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="px-4 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors"
        :class="$route.path === tab.to ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
      >
        {{ tab.label }}
      </router-link>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-5 py-3 flex items-center gap-3 flex-wrap">
      <div class="relative" style="flex:1;min-width:160px;">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
        <input
          v-model="search"
          type="text"
          placeholder="Search room or guest"
          class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <select v-model="filterFloor" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
        <option value="">Floor</option>
        <option v-for="f in floors" :key="f" :value="f">Floor {{ f }}</option>
      </select>
      <select v-model="filterType" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
        <option value="">Room Type</option>
        <option v-for="t in roomTypes" :key="t" :value="t">{{ t }}</option>
      </select>
      <select v-model="filterStatus" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
        <option value="">Status</option>
        <option value="Vacant">Vacant</option>
        <option value="Occupied">Occupied</option>
        <option value="Reserved">Reserved</option>
        <option value="Maintenance">Maintenance</option>
      </select>
      <select v-model="filterHK" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
        <option value="">Housekeeping</option>
        <option value="Clean">Clean</option>
        <option value="Dirty">Dirty</option>
        <option value="In Progress">In Progress</option>
        <option value="Inspected">Inspected</option>
      </select>
      <button
        @click="filterOverdue = !filterOverdue"
        class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
        :style="filterOverdue ? 'background:#fef2f2;color:#ef4444;border-color:#fecaca' : 'color:#6b7280;border-color:#e5e7eb'"
      >Only Overdue</button>
      <button
        @click="filterVIP = !filterVIP"
        class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
        :style="filterVIP ? 'background:#f5f3ff;color:#7c3aed;border-color:#ddd6fe' : 'color:#6b7280;border-color:#e5e7eb'"
      >VIP</button>
      <button
        @click="filterDirty = !filterDirty"
        class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
        :style="filterDirty ? 'background:#fffbeb;color:#d97706;border-color:#fde68a' : 'color:#6b7280;border-color:#e5e7eb'"
      >Dirty Only</button>
      <button @click="refreshRooms" style="background:#2563eb;color:white;" class="px-4 py-2 text-xs font-semibold rounded-lg hover:opacity-90 transition-opacity">
        Refresh Grid
      </button>
    </div>

    <!-- Live Room Grid -->
    <div>
      <div class="mb-3">
        <h3 class="text-sm font-bold text-gray-900">Live Room Grid</h3>
        <p class="text-xs text-gray-400">Compact operational tiles for rapid front desk scanning and action</p>
      </div>

      <div v-if="filteredRooms.length === 0" class="bg-white rounded-xl border border-gray-200 flex flex-col items-center justify-center py-16">
        <p class="text-sm font-medium text-gray-400">No rooms match your filters</p>
      </div>

      <div v-else style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div
          v-for="room in filteredRooms"
          :key="room.name"
          class="rounded-xl p-4 border cursor-pointer hover:shadow-md transition-shadow"
          :style="roomCardStyle(room)"
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-2">
            <div>
              <p class="text-sm font-bold" :style="{ color: roomTextColor(room) }">Room {{ room.room_number }}</p>
              <p class="text-xs mt-0.5" style="color:#6b7280;">{{ room.room_type }} • Floor {{ room.floor }}</p>
            </div>
            <div class="flex flex-wrap gap-1 justify-end">
              <span v-if="room.unpaid" style="background:#fee2e2;color:#dc2626;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">UNPAID</span>
              <span v-if="room.overdue" style="background:#fff7ed;color:#ea580c;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">DUE</span>
              <span v-if="room.status === 'Reserved'" style="background:#ede9fe;color:#7c3aed;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">VIP</span>
              <span v-if="room.housekeeping_status === 'In Progress'" style="background:#fef9c3;color:#ca8a04;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">HK</span>
              <span v-if="room.status === 'Reserved'" style="background:#dbeafe;color:#2563eb;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">HOLD</span>
              <span v-if="room.status === 'Vacant' && (room.housekeeping_status === 'Clean' || room.housekeeping_status === 'Inspected')" style="background:#dcfce7;color:#16a34a;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">READY</span>
            </div>
          </div>

          <!-- Guest -->
          <p class="text-xs font-semibold truncate" style="color:#374151;">
            {{ room.current_guest || '\u00a0' }}
          </p>

          <!-- Status line -->
          <p class="text-xs font-semibold mt-1" :style="{ color: statusLineColor(room) }">
            {{ statusLine(room) }}
          </p>

          <!-- Subtitle -->
          <p class="text-xs mt-0.5 truncate" style="color:#9ca3af;">{{ room.subtitle }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search } from 'lucide-vue-next'

const search = ref('')
const filterFloor = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterHK = ref('')
const filterOverdue = ref(false)
const filterVIP = ref(false)
const filterDirty = ref(false)

const tabs = [
  { label: 'Room View', to: '/room-view' },
  { label: 'Check-ins', to: '/check-ins' },
  { label: 'Check-outs', to: '/check-outs' },
  { label: 'Reservations', to: '/reservations' },
  { label: 'Housekeeping', to: '/housekeeping' },
  { label: 'Payments', to: '/payments' },
  { label: 'Stay Report', to: '/stay-report' },
  { label: 'Night Audit', to: '/night-audit' },
]

const rooms = [
  // Floor 1
  { name: '101', room_number: '101', room_type: 'Standard King', floor: '1', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '102', room_number: '102', room_type: 'Deluxe Twin', floor: '1', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Sarah Johnson', overdue: false, unpaid: false, subtitle: 'Check-out: 21 Apr • 12:00 PM' },
  { name: '103', room_number: '103', room_type: 'Deluxe Twin', floor: '1', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Ngozi Cole', overdue: true, unpaid: true, subtitle: 'Check-out: 18 Apr • 12:00 PM' },
  { name: '104', room_number: '104', room_type: 'Standard King', floor: '1', status: 'Vacant', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Needs housekeeping attention' },
  { name: '105', room_number: '105', room_type: 'Deluxe Room', floor: '1', status: 'Maintenance', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Under maintenance' },
  { name: '106', room_number: '106', room_type: 'Standard King', floor: '1', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Emeka Adeyemi', overdue: false, unpaid: false, subtitle: 'Check-out: 22 Apr • 12:00 PM' },
  { name: '107', room_number: '107', room_type: 'Deluxe Room', floor: '1', status: 'Vacant', housekeeping_status: 'Inspected', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '108', room_number: '108', room_type: 'Deluxe Twin', floor: '1', status: 'Reserved', housekeeping_status: 'Clean', current_guest: 'Amina Yusuf', overdue: false, unpaid: false, subtitle: 'Arrival expected today 2:00 PM' },

  // Floor 2
  { name: '201', room_number: '201', room_type: 'Executive Suite', floor: '2', status: 'Occupied', housekeeping_status: 'In Progress', current_guest: 'Daniel Ayo', overdue: false, unpaid: false, subtitle: 'Check-out: 23 Apr • 12:00 PM' },
  { name: '202', room_number: '202', room_type: 'Executive Suite', floor: '2', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '203', room_number: '203', room_type: 'Premium Queen', floor: '2', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Michael Duke', overdue: true, unpaid: false, subtitle: 'Check-out: 17 Apr • 12:00 PM' },
  { name: '204', room_number: '204', room_type: 'Premium Queen', floor: '2', status: 'Vacant', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Needs housekeeping attention' },
  { name: '205', room_number: '205', room_type: 'Executive Suite', floor: '2', status: 'Reserved', housekeeping_status: 'Clean', current_guest: 'Apex Holdings', overdue: false, unpaid: false, subtitle: 'Arrival expected today 3:00 PM' },
  { name: '206', room_number: '206', room_type: 'Premium Queen', floor: '2', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Fatima Ahmed', overdue: false, unpaid: true, subtitle: 'Check-out: 24 Apr • 12:00 PM' },
  { name: '207', room_number: '207', room_type: 'Executive Suite', floor: '2', status: 'Vacant', housekeeping_status: 'Inspected', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '208', room_number: '208', room_type: 'Premium Queen', floor: '2', status: 'Maintenance', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Plumbing repair pending' },

  // Floor 3
  { name: '301', room_number: '301', room_type: 'Deluxe King', floor: '3', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Blessing Owen', overdue: false, unpaid: false, subtitle: 'Check-out: 22 Apr • 12:00 PM' },
  { name: '302', room_number: '302', room_type: 'Deluxe King', floor: '3', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '303', room_number: '303', room_type: 'Standard King', floor: '3', status: 'Reserved', housekeeping_status: 'Clean', current_guest: 'Zenith Bank Team', overdue: false, unpaid: false, subtitle: 'Arrival expected today 4:00 PM' },
  { name: '304', room_number: '304', room_type: 'Standard King', floor: '3', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Tunde Fashola', overdue: true, unpaid: true, subtitle: 'Check-out: 16 Apr • 12:00 PM' },
  { name: '305', room_number: '305', room_type: 'Executive Suite', floor: '3', status: 'Occupied', housekeeping_status: 'In Progress', current_guest: 'Grace Cole', overdue: false, unpaid: false, subtitle: 'Check-out: 25 Apr • 12:00 PM' },
  { name: '306', room_number: '306', room_type: 'Deluxe King', floor: '3', status: 'Vacant', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Needs housekeeping attention' },
  { name: '307', room_number: '307', room_type: 'Standard King', floor: '3', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Chibuzor Nweke', overdue: false, unpaid: false, subtitle: 'Check-out: 21 Apr • 12:00 PM' },
  { name: '308', room_number: '308', room_type: 'Deluxe King', floor: '3', status: 'Vacant', housekeeping_status: 'Inspected', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },

  // Floor 4
  { name: '401', room_number: '401', room_type: 'Presidential Suite', floor: '4', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '402', room_number: '402', room_type: 'Presidential Suite', floor: '4', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Emeka Obi', overdue: true, unpaid: true, subtitle: 'Check-out: 15 Apr • 12:00 PM' },
  { name: '403', room_number: '403', room_type: 'Deluxe Twin', floor: '4', status: 'Maintenance', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'HVAC repair pending' },
  { name: '404', room_number: '404', room_type: 'Deluxe Twin', floor: '4', status: 'Vacant', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Needs housekeeping attention' },
  { name: '405', room_number: '405', room_type: 'Premium Queen', floor: '4', status: 'Reserved', housekeeping_status: 'Clean', current_guest: 'Bamidele Cole', overdue: false, unpaid: false, subtitle: 'Arrival expected today 5:00 PM' },
  { name: '406', room_number: '406', room_type: 'Presidential Suite', floor: '4', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Rita James', overdue: false, unpaid: false, subtitle: 'Check-out: 26 Apr • 12:00 PM' },
  { name: '407', room_number: '407', room_type: 'Premium Queen', floor: '4', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '408', room_number: '408', room_type: 'Deluxe Twin', floor: '4', status: 'Occupied', housekeeping_status: 'In Progress', current_guest: 'Segun Ade', overdue: false, unpaid: false, subtitle: 'Check-out: 23 Apr • 12:00 PM' },

  // Floor 5
  { name: '501', room_number: '501', room_type: 'Standard King', floor: '5', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Halima Musa', overdue: false, unpaid: false, subtitle: 'Check-out: 24 Apr • 12:00 PM' },
  { name: '502', room_number: '502', room_type: 'Standard King', floor: '5', status: 'Vacant', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '503', room_number: '503', room_type: 'Executive Suite', floor: '5', status: 'Occupied', housekeeping_status: 'In Progress', current_guest: 'Biodun Fashola', overdue: false, unpaid: false, subtitle: 'Check-out: 22 Apr • 12:00 PM' },
  { name: '504', room_number: '504', room_type: 'Executive Suite', floor: '5', status: 'Vacant', housekeeping_status: 'Inspected', current_guest: '', overdue: false, unpaid: false, subtitle: 'Ready for walk-in or reservation' },
  { name: '505', room_number: '505', room_type: 'Standard King', floor: '5', status: 'Occupied', housekeeping_status: 'Clean', current_guest: 'Chioma Okafor', overdue: true, unpaid: false, subtitle: 'Check-out: 19 Apr • 12:00 PM' },
  { name: '506', room_number: '506', room_type: 'Executive Suite', floor: '5', status: 'Reserved', housekeeping_status: 'Clean', current_guest: 'Samuel Dada', overdue: false, unpaid: false, subtitle: 'Arrival expected today 1:00 PM' },
  { name: '507', room_number: '507', room_type: 'Standard King', floor: '5', status: 'Vacant', housekeeping_status: 'Dirty', current_guest: '', overdue: false, unpaid: false, subtitle: 'Needs housekeeping attention' },
  { name: '508', room_number: '508', room_type: 'Executive Suite', floor: '5', status: 'Maintenance', housekeeping_status: 'Clean', current_guest: '', overdue: false, unpaid: false, subtitle: 'Electrical work in progress' },
]

const floors = computed(() => [...new Set(rooms.map(r => r.floor))].sort())
const roomTypes = computed(() => [...new Set(rooms.map(r => r.room_type))].sort())

const stats = computed(() => ({
  vacant: rooms.filter(r => r.status === 'Vacant').length,
  occupied: rooms.filter(r => r.status === 'Occupied').length,
  reserved: rooms.filter(r => r.status === 'Reserved').length,
  dirty: rooms.filter(r => r.housekeeping_status === 'Dirty').length,
  maintenance: rooms.filter(r => r.status === 'Maintenance').length,
  overdue: rooms.filter(r => r.overdue).length,
  unpaid: rooms.filter(r => r.unpaid).length,
  vip: 1,
}))

const statCards = computed(() => [
  { label: 'Vacant Rooms', value: stats.value.vacant, subtitle: 'Ready for sale', hexColor: '#22c55e' },
  { label: 'Occupied', value: stats.value.occupied, subtitle: 'Live stays', hexColor: '#3b82f6' },
  { label: 'Reserved Today', value: stats.value.reserved, subtitle: 'Incoming arrivals', hexColor: '#8b5cf6' },
  { label: 'Dirty Rooms', value: stats.value.dirty, subtitle: 'Housekeeping queue', hexColor: '#f97316' },
  { label: 'Maintenance', value: stats.value.maintenance, subtitle: 'Out of order', hexColor: '#6b7280' },
  { label: 'Overdue Check-outs', value: stats.value.overdue, subtitle: 'Immediate desk action', hexColor: '#ef4444' },
])

const filteredRooms = computed(() => {
  let list = rooms
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.room_number?.toLowerCase().includes(q) ||
      r.current_guest?.toLowerCase().includes(q) ||
      r.room_type?.toLowerCase().includes(q)
    )
  }
  if (filterFloor.value) list = list.filter(r => r.floor === filterFloor.value)
  if (filterType.value) list = list.filter(r => r.room_type === filterType.value)
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  if (filterHK.value) list = list.filter(r => r.housekeeping_status === filterHK.value)
  if (filterOverdue.value) list = list.filter(r => r.overdue)
  if (filterVIP.value) list = list.filter(r => r.status === 'Reserved')
  if (filterDirty.value) list = list.filter(r => r.housekeeping_status === 'Dirty')
  return list
})

function roomCardStyle(room) {
  if (room.overdue) return 'background:#fff1f2;border-color:#fecdd3;border-left:4px solid #ef4444;'
  if (room.status === 'Vacant' && (room.housekeeping_status === 'Clean' || room.housekeeping_status === 'Inspected')) return 'background:#f0fdf4;border-color:#bbf7d0;border-left:4px solid #22c55e;'
  if (room.status === 'Vacant' && room.housekeeping_status === 'Dirty') return 'background:#fffbeb;border-color:#fde68a;border-left:4px solid #f59e0b;'
  if (room.status === 'Occupied') return 'background:#eff6ff;border-color:#bfdbfe;border-left:4px solid #3b82f6;'
  if (room.status === 'Reserved') return 'background:#f5f3ff;border-color:#ddd6fe;border-left:4px solid #8b5cf6;'
  if (room.status === 'Maintenance') return 'background:#f9fafb;border-color:#e5e7eb;border-left:4px solid #9ca3af;'
  if (room.housekeeping_status === 'In Progress') return 'background:#fffbeb;border-color:#fde68a;border-left:4px solid #f59e0b;'
  return 'background:white;border-color:#e5e7eb;border-left:4px solid #e5e7eb;'
}

function roomTextColor(room) {
  if (room.overdue) return '#991b1b'
  if (room.status === 'Vacant') return '#166534'
  if (room.status === 'Occupied') return '#1e40af'
  if (room.status === 'Reserved') return '#5b21b6'
  return '#111827'
}

function statusLineColor(room) {
  if (room.overdue) return '#ef4444'
  if (room.status === 'Vacant' && (room.housekeeping_status === 'Clean' || room.housekeeping_status === 'Inspected')) return '#22c55e'
  if (room.status === 'Vacant' && room.housekeeping_status === 'Dirty') return '#f59e0b'
  if (room.status === 'Reserved') return '#8b5cf6'
  if (room.housekeeping_status === 'In Progress') return '#f59e0b'
  if (room.status === 'Maintenance') return '#6b7280'
  return '#374151'
}

function statusLine(room) {
  if (room.overdue) return 'Overdue check-out'
  if (room.status === 'Vacant' && (room.housekeeping_status === 'Clean' || room.housekeeping_status === 'Inspected')) return 'Vacant and clean'
  if (room.status === 'Vacant' && room.housekeeping_status === 'Dirty') return 'Vacant but dirty'
  if (room.status === 'Maintenance') return 'In maintenance'
  if (room.housekeeping_status === 'In Progress') return 'Cleaning in progress'
  if (room.status === 'Reserved') return 'Reserved for today'
  if (room.status === 'Occupied') return 'Occupied'
  return room.status || '—'
}

function refreshRooms() {
  // dummy — no-op with dummy data
}
</script>