<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Corporate billing • company bills, statements, outstanding balances, and payment follow-up</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end gap-2">
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        @click="$router.push('/billing')">Invoice List</button>
      <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Bills</button>
      <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Generate Statement</button>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Active Corporate Bills</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Open</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">32</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Outstanding Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦6.18M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Paid This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Received</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦7.59M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue Bills</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">9</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search client, bill no., statement..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterClient" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Clients</option>
          <option>Wells Corporate Services</option>
          <option>Rubiconnode Ltd</option>
          <option>Herotech Ltd</option>
          <option>Accentral Group</option>
          <option>Fixcenter Services</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Unpaid</option>
          <option>Part Paid</option>
          <option>Paid</option>
          <option>Overdue</option>
        </select>
        <select v-model="filterDueDate" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Due Dates</option>
          <option>This Week</option>
          <option>This Month</option>
          <option>Overdue</option>
        </select>
        <button @click="search='';filterClient='';filterStatus='';filterDueDate='';showOverdueOnly=false;currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showOverdueOnly = !showOverdueOnly">
          {{ showOverdueOnly ? 'Show All Bills' : 'Show Overdue Bills Only' }}
        </button>
      </div>
    </div>

    <!-- Corporate Bill Records -->
    <div class="bg-white rounded-xl border-2 border-blue-400 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Corporate Bill Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} bills</p>
      </div>
      <table class="w-full">
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
              <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                {{ b.action }}
              </button>
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
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const search = ref('')
const filterClient = ref('')
const filterStatus = ref('')
const filterDueDate = ref('')
const showOverdueOnly = ref(false)
const currentPage = ref(1)
const perPage = 25

const bills = [
  { billNo: 'CBL-000431', client: 'Wells Corporate Services', clientNote: 'Accommodation + conference charges', period: 'Mar 2026', issueDate: '18 Apr 2026', dueDate: '02 May 2026', amount: '₦1,250,000', balance: '₦1,250,000', status: 'Unpaid',   action: 'View' },
  { billNo: 'CBL-000430', client: 'Rubiconnode Ltd',          clientNote: 'Staff lodging invoice batch',        period: 'Apr 2026', issueDate: '16 Apr 2026', dueDate: '30 Apr 2026', amount: '₦920,000',   balance: '₦420,000',   status: 'Part Paid',action: 'View' },
  { billNo: 'CBL-000429', client: 'Herotech Ltd',             clientNote: 'Executive room usage billing',       period: 'Apr 2026', issueDate: '10 Apr 2026', dueDate: '24 Apr 2026', amount: '₦640,000',   balance: '₦640,000',   status: 'Unpaid',   action: 'View' },
  { billNo: 'CBL-000428', client: 'Wells Corporate Services', clientNote: 'February lodging invoice',           period: 'Feb 2026', issueDate: '20 Mar 2026', dueDate: '03 Apr 2026', amount: '₦1,980,000', balance: '₦1,980,000', status: 'Overdue',  action: 'Follow Up' },
  { billNo: 'CBL-000427', client: 'Accentral Group',          clientNote: 'Team stay and transport charges',   period: 'Apr 2026', issueDate: '15 Apr 2026', dueDate: '29 Apr 2026', amount: '₦540,000',   balance: '₦240,000',   status: 'Part Paid',action: 'View' },
  { billNo: 'CBL-000426', client: 'Fixcenter Services',       clientNote: 'Partner accommodation charges',     period: 'Apr 2026', issueDate: '11 Apr 2026', dueDate: '25 Apr 2026', amount: '₦460,000',   balance: '₦0.00',      status: 'Paid',     action: 'Print' },
  { billNo: 'CBL-000425', client: 'Herotech Ltd',             clientNote: 'Monthly corporate accommodation',   period: 'Mar 2026', issueDate: '01 Apr 2026', dueDate: '15 Apr 2026', amount: '₦780,000',   balance: '₦0.00',      status: 'Paid',     action: 'Print' },
  { billNo: 'CBL-000424', client: 'Rubiconnode Ltd',          clientNote: 'Conference and room charges',       period: 'Mar 2026', issueDate: '28 Mar 2026', dueDate: '11 Apr 2026', amount: '₦310,000',   balance: '₦310,000',   status: 'Overdue',  action: 'Follow Up' },
]

const filtered = computed(() => {
  let list = bills
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(b => b.billNo.toLowerCase().includes(q) || b.client.toLowerCase().includes(q))
  }
  if (filterClient.value) list = list.filter(b => b.client === filterClient.value)
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
</script>