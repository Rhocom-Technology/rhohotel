<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:780px;max-height:92vh;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Room Transfer</h2>
            <p class="text-xs text-gray-400 mt-1">Move guest to a different room while preserving billing and stay continuity</p>
          </div>
          <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">
          <div v-if="invoiceInfo" class="bg-green-50 border border-green-200 rounded-xl px-5 py-4">
            <p class="text-xs font-bold text-green-700 mb-1">Rate Adjustment Invoice Created</p>
            <p class="text-xs text-green-600">{{ invoiceInfo }}</p>
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
            <p class="text-xs font-bold text-red-600 mb-1">Transfer Failed</p>
            <p class="text-xs text-red-500">{{ error }}</p>
          </div>

          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">Current Stay</p>
            <p class="text-xs text-blue-600">{{ checkIn.guest }} • Room {{ checkIn.room_number }} • {{ checkIn.room_type }}</p>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Transfer Notes</h3>
              <div class="space-y-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reason for Transfer</p>
                  <select v-model="note" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-600">
                    <option value="">Select reason</option>
                    <option>Guest Request</option>
                    <option>Room Upgrade</option>
                    <option>Room Downgrade</option>
                    <option>Maintenance Issue</option>
                    <option>Noise Complaint</option>
                    <option>Housekeeping Issue</option>
                    <option>Management Decision</option>
                    <option>Operational Requirement</option>
                    <option>Other</option>
                  </select>
                </div>
                <div v-if="selectedRoom" class="bg-green-50 rounded-lg border border-green-200 px-4 py-3">
                  <p class="text-xs font-bold text-green-700">Selected: Room {{ selectedRoom.name }}</p>
                  <p class="text-xs text-green-600 mt-0.5">{{ selectedRoom.room_type }} • {{ fmt(selectedRoom.default_rate) }} / night</p>
                </div>
                <div v-else class="bg-gray-50 rounded-lg border border-gray-200 px-4 py-3">
                  <p class="text-xs text-gray-400">Select a room from the list →</p>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-bold text-gray-900">Available Rooms</h3>
                <button @click="loadRooms" class="text-xs text-blue-500 hover:text-blue-700">Refresh</button>
              </div>
              <div v-if="loadingRooms" class="py-6 text-center">
                <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p class="text-xs text-gray-400">Loading…</p>
              </div>
              <div v-else-if="availableRooms.length === 0" class="py-6 text-center">
                <p class="text-xs text-gray-400">No vacant rooms available.</p>
              </div>
              <div v-else class="space-y-2 max-h-64 overflow-y-auto">
                <div v-for="r in availableRooms" :key="r.name"
                  class="rounded-xl border px-4 py-3 flex items-center justify-between"
                  :class="selectedRoom?.name === r.name ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200'">
                  <div>
                    <p class="text-sm font-bold text-gray-900">{{ r.name }}</p>
                    <p class="text-xs text-gray-500 mt-0.5">{{ r.room_type }} • {{ r.floor || '' }}</p>
                    <p class="text-xs text-blue-600 mt-0.5">{{ fmt(r.default_rate) }} / night</p>
                  </div>
                  <button
                    class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors"
                    :class="selectedRoom?.name === r.name ? 'text-blue-700 bg-blue-100 border border-blue-200' : 'text-white bg-blue-600 hover:bg-blue-700'"
                    @click="selectedRoom = r">{{ selectedRoom?.name === r.name ? '✓ Selected' : 'Select' }}</button>
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50" @click="$emit('close')">Cancel</button>
            <button :disabled="submitting || !selectedRoom" @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Transferring…' : 'Confirm Room Transfer' }}
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
const availableRooms = ref([])
const selectedRoom = ref(null)
const note = ref('')
const loadingRooms = ref(true)
const submitting = ref(false)
const error = ref('')
const invoiceInfo = ref('')
function fmt(v) { return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00' }
async function apiPost(m, p) {
  const r = await fetch(`/api/method/${m}`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' }, body: new URLSearchParams(p) })
  return r.json()
}
function parseErr(data) {
  try { return JSON.parse(JSON.parse(data._server_messages || '[]')[0]).message } catch { return 'Request failed.' }
}
async function loadRooms() {
  loadingRooms.value = true
  error.value = ''
  try {
    const data = await apiPost('rhohotel.rhocom_hotel.api.checkin.get_rooms_for_transfer', {
      current_room: props.checkIn.room_number || '',
      check_in_dt: props.checkIn.check_in_datetime || '',
      check_out_dt: props.checkIn.expected_check_out_datetime || '',
    })
    if (data.exc) { error.value = parseErr(data); return }
    availableRooms.value = data.message || []
  } catch { error.value = 'Failed to load rooms.' } finally { loadingRooms.value = false }
}
onMounted(loadRooms)
async function submit() {
  if (!selectedRoom.value) return
  submitting.value = true; error.value = ''
  try {
    const data = await apiPost('rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.transfer_room', {
      check_in_name: props.checkIn.name, new_room_number: selectedRoom.value.name, note: note.value
    })
    if (data.exc) { error.value = parseErr(data); return }
    const result = data.message || {}
    if (result.rate_invoice) {
      invoiceInfo.value = `Invoice ${result.rate_invoice} created for the rate difference.`
      // Give user a moment to see it, then close
      setTimeout(() => { emit('done', result); emit('close') }, 2500)
    } else {
      emit('done', result); emit('close')
    }
  } catch { error.value = 'Network error.' } finally { submitting.value = false }
}
</script>
