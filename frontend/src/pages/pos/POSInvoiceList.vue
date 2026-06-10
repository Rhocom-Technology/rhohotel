<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Review POS invoices across outlets, monitor payment method usage, and trace posted room charges, drafts, and settlement records.</p>
    </div>

    <!-- Invoice Overview -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Invoice Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">1,284 invoices this month • 3 outlets • invoices from restaurant, bar, mini-mart, and room-posting transactions</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="refreshInvoices" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Invoices</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Create POS Invoice</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Invoices Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : invoiceStats.todayCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Invoice Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦{{ statsResource.loading ? '…' : Number(invoiceStats.todayValue).toLocaleString() }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Room-Posted Invoices</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Track</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : invoiceStats.roomPosted }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Voided / Cancelled</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsResource.loading ? '…' : invoiceStats.voided }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-4 flex-wrap">
        <div style="flex:2;min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Search invoice</p>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            <input v-model="search" type="text" placeholder="Invoice no., guest, cashier, room..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Outlet</p>
          <select v-model="filterOutlet" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Outlets</option>
            <option>Restaurant</option>
            <option>Bar Lounge</option>
            <option>Retail Corner</option>
            <option>Room Service</option>
          </select>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Method</p>
          <select v-model="filterMethod" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Methods</option>
            <option>Cash</option>
            <option>POS</option>
            <option>Post to Room</option>
            <option>Split</option>
            <option>Transfer</option>
          </select>
        </div>
        <div style="flex:1;min-width:130px;">
          <p class="text-xs text-gray-500 mb-1.5">Invoice Status</p>
          <select v-model="filterStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option>Draft</option>
            <option>Paid</option>
            <option>Void</option>
          </select>
        </div>
        <button @click="resetFilters" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button @click="applyFilters" class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply Filter</button>
      </div>
    </div>

    <!-- Invoice Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Invoice Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} invoices</p>
      </div>
      <p v-if="actionSuccess" class="mx-6 mt-4 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">{{ actionSuccess }}</p>
      <p v-if="actionError" class="mx-6 mt-4 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{{ actionError }}</p>

      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date / Time</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outlet</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Customer / Target</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Method</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paged.length === 0">
            <td colspan="9" class="text-center py-12 text-xs text-gray-400">No invoices match your filters</td>
          </tr>
          <tr v-for="inv in paged" :key="inv.id"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors cursor-pointer">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ inv.no }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.datetime }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.outlet }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.cashier }}</td>
            <td class="px-4 py-4 text-xs text-gray-700">{{ inv.customer }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ inv.method }}</td>
            <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ inv.amount.toLocaleString() }}</td>
            <td class="px-4 py-4">
              <span class="px-3 py-1 text-xs font-semibold rounded-full"
                :class="statusClass(inv.status)">
                {{ inv.status }}
              </span>
            </td>
            <td class="px-4 py-4">
              <button v-if="inv.docstatus === 1" @click.stop="cancelInvoice(inv)" :disabled="cancelling === inv.no"
                class="px-3 py-1.5 text-xs font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed">
                {{ cancelling === inv.no ? 'Cancelling…' : 'Cancel' }}
              </button>
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: {{ perPage }}</p>
        <div class="flex items-center gap-1">
          <button v-for="p in visiblePages" :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="p === currentPage
              ? 'bg-blue-600 text-white font-semibold'
              : p === '...'
                ? 'text-gray-400 cursor-default'
                : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages && currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed ml-1 transition-colors">
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const search = ref('')
const filterOutlet = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const cancelling = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const perPage = 10

function resetFilters() {
  search.value = ''
  filterOutlet.value = ''
  filterMethod.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  invoicesResource.params = {}
  invoicesResource.reload()
}

// ── API: Invoice List ───────────────────────────────────────────────
const invoicesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_invoices',
  auto: true,
})

const statsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_invoice_stats',
  auto: true,
})

const cancelResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.cancel_pos_invoice',
  onSuccess(data) {
    cancelling.value = ''
    actionError.value = ''
    actionSuccess.value = `Invoice ${data?.invoice || ''} cancelled successfully.`
    refreshInvoices()
    statsResource.reload()
    setTimeout(() => { actionSuccess.value = '' }, 4000)
  },
  onError(err) {
    cancelling.value = ''
    actionError.value = extractApiErrorMessage(err, 'Failed to cancel invoice')
    setTimeout(() => { actionError.value = '' }, 6000)
  },
})

const invoiceStats = computed(() => {
  const s = statsResource.data || {}
  return {
    todayCount: Number(s.today_count || 0),
    todayValue: Number(s.today_value || 0),
    roomPosted: Number(s.room_posted || 0),
    voided: Number(s.voided || 0),
  }
})

let filterTimer = null
function applyFilters() {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    refreshInvoices()
    currentPage.value = 1
  }, 300)
}

// ── Computed: invoices ──────────────────────────────────────────────
const allInvoices = computed(() =>
  (invoicesResource.data || []).map(inv => ({
    id: inv.invoice_no,
    no: inv.invoice_no,
    datetime: inv.posting_date || '—',
    outlet: inv.terminal || '—',
    cashier: inv.cashier || '—',
    customer: inv.customer || 'Walk In',
    method: inv.payment_method || '—',
    amount: Number(inv.grand_total) || 0,
    docstatus: Number(inv.docstatus),
    invoiceStatus: inv.invoice_status || '',
    status: inv.status || '—',
  }))
)

const filtered = computed(() => {
  let data = allInvoices.value
  if (search.value) {
    const q = search.value.toLowerCase()
    data = data.filter(i =>
      i.no.toLowerCase().includes(q) ||
      i.cashier.toLowerCase().includes(q) ||
      i.customer.toLowerCase().includes(q)
    )
  }
  if (filterStatus.value) data = data.filter(i => i.status === filterStatus.value)
  if (filterMethod.value) data = data.filter(i => i.method === filterMethod.value)
  return data
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart = computed(() => (currentPage.value - 1) * perPage)
const pageEnd = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(filtered, () => { currentPage.value = 1 })

// ── Helpers ────────────────────────────────────────────────────────
function statusClass(status) {
  return {
    'Draft':        'bg-gray-100 text-gray-500',
    'Paid':         'bg-green-50 text-green-600',
    'Void':         'bg-red-50 text-red-500',
    'Consolidated': 'bg-purple-50 text-purple-600',
    'Return':       'bg-orange-50 text-orange-600',
  }[status] || 'bg-blue-50 text-blue-600'
}

function refreshInvoices() {
  invoicesResource.params = {
    search: search.value || null,
    status: filterStatus.value || null,
    method: filterMethod.value || null,
  }
  invoicesResource.reload()
}

function cancelInvoice(inv) {
  if (!inv || cancelling.value) return
  const reason = window.prompt(`Cancel POS invoice ${inv.no}?\nReason (optional):`, '')
  if (reason === null) return
  cancelling.value = inv.no
  actionError.value = ''
  cancelResource.submit({ invoice_name: inv.no, reason: reason || null })
}

function extractApiErrorMessage(err, fallback = 'Request failed') {
  const serverMessage = err?._server_messages
  if (serverMessage) {
    try {
      const parsed = JSON.parse(serverMessage)
      if (Array.isArray(parsed) && parsed.length > 0) {
        const first = JSON.parse(parsed[0])
        if (first?.message) return String(first.message)
      }
    } catch (_) {}
  }
  return err?.message || fallback
}
</script>

