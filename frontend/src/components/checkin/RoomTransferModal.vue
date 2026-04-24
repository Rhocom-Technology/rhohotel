<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:780px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Room Transfer</h2>
            <p class="text-xs text-gray-400 mt-1">Move guest from current room to a new room while preserving stay continuity, billing integrity, and housekeeping flow</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-6">

          <!-- Current Guest Stay -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">Current Guest Stay</p>
            <p class="text-xs text-blue-600 mb-3">OGUMBA WAYNE • Checked In • Room 8408 • Executive Room • Check-out 24 Feb 2026 • Balance ₦41,000</p>
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Current</span>
              <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Balance Open</span>
            </div>
          </div>

          <!-- Two column layout -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

            <!-- Transfer Setup -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Transfer Setup</h3>
              <div class="space-y-4">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Transfer Date and Time</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">22 Feb 2026 • 14:30</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Posting Date and Time</p>
                    <input type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reason for Transfer</p>
                  <input type="text" v-model="transferReason"
                    placeholder="Guest request / maintenance / upgrade / service recovery"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Transfer Notes</p>
                  <textarea v-model="transferNotes" rows="3"
                    placeholder="Add explanation, guest approval note, bell desk coordination, or housekeeping instruction"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Billing Handling</p>
                  <input type="text" placeholder="Keep existing folios linked to same stay"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-gray-50" readonly />
                </div>
                <label class="flex items-center justify-between cursor-pointer">
                  <span class="text-xs text-gray-600">Notify housekeeping to inspect vacated room after transfer</span>
                  <div class="relative">
                    <input type="checkbox" v-model="notifyHK" class="sr-only" />
                    <div class="w-10 h-5 rounded-full transition-colors" :class="notifyHK ? 'bg-blue-600' : 'bg-gray-200'">
                      <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform" :class="notifyHK ? 'translate-x-5' : ''"></div>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Select New Room -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Select New Room</h3>
              <div class="mb-4">
                <p class="text-xs text-gray-500 mb-1.5">Search Available Room</p>
                <input type="text" v-model="roomSearch" placeholder="Search by room number, type, floor, or status"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div class="space-y-3">
                <div v-for="r in availableRooms" :key="r.number"
                  class="rounded-xl border px-4 py-3 flex items-center justify-between"
                  :class="selectedRoom === r.number ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200'">
                  <div>
                    <p class="text-sm font-bold text-gray-900">Room {{ r.number }}</p>
                    <p class="text-xs text-gray-500 mt-0.5">{{ r.desc }}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 text-xs font-medium rounded-full"
                      :class="r.tagClass">{{ r.tag }}</span>
                    <button v-if="r.tag !== 'Cleaning'"
                      class="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                      @click="selectedRoom = r.number">Select</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Transfer Impact Summary -->
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Transfer Impact Summary</h3>
            <div class="bg-gray-50 rounded-lg px-4 py-3">
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;" class="mb-2">
                <div class="text-xs text-gray-700"><span class="text-gray-400">From Room: </span>8408</div>
                <div class="text-xs text-gray-700"><span class="text-gray-400">To Room: </span>{{ selectedRoom || '—' }}</div>
                <div class="text-xs text-gray-700"><span class="text-gray-400">Rate Impact: </span>No change</div>
                <div class="text-xs text-gray-700"><span class="text-gray-400">Housekeeping: </span>Notify after move</div>
              </div>
              <p class="text-xs text-gray-500">Stay continuity preserved • Existing bills remain attached • Checkout page remains linked after transfer</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">Confirm Room Transfer</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
defineEmits(['close'])

const transferReason = ref('')
const transferNotes = ref('')
const notifyHK = ref(true)
const roomSearch = ref('')
const selectedRoom = ref('8505')

const availableRooms = [
  { number: '8505', desc: 'Deluxe Room • 2nd Floor • Vacant and clean',              tag: 'Suggested', tagClass: 'bg-blue-100 text-blue-600' },
  { number: '8510', desc: 'Executive Room • 2nd Floor • Vacant but dirty',           tag: 'Cleaning',  tagClass: 'bg-yellow-100 text-yellow-600' },
  { number: '8602', desc: 'Suite • 3rd Floor • Vacant and clean • Upgrade available',tag: 'Upgrade',   tagClass: 'bg-purple-100 text-purple-600' },
]
</script>