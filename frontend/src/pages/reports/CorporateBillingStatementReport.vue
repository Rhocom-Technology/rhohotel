<template>
  <div class="space-y-5">
    <div>
     

      <div class="flex justify-between items-center gap-3 flex-wrap">

              <h1 class="text-2xl font-bold text-gray-900">Corporate Billing Statement</h1>
            <button
                @click="downloadReport"
                class="bg-green-600 text-white px-4 py-2 rounded-lg">
                Download
              </button>

    </div>
      <p class="text-xs text-gray-400 mt-1">
        Corporate account balances, invoices, payments, aging, credit limits and outstanding billing overview.
      </p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input v-model="filters.date_from" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>

        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input v-model="filters.date_to" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700" />
        </div>

        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5"> Corporate Customer</p>
          <select v-model="filters.company" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Corporate Customers</option>
            <option v-for="company in companies" :key="company" :value="company">{{ company }}</option>
          </select>
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="filters.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Status</option>
            <option value="Paid">Paid</option>
            <option value="Unpaid">Unpaid</option>
            <option value="Overdue">Overdue</option>
          </select>
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Aging</p>
          <select v-model="filters.aging_bucket" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Aging</option>
            <option value="Current">Current</option>
            <option value="1-30">1 - 30 Days</option>
            <option value="31-60">31 - 60 Days</option>
            <option value="61-90">61 - 90 Days</option>
            <option value="90+">90+ Days</option>
          </select>
        </div>

        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input v-model="searchQuery" type="text" placeholder="Search company, invoice, guest, reference..." class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <button @click="resetFilters" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Reset
        </button>

        <button @click="fetchReport" :disabled="loading" class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>

      <p v-if="errorMessage" class="text-xs text-red-600 mt-3">{{ errorMessage }}</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Billing</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_billing) }}</p>
        <p class="text-[10px] text-blue-600 mt-1">invoice value</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Total Paid</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_paid) }}</p>
        <p class="text-[10px] text-green-600 mt-1">received</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.outstanding) }}</p>
        <p class="text-[10px] text-red-600 mt-1">balance due</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Overdue</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.overdue) }}</p>
        <p class="text-[10px] text-amber-600 mt-1">past due</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Invoices</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.invoice_count) }}</p>
        <p class="text-[10px] text-purple-600 mt-1">records</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
      <p class="text-xs text-gray-400 mb-1">Corporate Customers</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.company_count) }}</p>
        <p class="text-[10px] text-indigo-600 mt-1">accounts</p>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 2fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Aging Breakdown</h3>

        <div class="space-y-4">
          <div v-for="row in agingBreakdown" :key="row.bucket">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-medium text-gray-700">{{ row.bucket }}</span>
              <span class="text-xs font-bold text-gray-900">₦{{ formatNumber(row.amount) }}</span>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" :class="agingColor(row.bucket)" :style="{ width: getPercent(row.amount, maxAgingAmount) + '%' }"></div>
            </div>
          </div>

          <p v-if="!agingBreakdown.length" class="text-xs text-gray-400">No aging data found.</p>
        </div>

        <div class="pt-4 mt-4 border-t border-gray-100 flex items-center justify-between">
          <p class="text-xs text-gray-400">
            Showing {{ agingBreakdown.length }} of {{ agingTotal }} aging records
          </p>

          <div class="flex items-center gap-1">
            <button @click="goAgingPage(1)" :disabled="agingPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">«</button>
            <button @click="goAgingPage(agingPage - 1)" :disabled="agingPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">‹</button>
            <span class="px-3 text-xs text-gray-500">Page {{ agingPage }} of {{ agingTotalPages }}</span>
            <button @click="goAgingPage(agingPage + 1)" :disabled="agingPage === agingTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">›</button>
            <button @click="goAgingPage(agingTotalPages)" :disabled="agingPage === agingTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">»</button>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Corporate Customer Summary</h3>
          <p class="text-xs text-gray-400">Corporate customer billing performance</p>
        </div>

        <div class="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <div class="flex items-end gap-3 flex-wrap">
            <div class="flex-1 min-w-[220px]">
             <p class="text-xs text-gray-500 mb-1.5">Search Corporate Customer</p>
              <input v-model="companySummaryFilters.search" type="text" placeholder="Search corporate customer..." class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div style="min-width:160px;">
              <p class="text-xs text-gray-500 mb-1.5">Account Status</p>
              <select v-model="companySummaryFilters.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">All Accounts</option>
                <option value="Outstanding">Outstanding</option>
                <option value="Paid">Fully Paid</option>
              </select>
            </div>

            <div style="min-width:160px;">
              <p class="text-xs text-gray-500 mb-1.5">Min Outstanding</p>
              <input v-model="companySummaryFilters.min_outstanding" type="number" min="0" placeholder="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <button @click="resetCompanySummaryFilters" class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
              Clear
            </button>
          </div>
        </div>

        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Company</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Invoices</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Billed</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Paid</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Outstanding</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="company in companySummary" :key="company.company" class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
              <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ company.company }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ company.invoices }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">₦{{ formatNumber(company.billed) }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-green-600">₦{{ formatNumber(company.paid) }}</td>
              <td class="px-5 py-3.5 text-xs text-right font-bold text-red-600">₦{{ formatNumber(company.outstanding) }}</td>
            </tr>

            <tr v-if="!companySummary.length">
              <td colspan="5" class="px-5 py-8 text-center text-xs text-gray-400">
                No corporate customer summary found.
              </td>
            </tr>
          </tbody>
        </table>

        <div class="px-6 py-3 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
          <p class="text-xs text-gray-400">
            Showing {{ companySummary.length }} of {{ companyTotal }} companies
          </p>

          <div class="flex items-center gap-1">
            <button @click="goCompanyPage(1)" :disabled="companyPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">«</button>
            <button @click="goCompanyPage(companyPage - 1)" :disabled="companyPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">‹</button>
            <span class="px-3 text-xs text-gray-500">Page {{ companyPage }} of {{ companyTotalPages }}</span>
            <button @click="goCompanyPage(companyPage + 1)" :disabled="companyPage === companyTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">›</button>
            <button @click="goCompanyPage(companyTotalPages)" :disabled="companyPage === companyTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">»</button>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Detailed Corporate Billing Statement</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Invoice-level corporate billing, due dates, payments and outstanding balances.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedRows.length }} of {{ filteredRows.length }} records
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1300px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer" @click="sortBy('invoice')">
                Invoice <span v-if="sortKey === 'invoice'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[180px]">Company</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[160px]">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[130px]">Reference</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Due Date</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Billed</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Paid</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Outstanding</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[90px]">Aging</th>
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Status</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(row, index) in paginatedRows" :key="row.invoice || index" class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
              <td class="px-5 py-3.5 text-xs text-gray-400">{{ (currentPage - 1) * Number(pageSize) + index + 1 }}</td>

              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="min-w-[160px]">
                  <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                    {{ row.invoice }}
                  </span>
                </div>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.date }}</td>
              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ row.company }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.guest || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.reference || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ row.due_date || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700 whitespace-nowrap">₦{{ formatNumber(row.billed_amount) }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-green-600 whitespace-nowrap">₦{{ formatNumber(row.paid_amount) }}</td>
              <td class="px-4 py-3.5 text-xs text-right font-bold text-red-600 whitespace-nowrap">₦{{ formatNumber(row.outstanding_amount) }}</td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="agingBadgeClass(row.aging_bucket)">
                  {{ row.aging_bucket || 'Current' }}
                </span>
              </td>

              <td class="px-5 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="statusClass(row.status)">
                  {{ row.status || 'Unpaid' }}
                </span>
              </td>
            </tr>

            <tr v-if="!paginatedRows.length">
              <td colspan="12" class="px-5 py-10 text-center text-xs text-gray-400">
                No corporate billing record found for the selected filters.
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="7" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">₦{{ formatNumber(totals.billed_amount) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-green-600">₦{{ formatNumber(totals.paid_amount) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-red-600">₦{{ formatNumber(totals.outstanding_amount) }}</td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">Page {{ currentPage }} of {{ totalPages }}</p>

        <div class="flex items-center gap-1">
          <button @click="currentPage = 1" :disabled="currentPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">«</button>
          <button @click="currentPage--" :disabled="currentPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">‹</button>

          <button v-for="page in visiblePages" :key="page" @click="page !== '...' && (currentPage = page)" class="w-7 h-7 flex items-center justify-center text-xs rounded-lg" :class="page === currentPage ? 'bg-blue-600 text-white font-semibold' : page === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-gray-50 border border-gray-200'">
            {{ page }}
          </button>

          <button @click="currentPage++" :disabled="currentPage === totalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">›</button>
          <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">»</button>

          <select v-model="pageSize" @change="currentPage = 1" class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        Corporate billing note: Review overdue invoices, credit exposure, aging balances and payment follow-up.
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
  company: '',
  status: '',
  aging_bucket: '',
})

const companySummaryFilters = ref({
  search: '',
  status: '',
  min_outstanding: '',
})

const rows = ref([])
const companies = ref([])
const summary = ref({
  total_billing: 0,
  total_paid: 0,
  outstanding: 0,
  overdue: 0,
  invoice_count: 0,
  company_count: 0,
})

const companySummary = ref([])
const companyPage = ref(1)
const companyPageSize = ref(10)
const companyTotal = ref(0)
const companyTotalPages = ref(1)

const agingBreakdown = ref([])
const agingPage = ref(1)
const agingPageSize = ref(10)
const agingTotal = ref(0)
const agingTotalPages = ref(1)

let searchTimer = null
let filterTimer = null
let companyFilterTimer = null

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  const start = performance.now()

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_billing_statement.get_corporate_billing_statement',
      {
        date_from: filters.value.date_from || '',
        date_to: filters.value.date_to || '',
        company: filters.value.company || '',
        status: filters.value.status || '',
        aging_bucket: filters.value.aging_bucket || '',
        search: searchQuery.value || '',

        company_page: companyPage.value,
        company_page_size: companyPageSize.value,
        aging_page: agingPage.value,
        aging_page_size: agingPageSize.value,

        company_summary_search: companySummaryFilters.value.search || '',
        company_summary_status: companySummaryFilters.value.status || '',
        company_summary_min_outstanding: companySummaryFilters.value.min_outstanding || '',
      }
    )

    rows.value = result?.rows || result?.data || []
    companies.value = result?.companies || []

    summary.value = result?.summary || {
      total_billing: 0,
      total_paid: 0,
      outstanding: 0,
      overdue: 0,
      invoice_count: 0,
      company_count: 0,
    }

    companySummary.value = result?.company_summary || []
    companyTotal.value = result?.company_summary_total || 0
    companyPage.value = result?.company_summary_page || 1
    companyTotalPages.value = result?.company_summary_total_pages || 1

    agingBreakdown.value = result?.aging_breakdown || []
    agingTotal.value = result?.aging_breakdown_total || 0
    agingPage.value = result?.aging_breakdown_page || 1
    agingTotalPages.value = result?.aging_breakdown_total_pages || 1

    executionTime.value = ((performance.now() - start) / 1000).toFixed(1)
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading corporate billing statement.'
    rows.value = []
    companies.value = []
    companySummary.value = []
    agingBreakdown.value = []
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
  billed_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.billed_amount || 0), 0),
  paid_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.paid_amount || 0), 0),
  outstanding_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.outstanding_amount || 0), 0),
}))

const maxAgingAmount = computed(() => {
  return Math.max(...agingBreakdown.value.map(row => Number(row.amount || 0)), 1)
})

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
    company: filters.value.company,
    status: filters.value.status,
    aging_bucket: filters.value.aging_bucket,
  }),
  () => {
    clearTimeout(filterTimer)
    filterTimer = setTimeout(() => {
      currentPage.value = 1
      companyPage.value = 1
      agingPage.value = 1
      fetchReport()
    }, 250)
  },
  { deep: true }
)

watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    companyPage.value = 1
    agingPage.value = 1
    fetchReport()
  }, 450)
})

watch(
  () => ({
    search: companySummaryFilters.value.search,
    status: companySummaryFilters.value.status,
    min_outstanding: companySummaryFilters.value.min_outstanding,
  }),
  () => {
    clearTimeout(companyFilterTimer)
    companyFilterTimer = setTimeout(() => {
      companyPage.value = 1
      fetchReport()
    }, 350)
  },
  { deep: true }
)

function goCompanyPage(page) {
  if (page < 1 || page > companyTotalPages.value) return
  companyPage.value = page
  fetchReport()
}

function goAgingPage(page) {
  if (page < 1 || page > agingTotalPages.value) return
  agingPage.value = page
  fetchReport()
}

function resetCompanySummaryFilters() {
  companySummaryFilters.value = {
    search: '',
    status: '',
    min_outstanding: '',
  }

  companyPage.value = 1
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
    company: '',
    status: '',
    aging_bucket: '',
  }

  companySummaryFilters.value = {
    search: '',
    status: '',
    min_outstanding: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
  companyPage.value = 1
  agingPage.value = 1

  fetchReport()
}

function getPercent(value, max) {
  if (!max) return 0
  return Math.min(100, Math.round((Number(value || 0) / Number(max)) * 100))
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-NG', {
    maximumFractionDigits: 0,
  })
}

function agingColor(bucket) {
  return {
    Current: 'bg-green-500',
    '1-30': 'bg-blue-500',
    '31-60': 'bg-amber-500',
    '61-90': 'bg-orange-500',
    '90+': 'bg-red-500',
  }[bucket] || 'bg-gray-500'
}

function agingBadgeClass(bucket) {
  return {
    Current: 'bg-green-100 text-green-700',
    '1-30': 'bg-blue-100 text-blue-700',
    '31-60': 'bg-amber-100 text-amber-700',
    '61-90': 'bg-orange-100 text-orange-700',
    '90+': 'bg-red-100 text-red-700',
  }[bucket] || 'bg-gray-100 text-gray-600'
}

function statusClass(status) {
  return {
    Paid: 'bg-green-100 text-green-700',
    Unpaid: 'bg-red-100 text-red-600',
    Overdue: 'bg-red-100 text-red-700',
    Cancelled: 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

onMounted(() => {
  fetchReport()
})

function downloadReport() {
  const params = new URLSearchParams({
    date_from: filters.value.date_from || '',
    date_to: filters.value.date_to || '',
    company: filters.value.company || '',
    status: filters.value.status || '',
    aging_bucket: filters.value.aging_bucket || '',
    search: searchQuery.value || '',
  })

  window.open(
    `/api/method/rhohotel.rhocom_hotel.api.reports.download_corporate_billing_statement_report?${params.toString()}`,
    '_blank'
  )
}
</script>