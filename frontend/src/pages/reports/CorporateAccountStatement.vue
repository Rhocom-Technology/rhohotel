<template>
  <div class="space-y-5">
    <div>

      <div class="flex justify-between items-center gap-3 flex-wrap">

              <h1 class="text-2xl font-bold text-gray-900">Corporate Account Statement</h1>
            <button
                @click="downloadReport"
                class="bg-green-600 text-white px-4 py-2 rounded-lg">
                Download
              </button>

    </div>

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
          <p class="text-xs text-gray-500 mb-1.5">Corporate Customer</p>
          <select
            v-model="filters.customer"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Corporate Customers</option>
            <option
              v-for="customer in customers"
              :key="customer.name"
              :value="customer.name"
            >
              {{ customer.customer_name || customer.name }}
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
            <option value="Sales Invoice">Sales Invoice</option>
            <option value="Payment Entry">Payment Entry</option>
          </select>
        </div>

        <div class="flex-1 min-w-[240px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search customer, invoice, payment, reference..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Reset
        </button>

        <button
          @click="fetchReport"
          :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>

      <p v-if="errorMessage" class="text-xs text-red-600 mt-3">
        {{ errorMessage }}
      </p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-gray-500">
        <p class="text-xs text-gray-400 mb-1">Opening Balance</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.opening_balance) }}</p>
        <p class="text-[10px] text-gray-500 mt-1">before period</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Debit</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_debit) }}</p>
        <p class="text-[10px] text-blue-600 mt-1">invoices / charges</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Total Credit</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_credit) }}</p>
        <p class="text-[10px] text-green-600 mt-1">payments received</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Closing Balance</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.closing_balance) }}</p>
        <p class="text-[10px] text-red-600 mt-1">current balance</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Transactions</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.transaction_count) }}</p>
        <p class="text-[10px] text-purple-600 mt-1">ledger entries</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Corporate Customers</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.customer_count) }}</p>
        <p class="text-[10px] text-indigo-600 mt-1">accounts</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Corporate Account Summary</h3>
        <p class="text-xs text-gray-400">Customer-level debit, credit and balance overview</p>
      </div>

      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Customer</th>
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Transactions</th>
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Debit</th>
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Credit</th>
            <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Balance</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="account in accountSummary"
            :key="account.customer"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50"
          >
            <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">
              {{ account.customer_name || account.customer }}
            </td>
            <td class="px-4 py-3.5 text-xs text-right text-gray-700">
              {{ account.transactions }}
            </td>
            <td class="px-4 py-3.5 text-xs text-right text-blue-600">
              ₦{{ formatNumber(account.total_debit) }}
            </td>
            <td class="px-4 py-3.5 text-xs text-right text-green-600">
              ₦{{ formatNumber(account.total_credit) }}
            </td>
            <td
              class="px-5 py-3.5 text-xs text-right font-bold"
              :class="Number(account.balance || 0) > 0 ? 'text-red-600' : 'text-green-600'"
            >
              ₦{{ formatNumber(account.balance) }}
            </td>
          </tr>

          <tr v-if="!accountSummary.length">
            <td colspan="5" class="px-5 py-8 text-center text-xs text-gray-400">
             No corporate customer summary found.
            </td>
          </tr>
        </tbody>
      </table>

      <div class="px-6 py-3 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">
        Showing {{ accountSummary.length }} of {{ accountTotal }} corporate customer accounts
        </p>

        <div class="flex items-center gap-1">
          <button
            @click="goAccountPage(1)"
            :disabled="accountPage === 1"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            «
          </button>

          <button
            @click="goAccountPage(accountPage - 1)"
            :disabled="accountPage === 1"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            ‹
          </button>

          <span class="px-3 text-xs text-gray-500">
            Page {{ accountPage }} of {{ accountTotalPages }}
          </span>

          <button
            @click="goAccountPage(accountPage + 1)"
            :disabled="accountPage === accountTotalPages"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            ›
          </button>

          <button
            @click="goAccountPage(accountTotalPages)"
            :disabled="accountPage === accountTotalPages"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            »
          </button>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Detailed Corporate Account Ledger</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Chronological statement of debits, credits and running balances.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedRows.length }} of {{ filteredRows.length }} records
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1250px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[180px]">Customer</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[130px]">Type</th>
              <th
                class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer"
                @click="sortBy('reference')"
              >
                Reference
                <span v-if="sortKey === 'reference'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[220px]">Description</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Debit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Credit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Running Balance</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(row, index) in paginatedRows"
              :key="row.reference + '-' + index"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50"
            >
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * Number(pageSize) + index + 1 }}
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">
                {{ row.date }}
              </td>

              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">
                {{ row.party_name || row.party }}
              </td>

              <td class="px-4 py-3.5">
                <span
                  class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full"
                  :class="transactionClass(row.transaction_type)"
                >
                  {{ row.transaction_type }}
                </span>
              </td>

              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="min-w-[160px]">
                  <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                    {{ row.reference }}
                  </span>
                </div>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-600">
                {{ row.description || '—' }}
              </td>

              <td class="px-4 py-3.5 text-xs text-right text-blue-600 whitespace-nowrap">
                ₦{{ formatNumber(row.debit) }}
              </td>

              <td class="px-4 py-3.5 text-xs text-right text-green-600 whitespace-nowrap">
                ₦{{ formatNumber(row.credit) }}
              </td>

              <td
                class="px-5 py-3.5 text-xs text-right font-bold whitespace-nowrap"
                :class="Number(row.running_balance || 0) > 0 ? 'text-red-600' : 'text-green-600'"
              >
                ₦{{ formatNumber(row.running_balance) }}
              </td>
            </tr>

            <tr v-if="!paginatedRows.length">
              <td colspan="9" class="px-5 py-10 text-center text-xs text-gray-400">
                No corporate account transaction found for the selected filters.
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="6" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">
                Total
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-blue-600">
                ₦{{ formatNumber(totals.debit) }}
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-green-600">
                ₦{{ formatNumber(totals.credit) }}
              </td>
              <td class="px-5 py-4 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(summary.closing_balance) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">
          Page {{ currentPage }} of {{ totalPages }}
        </p>

        <div class="flex items-center gap-1">
          <button
            @click="currentPage = 1"
            :disabled="currentPage === 1"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            «
          </button>

          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            ‹
          </button>

          <button
            v-for="page in visiblePages"
            :key="page"
            @click="page !== '...' && (currentPage = page)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg"
            :class="page === currentPage
              ? 'bg-blue-600 text-white font-semibold'
              : page === '...'
                ? 'text-gray-400 cursor-default'
                : 'text-gray-600 hover:bg-gray-50 border border-gray-200'"
          >
            {{ page }}
          </button>

          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            ›
          </button>

          <button
            @click="currentPage = totalPages"
            :disabled="currentPage === totalPages"
            class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40"
          >
            »
          </button>

          <select
            v-model="pageSize"
            @change="currentPage = 1"
            class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        Corporate account note: Debit increases receivable balance, credit reduces customer balance.
      </p>
      <p class="text-xs text-gray-400">Execution Time: {{ executionTime }} sec</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')
const executionTime = ref('0.0')

const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)

const todayDate = new Date()
const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 30)

const today = todayDate.toISOString().slice(0, 10)
const monthAgo = fromDate.toISOString().slice(0, 10)

const filters = ref({
  date_from: monthAgo,
  date_to: today,
  customer: '',
  transaction_type: '',
})

const rows = ref([])
const customers = ref([])

const summary = ref({
  opening_balance: 0,
  total_debit: 0,
  total_credit: 0,
  closing_balance: 0,
  transaction_count: 0,
  customer_count: 0,
})

const accountSummary = ref([])
const accountPage = ref(1)
const accountPageSize = ref(10)
const accountTotal = ref(0)
const accountTotalPages = ref(1)

let searchTimer = null
let filterTimer = null

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  const start = performance.now()

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_account_statement.get_corporate_account_statement',
      {
        date_from: filters.value.date_from || '',
        date_to: filters.value.date_to || '',
        customer: filters.value.customer || '',
        transaction_type: filters.value.transaction_type || '',
        search: searchQuery.value || '',
        account_page: accountPage.value,
        account_page_size: accountPageSize.value,
      }
    )

    rows.value = result?.rows || []
    customers.value = result?.customers || []

    summary.value = result?.summary || {
      opening_balance: 0,
      total_debit: 0,
      total_credit: 0,
      closing_balance: 0,
      transaction_count: 0,
      customer_count: 0,
    }

    accountSummary.value = result?.account_summary || []
    accountTotal.value = result?.account_summary_total || 0
    accountPage.value = result?.account_summary_page || 1
    accountTotalPages.value = result?.account_summary_total_pages || 1

    executionTime.value = ((performance.now() - start) / 1000).toFixed(1)
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading corporate account statement.'
    rows.value = []
    customers.value = []
    accountSummary.value = []
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  let data = rows.value || []

  if (sortKey.value) {
    data = [...data].sort((a, b) => {
      const av = a[sortKey.value] ?? ''
      const bv = b[sortKey.value] ?? ''

      const aNum = Number(av)
      const bNum = Number(bv)

      if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
        return sortDir.value === 'asc' ? aNum - bNum : bNum - aNum
      }

      return sortDir.value === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
  }

  return data
})

const totals = computed(() => ({
  debit: filteredRows.value.reduce((sum, row) => sum + Number(row.debit || 0), 0),
  credit: filteredRows.value.reduce((sum, row) => sum + Number(row.credit || 0), 0),
}))

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRows.value.length / Number(pageSize.value)))
})

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * Number(pageSize.value)
  return filteredRows.value.slice(start, start + Number(pageSize.value))
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(
  () => ({
    date_from: filters.value.date_from,
    date_to: filters.value.date_to,
    customer: filters.value.customer,
    transaction_type: filters.value.transaction_type,
  }),
  () => {
    clearTimeout(filterTimer)

    filterTimer = setTimeout(() => {
      currentPage.value = 1
      accountPage.value = 1
      fetchReport()
    }, 250)
  },
  { deep: true }
)

watch(searchQuery, () => {
  clearTimeout(searchTimer)

  searchTimer = setTimeout(() => {
    currentPage.value = 1
    accountPage.value = 1
    fetchReport()
  }, 450)
})

function goAccountPage(page) {
  if (page < 1 || page > accountTotalPages.value) return

  accountPage.value = page
  fetchReport()
}

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function resetFilters() {
  filters.value = {
    date_from: monthAgo,
    date_to: today,
    customer: '',
    transaction_type: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
  accountPage.value = 1

  fetchReport()
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-NG', {
    maximumFractionDigits: 0,
  })
}

function transactionClass(type) {
  return {
    'Sales Invoice': 'bg-blue-100 text-blue-700',
    'Payment Entry': 'bg-green-100 text-green-700',
  }[type] || 'bg-gray-100 text-gray-600'
}

onMounted(() => {
  fetchReport()
})

function downloadReport() {
  const params = new URLSearchParams({
    date_from: filters.value.date_from || '',
    date_to: filters.value.date_to || '',
    customer: filters.value.customer || '',
    transaction_type: filters.value.transaction_type || '',
    search: searchQuery.value || '',
  })

  window.open(
    `/api/method/rhohotel.rhocom_hotel.api.reports.download_corporate_account_statement_report?${params.toString()}`,
    '_blank'
  )
}
</script>