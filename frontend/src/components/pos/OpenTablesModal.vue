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
                  <option>Restaurant</option>
                  <option>Bar Lounge</option>
                  <option>Poolside</option>
                </select>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Waiter</p>
                <select v-model="tableFilterWaiter" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Waiters</option>
                  <option>Boma</option>
                  <option>Adaeze</option>
                  <option>Ifeoma</option>
                  <option>Ngozi</option>
                </select>
              </div>
              <button @click="tableSearch='';tableFilterArea='';tableFilterWaiter='';tablePage=1"
                class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Reset</button>
              <button class="btn-hover px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Create New Table Order</button>
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
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
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
              </div>
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
                <div class="flex gap-2">
                  <button class="btn-hover flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 bg-white">Transfer</button>
                  <button class="btn-hover flex-1 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 bg-white">Print Bill</button>
                </div>
                <div class="flex gap-2">
                  <button class="btn-hover flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 bg-white">Settle Table</button>
                  <button class="btn-hover flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Resume Order</button>
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

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])

const tableSearch = ref('')
const tableFilterArea = ref('')
const tableFilterWaiter = ref('')
const tablePage = ref(1)
const perPage = 10

const tableStats = [
  { label: 'Open Tables', value: '14' },
  { label: 'Kitchen Pending', value: '6' },
  { label: 'Ready to Bill', value: '5' },
  { label: 'Longest Open Table', value: '1h 42m' },
]

const openTables = [
  { id: 1, name: 'Table 01', area: 'Restaurant', waiter: 'Boma', guests: 4, bill: 48500, status: 'Ordering', openTime: '10:05 AM', items: [{ name: 'Club Sandwich', qty: 2, amount: 24000 }, { name: 'Fresh Orange Juice', qty: 1, amount: 6500 }, { name: 'Grilled Chicken Meal', qty: 1, amount: 18000 }] },
  { id: 2, name: 'Table 02', area: 'Restaurant', waiter: 'Adaeze', guests: 2, bill: 26000, status: 'Kitchen', openTime: '10:15 AM', items: [{ name: 'Caesar Salad', qty: 2, amount: 19000 }, { name: 'Sparkling Water', qty: 2, amount: 6000 }] },
  { id: 3, name: 'Table 04', area: 'Bar Lounge', waiter: 'Ifeoma', guests: 3, bill: 18000, status: 'Ready', openTime: '10:30 AM', items: [{ name: 'Heineken Beer', qty: 3, amount: 15000 }, { name: 'Bottled Water', qty: 2, amount: 3000 }] },
  { id: 4, name: 'Table 06', area: 'Poolside', waiter: 'Ngozi', guests: 5, bill: 72500, status: 'Ordering', openTime: '9:45 AM', items: [{ name: 'Grilled Chicken Meal', qty: 3, amount: 55500 }, { name: 'Fresh Orange Juice', qty: 2, amount: 13000 }] },
  { id: 5, name: 'Table 08', area: 'Bar Lounge', waiter: 'Adaeze', guests: 2, bill: 15500, status: 'Kitchen', openTime: '10:48 AM', items: [{ name: 'Red Wine Glass', qty: 1, amount: 8500 }, { name: 'Club Sandwich', qty: 1, amount: 12000 }] },
  { id: 6, name: 'Table 09', area: 'Restaurant', waiter: 'Boma', guests: 6, bill: 91000, status: 'Ready', openTime: '9:30 AM', items: [{ name: 'Grilled Chicken Meal', qty: 4, amount: 74000 }, { name: 'Sparkling Water', qty: 3, amount: 9000 }] },
  { id: 7, name: 'Table 11', area: 'Poolside', waiter: 'Ngozi', guests: 2, bill: 23000, status: 'Ordering', openTime: '10:55 AM', items: [{ name: 'Caesar Salad', qty: 1, amount: 9500 }, { name: 'Cappuccino', qty: 2, amount: 11000 }] },
  { id: 8, name: 'Bar 01', area: 'Bar Lounge', waiter: 'Ifeoma', guests: 3, bill: 34500, status: 'Kitchen', openTime: '11:10 AM', items: [{ name: 'Heineken Beer', qty: 4, amount: 20000 }, { name: 'Burger Combo', qty: 1, amount: 14000 }] },
  { id: 9, name: 'Bar 03', area: 'Bar Lounge', waiter: 'Adaeze', guests: 1, bill: 17000, status: 'Ready', openTime: '11:20 AM', items: [{ name: 'Red Wine Glass', qty: 2, amount: 17000 }] },
  { id: 10, name: 'Table 13', area: 'Restaurant', waiter: 'Boma', guests: 4, bill: 52000, status: 'Ordering', openTime: '11:05 AM', items: [{ name: 'Club Sandwich', qty: 3, amount: 36000 }, { name: 'Fresh Orange Juice', qty: 2, amount: 13000 }] },
  { id: 11, name: 'Table 15', area: 'Restaurant', waiter: 'Adaeze', guests: 2, bill: 29500, status: 'Kitchen', openTime: '11:35 AM', items: [{ name: 'Grilled Chicken Meal', qty: 1, amount: 18500 }, { name: 'Bottled Water', qty: 2, amount: 3000 }] },
  { id: 12, name: 'Poolside 02', area: 'Poolside', waiter: 'Ngozi', guests: 5, bill: 67000, status: 'Ordering', openTime: '10:40 AM', items: [{ name: 'Grilled Chicken Meal', qty: 2, amount: 37000 }, { name: 'Heineken Beer', qty: 4, amount: 20000 }] },
]

const filteredTables = computed(() => {
  let data = openTables
  if (tableSearch.value) {
    const q = tableSearch.value.toLowerCase()
    data = data.filter(t =>
      t.name.toLowerCase().includes(q) ||
      t.waiter.toLowerCase().includes(q) ||
      t.area.toLowerCase().includes(q) ||
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
const selectedTable = ref(openTables[0])

watch(filteredTables, () => { tablePage.value = 1 })
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