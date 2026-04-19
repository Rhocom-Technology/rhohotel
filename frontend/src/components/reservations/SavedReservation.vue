<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <div class="flex items-start justify-between mb-3">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <h2 class="text-xl font-bold text-gray-900">{{ reservation.name }}</h2>
            <span class="px-2.5 py-1 text-xs font-semibold bg-yellow-50 text-yellow-600 rounded-full border border-yellow-200">Confirmed</span>
            <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-500 rounded-full border border-blue-200">{{ reservation.reservation_type || 'Individual' }}</span>
            <span class="px-2.5 py-1 text-xs font-semibold bg-red-500 text-white rounded-full">Payment Pending</span>
          </div>
          <p class="text-xs text-gray-400">
            Guest: {{ reservation.primary_guest_name || reservation.customer || '—' }} •
            Arrival {{ formatDate(reservation.from_date) }} •
            Departure {{ formatDate(reservation.to_date) }} •
            {{ reservation.number_of_nights }} nights •
            Grand Total {{ formatCurrency(reservation.total_amount) }}
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2 flex-wrap mt-4">
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Receive Payment</button>
        <button @click="showAdjustModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Adjust Reservation</button>
<button @click="showChangeRoomModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Change Room</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Check In Guest</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Send Confirmation</button>
        <button class="px-4 py-2 text-xs font-medium text-red-500 border border-red-200 rounded-lg hover:bg-red-50">Cancel Reservation</button>
      </div>
    </div>

    <!-- Financial Summary Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;" class="divide-x divide-gray-100">
        <div class="pr-6">
          <p class="text-xs text-gray-400 mb-1">Grand Total</p>
          <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.total_amount) }}</p>
          <p class="text-xs text-blue-500 mt-1">Rate less discount</p>
        </div>
        <div class="px-6">
          <p class="text-xs text-gray-400 mb-1">Amount Paid</p>
          <p class="text-2xl font-bold text-gray-900">₦0</p>
          <p class="text-xs text-red-400 mt-1">No payment received yet</p>
        </div>
        <div class="px-6">
          <p class="text-xs text-gray-400 mb-1">Outstanding</p>
          <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.total_amount) }}</p>
          <p class="text-xs text-orange-400 mt-1">Awaiting deposit or full payment</p>
        </div>
        <div class="pl-6">
          <p class="text-xs text-gray-500 mb-1">Reservation Readiness</p>
          <p class="text-sm font-bold text-gray-900">Ready for payment, adjustment, or check-in</p>
          <p class="text-xs text-gray-400 mt-1">Front desk can complete payment first, then check in the guest.</p>
        </div>
      </div>
    </div>

    <!-- Body Card -->
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <div style="display:grid;grid-template-columns:1fr 360px;gap:32px;">

        <!-- Left: Saved Reservation Details -->
        <div>
          <h3 class="text-sm font-bold text-gray-900 mb-4">Saved Reservation Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-400 mb-1">Guest</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">
                {{ reservation.primary_guest_name || reservation.customer || '—' }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Reservation Type</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ reservation.reservation_type || 'Individual' }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">From Date</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ formatDate(reservation.from_date) }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">To Date</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ formatDate(reservation.to_date) }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Nights</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ reservation.number_of_nights || '—' }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Status</p>
              <div class="bg-yellow-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-yellow-600">
                Reserved
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Room Type</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">—</div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Room Number</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-400 italic">
                Pending assignment
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Rate</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ formatCurrency(reservation.subtotal) }} per night
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1">Discount</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                {{ reservation.discount ? `${reservation.discount}% = ${formatCurrency(reservation.discount_amount)}` : '—' }}
              </div>
            </div>
          </div>

          <h3 class="text-sm font-bold text-gray-900 mt-6 mb-3">Reservation Notes</h3>
          <div class="bg-gray-50 rounded-lg px-4 py-3 text-xs text-gray-400 min-h-16 border border-gray-100">
            No reservation notes added.
          </div>

          <h3 class="text-sm font-bold text-gray-900 mt-6 mb-3">Invoice & Payment</h3>
          <div class="bg-gray-50 rounded-lg p-4 min-h-16 text-center text-xs text-gray-400 border border-gray-100">
            No invoices yet.
          </div>
        </div>

        <!-- Right: Reservation Control -->
        <div>
          <h3 class="text-sm font-bold text-gray-900 mb-4">Reservation Control</h3>

          <div class="bg-blue-50 rounded-xl border border-blue-100 p-4 mb-3">
            <h4 class="text-sm font-bold text-blue-700 mb-2">Financial Snapshot</h4>
            <p class="text-xs text-gray-600">Grand Total: {{ formatCurrency(reservation.total_amount) }}</p>
            <p class="text-xs text-gray-600 mt-0.5">Paid: ₦0.00</p>
            <p class="text-xs text-gray-600 mt-0.5">Outstanding: {{ formatCurrency(reservation.total_amount) }}</p>
          </div>

          <div class="bg-yellow-50 rounded-xl border border-yellow-100 p-4 mb-3">
            <h4 class="text-sm font-bold text-yellow-600 mb-2">Action Guidance</h4>
            <p class="text-xs text-yellow-600">Cancel only when booking is withdrawn or cannot be honored.</p>
          </div>

          <div class="bg-green-50 rounded-xl border border-green-100 p-4 mb-6">
            <h4 class="text-sm font-bold text-green-700 mb-2">Check-in Readiness</h4>
            <p class="text-xs text-green-700">Guest can be checked in directly from this saved reservation page.</p>
            <p class="text-xs text-green-600 mt-1">Check-in action carries reservation details into the check-in workflow automatically.</p>
          </div>

          <h3 class="text-sm font-bold text-gray-900 mb-3">Quick Actions</h3>
          <div class="space-y-2">
            <button class="w-full py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors">
              Receive Payment
            </button>
            <button class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-xl hover:bg-green-600 transition-colors">
              Check In Guest
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Stay Adjustment Modal -->
    <Teleport to="body">
      <div v-if="showAdjustModal" class="fixed inset-0 z-50 overflow-y-auto" style="background:rgba(0,0,0,0.55);">
        <div class="min-h-screen flex items-start justify-center py-8 px-4">
          <div class="bg-white rounded-2xl shadow-2xl w-full" style="max-width:900px;">
            <StayAdjustment :reservation="reservation" @close="showAdjustModal = false" />
          </div>
        </div>
      </div>
    </Teleport>


    <!-- Change Room Modal -->
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
import { ref } from 'vue'
import StayAdjustment from '@/components/reservations/StayAdjustment.vue'
import ChangeRoom from '@/components/reservations/ChangeRoom.vue'

const props = defineProps({ reservation: { type: Object, required: true } })
defineEmits(['close'])

const showAdjustModal = ref(false)
const showChangeRoomModal = ref(false)

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>