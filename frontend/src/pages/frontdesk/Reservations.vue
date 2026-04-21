<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Reservations / Reservation List</p>
      <h1 class="text-2xl font-bold text-gray-900">Reservation List</h1>
      <p class="text-xs text-gray-400 mt-1">View, filter, search, and manage all saved, checked-in, pending, and cancelled reservations.</p>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Reservations</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">This Month</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Arrival</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.pendingArrivalToday }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Checked In</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">In House</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.checkedIn }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Booked Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Total</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(stats.bookedValue) }}</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search reservation / guest</p>
          <input v-model="search" type="text" placeholder="Reservation no., guest, company..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Checked In">Checked In</option>
            <option value="Checked Out">Checked Out</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Pending">Pending</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Arrival Date</p>
          <input v-model="filterArrival" type="date" placeholder="Today"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600" />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Source</p>
          <select v-model="filterSource" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Sources</option>
            <option value="Individual">Individual</option>
            <option value="Corporate">Corporate</option>
          </select>
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button @click="showNewReservation = true" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            New Reservation
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">All Reservations</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ Math.min(pageSize, filteredList.length) }} of {{ filteredList.length.toLocaleString() }} reservations</p>
      </div>

      <div v-if="reservationResource.loading" class="flex items-center justify-center py-14">
        <p class="text-sm text-gray-400">Loading reservations...</p>
      </div>

      <div v-else-if="reservationResource.error" class="px-6 py-10 text-center">
        <p class="text-sm font-medium text-red-500">Unable to load reservations.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Reservation</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest / Company</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Stay</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Room</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Amount</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="item in paginatedList"
              :key="item.name"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
              @click="openReservation(item)"
            >
              <td class="px-6 py-4">
                <p class="text-xs font-bold text-gray-900">{{ item.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.reservation_type }}</p>
              </td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.primary_guest_name }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.reservation_type === 'Corporate' ? (item.customer || 'Corporate') : 'Individual Guest' }}</p>
              </td>
              <td class="px-4 py-4">
                <p class="text-xs text-gray-700">{{ formatDateShort(item.from_date) }} – {{ formatDateShort(item.to_date) }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.number_of_nights }} Night{{ item.number_of_nights !== 1 ? 's' : '' }}</p>
              </td>
              <td class="px-4 py-4">
                <p class="text-xs text-gray-700">{{ item.total_rooms }} {{ item.total_rooms > 1 ? 'Rooms' : 'Room' }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.room_type || 'Various' }}</p>
              </td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">
                {{ formatCurrency(item.total_amount) }}
              </td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(item.statusLabel)">
                  {{ item.statusLabel }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button
                  @click.stop="openReservation(item)"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  Open
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button
              v-for="p in Math.min(totalPages, 5)"
              :key="p"
              @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center transition-colors"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            >{{ p }}</button>
            <span v-if="totalPages > 5" class="text-xs text-gray-400">... {{ totalPages }}</span>
          </div>
          <button
            @click="page = Math.min(page + 1, totalPages)"
            :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
          >Next</button>
        </div>
      </div>
    </div>

    <!-- New Reservation Type Selector Modal -->
    <Teleport to="body">
      <div v-if="showNewReservation" class="fixed inset-0 z-50 flex items-center justify-center" style="background:rgba(0,0,0,0.55);" @click.self="showNewReservation = false">
        <div class="bg-white rounded-2xl shadow-2xl p-8 w-full mx-4" style="max-width:400px;">
          <h2 class="text-lg font-bold text-gray-900 mb-2">New Reservation</h2>
          <p class="text-xs text-gray-400 mb-6">Select the reservation type to continue.</p>
          <div class="grid grid-cols-2 gap-4">
            <button
              @click="startNewReservation('Individual')"
              class="flex flex-col items-center gap-3 p-5 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <User class="w-8 h-8 text-gray-400 group-hover:text-blue-500" />
              <div class="text-center">
                <p class="text-sm font-bold text-gray-900">Individual</p>
                <p class="text-xs text-gray-400 mt-0.5">Single guest booking</p>
              </div>
            </button>
            <button
              @click="startNewReservation('Corporate')"
              class="flex flex-col items-center gap-3 p-5 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <Building2 class="w-8 h-8 text-gray-400 group-hover:text-blue-500" />
              <div class="text-center">
                <p class="text-sm font-bold text-gray-900">Corporate</p>
                <p class="text-xs text-gray-400 mt-0.5">Bulk group booking</p>
              </div>
            </button>
          </div>
          <button @click="showNewReservation = false" class="w-full mt-4 py-2 text-xs text-gray-400 hover:text-gray-600">Cancel</button>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { User, Building2 } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'

const router = useRouter()
const search = ref('')
const filterStatus = ref('')
const filterArrival = ref('')
const filterSource = ref('')
const page = ref(1)
const pageSize = 10
const showNewReservation = ref(false)

const reservationResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Front Desk Reservation',
    fields: [
      'name',
      'reservation_type',
      'primary_guest_name',
      'customer',
      'from_date',
      'to_date',
      'number_of_nights',
      'total_rooms',
      'total_amount',
      'status',
      'docstatus',
    ],
    order_by: 'creation desc',
    limit_page_length: 500,
  },
  auto: true,
})

const reservations = computed(() => (reservationResource.data || []).map((row) => ({
  ...row,
  reservation_type: row.reservation_type || 'Individual',
  primary_guest_name: row.primary_guest_name || '—',
  total_rooms: Number(row.total_rooms || 0),
  total_amount: Number(row.total_amount || 0),
  number_of_nights: Number(row.number_of_nights || 0),
  statusLabel: mapReservationStatus(row),
})))

const stats = computed(() => ({
  total: reservations.value.length,
  pendingArrivalToday: reservations.value.filter((r) => isToday(r.from_date) && ['Confirmed', 'Pending', 'Due Today'].includes(r.statusLabel)).length,
  checkedIn: reservations.value.filter((r) => r.statusLabel === 'Checked In').length,
  bookedValue: reservations.value.reduce((sum, r) => sum + Number(r.total_amount || 0), 0),
}))

const filteredList = computed(() => {
  let list = reservations.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.name.toLowerCase().includes(q) ||
      r.primary_guest_name.toLowerCase().includes(q) ||
      String(r.customer || '').toLowerCase().includes(q)
    )
  }
  if (filterStatus.value) list = list.filter(r => r.statusLabel === filterStatus.value)
  if (filterSource.value) list = list.filter(r => r.reservation_type === filterSource.value)
  if (filterArrival.value) list = list.filter(r => r.from_date === filterArrival.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterStatus.value = ''
  filterArrival.value = ''
  filterSource.value = ''
  page.value = 1
}

function statusClass(status) {
  return {
    'Confirmed': 'bg-blue-50 text-blue-600',
    'Checked In': 'bg-green-50 text-green-600',
    'Checked Out': 'bg-gray-100 text-gray-500',
    'Cancelled': 'bg-red-50 text-red-500',
    'Pending': 'bg-yellow-50 text-yellow-600',
    'Due Today': 'bg-orange-50 text-orange-600',
    'Partly Paid': 'bg-yellow-50 text-yellow-600',
  }[status] || 'bg-gray-100 text-gray-500'
}

function formatDateShort(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

function formatCurrency(amount) {
  if (!amount) return '₦0'
  return `₦${Number(amount).toLocaleString('en-NG')}`
}

function startNewReservation(type) {
  showNewReservation.value = false
  router.push({ name: 'NewReservation', query: { type } })
}

function openReservation(item) {
  router.push({ name: 'SavedReservation', params: { id: item.name } })
}

function mapReservationStatus(item) {
  const rawStatus = item.status || ''
  if (rawStatus) {
    if (rawStatus.toLowerCase() === 'checked in') return 'Checked In'
    if (rawStatus.toLowerCase() === 'checked out') return 'Checked Out'
    if (rawStatus.toLowerCase() === 'cancelled') return 'Cancelled'
    if (rawStatus.toLowerCase() === 'pending') return 'Pending'
    if (rawStatus.toLowerCase() === 'confirmed') return 'Confirmed'
    return rawStatus
  }
  if (Number(item.docstatus) === 2) return 'Cancelled'
  if (isToday(item.from_date)) return 'Due Today'
  if (Number(item.docstatus) === 1) return 'Confirmed'
  return 'Pending'
}

function isToday(dateValue) {
  if (!dateValue) return false
  const today = new Date()
  const date = new Date(dateValue)
  return date.toDateString() === today.toDateString()
}

watch([search, filterStatus, filterArrival, filterSource], () => {
  page.value = 1
})
</script>