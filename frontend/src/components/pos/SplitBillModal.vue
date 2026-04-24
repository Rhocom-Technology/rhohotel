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
              <h2 class="text-xl font-bold text-gray-900">Split Bill</h2>
              <p class="text-xs text-gray-400 mt-1">Split this bill by amount, percentage, item selection, or payment type before final settlement.</p>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button @click="$emit('update:modelValue', false)" class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Apply Split</button>
            </div>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">
          <!-- Snapshot -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-6">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Bill Snapshot</h4>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;">
              <div><p class="text-xs text-gray-400 mb-1.5">Bill No.</p><p class="text-sm font-bold text-gray-900">POS-2026-00184</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Service Point</p><p class="text-sm font-bold text-gray-900">Table 03</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Cashier</p><p class="text-sm font-bold text-gray-900">Adaeze</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Grand Total</p><p class="text-sm font-bold text-blue-600">₦{{ grandTotal.toLocaleString() }}</p></div>
            </div>
          </div>

          <!-- Config -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-6">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Split Configuration</h4>
            <div class="flex items-end gap-4 flex-wrap">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Split Method</p>
                <select class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700 pr-8">
                  <option>By Payment Portion</option>
                  <option>Equal Split</option>
                  <option>By Item</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">No. of Splits</p>
                <input type="number" value="3" class="w-24 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-center" />
              </div>
              <button class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Equal Split</button>
              <button class="btn-hover px-4 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 bg-white">Split by Items</button>
            </div>
          </div>

          <!-- Items + portions -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-bold text-gray-900">Bill Items</h4>
                <p class="text-xs text-gray-400">Select items for specific split if needed</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-6 py-4">Item</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Qty</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Amount</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Split</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in splitItems" :key="item.name"
                      @click="selectedSplitItem = idx"
                      class="table-row cursor-pointer border-b border-gray-50 last:border-0"
                      :class="selectedSplitItem === idx ? 'bg-blue-50 ring-1 ring-inset ring-blue-200' : 'hover:bg-gray-50'">
                      <td class="px-6 py-4">
                        <div class="flex items-center gap-3">
                          <div class="w-4 h-4 rounded bg-blue-600 flex-shrink-0"></div>
                          <span class="text-xs font-semibold text-gray-900">{{ item.name }}</span>
                        </div>
                      </td>
                      <td class="px-4 py-4 text-xs text-gray-600">{{ item.qty }}</td>
                      <td class="px-4 py-4 text-xs font-bold text-gray-900">₦{{ item.amount.toLocaleString() }}</td>
                      <td class="px-4 py-4 text-xs font-semibold text-blue-600">{{ item.split }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4 class="text-sm font-bold text-gray-900 mb-3">Split Portions</h4>
              <div class="space-y-4">
                <div v-for="portion in splitPortions" :key="portion.label"
                  class="bg-gray-50 rounded-xl border border-gray-200 p-5">
                  <div class="flex items-center justify-between mb-4">
                    <h5 class="text-sm font-bold text-gray-900">{{ portion.label }}</h5>
                    <span v-if="portion.primary" class="px-2.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-600 rounded-full">Primary</span>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
                    <div>
                      <p class="text-xs text-gray-400 mb-1.5">Payment Type</p>
                      <div class="px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700">{{ portion.paymentType }}</div>
                    </div>
                    <div>
                      <p class="text-xs text-gray-400 mb-1.5">Target</p>
                      <div class="px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700">{{ portion.target }}</div>
                    </div>
                    <div>
                      <p class="text-xs text-gray-400 mb-1.5">Amount</p>
                      <div class="px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs font-bold text-gray-900">₦{{ portion.amount.toLocaleString() }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Check -->
          <div class="flex items-center gap-3 py-4 px-6 bg-green-50 rounded-xl border border-green-100">
            <svg class="w-4 h-4 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            <p class="text-xs text-gray-600">Split total check: <span class="font-bold text-green-600">₦{{ grandTotal.toLocaleString() }} allocated successfully</span></p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  grandTotal: { type: Number, default: 0 },
  cartItems: { type: Array, default: () => [] },
  serviceCharge: { type: Number, default: 0 },
})

defineEmits(['update:modelValue'])

const selectedSplitItem = ref(0)

const splitItems = computed(() => [
  ...props.cartItems.map((i, idx) => ({
    name: i.name, qty: i.qty, amount: i.price * i.qty,
    split: ['Split A', 'Split B', 'Split B'][idx] || 'Split A',
  })),
  { name: 'Service Charge + VAT', qty: 1, amount: props.serviceCharge, split: 'Split C' },
])

const splitPortions = [
  { label: 'Split A', primary: true, paymentType: 'Cash', target: 'Walk In', amount: 18500 },
  { label: 'Split B', primary: false, paymentType: 'POS', target: 'Guest 2', amount: 16000 },
  { label: 'Split C', primary: false, paymentType: 'Post to Room', target: 'Room 305', amount: 5865 },
]
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