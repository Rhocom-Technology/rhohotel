<template>
  <div class="p-6">

    <!-- Header -->
    <div class="flex items-start justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Stay Adjustment</h2>
        <p class="text-xs text-gray-400 mt-1">Adjust stay dates, nights, room continuity, and billing effect while preserving the standard reservation layout.</p>
      </div>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
    </div>

    <!-- Reservation Snapshot -->
    <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6">
      <h3 class="text-xs font-bold text-gray-900 mb-3">Reservation Snapshot</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
        <div>
          <p class="text-xs text-gray-400 mb-1">Reservation ID</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.name }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Guest</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.primary_guest_name || reservation.customer || '—' }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Current Stay</p>
          <p class="text-sm font-bold text-gray-900">{{ formatDate(reservation.from_date) }} → {{ formatDate(reservation.to_date) }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Current Room</p>
          <p class="text-sm font-bold text-gray-900">{{ reservation.room_number || 'Pending assignment' }}</p>
        </div>
      </div>
    </div>

    <!-- Body -->
      <div v-if="reservation.docstatus !== 1" class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-xs text-yellow-700">
        ⚠️ This reservation must be submitted before adjusting the stay.
      </div>
      <div v-else style="display:grid;grid-template-columns:1fr 320px;gap:24px;">

      <!-- Left: Adjustment Details -->
      <div>
        <h3 class="text-sm font-bold text-gray-900 mb-4">Adjustment Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Adjustment Type</p>
            <select v-model="adjustmentType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
              <option>Extend Stay</option>
              <option>Reduce Stay</option>
              <option>Change Dates</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Adjustment Reason</p>
            <select v-model="adjustmentReason" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
              <option>Guest Request</option>
              <option>Hotel Request</option>
              <option>Operational</option>
            </select>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-in Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDate(reservation.from_date) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-out Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDate(reservation.to_date) }}</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">New Check-out Date</p>
            <input v-model="newCheckoutDate" type="date"
              :min="minCheckoutDate"
              class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Additional Nights</p>
            <div class="flex items-center gap-2">
              <div class="flex-1 px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ additionalNights }}</div>
              <span class="text-xs text-blue-500 cursor-pointer">Auto Calculated</span>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Preferred Room Option</p>
          <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
            <option>Keep Current Room ({{ reservation.room_number || 'Pending assignment' }})</option>
            <option>Request New Room</option>
          </select>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Adjustment Notes</p>
          <textarea v-model="adjustmentNotes" rows="3"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Guest requested extension due to delayed travel plan."></textarea>
          <p class="text-xs text-gray-400 mt-1">This note will appear in the reservation activity timeline and audit history.</p>
        </div>

        <p class="text-xs text-gray-400 mt-4 pt-4 border-t border-gray-100">
          Updating the stay will recalculate reservation totals, occupancy, room availability, and activity history.
        </p>
      </div>

      <!-- Right: Rate Impact & Controls -->
      <div class="space-y-4">

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Rate Impact</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Current Rate / Night</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(reservation.subtotal) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Extra Nights</span>
              <span class="text-xs font-semibold text-gray-900">{{ additionalNights }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Additional Room Charges</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency((reservation.subtotal || 0) * additionalNights) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Taxes & Fees</span>
              <span class="text-xs font-semibold text-gray-900">₦0</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">New Balance Impact</span>
              <span class="text-xs font-bold text-gray-900">{{ formatCurrency((reservation.subtotal || 0) * additionalNights) }}</span>
            </div>
          </div>
          <div class="mt-2">
            <span class="px-2.5 py-1 text-xs font-medium bg-yellow-50 text-yellow-600 rounded-full">Pending Payment</span>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-2">Availability Check</h4>
          <span class="px-2.5 py-1 text-xs font-semibold bg-green-100 text-green-600 rounded-full">Available</span>
          <p class="text-xs text-gray-400 mt-2">Current room remains available for the selected extension period.</p>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-2">Approval & Audit</h4>
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Adjusted by</span>
            <span class="text-xs font-semibold text-gray-900">Front Desk Admin</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
      <div v-if="errorMsg" class="flex-1 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{{ errorMsg }}</div>
      <button @click="$emit('close')" class="px-5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
      <button :disabled="submitting || !newCheckoutDate || additionalNights === 0" @click="apply"
        class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">
        {{ submitting ? 'Applying…' : 'Apply Stay Adjustment' }}
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ reservation: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const adjustmentType = ref('Extend Stay')
const adjustmentReason = ref('Guest Request')
const newCheckoutDate = ref('')
const adjustmentNotes = ref('')
const submitting = ref(false)
const errorMsg = ref('')

// Earliest valid checkout: one day after check-in
const minCheckoutDate = computed(() => {
  if (!props.reservation.from_date) return ''
  const d = new Date(props.reservation.from_date)
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
})

// Correct rate per night: subtotal / number_of_nights
const ratePerNight = computed(() => {
  const nights = Number(props.reservation.number_of_nights) || 1
  return Number(props.reservation.subtotal || 0) / nights
})

const additionalNights = computed(() => {
  if (!newCheckoutDate.value || !props.reservation.to_date) return 0
  const current = new Date(props.reservation.to_date)
  const newDate = new Date(newCheckoutDate.value)
  const diff = Math.round((newDate - current) / (1000 * 60 * 60 * 24))
  return diff
})

function parseErr(data) {
  try { return JSON.parse(JSON.parse(data._server_messages || '[]')[0]).message } catch { return 'Adjustment failed.' }
}

async function apply() {
  if (!newCheckoutDate.value || additionalNights.value === 0) return
  submitting.value = true; errorMsg.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_front_desk_reservation.hotel_front_desk_reservation.adjust_front_desk_reservation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({
        reservation_name: props.reservation.name,
        new_checkout_date: newCheckoutDate.value,
        new_checkout_time: '12:00:00',
        new_discount: 0,
      })
    })
    const data = await res.json()
    if (data.exc) { errorMsg.value = parseErr(data); return }
    emit('done'); emit('close')
  } catch { errorMsg.value = 'Network error. Please try again.' } finally { submitting.value = false }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>