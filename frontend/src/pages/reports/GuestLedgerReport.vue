<template>
  <div class="space-y-5">
    <div>
      <div class="flex justify-between items-center gap-3 flex-wrap">
        <h1 class="text-2xl font-bold text-gray-900">Guest Ledger Report</h1>
        <div class="flex items-center gap-3">

          <button
            @click="downloadCsv"
            class="bg-green-600 text-white px-4 py-2 rounded-lg"
          >
            Download CSV
          </button>
            <button
             @click="downloadPdf"
              class="bg-green-600 text-white px-4 py-2 rounded-lg"
            >
              Download PDF
            </button>

<!--     
            <button @click="downloadPdf"
            class="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-green-600">
            Download  PDF
          </button> -->
        </div>

      </div>
      <p class="text-xs text-gray-400 mt-1">
        Guest folio transaction ledger in debit/credit format with running balance.
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

        <div style="min-width:220px;">
          <p class="text-xs text-gray-500 mb-1.5">Guest</p>
          <div class="relative">
            <button
              type="button"
              @click="guestDropdownOpen = !guestDropdownOpen"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg text-left text-gray-600 bg-white"
            >
              {{ selectedGuestLabel }}
            </button>

            <div
              v-if="guestDropdownOpen"
              class="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-2"
            >
              <input
                v-model="guestSearch"
                type="text"
                placeholder="Search guest..."
                class="w-full px-2.5 py-2 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              <button
                type="button"
                @click="selectGuest('')"
                class="w-full mt-2 px-2.5 py-2 text-left text-xs rounded-md hover:bg-gray-50 text-gray-700"
              >
                All Guests
              </button>

              <div class="max-h-48 overflow-auto mt-1">
                <button
                  v-for="guest in filteredGuestOptions"
                  :key="guest.guest"
                  type="button"
                  @click="selectGuest(guest.guest)"
                  class="w-full px-2.5 py-2 text-left text-xs rounded-md hover:bg-gray-50 text-gray-700"
                >
                  {{ guest.guest_name }}
                </button>
                <p v-if="!filteredGuestOptions.length" class="px-2.5 py-2 text-xs text-gray-400">
                  No guest found.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Check-in Status</p>
          <select
            v-model="filters.checkin_status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All</option>
            <option v-for="status in checkinStatusOptions" :key="status" :value="status">
              {{ status }}
            </option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select
            v-model="filters.room_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Room Types</option>
            <option v-for="type in roomTypeOptions" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Transaction Type</p>
          <select
            v-model="filters.transaction_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Transactions</option>
            <option v-for="type in transactionTypeOptions" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <div class="flex-1 min-w-[240px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Search check-in, guest, phone, room..."
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

    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-gray-500">
        <p class="text-xs text-gray-400 mb-1">Opening Balance</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatCurrency(summary.opening_balance) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Debit</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatCurrency(summary.total_debit) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Total Credit</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatCurrency(summary.total_credit) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Closing Balance</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatCurrency(summary.closing_balance) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Transactions</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.transaction_count }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Guests</p>
        <p class="text-3xl font-bold text-gray-900">{{ summary.guest_count }}</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Guest Ledger Transactions</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            ERPNext-style debit/credit ledger with running balance.
          </p>
        </div>
        <div class="flex items-center gap-3">
          <div class="inline-flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              type="button"
              @click="viewMode = 'simple'"
              class="px-3 py-1.5 text-xs font-medium"
              :class="viewMode === 'simple' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
            >
              Simple View
            </button>
            <button
              type="button"
              @click="viewMode = 'group'"
              class="px-3 py-1.5 text-xs font-medium"
              :class="viewMode === 'group' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
            >
              Group View
            </button>
          </div>

          <p class="text-xs text-gray-400">
            {{ viewMode === 'group' ? groupedRows.length : rows.length }}
            {{ viewMode === 'group' ? 'groups' : 'records' }}
          </p>
        </div>
      </div>

      <div v-if="viewMode === 'simple'" class="overflow-x-auto">
        <table class="w-full" style="min-width:1300px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Date</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Check-in</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Voucher</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[220px]">Remarks</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Debit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Credit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Running Balance</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="row in rows"
              :key="`${row.voucher_no}-${row.check_in}-${row.date}`"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs text-gray-700">{{ row.date || '—' }}</td>
              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ row.guest_name }}</td>
              <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ row.check_in }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.room_number || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.transaction_type || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ row.voucher_no || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.remarks || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-blue-700">₦{{ formatCurrency(row.debit) }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-green-700">₦{{ formatCurrency(row.credit) }}</td>
              <td
                class="px-5 py-3.5 text-xs text-right font-bold"
                :class="Number(row.running_balance || 0) > 0 ? 'text-red-700' : 'text-green-700'"
              >
                ₦{{ formatCurrency(row.running_balance) }}
              </td>
            </tr>

            <tr v-if="!rows.length">
              <td colspan="10" class="px-5 py-10 text-center text-xs text-gray-400">
                No guest ledger records found for selected filters.
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="7" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-blue-700">₦{{ formatCurrency(summary.total_debit) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-green-700">₦{{ formatCurrency(summary.total_credit) }}</td>
              <td class="px-5 py-4 text-xs text-right font-bold" :class="Number(summary.closing_balance || 0) > 0 ? 'text-red-700' : 'text-green-700'">
                ₦{{ formatCurrency(summary.closing_balance) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div v-else class="p-4 space-y-4">
        <div
          v-for="group in groupedRows"
          :key="group.guest"
          class="border border-gray-200 rounded-xl overflow-hidden"
        >
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-900">{{ group.guest_name }}</p>
              <p class="text-[11px] text-gray-500 mt-0.5">
                {{ group.transactions }} transactions • {{ group.checkins }} check-ins
              </p>
            </div>
            <div class="text-right">
              <p class="text-[11px] text-gray-500">Closing Balance</p>
              <p class="text-xs font-bold" :class="Number(group.closing_balance || 0) > 0 ? 'text-red-700' : 'text-green-700'">
                ₦{{ formatCurrency(group.closing_balance) }}
              </p>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full" style="min-width:1180px;">
              <thead>
                <tr class="border-b border-gray-100 bg-white">
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Date</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Check-in</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Room</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Type</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Voucher</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Remarks</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Debit</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Credit</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Running Balance</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="row in group.rows"
                  :key="`${row.voucher_no}-${row.check_in}-${row.date}`"
                  class="border-b border-gray-50 last:border-0"
                >
                  <td class="px-4 py-3 text-xs text-gray-700">{{ row.date || '—' }}</td>
                  <td class="px-4 py-3 text-xs font-semibold text-gray-900">{{ row.check_in }}</td>
                  <td class="px-4 py-3 text-xs text-gray-700">{{ row.room_number || '—' }}</td>
                  <td class="px-4 py-3 text-xs text-gray-700">{{ row.transaction_type || '—' }}</td>
                  <td class="px-4 py-3 text-xs text-gray-700">{{ row.voucher_no || '—' }}</td>
                  <td class="px-4 py-3 text-xs text-gray-600">{{ row.remarks || '—' }}</td>
                  <td class="px-4 py-3 text-xs text-right text-blue-700">₦{{ formatCurrency(row.debit) }}</td>
                  <td class="px-4 py-3 text-xs text-right text-green-700">₦{{ formatCurrency(row.credit) }}</td>
                  <td class="px-4 py-3 text-xs text-right font-bold" :class="Number(row.group_running_balance || 0) > 0 ? 'text-red-700' : 'text-green-700'">
                    ₦{{ formatCurrency(row.group_running_balance) }}
                  </td>
                </tr>
              </tbody>

              <tfoot>
                <tr class="border-t border-gray-200 bg-gray-50">
                  <td colspan="6" class="px-4 py-3 text-xs font-bold text-right text-gray-900">Subtotal</td>
                  <td class="px-4 py-3 text-xs font-bold text-right text-blue-700">₦{{ formatCurrency(group.total_debit) }}</td>
                  <td class="px-4 py-3 text-xs font-bold text-right text-green-700">₦{{ formatCurrency(group.total_credit) }}</td>
                  <td class="px-4 py-3 text-xs font-bold text-right" :class="Number(group.closing_balance || 0) > 0 ? 'text-red-700' : 'text-green-700'">
                    ₦{{ formatCurrency(group.closing_balance) }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div v-if="!groupedRows.length" class="px-5 py-10 text-center text-xs text-gray-400">
          No guest ledger records found for selected filters.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')
const reportData = ref({ summary: {}, rows: [], room_types: [], checkin_statuses: [], guest_options: [], transaction_types: [] })
const viewMode = ref('simple')
const guestDropdownOpen = ref(false)
const guestSearch = ref('')

const today = new Date()
const from = new Date()
from.setDate(today.getDate() - 30)

const defaultFilters = () => ({
  date_from: toInputDate(from),
  date_to: toInputDate(today),
  guest: '',
  checkin_status: '',
  room_type: '',
  transaction_type: '',
  search: '',
})

const filters = ref(defaultFilters())

const roomTypeOptions = computed(() => reportData.value.room_types || [])
const checkinStatusOptions = computed(() => reportData.value.checkin_statuses || [])
const guestOptions = computed(() => reportData.value.guest_options || [])
const transactionTypeOptions = computed(() => reportData.value.transaction_types || [])
const rows = computed(() => reportData.value.rows || [])

const selectedGuestLabel = computed(() => {
  if (!filters.value.guest) return 'All Guests'
  const found = guestOptions.value.find((g) => g.guest === filters.value.guest)
  return found?.guest_name || filters.value.guest
})

const filteredGuestOptions = computed(() => {
  const q = String(guestSearch.value || '').toLowerCase().trim()
  if (!q) return guestOptions.value
  return guestOptions.value.filter((g) =>
    String(g.guest_name || '').toLowerCase().includes(q) ||
    String(g.guest || '').toLowerCase().includes(q)
  )
})

const groupedRows = computed(() => {
  const groups = new Map()

  for (const row of rows.value) {
    const key = row.guest || row.guest_name || 'Unknown'
    if (!groups.has(key)) {
      groups.set(key, {
        guest: key,
        guest_name: row.guest_name || 'Unknown Guest',
        rows: [],
        total_debit: 0,
        total_credit: 0,
        closing_balance: 0,
        transactions: 0,
        checkinSet: new Set(),
        running: 0,
      })
    }

    const group = groups.get(key)
    group.running += Number(row.debit || 0) - Number(row.credit || 0)
    group.rows.push({ ...row, group_running_balance: group.running })
    group.total_debit += Number(row.debit || 0)
    group.total_credit += Number(row.credit || 0)
    group.transactions += 1
    if (row.check_in) group.checkinSet.add(row.check_in)
    group.closing_balance = group.running
  }

  return Array.from(groups.values())
    .map((g) => ({
      ...g,
      checkins: g.checkinSet.size,
      checkinSet: undefined,
      running: undefined,
    }))
    .sort((a, b) => String(a.guest_name || '').localeCompare(String(b.guest_name || '')))
})

const summary = computed(() => reportData.value.summary || {
  opening_balance: 0,
  total_debit: 0,
  total_credit: 0,
  closing_balance: 0,
  transaction_count: 0,
  guest_count: 0,
})

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  try {
    const data = await callMethodForm('rhohotel.rhocom_hotel.api.guest_ledger_report.get_guest_ledger_report', {
      date_from: filters.value.date_from,
      date_to: filters.value.date_to,
      guest: filters.value.guest,
      checkin_status: filters.value.checkin_status,
      room_type: filters.value.room_type,
      transaction_type: filters.value.transaction_type,
      search: filters.value.search,
    })

    reportData.value = data || { summary: {}, rows: [], room_types: [], checkin_statuses: [], guest_options: [], transaction_types: [] }
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to load guest ledger report.'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = defaultFilters()
  guestSearch.value = ''
  guestDropdownOpen.value = false
  fetchReport()
}

function selectGuest(guestId) {
  filters.value.guest = guestId || ''
  guestDropdownOpen.value = false
}

function toInputDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function downloadCsv() {
  if (!rows.value.length) return

  const headers = [
    'Date', 'Guest', 'Check In', 'Room', 'Type', 'Voucher', 'Remarks', 'Debit', 'Credit', 'Running Balance',
  ]

  const csvRows = rows.value.map((row) => [
    row.date || '',
    row.guest_name,
    row.check_in,
    row.room_number || '',
    row.transaction_type || '',
    row.voucher_no || '',
    row.remarks || '',
    row.debit || 0,
    row.credit || 0,
    row.running_balance || 0,
  ])

  const content = [headers, ...csvRows]
    .map((line) => line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n')

  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `guest-ledger-report-${toInputDate(new Date())}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function downloadPdf() {
  const params = new URLSearchParams({
    date_from: filters.value.date_from || '',
    date_to: filters.value.date_to || '',
    guest: filters.value.guest || '',
    checkin_status: filters.value.checkin_status || '',
    room_type: filters.value.room_type || '',
    transaction_type: filters.value.transaction_type || '',
  })
  await printPdf(`/api/method/rhohotel.rhocom_hotel.api.reports.download_guest_ledger_report?${params.toString()}`)
}


onMounted(() => {
  fetchReport()
})

async function printPdf(url) {
  try {
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error('Failed to fetch PDF')
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;top:0;left:0;width:0;height:0;border:0;visibility:hidden;'
    iframe.src = objectUrl
    document.body.appendChild(iframe)
    iframe.onload = () => {
      setTimeout(() => {
        iframe.contentWindow.focus()
        iframe.contentWindow.print()
        setTimeout(() => {
          document.body.removeChild(iframe)
          URL.revokeObjectURL(objectUrl)
        }, 1000)
      }, 300)
    }
  } catch (err) {
    console.error('Print error:', err)
  }
}
</script>
