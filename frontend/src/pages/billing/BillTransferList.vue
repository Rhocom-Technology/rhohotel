<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Bill Transfers</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Bill Transfer List</h1>
      <p class="text-xs text-gray-400 mt-1">All bill transfers between guest folios and corporate billing profiles — track status, approve pending transfers, and review journal entries.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Transfer Register</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ transfers.length }} records •
            {{ pendingCount }} pending approval •
            {{ completedCount }} completed
          </p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <input v-model="search" @input="debouncedLoad" type="text"
            placeholder="Search by guest, invoice, ref..."
            class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-52" />
          <select v-model="filterStatus" @change="loadTransfers"
            class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">All Statuses</option>
            <option>Draft</option>
            <option>Pending Approval</option>
            <option>Approved</option>
            <option>Cancelled</option>
          </select>
          <input v-model="filterFromDate" @change="loadTransfers" type="date"
            class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none" />
          <input v-model="filterToDate" @change="loadTransfers" type="date"
            class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none" />
          <button @click="loadTransfers"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Transfers</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ transfers.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Approval</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Action</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ pendingCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Completed</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Done</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ completedCount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Amount Transferred</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">₦</span>
        </div>
        <p class="text-xl font-bold text-gray-900">{{ fmt(totalTransferred) }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Ref</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">From Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">To Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Source Invoice</th>
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Reason</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Journal Entry</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Approved By</th>
            <th class="px-4 py-3 w-8"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="11" class="py-12 text-center">
              <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            </td>
          </tr>
          <tr v-else-if="transfers.length === 0">
            <td colspan="11" class="py-16 text-center text-xs text-gray-400">No bill transfers found</td>
          </tr>
          <tr v-for="t in transfers" :key="t.name"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-5 py-3 text-xs font-medium text-blue-600">{{ t.name }}</td>
            <td class="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{{ fmtDate(t.creation) }}</td>
            <td class="px-4 py-3 text-xs text-gray-700">{{ t.from_guest || '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-700">{{ t.to_guest || '—' }}</td>
            <td class="px-4 py-3 text-xs text-blue-600">{{ t.source_invoice || '—' }}</td>
            <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">{{ fmt(t.total_amount) }}</td>
            <td class="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{{ t.reason || '—' }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="statusClass(t.status)">
                {{ t.status || 'Draft' }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ t.journal_entry || '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ t.authorized_by || '—' }}</td>
            <td class="px-4 py-3">
              <button v-if="t.status === 'Pending Approval'"
                @click="openApproval(t)"
                class="px-3 py-1.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors whitespace-nowrap">
                Approve
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Approval Confirmation Modal -->
    <Teleport to="body">
      <div v-if="approvalTarget" class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md px-8 py-7 space-y-4">
          <h2 class="text-lg font-bold text-gray-900">Approve Bill Transfer</h2>

          <div class="bg-gray-50 border border-gray-200 rounded-xl px-4 py-4 space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-gray-500">Transfer Ref</span>
              <span class="font-semibold text-gray-900">{{ approvalTarget.name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">From Guest</span>
              <span class="text-gray-700">{{ approvalTarget.from_guest }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">To Guest</span>
              <span class="text-gray-700">{{ approvalTarget.to_guest }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Source Invoice</span>
              <span class="text-blue-600">{{ approvalTarget.source_invoice }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Amount</span>
              <span class="font-bold text-gray-900">{{ fmt(approvalTarget.total_amount) }}</span>
            </div>
          </div>

          <div v-if="approvalError" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-700 whitespace-pre-line">{{ approvalError }}</p>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button @click="approvalTarget = null; approvalError = ''"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button @click="executeApproval" :disabled="approving"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-60">
              {{ approving ? 'Processing...' : 'Confirm Approve & Execute' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const transfers = ref([])
const loading = ref(true)
const search = ref('')
const filterStatus = ref('')
const filterFromDate = ref('')
const filterToDate = ref('')
const approvalTarget = ref(null)
const approvalError = ref('')
const approving = ref(false)
let searchTimer = null

async function apiPost(method, params = {}) {
  const res = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body: new URLSearchParams(params),
  })
  return res.json()
}

function parseErr(data) {
  try {
    const msgs = JSON.parse(data._server_messages || '[]')
    if (msgs.length) return JSON.parse(msgs[0]).message
  } catch {}
  return data.exception || 'Request failed. Please try again.'
}

async function loadTransfers() {
  loading.value = true
  try {
    const data = await apiPost(
      'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.get_bill_transfers',
      {
        status: filterStatus.value,
        from_date: filterFromDate.value,
        to_date: filterToDate.value,
        search: search.value,
      }
    )
    transfers.value = data.message || []
  } catch {
    transfers.value = []
  } finally {
    loading.value = false
  }
}

function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadTransfers, 300)
}

onMounted(loadTransfers)

const pendingCount = computed(() =>
  transfers.value.filter(t => t.status === 'Pending Approval').length
)
const completedCount = computed(() =>
  transfers.value.filter(t => t.status === 'Approved').length
)
const totalTransferred = computed(() =>
  transfers.value
    .filter(t => t.status === 'Approved')
    .reduce((sum, t) => sum + (t.total_amount || 0), 0)
)

function fmt(v) {
  return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00'
}

function fmtDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function statusClass(status) {
  switch (status) {
    case 'Pending Approval': return 'bg-yellow-100 text-yellow-700'
    case 'Approved': return 'bg-green-100 text-green-700'
    case 'Cancelled': return 'bg-red-100 text-red-500'
    default: return 'bg-gray-100 text-gray-500'
  }
}

function openApproval(t) {
  approvalTarget.value = t
  approvalError.value = ''
}

async function executeApproval() {
  if (!approvalTarget.value) return
  approvalError.value = ''
  approving.value = true
  try {
    const data = await apiPost(
      'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.approve_and_execute_transfer',
      { docname: approvalTarget.value.name }
    )
    if (data.exc) {
      approvalError.value = parseErr(data)
    } else {
      approvalTarget.value = null
      await loadTransfers()
    }
  } catch {
    approvalError.value = 'Request failed. Please try again.'
  } finally {
    approving.value = false
  }
}
</script>
