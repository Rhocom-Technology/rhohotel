<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Review sales, reconcile cash and non-cash collections, confirm differences, and close the active POS terminal shift.</p>
    </div>

    <!-- Active Terminal -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Active Terminal</h3>
        <p class="text-xs text-gray-400 mt-0.5">{{ shiftStats.pos_profile }} • Cashier: {{ shiftStats.cashier }} • {{ shiftStats.shift_date }}</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="printShiftReport" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print Report</button>
        <button @click="showDraftOrders = true" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Open Drafts</button>
        <!-- <button @click="router.push('/pos')" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Open Drafts</button> -->
        <button @click="confirmClose" :disabled="closing"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {{ closing ? 'Closing…' : 'Close Shift Now' }}
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Gross Sales</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦{{ shiftResource.loading ? '…' : Number(shiftStats.gross_sales).toLocaleString() }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Net Collections</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Cleared</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦{{ shiftResource.loading ? '…' : Number(shiftStats.net_collections).toLocaleString() }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Bills / Drafts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Check</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ shiftResource.loading ? '…' : shiftStats.open_drafts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Difference</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦{{ shiftResource.loading ? '…' : Number(shiftStats.difference).toLocaleString() }}</p>
      </div>
    </div>

    <!-- Body grid -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;align-items:start;">

      <!-- Left: Shift Reconciliation -->
      <div class="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
        <h3 class="text-sm font-bold text-gray-900">Shift Reconciliation</h3>

        <!-- Shift info -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Shift Date</p>
            <div class="px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-700 bg-gray-50">{{ shiftStats.shift_date || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Shift</p>
            <div class="px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-700 bg-gray-50">{{ shiftStats.pos_profile || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Opened By</p>
            <div class="px-3 py-2.5 border border-blue-200 bg-blue-50 rounded-lg text-xs font-medium text-blue-700">{{ shiftStats.cashier || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Closing Time</p>
            <div class="px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-700 bg-gray-50">{{ currentTime }}</div>
          </div>
        </div>

        <!-- Tender breakdown -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 mb-3">Tender Breakdown</h4>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 pb-2 pr-4">Payment Type</th>
                <th class="text-left text-xs font-medium text-blue-600 pb-2 pr-4">System Amount</th>
                <th class="text-left text-xs font-medium text-blue-600 pb-2 pr-4">Counted Amount</th>
                <th class="text-left text-xs font-medium text-blue-600 pb-2">Difference</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="row in tenderRows" :key="row.type">
                <td class="py-3 pr-4 text-xs font-medium text-gray-900">{{ row.type }}</td>
                <td class="py-3 pr-4 text-xs text-gray-700">₦{{ row.system.toLocaleString() }}</td>
                <td class="py-3 pr-4">
                  <input v-if="row.editable" v-model="row.counted" type="text"
                    class="px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-36" />
                  <div v-else class="px-3 py-1.5 text-xs border border-gray-100 rounded-lg bg-gray-50 text-gray-400 w-36">Auto from system</div>
                </td>
                <td class="py-3 text-xs font-medium" :class="getDiff(row) === 0 ? 'text-green-600' : 'text-red-500'">{{ getDiff(row) === 0 ? '₦0.00' : (getDiff(row) > 0 ? '+₦' : '-₦') + Math.abs(getDiff(row)).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Closing note -->
        <div>
          <p class="text-xs font-semibold text-gray-700 mb-2">Closing Note / Difference Remark</p>
          <textarea v-model="closingNote" rows="4"
            placeholder="Enter closing note, explain any difference, record handover details, or mention unresolved draft orders..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <!-- Attachment -->
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">
          Add Attachment
        </button>
      </div>

      <!-- Right: Closing Summary -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h3 class="text-sm font-bold text-gray-900">Closing Summary</h3>

          <!-- Sales Performance -->
          <div class="bg-gray-50 rounded-lg border border-gray-100 p-4">
            <h4 class="text-xs font-bold text-gray-900 mb-3">Sales Performance</h4>
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-gray-500">Bills processed</span>
              <span class="font-semibold text-gray-900">{{ shiftResource.loading ? '…' : (shiftStats.bills_processed || 0) }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">Voids / cancellations</span>
              <span class="font-semibold text-gray-900">{{ shiftResource.loading ? '…' : (shiftStats.voided_count || 0) }}</span>
            </div>
          </div>

          <!-- Open Items -->
          <div class="bg-gray-50 rounded-lg border border-gray-100 p-4">
            <h4 class="text-xs font-bold text-gray-900 mb-3">Open Items Before Closing</h4>
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-gray-500">Draft orders</span>
              <span class="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-600 rounded-full">{{ shiftStats.open_drafts }} pending</span>
            </div>
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-gray-500">Open tables</span>
              <span class="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-600 rounded-full">{{ shiftStats.open_tables ?? 0 }} active</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">Unposted room charges</span>
              <span class="font-semibold text-gray-900">0</span>
            </div>
          </div>

          <!-- Cash Declaration -->
          <div class="bg-gray-50 rounded-lg border border-gray-100 p-4">
            <h4 class="text-xs font-bold text-gray-900 mb-3">Cash Declaration</h4>
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-gray-500">Opening float</span>
              <span class="font-semibold text-gray-900">₦{{ Number(shiftStats.opening_cash || 0).toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">Expected cash in drawer</span>
              <span class="font-semibold text-gray-900">₦{{ Number((shiftStats.opening_cash || 0) + (shiftStats.gross_sales || 0)).toLocaleString() }}</span>
            </div>
          </div>

          <!-- Closing Status -->
          <div class="bg-gray-50 rounded-lg border border-gray-100 p-4">
            <h4 class="text-xs font-bold text-gray-900 mb-1.5">Closing Status</h4>
            <p class="text-xs text-gray-500">All counted amounts match the system values.</p>
          </div>

          <button @click="printShiftReport" class="w-full py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">
            Preview Report
          </button>
        </div>
      </div>
    </div>

    <DraftOrdersModal v-model="showDraftOrders" />

    <!-- Confirm close modal -->
    <div v-if="showConfirm" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.5);">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h3 class="text-sm font-bold text-gray-900 mb-2">Close Shift?</h3>
        <p class="text-xs text-gray-500 mb-5">This will close the {{ shiftStats.pos_profile }} shift for {{ shiftStats.cashier }}. This action cannot be undone.</p>
        <p v-if="closeError" class="text-xs text-red-500 mt-2 mb-3 bg-red-50 border border-red-200 rounded px-3 py-2">{{ closeError }}</p>
        <div class="flex gap-2">
          <button @click="showConfirm = false" class="flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="doCloseShift" :disabled="closing"
            class="flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {{ closing ? 'Closing…' : 'Confirm Close' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'

const router = useRouter()
const showDraftOrders = ref(false)
const closingNote = ref('')
const showConfirm = ref(false)
const closing = ref(false)
const closeError = ref('')
const now = ref(new Date())

let timer
onMounted(() => { timer = setInterval(() => { now.value = new Date() }, 1000) })
onUnmounted(() => clearInterval(timer))

const currentTime = computed(() =>
  now.value.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
)

// ── API: Shift Stats ─────────────────────────────────────────────────
const shiftResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_shift_stats',
  auto: true,
})

const shiftStats = computed(() => {
  const d = shiftResource.data || {}
  return {
    gross_sales: Number(d.gross_sales || 0),
    net_collections: Number(d.net_collections || 0),
    open_drafts: Number(d.open_drafts || 0),
    difference: Number(d.difference || 0),
    cashier: d.cashier || '—',
    pos_profile: d.pos_profile || '—',
    shift_date: d.shift_date || '—',
    pos_opening_entry: d.pos_opening_entry || null,
    has_open_shift: d.has_open_shift || false,
    bills_processed: d.bills_processed || 0,
    voided_count: d.voided_count || 0,
    opening_cash: Number(d.opening_cash || 0),
  }
})

// Tender rows - reactive ref so v-model changes persist
const tenderRows = ref([])

watch(() => shiftResource.data?.tender_breakdown, (breakdown) => {
  if (!breakdown) return
  tenderRows.value = breakdown.map(t => ({
    type: t.payment_type,
    system: Number(t.system_amount || 0),
    counted: Number(t.system_amount || 0).toFixed(2),
    editable: t.editable !== false,
  }))
})

function getDiff(row) {
  return (parseFloat(row.counted) || 0) - row.system
}

// ── API: Close Shift ───────────────────────────────────────────────
const closeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.close_pos_shift',
  onSuccess() {
    closing.value = false
    showConfirm.value = false
    router.push('/pos')
  },
  onError(err) {
    closing.value = false
    closeError.value = err.message || 'Failed to close shift'
    setTimeout(() => { closeError.value = '' }, 6000)
  },
})

function confirmClose() {
  showConfirm.value = true
}

function printShiftReport() {
  const entry = shiftStats.value.pos_opening_entry
  if (!entry) {
    closeError.value = 'No open shift found to print.'
    setTimeout(() => { closeError.value = '' }, 3000)
    return
  }
  window.open(
    `/printview?doctype=POS%20Opening%20Entry&name=${encodeURIComponent(entry)}&trigger_print=1`,
    '_blank'
  )
}

function doCloseShift() {
  if (!shiftStats.value.pos_opening_entry) {
    // No open shift found — just redirect
    router.push('/pos')
    return
  }
  closing.value = true
  closeResource.submit({
    pos_opening_entry: shiftStats.value.pos_opening_entry,
    tender_rows: JSON.stringify(tenderRows.value.map(r => ({
      payment_type: r.type,
      system_amount: r.system,
      counted: parseFloat(r.counted) || 0,
    }))),
    closing_note: closingNote.value || null,
  })
}
</script>