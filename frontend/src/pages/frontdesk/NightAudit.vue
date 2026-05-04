<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div class="flex items-start justify-between">
      <div>
        <p class="text-xs text-gray-400 mb-1">Front Desk / Night Audit</p>
        <h1 class="text-2xl font-bold text-gray-900">Night Audit</h1>
        <p class="text-xs text-gray-400 mt-1">Daily revenue reconciliation, occupancy snapshot, and guest ledger review.</p>
      </div>
      <div class="flex items-center gap-2">
        <input
          v-model="auditDate"
          type="date"
          class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button @click="loadData" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Refresh
        </button>
        <button @click="printAudit" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
          Print Report
        </button>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="resource.loading" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <p class="text-sm text-gray-400">Loading audit data…</p>
    </div>
    <div v-else-if="resource.error" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <p class="text-sm font-medium text-red-500">Failed to load audit data.</p>
      <button @click="loadData" class="mt-3 px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Retry</button>
    </div>

    <template v-else-if="data">

      <!-- Audit Date Banner -->
      <div class="bg-blue-50 border border-blue-200 rounded-xl px-6 py-3 flex items-center justify-between">
        <p class="text-sm font-semibold text-blue-800">
          Audit Date: {{ formatDisplayDate(data.audit_date) }}
        </p>
        <span class="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
          {{ data.occupancy.occupancy_pct }}% Occupancy
        </span>
      </div>

      <!-- Stat Cards -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Total Revenue</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ fmt(data.revenue.total_revenue) }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ fmt(data.payments.total_collected) }} collected</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Occupied Rooms</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ data.occupancy.occupied }} / {{ data.occupancy.total_rooms }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ data.occupancy.vacant }} vacant</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Arrivals / Departures</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">Today</span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ data.occupancy.arrivals }} / {{ data.occupancy.departures }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ data.occupancy.reserved }} reserved</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Outstanding Balance</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">{{ data.outstanding.guest_count }} guests</span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ fmt(data.outstanding.total_outstanding) }}</p>
          <p class="text-xs text-gray-400 mt-1">pending collection</p>
        </div>
      </div>

      <!-- Revenue & Payments Row -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

        <!-- Revenue Breakdown -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Revenue Breakdown</h3>
            <p class="text-xs text-gray-400 mt-0.5">Charges posted for {{ formatDisplayDate(data.audit_date) }}</p>
          </div>
          <div class="px-6 py-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
                <p class="text-xs text-gray-600">Room Charges</p>
              </div>
              <p class="text-xs font-semibold text-gray-900">{{ fmt(data.revenue.room_revenue) }}</p>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-orange-400 inline-block"></span>
                <p class="text-xs text-gray-600">Food & Beverage</p>
              </div>
              <p class="text-xs font-semibold text-gray-900">{{ fmt(data.revenue.fnb_revenue) }}</p>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-gray-300 inline-block"></span>
                <p class="text-xs text-gray-600">Other Charges</p>
              </div>
              <p class="text-xs font-semibold text-gray-900">{{ fmt(data.revenue.other_revenue) }}</p>
            </div>
            <div class="border-t border-gray-100 pt-3 flex items-center justify-between">
              <p class="text-xs font-bold text-gray-900">Total Revenue</p>
              <p class="text-sm font-bold text-green-600">{{ fmt(data.revenue.total_revenue) }}</p>
            </div>
          </div>
          <!-- By Room Type -->
          <div v-if="data.revenue.by_room_type.length" class="px-6 pb-4">
            <p class="text-xs text-gray-400 mb-2">By Room Type</p>
            <div v-for="rt in data.revenue.by_room_type" :key="rt.room_type" class="flex items-center justify-between mb-1.5">
              <p class="text-xs text-gray-500">{{ rt.room_type }}</p>
              <p class="text-xs font-medium text-gray-700">{{ fmt(rt.revenue) }}</p>
            </div>
          </div>
        </div>

        <!-- Payment Reconciliation -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Payment Reconciliation</h3>
            <p class="text-xs text-gray-400 mt-0.5">Receipts collected on {{ formatDisplayDate(data.audit_date) }}</p>
          </div>
          <div v-if="data.payments.by_method.length" class="px-6 py-4 space-y-3">
            <div
              v-for="m in data.payments.by_method"
              :key="m.method"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full inline-block" :class="methodDotClass(m.method)"></span>
                <p class="text-xs text-gray-600">{{ m.method }}</p>
                <span class="text-xs text-gray-400">({{ m.count }} txn{{ m.count !== 1 ? 's' : '' }})</span>
              </div>
              <p class="text-xs font-semibold text-gray-900">{{ fmt(m.amount) }}</p>
            </div>
            <div class="border-t border-gray-100 pt-3 flex items-center justify-between">
              <p class="text-xs font-bold text-gray-900">Total Collected</p>
              <p class="text-sm font-bold text-green-600">{{ fmt(data.payments.total_collected) }}</p>
            </div>
          </div>
          <div v-else class="px-6 py-8 text-center">
            <p class="text-xs text-gray-400">No payments recorded for this date.</p>
          </div>
        </div>
      </div>

      <!-- Occupancy Summary -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Occupancy Summary</h3>
        </div>
        <div class="px-6 py-4">
          <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:16px;">
            <div class="text-center">
              <p class="text-2xl font-bold text-gray-900">{{ data.occupancy.total_rooms }}</p>
              <p class="text-xs text-gray-400 mt-1">Total Rooms</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-green-600">{{ data.occupancy.occupied }}</p>
              <p class="text-xs text-gray-400 mt-1">Occupied</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-gray-400">{{ data.occupancy.vacant }}</p>
              <p class="text-xs text-gray-400 mt-1">Vacant</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-blue-500">{{ data.occupancy.reserved }}</p>
              <p class="text-xs text-gray-400 mt-1">Reserved</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-purple-500">{{ data.occupancy.arrivals }}</p>
              <p class="text-xs text-gray-400 mt-1">Arrivals</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-orange-500">{{ data.occupancy.departures }}</p>
              <p class="text-xs text-gray-400 mt-1">Departures</p>
            </div>
          </div>
          <!-- Occupancy bar -->
          <div class="mt-4">
            <div class="flex items-center justify-between mb-1">
              <p class="text-xs text-gray-400">Occupancy Rate</p>
              <p class="text-xs font-semibold text-gray-700">{{ data.occupancy.occupancy_pct }}%</p>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="occupancyBarClass(data.occupancy.occupancy_pct)"
                :style="{ width: data.occupancy.occupancy_pct + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Guest Ledger (Outstanding) -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Guest Ledger — Outstanding Balances</h3>
            <p class="text-xs text-gray-400 mt-0.5">Guests with unpaid balances currently in house</p>
          </div>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">{{ data.outstanding.guest_count }} accounts</span>
        </div>
        <div v-if="data.outstanding.ledger.length" class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Check-in</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Room</th>
                <th class="text-right text-xs font-semibold text-gray-400 px-6 py-3">Outstanding</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="row in data.outstanding.ledger"
                :key="row.check_in"
                class="hover:bg-gray-50 cursor-pointer transition-colors"
                @click="router.push('/check-ins/' + row.check_in)"
              >
                <td class="px-6 py-3 text-xs font-mono text-blue-600">{{ row.check_in }}</td>
                <td class="px-4 py-3 text-xs font-semibold text-gray-800">{{ row.guest }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ row.room }}</td>
                <td class="px-6 py-3 text-xs font-bold text-red-600 text-right">{{ fmt(row.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-8 text-center">
          <p class="text-xs text-gray-400">No outstanding balances. All guests are settled.</p>
        </div>
      </div>

      <!-- Room Status Snapshot -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Room Status Snapshot</h3>
            <p class="text-xs text-gray-400 mt-0.5">Current state of all rooms</p>
          </div>
          <div class="flex items-center gap-2">
            <input
              v-model="roomSearch"
              type="text"
              placeholder="Search room…"
              class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
            />
            <select v-model="roomStatusFilter" class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">All Statuses</option>
              <option value="Occupied">Occupied</option>
              <option value="Vacant">Vacant</option>
              <option value="Reserved">Reserved</option>
              <option value="Maintenance">Maintenance</option>
            </select>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Room</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Type</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Floor</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">HK Status</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="rm in filteredRooms"
                :key="rm.room_number"
                class="hover:bg-gray-50 transition-colors"
              >
                <td class="px-6 py-3 text-xs font-bold text-gray-900">{{ rm.room_number }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ rm.room_type }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ rm.floor }}</td>
                <td class="px-4 py-3">
                  <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full" :class="roomStatusClass(rm.status)">
                    {{ rm.status }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="hkStatusClass(rm.housekeeping_status)">
                    {{ rm.housekeeping_status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ rm.guest || '—' }}</td>
              </tr>
              <tr v-if="!filteredRooms.length">
                <td colspan="6" class="px-6 py-8 text-center text-xs text-gray-400">No rooms match the filter.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Room table pagination -->
        <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
          <p class="text-xs text-gray-400">Showing {{ filteredRooms.length }} of {{ data.room_status.length }} rooms</p>
          <div v-if="totalRoomPages > 1" class="flex items-center gap-1">
            <button
              v-for="p in Math.min(totalRoomPages, 6)"
              :key="p"
              @click="roomPage = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center transition-colors"
              :class="roomPage === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            >{{ p }}</button>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()

const today = new Date().toISOString().slice(0, 10)
const auditDate = ref(today)
const roomSearch = ref('')
const roomStatusFilter = ref('')
const roomPage = ref(1)
const roomPageSize = 30

const resource = createResource({
  url: 'rhohotel.rhocom_hotel.api.front_desk.get_night_audit_data',
  params: { audit_date: auditDate.value },
  auto: true,
})

const data = computed(() => resource.data || null)

function loadData() {
  resource.params = { audit_date: auditDate.value }
  resource.reload()
}

watch(auditDate, () => {
  loadData()
})

// ── Room snapshot filtering & pagination ──────────────────────────────────
const filteredRoomsAll = computed(() => {
  if (!data.value) return []
  let list = data.value.room_status
  if (roomSearch.value) {
    const q = roomSearch.value.toLowerCase()
    list = list.filter(r =>
      r.room_number.toLowerCase().includes(q) ||
      r.room_type.toLowerCase().includes(q) ||
      (r.guest || '').toLowerCase().includes(q) ||
      String(r.floor).toLowerCase().includes(q)
    )
  }
  if (roomStatusFilter.value) {
    list = list.filter(r => r.status === roomStatusFilter.value)
  }
  return list
})

const totalRoomPages = computed(() => Math.max(1, Math.ceil(filteredRoomsAll.value.length / roomPageSize)))
const filteredRooms = computed(() =>
  filteredRoomsAll.value.slice((roomPage.value - 1) * roomPageSize, roomPage.value * roomPageSize)
)

watch([roomSearch, roomStatusFilter], () => { roomPage.value = 1 })

// ── Helpers ───────────────────────────────────────────────────────────────
function fmt(amount) {
  return `₦${Number(amount || 0).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDisplayDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
}

function roomStatusClass(status) {
  return {
    'Occupied': 'bg-green-100 text-green-700',
    'Vacant': 'bg-gray-100 text-gray-500',
    'Reserved': 'bg-blue-100 text-blue-600',
    'Maintenance': 'bg-red-100 text-red-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

function hkStatusClass(status) {
  return {
    'Clean': 'bg-green-50 text-green-600',
    'Dirty': 'bg-yellow-100 text-yellow-600',
    'In Progress': 'bg-blue-50 text-blue-600',
    'Inspected': 'bg-purple-50 text-purple-600',
  }[status] || 'bg-gray-50 text-gray-400'
}

function methodDotClass(method) {
  const map = {
    'Cash': 'bg-green-500',
    'Card': 'bg-blue-500',
    'POS': 'bg-purple-500',
    'Bank Transfer': 'bg-orange-400',
  }
  return map[method] || 'bg-gray-400'
}

function occupancyBarClass(pct) {
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 50) return 'bg-blue-500'
  if (pct >= 30) return 'bg-yellow-400'
  return 'bg-red-400'
}

function printAudit() {
  window.print()
}
</script>
