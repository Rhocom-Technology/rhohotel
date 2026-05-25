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
            <p class="text-xs text-gray-400 mt-0.5">{{ isReserved ? 'Reserved room — upcoming arrival' : 'Occupied room stay control modal' }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-6">

          <!-- Status Banner -->
          <div class="rounded-xl border px-5 py-4"
            :class="isReady ? 'bg-green-50 border-green-100' : isReserved ? 'bg-purple-50 border-purple-100' : room.overdue ? 'bg-red-50 border-red-100' : 'bg-blue-50 border-blue-100'">
            <div class="flex items-center gap-2 mb-2">
              <span v-if="isReady" class="px-2.5 py-0.5 text-xs font-bold bg-green-100 text-green-600 rounded-full">READY</span>
              <span v-else-if="isReserved" class="px-2.5 py-0.5 text-xs font-bold bg-purple-100 text-purple-600 rounded-full">RESERVED</span>
              <span v-else class="px-2.5 py-0.5 text-xs font-bold bg-blue-100 text-blue-600 rounded-full">{{ room.status?.toUpperCase() }}</span>
              <span class="px-2.5 py-0.5 text-xs font-bold rounded-full"
                :class="room.housekeeping_status === 'Clean' || room.housekeeping_status === 'Inspected' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'">
                {{ room.housekeeping_status?.toUpperCase() }}
              </span>
              <span v-if="room.overdue" class="px-2.5 py-0.5 text-xs font-bold bg-red-100 text-red-500 rounded-full">OVERDUE</span>
            </div>
            <p class="text-xs text-gray-500 leading-relaxed">
              <span v-if="isReady">Room is vacant and clean — ready for a new check-in.</span>
              <span v-else-if="isReserved">This room has an upcoming reservation. Open the reservation to initiate check-in or view guest details.</span>
              <span v-else>Guest is in-house. Review stay details, invoice position, outstanding amount, and departure actions from this modal.</span>
            </p>
          </div>

          <!-- Reserved Room Info -->
          <div v-if="isReserved">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Upcoming Reservation</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Expected Guest</p>
                <p class="text-sm font-bold text-gray-900">{{ room.current_guest || room.reserved_for || '—' }}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Arrival Date</p>
                <p class="text-sm font-bold text-gray-900">{{ room.reservation_arrival || room.check_in_date || '—' }}</p>
              </div>
              <div v-if="room.reservation" class="bg-purple-50 rounded-xl border border-purple-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Reservation ID</p>
                <p class="text-sm font-bold text-purple-700">{{ room.reservation }}</p>
              </div>
            </div>
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
          <div v-if="room.check_in">
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
                <p class="text-sm font-bold" :class="room.overdue ? 'text-red-500' : 'text-blue-600'">
                  {{ room.overdue ? 'Departure overdue' : 'In-house stay' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Invoices and Payment -->
          <div v-if="room.check_in">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Invoices and Payment</h3>
            <div v-if="loadingDetail" class="py-6 text-center">
              <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            </div>
            <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Invoice</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Total</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="invoices.length === 0">
                    <td colspan="3" class="px-5 py-6 text-center text-xs text-gray-400">No invoices yet for this stay</td>
                  </tr>
                  <tr v-for="inv in invoices" :key="inv.invoice" class="border-b border-gray-50 last:border-0">
                    <td class="px-5 py-3 text-xs text-gray-700">{{ inv.invoice }}</td>
                    <td class="px-4 py-3 text-xs text-right text-gray-700">{{ formatCurrency(inv.amount) }}</td>
                    <td class="px-5 py-3 text-xs text-right font-semibold"
                      :class="(inv.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-gray-400'">{{ formatCurrency(inv.outstanding_amount) }}</td>
                  </tr>
                </tbody>
                <tfoot v-if="invoices.length > 0">
                  <tr class="border-t border-gray-200 bg-gray-50">
                    <td class="px-5 py-3 text-xs font-bold text-gray-900">Total Outstanding</td>
                    <td></td>
                    <td class="px-5 py-3 text-xs font-bold text-right" :class="totalOutstanding > 0 ? 'text-red-500' : 'text-green-600'">{{ formatCurrency(totalOutstanding) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Actions -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-3">Actions</h3>
            <div class="flex items-center gap-2 flex-wrap">
              <button v-if="isReady"
                class="px-4 py-2.5 text-xs font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                @click="goNewCheckIn">New Check-in</button>
              <button v-if="isReady"
                class="px-4 py-2.5 text-xs font-bold text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
                @click="goMakeReservation">Make Reservation</button>
              <button v-if="isReady"
                :disabled="blockBusy"
                class="px-4 py-2.5 text-xs font-bold text-white bg-orange-500 rounded-lg hover:bg-orange-600 transition-colors"
                @click="blockRoom">{{ blockBusy ? 'Blocking...' : 'Block Room' }}</button>
              <button v-if="isReserved && room.reservation"
                class="px-4 py-2.5 text-xs font-bold text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
                @click="goToReservation">Open Reservation</button>
              <button v-if="isReserved"
                class="px-4 py-2.5 text-xs font-bold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                @click="goCheckInFromReservation">Check In Guest</button>
              <button v-if="!isReady && !isReserved" class="px-4 py-2.5 text-xs font-bold text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
                @click="goCheckout">Check-out</button>
              <button v-if="!isReady && !isReserved" class="px-4 py-2.5 text-xs font-bold text-white bg-teal-500 rounded-lg hover:bg-teal-600 transition-colors"
                @click="goCheckin">Open Check-in</button>
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-yellow-500 rounded-lg hover:bg-yellow-600 transition-colors"
                @click="goMaintenance">Maintenance Request</button>
              <button class="px-4 py-2.5 text-xs font-bold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                @click="goHousekeeping">Housekeeping Request</button>
              <button class="px-4 py-2.5 text-xs font-bold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="goRoomDetails">Room Details</button>
            </div>
            <p v-if="blockError" class="mt-2 text-xs font-medium text-red-600">{{ blockError }}</p>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  room: { type: Object, required: true },
})
const emit = defineEmits(['close'])
const router = useRouter()

const isReady = computed(() =>
  props.room.status === 'Vacant' &&
  (props.room.housekeeping_status === 'Clean' || props.room.housekeeping_status === 'Inspected')
)

const isReserved = computed(() => props.room.status === 'Reserved')

// Check-in detail (fetched when modal opens if there is an active check-in)
const checkinDetail = ref(null)
const loadingDetail = ref(false)

const checkinDate = computed(() => {
  const dt = checkinDetail.value?.check_in_datetime
    || props.room.check_in_datetime
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
})

const checkoutDate = computed(() => {
  const dt = checkinDetail.value?.expected_check_out_datetime
    || props.room.expected_check_out_datetime
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
})

const invoices = computed(() => checkinDetail.value?.invoices || [])
const blockBusy = ref(false)
const blockError = ref('')

const totalOutstanding = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (parseFloat(inv.outstanding_amount) || 0), 0)
)

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

onMounted(async () => {
  if (!props.room.check_in) return
  loadingDetail.value = true
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_checkin_detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({ name: props.room.check_in }),
    })
    const data = await res.json()
    if (data.message) checkinDetail.value = data.message
  } catch (e) {
    console.error('Failed to load check-in detail for modal', e)
  } finally {
    loadingDetail.value = false
  }
})

function ordinal(n) {
  const s = ['th','st','nd','rd']
  const v = n % 100
  return s[(v-20)%10] || s[v] || s[0]
}

function goToReservation() {
  emit('close')
  if (props.room.reservation) {
    router.push({ name: 'SavedReservation', params: { id: props.room.reservation } })
  } else {
    router.push({ path: '/reservations', query: { room: props.room.room_number } })
  }
}

function goCheckInFromReservation() {
  emit('close')
  const query = {
    room: props.room.room_number || props.room.name,
    room_type: props.room.room_type || '',
  }
  if (props.room.reservation) query.reservation = props.room.reservation
  if (props.room.reservation) query.canonical_reservation = props.room.reservation
  if (props.room.reservation_type) query.reservation_type = props.room.reservation_type
  if (props.room.current_guest || props.room.reserved_for) {
    query.guest_name = props.room.current_guest || props.room.reserved_for
  }
  if (props.room.guest_phone) query.guest_phone = props.room.guest_phone
  if (props.room.guest_email) query.guest_email = props.room.guest_email
  if (props.room.corporate_guest) query.guest = props.room.corporate_guest
  if (props.room.customer) query.customer = props.room.customer
  if (props.room.rate_per_night) query.rate_amount = props.room.rate_per_night
  if (props.room.number_of_nights) query.nights = props.room.number_of_nights
  if (props.room.reservation_arrival) query.check_in_dt = `${props.room.reservation_arrival} 14:00:00`
  if (props.room.reservation_departure) query.checkout_date = props.room.reservation_departure
  router.push({ path: '/check-ins/new', query })
}

function goNewCheckIn() {
  emit('close')
  router.push({
    path: '/check-ins/new',
    query: {
      room: props.room.room_number || props.room.name,
      room_type: props.room.room_type || '',
    },
  })
}

function goCheckout() {
  emit('close')
  router.push('/check-outs/' + (props.room.check_in || props.room.name))
}

function goCheckin() {
  emit('close')
  router.push('/check-ins/' + (props.room.check_in || props.room.name))
}
function goMakeReservation() {
  emit('close')
  router.push({ path: '/reservations/new', query: { type: 'Individual', room: props.room.room_number || props.room.name, room_type: props.room.room_type || '' } })
}

async function blockRoom() {
  if (blockBusy.value) return
  blockBusy.value = true
  blockError.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.front_desk.block_room', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({ room: props.room.room_number || props.room.name }),
    })
    const payload = await res.json().catch(() => ({}))
    if (!res.ok || payload?.exc) {
      throw new Error(payload?._server_messages || payload?.message || 'Failed to block room.')
    }
    emit('close')
  } catch (e) {
    blockError.value = String(e?.message || 'Failed to block room.')
  } finally {
    blockBusy.value = false
  }
}

function goMaintenance() { emit('close'); router.push('/maintenance/new-request') }
function goHousekeeping() { emit('close'); router.push({ path: '/housekeeping/task/new', query: { room: props.room.name } }) }
function goRoomDetails() { emit('close'); router.push('/rooms/' + props.room.room_number) }
</script>
