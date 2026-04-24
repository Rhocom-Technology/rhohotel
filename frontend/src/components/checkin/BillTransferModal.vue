<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:960px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Bill Transfer</h2>
            <p class="text-xs text-gray-400 mt-1">Move selected charges in or out between individual guest folios and corporate billing profiles while keeping audit trace intact</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Current Billing Context -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4 flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-blue-700 mb-1">Current Billing Context</p>
              <p class="text-xs text-blue-600">OGUMBA WAYNE • Room 8408 • Current folio balance ₦41,000 • Active stay linked to Executive Room</p>
            </div>
            <span class="px-3 py-1 text-xs font-semibold bg-yellow-100 text-yellow-600 rounded-full flex-shrink-0">Status</span>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

            <!-- Transfer Setup -->
            <div class="bg-white rounded-xl border border-blue-300 border-2 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Transfer Setup</h3>
              <div class="space-y-4">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Transfer Type</p>
                    <select v-model="transferType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option>Transfer Out</option>
                      <option>Transfer In</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Target Party Type</p>
                    <select v-model="targetPartyType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option>Corporate</option>
                      <option>Individual Guest</option>
                    </select>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Target Party</p>
                  <input type="text" placeholder="Select corporate account or individual guest"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Transfer Reason <span class="text-red-400">*</span></p>
                  <select v-model="transferReason" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                    <option value="">Select</option>
                    <option>Corporate billing arrangement</option>
                    <option>Guest split billing</option>
                    <option>Management instruction</option>
                    <option>Error correction</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Transfer Note</p>
                  <textarea v-model="transferNote" rows="4"
                    placeholder="Add internal explanation, guest approval, corporate billing note, or finance instruction"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-2">Direction Examples</p>
                  <div class="px-3 py-2 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">
                    Guest to Corporate • Corporate to Guest • Guest to Guest • Corporate to Corporate
                  </div>
                </div>
              </div>
            </div>

            <!-- Charge Selection and Impact -->
            <div class="space-y-4">
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div class="px-5 py-4 border-b border-gray-100">
                  <h3 class="text-sm font-bold text-gray-900">Charge Selection and Impact</h3>
                </div>
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100 bg-gray-50">
                      <th class="px-4 py-3 w-8"></th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Charge</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Type</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Date</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-3 py-3">Amount</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Amount to Transfer</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in charges" :key="c.name" class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3">
                        <input type="checkbox" v-model="c.selected" class="accent-blue-600 w-3.5 h-3.5" />
                      </td>
                      <td class="px-3 py-3 text-xs font-medium text-gray-900">{{ c.name }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ c.type }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ c.date }}</td>
                      <td class="px-3 py-3 text-xs text-right text-gray-700">{{ c.amount }}</td>
                      <td class="px-3 py-3">
                        <div class="h-2 w-20 bg-gray-200 rounded-full">
                          <div class="h-2 bg-blue-400 rounded-full" :style="{ width: c.selected ? '70%' : '0%' }"></div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Transfer Result -->
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h4 class="text-xs font-bold text-gray-900 mb-3">Transfer Result</h4>
                <div class="space-y-2">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-500">Total Amount to Transfer</span>
                    <div class="h-2 w-24 bg-gray-200 rounded-full">
                      <div class="h-2 bg-blue-400 rounded-full w-3/4"></div>
                    </div>
                  </div>
                  <div class="text-xs text-gray-600">Target Party After Transfer: Acme Corporate Account</div>
                </div>
              </div>

              <!-- Policy Notes -->
              <div class="bg-yellow-50 rounded-xl border border-yellow-200 px-5 py-4">
                <p class="text-xs font-bold text-yellow-700 mb-2">Policy Notes</p>
                <p class="text-xs text-yellow-600">Transfer Out removes selected charges from the active guest folio.</p>
                <p class="text-xs text-yellow-600 mt-1">Transfer In brings selected charges from another party into this current guest folio.</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Transfer Charges</button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-800 rounded-lg hover:bg-blue-900 transition-colors">Send For Approval</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive } from 'vue'
defineEmits(['close'])

const transferType = ref('Transfer Out')
const targetPartyType = ref('Corporate')
const transferReason = ref('')
const transferNote = ref('')

const charges = reactive([
  { name: 'Room Charge',    type: 'Room',   date: '21 Feb', amount: '₦120,000', selected: true },
  { name: 'Restaurant Bill',type: 'FandB',  date: '22 Feb', amount: '₦18,000',  selected: false },
  { name: 'Laundry Charge', type: 'Service',date: '22 Feb', amount: '₦6,000',   selected: true },
])
</script>