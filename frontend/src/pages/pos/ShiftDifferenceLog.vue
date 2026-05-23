<template>
  <div class="page-wrap">
    <!-- <div class="page-topbar">
      <div>
        <div class="topbar-title">Shift Difference Log</div>
        <div class="topbar-sub">Point of sale • difference history, reviews and resolutions</div>
      </div>
      <div class="topbar-actions">
        <span class="bell-icon">🔔</span>
        <span class="avatar-badge">AD</span>
      </div>
    </div> -->

    <div class="breadcrumb">Point of Sale / <span class="bc-current">Shift Difference Log</span></div>
    <div class="page-content">
      <h1 class="page-title">Shift Difference Log</h1>
      <p class="page-desc">Track cashier and terminal differences by shift, review exceptions, monitor pending investigations, and confirm final resolutions.</p>

      <!-- Overview -->
      <div class="section-card" style="margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div class="section-card-title">Difference Overview</div>
            <div class="section-card-sub">27 logged cases this month • 4 pending review • 2 escalated • 21 resolved</div>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-outline">Refresh</button>
            <button class="btn-outline-blue">Export Log</button>
            <button class="btn-primary" @click="showReviewDifference = true">New Review Entry</button>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;">
        <div class="stat-card"><div class="stat-label">Total Difference Amount <span class="badge-month">This Month</span></div><div class="stat-value">₦382,900</div></div>
        <div class="stat-card"><div class="stat-label">Pending Reviews <span class="badge-open">Open</span></div><div class="stat-value">4</div></div>
        <div class="stat-card"><div class="stat-label">Resolved Cases <span class="badge-closed">Closed</span></div><div class="stat-value">21</div></div>
        <div class="stat-card"><div class="stat-label">Largest Single Difference <span class="badge-review-b">Review</span></div><div class="stat-value">₦41,300</div></div>
      </div>

      <!-- Filters + Table + Detail Panel -->
      <div class="section-card" style="margin-bottom:20px;">
        <div class="inner-section-title">Filters & Search</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;align-items:flex-end;">
          <div>
            <div class="filter-label">Search log</div>
            <input class="search-input" placeholder="Shift, cashier, terminal, note..." v-model="searchText" />
          </div>
          <div>
            <div class="filter-label">Terminal</div>
            <select class="filter-select" v-model="filterTerminal">
              <option value="">All Terminals</option>
              <option>Restaurant POS 01</option>
              <option>Bar POS 02</option>
              <option>Mini-Mart POS 03</option>
            </select>
          </div>
          <div>
            <div class="filter-label">Status</div>
            <select class="filter-select" v-model="filterStatus">
              <option value="">All Statuses</option>
              <option>Under Review</option>
              <option>Resolved</option>
              <option>Escalated</option>
            </select>
          </div>
          <div>
            <div class="filter-label">Shift</div>
            <select class="filter-select" v-model="filterShift">
              <option value="">All Shifts</option>
              <option>Morning</option>
              <option>Evening</option>
              <option>Night</option>
            </select>
          </div>
          <button class="btn-outline">Reset</button>
          <button class="btn-primary">Apply Filter</button>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
        <!-- Records Table -->
        <div class="section-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
            <div class="inner-section-title">Difference Records</div>
            <div style="font-size:12px;color:#64748b;">Showing 1–6 of 27 logged cases</div>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Ref No.</th>
                <th>Date</th>
                <th>Terminal / Cashier</th>
                <th>Difference</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in paginatedRecords" :key="r.ref" :class="['record-row', { selected: selectedRef === r.ref }]" @click="selectRecord(r)">
                <td>
                  <div style="font-weight:600;font-size:13px;">{{ r.ref }}</div>
                  <div style="font-size:11px;color:#64748b;">{{ r.shift }}</div>
                </td>
                <td>{{ r.date }}</td>
                <td>
                  <div style="font-weight:500;">{{ r.terminal }}</div>
                  <div style="font-size:12px;color:#64748b;">{{ r.cashier }}</div>
                </td>
                <td><span style="color:#dc2626;font-weight:600;">{{ r.difference }}</span></td>
                <td><span :class="diffStatusClass(r.status)">{{ r.status }}</span></td>
              </tr>
            </tbody>
          </table>
          <div class="pagination-bar">
            <span style="font-size:12px;color:#64748b;">Rows per page: 10</span>
            <div style="display:flex;align-items:center;gap:6px;">
              <span v-for="p in totalPages" :key="p" :class="['page-num', { active: currentPage===p }]" @click="currentPage=p">{{ p }}</span>
              <span style="color:#64748b;font-size:13px;">...</span>
              <span class="page-num">5</span>
              <button class="btn-outline" style="padding:4px 12px;">Next</button>
            </div>
          </div>
        </div>

        <!-- Selected Entry Detail Panel -->
        <div class="section-card" v-if="selected">
          <div class="inner-section-title">Selected Entry</div>
          <div class="detail-row"><span class="detail-label">Reference</span><span class="detail-val">{{ selected.ref }}</span></div>
          <div class="detail-row"><span class="detail-label">Terminal</span><span class="detail-val">{{ selected.terminal }}</span></div>
          <div class="detail-row"><span class="detail-label">Cashier</span><span class="detail-val"><strong>{{ selected.cashier }}</strong></span></div>
          <div class="detail-row"><span class="detail-label">Difference</span><span style="color:#dc2626;font-weight:700;">{{ selected.difference }}</span></div>
          <div class="detail-row"><span class="detail-label">Status</span><span :class="diffStatusClass(selected.status)">{{ selected.status }}</span></div>
          <div style="margin-top:14px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Latest Review Note</div>
            <div style="font-size:12px;color:#64748b;background:#f8fafc;border-radius:7px;padding:10px;line-height:1.6;">{{ selected.note }}</div>
          </div>
          <div style="margin-top:14px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Manager Comment</div>
            <textarea class="note-area" placeholder="Add follow-up note, action owner, or final resolution summary..."></textarea>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;">
            <button class="btn-outline">Close</button>
            <button class="btn-outline-blue">Export Entry</button>
          </div>
          <button class="btn-primary-full" @click="showReviewDifference = true">Open Review Popup</button>
        </div>
        <div class="section-card" v-else style="display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:13px;">
          Select a record to view details
        </div>
      </div>
    </div>

    <ReviewDifferenceModal v-if="showReviewDifference" @close="showReviewDifference = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ReviewDifferenceModal from '@/components/pos/ReviewDifferenceModal.vue'


const showReviewDifference = ref(false)
const searchText = ref('')
const filterTerminal = ref('')
const filterStatus = ref('')
const filterShift = ref('')
const currentPage = ref(1)
const pageSize = 6
const selectedRef = ref('DIF-2026-0415-03')

const records = [
  { ref: 'DIF-2026-0415-03', shift: 'Morning shift', date: '15 Apr 2026', terminal: 'Mini-Mart POS 03', cashier: 'Boma', difference: '₦41,300', status: 'Under Review', note: 'Cash drawer count was below system total after midday float adjustment. Waiting for cashier explanation and supporting evidence.' },
  { ref: 'DIF-2026-0414-02', shift: 'Evening shift', date: '14 Apr 2026', terminal: 'Bar POS 02', cashier: 'Ifeoma', difference: '₦18,000', status: 'Resolved', note: 'Float replenishment error identified. Adjustment journal posted.' },
  { ref: 'DIF-2026-0413-01', shift: 'Morning shift', date: '13 Apr 2026', terminal: 'Restaurant POS 01', cashier: 'Adaeze', difference: '₦9,500', status: 'Escalated', note: 'Discrepancy linked to voided invoice not captured in end-of-day report.' },
  { ref: 'DIF-2026-0412-02', shift: 'Night shift', date: '12 Apr 2026', terminal: 'Mini-Mart POS 03', cashier: 'Boma', difference: '₦3,200', status: 'Resolved', note: 'Resolved by supervisor. Change error corrected.' },
  { ref: 'DIF-2026-0411-01', shift: 'Morning shift', date: '11 Apr 2026', terminal: 'Restaurant POS 01', cashier: 'Adaeze', difference: '₦5,100', status: 'Resolved', note: 'Overcharge reversed, customer refunded.' },
  { ref: 'DIF-2026-0410-02', shift: 'Evening shift', date: '10 Apr 2026', terminal: 'Bar POS 02', cashier: 'Ifeoma', difference: '₦2,750', status: 'Resolved', note: 'Reconciled successfully during shift handover.' },
  { ref: 'DIF-2026-0409-01', shift: 'Morning shift', date: '9 Apr 2026', terminal: 'Restaurant POS 01', cashier: 'Adaeze', difference: '₦11,200', status: 'Escalated', note: 'Under investigation — senior manager reviewing CCTV.' },
]

const totalPages = computed(() => Math.ceil(records.length / pageSize))
const paginatedRecords = computed(() => records.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const selected = computed(() => records.find(r => r.ref === selectedRef.value) || null)

function selectRecord(r) { selectedRef.value = r.ref }

function diffStatusClass(s) {
  if (s === 'Resolved') return 'badge-resolved'
  if (s === 'Under Review') return 'badge-under-review'
  if (s === 'Escalated') return 'badge-escalated'
  return 'badge-gray'
}
</script>

<style scoped>
.page-wrap { background: #f1f5f9; min-height: 100vh; font-family: 'DM Sans', sans-serif; }
.page-topbar { background: #0f172a; color: white; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; }
.topbar-title { font-size: 18px; font-weight: 600; }
.topbar-sub { font-size: 12px; color: #94a3b8; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.bell-icon { font-size: 18px; }
.avatar-badge { background: #22c55e; color: white; border-radius: 50%; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; }
.breadcrumb { padding: 10px 24px; font-size: 13px; color: #64748b; }
.bc-current { font-weight: 500; color: #1e293b; }
.page-content { padding: 0 24px 32px; }
.page-title { font-size: 26px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
.page-desc { font-size: 13px; color: #64748b; margin-bottom: 20px; }
.section-card { background: white; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.section-card-title { font-size: 15px; font-weight: 600; color: #0f172a; }
.section-card-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.inner-section-title { font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 4px; }
.filter-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.stat-card { background: white; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.stat-label { font-size: 12px; color: #64748b; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.stat-value { font-size: 28px; font-weight: 700; color: #0f172a; }
.badge-month { background: #dbeafe; color: #1e40af; font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; }
.badge-open { background: #fef9c3; color: #854d0e; font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; }
.badge-closed { background: #dcfce7; color: #166534; font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; }
.badge-review-b { background: #fee2e2; color: #991b1b; font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; }
.search-input { border: 1px solid #e2e8f0; border-radius: 7px; padding: 7px 12px; font-size: 13px; min-width: 200px; outline: none; }
.filter-select { border: 1px solid #e2e8f0; border-radius: 7px; padding: 7px 28px 7px 10px; font-size: 13px; background: white; cursor: pointer; outline: none; min-width: 140px; }
.btn-outline { background: white; border: 1px solid #d1d5db; color: #374151; padding: 7px 14px; border-radius: 7px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-outline-blue { background: white; border: 1px solid #3b82f6; color: #3b82f6; padding: 7px 14px; border-radius: 7px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-primary { background: #1d4ed8; color: white; border: none; padding: 7px 14px; border-radius: 7px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-primary-full { background: #1d4ed8; color: white; border: none; padding: 11px; border-radius: 8px; font-size: 13px; cursor: pointer; font-weight: 600; width: 100%; margin-top: 10px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; color: #64748b; font-weight: 500; padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 12px; }
.data-table td { padding: 11px 10px; border-bottom: 1px solid #f8fafc; color: #1e293b; }
.record-row { cursor: pointer; transition: background 0.1s; }
.record-row:hover { background: #f8fafc; }
.record-row.selected { background: #eff6ff; }
.badge-resolved { background: #dcfce7; color: #166534; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-under-review { background: #fef9c3; color: #854d0e; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-escalated { background: #fee2e2; color: #991b1b; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-gray { background: #f1f5f9; color: #475569; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid #f8fafc; font-size: 13px; }
.detail-label { color: #64748b; }
.detail-val { color: #0f172a; font-weight: 500; }
.note-area { width: 100%; border: 1px solid #e2e8f0; border-radius: 7px; padding: 9px 12px; font-size: 12px; resize: none; height: 80px; outline: none; font-family: inherit; color: #374151; }
.pagination-bar { display: flex; justify-content: space-between; align-items: center; padding-top: 14px; margin-top: 6px; border-top: 1px solid #f1f5f9; }
.page-num { width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-size: 13px; cursor: pointer; color: #374151; }
.page-num.active { background: #1d4ed8; color: white; font-weight: 600; }
</style>