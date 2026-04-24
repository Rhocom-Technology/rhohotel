<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:800px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-4 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Room {{ room.room_number }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">Occupied room stay control modal</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-6">

          <!-- Status Banner -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2.5 py-0.5 text-xs font-bold bg-blue-100 text-blue-600 rounded-full">OCCUPIED</span>
              <span class="px-2.5 py-0.5 text-xs font-bold bg-green-100 text-green-600 rounded-full">CLEAN</span>
              <span v-if="room.overdue" class="px-2.5 py-0.5 text-xs font-bold bg-red-100 text-red-500 rounded-full">DUE TODAY</span>
            </div>
            <p class="text-xs text-gray-500 leading-relaxed">Guest is in-house. Review stay details, invoice position, outstanding amount, payment options, and departure actions from this single control modal.</p>
          </div>

          <!-- Room Details -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-3">Room Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Room Type</p>
                <p class="text-sm font-bold text-gray-900">{{ room.room_type }}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Floor</p>
                <p class="text-sm font-bold text-gray-900">{{ room.floor }}{{ ordinal(room.floor) }} Floor</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Status</p>
                <p class="text-sm font-bold text-blue-600">{{ room.status }}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Housekeeping</p>
                <p class="text-sm font-bold text-green-600">{{ room.housekeeping_status }}</p>
              </div>
            </div>
          </div>

          <!-- Current Check-in Details -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-3">Current Check-in Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Guest</p>
                <p class="text-sm font-bold text-gray-900">{{ room.current_guest || '—' }}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Expected Check-out</p>
                <p class="text-sm font-bold text-gray-900">{{ checkoutDate }}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Check-in Time</p>
                <p class="text-sm font-bold text-gray-900">{{ checkinDate }}</p>
              </div>
              <div class="bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Stay Position</p>
                <p class="text-sm font-bold" :class="room.overdue ? 'text-blue-600' : 'text-gray-900'">
                  {{ room.overdue ? 'Departure due today' : 'In-house stay' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Invoices and Payment -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-3">Invoices and Payment</h3>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Invoice</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Total</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="inv in invoices" :key="inv.id" class="border-b border-gray-50 last:border-0">
                    <td class="px-5 py-3 text-xs text-gray-700">{{ inv.id }}</td>
                    <td class="px-4 py-3 text-xs text-right text-gray-700">{{ inv.total }}</td>
                    <td class="px-5 py-3 text-xs text-right font-semibold"
                      :class="inv.outstanding === '₦ 0.00' ? 'text-gray-400' : 'text-red-500'">{{ inv.outstanding }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- Payment Controls -->
            <div class="flex items-center gap-2 mt-3 flex-wrap">
              <input type="text" placeholder="Mode: Cash"
                class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none" style="min-width:120px;" />
              <input type="text" placeholder="Reference optional"
                class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none flex-1" style="min-width:140px;" />
              <button class="px-4 py-2 text-xs font-bold text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors">Pay Selected</button>
              <button class="px-4 py-2 text-xs font-bold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">Pay All</button>
              <button class="px-4 py-2 text-xs font-bold text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
                @click="goCheckout">Checkout</button>
              <span class="text-xs font-bold text-gray-700 ml-1">Outstanding: ₦ 0.00</span>
            </div>
          </div>

          <!-- Actions -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-3">Actions</h3>
            <div class="flex items-center gap-2 flex-wrap">
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
                @click="goCheckout">Check-out</button>
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-teal-500 rounded-lg hover:bg-teal-600 transition-colors"
                @click="goCheckin">Open Check-in</button>
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-yellow-500 rounded-lg hover:bg-yellow-600 transition-colors"
                @click="goMaintenance">Maintenance Request</button>
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                @click="goHousekeeping">Housekeeping Request</button>
              <button class="px-4 py-2.5 text-xs font-bold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="goRoomDetails">Room Details</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  room: { type: Object, required: true },
})
const emit = defineEmits(['close'])
const router = useRouter()

const invoices = [
  { id: 'ACC-SINV-2026-02415', total: '₦ 90,000.00', outstanding: '₦ 0.00' },
  { id: 'ACC-SINV-2026-02412', total: '₦ 90,000.00', outstanding: '₦ 0.00' },
]

const checkinDate = '05 Apr 2026 • 1:10 PM'
const checkoutDate = computed(() => props.room.overdue ? '08 Apr 2026 • 12:00 PM' : '24 Apr 2026 • 12:00 PM')

function ordinal(n) {
  const s = ['th','st','nd','rd']
  const v = n % 100
  return s[(v-20)%10] || s[v] || s[0]
}

function goCheckout() {
  emit('close')
  router.push('/check-outs/' + (props.room.name || props.room.room_number))
}

function goCheckin() {emit('close')
  router.push('/check-ins/' + props.room.name)
}
function goMaintenance() { emit('close'); router.push('/maintenance/new-request') }
function goHousekeeping() { emit('close'); router.push('/housekeeping/task/new') }
function goRoomDetails() { emit('close'); router.push('/rooms/' + props.room.room_number) }
</script>