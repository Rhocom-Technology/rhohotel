<template>
  <div class="night-audit-wrapper">

    <!-- ── Top Navbar ─────────────────────────────────────────────────── -->
    <header class="na-navbar">
      <div class="na-navbar-left">
        <h1 class="na-navbar-title">Night Audit Summary Report</h1>
        <p class="na-navbar-sub">Operations, finance, and control overview for end-of-day review</p>
      </div>
      <div class="na-navbar-right">
        <span class="na-navbar-date">{{ nowLabel }}</span>
        <label class="na-date-label">
          Audit Date:
          <input v-model="auditDate" type="date" class="na-date-input" />
        </label>
        <button @click="loadData" class="na-btn-refresh">Refresh</button>
        <button @click="closeDay" :disabled="closingDay || isDayClosed" class="na-btn-close" :class="{ 'na-btn-closed': isDayClosed }">{{ closingDay ? 'Closing...' : isDayClosed ? 'Day Closed' : 'Close Day' }}</button>
        <div class="na-avatar">{{ avatarInitials }}</div>
      </div>
    </header>

    <!-- ── Main Body ──────────────────────────────────────────────────── -->
    <main class="na-body">

      <div v-if="closeDaySuccess" class="na-inline-ok">{{ closeDaySuccess }}</div>
      <div v-if="closeDayError" class="na-inline-err">{{ closeDayError }}</div>

      <!-- Audit Meta Row -->
      <div class="na-meta-row">
        <div class="na-meta-item" v-for="m in auditMeta" :key="m.label">
          <p class="na-meta-label">{{ m.label }}</p>
          <p class="na-meta-value">{{ m.value }}</p>
        </div>
      </div>

      <!-- Loading / Error -->
      <div v-if="resource.loading" class="na-state-card">
        <p class="na-state-text">Loading audit data…</p>
      </div>
      <div v-else-if="resource.error" class="na-state-card">
        <p class="na-state-text na-state-err">Failed to load audit data.</p>
        <button @click="loadData" class="na-btn-retry">Retry</button>
      </div>

      <template v-else-if="data">

        <!-- AI Night Audit Narrative -->
        <AIInsightPanel
          v-if="session.isHotelManager || session.isFrontDeskManager"
          title="AI Night Audit Narrative"
          context-type="night_audit_summary"
          :context-data="nightAuditContext"
          :auto-load="false"
          panel-id="night-audit"
          style="margin-bottom:2px;"
        />

        <!-- ── Top Summary ──────────────────────────────────────────── -->
        <section class="na-section">
          <div class="na-section-header">
            <h2 class="na-section-title">Top Summary <span class="na-section-sub">glance</span></h2>
          </div>
          <div class="na-stat-grid">
            <div class="na-stat-card na-stat-dark">
              <p class="na-stat-label">Total Revenue Today</p>
              <p class="na-stat-value">{{ fmt(data.revenue.total_revenue) }}</p>
              <p class="na-stat-badge na-badge-green">Room + F&amp;B + Other</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Room Revenue</p>
              <p class="na-stat-value na-value-dark">{{ fmt(data.revenue.room_revenue) }}</p>
              <p class="na-stat-badge na-badge-blue">{{ roomRevPct }}% of total revenue</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Total Pending Payment</p>
              <p class="na-stat-value na-value-dark">{{ fmt(data.outstanding.total_outstanding) }}</p>
              <p class="na-stat-badge na-badge-red">{{ data.outstanding.open_invoice_count || 0 }} open invoices</p>
            </div>
            <div class="na-stat-card na-stat-green-tint">
              <p class="na-stat-label">Occupancy %</p>
              <p class="na-stat-value na-value-dark">{{ data.occupancy.occupancy_pct }}%</p>
              <p class="na-stat-badge na-badge-gray">{{ data.occupancy.occupied }} occupied out of {{ data.occupancy.total_rooms }} rooms</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Check-ins / Check-outs</p>
              <p class="na-stat-value na-value-dark">{{ data.occupancy.arrivals }} / {{ data.occupancy.departures }}</p>
              <p class="na-stat-badge na-badge-gray">Today</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Open Invoices</p>
              <p class="na-stat-value na-value-dark">{{ data.outstanding.open_invoice_count || 0 }}</p>
              <p class="na-stat-badge na-badge-red">Submitted invoices requiring follow-up</p>
            </div>
          </div>
        </section>

        <!-- ── Revenue + Transaction Validation ────────────────────── -->
        <div class="na-two-col">

          <!-- Revenue Breakdown -->
          <section class="na-card">
            <h3 class="na-card-title">Revenue Breakdown</h3>
            <p class="na-card-sub">Rooms vs POS vs Other Income, including payment methods</p>

            <!-- Legend -->
            <div class="na-legend">
              <span class="na-dot na-dot-blue"></span><span class="na-legend-label">Rooms</span>
              <span class="na-dot na-dot-green"></span><span class="na-legend-label">POS</span>
              <span class="na-dot na-dot-orange"></span><span class="na-legend-label">Other Income</span>
            </div>

            <!-- Horizontal bars -->
            <div class="na-bar-group">
              <div class="na-bar-row" v-for="rb in revenueBars" :key="rb.label">
                <span class="na-bar-label">{{ rb.label }}</span>
                <div class="na-bar-track">
                  <div class="na-bar-fill" :style="{ width: rb.pct + '%', background: rb.color }"></div>
                </div>
                <span class="na-bar-amt">{{ fmt(rb.amount) }}</span>
              </div>
            </div>

            <!-- Mini Trend Line (SVG) -->
            <div class="na-trend-label">Revenue Trend</div>
            <svg class="na-trend-svg" viewBox="0 0 280 60" preserveAspectRatio="none">
              <polyline points="0,50 40,42 80,38 120,30 160,25 200,18 240,12 280,5" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="0,55 40,50 80,48 120,44 160,40 200,36 240,30 280,22" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>

            <!-- Payment Methods -->
            <div class="na-pm-section">
              <h4 class="na-pm-title">Payment Methods</h4>
              <div class="na-pm-list">
                <div class="na-pm-row" v-for="m in data.payments.by_method" :key="m.method">
                  <span class="na-pm-label">{{ m.method }}</span>
                  <div class="na-pm-track">
                    <div class="na-pm-fill" :style="{ width: paymentPct(m.amount) + '%', background: pmColor(m.method) }"></div>
                  </div>
                  <span class="na-pm-amt">{{ fmt(m.amount) }}</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Transaction Validation Critical -->
          <section class="na-card" :class="criticalItems.length ? 'na-card-critical' : 'na-card-ok'">
            <h3 class="na-card-title" :class="criticalItems.length ? 'na-title-red' : 'na-title-green'">
              Transaction Validation {{ criticalItems.length ? '(Critical)' : '(All Clear)' }}
            </h3>
            <p class="na-card-sub" :class="criticalItems.length ? 'na-sub-red' : ''">
              {{ criticalItems.length
                ? 'Exceptions exist and require action before close of day.'
                : 'No exceptions found. Safe to proceed with day close.' }}
            </p>

            <div v-if="criticalItems.length" class="na-critical-list">
              <div class="na-critical-item" v-for="c in criticalItems" :key="c.title">
                <div class="na-critical-left">
                  <span class="na-critical-dot"></span>
                  <div>
                    <p class="na-critical-title">{{ c.title }}</p>
                    <p class="na-critical-desc">{{ c.desc }}</p>
                  </div>
                </div>
                <span class="na-critical-count">{{ c.count }}</span>
              </div>
            </div>
            <div v-else class="na-all-clear">
              <span class="na-all-clear-icon">✓</span>
              <p>All transactions validated</p>
            </div>
          </section>
        </div>

        <!-- ── Room Status + Guest Movement ─────────────────────────── -->
        <div class="na-two-col">

          <!-- Room Status Summary -->
          <section class="na-card">
            <h3 class="na-card-title">Room Status Summary</h3>
            <p class="na-card-sub">Occupied, vacant by cleanliness state, and out of service</p>

            <div class="na-room-bars">
              <div class="na-room-bar-row" v-for="rs in roomStatusBars" :key="rs.label">
                <span class="na-room-label">{{ rs.label }}</span>
                <div class="na-room-track">
                  <div class="na-room-fill" :style="{ width: rs.pct + '%', background: rs.color }"></div>
                </div>
                <span class="na-room-count">{{ rs.count }}</span>
              </div>
            </div>

            <!-- Distribution Chart (SVG bar chart - dynamic) -->
            <div class="na-dist-section">
              <h4 class="na-pm-title">Distribution</h4>
              <div class="na-dist-chart">
                <svg viewBox="0 0 200 90" class="na-dist-svg">
                  <rect v-for="b in distSvgBars" :key="b.x"
                    :x="b.x" :y="b.y" width="35" :height="b.height" :fill="b.color" rx="3"/>
                </svg>
                <div class="na-dist-legend">
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-blue"></span> Occupied ({{ roomDistribution.occupied }})</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-green"></span> Vacant Clean ({{ roomDistribution.vacClean }})</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-orange"></span> Vacant Dirty ({{ roomDistribution.vacDirty }})</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-red"></span> Out of Service ({{ roomDistribution.oos }})</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Guest Movement Summary -->
          <section class="na-card">
            <h3 class="na-card-title">Guest Movement Summary</h3>
            <p class="na-card-sub">Arrivals, departures, and no-shows for the day</p>

            <div class="na-gm-stats">
              <div class="na-gm-stat">
                <p class="na-gm-label">Total Arrivals</p>
                <p class="na-gm-value">{{ data.occupancy.arrivals }}</p>
              </div>
              <div class="na-gm-stat">
                <p class="na-gm-label">Total Departures</p>
                <p class="na-gm-value">{{ data.occupancy.departures }}</p>
              </div>
              <div class="na-gm-stat">
                <p class="na-gm-label">No-shows</p>
                <p class="na-gm-value">{{ data.occupancy.noshows ?? 0 }}</p>
              </div>
            </div>

            <!-- Guest Flow Chart -->
            <div class="na-gf-section">
              <h4 class="na-pm-title">Guest Flow Chart</h4>
              <div v-if="guestFlowData.length" class="na-gf-chart">
                <div class="na-gf-group" v-for="slot in guestFlowData" :key="slot.label">
                  <div class="na-gf-bars">
                    <div class="na-gf-bar na-gf-arr" :style="{ height: slot.arrPx + 'px' }" :title="'Arrivals: ' + slot.arrivals"></div>
                    <div class="na-gf-bar na-gf-dep" :style="{ height: slot.depPx + 'px' }" :title="'Departures: ' + slot.departures"></div>
                  </div>
                  <span class="na-gf-label">{{ slot.label }}</span>
                </div>
              </div>
              <p v-else class="na-empty-sm">No movement data for this date.</p>
              <div class="na-legend" style="margin-top:8px;">
                <span class="na-dot na-dot-blue"></span><span class="na-legend-label">Arrivals</span>
                <span class="na-dot na-dot-green"></span><span class="na-legend-label">Departures</span>
              </div>
            </div>
          </section>
        </div>

        <!-- ── Guest Ledger ──────────────────────────────────────────── -->
        <section class="na-card">
          <div class="na-table-header">
            <div>
              <h3 class="na-card-title">Guest Ledger — Outstanding Balances</h3>
              <p class="na-card-sub">In-house folios with unpaid invoice balances</p>
            </div>
            <span class="na-badge-pill na-badge-red-pill">{{ data.outstanding.guest_count }} accounts</span>
          </div>
          <div class="na-table-wrap" v-if="data.outstanding.ledger.length">
            <table class="na-table">
              <thead>
                <tr>
                  <th>Check-in</th>
                  <th>Guest</th>
                  <th>Room</th>
                  <th class="na-th-right">Outstanding</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in data.outstanding.ledger" :key="row.check_in"
                    @click="router.push('/check-ins/' + row.check_in)">
                  <td class="na-td-mono na-td-blue">{{ row.check_in }}</td>
                  <td class="na-td-bold">{{ row.guest }}</td>
                  <td>{{ row.room }}</td>
                  <td class="na-td-right na-td-red">{{ fmt(row.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="na-empty">No outstanding balances.</div>
        </section>

        <!-- ── Room Status Snapshot ──────────────────────────────────── -->
        <section class="na-card">
          <div class="na-table-header">
            <div>
              <h3 class="na-card-title">Room Status Snapshot</h3>
              <p class="na-card-sub">Current state of all rooms</p>
            </div>
            <div class="na-filter-row">
              <input v-model="roomSearch" type="text" placeholder="Search room…" class="na-input"/>
              <select v-model="roomStatusFilter" class="na-select">
                <option value="">All Statuses</option>
                <option value="Occupied">Occupied</option>
                <option value="Vacant">Vacant</option>
                <option value="Reserved">Reserved</option>
                <option value="Maintenance">Maintenance</option>
              </select>
            </div>
          </div>
          <div class="na-table-wrap">
            <table class="na-table">
              <thead>
                <tr>
                  <th>Room</th><th>Type</th><th>Floor</th><th>Status</th><th>HK Status</th><th>Guest</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rm in filteredRooms" :key="rm.room_number">
                  <td class="na-td-bold">{{ rm.room_number }}</td>
                  <td>{{ rm.room_type }}</td>
                  <td>{{ rm.floor }}</td>
                  <td><span class="na-status-pill" :class="roomStatusClass(rm.status)">{{ rm.status }}</span></td>
                  <td><span class="na-status-pill" :class="hkStatusClass(rm.housekeeping_status)">{{ rm.housekeeping_status }}</span></td>
                  <td>{{ rm.guest || '—' }}</td>
                </tr>
                <tr v-if="!filteredRooms.length">
                  <td colspan="6" class="na-empty">No rooms match the filter.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="na-table-footer">
            <p class="na-footer-info">Showing {{ filteredRooms.length }} of {{ data.room_status.length }} rooms</p>
            <div class="na-pagination" v-if="totalRoomPages > 1">
              <button v-for="p in Math.min(totalRoomPages, 6)" :key="p"
                @click="roomPage = p"
                class="na-page-btn"
                :class="{ 'na-page-btn-active': roomPage === p }">{{ p }}</button>
            </div>
          </div>
        </section>

      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'
import { callMethodForm } from '@/lib/api'

const router = useRouter()
const session = useSessionStore()

function localDateISO(date = new Date()) {
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

const today = localDateISO()
const auditDate = ref(today)
const roomSearch = ref('')
const roomStatusFilter = ref('')
const roomPage = ref(1)
const roomPageSize = 30
const closingDay = ref(false)
const closeDayError = ref('')
const closeDaySuccess = ref('')
const isDayClosed = computed(() => !!data.value?.is_closed)

// ── Session / avatar ─────────────────────────────────────────────────────
const avatarInitials = computed(() => {
  const name = session.fullName || session.user || ''
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'NA'
})

const nowLabel = computed(() => {
  return new Date().toLocaleString('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  }).replace(',', '')
})

const auditMeta = computed(() => [
  { label: 'Audit Date',  value: auditDate.value },
  { label: 'Shift',       value: 'Night Shift' },
  { label: 'Prepared By', value: session.fullName || session.user || 'Night Auditor' },
  { label: 'Scope',       value: 'All Departments' },
  { label: 'Status',      value: data.value ? 'Audit Open' : 'Loading…' },
])

// ── API resource ─────────────────────────────────────────────────────────
const resource = createResource({
  url: 'rhohotel.rhocom_hotel.api.front_desk.get_night_audit_data',
  params: { audit_date: auditDate.value },
  auto: true,
})

const data = computed(() => resource.data || null)

function loadData() {
  resource.params = { audit_date: auditDate.value }
  resource.reload()
}

watch(auditDate, loadData)

// ── Revenue ──────────────────────────────────────────────────────────────
const roomRevPct = computed(() => {
  if (!data.value || !data.value.revenue.total_revenue) return 0
  return Math.round((data.value.revenue.room_revenue / data.value.revenue.total_revenue) * 100)
})

const revenueBars = computed(() => {
  if (!data.value) return []
  const max = data.value.revenue.total_revenue || 1
  return [
    { label: 'Rooms', amount: data.value.revenue.room_revenue, pct: (data.value.revenue.room_revenue / max) * 100, color: '#3b82f6' },
    { label: 'POS',   amount: data.value.revenue.fnb_revenue,  pct: (data.value.revenue.fnb_revenue  / max) * 100, color: '#22c55e' },
    { label: 'Other', amount: data.value.revenue.other_revenue, pct: (data.value.revenue.other_revenue / max) * 100, color: '#f59e0b' },
  ]
})

// ── Critical items (real API data) ───────────────────────────────────────
const criticalItems = computed(() => {
  if (!data.value) return []
  const items = []
  const openInvoices = data.value.outstanding.open_invoice_count || 0
  if (openInvoices > 0) {
    items.push({
      title: 'Unsettled Invoices',
      desc: `${openInvoices} submitted invoices remain open with pending settlement.`,
      count: openInvoices,
    })
  }
  const openPos = data.value.critical?.open_pos_orders || 0
  if (openPos > 0) {
    items.push({
      title: 'POS Orders Not Closed',
      desc: `${openPos} draft or held POS bills are still open at shift end.`,
      count: openPos,
    })
  }
  const unalloc = data.value.critical?.unallocated_payments || 0
  if (unalloc > 0) {
    items.push({
      title: 'Unallocated Payments',
      desc: `${unalloc} payment entries have not been allocated to invoices.`,
      count: unalloc,
    })
  }
  return items
})

// ── Room distribution (computed from real room_status list) ──────────────
const roomDistribution = computed(() => {
  if (!data.value) return { occupied: 0, vacClean: 0, vacDirty: 0, oos: 0 }
  const rooms = data.value.room_status
  return {
    occupied: rooms.filter(r => r.status === 'Occupied').length,
    vacClean: rooms.filter(r => r.status === 'Vacant' && r.housekeeping_status === 'Clean').length,
    vacDirty: rooms.filter(r => r.status === 'Vacant' && ['Dirty', 'In Progress'].includes(r.housekeeping_status)).length,
    oos:      rooms.filter(r => r.status === 'Maintenance').length,
  }
})

const roomStatusBars = computed(() => {
  if (!data.value) return []
  const d = roomDistribution.value
  const max = Math.max(d.occupied, 1)
  return [
    { label: 'Occupied',       count: d.occupied,  pct: 100,                       color: '#3b82f6' },
    { label: 'Vacant Clean',   count: d.vacClean,  pct: (d.vacClean / max) * 100,  color: '#22c55e' },
    { label: 'Vacant Dirty',   count: d.vacDirty,  pct: (d.vacDirty / max) * 100,  color: '#f59e0b' },
    { label: 'Out of Service', count: d.oos,       pct: (d.oos / max) * 100,        color: '#ef4444' },
  ]
})

const distSvgBars = computed(() => {
  const d = roomDistribution.value
  const total = (d.occupied + d.vacClean + d.vacDirty + d.oos) || 1
  const maxH = 75
  return [
    { x: 10,  color: '#3b82f6', val: d.occupied  },
    { x: 60,  color: '#22c55e', val: d.vacClean  },
    { x: 110, color: '#f59e0b', val: d.vacDirty  },
    { x: 160, color: '#ef4444', val: d.oos        },
  ].map(g => {
    const h = Math.max(3, Math.round((g.val / total) * maxH))
    return { ...g, height: h, y: 85 - h }
  })
})

// ── Guest flow chart (real hourly_movement from API) ─────────────────────
const guestFlowData = computed(() => {
  if (!data.value?.hourly_movement?.length) return []
  const maxVal = Math.max(...data.value.hourly_movement.map(h => Math.max(h.arrivals, h.departures, 1)))
  const chartH = 60
  return data.value.hourly_movement.map(h => ({
    label:      fmtHour(h.hour),
    arrPx:      Math.max(3, Math.round((h.arrivals   / maxVal) * chartH)),
    depPx:      Math.max(3, Math.round((h.departures / maxVal) * chartH)),
    arrivals:   h.arrivals,
    departures: h.departures,
  }))
})

function fmtHour(h) {
  if (h === 0)  return '12AM'
  if (h < 12)   return h + 'AM'
  if (h === 12) return '12PM'
  return (h - 12) + 'PM'
}

// ── Payment helpers ──────────────────────────────────────────────────────
function paymentPct(amount) {
  if (!data.value || !data.value.payments.total_collected) return 0
  return Math.round((amount / data.value.payments.total_collected) * 100)
}

function pmColor(method) {
  return {
    Cash:               '#f87171',
    Transfer:           '#fb923c',
    Card:               '#60a5fa',
    'Bank Transfer':    '#a78bfa',
    'Corporate Credit': '#4ade80',
    POS:                '#34d399',
  }[method] || '#9ca3af'
}

// ── Room filtering & pagination ──────────────────────────────────────────
const filteredRoomsAll = computed(() => {
  if (!data.value) return []
  let list = data.value.room_status
  if (roomSearch.value) {
    const q = roomSearch.value.toLowerCase()
    list = list.filter(r =>
      r.room_number.toLowerCase().includes(q) ||
      r.room_type.toLowerCase().includes(q) ||
      (r.guest || '').toLowerCase().includes(q) ||
      String(r.floor).toLowerCase().includes(q)
    )
  }
  if (roomStatusFilter.value) list = list.filter(r => r.status === roomStatusFilter.value)
  return list
})

const totalRoomPages = computed(() => Math.max(1, Math.ceil(filteredRoomsAll.value.length / roomPageSize)))
const filteredRooms = computed(() =>
  filteredRoomsAll.value.slice((roomPage.value - 1) * roomPageSize, roomPage.value * roomPageSize)
)
watch([roomSearch, roomStatusFilter], () => { roomPage.value = 1 })

// ── Generic helpers ──────────────────────────────────────────────────────
function fmt(amount) {
  return `₦${Number(amount || 0).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
function roomStatusClass(s) {
  return { Occupied: 'pill-green', Vacant: 'pill-gray', Reserved: 'pill-blue', Maintenance: 'pill-red' }[s] || 'pill-gray'
}
function hkStatusClass(s) {
  return { Clean: 'pill-green-soft', Dirty: 'pill-yellow', 'In Progress': 'pill-blue-soft', Inspected: 'pill-purple' }[s] || 'pill-gray'
}
async function closeDay() {
  if (closingDay.value || isDayClosed.value) return
  closeDayError.value = ''
  closeDaySuccess.value = ''
  if (!confirm('Are you sure you want to close the day? This action cannot be undone.')) return

  closingDay.value = true
  try {
    const result = await callMethodForm('rhohotel.rhocom_hotel.api.front_desk.close_day', {
      audit_date: auditDate.value,
      force_close: 0,
      reason: '',
    })
    closeDaySuccess.value = result?.message || 'Day close completed successfully.'
    await loadData()  // reloads data.is_closed → disables button
  } catch (e) {
    const msg = String(e?.message || 'Day close failed.')
    // Allow manager override from UI when server blocks with exceptions.
    if (msg.toLowerCase().includes('force close')) {
      const proceed = confirm(msg + '\n\nProceed with manager override?')
      if (!proceed) {
        closeDayError.value = msg
        return
      }
      const reason = prompt('Enter manager reason for force close:') || ''
      if (!reason.trim()) {
        closeDayError.value = 'Manager reason is required for force close.'
        return
      }
      try {
        const forced = await callMethodForm('rhohotel.rhocom_hotel.api.front_desk.close_day', {
          audit_date: auditDate.value,
          force_close: 1,
          reason,
        })
        closeDaySuccess.value = forced?.message || 'Day close completed with manager override.'
        await loadData()
      } catch (forcedErr) {
        closeDayError.value = String(forcedErr?.message || 'Forced close failed.')
      }
      return
    }
    closeDayError.value = msg
  } finally {
    closingDay.value = false
  }
}

const nightAuditContext = computed(() => {
  if (!data.value) return null
  return {
    date: auditDate.value,
    total_revenue: data.value.revenue?.total_revenue,
    room_revenue: data.value.revenue?.room_revenue,
    fnb_revenue: data.value.revenue?.fnb_revenue,
    occupancy_pct: data.value.occupancy?.occupancy_pct,
    occupied: data.value.occupancy?.occupied,
    total_rooms: data.value.occupancy?.total_rooms,
    arrivals: data.value.occupancy?.arrivals,
    departures: data.value.occupancy?.departures,
    noshows: data.value.occupancy?.noshows ?? 0,
    outstanding_total: data.value.outstanding?.total_outstanding,
    outstanding_count: data.value.outstanding?.open_invoice_count ?? data.value.outstanding?.guest_count,
    critical_items_count: criticalItems.value.length,
  }
})
</script>

<style scoped>
/* ── Tokens ─────────────────────────────────────────────────────────── */
* { box-sizing: border-box; margin: 0; padding: 0; }

.night-audit-wrapper {
  font-family: 'DM Sans', 'Segoe UI', sans-serif;
  background: #f1f5f9;
  min-height: 100vh;
  color: #111827;
}

/* ── Navbar ─────────────────────────────────────────────────────────── */
.na-navbar {
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  position: sticky;
  top: 0;
  z-index: 50;
  flex-wrap: wrap;
  gap: 10px;
}
.na-navbar-title { font-size: 17px; font-weight: 700; color: #f8fafc; letter-spacing: -.3px; }
.na-navbar-sub   { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.na-navbar-right { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.na-navbar-date  { font-size: 11px; color: #94a3b8; }
.na-btn-close {
  background: #ef4444; color: #fff; border: none;
  padding: 7px 16px; border-radius: 7px;
  font-size: 12px; font-weight: 600; cursor: pointer; transition: background .15s;
}
.na-btn-close:hover { background: #dc2626; }
.na-btn-close.na-btn-closed,
.na-btn-close:disabled { background: #6b7280; cursor: not-allowed; opacity: 0.75; }
.na-btn-close.na-btn-closed:hover { background: #6b7280; }
.na-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: #2563eb; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}

/* ── Body ───────────────────────────────────────────────────────────── */
.na-body {
  max-width: 1280px; margin: 0 auto;
  padding: 24px 24px 48px;
  display: flex; flex-direction: column; gap: 18px;
}

/* ── Close Banner ───────────────────────────────────────────────────── */
.na-close-banner {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 14px 24px;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 10px;
}
.na-close-banner-meta { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.na-close-banner-right { display: flex; align-items: center; gap: 8px; }
.na-meta-ts { font-size: 11px; color: #6b7280; }
.na-date-label { font-size: 11px; color: #6b7280; display: flex; align-items: center; gap: 6px; }
.na-date-input {
  padding: 5px 10px; font-size: 11px;
  border: 1px solid #e5e7eb; border-radius: 7px; outline: none; color: #111827;
}
.na-date-input:focus { border-color: #3b82f6; }
.na-btn-refresh {
  background: #f1f5f9; color: #374151; border: 1px solid #e5e7eb;
  padding: 7px 14px; border-radius: 7px;
  font-size: 12px; font-weight: 600; cursor: pointer; transition: background .15s;
}
.na-btn-refresh:hover { background: #e2e8f0; }
.na-btn-close-lg {
  background: #ef4444; color: #fff; border: none;
  padding: 8px 22px; border-radius: 8px;
  font-size: 13px; font-weight: 700; cursor: pointer;
}
.na-btn-close-lg:hover { background: #dc2626; }

.na-inline-ok {
  background: #f0fdf4;
  border: 1px solid #86efac;
  color: #166534;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
}

.na-inline-err {
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #b91c1c;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
}

/* ── Audit Meta Row ─────────────────────────────────────────────────── */
.na-meta-row {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  display: grid; grid-template-columns: repeat(5, 1fr);
}
.na-meta-item { padding: 14px 20px; border-right: 1px solid #e5e7eb; }
.na-meta-item:last-child { border-right: none; }
.na-meta-label { font-size: 10px; color: #6b7280; margin-bottom: 5px; }
.na-meta-value { font-size: 13px; font-weight: 600; color: #111827; }

/* ── States ─────────────────────────────────────────────────────────── */
.na-state-card { background: #fff; border-radius: 12px; border: 1px solid #e5e7eb; padding: 48px; text-align: center; }
.na-state-text { font-size: 13px; color: #6b7280; }
.na-state-err  { color: #ef4444; }
.na-btn-retry  { margin-top: 10px; padding: 6px 16px; font-size: 12px; border: 1px solid #bfdbfe; color: #3b82f6; border-radius: 6px; background: #eff6ff; cursor: pointer; }

/* ── Section ─────────────────────────────────────────────────────────── */
.na-section-header { margin-bottom: 12px; }
.na-section-title  { font-size: 15px; font-weight: 700; color: #111827; }
.na-section-sub    { font-size: 12px; font-weight: 400; color: #6b7280; margin-left: 4px; }

/* ── Stat Grid ──────────────────────────────────────────────────────── */
.na-stat-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
.na-stat-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px 18px;
}
.na-stat-dark       { background: #1e293b; }
.na-stat-green-tint { background: #f0fdf4; }
.na-stat-label { font-size: 10px; color: #6b7280; margin-bottom: 8px; }
.na-stat-dark .na-stat-label { color: #94a3b8; }
.na-stat-value { font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: -.5px; }
.na-value-dark { color: #111827; }
.na-stat-badge { font-size: 10px; margin-top: 6px; font-weight: 500; }
.na-badge-green { color: #16a34a; }
.na-badge-blue  { color: #2563eb; }
.na-badge-red   { color: #dc2626; }
.na-badge-gray  { color: #6b7280; }

/* ── Two-col layout ─────────────────────────────────────────────────── */
.na-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

/* ── Cards ──────────────────────────────────────────────────────────── */
.na-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 20px 24px;
}
.na-card-critical { border-color: #fca5a5; background: #fff5f5; }
.na-card-ok       { border-color: #86efac; background: #f0fdf4; }
.na-card-title { font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 2px; }
.na-card-sub   { font-size: 11px; color: #6b7280; margin-bottom: 14px; }
.na-title-red   { color: #b91c1c; }
.na-title-green { color: #15803d; }
.na-sub-red    { color: #dc2626; }

/* ── All Clear ──────────────────────────────────────────────────────── */
.na-all-clear {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 32px; gap: 8px; color: #16a34a;
}
.na-all-clear-icon { font-size: 32px; font-weight: 700; }
.na-all-clear p { font-size: 13px; font-weight: 600; }

/* ── Legend ─────────────────────────────────────────────────────────── */
.na-legend { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.na-legend-label { font-size: 11px; color: #6b7280; margin-right: 6px; }
.na-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.na-dot-blue   { background: #3b82f6; }
.na-dot-green  { background: #22c55e; }
.na-dot-orange { background: #f59e0b; }
.na-dot-red    { background: #ef4444; }

/* ── Revenue bars ───────────────────────────────────────────────────── */
.na-bar-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.na-bar-row   { display: flex; align-items: center; gap: 10px; }
.na-bar-label { font-size: 11px; color: #6b7280; width: 40px; flex-shrink: 0; }
.na-bar-track { flex: 1; height: 10px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.na-bar-fill  { height: 100%; border-radius: 99px; transition: width .4s ease; min-width: 2px; }
.na-bar-amt   { font-size: 11px; font-weight: 600; color: #111827; width: 70px; text-align: right; flex-shrink: 0; }

/* ── Trend SVG ──────────────────────────────────────────────────────── */
.na-trend-label { font-size: 10px; color: #6b7280; margin-bottom: 4px; }
.na-trend-svg { width: 100%; height: 60px; margin-bottom: 16px; }

/* ── Payment methods ────────────────────────────────────────────────── */
.na-pm-section { border-top: 1px solid #e5e7eb; padding-top: 14px; }
.na-pm-title { font-size: 12px; font-weight: 600; color: #111827; margin-bottom: 10px; }
.na-pm-list { display: flex; flex-direction: column; gap: 8px; }
.na-pm-row  { display: flex; align-items: center; gap: 10px; }
.na-pm-label { font-size: 11px; color: #6b7280; width: 110px; flex-shrink: 0; }
.na-pm-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.na-pm-fill  { height: 100%; border-radius: 99px; min-width: 2px; }
.na-pm-amt   { font-size: 11px; font-weight: 600; color: #111827; width: 70px; text-align: right; flex-shrink: 0; }
.na-empty-sm { font-size: 11px; color: #6b7280; padding: 12px 0; }

/* ── Critical items ─────────────────────────────────────────────────── */
.na-critical-list { display: flex; flex-direction: column; gap: 14px; margin-top: 6px; }
.na-critical-item {
  background: #fff; border: 1px solid #fca5a5; border-radius: 10px;
  padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 10px;
}
.na-critical-left { display: flex; align-items: flex-start; gap: 10px; }
.na-critical-dot  { width: 10px; height: 10px; border-radius: 50%; background: #ef4444; flex-shrink: 0; margin-top: 3px; }
.na-critical-title { font-size: 12px; font-weight: 700; color: #b91c1c; }
.na-critical-desc  { font-size: 11px; color: #6b7280; margin-top: 2px; }
.na-critical-count {
  background: #fee2e2; color: #b91c1c;
  font-size: 12px; font-weight: 700;
  padding: 4px 12px; border-radius: 8px; flex-shrink: 0;
}

/* ── Room status bars ───────────────────────────────────────────────── */
.na-room-bars { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
.na-room-bar-row { display: flex; align-items: center; gap: 10px; }
.na-room-label { font-size: 11px; color: #6b7280; width: 90px; flex-shrink: 0; }
.na-room-track { flex: 1; height: 16px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.na-room-fill  { height: 100%; border-radius: 6px; transition: width .4s ease; min-width: 2px; }
.na-room-count { font-size: 11px; font-weight: 600; color: #111827; width: 30px; text-align: right; flex-shrink: 0; }

/* ── Distribution chart ─────────────────────────────────────────────── */
.na-dist-section { border-top: 1px solid #e5e7eb; padding-top: 14px; }
.na-dist-chart   { display: flex; align-items: flex-end; gap: 16px; }
.na-dist-svg     { width: 160px; height: 90px; flex-shrink: 0; }
.na-dist-legend  { display: flex; flex-direction: column; gap: 6px; }
.na-dist-legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #6b7280; }

/* ── Guest movement ─────────────────────────────────────────────────── */
.na-gm-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
.na-gm-stat  { background: #f8fafc; border-radius: 10px; padding: 14px; border: 1px solid #e5e7eb; }
.na-gm-label { font-size: 10px; color: #6b7280; margin-bottom: 6px; }
.na-gm-value { font-size: 26px; font-weight: 800; color: #111827; }

/* ── Guest flow chart ── FIXED ──────────────────────────────────────── */
.na-gf-section { border-top: 1px solid #e5e7eb; padding-top: 14px; }
.na-gf-chart {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 10px;
  height: 80px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 4px;
  overflow-x: auto;
  padding-top: 4px;
}
/* Each time-slot group */
.na-gf-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
/* Bars sit side-by-side, growing upward */
.na-gf-bars {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 3px;
  height: 65px;
}
.na-gf-bar { width: 10px; border-radius: 3px 3px 0 0; }
.na-gf-arr { background: #3b82f6; }
.na-gf-dep { background: #22c55e; }
.na-gf-label { font-size: 9px; color: #94a3b8; margin-top: 4px; white-space: nowrap; }

/* ── Tables ─────────────────────────────────────────────────────────── */
.na-table-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
.na-table-wrap   { overflow-x: auto; }
.na-table { width: 100%; border-collapse: collapse; }
.na-table thead tr { border-bottom: 1px solid #e5e7eb; }
.na-table th { text-align: left; font-size: 11px; font-weight: 600; color: #6b7280; padding: 8px 14px; white-space: nowrap; }
.na-table tbody tr { border-bottom: 1px solid #f8fafc; transition: background .1s; cursor: pointer; }
.na-table tbody tr:hover { background: #f8fafc; }
.na-table td { padding: 10px 14px; font-size: 12px; color: #6b7280; }
.na-th-right { text-align: right; }
.na-td-mono  { font-family: monospace; }
.na-td-blue  { color: #2563eb; }
.na-td-bold  { font-weight: 600; color: #111827; }
.na-td-right { text-align: right; }
.na-td-red   { color: #dc2626; font-weight: 700; }
.na-empty    { padding: 32px; text-align: center; font-size: 12px; color: #6b7280; }

/* ── Badges / pills ─────────────────────────────────────────────────── */
.na-badge-pill    { padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; }
.na-badge-red-pill { background: #fee2e2; color: #dc2626; }
.na-status-pill   { padding: 2px 9px; border-radius: 99px; font-size: 10px; font-weight: 600; }
.pill-green       { background: #dcfce7; color: #16a34a; }
.pill-gray        { background: #f3f4f6; color: #6b7280; }
.pill-blue        { background: #dbeafe; color: #2563eb; }
.pill-red         { background: #fee2e2; color: #dc2626; }
.pill-green-soft  { background: #f0fdf4; color: #16a34a; }
.pill-yellow      { background: #fef9c3; color: #a16207; }
.pill-blue-soft   { background: #eff6ff; color: #3b82f6; }
.pill-purple      { background: #f5f3ff; color: #7c3aed; }

/* ── Filters ─────────────────────────────────────────────────────────── */
.na-filter-row { display: flex; gap: 8px; flex-wrap: wrap; }
.na-input, .na-select {
  padding: 6px 12px; font-size: 11px;
  border: 1px solid #e5e7eb; border-radius: 8px; outline: none;
  color: #111827; background: #fff;
}
.na-input:focus, .na-select:focus { border-color: #3b82f6; }

/* ── Pagination ─────────────────────────────────────────────────────── */
.na-table-footer { padding: 12px 14px; border-top: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.na-footer-info  { font-size: 11px; color: #6b7280; }
.na-pagination   { display: flex; gap: 4px; }
.na-page-btn {
  width: 26px; height: 26px; border-radius: 6px; border: none;
  background: #f1f5f9; color: #6b7280;
  font-size: 11px; cursor: pointer; transition: background .15s;
  display: flex; align-items: center; justify-content: center;
}
.na-page-btn-active          { background: #2563eb; color: #fff; }
.na-page-btn:hover:not(.na-page-btn-active) { background: #e2e8f0; }

/* ── Responsive: tablet (≤1024px) ──────────────────────────────────── */
@media (max-width: 1024px) {
  .na-stat-grid { grid-template-columns: repeat(3, 1fr); }
  .na-meta-row  { grid-template-columns: repeat(3, 1fr); }
  .na-meta-item:nth-child(3) { border-right: none; }
  .na-meta-item:nth-child(4) { border-top: 1px solid #e5e7eb; }
  .na-meta-item:nth-child(5) { border-top: 1px solid #e5e7eb; border-right: none; }
}

/* ── Responsive: small tablet (≤768px) ─────────────────────────────── */
@media (max-width: 768px) {
  .na-body   { padding: 16px 14px 36px; gap: 14px; }
  .na-navbar { padding: 12px 16px; }
  .na-navbar-sub { display: none; }

  .na-stat-grid  { grid-template-columns: repeat(2, 1fr); }
  .na-two-col    { grid-template-columns: 1fr; }
  .na-meta-row   { grid-template-columns: repeat(2, 1fr); }
  .na-meta-item  { border-right: 1px solid #e5e7eb; }
  .na-meta-item:nth-child(2n) { border-right: none; }
  .na-meta-item:nth-child(n+3) { border-top: 1px solid #e5e7eb; }
  .na-meta-item:nth-child(3)   { border-right: 1px solid #e5e7eb; }
  .na-meta-item:nth-child(5)   { border-right: none; }

  .na-gm-stats { grid-template-columns: repeat(3, 1fr); }
  .na-dist-svg { width: 120px; }
}

/* ── Responsive: mobile (≤480px) ───────────────────────────────────── */
@media (max-width: 480px) {
  .na-navbar-right .na-navbar-date { display: none; }
  .na-stat-grid   { grid-template-columns: 1fr 1fr; }
  .na-gm-stats    { grid-template-columns: 1fr; }
  .na-close-banner { flex-direction: column; align-items: flex-start; }
  .na-close-banner-right { align-self: flex-end; }
  .na-stat-value  { font-size: 18px; }
  .na-pm-label    { width: 80px; }
  .na-room-label  { width: 70px; }
}
</style>