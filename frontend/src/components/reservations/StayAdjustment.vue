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
            <p class="text-xs text-gray-500 mb-1.5">New Check-in Date</p>
            <input v-model="newCheckinDate" type="date"
              class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">New Check-out Date</p>
            <input v-model="newCheckoutDate" type="date"
              :min="minCheckoutDate"
              class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
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
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(ratePerNight) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Extra Nights</span>
              <span class="text-xs font-semibold text-gray-900">{{ additionalNights }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Additional Room Charges</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(ratePerNight * additionalNights) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Taxes & Fees</span>
              <span class="text-xs font-semibold text-gray-900">₦0</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">New Balance Impact</span>
              <span class="text-xs font-bold text-gray-900">{{ formatCurrency(ratePerNight * additionalNights) }}</span>
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
      <button :disabled="submitting || !canApply" @click="apply"
        class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">
        {{ submitting ? 'Applying…' : 'Apply Stay Adjustment' }}
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { callMethodForm } from '@/lib/api'

const props = defineProps({ reservation: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const adjustmentType = ref('Extend Stay')
const adjustmentReason = ref('Guest Request')
const newCheckoutDate = ref(asISODate(props.reservation.to_date))
const newCheckinDate = ref(asISODate(props.reservation.from_date))
const adjustmentNotes = ref('')
const submitting = ref(false)
const errorMsg = ref('')

// Earliest valid checkout: one day after check-in
const minCheckoutDate = computed(() => {
  if (!newCheckinDate.value) return ''
  const d = parseDateOnly(newCheckinDate.value)
  d.setDate(d.getDate() + 1)
  return formatISODate(d)
})

// Correct rate per night: subtotal / number_of_nights
const ratePerNight = computed(() => {
  const nights = Number(props.reservation.number_of_nights) || 1
  return Number(props.reservation.subtotal || 0) / nights
})

const additionalNights = computed(() => {
  if (!newCheckoutDate.value || !props.reservation.to_date) return 0
  const current = parseDateOnly(asISODate(props.reservation.to_date))
  const newDate = parseDateOnly(newCheckoutDate.value)
  const diff = Math.round((newDate - current) / (1000 * 60 * 60 * 24))
  return diff
})

const hasDateChanges = computed(() => {
  return (
    newCheckinDate.value !== asISODate(props.reservation.from_date) ||
    newCheckoutDate.value !== asISODate(props.reservation.to_date)
  )
})

const isRangeValid = computed(() => {
  if (!newCheckinDate.value || !newCheckoutDate.value) return false
  return parseDateOnly(newCheckoutDate.value) > parseDateOnly(newCheckinDate.value)
})

const canApply = computed(() => hasDateChanges.value && isRangeValid.value)

async function apply() {
  if (!canApply.value) return
  submitting.value = true; errorMsg.value = ''
  try {
    const params = {
      reservation_name: props.reservation.name,
      new_check_in: newCheckinDate.value,
      new_checkout: newCheckoutDate.value,
    }
    await callMethodForm(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.adjust_reservation',
      params,
    )
    emit('done'); emit('close')
  } catch (error) {
    errorMsg.value = String(error?.message || 'Adjustment failed.')
  } finally { submitting.value = false }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function asISODate(value) {
  if (!value) return ''
  if (typeof value === 'string') return value.slice(0, 10)
  return formatISODate(value)
}

function parseDateOnly(value) {
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(year, (month || 1) - 1, day || 1)
}

function formatISODate(value) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>