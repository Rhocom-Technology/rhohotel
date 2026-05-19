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
            class="border-b border-gray-50 last:border-0 hover:bg-blue-50/40 transition-colors cursor-pointer"
            @click="openDetail(t)">
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
            <td class="px-4 py-3" @click.stop>
              <button v-if="t.status === 'Pending Approval'"
                @click="openDetail(t)"
                class="px-3 py-1.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors whitespace-nowrap">
                Review
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Approval Detail Panel -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div v-if="detailTarget" class="fixed inset-0 z-50 flex"
          style="background:rgba(15,23,42,0.55);backdrop-filter:blur(3px);"
          @click.self="closePanel">

          <Transition
            enter-active-class="transition-transform duration-300 ease-out"
            enter-from-class="translate-x-full"
            enter-to-class="translate-x-0"
            leave-active-class="transition-transform duration-200 ease-in"
            leave-from-class="translate-x-0"
            leave-to-class="translate-x-full"
          >
            <div v-if="detailTarget" class="ml-auto w-full max-w-xl bg-white h-full flex flex-col shadow-2xl overflow-hidden">

              <!-- Panel Header -->
              <div class="flex items-center justify-between px-7 py-5 border-b border-gray-100">
                <div class="flex items-center gap-3">
                  <div>
                    <h2 class="text-base font-bold text-gray-900">{{ detailLoading ? '...' : detailTarget.name }}</h2>
                    <p class="text-xs text-gray-400 mt-0.5">Bill Transfer Detail</p>
                  </div>
                  <span v-if="!detailLoading" class="px-2.5 py-1 text-xs font-semibold rounded-full"
                    :class="statusClass(detailTarget.status)">
                    {{ detailTarget.status || 'Draft' }}
                  </span>
                </div>
                <button @click="closePanel" class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Panel Body -->
              <div class="flex-1 overflow-y-auto px-7 py-6 space-y-6">

                <!-- Loading spinner -->
                <div v-if="detailLoading" class="flex items-center justify-center py-20">
                  <div class="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>

                <template v-else>

                  <!-- Parties -->
                  <div class="grid grid-cols-2 gap-4">
                    <div class="bg-blue-50 border border-blue-100 rounded-xl px-4 py-4">
                      <p class="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-1">From Guest</p>
                      <p class="text-sm font-bold text-gray-900">{{ detailTarget.from_guest || '—' }}</p>
                      <p class="text-xs text-gray-400 mt-1">Check-in: <span class="text-gray-600">{{ detailTarget.from_check_in || '—' }}</span></p>
                    </div>
                    <div class="bg-green-50 border border-green-100 rounded-xl px-4 py-4">
                      <p class="text-xs font-semibold text-green-400 uppercase tracking-wide mb-1">To Guest</p>
                      <p class="text-sm font-bold text-gray-900">{{ detailTarget.to_guest || '—' }}</p>
                      <p class="text-xs text-gray-400 mt-1">Check-in: <span class="text-gray-600">{{ detailTarget.to_check_in || '—' }}</span></p>
                    </div>
                  </div>

                  <!-- Invoice + Amount -->
                  <div class="bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 space-y-2">
                    <div class="flex justify-between items-center">
                      <span class="text-xs text-gray-500">Source Invoice</span>
                      <span class="text-xs font-semibold text-blue-600">{{ detailTarget.source_invoice || '—' }}</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-xs text-gray-500">Total Amount</span>
                      <span class="text-sm font-bold text-gray-900">{{ fmt(detailTarget.total_amount) }}</span>
                    </div>
                    <div v-if="detailTarget.journal_entry" class="flex justify-between items-center">
                      <span class="text-xs text-gray-500">Journal Entry</span>
                      <span class="text-xs font-semibold text-purple-600">{{ detailTarget.journal_entry }}</span>
                    </div>
                    <div v-if="detailTarget.authorized_by" class="flex justify-between items-center">
                      <span class="text-xs text-gray-500">Authorized By</span>
                      <span class="text-xs text-gray-700">{{ detailTarget.authorized_by }}</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-xs text-gray-500">Created</span>
                      <span class="text-xs text-gray-500">{{ fmtDate(detailTarget.creation) }}</span>
                    </div>
                  </div>

                  <!-- Reason / Notes -->
                  <div v-if="detailTarget.reason">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Reason / Notes</p>
                    <div class="bg-yellow-50 border border-yellow-100 rounded-xl px-4 py-3">
                      <p class="text-xs text-gray-700 whitespace-pre-line">{{ detailTarget.reason }}</p>
                    </div>
                  </div>

                  <!-- Line Items -->
                  <div v-if="detailTarget.items && detailTarget.items.length">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Transfer Items</p>
                    <div class="bg-white border border-gray-200 rounded-xl overflow-hidden">
                      <table class="w-full">
                        <thead>
                          <tr class="bg-gray-50 border-b border-gray-100">
                            <th class="text-left text-xs font-medium text-gray-400 px-4 py-2.5">Description</th>
                            <th class="text-left text-xs font-medium text-gray-400 px-4 py-2.5">Reference</th>
                            <th class="text-right text-xs font-medium text-gray-400 px-4 py-2.5">Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(item, idx) in detailTarget.items" :key="idx"
                            class="border-b border-gray-50 last:border-0">
                            <td class="px-4 py-2.5 text-xs text-gray-700">{{ item.description || '—' }}</td>
                            <td class="px-4 py-2.5 text-xs text-gray-400">{{ item.reference_document || '—' }}</td>
                            <td class="px-4 py-2.5 text-xs text-right font-semibold text-gray-900">{{ fmt(item.amount) }}</td>
                          </tr>
                        </tbody>
                        <tfoot>
                          <tr class="bg-gray-50 border-t border-gray-200">
                            <td colspan="2" class="px-4 py-2.5 text-xs font-semibold text-gray-500">Total</td>
                            <td class="px-4 py-2.5 text-xs text-right font-bold text-gray-900">{{ fmt(detailTarget.total_amount) }}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>

                  <!-- Error Banner -->
                  <div v-if="approvalError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                    <p class="text-xs text-red-700 whitespace-pre-line">{{ approvalError }}</p>
                  </div>

                  <!-- Rejection Reason -->
                  <div v-if="showRejectForm">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Rejection Reason</p>
                    <textarea v-model="rejectionReason" rows="3" placeholder="Enter reason for rejection..."
                      class="w-full px-3 py-2.5 text-xs border border-red-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-400 resize-none bg-red-50"></textarea>
                  </div>

                </template>
              </div>

              <!-- Panel Footer — Action Buttons -->
              <div v-if="!detailLoading && detailTarget.status === 'Pending Approval'"
                class="border-t border-gray-100 px-7 py-5 bg-white">

                <div v-if="!showRejectForm" class="flex items-center gap-3">
                  <button @click="showRejectForm = true"
                    class="flex-1 px-4 py-2.5 text-xs font-semibold text-red-600 border border-red-200 rounded-xl hover:bg-red-50 transition-colors">
                    Reject Transfer
                  </button>
                  <button @click="executeApproval" :disabled="approving"
                    class="flex-1 px-4 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-60 transition-colors">
                    {{ approving ? 'Processing...' : 'Approve & Execute' }}
                  </button>
                </div>

                <div v-else class="space-y-3">
                  <p class="text-xs text-red-600 font-medium">Confirm rejection of this transfer?</p>
                  <div class="flex items-center gap-3">
                    <button @click="showRejectForm = false; rejectionReason = ''"
                      class="flex-1 px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors">
                      Back
                    </button>
                    <button @click="executeRejection" :disabled="approving"
                      class="flex-1 px-4 py-2.5 text-xs font-semibold text-white bg-red-600 rounded-xl hover:bg-red-700 disabled:opacity-60 transition-colors">
                      {{ approving ? 'Processing...' : 'Confirm Reject' }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Read-only footer for non-pending states -->
              <div v-else-if="!detailLoading && detailTarget.status !== 'Pending Approval'"
                class="border-t border-gray-100 px-7 py-4 bg-gray-50 flex items-center justify-between">
                <p class="text-xs text-gray-400">
                  This transfer is <span class="font-semibold text-gray-600">{{ detailTarget.status }}</span> — no actions available.
                </p>
                <button @click="closePanel"
                  class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-white transition-colors">
                  Close
                </button>
              </div>

            </div>
          </Transition>
        </div>
      </Transition>
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

// Detail panel state
const detailTarget = ref(null)
const detailLoading = ref(false)
const approvalError = ref('')
const approving = ref(false)
const showRejectForm = ref(false)
const rejectionReason = ref('')

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

async function openDetail(row) {
  // Seed with list-row data immediately so the panel opens fast
  detailTarget.value = { ...row, items: [] }
  detailLoading.value = true
  approvalError.value = ''
  showRejectForm.value = false
  rejectionReason.value = ''

  try {
    const data = await apiPost(
      'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.get_bill_transfer_detail',
      { docname: row.name }
    )
    if (data.message) {
      detailTarget.value = data.message
    }
  } catch {
    // keep seeded data
  } finally {
    detailLoading.value = false
  }
}

function closePanel() {
  detailTarget.value = null
  approvalError.value = ''
  showRejectForm.value = false
  rejectionReason.value = ''
}

async function executeApproval() {
  if (!detailTarget.value) return
  approvalError.value = ''
  approving.value = true
  try {
    const data = await apiPost(
      'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.approve_and_execute_transfer',
      { docname: detailTarget.value.name }
    )
    if (data.exc) {
      approvalError.value = parseErr(data)
    } else {
      closePanel()
      await loadTransfers()
    }
  } catch {
    approvalError.value = 'Request failed. Please try again.'
  } finally {
    approving.value = false
  }
}

async function executeRejection() {
  if (!detailTarget.value) return
  approvalError.value = ''
  approving.value = true
  try {
    const data = await apiPost(
      'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.reject_transfer',
      { docname: detailTarget.value.name, rejection_reason: rejectionReason.value }
    )
    if (data.exc) {
      approvalError.value = parseErr(data)
    } else {
      closePanel()
      await loadTransfers()
    }
  } catch {
    approvalError.value = 'Request failed. Please try again.'
  } finally {
    approving.value = false
  }
}
</script>
