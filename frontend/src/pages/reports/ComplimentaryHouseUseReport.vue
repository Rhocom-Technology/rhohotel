<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Complimentary & House Use Report</h1>
        <p class="text-xs text-gray-400 mt-1">Internal stays, complimentary stays, authorisation, occupancy, and theoretical room revenue.</p>
      </div>
      <button
        @click="downloadCsv"
        class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700"
      >
        Export CSV
      </button>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input v-model="filters.date_from" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input v-model="filters.date_to" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Type</p>
          <select v-model="filters.reservation_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Types</option>
            <option>House Use</option>
            <option>Complimentary</option>
          </select>
        </div>
        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="filters.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option>Confirmed</option>
            <option>Checked In</option>
            <option>Checked Out</option>
            <option>Cancelled</option>
            <option>No Show</option>
          </select>
        </div>
        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input v-model="filters.search" type="text" placeholder="Reservation, guest, reason, cost centre..." class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <button @click="resetFilters" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Reset</button>
        <button @click="fetchReport" :disabled="loading" class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
      <p v-if="errorMessage" class="text-xs text-red-600 mt-3">{{ errorMessage }}</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Reservations</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.reservation_count) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">House Use</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.house_use_count) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Complimentary</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.complimentary_count) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Room Nights</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.room_nights) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Theoretical Revenue</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatMoney(summary.theoretical_room_revenue) }}</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Reservation Details</h3>
        <p class="text-xs text-gray-400">Showing {{ rows.length }} records</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1180px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Reservation</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest / Occupants</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Stay</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Rooms</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Reason / Cost Centre</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Theoretical Revenue</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
              <td class="px-5 py-3.5">
                <p class="text-xs font-bold text-gray-900">{{ row.reservation_number || row.name }}</p>
                <p class="text-[10px] text-gray-400">{{ row.reservation_type }} · {{ row.reservation_status }}</p>
              </td>
              <td class="px-4 py-3.5">
                <p class="text-xs font-semibold text-gray-900">{{ row.primary_guest_name || '—' }}</p>
                <p class="text-[10px] text-gray-400">{{ row.occupants || row.primary_guest_phone || '—' }}</p>
              </td>
              <td class="px-4 py-3.5 text-xs text-gray-600">
                <p>{{ formatDate(row.from_date) }} → {{ formatDate(row.to_date) }}</p>
                <p class="text-[10px] text-gray-400">{{ row.number_of_nights || 0 }} night(s)</p>
              </td>
              <td class="px-4 py-3.5 text-xs text-gray-600">
                <p>{{ row.room_numbers || '—' }}</p>
                <p class="text-[10px] text-gray-400">{{ row.room_count || 0 }} room(s)</p>
              </td>
              <td class="px-4 py-3.5 text-xs text-gray-600">
                <p>{{ row.comp_reason || '—' }}</p>
                <p class="text-[10px] text-gray-400">{{ row.internal_cost_center || 'No cost centre' }}</p>
              </td>
              <td class="px-5 py-3.5 text-xs text-right font-bold text-gray-900">
                ₦{{ formatMoney(row.theoretical_room_revenue) }}
              </td>
            </tr>
            <tr v-if="!rows.length">
              <td colspan="6" class="px-5 py-10 text-center text-xs text-gray-400">No House Use or Complimentary reservations found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const todayDate = new Date()
const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 30)

const today = todayDate.toISOString().slice(0, 10)
const monthAgo = fromDate.toISOString().slice(0, 10)

const filters = ref({
  date_from: monthAgo,
  date_to: today,
  reservation_type: '',
  status: '',
  search: '',
})

const rows = ref([])
const summary = ref({
  reservation_count: 0,
  house_use_count: 0,
  complimentary_count: 0,
  room_nights: 0,
  theoretical_room_revenue: 0,
})
const loading = ref(false)
const errorMessage = ref('')
let filterTimer = null

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.special_reservation_report.get_special_reservation_report',
      {
        date_from: filters.value.date_from || '',
        date_to: filters.value.date_to || '',
        reservation_type: filters.value.reservation_type || '',
        status: filters.value.status || '',
        search: filters.value.search || '',
      },
    )
    rows.value = result?.rows || []
    summary.value = result?.summary || summary.value
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading the report.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(filters, () => {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(fetchReport, 350)
}, { deep: true })

function resetFilters() {
  filters.value = {
    date_from: monthAgo,
    date_to: today,
    reservation_type: '',
    status: '',
    search: '',
  }
  fetchReport()
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-NG', { maximumFractionDigits: 0 })
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function csvEscape(value) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`
}

function downloadCsv() {
  const header = ['Reservation', 'Type', 'Status', 'Guest', 'From', 'To', 'Rooms', 'Reason', 'Cost Centre', 'Theoretical Revenue']
  const body = rows.value.map((row) => [
    row.reservation_number || row.name,
    row.reservation_type,
    row.reservation_status,
    row.primary_guest_name,
    row.from_date,
    row.to_date,
    row.room_numbers,
    row.comp_reason,
    row.internal_cost_center,
    row.theoretical_room_revenue,
  ])
  const csv = [header, ...body].map((line) => line.map(csvEscape).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `complimentary-house-use-report-${today}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(fetchReport)
</script>
