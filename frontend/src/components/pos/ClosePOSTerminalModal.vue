<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:960px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Close POS Terminal List</h2>
              <p class="text-xs text-gray-400 mt-1">Manager view to review active cashier terminals, confirm readiness, and close staff POS shifts from one control point.</p>
            </div>
            <div class="flex items-center gap-2 ml-4 flex-shrink-0">
              <button @click="terminalsResource.reload()" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh List</button>
              <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                :class="!selectedTerminal ? 'opacity-50 cursor-not-allowed' : ''"
                  :disabled="!selectedTerminal || closing"
                  @click="closeSelectedShift">{{ closing ? 'Closing…' : 'Close Selected Shift' }}</button>
              <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$emit('close')">Cancel</button>
            </div>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-5">

          <!-- Terminal Closing Summary -->
          <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p class="text-xs text-gray-400 mb-1">Open terminals</p>
                <p class="text-2xl font-bold text-gray-900">{{ terminalsResource.loading ? '…' : terminals.length }}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p class="text-xs text-gray-400 mb-1">Pending drafts</p>
                <p class="text-2xl font-bold text-gray-900">{{ terminalsResource.loading ? '…' : terminals.reduce((s,t)=>s+t.drafts,0) }}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p class="text-xs text-gray-400 mb-1">Open tables</p>
              <p class="text-2xl font-bold text-gray-900">{{ terminalsResource.loading ? '…' : terminals.reduce((s,t)=>s+t.tables,0) }}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p class="text-xs text-gray-400 mb-1">Flagged differences</p>
              <p class="text-2xl font-bold text-red-500">₦41,300</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p class="text-xs text-gray-400 mb-1">Manager</p>
              <p class="text-2xl font-bold text-gray-900">On Duty</p>
            </div>
          </div>

          <!-- Filters -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-6 py-5">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Filters & Search</h4>
            <div class="flex items-end gap-3 flex-wrap">
              <div class="flex-1" style="min-width:160px;">
                <p class="text-xs text-gray-500 mb-1.5">Search terminal</p>
                <input v-model="searchText" type="text" placeholder="Cashier, outlet, terminal..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
              </div>
              <div style="min-width:130px;">
                <p class="text-xs text-gray-500 mb-1.5">Outlet</p>
                <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-600">
                  <option>All Outlets</option>
                  <option>Main Restaurant</option>
                  <option>Bar Lounge</option>
                  <option>Retail Corner</option>
                </select>
              </div>
              <div style="min-width:130px;">
                <p class="text-xs text-gray-500 mb-1.5">Shift Status</p>
                <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-600">
                  <option>All Statuses</option>
                  <option>Open</option>
                  <option>Closing</option>
                </select>
              </div>
              <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
              <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply Filter</button>
            </div>
          </div>

          <!-- Terminals + Detail -->
            <div v-if="closeError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-xs text-red-600">{{ closeError }}</div>
            <div v-if="closeSuccess" class="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-xs text-green-700 font-semibold">{{ closeSuccess }}</div>
          <div style="display:grid;grid-template-columns:1fr 280px;gap:16px;">

            <!-- Terminal Table -->
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <h4 class="text-xs font-bold text-gray-900">Active Staff POS Terminals</h4>
                <p class="text-xs text-gray-400">Select a terminal to close the cashier's shift</p>
              </div>
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="px-4 py-3.5 w-8"></th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Terminal</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outlet</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Drafts / Tables</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Difference</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in filteredTerminals" :key="t.name"
                    @click="selectedTerminal = t.name"
                    class="border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
                    :class="selectedTerminal === t.name ? 'bg-blue-50' : 'hover:bg-gray-50'">
                    <td class="px-4 py-4">
                      <input type="checkbox" :checked="selectedTerminal === t.name"
                        @click.stop="selectedTerminal = t.name"
                        class="accent-blue-600" />
                    </td>
                    <td class="px-4 py-4">
                      <div class="text-xs font-bold text-blue-600">{{ t.name }}</div>
                      <div class="text-xs text-gray-400">{{ t.shiftLabel }}</div>
                      <div class="text-xs text-gray-400">{{ t.opened }}</div>
                    </td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ t.cashier }}</td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ t.outlet }}</td>
                    <td class="px-4 py-4 text-xs text-gray-700">{{ t.drafts }} / {{ t.tables }}</td>
                    <td class="px-4 py-4 text-xs font-semibold"
                      :class="t.diff === '₦0.00' ? 'text-green-600' : 'text-red-500'">{{ t.diff }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Detail Panel -->
            <div v-if="selected" class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-5 py-4 border-b border-gray-200 bg-white">
                <h4 class="text-xs font-bold text-gray-900">Selected Terminal</h4>
              </div>
              <div class="p-5 space-y-0">
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Terminal</span>
                  <span class="font-semibold text-gray-900">{{ selected.name }}</span>
                </div>
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Cashier</span>
                  <span class="font-bold text-gray-900">{{ selected.cashier }}</span>
                </div>
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Outlet</span>
                  <span class="font-semibold text-gray-900">{{ selected.outlet }}</span>
                </div>
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Gross Sales</span>
                  <span class="font-bold text-gray-900">{{ selected.sales }}</span>
                </div>
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Open Drafts</span>
                  <span class="font-bold" :class="selected.drafts > 0 ? 'text-yellow-600' : 'text-green-600'">{{ selected.drafts }}</span>
                </div>
                <div class="flex justify-between py-2.5 border-b border-gray-100 text-xs">
                  <span class="text-gray-400">Open Tables</span>
                  <span class="font-bold" :class="selected.tables > 0 ? 'text-blue-600' : 'text-green-600'">{{ selected.tables }}</span>
                </div>
                <div class="flex justify-between py-2.5 text-xs">
                  <span class="text-gray-400">Difference</span>
                  <span class="font-bold" :class="selected.diff === '₦0.00' ? 'text-green-600' : 'text-red-500'">{{ selected.diff }}</span>
                </div>
              </div>
              <div class="mx-5 mb-4 bg-white rounded-xl border border-gray-200 p-4">
                <p class="text-xs font-bold text-gray-900 mb-2">Closing Readiness</p>
                <p class="text-xs text-gray-500 leading-relaxed">{{ selected.readiness }}</p>
              </div>
              <div class="px-5 pb-5">
                <p class="text-xs text-gray-500 mb-1.5">Manager Closing Note</p>
                <textarea
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none bg-white"
                  rows="3"
                  placeholder="Optional note for staff handover or shift closure instruction..."></textarea>
              </div>
            </div>
            <div v-else class="bg-gray-50 rounded-xl border border-gray-200 flex items-center justify-center text-xs text-gray-400">
              Select a terminal to view details
            </div>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

defineEmits(['close'])

const searchText = ref('')
const selectedTerminal = ref('Restaurant POS 01')

const closing = ref(false)
const closeError = ref('')
const closeSuccess = ref('')

// ── API ───────────────────────────────────────────────────────────────────
const terminalsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_open_pos_terminals',
  auto: true,
})

const closeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.close_pos_shift',
  onSuccess() {
    closing.value = false
    closeSuccess.value = `Shift closed for ${selectedTerminal.value}`
    selectedTerminal.value = ''
    terminalsResource.reload()
    setTimeout(() => { closeSuccess.value = '' }, 4000)
  },
  onError(err) {
    closing.value = false
    closeError.value = err?.message || 'Failed to close shift'
    setTimeout(() => { closeError.value = '' }, 5000)
  },
})

const terminals = computed(() =>
  (terminalsResource.data || []).map(t => ({
    name: t.terminal_name || t.opening_entry,
    opening_entry: t.opening_entry,
    cashier: t.cashier || t.user || '—',
    outlet: t.terminal_name || '—',
    drafts: t.open_drafts || 0,
    tables: t.open_tables || 0,
    diff: '₦0.00',
    sales: `₦${Number(t.gross_sales || 0).toLocaleString()}`,
    shiftLabel: 'Active shift •',
    opened: t.shift_start ? `Opened ${t.shift_start}` : '',
    readiness: t.open_drafts > 0
      ? `${t.open_drafts} draft order(s) still pending. Resolve before closing.`
      : 'No pending drafts. Ready to close.',
  }))
)

const filteredTerminals = computed(() => {
  const q = (searchText.value || '').trim().toLowerCase()
  if (!q) return terminals.value
  return terminals.value.filter(t =>
    (t.name || '').toLowerCase().includes(q) ||
    (t.cashier || '').toLowerCase().includes(q) ||
    (t.outlet || '').toLowerCase().includes(q)
  )
})

const selected = computed(() => terminals.value.find(t => t.name === selectedTerminal.value) || null)

watch(filteredTerminals, (rows) => {
  if (!rows.length) {
    selectedTerminal.value = ''
    return
  }
  if (!rows.some(t => t.name === selectedTerminal.value)) {
    selectedTerminal.value = rows[0].name
  }
}, { immediate: true })

function closeSelectedShift() {
  if (!selected.value || closing.value) return
  if (!confirm(`Close shift for ${selected.value.cashier} on ${selected.value.name}?`)) return
  closing.value = true
  closeResource.submit({
    pos_opening_entry: selected.value.opening_entry,
    tender_rows: JSON.stringify([]),
    closing_note: null,
  })
}
</script>