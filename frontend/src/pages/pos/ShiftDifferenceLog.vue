<template>
  <div class="page-wrap">
    <div class="breadcrumb">Point of Sale / <span class="bc-current">Shift Difference Log</span></div>
    <div class="page-content">
      <h1 class="page-title">Shift Difference Log</h1>
      <p class="page-desc">Track cashier and terminal differences by shift, review exceptions, monitor pending investigations, and confirm final resolutions.</p>

      <!-- Overview -->
      <div class="section-card" style="margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div class="section-card-title">Difference Overview</div>
            <div class="section-card-sub" v-if="summary.total_cases">
              {{ summary.total_cases }} logged cases •
              {{ summary.pending_count || 0 }} pending review •
              {{ summary.escalated_count || 0 }} escalated •
              {{ summary.resolved_count || 0 }} resolved
            </div>
            <div class="section-card-sub" v-else>No difference records found</div>
          </div>
          <button class="btn-outline" @click="fetchLog">Refresh</button>
        </div>
      </div>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;">
        <div class="stat-card">
          <div class="stat-label">Total Difference <span class="badge-month">All Time</span></div>
          <div class="stat-value">{{ fmt(summary.total_amount) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Pending Reviews <span class="badge-open">Open</span></div>
          <div class="stat-value">{{ summary.pending_count || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Resolved Cases <span class="badge-closed">Closed</span></div>
          <div class="stat-value">{{ summary.resolved_count || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Escalated Cases <span class="badge-review-b">Escalated</span></div>
          <div class="stat-value">{{ summary.escalated_count || 0 }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="section-card" style="margin-bottom:20px;">
        <div class="inner-section-title">Filters & Search</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;align-items:flex-end;">
          <div>
            <div class="filter-label">Search log</div>
            <input class="search-input" placeholder="Shift ID, cashier, terminal..." v-model="searchText" />
          </div>
          <div>
            <div class="filter-label">Date From</div>
            <input type="date" class="filter-select" v-model="filterDateFrom" />
          </div>
          <div>
            <div class="filter-label">Date To</div>
            <input type="date" class="filter-select" v-model="filterDateTo" />
          </div>
          <div>
            <div class="filter-label">Terminal</div>
            <select class="filter-select" v-model="filterTerminal">
              <option value="">All Terminals</option>
              <option v-for="t in terminals" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <div class="filter-label">Status</div>
            <select class="filter-select" v-model="filterStatus">
              <option value="">All Statuses</option>
              <option>Pending Review</option>
              <option>Under Review</option>
              <option>Resolved</option>
              <option>Escalated</option>
            </select>
          </div>
          <button class="btn-outline" @click="resetFilters">Reset</button>
          <button class="btn-primary" @click="fetchLog">Apply Filter</button>
        </div>
      </div>

      <!-- Loading / Empty -->
      <div v-if="loading" style="text-align:center;padding:40px;color:#64748b;">Loading…</div>
      <div v-else-if="filteredRecords.length === 0" style="text-align:center;padding:40px;color:#94a3b8;font-size:13px;">
        No shift differences found{{ hasActiveFilters ? ' for the selected filters' : '' }}.
      </div>
      <div v-else style="display:grid;grid-template-columns:1fr 340px;gap:16px;">
        <!-- Records Table -->
        <div class="section-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
            <div class="inner-section-title">Difference Records</div>
            <div style="font-size:12px;color:#64748b;">{{ filteredRecords.length }} record{{ filteredRecords.length === 1 ? '' : 's' }}</div>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Shift ID</th>
                <th>Date</th>
                <th>Terminal / Cashier</th>
                <th>Difference</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in paginatedRecords"
                :key="r.name"
                :class="['record-row', { selected: selectedName === r.name }]"
                @click="selectRecord(r)"
              >
                <td>
                  <div style="font-weight:600;font-size:13px;">{{ r.name }}</div>
                  <div style="font-size:11px;color:#64748b;">{{ fmtDate(r.period_start_date) }}</div>
                </td>
                <td>{{ r.posting_date }}</td>
                <td>
                  <div style="font-weight:500;">{{ r.pos_profile }}</div>
                  <div style="font-size:12px;color:#64748b;">{{ r.user }}</div>
                </td>
                <td><span style="color:#dc2626;font-weight:600;">{{ fmt(r.total_difference) }}</span></td>
                <td><span :class="diffStatusClass(r.status)">{{ r.status }}</span></td>
              </tr>
            </tbody>
          </table>
          <div class="pagination-bar" v-if="totalPages > 1">
            <span style="font-size:12px;color:#64748b;">Page {{ currentPage }} of {{ totalPages }}</span>
            <div style="display:flex;align-items:center;gap:6px;">
              <span v-for="p in totalPages" :key="p" :class="['page-num', { active: currentPage===p }]" @click="currentPage=p">{{ p }}</span>
            </div>
          </div>
        </div>

        <!-- Detail Panel -->
        <div class="section-card" v-if="selected">
          <div class="inner-section-title">Selected Entry</div>
          <div class="detail-row"><span class="detail-label">Reference</span><span class="detail-val">{{ selected.name }}</span></div>
          <div class="detail-row"><span class="detail-label">Terminal</span><span class="detail-val">{{ selected.pos_profile }}</span></div>
          <div class="detail-row"><span class="detail-label">Cashier</span><span class="detail-val"><strong>{{ selected.user }}</strong></span></div>
          <div class="detail-row"><span class="detail-label">Date</span><span class="detail-val">{{ selected.posting_date }}</span></div>
          <div class="detail-row"><span class="detail-label">Total Difference</span><span style="color:#dc2626;font-weight:700;">{{ fmt(selected.total_difference) }}</span></div>
          <div class="detail-row"><span class="detail-label">Status</span><span :class="diffStatusClass(selected.status)">{{ selected.status }}</span></div>

          <div style="margin-top:14px;" v-if="breakdownParts.length">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Breakdown by Payment Method</div>
            <div style="font-size:12px;color:#64748b;background:#f8fafc;border-radius:7px;padding:10px;line-height:1.8;">
              <div v-for="part in breakdownParts" :key="part">{{ part }}</div>
            </div>
          </div>

          <div style="margin-top:14px;" v-if="selected.note">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Review Note</div>
            <div style="font-size:12px;color:#64748b;background:#f8fafc;border-radius:7px;padding:10px;line-height:1.6;">{{ selected.note }}</div>
          </div>

          <div style="margin-top:14px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Update Status</div>
            <select class="filter-select" v-model="editStatus" style="width:100%;margin-bottom:8px;">
              <option>Pending Review</option>
              <option>Under Review</option>
              <option>Resolved</option>
              <option>Escalated</option>
            </select>
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Add / Update Note</div>
            <textarea class="note-area" v-model="editNote" placeholder="Add follow-up note, action owner, or final resolution summary..."></textarea>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;">
            <button class="btn-outline" @click="selectedName = null">Close</button>
            <button class="btn-primary" @click="saveReview" :disabled="savingReview" style="flex:1;">
              {{ savingReview ? 'Saving…' : 'Save Review' }}
            </button>
          </div>
          <div v-if="saveError" style="color:#dc2626;font-size:12px;margin-top:6px;">{{ saveError }}</div>
        </div>
        <div class="section-card" v-else style="display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:13px;">
          Select a record to view details
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const loading = ref(false)
const records = ref([])
const terminals = ref([])
const summary = ref({})
const searchText = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterTerminal = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = 10
const selectedName = ref(null)
const editStatus = ref('')
const editNote = ref('')
const savingReview = ref(false)
const saveError = ref('')

async function fetchLog() {
  loading.value = true
  try {
    const res = await callMethod('rhohotel.rhocom_hotel.api.pos.get_shift_difference_log', {
      date_from: filterDateFrom.value || null,
      date_to: filterDateTo.value || null,
      terminal: filterTerminal.value || null,
      status: filterStatus.value || null,
      page_length: 200,
      start: 0,
    })
    records.value = res.rows || []
    terminals.value = res.terminals || []
    summary.value = res.summary || {}
  } catch (e) {
    console.error('Failed to load shift difference log', e)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  searchText.value = ''
  filterDateFrom.value = ''
  filterDateTo.value = ''
  filterTerminal.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  fetchLog()
}

const hasActiveFilters = computed(() =>
  !!(searchText.value || filterDateFrom.value || filterDateTo.value || filterTerminal.value || filterStatus.value)
)

const filteredRecords = computed(() => {
  const q = searchText.value.toLowerCase()
  if (!q) return records.value
  return records.value.filter(r =>
    (r.name || '').toLowerCase().includes(q) ||
    (r.pos_profile || '').toLowerCase().includes(q) ||
    (r.user || '').toLowerCase().includes(q)
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize)))
const paginatedRecords = computed(() =>
  filteredRecords.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize)
)

const selected = computed(() => records.value.find(r => r.name === selectedName.value) || null)

const breakdownParts = computed(() => {
  if (!selected.value?.difference_breakdown) return []
  return selected.value.difference_breakdown.split(' | ')
})

function selectRecord(r) {
  selectedName.value = r.name
  editStatus.value = r.status || 'Pending Review'
  editNote.value = r.note || ''
  saveError.value = ''
}

async function saveReview() {
  if (!selected.value) return
  savingReview.value = true
  saveError.value = ''
  try {
    await callMethod('rhohotel.rhocom_hotel.api.pos.update_shift_difference_status', {
      closing_entry: selected.value.name,
      status: editStatus.value,
      note: editNote.value,
    })
    const rec = records.value.find(r => r.name === selected.value.name)
    if (rec) {
      rec.status = editStatus.value
      rec.note = editNote.value
    }
    fetchLog()
  } catch (e) {
    saveError.value = e.message || 'Failed to save review'
  } finally {
    savingReview.value = false
  }
}

function diffStatusClass(s) {
  if (s === 'Resolved') return 'badge-resolved'
  if (s === 'Under Review') return 'badge-under-review'
  if (s === 'Escalated') return 'badge-escalated'
  return 'badge-pending'
}

function fmt(val) {
  const n = parseFloat(val) || 0
  return '₦' + n.toLocaleString('en-NG', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function fmtDate(val) {
  if (!val) return ''
  try { return new Date(val).toLocaleString('en-NG', { dateStyle: 'medium', timeStyle: 'short' }) } catch (_) { return val }
}

onMounted(fetchLog)
</script>

<style scoped>
.page-wrap { background: #f1f5f9; min-height: 100vh; font-family: 'DM Sans', sans-serif; }
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
.filter-select { border: 1px solid #e2e8f0; border-radius: 7px; padding: 7px 10px; font-size: 13px; background: white; cursor: pointer; outline: none; min-width: 140px; }
.btn-outline { background: white; border: 1px solid #d1d5db; color: #374151; padding: 7px 14px; border-radius: 7px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-primary { background: #1d4ed8; color: white; border: none; padding: 7px 14px; border-radius: 7px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; color: #64748b; font-weight: 500; padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 12px; }
.data-table td { padding: 11px 10px; border-bottom: 1px solid #f8fafc; color: #1e293b; }
.record-row { cursor: pointer; transition: background 0.1s; }
.record-row:hover { background: #f8fafc; }
.record-row.selected { background: #eff6ff; }
.badge-resolved { background: #dcfce7; color: #166534; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-under-review { background: #fef9c3; color: #854d0e; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-escalated { background: #fee2e2; color: #991b1b; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-pending { background: #f1f5f9; color: #475569; font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid #f8fafc; font-size: 13px; }
.detail-label { color: #64748b; }
.detail-val { color: #0f172a; font-weight: 500; }
.note-area { width: 100%; border: 1px solid #e2e8f0; border-radius: 7px; padding: 9px 12px; font-size: 12px; resize: none; height: 80px; outline: none; font-family: inherit; color: #374151; box-sizing: border-box; }
.pagination-bar { display: flex; justify-content: space-between; align-items: center; padding-top: 14px; margin-top: 6px; border-top: 1px solid #f1f5f9; }
.page-num { width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-size: 13px; cursor: pointer; color: #374151; }
.page-num.active { background: #1d4ed8; color: white; font-weight: 600; }
</style>
