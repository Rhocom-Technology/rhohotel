<template>
  <Teleport to="body">
    <div v-if="modelValue"
      class="modal-enter fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('update:modelValue', false)">
      <div class="modal-panel bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:1000px;max-height:92vh;">

        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Post to Room</h2>
              <p class="text-xs text-gray-400 mt-1">Select an occupied room and post this POS bill directly to the room folio.</p>
            </div>
            <button @click="$emit('update:modelValue', false)"
              class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm ml-4 flex-shrink-0">✕</button>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">
          <!-- Snapshot -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-6">
            <h4 class="text-xs font-bold text-gray-700 mb-4">POS Bill Snapshot</h4>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;">
              <div><p class="text-xs text-gray-400 mb-1.5">Bill No.</p><p class="text-sm font-bold text-gray-900">POS-2026-00184</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Service Point</p><p class="text-sm font-bold text-gray-900">Table 03</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Cashier</p><p class="text-sm font-bold text-gray-900">Adaeze</p></div>
              <div><p class="text-xs text-gray-400 mb-1.5">Bill Total</p><p class="text-sm font-bold text-blue-600">₦{{ grandTotal.toLocaleString() }}</p></div>
            </div>
          </div>

          <!-- Search -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-6">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Find Occupied Room</h4>
            <p class="text-xs text-gray-500 mb-2">Search guest / room</p>
            <div class="flex gap-3">
              <div class="flex-1 relative">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <input v-model="roomSearch" type="text" placeholder="Room no., guest name, folio..."
                  class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
              </div>
              <button @click="roomSearch='';roomPage=1" class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Reset</button>
              <button class="btn-hover px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Search Rooms</button>
            </div>
          </div>

          <!-- Rooms + preview -->
          <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-xs font-bold text-gray-900">Occupied Rooms Only</h4>
                <p class="text-xs text-gray-400">Showing {{ roomPageStart + 1 }}–{{ roomPageEnd }} of {{ filteredRooms.length }} rooms</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100">
                      <th class="text-left text-xs font-medium text-gray-500 px-6 py-4">Room</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Guest Name</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Balance</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-4 py-4">Payment Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="r in pagedRooms" :key="r.room"
                      @click="selectRoom(r)"
                      class="table-row cursor-pointer border-b border-gray-50 last:border-0"
                      :class="selectedPostRoom?.room === r.room ? 'bg-blue-50' : 'hover:bg-gray-50'">
                      <td class="px-6 py-4">
                        <p class="text-sm font-bold" :class="selectedPostRoom?.room === r.room ? 'text-blue-600' : 'text-gray-900'">{{ r.room }}</p>
                        <p class="text-xs text-gray-400 mt-0.5">{{ r.type }}</p>
                      </td>
                      <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ r.guest }}</td>
                      <td class="px-4 py-4 text-xs font-medium text-gray-700">₦{{ r.balance.toLocaleString() }}</td>
                      <td class="px-4 py-4 text-xs font-semibold" :class="r.paymentType === 'Direct Guest' ? 'text-blue-600' : 'text-gray-600'">{{ r.paymentType }}</td>
                    </tr>
                  </tbody>
                </table>
                <!-- Pagination -->
                <div v-if="roomTotalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-gray-50">
                  <p class="text-xs text-gray-400">Page {{ roomPage }} of {{ roomTotalPages }}</p>
                  <div class="flex items-center gap-1">
                    <button @click="roomPage--" :disabled="roomPage === 1"
                      class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">← Prev</button>
                    <button v-for="p in roomTotalPages" :key="p" @click="roomPage = p"
                      class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                      :class="roomPage === p ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-white border border-gray-200 bg-transparent'">{{ p }}</button>
                    <button @click="roomPage++" :disabled="roomPage === roomTotalPages"
                      class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">Next →</button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedPostRoom" class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-200 bg-white">
                <h4 class="text-xs font-bold text-gray-900">Posting Preview</h4>
              </div>
              <div class="p-6 space-y-3 text-xs">
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Selected Room</span><span class="font-bold text-gray-900">{{ selectedPostRoom.room }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Guest Name</span><span class="font-bold text-gray-900">{{ selectedPostRoom.guest }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Current Folio Balance</span><span class="font-bold text-gray-900">₦{{ selectedPostRoom.balance.toLocaleString() }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">POS Bill Amount</span><span class="font-bold text-gray-900">₦{{ grandTotal.toLocaleString() }}</span></div>
                <div class="flex justify-between py-1.5">
                  <span class="text-gray-400">Projected New Balance</span>
                  <span class="font-bold text-blue-600">₦{{ (selectedPostRoom.balance + grandTotal).toLocaleString() }}</span>
                </div>
              </div>
              <div class="mx-6 mb-5 bg-white rounded-xl border border-gray-200 p-4">
                <p class="text-xs font-bold text-gray-900 mb-2">Posting Note</p>
                <p class="text-xs text-gray-500 leading-relaxed">Restaurant dining bill from Table 03 will be posted to Room {{ selectedPostRoom.room }} folio.</p>
                <p class="text-xs text-gray-400 mt-2">Cashier: Adaeze • Time: 10:46 AM</p>
              </div>
              <div class="px-6 pb-6">
                <p class="text-xs text-gray-500 mb-1.5">Narration / Remark</p>
                <textarea rows="3" placeholder="Optional posting remark for folio audit trail..."
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none bg-white focus:ring-2 focus:ring-blue-500"></textarea>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-3 px-8 py-5 border-t border-gray-100 bg-gray-50">
          <button @click="$emit('update:modelValue', false)" class="btn-hover px-6 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100">Cancel</button>
          <button @click="confirm" :disabled="!selectedPostRoom"
            class="btn-hover px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">Post</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  grandTotal: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue', 'confirmed', 'room-selected'])

const roomSearch = ref('')
const roomPage = ref(1)
const perPage = 10

const occupiedRooms = [
  { room: '305', type: 'Premium Queen', guest: 'Sarah Johnson', balance: 12500, paymentType: 'Direct Guest' },
  { room: '402', type: 'Executive Deluxe', guest: 'Uche Bassey', balance: 0, paymentType: 'Corporate' },
  { room: '118', type: 'Standard Room', guest: 'Daniel Ayo', balance: 8750, paymentType: 'Direct Guest' },
  { room: '511', type: 'Executive Suite', guest: 'Ngozi Cole', balance: 21200, paymentType: 'Corporate' },
  { room: '214', type: 'Deluxe King', guest: 'Chinedu Okafor', balance: 5000, paymentType: 'Direct Guest' },
  { room: '401', type: 'Premium Twin', guest: 'Fatima Ahmed', balance: 9800, paymentType: 'Direct Guest' },
  { room: '102', type: 'Standard Room', guest: 'Tunde Balogun', balance: 3200, paymentType: 'Direct Guest' },
  { room: '207', type: 'Deluxe Queen', guest: 'Amina Suleiman', balance: 15600, paymentType: 'Corporate' },
  { room: '310', type: 'Executive King', guest: 'David Mensah', balance: 7400, paymentType: 'Direct Guest' },
  { room: '415', type: 'Suite', guest: 'Chidinma Eze', balance: 42000, paymentType: 'Corporate' },
  { room: '501', type: 'Penthouse', guest: 'Oluwaseun Adebayo', balance: 88000, paymentType: 'Corporate' },
  { room: '309', type: 'Standard Twin', guest: 'Halima Usman', balance: 4100, paymentType: 'Direct Guest' },
]

const selectedPostRoom = ref(null)

const filteredRooms = computed(() => {
  if (!roomSearch.value) return occupiedRooms
  const q = roomSearch.value.toLowerCase()
  return occupiedRooms.filter(r =>
    r.room.includes(q) ||
    r.guest.toLowerCase().includes(q) ||
    r.type.toLowerCase().includes(q)
  )
})

const roomTotalPages = computed(() => Math.max(1, Math.ceil(filteredRooms.value.length / perPage)))
const roomPageStart = computed(() => (roomPage.value - 1) * perPage)
const roomPageEnd = computed(() => Math.min(roomPageStart.value + perPage, filteredRooms.value.length))
const pagedRooms = computed(() => filteredRooms.value.slice(roomPageStart.value, roomPageEnd.value))

function selectRoom(r) {
  selectedPostRoom.value = r
  emit('room-selected', { id: r.room, name: r.guest, room: r.room, type: r.paymentType })
}

function confirm() {
  emit('confirmed', selectedPostRoom.value)
  emit('update:modelValue', false)
}

watch(filteredRooms, () => { roomPage.value = 1 })
</script>

<style>
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.modal-enter { animation: overlayIn 0.2s ease; }
.modal-panel { animation: modalIn 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.btn-hover { transition: all 0.15s ease; }
.btn-hover:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-hover:active { transform: translateY(0); }
.table-row { transition: background 0.15s ease; }
</style>