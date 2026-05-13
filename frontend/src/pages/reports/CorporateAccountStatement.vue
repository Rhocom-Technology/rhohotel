<template>
  <div class="space-y-5">

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Account Statement</h1>
      <p class="text-xs text-gray-400 mt-1">Review charges, invoices, payments, outstanding balance, aging buckets, and account activity for a selected corporate client.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end gap-2">
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Report view</button>
      <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export PDF</button>
      <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Send Statement</button>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Current Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Outstanding</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦4,860,000</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Invoiced</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Period</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦12,450,000</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Paid</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Received</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦7,590,000</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue 30+ Days</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Aging</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦1,980,000</p>
      </div>
    </div>

    <!-- Statement Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Statement Filters</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div style="min-width:220px;">
          <input v-model="filterClient" type="text"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
            placeholder="Select client..." />
        </div>
        <div style="min-width:160px;">
          <input v-model="filterDate" type="text"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
            placeholder="Jan 01 - Apr 18, 2026" />
        </div>
        <select v-model="filterTxType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Transactions</option>
          <option>Invoices Only</option>
          <option>Payments Only</option>
          <option>Credit Notes</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Invoice Status</option>
          <option>Paid</option>
          <option>Unpaid</option>
          <option>Overdue</option>
          <option>Part Paid</option>
        </select>
        <button @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showOverdueOnly = !showOverdueOnly">
          {{ showOverdueOnly ? 'Show All' : 'Show Overdue Only' }}
        </button>
      </div>
    </div>

    <!-- Statement Activity + Snapshot -->
    <div style="display:grid;grid-template-columns:1fr 280px;gap:12px;">

      <!-- Statement Activity Table -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Statement Activity</h3>
          <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} entries</p>
        </div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Date</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Reference</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Description</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Debit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Credit</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Balance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in paged" :key="t.ref"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
              <td class="px-5 py-4 text-xs text-gray-600 whitespace-nowrap">{{ t.date }}</td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900 whitespace-nowrap">{{ t.ref }}</td>
              <td class="px-4 py-4">
                <p class="text-xs text-gray-700">{{ t.desc }}</p>
                <p class="text-xs mt-0.5" :class="t.subClass">{{ t.sub }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-right font-semibold text-gray-900">{{ t.debit || '—' }}</td>
              <td class="px-4 py-4 text-xs text-right font-semibold text-green-600">{{ t.credit || '—' }}</td>
              <td class="px-5 py-4 text-xs text-right font-bold text-gray-900">{{ t.balance }}</td>
            </tr>
          </tbody>
        </table>
        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
          <p class="text-xs text-gray-400">Rows per page: 10</p>
          <div class="flex items-center gap-1">
            <button v-for="p in totalPages" :key="p" @click="currentPage=p"
              class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
              :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
              {{ p }}
            </button>
            <button @click="currentPage < totalPages && currentPage++"
              :disabled="currentPage === totalPages"
              class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 ml-1 transition-colors">Next</button>
          </div>
        </div>
      </div>

      <!-- Account Snapshot -->
      <div class="space-y-3">
        <h3 class="text-sm font-bold text-gray-900">Account Snapshot</h3>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-1">Client</p>
          <p class="text-sm font-bold text-gray-900">Wells Corporate Services Ltd</p>
          <p class="text-xs text-green-600 mt-1">Credit limit: ₦15,000,000</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-3">Aging Summary</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">Current: ₦2,880,000</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">1-30 Days: ₦1,120,000</p>
          <p class="text-xs text-gray-600 py-1">31-60 Days: ₦1,980,000</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-2">Payment Terms</p>
          <p class="text-xs text-gray-600">Net 30 days</p>
          <p class="text-xs text-gray-600 mt-1">Last payment: 12 Apr 2026</p>
        </div>

        <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
          <p class="text-sm font-bold text-blue-700 mb-2">Suggested Follow-up</p>
          <p class="text-xs text-blue-600 leading-relaxed">Send reminder for INV-000396 and attach updated statement with aging breakdown.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">Corporate client statement with ledger activity, aging analysis, and follow-up readiness.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const filterClient = ref('Wells Corporate Services Ltd')
const filterDate = ref('Jan 01 - Apr 18, 2026')
const filterTxType = ref('')
const filterStatus = ref('')
const showOverdueOnly = ref(false)
const currentPage = ref(1)
const perPage = 10

const transactions = [
  { date: '18 Apr 2026', ref: 'INV-000431', desc: 'Accommodation invoice - March stay batch', sub: 'Due in 14 days',         subClass: 'text-gray-400', debit: '₦1,250,000', credit: '',          balance: '₦4,860,000', type: 'invoice', overdue: false },
  { date: '12 Apr 2026', ref: 'PAY-000188', desc: 'Bank transfer received',                    sub: 'Applied to oldest invoices', subClass: 'text-gray-400', debit: '',           credit: '₦750,000',  balance: '₦3,610,000', type: 'payment', overdue: false },
  { date: '04 Apr 2026', ref: 'INV-000417', desc: 'Conference hall charges',                   sub: 'Overdue by 10 days',     subClass: 'text-red-400',  debit: '₦680,000',  credit: '',          balance: '₦4,360,000', type: 'invoice', overdue: true },
  { date: '29 Mar 2026', ref: 'CRN-000041', desc: 'Credit note - cancelled room night',        sub: 'Adjustment approved',    subClass: 'text-gray-400', debit: '',           credit: '₦120,000',  balance: '₦3,680,000', type: 'credit',  overdue: false },
  { date: '20 Mar 2026', ref: 'INV-000396', desc: 'Corporate lodging invoice - February',      sub: 'Overdue by 32 days',     subClass: 'text-red-400',  debit: '₦1,980,000', credit: '',         balance: '₦3,800,000', type: 'invoice', overdue: true },
  { date: '15 Mar 2026', ref: 'PAY-000171', desc: 'Cheque payment cleared',                    sub: 'Reconciled successfully',subClass: 'text-gray-400', debit: '',           credit: '₦2,100,000',balance: '₦1,820,000', type: 'payment', overdue: false },
  { date: '05 Mar 2026', ref: 'INV-000381', desc: 'Accommodation batch - January closes',      sub: 'Paid in full',           subClass: 'text-green-500',debit: '₦950,000',  credit: '',          balance: '₦3,920,000', type: 'invoice', overdue: false },
  { date: '22 Feb 2026', ref: 'PAY-000154', desc: 'Bank transfer - February payment',          sub: 'Applied to INV-000361',  subClass: 'text-gray-400', debit: '',           credit: '₦1,500,000',balance: '₦2,970,000', type: 'payment', overdue: false },
  { date: '10 Feb 2026', ref: 'INV-000361', desc: 'January corporate accommodation',           sub: 'Settled',                subClass: 'text-green-500',debit: '₦1,750,000', credit: '',         balance: '₦4,470,000', type: 'invoice', overdue: false },
  { date: '01 Feb 2026', ref: 'PAY-000141', desc: 'Opening balance payment received',          sub: 'Reconciled successfully',subClass: 'text-gray-400', debit: '',           credit: '₦800,000',  balance: '₦2,720,000', type: 'payment', overdue: false },
  { date: '20 Jan 2026', ref: 'INV-000344', desc: 'December lodging batch invoice',            sub: 'Fully settled',          subClass: 'text-green-500',debit: '₦1,100,000', credit: '',         balance: '₦3,520,000', type: 'invoice', overdue: false },
  { date: '10 Jan 2026', ref: 'PAY-000128', desc: 'Wire transfer received - December',         sub: 'Applied to oldest',      subClass: 'text-gray-400', debit: '',           credit: '₦1,200,000',balance: '₦2,420,000', type: 'payment', overdue: false },
]

function resetFilters() {
  filterClient.value = 'Wells Corporate Services Ltd'
  filterDate.value = 'Jan 01 - Apr 18, 2026'
  filterTxType.value = ''
  filterStatus.value = ''
  showOverdueOnly.value = false
  currentPage.value = 1
}

const filtered = computed(() => {
  let list = transactions
  if (showOverdueOnly.value) list = list.filter(t => t.overdue)
  if (filterTxType.value === 'Invoices Only') list = list.filter(t => t.type === 'invoice')
  if (filterTxType.value === 'Payments Only') list = list.filter(t => t.type === 'payment')
  if (filterTxType.value === 'Credit Notes') list = list.filter(t => t.type === 'credit')
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))
</script>