<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:560px;max-height:92vh;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Refund Request</h2>
            <p class="text-xs text-gray-400 mt-1">Creates a Hotel Refund record pending finance approval</p>
          </div>
          <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-4">
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-600">{{ error }}</p>
          </div>

          <div class="bg-red-50 rounded-xl border border-red-100 px-5 py-4">
            <p class="text-sm font-bold text-red-600 mb-1">Guest Billing Context</p>
            <p class="text-xs text-red-500">{{ checkIn.guest }} • Room {{ checkIn.room_number }} • {{ checkIn.status }}</p>
            <span class="mt-2 inline-block px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Approval Needed</span>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Refund Amount (based on payments received)</p>
            <div v-if="loadingAmount" class="px-3 py-2.5 text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-lg">Loading…</div>
            <div v-else class="px-3 py-2.5 text-xs font-bold text-red-500 bg-red-50 border border-red-200 rounded-lg">{{ fmt(refundAmount) }}</div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Reason <span class="text-red-400">*</span></p>
            <textarea v-model="reason" rows="4"
              placeholder="Explain why the refund is required"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>

          <div class="bg-yellow-50 rounded-xl border border-yellow-200 px-4 py-3">
            <p class="text-xs text-yellow-700">Refund requests require finance approval before payment release. A Hotel Refund document will be created in submitted (Pending Approval) status.</p>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50" @click="$emit('close')">Cancel</button>
            <button :disabled="submitting || loadingAmount || refundAmount <= 0 || !reason.trim()" @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Submitting…' : 'Submit Refund Request' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps({ checkIn: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])
const reason = ref('')
const refundAmount = ref(0)
const loadingAmount = ref(true)
const submitting = ref(false)
const error = ref('')
function fmt(v) { return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00' }
async function apiPost(m, p) {
  const r = await fetch(`/api/method/${m}`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' }, body: new URLSearchParams(p) })
  return r.json()
}
onMounted(async () => {
  try {
    // Get total paid from payment entries
    const data = await apiPost('frappe.client.get_list', {
      doctype: 'Payment Entry',
      filters: JSON.stringify([['custom_hotel_room_check_in', '=', props.checkIn.name], ['docstatus', '=', 1]]),
      fields: JSON.stringify(['paid_amount']),
      limit: 100,
    })
    refundAmount.value = (data.message || []).reduce((s, p) => s + (p.paid_amount || 0), 0)
  } catch { error.value = 'Failed to load payment data.' } finally { loadingAmount.value = false }
})
async function submit() {
  if (!reason.value.trim() || refundAmount.value <= 0) return
  submitting.value = true; error.value = ''
  try {
    const data = await apiPost('rhohotel.rhocom_hotel.api.checkin.create_refund', {
      check_in_name: props.checkIn.name,
      reason: reason.value,
    })
    if (data.exc) {
      try { error.value = JSON.parse(JSON.parse(data._server_messages || '[]')[0]).message } catch { error.value = 'Refund failed.' }
      return
    }
    emit('done', data.message); emit('close')
  } catch { error.value = 'Network error.' } finally { submitting.value = false }
}
</script>
