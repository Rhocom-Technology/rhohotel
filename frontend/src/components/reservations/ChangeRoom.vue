<template>
  <div class="p-6">
    <div class="flex items-start justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Change Room</h2>
        <p class="text-xs text-gray-400 mt-1">Move this reservation to another room — validates availability and recalculates pricing.</p>
      </div>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
    </div>

    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">
      <p class="text-xs text-red-600">{{ error }}</p>
    </div>

    <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-5">
      <h3 class="text-xs font-bold text-gray-900 mb-3">Reservation Snapshot</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
        <div><p class="text-xs text-gray-400 mb-1">Reservation</p><p class="text-sm font-bold text-gray-900">{{ reservation.name }}</p></div>
        <div><p class="text-xs text-gray-400 mb-1">Guest</p><p class="text-sm font-bold text-gray-900">{{ reservation.primary_guest_name || '—' }}</p></div>
        <div><p class="text-xs text-gray-400 mb-1">Stay Period</p><p class="text-sm font-bold text-gray-900">{{ fmtDate(reservation.from_date) }} → {{ fmtDate(reservation.to_date) }}</p></div>
        <div><p class="text-xs text-gray-400 mb-1">Nights</p><p class="text-sm font-bold text-gray-900">{{ reservation.number_of_nights }}</p></div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
      <!-- Current rooms: pick which to change -->
      <div>
        <h3 class="text-sm font-bold text-gray-900 mb-3">Select Room to Change</h3>
        <div v-if="!rooms.length" class="text-xs text-gray-400 py-4 text-center border border-gray-100 rounded-lg">No rooms in reservation</div>
        <div v-else-if="!changeableRooms.length" class="text-xs text-gray-400 py-4 text-center border border-gray-100 rounded-lg">All rooms are currently checked in and cannot be changed.</div>
        <div v-else class="space-y-2">
          <div v-for="r in changeableRooms" :key="r.room_number"
            class="rounded-xl border px-4 py-3 flex items-center justify-between cursor-pointer transition-colors"
            :class="selectedOldRoom === r.room_number ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200 hover:border-gray-300'"
            @click="selectedOldRoom = r.room_number">
            <div>
              <p class="text-sm font-bold text-gray-900">{{ r.room_number }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ r.room_type }} • {{ r.guest_name || '—' }}</p>
              <p class="text-xs text-blue-600 mt-0.5">{{ fmt(r.rate_per_night) }} / night</p>
            </div>
            <span v-if="selectedOldRoom === r.room_number"
              class="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded-full flex-shrink-0">Selected</span>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Reason for Change</p>
          <select v-model="reason"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select reason</option>
            <option v-for="item in reasonOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </div>
      </div>

      <!-- Available rooms to move to -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-gray-900">Available Rooms</h3>
          <button @click="loadRooms" class="text-xs text-blue-500 hover:text-blue-700 transition-colors">Refresh</button>
        </div>
        <div v-if="loadingRooms" class="py-8 text-center">
          <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p class="text-xs text-gray-400">Loading rooms…</p>
        </div>
        <div v-else-if="!availableRooms.length" class="py-8 text-center border border-gray-100 rounded-lg">
          <p class="text-xs text-gray-400">No available rooms for this period.</p>
        </div>
        <div v-else class="space-y-2 max-h-72 overflow-y-auto">
          <div v-for="r in availableRooms" :key="r.name"
            class="rounded-xl border px-4 py-3 flex items-center justify-between transition-colors"
            :class="selectedNewRoom === r.name ? 'bg-green-50 border-green-300' : 'bg-white border-gray-200'">
            <div>
              <p class="text-sm font-bold text-gray-900">{{ r.name }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ r.room_type }} • {{ r.floor || '' }}</p>
              <p class="text-xs text-blue-600 mt-0.5">{{ fmt(r.rate_per_night) }} / night</p>
            </div>
            <button
              class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors flex-shrink-0"
              :class="selectedNewRoom === r.name ? 'text-green-700 bg-green-100 border border-green-200' : 'text-white bg-blue-600 hover:bg-blue-700'"
              @click="selectedNewRoom = r.name">{{ selectedNewRoom === r.name ? '✓ Selected' : 'Select' }}</button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
      <button @click="$emit('close')" class="px-6 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
      <button :disabled="submitting || !selectedOldRoom || !selectedNewRoom" @click="applyChange"
        class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
        {{ submitting ? 'Applying…' : 'Apply Room Change' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const props = defineProps({
  reservation: { type: Object, required: true },
  preselectedRoom: { type: String, default: '' },
})
const emit = defineEmits(['close', 'done'])

const rooms = computed(() => props.reservation?.rooms || [])
const changeableRooms = computed(() => rooms.value.filter(r => !r.check_in_reference && String(r.status || '').toLowerCase() !== 'checked in'))
const availableRooms = ref([])
const selectedOldRoom = ref('')
const selectedNewRoom = ref('')
const reason = ref('')
const loadingRooms = ref(true)
const submitting = ref(false)
const error = ref('')
const reasonOptions = [
  'Guest Request',
  'Maintenance Issue',
  'Room Upgrade',
  'Room Downgrade',
  'Operational Reassignment',
]

function fmt(v) { return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00' }
function fmtDate(dt) { if (!dt) return '—'; return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }

async function loadRooms() {
  if (!props.reservation.from_date || !props.reservation.to_date) return
  loadingRooms.value = true; error.value = ''
  const reservedRooms = rooms.value.map(r => r.room_number)
  try {
    const rows = await callMethodForm('rhohotel.rhocom_hotel.utils.room_availability.get_available_rooms', {
      check_in_dt: props.reservation.from_date + ' 12:00:00',
      check_out_dt: props.reservation.to_date + ' 12:00:00',
    })
    availableRooms.value = (rows || []).filter(r => !reservedRooms.includes(r.name))
  } catch (err) {
    error.value = String(err?.message || 'Failed to load available rooms.')
  } finally { loadingRooms.value = false }
}

onMounted(loadRooms)

watch(
  changeableRooms,
  (list) => {
    if (props.preselectedRoom) {
      selectedOldRoom.value = props.preselectedRoom
    } else if (Array.isArray(list) && list.length === 1) {
      selectedOldRoom.value = list[0].room_number || ''
    }
  },
  { immediate: true },
)

async function applyChange() {
  if (!selectedOldRoom.value || !selectedNewRoom.value) return
  submitting.value = true; error.value = ''
  try {
    await callMethodForm('rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.change_room_in_reservation', {
      reservation_name: props.reservation.name,
      old_room_number: selectedOldRoom.value,
      new_room_number: selectedNewRoom.value,
      reason: reason.value,
    })
    emit('done'); emit('close')
  } catch (err) {
    error.value = String(err?.message || 'Could not change room.')
  } finally { submitting.value = false }
}
</script>
