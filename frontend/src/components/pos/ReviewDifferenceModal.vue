<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:920px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Review Difference</h2>
              <p class="text-xs text-gray-400 mt-1">Inspect terminal closing differences, compare counted values with system totals, and record review remarks before resolution.</p>
            </div>
            <div class="flex items-center gap-2 ml-4 flex-shrink-0">
              <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$emit('close')">Close</button>
              <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                @click="resolve">Resolve Review</button>
            </div>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-5">

          <!-- Difference Snapshot -->
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <p class="text-xs text-gray-400 mb-1">Terminal</p>
              <p class="text-sm font-bold text-gray-900">Mini-Mart POS 03</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <p class="text-xs text-gray-400 mb-1">Cashier</p>
              <p class="text-sm font-bold text-gray-900">Boma</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <p class="text-xs text-gray-400 mb-1">Shift</p>
              <p class="text-sm font-bold text-gray-900">Morning • 15 Apr 2026</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <p class="text-xs text-gray-400 mb-1">Difference</p>
              <p class="text-sm font-bold text-red-500">₦41,300</p>
            </div>
          </div>

          <!-- Tender Review + Review Action -->
          <div style="display:grid;grid-template-columns:1fr 300px;gap:16px;">

            <!-- Left: Tender Review + Supporting Activity -->
            <div class="space-y-5">
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-100">
                  <h4 class="text-xs font-bold text-gray-900">Tender Review</h4>
                </div>
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100 bg-gray-50">
                      <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Tender Type</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">System Amount</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Counted / Reported</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Difference</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in tenders" :key="t.type" class="border-b border-gray-50 last:border-0">
                      <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ t.type }}</td>
                      <td class="px-4 py-4 text-xs text-gray-600">{{ t.system }}</td>
                      <td class="px-4 py-4 text-xs text-gray-600">{{ t.counted }}</td>
                      <td class="px-4 py-4 text-xs font-bold"
                        :class="t.diff === '₦0.00' ? 'text-green-600' : 'text-red-500'">{{ t.diff }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
                <h4 class="text-xs font-bold text-gray-900 mb-4">Supporting Activity</h4>
                <div class="bg-gray-50 rounded-lg px-4 py-4">
                  <p class="text-xs font-semibold text-gray-700 mb-3">Shift Notes</p>
                  <p class="text-xs text-gray-600 py-1.5 border-b border-gray-100">• Cash drawer was reopened at 01:12 PM for float adjustment.</p>
                  <p class="text-xs text-gray-600 py-1.5 border-b border-gray-100">• 2 invoices were voided after item correction.</p>
                  <p class="text-xs text-gray-600 py-1.5">• 1 draft order remained open during closing review.</p>
                </div>
              </div>
            </div>

            <!-- Right: Review Action -->
            <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
              <h4 class="text-xs font-bold text-gray-900">Review Action</h4>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Difference Category</p>
                <select v-model="category" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option>Cash shortage</option>
                  <option>Overcount</option>
                  <option>Float error</option>
                  <option>Voided invoice</option>
                  <option>Other</option>
                </select>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Reviewed By</p>
                <div class="px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 rounded-lg text-center">
                  Manager On Duty
                </div>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Review Decision</p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                  <button
                    class="py-2.5 text-xs font-semibold rounded-lg transition-colors"
                    :class="decision==='Escalate' ? 'bg-red-500 text-white' : 'bg-red-50 text-red-500 hover:bg-red-100'"
                    @click="decision='Escalate'">Escalate</button>
                  <button
                    class="py-2.5 text-xs font-semibold rounded-lg transition-colors"
                    :class="decision==='Accept' ? 'bg-green-600 text-white' : 'bg-green-50 text-green-600 hover:bg-green-100'"
                    @click="decision='Accept'">Accept Note</button>
                </div>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Review Remark</p>
                <textarea v-model="remark"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows="4"
                  placeholder="Record explanation for the cash shortage, staff feedback, handover note, or next review action..."></textarea>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Resolution Tracking</p>
                <div class="bg-gray-50 rounded-lg px-4 py-3 space-y-2">
                  <div class="flex justify-between text-xs">
                    <span class="text-gray-400">Status</span>
                    <span class="font-semibold text-yellow-600">Under Review</span>
                  </div>
                  <div class="flex justify-between text-xs">
                    <span class="text-gray-400">Next action</span>
                    <span class="font-semibold text-gray-900">Await cashier explanation</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Warning -->
          <div class="bg-orange-50 border border-orange-200 rounded-xl px-5 py-3">
            <p class="text-xs font-medium text-red-600">⚠ Difference requires manager remark before final shift sign-off.</p>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

defineEmits(['close'])

const category = ref('Cash shortage')
const decision = ref('')
const remark = ref('')

const tenders = [
  { type: 'Cash',         system: '₦186,500', counted: '₦145,200',   diff: '₦41,300' },
  { type: 'POS Terminal', system: '₦402,700', counted: '₦402,700',   diff: '₦0.00' },
  { type: 'Transfer',     system: '₦97,000',  counted: '₦97,000',    diff: '₦0.00' },
  { type: 'Post to Room', system: '₦115,000', counted: 'Auto posted', diff: '₦0.00' },
]

function resolve() {
  if (!remark.value) {
    alert('Please add a review remark before resolving.')
    return
  }
}
</script>