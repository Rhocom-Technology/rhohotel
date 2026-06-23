<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Corporate billing • company bills, statements, outstanding balances, and payment follow-up</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end sm:px-6">
      <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
        @click="$router.push('/billing')">Invoice List</button>
      <button class="w-full px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto">Export Bills</button>
      <button class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors sm:w-auto">Generate Statement</button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Active Corporate Bills</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '…' : summary.activeBills }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Outstanding Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '…' : summary.outstandingValue }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Paid This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Received</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '…' : summary.paidThisMonth }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue Bills</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '…' : summary.overdueCount }}</p>
      </div>
    </div>

    <!-- AI Corporate Billing Summary -->
    <AIInsightPanel
      title="AI Corporate Billing Analysis"
      context-type="billing_risk_summary"
      :context-data="corporateBillsAiContext"
      :auto-load="false"
      panel-id="corporate-bill-list"
    />

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div class="w-full sm:min-w-[180px] sm:flex-1">
          <input v-model="search" type="text" placeholder="Search client, bill no., statement..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
     <div
  id="corporate-client-dropdown"
  class="relative w-full sm:min-w-[220px] sm:w-auto"
>
  <input
  v-model="clientSearch"
  @focus="showClientDropdown = true"
  type="text"
  placeholder="Search corporate customer..."
  class="w-full px-3 py-2.5 pr-8 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-600"
/>

<span
  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"
>
  ▼
</span>

  <div
    v-if="showClientDropdown"
    class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto"
  >
    <button
      type="button"
      @click="filterClient = ''; clientSearch = ''; showClientDropdown = false"
      class="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 font-medium text-gray-700"
    >
      All Corporate Customers
    </button>

    <button
      v-for="c in filteredClients"
      :key="c.name"
      type="button"
      @click="filterClient = c.name; clientSearch = c.customer_name || c.name; showClientDropdown = false"
      class="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 text-gray-700"
    >
      {{ c.customer_name || c.name }}
    </button>

    <div
      v-if="!filteredClients.length"
      class="px-3 py-2 text-xs text-gray-400"
    >
      No corporate customer found.
    </div>
  </div>
</div>
        <select v-model="filterStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Statuses</option>
          <option>Unpaid</option>
          <option>Part Paid</option>
          <option>Paid</option>
          <option>Overdue</option>
        </select>
        <select v-model="filterDueDate" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Due Dates</option>
          <option>This Week</option>
          <option>This Month</option>
          <option>Overdue</option>
        </select>
        <button
  @click="search='';filterClient='';clientSearch='';filterStatus='';filterDueDate='';showOverdueOnly=false;currentPage=1"
  class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
>
  Reset
</button>
        <button
          class="w-full px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors sm:w-auto"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showOverdueOnly = !showOverdueOnly">
          {{ showOverdueOnly ? 'Show All Bills' : 'Show Overdue Bills Only' }}
        </button>
      </div>
    </div>

      <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-xs text-red-600">{{ error }}</div>

    <!-- Corporate Bill Records -->
    <div class="bg-white rounded-xl border-2 border-blue-400 overflow-hidden">
      <div class="px-4 py-4 border-b border-gray-100 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h3 class="text-sm font-bold text-gray-900">Corporate Bill Records</h3>
        <p class="text-xs text-gray-400">Showing {{ filtered.length === 0 ? 0 : pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} bills</p>
      </div>
      <div class="overflow-x-auto">
      <table class="w-full min-w-[980px]">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Bill No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Client</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Statement Period</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issue Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Due Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Balance</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="px-6 py-10 text-center text-xs text-gray-400">Loading bills…</td>
          </tr>
          <tr v-else-if="paged.length === 0">
            <td colspan="9" class="px-6 py-10 text-center text-xs text-gray-400">No bills found.</td>
          </tr>
          <tr v-for="b in paged" :key="b.billNo" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ b.billNo }}</td>
            <td class="px-4 py-4">
              <p class="text-xs font-bold text-gray-900">{{ b.client }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ b.clientNote }}</p>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ b.period }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ b.issueDate }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ b.dueDate }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ b.amount }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ b.balance }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="billStatusClass(b.status)">{{ b.status }}</span>
            </td>
            <td class="px-4 py-4">
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push('/billing/corporate/' + b.billNo)">
                {{ b.action }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <div class="px-4 py-4 border-t border-gray-100 flex flex-col gap-3 bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex flex-wrap items-center gap-1">
          <button v-for="p in totalPages" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { callMethodForm } from '@/lib/api'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const search = ref('')
const filterClient = ref('')
const clientSearch = ref('')
const showClientDropdown = ref(false)
const filterStatus = ref('')
const filterDueDate = ref('')
const showOverdueOnly = ref(false)
const currentPage = ref(1)
const perPage = 25

const bills = ref([])
const summary = ref({ activeBills: 0, outstandingValue: '₦0', paidThisMonth: '₦0', overdueCount: 0 })
const loading = ref(false)
const error = ref('')

const corporateBillsAiContext = computed(() => {
  if (!bills.value.length && !summary.value.activeBills) return null
  const overdueBills = bills.value.filter(b => b.status === 'Overdue').slice(0, 5)
  return {
    active_bills: summary.value.activeBills,
    outstanding_value: summary.value.outstandingValue,
    paid_this_month: summary.value.paidThisMonth,
    overdue_count: summary.value.overdueCount,
    top_overdue_bills: overdueBills.map(b => ({
      client: b.client, balance: b.balance, due: b.dueDate,
    })),
  }
})


function handleClickOutside(event) {
  const dropdown = document.getElementById('corporate-client-dropdown')

  if (dropdown && !dropdown.contains(event.target)) {
    showClientDropdown.value = false
  }
}

onMounted(() => {
  fetchBills()
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})


const clients = computed(() =>
  [...new Map(
    bills.value
      .filter(b => b.client_id)
      .map(b => [b.client_id, {
        name: b.client_id,
        customer_name: b.client || b.client_id
      }])
  ).values()].sort((a, b) =>
    String(a.customer_name || '').localeCompare(String(b.customer_name || ''))
  )
)

const filteredClients = computed(() => {
  const q = clientSearch.value.toLowerCase().trim()

  if (!q) return clients.value

  return clients.value.filter(c =>
    String(c.customer_name || c.name || '').toLowerCase().includes(q)
  )
})

async function fetchBills() {
  loading.value = true
  error.value = ''

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_billing.get_corporate_bills',
      { page: 1, page_size: 500 }
    )

    bills.value = result?.bills || []

    summary.value = result?.summary || {
      activeBills: 0,
      outstandingValue: '₦0',
      paidThisMonth: '₦0',
      overdueCount: 0
    }

    // clients.value = result?.customers || []

  } catch (e) {
    error.value = e.message || 'Failed to load bills'
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  let list = bills.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(b => b.billNo.toLowerCase().includes(q) || b.client.toLowerCase().includes(q))
  }
  if (filterClient.value) list = list.filter(b => b.client_id === filterClient.value)
  if (filterStatus.value) list = list.filter(b => b.status === filterStatus.value)
  if (showOverdueOnly.value) list = list.filter(b => b.status === 'Overdue')
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function billStatusClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Part Paid': 'bg-blue-50 text-blue-600',
    'Paid':      'bg-green-50 text-green-600',
    'Overdue':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

// onMounted(fetchBills)
</script>