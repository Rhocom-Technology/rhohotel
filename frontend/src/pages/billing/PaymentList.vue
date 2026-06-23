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
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Payment Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ payments.length }} total receipts • {{ unallocatedCount }} unallocated • {{ allocatedCount }} fully allocated</p>
      </div>
      <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
        <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
          @click="$router.push('/billing')">Billing Dashboard</button>
        <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
          @click="$router.push('/billing/invoices')">Invoice List</button>
        <button @click="openRecordPaymentModal"
          class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors sm:w-auto">Record Payment</button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Received Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ fmtAmount(stats.received_today) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Received This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Month</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ fmtAmount(stats.received_month) }}</p>
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
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div class="w-full sm:min-w-[180px] sm:flex-1">
          <input v-model="search" type="text" placeholder="Search receipt no., guest, reference..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <!-- Date range -->
        <div class="flex w-full items-center gap-1.5 sm:w-auto">
          <label class="text-xs text-gray-500 font-medium">From</label>
          <input v-model="fromDate" type="date"
            class="min-w-0 flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700 sm:flex-none" />
        </div>
          <div class="flex w-full items-center gap-1.5 sm:w-auto">
          <label class="text-xs text-gray-500 font-medium">To</label>
          <input v-model="toDate" type="date"
            class="min-w-0 flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700 sm:flex-none" />
        </div>
          <select v-model="filterMethod" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Methods</option>
          <option>Cash</option>
          <option>Bank Transfer</option>
          <option>POS</option>
          <option>Cheque</option>
        </select>
        <select v-model="filterStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Statuses</option>
          <option>Allocated</option>
          <option>Part Allocated</option>
          <option>Unallocated</option>
        </select>
        <button @click="resetFilters"
          class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">Reset</button>
        <button
          class="w-full px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors sm:w-auto"
          :class="showUnallocatedOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showUnallocatedOnly = !showUnallocatedOnly; currentPage = 1">
          {{ showUnallocatedOnly ? 'Show All' : 'Unallocated Only' }}
        </button>
      </div>
      <!-- Active date range indicator -->
      <div v-if="fromDate || toDate" class="mt-3 flex items-center gap-2">
        <span class="text-xs text-gray-400">Date range:</span>
        <span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
          {{ fromDate ? fmtDate(fromDate) : 'Any' }} → {{ toDate ? fmtDate(toDate) : 'Any' }}
        </span>
        <span class="text-xs text-gray-400">· {{ filtered.length }} result{{ filtered.length === 1 ? '' : 's' }}</span>
      </div>
    </div>

    <!-- Payment Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-4 py-4 border-b border-gray-100 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h3 class="text-sm font-bold text-gray-900">Payment Records</h3>
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} payments</p>
      </div>
      <div class="overflow-x-auto">
      <table class="w-full min-w-[980px]">
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
          <tr v-if="loading">
            <td colspan="9" class="px-6 py-8 text-center text-xs text-gray-400">Loading payment records...</td>
          </tr>
          <tr v-else-if="error">
            <td colspan="9" class="px-6 py-8 text-center text-xs text-red-500">{{ error }} <button @click="load" class="ml-2 underline font-semibold">Retry</button></td>
          </tr>
          <tr v-else-if="paged.length === 0">
            <td colspan="9" class="px-6 py-8 text-center text-xs text-gray-400">No payment records found.</td>
          </tr>
          <tr v-for="p in paged" v-else :key="p.receiptNo"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ p.receiptNo }}</td>
            <td class="px-4 py-4">
              <p class="text-xs font-bold text-gray-900">{{ p.payer }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ p.payerNote }}</p>
            </td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="methodClass(p.method)">{{ p.method }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-500 font-mono">{{ p.reference || '-' }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ fmtDate(p.date) }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ fmtAmount(p.amount) }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ fmtAmount(p.allocated) }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="paymentStatusClass(p.status)">{{ p.status }}</span>
            </td>
            <td class="px-4 py-4">
              <div class="flex items-center gap-1.5">
                <button @click="openPaymentDetail(p)"
                  class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  View
                </button>
                <button v-if="p.status !== 'Allocated'"
                  @click="$router.push('/billing/reconcile')"
                  class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                  Allocate
                </button>
                <button v-if="p.status === 'Allocated'"
                  @click="printPayment(p)"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  Print
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <div class="px-4 py-4 border-t border-gray-100 flex flex-col gap-3 bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex flex-wrap items-center gap-1">
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

  <!-- Payment Detail Modal -->
  <Teleport to="body">
    <div v-if="showDetailModal" class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="closeDetailModal">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:680px;max-height:92vh;">
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">{{ detailPayment?.name || 'Payment Entry' }}</h2>
            <p class="text-xs text-gray-400 mt-1">{{ detailPayment?.party_name || detailPayment?.party || 'Customer receipt' }}</p>
          </div>
          <button @click="closeDetailModal"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">
          <div v-if="detailLoading" class="py-10 text-center text-xs text-gray-400">Loading payment details...</div>
          <div v-else-if="detailError" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-600">{{ detailError }}</div>
          <template v-else-if="detailPayment">
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <p class="text-xs text-gray-400 mb-1">Date</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtDate(detailPayment.posting_date) }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Mode</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ detailPayment.mode_of_payment || '-' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Reference</p>
                <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg truncate">{{ detailPayment.reference_no || '-' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Paid Amount</p>
                <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtAmount(detailPayment.paid_amount) }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Allocated</p>
                <div class="px-3 py-2.5 text-xs font-bold text-green-600 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtAmount(detailAllocatedAmount) }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Unallocated</p>
                <div class="px-3 py-2.5 text-xs font-bold text-red-500 bg-gray-50 border border-gray-200 rounded-lg">{{ fmtAmount(detailPayment.unallocated_amount) }}</div>
              </div>
            </div>

            <div>
              <h3 class="text-sm font-bold text-gray-900 mb-3">Allocations</h3>
              <div class="rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full min-w-[520px]">
                  <thead>
                    <tr class="bg-gray-50 border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Reference</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Type</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Allocated</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!detailPayment.references?.length">
                      <td colspan="3" class="px-4 py-8 text-center text-xs text-gray-400">No allocations recorded.</td>
                    </tr>
                    <tr v-for="ref in detailPayment.references" :key="ref.reference_doctype + ref.reference_name" class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3 text-xs font-semibold text-gray-900">{{ ref.reference_name }}</td>
                      <td class="px-4 py-3 text-xs text-gray-500">{{ ref.reference_doctype }}</td>
                      <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">{{ fmtAmount(ref.allocated_amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="detailPayment.remarks">
              <p class="text-xs text-gray-400 mb-1.5">Remarks</p>
              <div class="px-4 py-3 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-xl">{{ detailPayment.remarks }}</div>
            </div>
          </template>

          <div class="flex items-center justify-end gap-2">
            <button v-if="detailPayment" @click="printPayment({ receiptNo: detailPayment.name })"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Print</button>
            <button @click="closeDetailModal"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Close</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Record Payment Modal -->
  <Teleport to="body">
    <div v-if="showRecordModal" class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="closeRecordPaymentModal">
      <div class="bg-white rounded-2xl w-full shadow-2xl" style="max-width:560px;">
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Record Payment</h2>
            <p class="text-xs text-gray-400 mt-1">Create a customer receipt and allocate it later if needed.</p>
          </div>
          <button @click="closeRecordPaymentModal"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">✕</button>
        </div>

        <div class="px-8 py-6 space-y-4">
          <div v-if="recordError" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-600">{{ recordError }}</div>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <p class="text-xs text-gray-500 mb-1.5">Customer <span class="text-red-400">*</span></p>
              <select v-model="recordForm.customer"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select customer</option>
                <option v-for="c in customers" :key="c.name" :value="c.name">{{ c.customer_name || c.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Mode of Payment <span class="text-red-400">*</span></p>
              <select v-model="recordForm.mode_of_payment"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select mode</option>
                <option v-for="m in paymentModes" :key="m.name" :value="m.name">{{ m.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Amount Received <span class="text-red-400">*</span></p>
              <input type="number" v-model.number="recordForm.paid_amount" min="0.01" step="0.01"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
              <input type="date" v-model="recordForm.payment_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference No</p>
              <input type="text" v-model="recordForm.reference_no" placeholder="Bank / terminal reference"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference Date</p>
              <input type="date" v-model="recordForm.reference_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Remarks</p>
              <input type="text" v-model="recordForm.remarks" placeholder="Optional note"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button @click="closeRecordPaymentModal"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
            <button
              :disabled="recordSubmitting || !recordForm.customer || !recordForm.mode_of_payment || !(recordForm.paid_amount > 0)"
              @click="submitRecordPayment"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ recordSubmitting ? 'Processing…' : 'Confirm Payment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const search = ref('')
const fromDate = ref('')
const toDate = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const showUnallocatedOnly = ref(false)
const currentPage = ref(1)
const perPage = 25
const payments = ref([])
const stats = ref({ received_today: 0, received_month: 0 })
const loading = ref(false)
const error = ref(null)
const showDetailModal = ref(false)
const detailPayment = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const showRecordModal = ref(false)
const customers = ref([])
const paymentModes = ref([])
const recordSubmitting = ref(false)
const recordError = ref('')
const today = new Date().toISOString().slice(0, 10)
const recordForm = reactive({
  customer: '',
  mode_of_payment: '',
  paid_amount: 0,
  payment_date: today,
  reference_no: '',
  reference_date: '',
  remarks: '',
})

function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function fmtAmount(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `₦${+(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `₦${+(n / 1_000).toFixed(1)}K`
  return `₦${n.toLocaleString()}`
}

function resetFilters() {
  search.value = ''
  fromDate.value = ''
  toDate.value = ''
  filterMethod.value = ''
  filterStatus.value = ''
  showUnallocatedOnly.value = false
  currentPage.value = 1
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.get_payment_register', {
      from_date: fromDate.value,
      to_date: toDate.value,
    })
    payments.value = data?.payments || []
    stats.value = data?.stats || { received_today: 0, received_month: 0 }
    currentPage.value = 1
  } catch (err) {
    error.value = err.message || 'Failed to load payment records.'
  } finally {
    loading.value = false
  }
}

async function loadPaymentModes() {
  try {
    paymentModes.value = await callMethod('rhohotel.rhocom_hotel.api.corporate_billing.get_payment_modes') || []
  } catch {
    paymentModes.value = []
  }
}

async function loadCustomers() {
  try {
    customers.value = await callMethod('frappe.client.get_list', {
      doctype: 'Customer',
      fields: ['name', 'customer_name'],
      filters: { disabled: 0 },
      order_by: 'customer_name asc',
      limit_page_length: 500,
    }) || []
  } catch {
    customers.value = []
  }
}

async function openPaymentDetail(payment) {
  showDetailModal.value = true
  detailPayment.value = null
  detailError.value = ''
  detailLoading.value = true
  try {
    detailPayment.value = await callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.get_payment_entry_detail', {
      payment_entry: payment.receiptNo,
    })
  } catch (err) {
    detailError.value = err.message || 'Failed to load payment details.'
  } finally {
    detailLoading.value = false
  }
}

function closeDetailModal() {
  showDetailModal.value = false
  detailPayment.value = null
  detailError.value = ''
}

function resetRecordForm() {
  recordForm.customer = ''
  recordForm.mode_of_payment = ''
  recordForm.paid_amount = 0
  recordForm.payment_date = today
  recordForm.reference_no = ''
  recordForm.reference_date = ''
  recordForm.remarks = ''
}

function openRecordPaymentModal() {
  resetRecordForm()
  recordError.value = ''
  showRecordModal.value = true
  if (!customers.value.length) loadCustomers()
  if (!paymentModes.value.length) loadPaymentModes()
}

function closeRecordPaymentModal() {
  showRecordModal.value = false
  recordError.value = ''
}

async function submitRecordPayment() {
  if (!recordForm.customer || !recordForm.mode_of_payment || !(recordForm.paid_amount > 0)) return
  recordSubmitting.value = true
  recordError.value = ''
  try {
    await callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.record_customer_payment', {
      customer: recordForm.customer,
      mode_of_payment: recordForm.mode_of_payment,
      paid_amount: recordForm.paid_amount,
      payment_date: recordForm.payment_date,
      reference_no: recordForm.reference_no,
      reference_date: recordForm.reference_date,
      remarks: recordForm.remarks,
    })
    closeRecordPaymentModal()
    await load()
  } catch (err) {
    recordError.value = err.message || 'Failed to record payment.'
  } finally {
    recordSubmitting.value = false
  }
}

function printPayment(payment) {
  if (!payment?.receiptNo) return
  const params = new URLSearchParams({ doctype: 'Payment Entry', name: payment.receiptNo, trigger_print: 1 })
  window.open(`/printview?${params.toString()}`, '_blank', 'noopener')
}

const unallocatedCount = computed(() => payments.value.filter(p => p.status === 'Unallocated').length)
const allocatedCount = computed(() => payments.value.filter(p => p.status === 'Allocated').length)

const filtered = computed(() => {
  let list = payments.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(p =>
      String(p.receiptNo || '').toLowerCase().includes(q) ||
      String(p.payer || '').toLowerCase().includes(q) ||
      String(p.reference || '').toLowerCase().includes(q)
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
const detailAllocatedAmount = computed(() =>
  (detailPayment.value?.references || []).reduce((sum, row) => sum + (Number(row.allocated_amount) || 0), 0)
)

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

let debounceTimer = null
watch([fromDate, toDate], () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 250)
})
watch([search, filterMethod, filterStatus, showUnallocatedOnly], () => { currentPage.value = 1 })
onMounted(() => {
  load()
  loadPaymentModes()
})
</script>
