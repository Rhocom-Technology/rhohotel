<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl" style="max-width:480px;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Apply Discount</h2>
            <p class="text-xs text-gray-400 mt-1">Creates a credit note against this folio</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm">✕</button>
        </div>

        <div class="px-8 py-6 space-y-4">

          <!-- Error -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-600">{{ error }}</p>
          </div>

          <!-- Context -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
            <p class="text-xs text-blue-700 font-semibold">{{ checkIn.guest }}</p>
            <p class="text-xs text-blue-500 mt-0.5">Room {{ checkIn.room_number }} • Total Charges {{ fmt(checkIn.total_charges) }}</p>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Discount Amount (₦) <span class="text-red-400">*</span></p>
            <input type="number" v-model.number="discountAmount" min="0.01" step="0.01"
              placeholder="Enter amount"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Reason <span class="text-red-400">*</span></p>
            <textarea v-model="reason" rows="3"
              placeholder="Explain why the discount is being applied"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button :disabled="submitting || !(discountAmount > 0) || !reason.trim()"
              @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Applying…' : 'Apply Discount' }}
            </button>
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

const discountAmount = ref(0)
const reason = ref('')
const submitting = ref(false)
const error = ref('')

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

async function submit() {
  if (!(discountAmount.value > 0) || !reason.value.trim()) return
  submitting.value = true
  error.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.apply_discount', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({
        check_in_name: props.checkIn.name,
        discount_amount: discountAmount.value,
        reason: reason.value,
      }),
    })
    const data = await res.json()
    if (data.exc) {
      try {
        const msgs = JSON.parse(data._server_messages || '[]')
        error.value = JSON.parse(msgs[0]).message || 'Failed to apply discount.'
      } catch { error.value = 'Failed to apply discount.' }
      return
    }
    emit('done', data.message)
    emit('close')
  } catch {
    error.value = 'Network error. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
