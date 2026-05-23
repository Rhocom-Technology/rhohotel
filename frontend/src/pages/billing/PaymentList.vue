<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Payment List</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Payment List</h1>
      <p class="text-xs text-gray-400 mt-1">All payment receipts received — track allocation status, payment methods, amounts, and link receipts to guest folios or corporate accounts.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Payment Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ payments.length }} total receipts • {{ unallocatedCount }} unallocated • {{ allocatedCount }} fully allocated</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing')">Billing Dashboard</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing/invoices')">Invoice List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Record Payment</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Received Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦840K</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Received This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Month</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦14.3M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unallocated Receipts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ unallocatedCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Receipts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ payments.length }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search receipt no., guest, reference..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterMethod" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Methods</option>
          <option>Cash</option>
          <option>Bank Transfer</option>
          <option>POS</option>
          <option>Cheque</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Allocated</option>
          <option>Part Allocated</option>
          <option>Unallocated</option>
        </select>
        <button @click="search='';filterMethod='';filterStatus='';showUnallocatedOnly=false;currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showUnallocatedOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showUnallocatedOnly = !showUnallocatedOnly; currentPage = 1">
          {{ showUnallocatedOnly ? 'Show All' : 'Unallocated Only' }}
        </button>
      </div>
    </div>

    <!-- Payment Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Payment Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} payments</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Receipt No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Payer</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Method</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Reference</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date Received</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Allocated</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in paged" :key="p.receiptNo"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ p.receiptNo }}</td>
            <td class="px-4 py-4">
              <p class="text-xs font-bold text-gray-900">{{ p.payer }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ p.payerNote }}</p>
            </td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="methodClass(p.method)">{{ p.method }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-500 font-mono">{{ p.reference }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ p.date }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ p.amount }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ p.allocated }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="paymentStatusClass(p.status)">{{ p.status }}</span>
            </td>
            <td class="px-4 py-4">
              <div class="flex items-center gap-1.5">
                <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  View
                </button>
                <button v-if="p.status !== 'Allocated'"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                  Allocate
                </button>
                <button v-if="p.status === 'Allocated'"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  Print
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
          <button v-for="p in totalPages" :key="p" @click="currentPage = p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages ? currentPage++ : null"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const search = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const showUnallocatedOnly = ref(false)
const currentPage = ref(1)
const perPage = 25

const payments = [
  { receiptNo: 'RCPT-000231', payer: 'Ngozi Cole',                payerNote: 'Guest • Room 511',                   method: 'POS',           reference: 'POS-92831',    date: '07 May 2026', amount: '₦185,000',  allocated: '₦185,000',  status: 'Allocated'       },
  { receiptNo: 'RCPT-000230', payer: 'Wells Corporate Services',  payerNote: 'Corporate Account',                  method: 'Bank Transfer', reference: 'TXN-0013982',  date: '07 May 2026', amount: '₦750,000',  allocated: '₦0.00',     status: 'Unallocated'     },
  { receiptNo: 'RCPT-000229', payer: 'Emeka Obi',                 payerNote: 'Guest • Room 203',                   method: 'Cash',          reference: 'CSH-00112',    date: '06 May 2026', amount: '₦60,000',   allocated: '₦60,000',   status: 'Allocated'       },
  { receiptNo: 'RCPT-000228', payer: 'Ibrahim Musa',              payerNote: 'Guest • Room 309',                   method: 'Bank Transfer', reference: 'TXN-0013870',  date: '05 May 2026', amount: '₦200,000',  allocated: '₦200,000',  status: 'Part Allocated'  },
  { receiptNo: 'RCPT-000227', payer: 'Rubiconnode Ltd',           payerNote: 'Corporate Account',                  method: 'Bank Transfer', reference: 'TXN-0013802',  date: '04 May 2026', amount: '₦500,000',  allocated: '₦500,000',  status: 'Allocated'       },
  { receiptNo: 'RCPT-000226', payer: 'Uche Dibia',                payerNote: 'Guest • Room 112',                   method: 'POS',           reference: 'POS-91774',    date: '03 May 2026', amount: '₦37,000',   allocated: '₦37,000',   status: 'Allocated'       },
  { receiptNo: 'RCPT-000225', payer: 'Accentral Group',           payerNote: 'Corporate Account',                  method: 'Cheque',        reference: 'CHQ-00228',    date: '02 May 2026', amount: '₦300,000',  allocated: '₦0.00',     status: 'Unallocated'     },
  { receiptNo: 'RCPT-000224', payer: 'Tunde Adeyemi',             payerNote: 'Guest • Room 407',                   method: 'Cash',          reference: 'CSH-00109',    date: '01 May 2026', amount: '₦18,500',   allocated: '₦18,500',   status: 'Allocated'       },
  { receiptNo: 'RCPT-000223', payer: 'Fixcenter Services',        payerNote: 'Corporate Account',                  method: 'Bank Transfer', reference: 'TXN-0013751',  date: '30 Apr 2026', amount: '₦460,000',  allocated: '₦460,000',  status: 'Allocated'       },
  { receiptNo: 'RCPT-000222', payer: 'Chisom Anozie',             payerNote: 'Guest • Room 504',                   method: 'POS',           reference: 'POS-90811',    date: '29 Apr 2026', amount: '₦95,000',   allocated: '₦0.00',     status: 'Unallocated'     },
]

const unallocatedCount = computed(() => payments.filter(p => p.status === 'Unallocated').length)
const allocatedCount = computed(() => payments.filter(p => p.status === 'Allocated').length)

const filtered = computed(() => {
  let list = payments
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(p =>
      p.receiptNo.toLowerCase().includes(q) ||
      p.payer.toLowerCase().includes(q) ||
      p.reference.toLowerCase().includes(q)
    )
  }
  if (filterMethod.value) list = list.filter(p => p.method === filterMethod.value)
  if (filterStatus.value) list = list.filter(p => p.status === filterStatus.value)
  if (showUnallocatedOnly.value) list = list.filter(p => p.status === 'Unallocated')
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function methodClass(m) {
  return {
    'Cash':          'bg-green-50 text-green-600',
    'Bank Transfer': 'bg-blue-50 text-blue-600',
    'POS':           'bg-purple-50 text-purple-600',
    'Cheque':        'bg-yellow-50 text-yellow-600',
  }[m] || 'bg-gray-100 text-gray-500'
}

function paymentStatusClass(s) {
  return {
    'Allocated':      'bg-green-50 text-green-600',
    'Part Allocated': 'bg-blue-50 text-blue-600',
    'Unallocated':    'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>
