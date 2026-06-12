<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Payment Reconciliation</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Payment Reconciliation</h1>
      <p class="text-xs text-gray-400 mt-1">Apply guest overpayments to outstanding invoices without involving the accounts department.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Overpayment Register</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ filteredCustomers.length }} of {{ customers.length }} customer{{ customers.length === 1 ? '' : 's' }} with unallocated funds
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing')">Billing Dashboard</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing/payments')">Payment List</button>
        <button @click="loadCustomers"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5" v-if="!loadingCustomers && !customersError && customers.length > 0">
      <div class="flex items-center gap-3 flex-wrap">
        <!-- Search -->
        <div class="flex-1" style="min-width:200px;">
          <input v-model="filterSearch" type="text" placeholder="Search customer name…"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <!-- Sort -->
        <select v-model="filterSort" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="overpayment_desc">Highest Overpayment First</option>
          <option value="overpayment_asc">Lowest Overpayment First</option>
          <option value="invoices_desc">Most Open Invoices First</option>
          <option value="customer_asc">Customer A → Z</option>
          <option value="customer_desc">Customer Z → A</option>
        </select>
        <!-- Min overpayment -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 font-medium whitespace-nowrap">Min Credit</label>
          <input v-model.number="filterMinCredit" type="number" min="0" step="1000" placeholder="0"
            class="w-28 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <!-- Overdue-only toggle -->
        <button
          class="px-4 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="filterOverdueOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="filterOverdueOnly = !filterOverdueOnly">
          {{ filterOverdueOnly ? 'Overdue Only ✓' : 'Overdue Only' }}
        </button>
        <!-- Has open invoices toggle -->
        <button
          class="px-4 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="filterHasInvoices ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="filterHasInvoices = !filterHasInvoices">
          {{ filterHasInvoices ? 'Has Invoices ✓' : 'Has Open Invoices' }}
        </button>
        <!-- Reset -->
        <button @click="resetFilters"
          class="px-4 py-2.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors">Reset</button>
      </div>
      <!-- Active filter summary -->
      <div v-if="activeFilterCount > 0" class="mt-3 flex items-center gap-2">
        <span class="text-xs text-gray-400">Active filters:</span>
        <span v-if="filterSearch" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">Search: "{{ filterSearch }}"</span>
        <span v-if="filterMinCredit > 0" class="px-2 py-0.5 text-xs bg-orange-100 text-orange-600 rounded-full">Min Credit: {{ fmt(filterMinCredit) }}</span>
        <span v-if="filterOverdueOnly" class="px-2 py-0.5 text-xs bg-red-100 text-red-500 rounded-full">Overdue invoices only</span>
        <span v-if="filterHasInvoices" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">Has open invoices</span>
        <span class="text-xs text-gray-400 ml-1">· {{ filteredCustomers.length }} result{{ filteredCustomers.length === 1 ? '' : 's' }}</span>
      </div>
    </div>

    <!-- How it Works Banner -->
    <div class="bg-blue-50 border border-blue-100 rounded-xl px-6 py-4">
      <p class="text-xs font-semibold text-blue-700 mb-1">How it works</p>
      <p class="text-xs text-blue-600">When a guest pays more than their bill (e.g. ₦100k for a ₦50k invoice), the surplus sits as an <strong>unallocated payment</strong>. Use this tool to apply that surplus directly to any of their outstanding invoices — no accounts department needed.</p>
    </div>

    <!-- Loading -->
    <div v-if="loadingCustomers" class="flex items-center justify-center py-12">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-xs">Loading overpayment register…</span>
      </div>
    </div>

    <div v-else-if="customersError" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-xs text-red-600">
      {{ customersError }} <button @click="loadCustomers" class="ml-3 underline font-medium">Retry</button>
    </div>

    <!-- Empty state (no data at all) -->
    <div v-else-if="customers.length === 0" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
      <p class="text-sm font-semibold text-gray-700">All clear!</p>
      <p class="text-xs text-gray-400 mt-1">No customers currently have unallocated funds. All payments have been fully applied.</p>
    </div>

    <!-- No filter results -->
    <div v-else-if="filteredCustomers.length === 0"
      class="bg-white rounded-xl border border-gray-200 px-6 py-10 text-center">
      <p class="text-sm font-semibold text-gray-700">No matches</p>
      <p class="text-xs text-gray-400 mt-1">No customers match the current filters. <button @click="resetFilters" class="underline text-blue-500">Clear filters</button></p>
    </div>

    <!-- Customer List -->
    <template v-else>
      <div class="space-y-3">
        <div v-for="c in filteredCustomers" :key="c.customer"
          class="bg-white rounded-xl border border-gray-200 overflow-hidden">

          <!-- Customer header -->
          <div class="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
            @click="toggleCustomer(c.customer)">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span class="text-xs font-bold text-orange-600">{{ c.customer.charAt(0).toUpperCase() }}</span>
              </div>
              <div>
                <p class="text-sm font-bold text-gray-900">{{ c.customer }}</p>
                <p class="text-xs text-gray-400 mt-0.5">
                  {{ c.payment_count }} unallocated receipt{{ c.payment_count === 1 ? '' : 's' }} ·
                  {{ c.open_invoice_count }} open invoice{{ c.open_invoice_count === 1 ? '' : 's' }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <p class="text-xs text-gray-400">Available Credit</p>
                <p class="text-base font-bold text-orange-500">{{ fmt(c.total_overpayment) }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-400">Open Invoices</p>
                <p class="text-base font-bold text-gray-700">{{ fmt(c.open_invoice_total) }}</p>
              </div>
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="expanded === c.customer ? 'rotate-180' : ''"
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </div>
          </div>

          <!-- Expanded detail -->
          <div v-if="expanded === c.customer" class="border-t border-gray-100">
            <!-- Loading detail -->
            <div v-if="loadingDetail" class="px-6 py-8 text-center text-xs text-gray-400">
              <svg class="animate-spin w-4 h-4 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Loading customer detail…
            </div>

            <div v-else-if="detail" class="grid grid-cols-2 divide-x divide-gray-100">

              <!-- Left: Unallocated Payments -->
              <div class="p-5">
                <h4 class="text-xs font-bold text-gray-700 mb-3">Unallocated Receipts</h4>
                <div v-if="detail.payments.length === 0" class="text-xs text-gray-400">No unallocated receipts.</div>
                <div v-else class="space-y-2">
                  <div v-for="p in detail.payments" :key="p.name"
                    class="rounded-lg border px-4 py-3 cursor-pointer transition-all"
                    :class="selectedPayment?.name === p.name ? 'border-orange-400 bg-orange-50' : 'border-gray-200 hover:border-orange-200 hover:bg-orange-50/50'"
                    @click="selectPayment(p)">
                    <div class="flex items-center justify-between">
                      <div>
                        <p class="text-xs font-bold text-gray-900">{{ p.name }}</p>
                        <p class="text-xs text-gray-400 mt-0.5">{{ p.mode_of_payment }} · {{ p.posting_date }}<span v-if="p.reference_no"> · Ref: {{ p.reference_no }}</span></p>
                      </div>
                      <div class="text-right">
                        <p class="text-xs text-gray-400">Total paid</p>
                        <p class="text-xs font-semibold text-gray-700">{{ fmt(p.paid_amount) }}</p>
                        <p class="text-xs font-bold text-orange-500 mt-0.5">{{ fmt(p.unallocated_amount) }} available</p>
                      </div>
                    </div>
                    <div v-if="selectedPayment?.name === p.name"
                      class="mt-1.5 text-xs text-orange-600 font-medium">✓ Selected — choose an invoice to apply this credit</div>
                  </div>
                </div>
              </div>

              <!-- Right: Outstanding Invoices & Transferred Bills -->
              <div class="p-5">
                <h4 class="text-xs font-bold text-gray-700 mb-3">Outstanding Charges</h4>
                <div v-if="detail.invoices.length === 0" class="text-xs text-gray-400">No outstanding invoices or transferred bills.</div>
                <div v-else class="space-y-2">
                  <div v-for="inv in detail.invoices" :key="inv.name"
                    class="rounded-lg border px-4 py-3"
                    :class="selectedInvoice?.name === inv.name ? 'border-blue-400 bg-blue-50' : 'border-gray-200'">
                    <div class="flex items-start justify-between">
                      <div class="flex-1 min-w-0 mr-3">
                        <div class="flex items-center gap-2 mb-0.5">
                          <p class="text-xs font-bold text-gray-900">{{ inv.name }}</p>
                          <span v-if="inv.is_transfer"
                            class="px-1.5 py-0.5 text-xs font-semibold bg-purple-100 text-purple-600 rounded-full whitespace-nowrap">
                            Transferred Bill
                          </span>
                        </div>
                        <p class="text-xs text-gray-400">
                          {{ inv.posting_date }}
                          <span v-if="inv.due_date"> · Due {{ inv.due_date }}</span>
                        </p>
                        <p v-if="inv.is_transfer && inv.description"
                          class="text-xs text-purple-600 mt-0.5 truncate">{{ inv.description }}</p>
                        <p v-if="!inv.is_transfer && inv.due_date && isDue(inv.due_date)"
                          class="text-xs font-semibold text-red-500 mt-0.5">Overdue</p>
                      </div>
                      <div class="text-right flex-shrink-0">
                        <p class="text-xs text-gray-400">Total</p>
                        <p class="text-xs font-semibold text-gray-700">{{ fmt(inv.grand_total) }}</p>
                        <p class="text-xs font-bold text-gray-900 mt-0.5">{{ fmt(inv.outstanding_amount) }} outstanding</p>
                      </div>
                    </div>

                    <!-- Apply section — shown only when a payment is selected -->
                    <div v-if="selectedPayment" class="mt-3 pt-3 border-t border-gray-100">
                      <div class="flex items-center gap-2">
                        <input
                          v-model.number="applyAmounts[inv.name]"
                          type="number"
                          :max="Math.min(selectedPayment.unallocated_amount, inv.outstanding_amount)"
                          :min="0.01"
                          step="0.01"
                          placeholder="Amount to apply"
                          class="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          @click.stop
                        />
                        <button
                          @click.stop="applyMax(inv)"
                          class="px-2 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap">Max</button>
                        <button
                          @click.stop="applyPayment(inv)"
                          :disabled="!canApply(inv)"
                          class="px-3 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap"
                          :class="canApply(inv) ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'">Apply</button>
                      </div>
                      <p v-if="applyAmounts[inv.name] > 0" class="text-xs text-gray-400 mt-1.5">
                        Applying {{ fmt(applyAmounts[inv.name]) }} of {{ fmt(selectedPayment.unallocated_amount) }} available credit
                      </p>
                    </div>
                    <div v-else class="mt-2 text-xs text-gray-400 italic">← Select a receipt on the left to apply credit</div>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    </template>

    <!-- Apply confirmation modal -->
    <div v-if="applyModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-7">
        <div v-if="!applyResult">
          <h2 class="text-base font-bold text-gray-900 mb-1">Confirm Reconciliation</h2>
          <p class="text-xs text-gray-400 mb-5">This will permanently link the payment to the invoice and update the guest's ledger.</p>
          <div class="bg-gray-50 rounded-xl p-4 space-y-2 text-xs mb-5">
            <div class="flex items-center justify-between">
              <span class="text-gray-500">Receipt</span>
              <span class="font-semibold text-gray-900">{{ applyModal.payment.name }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-500">{{ applyModal.invoice.is_transfer ? 'Transferred Bill' : 'Invoice' }}</span>
              <div class="flex items-center gap-1.5">
                <span v-if="applyModal.invoice.is_transfer"
                  class="px-1.5 py-0.5 text-xs font-semibold bg-purple-100 text-purple-600 rounded-full">Transfer</span>
                <span class="font-semibold text-gray-900">{{ applyModal.invoice.name }}</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-500">Customer</span>
              <span class="font-semibold text-gray-900">{{ expanded }}</span>
            </div>
            <div class="flex items-center justify-between border-t border-gray-200 pt-2">
              <span class="text-gray-700 font-semibold">Amount to Apply</span>
              <span class="text-green-600 font-bold text-sm">{{ fmt(applyModal.amount) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button @click="applyModal = null" class="flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">Cancel</button>
            <button @click="confirmApply" :disabled="applying"
              class="flex-1 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700 transition-colors disabled:opacity-60">
              <span v-if="applying">Applying…</span>
              <span v-else>Confirm &amp; Apply</span>
            </button>
          </div>
        </div>
        <div v-else>
          <div v-if="applyResult.success" class="text-center">
            <div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <h3 class="text-base font-bold text-gray-900 mb-2">Reconciled Successfully</h3>
            <p class="text-xs text-gray-500 mb-1">{{ fmt(applyResult.applied_amount) }} applied to {{ applyResult.invoice }}</p>
            <div class="mt-3 bg-gray-50 rounded-xl p-3 text-xs space-y-1">
              <div class="flex justify-between"><span class="text-gray-500">Remaining credit on receipt</span><span class="font-semibold">{{ fmt(applyResult.pe_remaining) }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">Invoice balance remaining</span><span class="font-semibold">{{ fmt(applyResult.invoice_outstanding) }}</span></div>
            </div>
          </div>
          <div v-else class="text-center">
            <div class="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-7 h-7 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </div>
            <h3 class="text-base font-bold text-gray-900 mb-2">Reconciliation Failed</h3>
            <p class="text-xs text-red-500 mb-4">{{ applyResult.message }}</p>
          </div>
          <button @click="afterApply" class="w-full mt-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors">Done</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

// ── Formatting ────────────────────────────────────────────────────────────────
function fmt(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `₦${+(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `₦${+(n / 1_000).toFixed(1)}K`
  return `₦${n.toLocaleString()}`
}
function isDue(dateStr) {
  return dateStr && new Date(dateStr) < new Date()
}

// ── State ─────────────────────────────────────────────────────────────────────
const customers      = ref([])
const loadingCustomers = ref(false)
const customersError = ref(null)

// ── Filter state ──────────────────────────────────────────────────────────────
const filterSearch      = ref('')
const filterSort        = ref('overpayment_desc')
const filterMinCredit   = ref(0)
const filterOverdueOnly = ref(false)
const filterHasInvoices = ref(false)

const activeFilterCount = computed(() =>
  (filterSearch.value ? 1 : 0) +
  (filterMinCredit.value > 0 ? 1 : 0) +
  (filterOverdueOnly.value ? 1 : 0) +
  (filterHasInvoices.value ? 1 : 0)
)

function resetFilters() {
  filterSearch.value      = ''
  filterSort.value        = 'overpayment_desc'
  filterMinCredit.value   = 0
  filterOverdueOnly.value = false
  filterHasInvoices.value = false
}

const filteredCustomers = computed(() => {
  let list = customers.value

  // Search by customer name
  if (filterSearch.value) {
    const q = filterSearch.value.toLowerCase()
    list = list.filter(c => c.customer.toLowerCase().includes(q))
  }

  // Minimum credit amount
  if (filterMinCredit.value > 0) {
    list = list.filter(c => c.total_overpayment >= filterMinCredit.value)
  }

  // Has at least one open invoice
  if (filterHasInvoices.value) {
    list = list.filter(c => c.open_invoice_count > 0)
  }

  // Overdue only — requires open invoices where total > overpayment
  // (we approximate: any customer with open invoices and due amount > 0)
  if (filterOverdueOnly.value) {
    list = list.filter(c => c.open_invoice_count > 0 && c.open_invoice_total > 0)
  }

  // Sort
  const sorted = [...list]
  switch (filterSort.value) {
    case 'overpayment_asc':  sorted.sort((a, b) => a.total_overpayment - b.total_overpayment); break
    case 'overpayment_desc': sorted.sort((a, b) => b.total_overpayment - a.total_overpayment); break
    case 'invoices_desc':    sorted.sort((a, b) => b.open_invoice_count - a.open_invoice_count); break
    case 'customer_asc':     sorted.sort((a, b) => a.customer.localeCompare(b.customer)); break
    case 'customer_desc':    sorted.sort((a, b) => b.customer.localeCompare(a.customer)); break
  }
  return sorted
})

const expanded       = ref(null)
const detail         = ref(null)
const loadingDetail  = ref(false)

const selectedPayment = ref(null)
const applyAmounts    = reactive({})

const applyModal   = ref(null)
const applying     = ref(false)
const applyResult  = ref(null)

// ── Load customer list ────────────────────────────────────────────────────────
async function loadCustomers() {
  loadingCustomers.value = true
  customersError.value   = null
  try {
    customers.value = await callMethod(
      'rhohotel.rhocom_hotel.api.billing_reconcile.get_customers_with_overpayments'
    )
  } catch (err) {
    customersError.value = err.message || 'Failed to load overpayment register.'
  } finally {
    loadingCustomers.value = false
  }
}

// ── Toggle / expand customer ──────────────────────────────────────────────────
async function toggleCustomer(customer) {
  if (expanded.value === customer) {
    expanded.value  = null
    detail.value    = null
    selectedPayment.value = null
    return
  }
  expanded.value  = customer
  detail.value    = null
  selectedPayment.value = null
  loadingDetail.value = true
  try {
    detail.value = await callMethod(
      'rhohotel.rhocom_hotel.api.billing_reconcile.get_customer_overpayment_detail',
      { customer }
    )
  } catch (err) {
    detail.value = { payments: [], invoices: [], error: err.message }
  } finally {
    loadingDetail.value = false
  }
}

// ── Payment selection ─────────────────────────────────────────────────────────
function selectPayment(p) {
  selectedPayment.value = (selectedPayment.value?.name === p.name) ? null : p
  // Reset all apply amounts when switching selection
  Object.keys(applyAmounts).forEach(k => delete applyAmounts[k])
}

function applyMax(inv) {
  if (!selectedPayment.value) return
  applyAmounts[inv.name] = Math.min(
    selectedPayment.value.unallocated_amount,
    inv.outstanding_amount
  )
}

function canApply(inv) {
  const amt = Number(applyAmounts[inv.name])
  if (!selectedPayment.value || !amt || amt <= 0) return false
  if (amt > selectedPayment.value.unallocated_amount + 0.001) return false
  if (amt > inv.outstanding_amount + 0.001) return false
  return true
}

// ── Apply payment (open confirmation modal) ───────────────────────────────────
function applyPayment(inv) {
  if (!canApply(inv)) return
  applyResult.value = null
  applyModal.value  = {
    payment: selectedPayment.value,
    invoice: inv,
    amount:  Number(applyAmounts[inv.name]),
  }
}

// ── Confirm and execute reconciliation ───────────────────────────────────────
async function confirmApply() {
  if (!applyModal.value) return
  applying.value = true
  try {
    const res = await callMethod(
      'rhohotel.rhocom_hotel.api.billing_reconcile.apply_overpayment_to_invoice',
      {
        payment_entry: applyModal.value.payment.name,
        invoice_name:  applyModal.value.invoice.name,
        amount:        applyModal.value.amount,
      }
    )
    applyResult.value = res
  } catch (err) {
    applyResult.value = { success: false, message: err.message || 'Reconciliation failed.' }
  } finally {
    applying.value = false
  }
}

// ── After apply: refresh data ─────────────────────────────────────────────────
async function afterApply() {
  const wasExpanded = expanded.value
  applyModal.value  = null
  applyResult.value = null
  selectedPayment.value = null
  Object.keys(applyAmounts).forEach(k => delete applyAmounts[k])

  await loadCustomers()
  // Re-open customer panel if they still have payments
  if (wasExpanded && customers.value.find(c => c.customer === wasExpanded)) {
    await toggleCustomer(wasExpanded)
  } else {
    expanded.value = null
    detail.value   = null
  }
}

onMounted(loadCustomers)
</script>
