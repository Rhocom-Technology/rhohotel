<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Dashboard</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Billing Dashboard</h1>
      <p class="text-xs text-gray-400 mt-1">Live receivables — individual, corporate, aging, credit notes, and collection performance.</p>
    </div>

    <!-- Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-1">Billing Control Center</h3>
      <p class="text-xs text-gray-400 mb-4">Central workspace for guest billing, corporate accounts, group master folios, invoices, receipts, settlements, and aging review.</p>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 font-medium">From</label>
          <input v-model="fromDate" type="date" class="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <label class="text-xs text-gray-500 font-medium">To</label>
          <input v-model="toDate" type="date" class="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button @click="resetDates" class="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors">Reset</button>
        </div>
        <div class="flex items-center gap-2">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="$router.push('/billing/payments')">Payment List</button>
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="$router.push('/billing/invoices')">Invoice List</button>
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="$router.push('/billing/corporate')">Corporate Billing</button>
          <button v-if="isFrontDeskManager" class="px-4 py-2 text-xs font-medium text-white bg-green-600 border border-green-600 rounded-lg hover:bg-green-700 transition-colors" @click="$router.push('/billing/reconcile')">Payment Reconciliation</button>
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Invoice</button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-xs">Loading billing data…</span>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-xs text-red-600">
      {{ error }} <button @click="load" class="ml-3 underline font-medium">Retry</button>
    </div>

    <template v-else>

      <!-- AI Billing Risk Summary -->
      <AIInsightPanel
        title="AI Billing Risk Summary"
        context-type="billing_risk_summary"
        :context-data="billingAiContext"
        :auto-load="false"
        panel-id="billing-dashboard"
      />

      <!-- ── Row 1: Headline KPIs ── -->
      <div style="display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr 1fr;gap:12px;">

        <!-- Total Outstanding — hero -->
        <div class="bg-blue-600 rounded-xl px-5 py-4">
          <div class="flex items-center justify-between mb-1">
            <p class="text-xs text-blue-200">Total Outstanding</p>
            <span class="text-xs text-blue-200 font-medium">AR Report Match</span>
          </div>
          <p class="text-3xl font-bold text-white mt-2">{{ fmt(stats.total_outstanding) }}</p>
          <div class="mt-3 pt-3 border-t border-blue-500 flex items-center justify-between">
            <span class="text-xs text-blue-200">Invoiced {{ fmt(stats.total_invoiced) }}</span>
            <span class="text-xs text-blue-200">Collected {{ fmt(stats.total_collected) }}</span>
          </div>
        </div>

        <!-- Collection Rate -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Collection Rate</p>
          <p class="text-3xl font-bold" :class="stats.collection_rate >= 60 ? 'text-green-600' : stats.collection_rate >= 40 ? 'text-yellow-600' : 'text-red-500'">
            {{ stats.collection_rate }}%
          </p>
          <div class="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-500"
              :class="stats.collection_rate >= 60 ? 'bg-green-400' : stats.collection_rate >= 40 ? 'bg-yellow-400' : 'bg-red-500'"
              :style="{ width: Math.min(100, stats.collection_rate) + '%' }"></div>
          </div>
          <p class="text-xs text-gray-400 mt-1.5">of total invoiced collected</p>
        </div>

        <!-- Overdue -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400">Overdue</p>
            <span class="text-xs text-gray-400">All-time</span>
          </div>
          <p class="text-3xl font-bold text-red-500">{{ fmt(stats.total_overdue) }}</p>
          <p class="text-xs text-gray-400 mt-2">{{ pct(stats.total_overdue, stats.total_outstanding) }}% of net outstanding</p>
        </div>

        <!-- Invoices in Period -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Invoices in Period</p>
          <p class="text-3xl font-bold text-gray-900">{{ stats.invoices_in_range }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ fmt(stats.invoiced_in_range) }} invoiced</p>
          <p class="text-xs text-gray-400">{{ fmtDate(fromDate) }} – {{ fmtDate(toDate) }}</p>
        </div>

        <!-- Unallocated Payments -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Unallocated Payments</p>
          <p class="text-3xl font-bold" :class="stats.unallocated_payments > 0 ? 'text-red-500' : 'text-gray-900'">
            {{ stats.unallocated_payments }}
          </p>
          <p class="text-xs text-gray-400 mt-2">Receipts pending allocation</p>
        </div>

      </div>

      <!-- ── Row 2: Individual vs Corporate ── -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

        <!-- Individual -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-gray-900">Individual Guests</h3>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">{{ pct(stats.ind_outstanding, stats.total_outstanding) }}% of total</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
            <div>
              <p class="text-xs text-gray-400 mb-1">Invoiced</p>
              <p class="text-lg font-bold text-gray-900">{{ fmt(stats.ind_invoiced) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Collected</p>
              <p class="text-lg font-bold text-green-600">{{ fmt(stats.ind_collected) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Outstanding</p>
              <p class="text-lg font-bold text-gray-900">{{ fmt(stats.ind_outstanding) }}</p>
            </div>
          </div>
          <!-- Individual aging bars -->
          <div class="mt-4 pt-3 border-t border-gray-100 space-y-2">
            <p class="text-xs font-semibold text-gray-600 mb-2">Aging</p>
            <div v-for="b in indAgingBuckets" :key="b.label">
              <div class="flex items-center justify-between mb-0.5">
                <span class="text-xs text-gray-500">{{ b.label }}</span>
                <span class="text-xs font-semibold" :class="b.color">{{ fmt(b.value) }}</span>
              </div>
              <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500" :class="b.bg"
                  :style="{ width: agingPct(b.value, insights.ind_aging?.total) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Corporate -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-gray-900">Corporate Accounts</h3>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">{{ pct(stats.corp_outstanding, stats.total_outstanding) }}% of total</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
            <div>
              <p class="text-xs text-gray-400 mb-1">Invoiced</p>
              <p class="text-lg font-bold text-gray-900">{{ fmt(stats.corp_invoiced) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Collected</p>
              <p class="text-lg font-bold text-green-600">{{ fmt(stats.corp_collected) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Outstanding</p>
              <p class="text-lg font-bold text-gray-900">{{ fmt(stats.corp_outstanding) }}</p>
            </div>
          </div>
          <!-- Corporate aging bars -->
          <div class="mt-4 pt-3 border-t border-gray-100 space-y-2">
            <p class="text-xs font-semibold text-gray-600 mb-2">Aging</p>
            <div v-for="b in corpAgingBuckets" :key="b.label">
              <div class="flex items-center justify-between mb-0.5">
                <span class="text-xs text-gray-500">{{ b.label }}</span>
                <span class="text-xs font-semibold" :class="b.color">{{ fmt(b.value) }}</span>
              </div>
              <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500" :class="b.bg"
                  :style="{ width: agingPct(b.value, insights.corp_aging?.total) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ── Row 3: Activity Feed + Attention Required + Insights ── -->
      <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

        <!-- Activity Feed -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-sm font-bold text-gray-900">Billing Activity Feed</h3>
            <span class="text-xs text-gray-400">{{ activityFeed.length }} events</span>
          </div>
          <div v-if="activityFeed.length === 0" class="px-6 py-8 text-center text-xs text-gray-400">
            No billing activity found for the selected period.
          </div>
          <div v-else class="divide-y divide-gray-50">
            <div v-for="a in pagedFeed" :key="a.id" class="px-6 py-4 flex items-center justify-between">
              <div>
                <p class="text-xs font-semibold text-gray-900 mb-0.5">{{ a.title }}</p>
                <p class="text-xs text-gray-400">{{ a.desc }}</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full flex-shrink-0 ml-4" :class="feedClass(a.status)">{{ a.status }}</span>
            </div>
          </div>
          <div v-if="feedTotalPages > 1" class="px-6 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
            <p class="text-xs text-gray-400">{{ feedPageStart + 1 }}–{{ feedPageEnd }} of {{ activityFeed.length }}</p>
            <div class="flex items-center gap-1">
              <button @click="feedPage > 1 ? feedPage-- : null" :disabled="feedPage === 1"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
                :class="feedPage === 1 ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Prev</button>
              <button v-for="p in feedTotalPages" :key="p" @click="feedPage = p"
                class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                :class="feedPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">{{ p }}</button>
              <button @click="feedPage < feedTotalPages ? feedPage++ : null" :disabled="feedPage === feedTotalPages"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
                :class="feedPage === feedTotalPages ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Next</button>
            </div>
          </div>
        </div>

        <!-- Right panel -->
        <div class="space-y-3">

          <!-- Unreconciled Credits & Overpayments -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4" v-if="(insights.unreconciled_credits?.total_count > 0) || (insights.unreconciled_credits?.overpayment_total > 0)">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-bold text-gray-900">Credits & Overpayments</p>
              <span class="px-2 py-0.5 text-xs font-semibold bg-red-100 text-red-500 rounded-full">Action Required</span>
            </div>
            <!-- Credit notes row -->
            <div v-if="insights.unreconciled_credits?.credit_note_total > 0" class="mb-1">
              <p class="text-xs text-gray-500">Credit Notes</p>
              <p class="text-base font-bold text-red-500">-{{ fmt(insights.unreconciled_credits?.credit_note_total) }}</p>
            </div>
            <!-- Overpayments row -->
            <div v-if="insights.unreconciled_credits?.overpayment_total > 0" class="mb-2">
              <p class="text-xs text-gray-500">Guest Overpayments</p>
              <p class="text-base font-bold text-orange-500">{{ fmt(insights.unreconciled_credits?.overpayment_total) }}</p>
            </div>
            <div class="space-y-1 mb-3">
              <div v-for="c in (insights.unreconciled_credits?.by_customer || []).slice(0,5)" :key="c.customer"
                class="flex items-center justify-between text-xs">
                <span class="text-gray-600 truncate mr-2">{{ c.customer }}</span>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span v-if="c.overpayment_amount > 0" class="text-orange-500 font-semibold">+{{ fmt(c.overpayment_amount) }}</span>
                  <span v-if="c.credit_note_amount > 0" class="text-red-500 font-semibold">-{{ fmt(c.credit_note_amount) }}</span>
                </div>
              </div>
            </div>
            <button @click="$router.push('/billing/reconcile')"
              class="w-full py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              Reconcile Now
            </button>
          </div>

          <!-- Corporate Follow-up -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-1">Corporate Follow-up</p>
            <p class="text-xs text-gray-500">
              <template v-if="insights.corporate_followup_count === 0">No corporate invoices due in the next 48 hours.</template>
              <template v-else>{{ insights.corporate_followup_count }} invoice{{ insights.corporate_followup_count === 1 ? '' : 's' }} need reminders within 48 hours.</template>
            </p>
          </div>

          <!-- Checkout Risk -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-1">Individual Checkout Risk</p>
            <p class="text-xs text-gray-500">
              <template v-if="insights.checkout_risk_count === 0">All in-house folios are settled.</template>
              <template v-else>{{ insights.checkout_risk_count }} departure{{ insights.checkout_risk_count === 1 ? '' : 's' }} still {{ insights.checkout_risk_count === 1 ? 'carries' : 'carry' }} unsettled balances.</template>
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
import { useSessionStore } from '@/stores/session'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const session = useSessionStore()
const isFrontDeskManager = computed(() => session.hasAnyRole(['Front Desk Manager']))

// ── API ──────────────────────────────────────────────────────────────────────
async function getBillingDashboardData(from, to) {
  return callMethod('rhohotel.rhocom_hotel.api.billing_dashboard.get_billing_dashboard_data', {
    from_date: from ?? '', to_date: to ?? '',
  })
}

// ── Formatting ───────────────────────────────────────────────────────────────
function fmt(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `₦${+(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `₦${+(n / 1_000).toFixed(1)}K`
  return `₦${n.toLocaleString()}`
}
function pct(part, total) {
  if (!total) return 0
  return Math.min(100, Math.round((part / total) * 100))
}
function agingPct(bucket, total) {
  if (!total || !bucket) return 0
  return Math.min(100, Math.round((bucket / total) * 100))
}
function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Date filter ───────────────────────────────────────────────────────────────
function todayISO() { return new Date().toISOString().slice(0, 10) }
function weekAgoISO() { const d = new Date(); d.setDate(d.getDate() - 7); return d.toISOString().slice(0, 10) }

const fromDate = ref(weekAgoISO())
const toDate   = ref(todayISO())
function resetDates() { fromDate.value = weekAgoISO(); toDate.value = todayISO() }

// ── State ─────────────────────────────────────────────────────────────────────
const loading = ref(false)
const error   = ref(null)

const stats = ref({
  total_invoiced: 0, total_collected: 0, total_outstanding: 0, collection_rate: 0,
  total_overdue: 0, total_current: 0,
  corp_invoiced: 0, corp_collected: 0, corp_outstanding: 0,
  ind_invoiced: 0,  ind_collected: 0,  ind_outstanding: 0,
  unreconciled_credits_count: 0, unreconciled_credits_amount: 0,
  invoices_in_range: 0, invoiced_in_range: 0, outstanding_in_range: 0,
  unallocated_payments: 0,
})

const activityFeed = ref([])
const feedPage     = ref(1)
const feedPerPage  = 10

const emptyAging = () => ({ current: 0, days_1_30: 0, days_31_60: 0, days_60_plus: 0, total: 0 })
const insights = ref({
  corp_aging:               emptyAging(),
  ind_aging:                emptyAging(),
  unreconciled_credits:     { total_count: 0, total_amount: 0, by_customer: [] },
  corporate_followup_count: 0,
  checkout_risk_count:      0,
})

// ── Aging bucket definitions ─────────────────────────────────────────────────
const agingDefs = [
  { label: 'Current',   key: 'current',      color: 'text-green-600',  bg: 'bg-green-400'  },
  { label: '1–30 Days', key: 'days_1_30',    color: 'text-yellow-600', bg: 'bg-yellow-400' },
  { label: '31–60 Days',key: 'days_31_60',   color: 'text-orange-600', bg: 'bg-orange-400' },
  { label: '60+ Days',  key: 'days_60_plus', color: 'text-red-600',    bg: 'bg-red-500'    },
]
const corpAgingBuckets = computed(() => {
  const aging = insights.value.corp_aging || {}
  return agingDefs.map(d => ({ ...d, value: aging[d.key] || 0 }))
})
const indAgingBuckets = computed(() => {
  const aging = insights.value.ind_aging || {}
  return agingDefs.map(d => ({ ...d, value: aging[d.key] || 0 }))
})

// ── AI context ────────────────────────────────────────────────────────────────
const billingAiContext = computed(() => {
  if (!stats.value.total_invoiced && !stats.value.total_outstanding) return null
  return {
    date_range: `${fromDate.value} to ${toDate.value}`,
    total_outstanding: stats.value.total_outstanding,
    total_overdue: stats.value.total_overdue,
    collection_rate_pct: stats.value.collection_rate,
    unallocated_payments: stats.value.unallocated_payments,
    corporate_outstanding: stats.value.corp_outstanding,
    individual_outstanding: stats.value.ind_outstanding,
    corporate_followup_due: insights.value.corporate_followup_count,
    checkout_risk_folios: insights.value.checkout_risk_count,
    corporate_aging_60_plus: insights.value.corp_aging?.days_60_plus || 0,
    individual_aging_60_plus: insights.value.ind_aging?.days_60_plus || 0,
  }
})

// ── Feed pagination ───────────────────────────────────────────────────────────
const feedTotalPages = computed(() => Math.max(1, Math.ceil(activityFeed.value.length / feedPerPage)))
const feedPageStart  = computed(() => (feedPage.value - 1) * feedPerPage)
const feedPageEnd    = computed(() => Math.min(feedPageStart.value + feedPerPage, activityFeed.value.length))
const pagedFeed      = computed(() => activityFeed.value.slice(feedPageStart.value, feedPageEnd.value))

// ── Load ──────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  error.value   = null
  try {
    const data = await getBillingDashboardData(fromDate.value, toDate.value)
    stats.value        = data.stats
    activityFeed.value = data.activity_feed
    insights.value     = {
      corp_aging:               data.insights?.corp_aging               || emptyAging(),
      ind_aging:                data.insights?.ind_aging                || emptyAging(),
      unreconciled_credits:     data.insights?.unreconciled_credits     || { total_count: 0, total_amount: 0, by_customer: [] },
      corporate_followup_count: data.insights?.corporate_followup_count ?? 0,
      checkout_risk_count:      data.insights?.checkout_risk_count      ?? 0,
    }
    feedPage.value     = 1
  } catch (err) {
    error.value = err.message || 'Failed to load billing data.'
  } finally {
    loading.value = false
  }
}

let debounceTimer = null
watch([fromDate, toDate], () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(load, 300) })
onMounted(load)

// ── Feed status classes ───────────────────────────────────────────────────────
function feedClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Follow-up': 'bg-yellow-100 text-yellow-700',
    'Open':      'bg-blue-50 text-blue-600',
    'Unapplied': 'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>