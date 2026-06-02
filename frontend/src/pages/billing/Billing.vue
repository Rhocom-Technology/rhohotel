<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Dashboard</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Billing Dashboard</h1>
      <p class="text-xs text-gray-400 mt-1">Manage billing across individual guests and corporate clients with quick access to invoices, payments, folios, statements, and follow-up actions.</p>
    </div>

    <!-- Billing Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-1">Billing Control Center</h3>
      <p class="text-xs text-gray-400 mb-4">Central workspace for guest billing, corporate accounts, group master folios, invoices, receipts, settlements, and aging review.</p>

      <div class="flex items-center justify-between">
        <!-- Date range filter -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 font-medium">From</label>
          <input v-model="fromDate" type="date"
            class="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <label class="text-xs text-gray-500 font-medium">To</label>
          <input v-model="toDate" type="date"
            class="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button @click="resetDates"
            class="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors">Reset</button>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="$router.push('/billing/payments')">Payment List</button>
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="$router.push('/billing/invoices')">Invoice List</button>
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="$router.push('/billing/corporate')">Corporate Billing</button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
            New Invoice
          </button>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-xs">Loading billing data…</span>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-xs text-red-600">
      {{ error }}
      <button @click="load" class="ml-3 underline font-medium">Retry</button>
    </div>

    <template v-else>

  <!-- Stats Cards -->
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">

  <!-- Total Invoiced -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Total Invoiced</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.total_invoiced) }}</p>
    <p class="text-xs text-gray-400 mt-2">All submitted invoices</p>
  </div>

  <!-- Total Paid -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Total Paid</p>
    <p class="text-3xl font-bold text-green-600">{{ formatNaira(stats.total_paid) }}</p>
    <p class="text-xs text-gray-400 mt-2">From invoice payment allocation</p>
  </div>

  <!-- Total Receivables -->
  <div class="bg-blue-600 rounded-xl px-5 py-4">
    <p class="text-xs text-blue-200 mb-3">Total Receivables</p>
    <p class="text-3xl font-bold text-white">{{ formatNaira(stats.total_receivables) }}</p>
    <p class="text-xs text-blue-200 mt-2">Still owed</p>
  </div>

  <!-- Invoices in Period -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Invoices in Period</p>
    <p class="text-3xl font-bold text-gray-900">{{ stats.invoices_in_range }}</p>
    <p class="text-xs text-gray-400 mt-2">Within selected date range</p>
  </div>

  <!-- Individual Invoiced -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Individual Invoiced</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.individual_invoiced) }}</p>
    <p class="text-xs text-gray-400 mt-2">Guest invoice total</p>
  </div>

  <!-- Individual Paid -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Individual Paid</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.individual_paid) }}</p>
    <p class="text-xs text-gray-400 mt-2">Guest collections</p>
  </div>

  <!-- Individual Receivable -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Individual Receivable</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.individual_guest_balance) }}</p>
    <p class="text-xs text-gray-400 mt-2">
      {{ pctOf(stats.individual_guest_balance, stats.total_receivables) }}% of receivables
    </p>
  </div>

  <!-- Unallocated Payments -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Unallocated Payments</p>
    <p class="text-3xl font-bold text-gray-900">{{ stats.unallocated_payments }}</p>
    <p class="text-xs text-gray-400 mt-2">Receipts pending allocation</p>
  </div>

  <!-- Corporate Invoiced -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Corporate Invoiced</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.corporate_invoiced) }}</p>
    <p class="text-xs text-gray-400 mt-2">Corporate invoice total</p>
  </div>

  <!-- Corporate Paid -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Corporate Paid</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.corporate_paid) }}</p>
    <p class="text-xs text-gray-400 mt-2">Corporate collections</p>
  </div>

  <!-- Corporate Receivable -->
  <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
    <p class="text-xs text-gray-400 mb-3">Corporate Receivable</p>
    <p class="text-3xl font-bold text-gray-900">{{ formatNaira(stats.corporate_balance) }}</p>
    <p class="text-xs text-gray-400 mt-2">
      {{ pctOf(stats.corporate_balance, stats.total_receivables) }}% of receivables
    </p>
  </div>

</div>

      <!-- Activity Feed + Insights -->
      <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

        <!-- Billing Activity Feed -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-sm font-bold text-gray-900">Billing Activity Feed</h3>
            <span class="text-xs text-gray-400">{{ activityFeed.length }} events</span>
          </div>

          <div v-if="activityFeed.length === 0" class="px-6 py-8 text-center text-xs text-gray-400">
            No billing activity found for the selected period.
          </div>

          <div v-else class="divide-y divide-gray-50">
            <div v-for="a in pagedFeed" :key="a.id"
              class="px-6 py-4 flex items-center justify-between">
              <div>
                <p class="text-xs font-semibold text-gray-900 mb-0.5">{{ a.title }}</p>
                <p class="text-xs text-gray-400">{{ a.desc }}</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full flex-shrink-0 ml-4"
                :class="feedStatusClass(a.status)">{{ a.status }}</span>
            </div>
          </div>

          <!-- Pagination -->
          <div v-if="feedTotalPages > 1"
            class="px-6 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
            <p class="text-xs text-gray-400">
              {{ feedPageStart + 1 }}–{{ feedPageEnd }} of {{ activityFeed.length }} events
            </p>
            <div class="flex items-center gap-1">
              <button @click="feedPage > 1 ? feedPage-- : null"
                :disabled="feedPage === 1"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
                :class="feedPage === 1 ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">
                Prev
              </button>
              <button v-for="p in feedTotalPages" :key="p" @click="feedPage = p"
                class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                :class="feedPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
                {{ p }}
              </button>
              <button @click="feedPage < feedTotalPages ? feedPage++ : null"
                :disabled="feedPage === feedTotalPages"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
                :class="feedPage === feedTotalPages ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">
                Next
              </button>
            </div>
          </div>
        </div>

        <!-- Billing Insights -->
        <div class="space-y-3">
          <h3 class="text-sm font-bold text-gray-900">Billing Insights</h3>

          <!-- Corporate Aging — visual bars -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <div class="flex items-center justify-between mb-3">
              <p class="text-xs font-bold text-gray-900">Corporate Aging</p>
              <p class="text-xs text-gray-400">{{ formatNaira(insights.corporate_aging.total) }} total</p>
            </div>

            <div class="space-y-2.5">
              <!-- Current -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-500">Current</span>
                  <span class="text-xs font-semibold text-gray-700">{{ formatNaira(insights.corporate_aging.current) }}</span>
                </div>
                <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-green-400 rounded-full transition-all duration-500"
                    :style="{ width: agingPct(insights.corporate_aging.current) + '%' }"></div>
                </div>
              </div>

              <!-- 1–30 days -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-500">1–30 Days</span>
                  <span class="text-xs font-semibold text-yellow-600">{{ formatNaira(insights.corporate_aging.days_1_30) }}</span>
                </div>
                <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-yellow-400 rounded-full transition-all duration-500"
                    :style="{ width: agingPct(insights.corporate_aging.days_1_30) + '%' }"></div>
                </div>
              </div>

              <!-- 31–60 days -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-500">31–60 Days</span>
                  <span class="text-xs font-semibold text-orange-600">{{ formatNaira(insights.corporate_aging.days_31_60) }}</span>
                </div>
                <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-orange-400 rounded-full transition-all duration-500"
                    :style="{ width: agingPct(insights.corporate_aging.days_31_60) + '%' }"></div>
                </div>
              </div>

              <!-- 60+ days -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-500">60+ Days</span>
                  <span class="text-xs font-semibold text-red-600">{{ formatNaira(insights.corporate_aging.days_60_plus) }}</span>
                </div>
                <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full bg-red-500 rounded-full transition-all duration-500"
                    :style="{ width: agingPct(insights.corporate_aging.days_60_plus) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Corporate Follow-up -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-1">Corporate Follow-up</p>
            <p class="text-xs text-gray-500">
              <template v-if="insights.corporate_followup_count === 0">
                No corporate invoices due in the next 48 hours.
              </template>
              <template v-else>
                {{ insights.corporate_followup_count }} corporate invoice{{ insights.corporate_followup_count === 1 ? '' : 's' }}
                need reminders within the next 48 hours.
              </template>
            </p>
          </div>

          <!-- Individual Checkout Risk -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-1">Individual Checkout Risk</p>
            <p class="text-xs text-gray-500">
              <template v-if="insights.checkout_risk_count === 0">
                All in-house folios are settled.
              </template>
              <template v-else>
                {{ insights.checkout_risk_count }} departure{{ insights.checkout_risk_count === 1 ? '' : 's' }}
                still {{ insights.checkout_risk_count === 1 ? 'carries' : 'carry' }} unsettled folio balances.
              </template>
            </p>
          </div>

          <div v-if="insights.corporate_followup_count > 0"
            class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-3 text-center">
            <button class="text-xs font-semibold text-blue-600 hover:underline"
              @click="$router.push('/billing/corporate')">Follow up overdue invoices today</button>
          </div>
        </div>

      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function getBillingDashboardData(fromDate, toDate) {
  return callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.get_billing_dashboard_data', {
    from_date: fromDate ?? '',
    to_date:   toDate   ?? '',
  })
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatNaira(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `₦${+(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `₦${+(n / 1_000).toFixed(1)}K`
  return `₦${n.toLocaleString()}`
}

function pctOf(part, total) {
  if (!total) return 0
  return Math.round((part / total) * 100)
}

// ---------------------------------------------------------------------------
// Date filter
// ---------------------------------------------------------------------------

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function weekAgoISO() {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().slice(0, 10)
}

const fromDate = ref(weekAgoISO())
const toDate   = ref(todayISO())

function resetDates() {
  fromDate.value = weekAgoISO()
  toDate.value   = todayISO()
}

// ---------------------------------------------------------------------------
// Data state
// ---------------------------------------------------------------------------

const loading = ref(false)
const error   = ref(null)

const stats = ref({
  total_invoiced:          0,
  total_paid:              0,
  total_receivables:       0,

  individual_invoiced:     0,
  individual_paid:         0,
  individual_guest_balance: 0,

  corporate_invoiced:      0,
  corporate_paid:          0,
  corporate_balance:       0,

  invoices_in_range:       0,
  unallocated_payments:    0,
})

const activityFeed = ref([])
const feedPage    = ref(1)
const feedPerPage = 10

const insights = ref({
  corporate_aging: { current: 0, days_1_30: 0, days_31_60: 0, days_60_plus: 0, total: 0 },
  corporate_followup_count: 0,
  checkout_risk_count:      0,
})

// ---------------------------------------------------------------------------
// Feed pagination
// ---------------------------------------------------------------------------

const feedTotalPages = computed(() => Math.max(1, Math.ceil(activityFeed.value.length / feedPerPage)))
const feedPageStart  = computed(() => (feedPage.value - 1) * feedPerPage)
const feedPageEnd    = computed(() => Math.min(feedPageStart.value + feedPerPage, activityFeed.value.length))
const pagedFeed      = computed(() => activityFeed.value.slice(feedPageStart.value, feedPageEnd.value))

// ---------------------------------------------------------------------------
// Aging bar width helper
// ---------------------------------------------------------------------------

function agingPct(bucket) {
  const total = insights.value.corporate_aging.total
  if (!total) return 0
  return Math.min(100, Math.round((bucket / total) * 100))
}

// ---------------------------------------------------------------------------
// Load
// ---------------------------------------------------------------------------

async function load() {
  loading.value = true
  error.value   = null
  try {
    const data = await getBillingDashboardData(fromDate.value, toDate.value)
    stats.value        = data.stats
    activityFeed.value = data.activity_feed
    insights.value     = data.insights
    feedPage.value     = 1
  } catch (err) {
    error.value = err.message || 'Failed to load billing data.'
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// Watch — debounced 300ms
// ---------------------------------------------------------------------------

let debounceTimer = null
watch([fromDate, toDate], () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 300)
})

onMounted(load)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function feedStatusClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Follow-up': 'bg-yellow-100 text-yellow-700',
    'Open':      'bg-blue-50 text-blue-600',
    'Unapplied': 'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>