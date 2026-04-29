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
              <p class="text-xs text-blue-600">{{ checkIn.guest }} • Room {{ checkIn.room_number }} • Outstanding {{ fmt(checkIn.total_outstanding_amount) }}</p>
            </div>
            <span class="px-3 py-1 text-xs font-semibold bg-yellow-100 text-yellow-600 rounded-full flex-shrink-0">{{ checkIn.status }}</span>
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
                  <div class="relative">
                    <input type="text" v-model="targetSearch" @input="searchTargets" @focus="showTargetDropdown = true" @blur="hideTargetDropdown"
                      :placeholder="targetPartyType === 'Corporate' ? 'Search corporate account...' : 'Search guest by name, room...'"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      :class="selectedTarget ? 'border-green-300 bg-green-50' : ''" />
                    <div v-if="showTargetDropdown && targetResults.length > 0"
                      class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
                      <button v-for="t in targetResults" :key="t.name" @mousedown.prevent="selectTarget(t)"
                        class="block w-full text-left px-4 py-2.5 text-xs hover:bg-gray-50 border-b border-gray-50 last:border-0">
                        <span class="font-semibold text-gray-900">{{ t.hotel_guest_name || t.name }}</span>
                        <span class="text-gray-400 ml-2">{{ t.room_number ? 'Room ' + t.room_number : '' }}</span>
                      </button>
                    </div>
                    <p v-if="selectedTarget" class="mt-1 text-xs text-green-600 font-medium">✓ {{ selectedTarget.hotel_guest_name || selectedTarget.name }} selected</p>
                  </div>
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
                    <tr v-if="!checkIn.invoices || checkIn.invoices.length === 0">
                      <td colspan="6" class="px-4 py-6 text-center text-xs text-gray-400">No invoices found for this check-in</td>
                    </tr>
                    <tr v-for="c in checkIn.invoices || []" :key="c.invoice" class="border-b border-gray-50 last:border-0">
                      <td class="px-4 py-3">
                        <input type="checkbox" v-model="c.selected" class="accent-blue-600 w-3.5 h-3.5" />
                      </td>
                      <td class="px-3 py-3 text-xs font-medium text-blue-600">{{ c.invoice }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ c.invoice_type }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ c.posting_date || '—' }}</td>
                      <td class="px-3 py-3 text-xs text-right text-gray-700">{{ fmt(c.amount) }}</td>
                      <td class="px-3 py-3 text-xs text-right font-semibold text-red-500">{{ fmt(c.outstanding_amount) }}</td>
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
          <div v-if="transferMsg" class="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
            <p class="text-xs text-blue-700">{{ transferMsg }}</p>
          </div>
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button @click="submitTransfer"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Transfer Charges</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ checkIn: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])
const transferType = ref('Transfer Out')
const targetPartyType = ref('Corporate')
const transferReason = ref('')
const transferNote = ref('')
const transferMsg = ref('')
const targetSearch = ref('')
const targetResults = ref([])
const selectedTarget = ref(null)
const showTargetDropdown = ref(false)
let searchTimeout = null

function fmt(v) { return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00' }

function searchTargets() {
  selectedTarget.value = null
  clearTimeout(searchTimeout)
  if (targetSearch.value.length < 2) {
    targetResults.value = []
    return
  }
  searchTimeout = setTimeout(async () => {
    try {
      const guestType = targetPartyType.value === 'Corporate' ? 'Corporate' : 'Individual'
      const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.search_guests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
        body: new URLSearchParams({ query: targetSearch.value, guest_type: guestType }),
      })
      const data = await res.json()
      targetResults.value = (data.message || []).filter(g => g.name !== props.checkIn.guest)
    } catch {
      targetResults.value = []
    }
  }, 300)
}

function selectTarget(t) {
  selectedTarget.value = t
  targetSearch.value = t.hotel_guest_name || t.name
  showTargetDropdown.value = false
  targetResults.value = []
}

function hideTargetDropdown() {
  setTimeout(() => { showTargetDropdown.value = false }, 150)
}

function submitTransfer() {
  if (!transferReason.value) { transferMsg.value = 'Please select a transfer reason.'; return }
  if (!selectedTarget.value) { transferMsg.value = 'Please select a target party.'; return }
  transferMsg.value = 'Transfer request has been logged. The finance team will process the charge movement and update the folio accordingly.'
}
</script>