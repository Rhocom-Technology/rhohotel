<template>
  <Teleport to="body">
    <div v-if="modelValue"
      class="modal-enter fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('update:modelValue', false)">
      <div class="modal-panel bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:1000px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Draft Orders</h2>
              <p class="text-xs text-gray-400 mt-1">Review saved POS drafts, resume suspended bills, reassign service points, or delete old drafts before checkout.</p>
            </div>
            <button @click="$emit('update:modelValue', false)"
              class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm ml-4 flex-shrink-0">✕</button>
          </div>
          <div class="flex items-center gap-2 mt-5">
            <button class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Delete Draft</button>
            <button @click="$emit('update:modelValue', false)" class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close Page</button>
            <button class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print Draft Bill</button>
            <button class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Resume Draft</button>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">
          <!-- Filters -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Filters & Search</h4>
            <div class="flex items-end gap-3 flex-wrap">
              <div class="flex-1 min-w-40">
                <p class="text-xs text-gray-500 mb-1.5">Search draft</p>
                <div class="relative">
                  <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                  <input v-model="draftSearch" type="text" placeholder="Invoice no., room, table, cashier..."
                    class="w-full pl-8 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Service Point</p>
                <select v-model="draftFilterPoint" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Points</option>
                  <option>Restaurant</option>
                  <option>Bar</option>
                  <option>Room Service</option>
                </select>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Cashier</p>
                <select v-model="draftFilterCashier" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Cashiers</option>
                  <option>Adaeze</option>
                  <option>Boma</option>
                  <option>Ifeoma</option>
                </select>
              </div>
              <button @click="draftSearch='';draftFilterPoint='';draftFilterCashier='';draftPage=1"
                class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Reset</button>
              <button class="btn-hover px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Create New Draft</button>
            </div>
          </div>

          <!-- Stats -->
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
            <div v-for="s in draftStats" :key="s.label" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
              <p class="text-xs text-gray-400 mb-2">{{ s.label }}</p>
              <p class="text-2xl font-bold text-gray-900">{{ s.value }}</p>
            </div>
          </div>

          <!-- List + selected -->
          <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h4 class="text-xs font-bold text-gray-900">Saved Draft Orders</h4>
                <p class="text-xs text-gray-400">Showing {{ draftPageStart + 1 }}–{{ draftPageEnd }} of {{ filteredDrafts.length }} drafts</p>
              </div>
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Service Point</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Items</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Age</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="d in pagedDrafts" :key="d.id"
                    @click="selectedDraft = d"
                    class="table-row cursor-pointer border-b border-gray-50 last:border-0"
                    :class="selectedDraft?.id === d.id ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'">
                    <td class="px-6 py-4 text-xs font-semibold text-blue-600">{{ d.invoice }}</td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ d.point }}</td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ d.cashier }}</td>
                    <td class="px-4 py-4 text-xs text-gray-700">{{ d.items }}</td>
                    <td class="px-4 py-4 text-xs font-semibold text-gray-900">₦{{ d.amount.toLocaleString() }}</td>
                    <td class="px-4 py-4 text-xs font-semibold" :class="d.ageMinutes > 60 ? 'text-orange-500' : 'text-amber-400'">{{ d.age }}</td>
                  </tr>
                </tbody>
              </table>
              <!-- Pagination -->
              <div v-if="draftTotalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-gray-50">
                <p class="text-xs text-gray-400">Page {{ draftPage }} of {{ draftTotalPages }}</p>
                <div class="flex items-center gap-1">
                  <button @click="draftPage--" :disabled="draftPage === 1"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">← Prev</button>
                  <button v-for="p in draftTotalPages" :key="p" @click="draftPage = p"
                    class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                    :class="draftPage === p ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-white border border-gray-200 bg-transparent'">{{ p }}</button>
                  <button @click="draftPage++" :disabled="draftPage === draftTotalPages"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">Next →</button>
                </div>
              </div>
            </div>

            <div v-if="selectedDraft" class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-200 bg-white">
                <h4 class="text-xs font-bold text-gray-900">Selected Draft</h4>
              </div>
              <div class="p-6 space-y-3 text-xs">
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Invoice No.</span><span class="font-bold text-gray-900">{{ selectedDraft.invoice }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Service Point</span><span class="font-semibold text-gray-900">{{ selectedDraft.detailPoint }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Cashier</span><span class="font-semibold text-gray-900">{{ selectedDraft.cashier }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Saved At</span><span class="font-semibold text-gray-900">{{ selectedDraft.savedAt }}</span></div>
                <div class="flex justify-between py-1.5"><span class="text-gray-400">Total Value</span><span class="font-bold text-blue-600">₦{{ selectedDraft.amount.toLocaleString() }}</span></div>
              </div>
              <div class="mx-6 mb-5 bg-white rounded-xl border border-gray-200 p-4">
                <p class="text-xs font-bold text-gray-900 mb-3">Draft Items</p>
                <div v-for="item in selectedDraft.draftItems" :key="item.name"
                  class="flex justify-between text-xs py-2 border-b border-gray-50 last:border-0">
                  <span class="text-gray-600">{{ item.name }}</span>
                  <span class="font-semibold text-gray-900">× {{ item.qty }}</span>
                </div>
              </div>
              <div class="px-6 pb-6">
                <p class="text-xs font-bold text-gray-900 mb-2">Draft Note</p>
                <div class="bg-white rounded-xl border border-gray-200 p-4 text-xs text-gray-500 leading-relaxed min-h-12">
                  {{ selectedDraft.note || 'No note added.' }}
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

const props = defineProps({
  modelValue: Boolean,
})
defineEmits(['update:modelValue'])

const draftSearch = ref('')
const draftFilterPoint = ref('')
const draftFilterCashier = ref('')
const draftPage = ref(1)
const perPage = 10

const draftStats = [
  { label: 'Total Draft Orders', value: '24' },
  { label: 'Room Charge Drafts', value: '9' },
  { label: 'Table / Bar Drafts', value: '11' },
  { label: 'Oldest Draft Pending', value: '2h 18m' },
]

const draftOrders = [
  { id: 1, invoice: 'INV-DRAFT-000421', point: 'Restaurant', cashier: 'Adaeze', items: 4, amount: 40365, age: '18 min', ageMinutes: 18, savedAt: '10:14 AM', detailPoint: 'Room 305', draftItems: [{ name: 'Grilled Chicken Meal', qty: 1 }, { name: 'Fresh Orange Juice', qty: 2 }], note: 'No pepper on meal. Deliver to room within 20 mins.' },
  { id: 2, invoice: 'INV-DRAFT-000418', point: 'Table 02', cashier: 'Adaeze', items: 6, amount: 62800, age: '34 min', ageMinutes: 34, savedAt: '9:58 AM', detailPoint: 'Table 02', draftItems: [{ name: 'Club Sandwich', qty: 2 }, { name: 'Heineken Beer', qty: 4 }], note: 'Extra napkins needed.' },
  { id: 3, invoice: 'INV-DRAFT-000416', point: 'Bar 04', cashier: 'Adaeze', items: 3, amount: 18000, age: '1h 05m', ageMinutes: 65, savedAt: '9:27 AM', detailPoint: 'Bar 04', draftItems: [{ name: 'Red Wine Glass', qty: 2 }, { name: 'Sparkling Water', qty: 1 }], note: '' },
  { id: 4, invoice: 'INV-DRAFT-000413', point: 'Restaurant', cashier: 'Adaeze', items: 2, amount: 14500, age: '1h 22m', ageMinutes: 82, savedAt: '9:10 AM', detailPoint: 'Restaurant', draftItems: [{ name: 'Caesar Salad', qty: 1 }, { name: 'Cappuccino', qty: 1 }], note: '' },
  { id: 5, invoice: 'INV-DRAFT-000409', point: 'Restaurant', cashier: 'Adaeze', items: 5, amount: 27500, age: '1h 48m', ageMinutes: 108, savedAt: '8:44 AM', detailPoint: 'Restaurant', draftItems: [{ name: 'Burger Combo', qty: 1 }, { name: 'Bottled Water', qty: 2 }], note: 'Allergic to peanuts.' },
  { id: 6, invoice: 'INV-DRAFT-000405', point: 'Bar', cashier: 'Boma', items: 2, amount: 11000, age: '2h 01m', ageMinutes: 121, savedAt: '8:31 AM', detailPoint: 'Bar 01', draftItems: [{ name: 'Heineken Beer', qty: 2 }], note: '' },
  { id: 7, invoice: 'INV-DRAFT-000402', point: 'Restaurant', cashier: 'Ifeoma', items: 3, amount: 22000, age: '2h 18m', ageMinutes: 138, savedAt: '8:14 AM', detailPoint: 'Room 402', draftItems: [{ name: 'Club Sandwich', qty: 1 }, { name: 'Fresh Orange Juice', qty: 2 }], note: 'No salt please.' },
  { id: 8, invoice: 'INV-DRAFT-000399', point: 'Restaurant', cashier: 'Adaeze', items: 1, amount: 9500, age: '2h 35m', ageMinutes: 155, savedAt: '7:57 AM', detailPoint: 'Table 05', draftItems: [{ name: 'Caesar Salad', qty: 1 }], note: '' },
  { id: 9, invoice: 'INV-DRAFT-000396', point: 'Bar', cashier: 'Boma', items: 4, amount: 31000, age: '2h 52m', ageMinutes: 172, savedAt: '7:40 AM', detailPoint: 'Bar 03', draftItems: [{ name: 'Red Wine Glass', qty: 2 }, { name: 'Burger Combo', qty: 2 }], note: '' },
  { id: 10, invoice: 'INV-DRAFT-000391', point: 'Room Service', cashier: 'Ifeoma', items: 3, amount: 18500, age: '3h 10m', ageMinutes: 190, savedAt: '7:22 AM', detailPoint: 'Room 214', draftItems: [{ name: 'Grilled Chicken Meal', qty: 1 }, { name: 'Bottled Water', qty: 2 }], note: 'Extra napkins.' },
  { id: 11, invoice: 'INV-DRAFT-000388', point: 'Restaurant', cashier: 'Adaeze', items: 2, amount: 12000, age: '3h 28m', ageMinutes: 208, savedAt: '7:04 AM', detailPoint: 'Table 08', draftItems: [{ name: 'Club Sandwich', qty: 1 }, { name: 'Cappuccino', qty: 1 }], note: '' },
  { id: 12, invoice: 'INV-DRAFT-000385', point: 'Bar', cashier: 'Boma', items: 6, amount: 45000, age: '3h 45m', ageMinutes: 225, savedAt: '6:47 AM', detailPoint: 'Bar 02', draftItems: [{ name: 'Red Wine Glass', qty: 4 }, { name: 'Heineken Beer', qty: 2 }], note: '' },
]

const filteredDrafts = computed(() => {
  let data = draftOrders
  if (draftSearch.value) {
    const q = draftSearch.value.toLowerCase()
    data = data.filter(d =>
      d.invoice.toLowerCase().includes(q) ||
      d.point.toLowerCase().includes(q) ||
      d.cashier.toLowerCase().includes(q)
    )
  }
  if (draftFilterPoint.value) data = data.filter(d => d.point === draftFilterPoint.value)
  if (draftFilterCashier.value) data = data.filter(d => d.cashier === draftFilterCashier.value)
  return data
})

const draftTotalPages = computed(() => Math.max(1, Math.ceil(filteredDrafts.value.length / perPage)))
const draftPageStart = computed(() => (draftPage.value - 1) * perPage)
const draftPageEnd = computed(() => Math.min(draftPageStart.value + perPage, filteredDrafts.value.length))
const pagedDrafts = computed(() => filteredDrafts.value.slice(draftPageStart.value, draftPageEnd.value))

const selectedDraft = ref(draftOrders[0])

watch(filteredDrafts, () => { draftPage.value = 1 })
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