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
        <button @click="closeDay" class="na-btn-close">Close Day</button>
        <div class="na-avatar">RP</div>
      </div>
    </header>

    <!-- ── Main Body ──────────────────────────────────────────────────── -->
    <main class="na-body">

      <!-- Close Day Banner (inside body) -->
      <div class="na-close-banner">
        <div class="na-close-banner-meta">
          <span class="na-meta-ts">{{ nowLabel }}</span>
        </div>
        <button @click="closeDay" class="na-btn-close-lg">Close Day</button>
      </div>

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

        <!-- ── Top Summary ──────────────────────────────────────────── -->
        <section class="na-section">
          <div class="na-section-header">
            <h2 class="na-section-title">Top Summary <span class="na-section-sub">glance</span></h2>
          </div>
          <div class="na-stat-grid">
            <div class="na-stat-card na-stat-dark">
              <p class="na-stat-label">Total Revenue Today</p>
              <p class="na-stat-value">{{ fmt(data.revenue.total_revenue) }}</p>
              <p class="na-stat-badge na-badge-green">+8.4% vs previous day</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Room Revenue</p>
              <p class="na-stat-value na-value-dark">{{ fmt(data.revenue.room_revenue) }}</p>
              <p class="na-stat-badge na-badge-blue">{{ roomRevPct }}% of total revenue</p>
            </div>
            <div class="na-stat-card">
              <p class="na-stat-label">Total Pending Payment</p>
              <p class="na-stat-value na-value-dark">{{ fmt(data.outstanding.total_outstanding) }}</p>
              <p class="na-stat-badge na-badge-red">{{ data.outstanding.guest_count }} open unsettled bills</p>
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
              <p class="na-stat-value na-value-dark">{{ data.outstanding.guest_count }}</p>
              <p class="na-stat-badge na-badge-red">Unsettled bills requiring follow-up</p>
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
          <section class="na-card na-card-critical">
            <h3 class="na-card-title na-title-red">Transaction Validation (Critical)</h3>
            <p class="na-card-sub na-sub-red">This section turns red because exceptions exist and require action before close of day.</p>

            <div class="na-critical-list">
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

            <!-- Distribution Chart (SVG bar chart) -->
            <div class="na-dist-section">
              <h4 class="na-pm-title">Distribution</h4>
              <div class="na-dist-chart">
                <svg viewBox="0 0 200 100" class="na-dist-svg">
                  <rect x="10"  y="10" width="35" height="75" fill="#3b82f6" rx="3"/>
                  <rect x="60"  y="55" width="35" height="30" fill="#22c55e" rx="3"/>
                  <rect x="110" y="72" width="35" height="13" fill="#f59e0b" rx="3"/>
                  <rect x="160" y="80" width="35" height="5"  fill="#ef4444" rx="3"/>
                </svg>
                <div class="na-dist-legend">
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-blue"></span> Occupied</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-green"></span> Vacant Clean</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-orange"></span> Vacant Dirty</div>
                  <div class="na-dist-legend-item"><span class="na-dot na-dot-red"></span> Out of Service</div>
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
                <p class="na-gm-value">{{ data.occupancy.noshows || 3 }}</p>
              </div>
            </div>

            <!-- Guest Flow Chart -->
            <div class="na-gf-section">
              <h4 class="na-pm-title">Guest Flow Chart</h4>
              <div class="na-gf-chart">
                <div class="na-gf-bars" v-for="(hr, i) in guestFlowHours" :key="hr">
                  <div class="na-gf-bar na-gf-arr" :style="{ height: gfArrival(i) + 'px' }"></div>
                  <div class="na-gf-bar na-gf-dep" :style="{ height: gfDeparture(i) + 'px' }"></div>
                  <div class="na-gf-bar na-gf-nos" :style="{ height: gfNoshows(i) + 'px' }"></div>
                  <span class="na-gf-label">{{ hr }}</span>
                </div>
              </div>
              <div class="na-legend" style="margin-top:8px;">
                <span class="na-dot na-dot-blue"></span><span class="na-legend-label">Arrivals</span>
                <span class="na-dot na-dot-green"></span><span class="na-legend-label">Departures</span>
                <span class="na-dot na-dot-red"></span><span class="na-legend-label">No-show</span>
              </div>
            </div>
          </section>
        </div>

        <!-- ── Guest Ledger ──────────────────────────────────────────── -->
        <section class="na-card">
          <div class="na-table-header">
            <div>
              <h3 class="na-card-title">Guest Ledger — Outstanding Balances</h3>
              <p class="na-card-sub">Guests with unpaid balances currently in house</p>
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

const router = useRouter()

const today = new Date().toISOString().slice(0, 10)
const auditDate = ref(today)
const roomSearch = ref('')
const roomStatusFilter = ref('')
const roomPage = ref(1)
const roomPageSize = 30

const nowLabel = computed(() => {
  return new Date().toLocaleString('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true
  }).replace(',', '')
})

const auditMeta = computed(() => [
  { label: 'Audit Date', value: auditDate.value },
  { label: 'Shift', value: 'Night Shift' },
  { label: 'Prepared By', value: 'Night Auditor' },
  { label: 'Scope', value: 'All Departments' },
  { label: 'Status', value: 'Audit Open' },
])

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

// ── Computed helpers ──────────────────────────────────────────────────────
const roomRevPct = computed(() => {
  if (!data.value) return 0
  return Math.round((data.value.revenue.room_revenue / data.value.revenue.total_revenue) * 100)
})

const revenueBars = computed(() => {
  if (!data.value) return []
  const max = data.value.revenue.total_revenue
  return [
    { label: 'Rooms', amount: data.value.revenue.room_revenue, pct: (data.value.revenue.room_revenue / max) * 100, color: '#3b82f6' },
    { label: 'POS',   amount: data.value.revenue.fnb_revenue,  pct: (data.value.revenue.fnb_revenue / max) * 100,  color: '#22c55e' },
    { label: 'Other', amount: data.value.revenue.other_revenue, pct: (data.value.revenue.other_revenue / max) * 100, color: '#f59e0b' },
  ]
})

const criticalItems = computed(() => {
  if (!data.value) return []
  return [
    { title: 'Unsettled Invoices', desc: `${data.value.outstanding.guest_count} guest folios remain open with pending settlement.`, count: data.value.outstanding.guest_count },
    { title: 'POS Orders Not Closed', desc: '5 draft or held POS bills are still open at shift end.', count: 5 },
    { title: 'Payment Unallocated', desc: '2 transfer payments have not been allocated to invoices.', count: 2 },
  ]
})

const roomStatusBars = computed(() => {
  if (!data.value) return []
  const occ = data.value.occupancy.occupied
  const total = data.value.occupancy.total_rooms
  const vacClean = Math.round(data.value.occupancy.vacant * 0.6)
  const vacDirty = Math.round(data.value.occupancy.vacant * 0.3)
  const oos = data.value.occupancy.vacant - vacClean - vacDirty
  const max = occ
  return [
    { label: 'Occupied',      count: occ,      pct: 100,                    color: '#3b82f6' },
    { label: 'Vacant Clean',  count: vacClean, pct: (vacClean / max) * 100, color: '#22c55e' },
    { label: 'Vacant Dirty',  count: vacDirty, pct: (vacDirty / max) * 100, color: '#f59e0b' },
    { label: 'Out of Service',count: oos,      pct: (oos / max) * 100,      color: '#ef4444' },
  ]
})

function paymentPct(amount) {
  if (!data.value) return 0
  return Math.round((amount / data.value.payments.total_collected) * 100)
}

function pmColor(method) {
  return { Cash: '#f87171', Transfer: '#fb923c', Card: '#60a5fa', 'Corporate Credit': '#4ade80' }[method] || '#9ca3af'
}

// Guest flow fake data
const guestFlowHours = ['8PM', '9PM', '10PM', '11PM', '12AM']
const arrData  = [8, 4, 5, 3, 1]
const depData  = [5, 6, 3, 2, 2]
const nosData  = [1, 1, 0, 1, 0]
const gfArrival   = i => arrData[i] * 4
const gfDeparture = i => depData[i] * 4
const gfNoshows   = i => nosData[i] * 4

// Room filtering
const filteredRoomsAll = computed(() => {
  if (!data.value) return []
  let list = data.value.room_status
  if (roomSearch.value) {
    const q = roomSearch.value.toLowerCase()
    list = list.filter(r =>
      r.room_number.toLowerCase().includes(q) ||
      r.room_type.toLowerCase().includes(q) ||
      (r.guest || '').toLowerCase().includes(q)
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

// Helpers
function fmt(amount) {
  return `₦${Number(amount || 0).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function roomStatusClass(s) {
  return { Occupied: 'pill-green', Vacant: 'pill-gray', Reserved: 'pill-blue', Maintenance: 'pill-red' }[s] || 'pill-gray'
}

function hkStatusClass(s) {
  return { Clean: 'pill-green-soft', Dirty: 'pill-yellow', 'In Progress': 'pill-blue-soft', Inspected: 'pill-purple' }[s] || 'pill-gray'
}

function closeDay() {
  // Emit or handle close day logic here
  alert('Closing Day…')
}
</script>

<style scoped>
/* ── Tokens ─────────────────────────────────────────────────────────── */
:root {
  --na-bg: #f3f4f6;
  --na-navbar-bg: #111827;
  --na-card-bg: #ffffff;
  --na-border: #e5e7eb;
  --na-text: #111827;
  --na-muted: #6b7280;
  --na-blue: #3b82f6;
  --na-green: #22c55e;
  --na-red: #ef4444;
  --na-orange: #f59e0b;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.night-audit-wrapper {
  font-family: 'DM Sans', 'Segoe UI', sans-serif;
  background: #f1f5f9;
  min-height: 100vh;
  color: var(--na-text);
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
}
.na-navbar-title { font-size: 17px; font-weight: 700; color: #f8fafc; letter-spacing: -.3px; }
.na-navbar-sub   { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.na-navbar-right { display: flex; align-items: center; gap: 14px; }
.na-navbar-date  { font-size: 11px; color: #94a3b8; }
.na-btn-close {
  background: #ef4444;
  color: #fff;
  border: none;
  padding: 7px 16px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.na-btn-close:hover { background: #dc2626; }
.na-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: #2563eb; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}

/* ── Body ───────────────────────────────────────────────────────────── */
.na-body { max-width: 1280px; margin: 0 auto; padding: 24px 24px 48px; display: flex; flex-direction: column; gap: 18px; }

/* Close Banner */
.na-close-banner {
  background: #fff;
  border: 1px solid var(--na-border);
  border-radius: 12px;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.na-close-banner-meta { display: flex; align-items: center; gap: 8px; }
.na-meta-ts { font-size: 11px; color: var(--na-muted); }
.na-btn-close-lg {
  background: #ef4444;
  color: #fff;
  border: none;
  padding: 8px 22px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

/* Audit Meta Row */
.na-meta-row {
  background: #fff;
  border: 1px solid var(--na-border);
  border-radius: 12px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  divide-x: 1px solid var(--na-border);
}
.na-meta-item {
  padding: 14px 20px;
  border-right: 1px solid var(--na-border);
}
.na-meta-item:last-child { border-right: none; }
.na-meta-label { font-size: 10px; color: var(--na-muted); margin-bottom: 5px; }
.na-meta-value { font-size: 13px; font-weight: 600; color: var(--na-text); }

/* States */
.na-state-card { background: #fff; border-radius: 12px; border: 1px solid var(--na-border); padding: 48px; text-align: center; }
.na-state-text { font-size: 13px; color: var(--na-muted); }
.na-state-err  { color: #ef4444; }
.na-btn-retry  { margin-top: 10px; padding: 6px 16px; font-size: 12px; border: 1px solid #bfdbfe; color: #3b82f6; border-radius: 6px; background: #eff6ff; cursor: pointer; }

/* ── Section ─────────────────────────────────────────────────────────── */
.na-section { }
.na-section-header { margin-bottom: 12px; }
.na-section-title  { font-size: 15px; font-weight: 700; color: var(--na-text); }
.na-section-sub    { font-size: 12px; font-weight: 400; color: var(--na-muted); margin-left: 4px; }

/* ── Stat Grid ──────────────────────────────────────────────────────── */
.na-stat-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
.na-stat-card {
  background: #fff;
  border: 1px solid var(--na-border);
  border-radius: 12px;
  padding: 16px 18px;
}
.na-stat-dark { background: #1e293b; }
.na-stat-green-tint { background: #f0fdf4; }
.na-stat-label { font-size: 10px; color: var(--na-muted); margin-bottom: 8px; }
.na-stat-dark .na-stat-label { color: #94a3b8; }
.na-stat-value { font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: -.5px; }
.na-value-dark { color: var(--na-text); }
.na-stat-badge { font-size: 10px; margin-top: 6px; font-weight: 500; }
.na-badge-green { color: #16a34a; }
.na-badge-blue  { color: #2563eb; }
.na-badge-red   { color: #dc2626; }
.na-badge-gray  { color: var(--na-muted); }

/* ── Two-col layout ─────────────────────────────────────────────────── */
.na-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

/* ── Cards ──────────────────────────────────────────────────────────── */
.na-card {
  background: #fff;
  border: 1px solid var(--na-border);
  border-radius: 14px;
  padding: 20px 24px;
}
.na-card-critical { border-color: #fca5a5; background: #fff5f5; }
.na-card-title { font-size: 14px; font-weight: 700; color: var(--na-text); margin-bottom: 2px; }
.na-card-sub   { font-size: 11px; color: var(--na-muted); margin-bottom: 14px; }
.na-title-red  { color: #b91c1c; }
.na-sub-red    { color: #dc2626; }

/* Legend */
.na-legend { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.na-legend-label { font-size: 11px; color: var(--na-muted); margin-right: 6px; }
.na-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; }
.na-dot-blue   { background: #3b82f6; }
.na-dot-green  { background: #22c55e; }
.na-dot-orange { background: #f59e0b; }
.na-dot-red    { background: #ef4444; }

/* Revenue bars */
.na-bar-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.na-bar-row { display: flex; align-items: center; gap: 10px; }
.na-bar-label { font-size: 11px; color: var(--na-muted); width: 40px; flex-shrink: 0; }
.na-bar-track { flex: 1; height: 10px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.na-bar-fill  { height: 100%; border-radius: 99px; transition: width .4s ease; }
.na-bar-amt   { font-size: 11px; font-weight: 600; color: var(--na-text); width: 70px; text-align: right; flex-shrink: 0; }

/* Trend SVG */
.na-trend-label { font-size: 10px; color: var(--na-muted); margin-bottom: 4px; }
.na-trend-svg { width: 100%; height: 60px; margin-bottom: 16px; }

/* Payment methods */
.na-pm-section { border-top: 1px solid var(--na-border); padding-top: 14px; }
.na-pm-title { font-size: 12px; font-weight: 600; color: var(--na-text); margin-bottom: 10px; }
.na-pm-list { display: flex; flex-direction: column; gap: 8px; }
.na-pm-row { display: flex; align-items: center; gap: 10px; }
.na-pm-label { font-size: 11px; color: var(--na-muted); width: 110px; flex-shrink: 0; }
.na-pm-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.na-pm-fill  { height: 100%; border-radius: 99px; }
.na-pm-amt   { font-size: 11px; font-weight: 600; color: var(--na-text); width: 70px; text-align: right; flex-shrink: 0; }

/* Critical items */
.na-critical-list { display: flex; flex-direction: column; gap: 14px; margin-top: 6px; }
.na-critical-item {
  background: #fff;
  border: 1px solid #fca5a5;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.na-critical-left { display: flex; align-items: flex-start; gap: 10px; }
.na-critical-dot  { width: 10px; height: 10px; border-radius: 50%; background: #ef4444; flex-shrink: 0; margin-top: 3px; }
.na-critical-title { font-size: 12px; font-weight: 700; color: #b91c1c; }
.na-critical-desc  { font-size: 11px; color: #6b7280; margin-top: 2px; }
.na-critical-count {
  background: #fee2e2; color: #b91c1c;
  font-size: 12px; font-weight: 700;
  padding: 4px 12px; border-radius: 8px;
  flex-shrink: 0;
}

/* Room status bars */
.na-room-bars { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
.na-room-bar-row { display: flex; align-items: center; gap: 10px; }
.na-room-label { font-size: 11px; color: var(--na-muted); width: 90px; flex-shrink: 0; }
.na-room-track { flex: 1; height: 16px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.na-room-fill  { height: 100%; border-radius: 6px; }
.na-room-count { font-size: 11px; font-weight: 600; color: var(--na-text); width: 30px; text-align: right; flex-shrink: 0; }

/* Distribution chart */
.na-dist-section { border-top: 1px solid var(--na-border); padding-top: 14px; }
.na-dist-chart { display: flex; align-items: flex-end; gap: 16px; }
.na-dist-svg { width: 160px; height: 100px; }
.na-dist-legend { display: flex; flex-direction: column; gap: 6px; }
.na-dist-legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--na-muted); }

/* Guest movement */
.na-gm-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
.na-gm-stat { background: #f8fafc; border-radius: 10px; padding: 14px; border: 1px solid var(--na-border); }
.na-gm-label { font-size: 10px; color: var(--na-muted); margin-bottom: 6px; }
.na-gm-value { font-size: 26px; font-weight: 800; color: var(--na-text); }

/* Guest flow chart */
.na-gf-section { border-top: 1px solid var(--na-border); padding-top: 14px; }
.na-gf-chart { display: flex; align-items: flex-end; gap: 12px; height: 60px; margin-top: 10px; margin-bottom: 4px; }
.na-gf-bars { display: flex; align-items: flex-end; gap: 2px; flex-direction: column; position: relative; }
.na-gf-bar { width: 10px; border-radius: 3px 3px 0 0; }
.na-gf-arr { background: #3b82f6; }
.na-gf-dep { background: #22c55e; }
.na-gf-nos { background: #ef4444; }
.na-gf-label { font-size: 9px; color: var(--na-muted); margin-top: 4px; text-align: center; }

/* Tables */
.na-table-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; }
.na-table-wrap { overflow-x: auto; }
.na-table { width: 100%; border-collapse: collapse; }
.na-table thead tr { border-bottom: 1px solid var(--na-border); }
.na-table th { text-align: left; font-size: 11px; font-weight: 600; color: var(--na-muted); padding: 8px 14px; }
.na-table tbody tr { border-bottom: 1px solid #f8fafc; transition: background .1s; cursor: pointer; }
.na-table tbody tr:hover { background: #f8fafc; }
.na-table td { padding: 10px 14px; font-size: 12px; color: var(--na-muted); }
.na-th-right { text-align: right; }
.na-td-mono { font-family: monospace; }
.na-td-blue { color: #2563eb; }
.na-td-bold { font-weight: 600; color: var(--na-text); }
.na-td-right { text-align: right; }
.na-td-red  { color: #dc2626; font-weight: 700; }
.na-empty { padding: 32px; text-align: center; font-size: 12px; color: var(--na-muted); }

/* Badges / pills */
.na-badge-pill { padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; }
.na-badge-red-pill { background: #fee2e2; color: #dc2626; }

/* Status pills */
.na-status-pill { padding: 2px 9px; border-radius: 99px; font-size: 10px; font-weight: 600; }
.pill-green      { background: #dcfce7; color: #16a34a; }
.pill-gray       { background: #f3f4f6; color: #6b7280; }
.pill-blue       { background: #dbeafe; color: #2563eb; }
.pill-red        { background: #fee2e2; color: #dc2626; }
.pill-green-soft { background: #f0fdf4; color: #16a34a; }
.pill-yellow     { background: #fef9c3; color: #a16207; }
.pill-blue-soft  { background: #eff6ff; color: #3b82f6; }
.pill-purple     { background: #f5f3ff; color: #7c3aed; }

/* Filters */
.na-filter-row { display: flex; gap: 8px; }
.na-input, .na-select {
  padding: 6px 12px; font-size: 11px;
  border: 1px solid var(--na-border);
  border-radius: 8px; outline: none;
  color: var(--na-text);
  background: #fff;
}
.na-input:focus, .na-select:focus { border-color: #3b82f6; }

/* Pagination */
.na-table-footer { padding: 12px 14px; border-top: 1px solid var(--na-border); display: flex; align-items: center; justify-content: space-between; }
.na-footer-info { font-size: 11px; color: var(--na-muted); }
.na-pagination { display: flex; gap: 4px; }
.na-page-btn {
  width: 26px; height: 26px; border-radius: 6px; border: none;
  background: #f1f5f9; color: var(--na-muted);
  font-size: 11px; cursor: pointer; transition: background .15s;
  display: flex; align-items: center; justify-content: center;
}
.na-page-btn-active { background: #2563eb; color: #fff; }
.na-page-btn:hover:not(.na-page-btn-active) { background: #e2e8f0; }
</style>