<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:900px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Refund Request</h2>
            <p class="text-xs text-gray-400 mt-1">Create a refund request for guest billing reversal, early departure balance return, overpayment, or approved service recovery credit</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Guest Billing Context -->
          <div class="bg-red-50 rounded-xl border border-red-100 px-5 py-4">
            <p class="text-sm font-bold text-red-600 mb-1">Guest Billing Context</p>
            <p class="text-xs text-red-500 mb-3">OGUMBA WAYNE • Room 8408 • Checked In • Current balance ₦41,000 • Refunds require financial validation and approval routing</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Approval Needed</span>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

            <!-- Refund Details -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Refund Details</h3>
              <div class="space-y-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Refund Type</p>
                  <select v-model="refundType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                    <option value="">Select</option>
                    <option>Overpayment Reversal</option>
                    <option>Early Departure Balance Return</option>
                    <option>Service Recovery Credit</option>
                    <option>Billing Error Correction</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Source Invoice or Payment</p>
                  <input type="text" v-model="sourceInvoice"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Refund Amount</p>
                    <div class="px-3 py-2.5 text-xs font-bold text-red-500 bg-red-50 border border-red-200 rounded-lg">₦ 41,000.00</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Refund Method</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">Cash / transfer</div>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Refund Reason</p>
                  <textarea v-model="refundReason" rows="3"
                    placeholder="Explain why the refund is required and what source transaction is being reversed"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Supporting Document</p>
                  <input type="text" placeholder="Attach approval reference or finance note"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
            </div>

            <!-- Financial Validation -->
            <div class="space-y-4">
              <h3 class="text-sm font-bold text-gray-900">Financial Validation</h3>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <p class="text-xs font-bold text-gray-900 mb-3">Source Transaction Check</p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                  <div class="text-xs text-gray-600">Invoice Total: ₦41,000.00</div>
                  <div class="text-xs text-gray-600">Outstanding: ₦41,000.00</div>
                  <div class="text-xs text-gray-600">Paid Amount: ₦41,000.00</div>
                  <div class="text-xs font-bold text-gray-900">Refundable: ₦41,000.00</div>
                </div>
              </div>

              <div class="bg-yellow-50 rounded-xl border border-yellow-200 px-5 py-4">
                <p class="text-xs font-bold text-yellow-700 mb-2">Approval Governance</p>
                <p class="text-xs text-yellow-600 leading-relaxed">Refund requests above threshold require finance or manager approval before payment release.</p>
                <p class="text-xs text-yellow-500 mt-1">Policy route: Front Desk → Finance → Cashier release.</p>
              </div>

              <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
                <p class="text-xs font-bold text-blue-700 mb-2">Posting Impact</p>
                <p class="text-xs text-blue-600 leading-relaxed">Refund will create reversal records, update folio balance, and sync guest account history.</p>
              </div>

              <div class="bg-green-50 rounded-xl border border-green-200 px-5 py-4">
                <p class="text-xs font-bold text-green-700 mb-2">Guest Notification</p>
                <p class="text-xs text-green-600 leading-relaxed">Optional WhatsApp and email refund confirmation can be triggered after approval and payment.</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Submit Request</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
defineEmits(['close'])

const refundType = ref('')
const sourceInvoice = ref('ACC-SINV-2026-02365')
const refundReason = ref('')
</script>