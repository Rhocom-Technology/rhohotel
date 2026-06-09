<template>
  <Teleport to="body">
    <div v-if="modelValue"
      class="modal-enter fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('update:modelValue', false)">
      <div class="modal-panel bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:1100px;max-height:92vh;">

        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Open Tables</h2>
              <p class="text-xs text-gray-400 mt-1">View active restaurant and bar tables, monitor live orders, and resume billing for occupied service points.</p>
            </div>
            <button @click="$emit('update:modelValue', false)"
              class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm ml-4 flex-shrink-0">✕</button>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">
          <!-- Filters -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Filters & Search</h4>
            <div class="flex items-end gap-3 flex-wrap">
              <div class="flex-1 min-w-40">
                <p class="text-xs text-gray-500 mb-1.5">Search table</p>
                <div class="relative">
                  <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                  <input v-model="tableSearch" type="text" placeholder="Table no., waiter, guest or bill..."
                    class="w-full pl-8 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Area</p>
                <select v-model="tableFilterArea" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Areas</option>
                  <option v-for="a in availableAreas" :key="a">{{ a }}</option>
                </select>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Waiter</p>
                <select v-model="tableFilterWaiter" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Waiters</option>
                  <option v-for="w in availableWaiters" :key="w">{{ w }}</option>
                </select>
              </div>
              <button @click="tableSearch='';tableFilterArea='';tableFilterWaiter='';tablePage=1"
                class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Reset</button>
              <button @click="tablesResource.reload()" class="btn-hover px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Refresh Tables</button>
            </div>
          </div>

          <!-- Stats -->
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
            <div v-for="s in tableStats" :key="s.label" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
              <p class="text-xs text-gray-400 mb-2">{{ s.label }}</p>
              <p class="text-2xl font-bold text-gray-900">{{ s.value }}</p>
            </div>
          </div>

          <!-- Tables + selected -->
          <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-bold text-gray-900">Active Tables</h4>
                <p class="text-xs text-gray-400">Showing {{ tablePageStart + 1 }}–{{ tablePageEnd }} of {{ filteredTables.length }} open tables</p>
              </div>
              <div v-if="tablesResource.loading" class="py-12 text-center text-xs text-gray-400">Loading tables…</div>
              <div v-else-if="filteredTables.length === 0" class="py-12 text-center text-xs text-gray-400 bg-white rounded-xl border border-gray-200">
                No open table orders found. Tables appear here when a draft order is created with a table name (e.g. &ldquo;Table 01&rdquo;) as the customer.
              </div>
              <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100">
                      <th class="text-left text-xs font-semibold text-blue-600 px-6 py-4">Table</th>
                      <th class="text-left text-xs font-semibold text-blue-600 px-4 py-4">Area</th>
                      <th class="text-left text-xs font-semibold text-blue-600 px-4 py-4">Waiter</th>
                      <th class="text-left text-xs font-semibold text-blue-600 px-4 py-4">Guests</th>
                      <th class="text-left text-xs font-semibold text-blue-600 px-4 py-4">Current Bill</th>
                      <th class="text-left text-xs font-semibold text-blue-600 px-4 py-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in pagedTables" :key="t.id"
                      @click="selectedTable = t"
                      class="table-row cursor-pointer border-b border-gray-50 last:border-0"
                      :class="selectedTable?.id === t.id ? 'bg-blue-50' : 'hover:bg-gray-50'">
                      <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ t.name }}</td>
                      <td class="px-4 py-4 text-xs text-gray-600">{{ t.area }}</td>
                      <td class="px-4 py-4 text-xs text-gray-600">{{ t.waiter }}</td>
                      <td class="px-4 py-4 text-xs text-gray-700">{{ t.guests }}</td>
                      <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ t.bill.toLocaleString() }}</td>
                      <td class="px-4 py-4">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                          :class="t.status === 'Ordering' ? 'bg-blue-100 text-blue-600' :
                                  t.status === 'Kitchen' ? 'bg-yellow-100 text-yellow-600' :
                                  'bg-green-100 text-green-700'">
                          {{ t.status }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <!-- Pagination -->
                <div v-if="tableTotalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-gray-50">
                  <p class="text-xs text-gray-400">Page {{ tablePage }} of {{ tableTotalPages }}</p>
                  <div class="flex items-center gap-1">
                    <button @click="tablePage--" :disabled="tablePage === 1"
                      class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">← Prev</button>
                    <button v-for="p in tableTotalPages" :key="p" @click="tablePage = p"
                      class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                      :class="tablePage === p ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-white border border-gray-200 bg-transparent'">{{ p }}</button>
                    <button @click="tablePage++" :disabled="tablePage === tableTotalPages"
                      class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">Next →</button>
                  </div>
                </div>
              </div><!-- end v-else table wrapper -->
            </div>

            <div v-if="selectedTable" class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-200 bg-white">
                <h4 class="text-sm font-bold text-gray-900">Selected Table</h4>
              </div>
              <div class="p-6 space-y-3 text-xs">
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Table</span><span class="font-bold text-gray-900">{{ selectedTable.name }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Area</span><span class="font-bold text-gray-900">{{ selectedTable.area }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Waiter</span><span class="font-bold text-gray-900">{{ selectedTable.waiter }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Open Time</span><span class="font-bold text-gray-900">{{ selectedTable.openTime }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Guests</span><span class="font-bold text-gray-900">{{ selectedTable.guests }}</span></div>
                <div class="flex justify-between py-1.5"><span class="text-gray-400">Current Bill</span><span class="font-bold text-blue-600">₦{{ selectedTable.bill.toLocaleString() }}</span></div>
              </div>
              <div class="mx-6 mb-5 bg-white rounded-xl border border-gray-200 p-4">
                <p class="text-xs font-bold text-gray-900 mb-3">Current Items</p>
                <div v-for="item in selectedTable.items" :key="item.name"
                  class="flex justify-between text-xs py-2 border-b border-gray-50 last:border-0">
                  <span class="text-gray-600">{{ item.qty }} × {{ item.name }}</span>
                  <span class="font-semibold text-gray-900">₦{{ item.amount.toLocaleString() }}</span>
                </div>
              </div>
              <div class="px-6 pb-6 space-y-2">
                <p v-if="actionMessage" class="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">{{ actionMessage }}</p>
                <p v-if="actionError" class="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{{ actionError }}</p>
                <div class="flex gap-2">
                  <button @click="transferTable" :disabled="transferring"
                    class="btn-hover flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 bg-white disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ transferring ? 'Transferring…' : 'Transfer' }}
                  </button>
                  <button @click="printTableBill" class="btn-hover flex-1 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 bg-white">Print Bill</button>
                </div>
                <div class="flex gap-2">
                  <button @click="settleTable" class="btn-hover flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 bg-white">Settle Table</button>
                  <button @click="$emit('resume', selectedTable); $emit('update:modelValue', false)" class="btn-hover flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Resume Order</button>
                </div>
              </div>
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
import { printPOSInvoice } from '@/lib/posPrint'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'resume'])

const tableSearch = ref('')
const tableFilterArea = ref('')
const tableFilterWaiter = ref('')
const tablePage = ref(1)
const perPage = 10
const selectedTable = ref(null)
const transferring = ref(false)
const actionError = ref('')
const actionMessage = ref('')

// ── API: Open Tables ───────────────────────────────────────────────────────
const tablesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_open_pos_tables',
  auto: false,
})

const transferResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.save_pos_draft_invoice',
  onSuccess(data) {
    transferring.value = false
    actionError.value = ''
    actionMessage.value = `Table transferred. Draft ${data.pos_invoice} updated.`
    selectedTable.value = null
    tablesResource.reload()
    setTimeout(() => { actionMessage.value = '' }, 3500)
  },
  onError(err) {
    transferring.value = false
    actionError.value = err?.message || 'Failed to transfer table'
    setTimeout(() => { actionError.value = '' }, 4500)
  },
})

watch(() => props.modelValue, (open) => {
  if (open) tablesResource.reload()
})

const openTables = computed(() => tablesResource.data || [])

const tableStats = computed(() => {
  const all = openTables.value
  const oldest = all.reduce((max, t) => Math.max(max, t.age_minutes || 0), 0)
  const h = Math.floor(oldest / 60)
  const m = oldest % 60
  return [
    { label: 'Open Tables', value: String(all.length) },
    { label: 'Total Pending Bill', value: `₦${all.reduce((s, t) => s + t.bill, 0).toLocaleString()}` },
    { label: 'Ready to Bill', value: String(all.filter(t => t.status === 'Ready').length) },
    { label: 'Longest Open', value: h ? `${h}h ${m}m` : `${m}m` },
  ]
})

const availableAreas = computed(() => [...new Set(openTables.value.map(t => t.area).filter(Boolean))])
const availableWaiters = computed(() => [...new Set(openTables.value.map(t => t.waiter).filter(Boolean))])

const filteredTables = computed(() => {
  let data = openTables.value
  if (tableSearch.value) {
    const q = tableSearch.value.toLowerCase()
    data = data.filter(t =>
      t.name.toLowerCase().includes(q) ||
      (t.waiter || '').toLowerCase().includes(q) ||
      (t.area || '').toLowerCase().includes(q) ||
      String(t.bill).includes(q)
    )
  }
  if (tableFilterArea.value) data = data.filter(t => t.area === tableFilterArea.value)
  if (tableFilterWaiter.value) data = data.filter(t => t.waiter === tableFilterWaiter.value)
  return data
})

const tableTotalPages = computed(() => Math.max(1, Math.ceil(filteredTables.value.length / perPage)))
const tablePageStart = computed(() => (tablePage.value - 1) * perPage)
const tablePageEnd = computed(() => Math.min(tablePageStart.value + perPage, filteredTables.value.length))
const pagedTables = computed(() => filteredTables.value.slice(tablePageStart.value, tablePageEnd.value))

watch(filteredTables, () => { tablePage.value = 1 })

function printTableBill() {
  if (!selectedTable.value?.invoice) return
  printPOSInvoice(selectedTable.value.invoice)
}

function settleTable() {
  if (!selectedTable.value) return
  emit('resume', { ...selectedTable.value, settle: true })
  emit('update:modelValue', false)
}

function transferTable() {
  if (!selectedTable.value || transferring.value) return
  const nextTable = window.prompt('Transfer this order to which table?', selectedTable.value.name || '')
  const customer = (nextTable || '').trim()
  if (!customer || customer === selectedTable.value.name) return

  transferring.value = true
  actionError.value = ''
  transferResource.submit({
    items: JSON.stringify((selectedTable.value.items || []).map(i => ({
      item_code: i.item_code || i.name,
      qty: i.qty,
      price: i.price || (i.qty > 0 ? i.amount / i.qty : 0),
    }))),
    customer,
    kitchen_note: selectedTable.value.notes || null,
    existing_draft: selectedTable.value.invoice || null,
  })
}
</script>

<style>
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.modal-enter { animation: overlayIn 0.2s ease; }
.modal-panel { animation: modalIn 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.btn-hover { transition: all 0.15s ease; }
.btn-hover:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-hover:active { transform: translateY(0); }
.table-row { transition: background 0.15s ease; }
</style>
