<template>
  <div class="space-y-5">
    <div>
      <div class="flex justify-between items-center gap-3 flex-wrap">
        <h1 class="text-2xl font-bold text-gray-900">Kitchen Order Report</h1>
        <button
          @click="downloadCsv"
          class="bg-green-600 text-white px-4 py-2 rounded-lg"
        >
          Download
        </button>
      </div>
      <p class="text-xs text-gray-400 mt-1">
        Track kitchen ticket volume, preparation stage, source mix, and completion performance.
      </p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input
            v-model="filters.date_from"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input
            v-model="filters.date_to"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select
            v-model="filters.status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Status</option>
            <option v-for="status in statusOptions" :key="status" :value="status">
              {{ status }}
            </option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Source</p>
          <select
            v-model="filters.source"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Sources</option>
            <option v-for="source in sourceOptions" :key="source" :value="source">
              {{ source }}
            </option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Station</p>
          <select
            v-model="filters.station"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Stations</option>
            <option v-for="station in stationOptions" :key="station" :value="station">
              {{ station }}
            </option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">POS Profile</p>
          <select
            v-model="filters.pos_profile"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All POS Profiles</option>
            <option v-for="profile in posProfiles" :key="profile" :value="profile">
              {{ profile }}
            </option>
          </select>
        </div>

        <div class="flex-1 min-w-[240px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Search ticket, table/room, invoice, notes..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>

        <button
          @click="fetchReport"
          :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Apply' }}
        </button>
      </div>

      <p v-if="errorMessage" class="text-xs text-red-600 mt-3">{{ errorMessage }}</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-slate-500">
        <p class="text-xs text-gray-400 mb-1">Total Tickets</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.total_tickets }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Pending</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.pending_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-yellow-500">
        <p class="text-xs text-gray-400 mb-1">In Progress</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.in_progress_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Ready</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.ready_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Delayed</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.delayed_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-emerald-600">
        <p class="text-xs text-gray-400 mb-1">Served</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.served_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Avg Stage (min)</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.avg_stage_minutes) }}</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Kitchen Tickets</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Showing {{ rows.length }} records. Total items: {{ summary.total_items }}
          </p>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1200px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Ticket</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Sent At</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Source</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Station</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">POS Profile</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Table/Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Invoice</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Lines</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Qty</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Age (min)</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Stage (min)</th>
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Status</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="row in rows"
              :key="row.ticket_name"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ row.ticket_name }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ formatDateTime(row.sent_at) }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.source || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.chef_station || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.pos_profile || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.table_or_room || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.pos_invoice || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ row.item_count || 0 }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ formatNumber(row.total_qty || 0) }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ formatNumber(row.age_minutes || 0) }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ formatNumber(row.stage_age_minutes || 0) }}</td>
              <td class="px-5 py-3.5 text-xs">
                <span class="px-2 py-1 rounded-full font-semibold" :class="statusClass(row.status)">
                  {{ row.status }}
                </span>
              </td>
            </tr>

            <tr v-if="!rows.length">
              <td colspan="12" class="px-5 py-10 text-center text-xs text-gray-400">
                No kitchen tickets found for the selected filters.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { callMethod, callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')
const rows = ref([])
const posProfiles = ref([])

const statusOptions = ['Pending', 'In Progress', 'Ready', 'Delayed', 'Served']
const sourceOptions = ['Restaurant Dining', 'Room Service', 'Takeaway', 'Bar Snack']
const stationOptions = ['Hot Kitchen', 'Cold Kitchen', 'Bar', 'Bakery']

const today = new Date()
const from = new Date()
from.setDate(today.getDate() - 7)

const filters = ref({
  date_from: toInputDate(from),
  date_to: toInputDate(today),
  status: '',
  source: '',
  station: '',
  pos_profile: '',
  search: '',
})

const summary = computed(() => {
  return reportData.value.summary || {
    total_tickets: 0,
    pending_count: 0,
    in_progress_count: 0,
    ready_count: 0,
    delayed_count: 0,
    served_count: 0,
    total_items: 0,
    avg_stage_minutes: 0,
  }
})

const reportData = ref({ summary: {}, rows: [] })

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await callMethodForm('rhohotel.restaurant.api.kitchen.get_kitchen_order_report', {
      date_from: filters.value.date_from,
      date_to: filters.value.date_to,
      status: filters.value.status,
      source: filters.value.source,
      station: filters.value.station,
      pos_profile: filters.value.pos_profile,
      search: filters.value.search,
    })

    reportData.value = data || { summary: {}, rows: [] }
    rows.value = reportData.value.rows || []
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to load kitchen order report.'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    date_from: toInputDate(from),
    date_to: toInputDate(today),
    status: '',
    source: '',
    station: '',
    pos_profile: '',
    search: '',
  }
  fetchReport()
}

function statusClass(status) {
  if (status === 'Pending') return 'bg-blue-100 text-blue-700'
  if (status === 'In Progress') return 'bg-yellow-100 text-yellow-700'
  if (status === 'Ready') return 'bg-green-100 text-green-700'
  if (status === 'Delayed') return 'bg-red-100 text-red-700'
  if (status === 'Served') return 'bg-emerald-100 text-emerald-700'
  return 'bg-gray-100 text-gray-700'
}

function formatDateTime(value) {
  if (!value) return '—'
  const d = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString()
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function toInputDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

async function loadProfiles() {
  try {
    const profiles = await callMethod('rhohotel.restaurant.api.kitchen.get_kitchen_pos_profiles')
    posProfiles.value = profiles || []
  } catch (_) {
    posProfiles.value = []
  }
}

function downloadCsv() {
  if (!rows.value.length) return

  const headers = [
    'Ticket', 'Sent At', 'Source', 'Station', 'POS Profile', 'Table/Room', 'Invoice',
    'Item Lines', 'Total Qty', 'Age Minutes', 'Stage Minutes', 'Status', 'Notes',
  ]

  const csvRows = rows.value.map((row) => [
    row.ticket_name,
    formatDateTime(row.sent_at),
    row.source || '',
    row.chef_station || '',
    row.pos_profile || '',
    row.table_or_room || '',
    row.pos_invoice || '',
    row.item_count || 0,
    row.total_qty || 0,
    row.age_minutes || 0,
    row.stage_age_minutes || 0,
    row.status || '',
    row.notes || '',
  ])

  const content = [headers, ...csvRows]
    .map((line) => line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n')

  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `kitchen-order-report-${toInputDate(new Date())}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await loadProfiles()
  await fetchReport()
})
</script>
