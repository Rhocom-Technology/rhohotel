<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-10 text-sm text-gray-400 text-center">Loading reservation...</div>
    <div v-else-if="error" class="bg-white rounded-xl border border-red-200 px-6 py-10 text-sm text-red-500 text-center">{{ error }}</div>

    <template v-else>
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <div class="flex items-start justify-between mb-3">
          <div>
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <h2 class="text-xl font-bold text-gray-900">{{ reservation.name }}</h2>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="statusClass">{{ reservation.status || 'Draft' }}</span>
              <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-500 rounded-full border border-blue-200">{{ reservation.reservation_type || 'Individual' }}</span>
            </div>
            <p class="text-xs text-gray-400">
              Guest: {{ reservation.primary_guest_name || reservation.customer || '—' }} •
              Arrival {{ formatDate(reservation.from_date) }} •
              Departure {{ formatDate(reservation.to_date) }} •
              {{ reservation.number_of_nights || 0 }} nights
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 flex-wrap mt-4">
          <button @click="emit('openPayments')" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Receive Payment</button>
          <button @click="showAdjustModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Adjust Reservation</button>
          <button @click="showChangeRoomModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Change Room</button>
          <button :disabled="actionLoading" @click="emit('checkIn')" class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-40">Check In Guest</button>
          <button @click="emit('refresh')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Refresh</button>
          <button :disabled="actionLoading" @click="emit('cancelReservation')" class="px-4 py-2 text-xs font-medium text-red-500 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-40">Cancel Reservation</button>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;" class="divide-x divide-gray-100">
          <div class="pr-6">
            <p class="text-xs text-gray-400 mb-1">Grand Total</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.total_amount) }}</p>
          </div>
          <div class="px-6">
            <p class="text-xs text-gray-400 mb-1">Subtotal</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.subtotal) }}</p>
          </div>
          <div class="px-6">
            <p class="text-xs text-gray-400 mb-1">Discount</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.discount_amount) }}</p>
          </div>
          <div class="pl-6">
            <p class="text-xs text-gray-400 mb-1">Linked Payment</p>
            <p class="text-sm font-bold text-gray-900">{{ reservation.payment_entry || 'None' }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Reserved Rooms</h3>
        <div class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Guest</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate/Night</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="rooms.length === 0">
                <td colspan="5" class="px-3 py-4 text-center text-xs text-gray-300">No room rows found.</td>
              </tr>
              <tr v-for="row in rooms" :key="row.name || row.idx" class="border-t border-gray-100">
                <td class="px-3 py-2 text-xs text-gray-700">{{ row.room_number || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ row.room_type || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ row.guest_name || reservation.primary_guest_name || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(row.rate_per_night) }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(row.room_total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="showAdjustModal" class="fixed inset-0 z-50 overflow-y-auto" style="background:rgba(0,0,0,0.55);">
        <div class="min-h-screen flex items-start justify-center py-8 px-4">
          <div class="bg-white rounded-2xl shadow-2xl w-full" style="max-width:900px;">
            <StayAdjustment :reservation="reservation" @close="showAdjustModal = false" />
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showChangeRoomModal" class="fixed inset-0 z-50 overflow-y-auto" style="background:rgba(0,0,0,0.55);">
        <div class="min-h-screen flex items-start justify-center py-8 px-4">
          <div class="bg-white rounded-2xl shadow-2xl w-full" style="max-width:900px;">
            <ChangeRoom :reservation="reservation" @close="showChangeRoomModal = false" />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import StayAdjustment from '@/components/reservations/StayAdjustment.vue'
import ChangeRoom from '@/components/reservations/ChangeRoom.vue'

const props = defineProps({
  reservation: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  actionLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['refresh', 'openPayments', 'checkIn', 'cancelReservation'])

const showAdjustModal = ref(false)
const showChangeRoomModal = ref(false)

const rooms = computed(() => props.reservation?.rooms || [])

const statusClass = computed(() => {
  const status = String(props.reservation?.status || '').toLowerCase()
  if (status === 'confirmed') return 'bg-yellow-50 text-yellow-700 border-yellow-200'
  if (status === 'checked in') return 'bg-green-50 text-green-700 border-green-200'
  if (status === 'cancelled') return 'bg-red-50 text-red-700 border-red-200'
  return 'bg-gray-50 text-gray-700 border-gray-200'
})

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>