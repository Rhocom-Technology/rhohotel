<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Invoice List</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Invoice List</h1>
      <p class="text-xs text-gray-400 mt-1">All individual guest invoices — view outstanding balances, payment status, folio charges, and issue quick actions or prints.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Invoice Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ invoices.length }} total invoices • {{ unpaidCount }} unpaid • {{ overdueCount }} overdue</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing')">Billing Dashboard</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing/payments')">Payment List</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Invoice</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Invoices</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ invoices.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unpaid</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Pending</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ unpaidCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Overdue</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ overdueCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Outstanding</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Balance</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦2.14M</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search invoice no., guest, room..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Unpaid</option>
          <option>Part Paid</option>
          <option>Paid</option>
          <option>Overdue</option>
        </select>
        <select v-model="filterType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Types</option>
          <option>Room</option>
          <option>Restaurant</option>
          <option>Minibar</option>
          <option>Laundry</option>
          <option>Misc</option>
        </select>
        <button @click="search='';filterStatus='';filterType='';showOverdueOnly=false;currentPage=1"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showOverdueOnly = !showOverdueOnly; currentPage = 1">
          {{ showOverdueOnly ? 'Show All' : 'Overdue Only' }}
        </button>
      </div>
    </div>

    <!-- Invoice Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Invoice Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} invoices</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issue Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Due Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Balance</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in paged" :key="inv.invoiceNo"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ inv.invoiceNo }}</td>
            <td class="px-4 py-4">
              <p class="text-xs font-bold text-gray-900">{{ inv.guest }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ inv.guestNote }}</p>
            </td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-700">{{ inv.room }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.issueDate }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.dueDate }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ inv.amount }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ inv.balance }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="invoiceStatusClass(inv.status)">{{ inv.status }}</span>
            </td>
            <td class="px-4 py-4">
              <div class="flex items-center gap-1.5">
                <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  View
                </button>
                <button v-if="inv.status === 'Unpaid' || inv.status === 'Part Paid' || inv.status === 'Overdue'"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                  Settle
                </button>
                <button v-if="inv.status === 'Paid'"
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
const filterStatus = ref('')
const filterType = ref('')
const showOverdueOnly = ref(false)
const currentPage = ref(1)
const perPage = 25

const invoices = [
  { invoiceNo: 'INV-000501', guest: 'Ngozi Cole',        guestNote: 'VIP Guest • Loyalty Member',        room: '511', type: 'Room',       issueDate: '05 May 2026', dueDate: '05 May 2026', amount: '₦185,000',  balance: '₦185,000',  status: 'Unpaid'   },
  { invoiceNo: 'INV-000500', guest: 'Emeka Obi',         guestNote: 'Standard Guest',                    room: '203', type: 'Room',       issueDate: '04 May 2026', dueDate: '06 May 2026', amount: '₦120,000',  balance: '₦60,000',   status: 'Part Paid'},
  { invoiceNo: 'INV-000499', guest: 'Fatima Bello',      guestNote: 'Conference Attendee',                room: '318', type: 'Restaurant', issueDate: '03 May 2026', dueDate: '03 May 2026', amount: '₦45,500',   balance: '₦0.00',     status: 'Paid'     },
  { invoiceNo: 'INV-000498', guest: 'Chidi Nwosu',       guestNote: 'Long Stay Guest',                   room: '102', type: 'Room',       issueDate: '02 May 2026', dueDate: '02 May 2026', amount: '₦540,000',  balance: '₦540,000',  status: 'Overdue'  },
  { invoiceNo: 'INV-000497', guest: 'Amara Eze',         guestNote: 'Honeymoon Package',                 room: '601', type: 'Misc',       issueDate: '01 May 2026', dueDate: '03 May 2026', amount: '₦220,000',  balance: '₦220,000',  status: 'Overdue'  },
  { invoiceNo: 'INV-000496', guest: 'Tunde Adeyemi',     guestNote: 'Standard Guest',                    room: '407', type: 'Minibar',    issueDate: '01 May 2026', dueDate: '01 May 2026', amount: '₦18,500',   balance: '₦0.00',     status: 'Paid'     },
  { invoiceNo: 'INV-000495', guest: 'Blessing Okoro',    guestNote: 'Corporate Delegate',                room: '215', type: 'Laundry',    issueDate: '30 Apr 2026', dueDate: '30 Apr 2026', amount: '₦12,000',   balance: '₦0.00',     status: 'Paid'     },
  { invoiceNo: 'INV-000494', guest: 'Ibrahim Musa',      guestNote: 'Business Traveller',                room: '309', type: 'Room',       issueDate: '28 Apr 2026', dueDate: '04 May 2026', amount: '₦375,000',  balance: '₦375,000',  status: 'Unpaid'   },
  { invoiceNo: 'INV-000493', guest: 'Chisom Anozie',     guestNote: 'Weekend Package',                   room: '504', type: 'Room',       issueDate: '27 Apr 2026', dueDate: '29 Apr 2026', amount: '₦95,000',   balance: '₦95,000',   status: 'Overdue'  },
  { invoiceNo: 'INV-000492', guest: 'Uche Dibia',        guestNote: 'Extended Stay',                     room: '112', type: 'Restaurant', issueDate: '26 Apr 2026', dueDate: '26 Apr 2026', amount: '₦67,000',   balance: '₦30,000',   status: 'Part Paid'},
]

const unpaidCount = computed(() => invoices.filter(i => i.status === 'Unpaid' || i.status === 'Part Paid').length)
const overdueCount = computed(() => invoices.filter(i => i.status === 'Overdue').length)

const filtered = computed(() => {
  let list = invoices
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(i =>
      i.invoiceNo.toLowerCase().includes(q) ||
      i.guest.toLowerCase().includes(q) ||
      i.room.toLowerCase().includes(q)
    )
  }
  if (filterStatus.value) list = list.filter(i => i.status === filterStatus.value)
  if (filterType.value) list = list.filter(i => i.type === filterType.value)
  if (showOverdueOnly.value) list = list.filter(i => i.status === 'Overdue')
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function invoiceStatusClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Part Paid': 'bg-blue-50 text-blue-600',
    'Paid':      'bg-green-50 text-green-600',
    'Overdue':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>
