<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Front desk • overdue departure monitoring</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end gap-2">
      <button @click="refreshData" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
      <button @click="exportOverdue" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Overdue</button>
      <button @click="startCheckout" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Start Check-out</button>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="rounded-xl px-5 py-4" style="background:#e8d5d5;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-600">Overdue Departures</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Urgent</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statCards.overdueDepartures }}</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#e8d5d5;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-600">Balance Due</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statCards.balanceDue }}</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#e0d5e8;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-600">Extension Requests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statCards.extensionRequests }}</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#d5e0c8;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-600">Awaiting Inspection</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statCards.awaitingInspection }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">Search guest / folio</p>
          <input v-model="search" type="text" placeholder="Guest name, folio, room..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <button
            class="w-full px-4 py-2.5 text-xs font-semibold rounded-lg transition-colors"
            :class="overdueOnly ? 'bg-red-50 text-red-500 border border-red-200' : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'"
            @click="overdueOnly = !overdueOnly">
            {{ overdueOnly ? 'Overdue Only' : 'All Statuses' }}
          </button>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Status</p>
          <select v-model="filterPayment" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Payments</option>
            <option>Settled</option>
            <option>Balance Due</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
          <select v-model="filterRoom" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Rooms</option>
            <option>Occupied</option>
            <option>Vacant</option>
          </select>
        </div>
        <button @click="search='';overdueOnly=true;filterPayment='';filterRoom='';currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply Filter</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Overdue Check-out Records</h3>
        <p class="text-xs text-gray-400">Showing {{ filtered.length ? pageStart + 1 : 0 }}–{{ pageEnd }} of {{ filtered.length }} overdue departures</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Folio No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest Name</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Expected Check-out</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Payment</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Overdue By</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in paged" :key="r.folio"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.folio }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ r.guest }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.room }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.expectedCheckout }}</td>
            <td class="px-4 py-4 text-xs font-semibold"
              :class="r.payment === 'Balance Due' ? 'text-red-500' : 'text-green-600'">
              {{ r.payment }}
            </td>
            <td class="px-4 py-4 text-xs font-bold text-red-500">{{ r.overdueBy }}</td>
            <td class="px-4 py-4">
              <button v-if="r.payment === 'Balance Due'"
                class="px-3 py-1.5 text-xs font-semibold text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
                @click="$router.push('/check-outs/' + r.folio)">View</button>
              <button v-else
                class="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                @click="$router.push('/check-outs/' + r.folio)">Check Out</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
          <button v-for="p in totalPages" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage = Math.min(currentPage + 1, totalPages)" class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const search = ref('')
const overdueOnly = ref(true)
const filterPayment = ref('')
const filterRoom = ref('')
const currentPage = ref(1)
const perPage = 25

const roomViewResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.front_desk.get_room_view_data',
  params: {
    filters: {
      only_overdue: true,
    },
  },
  auto: true,
})

const roomViewPayload = computed(() => {
  const data = roomViewResource.data || {}
  return data.message || data
})

const records = computed(() => {
  const rows = roomViewPayload.value.rooms || []
  return rows.map((row) => {
    const expectedCheckoutDate = row.expected_check_out_datetime ? new Date(row.expected_check_out_datetime) : null
    return {
      folio: row.check_in || row.name,
      guest: row.current_guest || '—',
      room: row.room_number || row.name,
      roomStatus: row.status || '—',
      expectedCheckout: formatExpectedCheckout(expectedCheckoutDate),
      expectedCheckoutDate,
      payment: Number(row.total_outstanding_amount || 0) > 0 ? 'Balance Due' : 'Settled',
      overdueBy: formatOverdueBy(expectedCheckoutDate),
    }
  })
})

// TODO: Replace extensionRequests with backend value when available
const statCards = computed(() => ({
  overdueDepartures: records.value.length,
  balanceDue: records.value.filter((r) => r.payment === 'Balance Due').length,
  extensionRequests: extensionRequests.value,
  awaitingInspection: records.value.filter((r) => r.roomStatus === 'Occupied').length,
}))

// Placeholder for extension requests, to be replaced with backend value
const extensionRequests = ref(0)

// Example: fetch extension requests count from backend if/when available
// onMounted(async () => {
//   const res = await callMethod('rhohotel.rhocom_hotel.api.front_desk.get_extension_requests_count')
//   extensionRequests.value = res?.count || 0
// })
import { callMethod } from '@/lib/api'
function exportOverdue() {
  // Export filtered list as CSV
  const rows = filtered.value
  if (!rows.length) return alert('No overdue records to export.')
  const header = ['Folio', 'Guest', 'Room', 'Expected Check-out', 'Payment', 'Overdue By']
  const csv = [header.join(',')]
  for (const r of rows) {
    csv.push([
      r.folio,
      r.guest,
      r.room,
      r.expectedCheckout,
      r.payment,
      r.overdueBy
    ].map(x => '"' + String(x).replace(/"/g, '""') + '"').join(','))
  }
  const blob = new Blob([csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'overdue-checkouts.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function startCheckout() {
  // Start check-out for the first overdue folio with no balance due
  const first = filtered.value.find(r => r.payment !== 'Balance Due')
  if (!first) return alert('No eligible overdue folio to check out.')
  try {
    await callMethod('rhohotel.rhocom_hotel.api.front_desk.make_check_out', { checkin_name: first.folio })
    alert('Check-out started for folio ' + first.folio)
    refreshData()
  } catch (e) {
    alert('Check-out failed: ' + (e?.message || e))
  }
}

const filtered = computed(() => {
  let list = records.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      String(r.guest || '').toLowerCase().includes(q) ||
      String(r.folio || '').toLowerCase().includes(q) ||
      String(r.room || '').toLowerCase().includes(q)
    )
  }
  if (overdueOnly.value) list = list.filter((r) => r.overdueBy !== '—')
  if (filterPayment.value) list = list.filter(r => r.payment === filterPayment.value)
  if (filterRoom.value) list = list.filter((r) => r.roomStatus === filterRoom.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function formatExpectedCheckout(date) {
  if (!date || Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

function formatOverdueBy(date) {
  if (!date || Number.isNaN(date.getTime())) return '—'
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000))
  if (minutes < 60) return `${minutes} min`
  const hours = (minutes / 60).toFixed(1)
  return `${hours} hrs`
}

watch([search, overdueOnly, filterPayment, filterRoom], () => {
  currentPage.value = 1
})

function refreshData() {
  roomViewResource.reload()
}
</script>