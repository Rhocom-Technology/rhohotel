<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Billing / Payment List</p>
      <h1 class="text-2xl font-bold text-gray-900">Payment List</h1>
      <p class="text-xs text-gray-400 mt-1">Track all front desk payment transactions, balances, methods, references, and posting status.</p>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Payments Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Posted</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">86</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Collected</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦12.8M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unallocated</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Outstanding Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Due</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦18.4M</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search payment</p>
          <input
            v-model="search"
            type="text"
            placeholder="Receipt no., guest, reservation..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Method</p>
          <select v-model="filterMethod" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Methods</option>
            <option value="Cash">Cash</option>
            <option value="Card">Card</option>
            <option value="POS">POS</option>
            <option value="Bank Transfer">Bank Transfer</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Posting Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option value="Posted">Posted</option>
            <option value="Pending">Pending</option>
            <option value="Reversed">Reversed</option>
          </select>
        </div>
        <div style="flex:1;min-width:120px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
          <input v-model="filterDate" type="text" placeholder="Today"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600" />
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Receive Payment</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">All Payments</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ Math.min(pageSize, filteredList.length) }} of {{ filteredList.length.toLocaleString() }} payments</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Receipt</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Guest / Reservation</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Method</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Reference</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Amount</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Posting Status</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="item in paginatedList"
              :key="item.id"
              class="hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <td class="px-6 py-4">
                <p class="text-xs font-bold text-gray-900">{{ item.id }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.date }}</p>
              </td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ item.guest }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ item.reservation }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.method }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ item.reference }}</td>
              <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ formatCurrency(item.amount) }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(item.status)">
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-4">
                <button class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors">
                  Open
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ pageSize }}</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button
              v-for="p in Math.min(totalPages, 5)"
              :key="p"
              @click="page = p"
              class="w-6 h-6 text-xs rounded flex items-center justify-center transition-colors"
              :class="page === p ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            >{{ p }}</button>
            <span v-if="totalPages > 5" class="text-xs text-gray-400">... {{ totalPages }}</span>
          </div>
          <button
            @click="page = Math.min(page + 1, totalPages)"
            :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
          >Next</button>
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
const filterDate = ref('')
const page = ref(1)
const pageSize = 10

const payments = [
  { id: 'PMT-2026-01152', date: '15 Apr 2026 • 10:08 AM', guest: 'Chinedu Okafor', reservation: 'RES-2026-00481', method: 'POS', reference: 'MON-883921', amount: 80000, status: 'Posted' },
  { id: 'PMT-2026-01153', date: '15 Apr 2026 • 10:15 AM', guest: 'Sarah Johnson', reservation: 'RES-2026-00483', method: 'Card', reference: 'STR-204188', amount: 220000, status: 'Posted' },
  { id: 'PMT-2026-01154', date: '15 Apr 2026 • 10:23 AM', guest: 'Apex Holdings', reservation: 'RES-2026-00482', method: 'Bank Transfer', reference: 'TRF-991204', amount: 1500000, status: 'Pending' },
  { id: 'PMT-2026-01155', date: '15 Apr 2026 • 10:30 AM', guest: 'Emeka Adeyemi', reservation: 'RES-2026-00490', method: 'Cash', reference: 'CSH-000381', amount: 120000, status: 'Posted' },
  { id: 'PMT-2026-01156', date: '15 Apr 2026 • 10:38 AM', guest: 'Grace Cole', reservation: 'RES-2026-00491', method: 'POS', reference: 'MON-883977', amount: 64000, status: 'Reversed' },
  { id: 'PMT-2026-01157', date: '15 Apr 2026 • 10:45 AM', guest: 'Bamidele Akin', reservation: 'RES-2026-00488', method: 'Card', reference: 'STR-204230', amount: 180000, status: 'Posted' },
  { id: 'PMT-2026-01158', date: '15 Apr 2026 • 10:52 AM', guest: 'Ngozi Lawson', reservation: 'RES-2026-00482', method: 'POS', reference: 'CRD-APX-09', amount: 820000, status: 'Pending' },
  { id: 'PMT-2026-01159', date: '15 Apr 2026 • 10:00 AM', guest: 'Fatima Ahmed', reservation: 'RES-2026-00492', method: 'Bank Transfer', reference: 'TRF-991240', amount: 54000, status: 'Posted' },
  { id: 'PMT-2026-01160', date: '14 Apr 2026 • 09:15 AM', guest: 'Tunde Balogun', reservation: 'RES-2026-00477', method: 'Cash', reference: 'CSH-000375', amount: 95000, status: 'Posted' },
  { id: 'PMT-2026-01161', date: '14 Apr 2026 • 09:45 AM', guest: 'Amina Yusuf', reservation: 'RES-2026-00478', method: 'Card', reference: 'STR-204100', amount: 310000, status: 'Posted' },
  { id: 'PMT-2026-01162', date: '14 Apr 2026 • 11:00 AM', guest: 'Chibuzor Nweke', reservation: 'RES-2026-00479', method: 'POS', reference: 'MON-883800', amount: 75000, status: 'Pending' },
  { id: 'PMT-2026-01163', date: '14 Apr 2026 • 11:30 AM', guest: 'Oluwaseun Adisa', reservation: 'RES-2026-00480', method: 'Bank Transfer', reference: 'TRF-991100', amount: 450000, status: 'Posted' },
  { id: 'PMT-2026-01164', date: '13 Apr 2026 • 08:00 AM', guest: 'Kemi Obi', reservation: 'RES-2026-00470', method: 'Cash', reference: 'CSH-000360', amount: 60000, status: 'Reversed' },
  { id: 'PMT-2026-01165', date: '13 Apr 2026 • 08:45 AM', guest: 'Emeka Eze', reservation: 'RES-2026-00471', method: 'Card', reference: 'STR-204050', amount: 200000, status: 'Posted' },
  { id: 'PMT-2026-01166', date: '13 Apr 2026 • 09:30 AM', guest: 'Halima Musa', reservation: 'RES-2026-00472', method: 'POS', reference: 'MON-883700', amount: 130000, status: 'Posted' },
  { id: 'PMT-2026-01167', date: '12 Apr 2026 • 14:00 PM', guest: 'Biodun Fashola', reservation: 'RES-2026-00465', method: 'Bank Transfer', reference: 'TRF-991000', amount: 980000, status: 'Pending' },
  { id: 'PMT-2026-01168', date: '12 Apr 2026 • 14:30 PM', guest: 'Chioma Okafor', reservation: 'RES-2026-00466', method: 'Cash', reference: 'CSH-000350', amount: 45000, status: 'Posted' },
  { id: 'PMT-2026-01169', date: '12 Apr 2026 • 15:00 PM', guest: 'Samuel Dada', reservation: 'RES-2026-00467', method: 'Card', reference: 'STR-203990', amount: 275000, status: 'Posted' },
  { id: 'PMT-2026-01170', date: '11 Apr 2026 • 10:00 AM', guest: 'Rukayat Bello', reservation: 'RES-2026-00460', method: 'POS', reference: 'MON-883600', amount: 88000, status: 'Posted' },
  { id: 'PMT-2026-01171', date: '11 Apr 2026 • 10:30 AM', guest: 'Tokunbo Adewale', reservation: 'RES-2026-00461', method: 'Bank Transfer', reference: 'TRF-990900', amount: 620000, status: 'Pending' },
]

const filteredList = computed(() => {
  let list = payments
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.id.toLowerCase().includes(q) ||
      r.guest.toLowerCase().includes(q) ||
      r.reservation.toLowerCase().includes(q) ||
      r.reference.toLowerCase().includes(q)
    )
  }
  if (filterMethod.value) list = list.filter(r => r.method === filterMethod.value)
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize)))
const paginatedList = computed(() => filteredList.value.slice((page.value - 1) * pageSize, page.value * pageSize))

function clearFilters() {
  search.value = ''
  filterMethod.value = ''
  filterStatus.value = ''
  filterDate.value = ''
  page.value = 1
}

function statusClass(status) {
  return {
    'Posted': 'bg-green-100 text-green-600',
    'Pending': 'bg-yellow-100 text-yellow-600',
    'Reversed': 'bg-red-100 text-red-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

function formatCurrency(amount) {
  return `₦${Number(amount).toLocaleString('en-NG')}`
}
</script>