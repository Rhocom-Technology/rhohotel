<template>
  <Teleport to="body">
    <div v-if="modelValue"
      class="modal-enter fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('update:modelValue', false)">
      <div class="modal-panel bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:960px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Split Bill</h2>
              <p class="text-xs text-gray-400 mt-1">Split this bill across multiple payment methods or rooms.</p>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button @click="$emit('update:modelValue', false)" class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button @click="applySplit" :disabled="applying || portionTotal !== grandTotal"
                class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                {{ applying ? 'Processing…' : 'Apply Split' }}
              </button>
            </div>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">

          <!-- Bill Snapshot -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <h4 class="text-xs font-bold text-gray-700 mb-3">Bill Snapshot</h4>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
              <div><p class="text-xs text-gray-400 mb-1">Cashier</p><p class="text-sm font-bold text-gray-900">{{ cashier || '—' }}</p></div>
              <div><p class="text-xs text-gray-400 mb-1">Items</p><p class="text-sm font-bold text-gray-900">{{ cartItems.length }}</p></div>
              <div><p class="text-xs text-gray-400 mb-1">Sub Total</p><p class="text-sm font-bold text-gray-900">₦{{ subTotal.toLocaleString() }}</p></div>
              <div><p class="text-xs text-gray-400 mb-1">Grand Total</p><p class="text-sm font-bold text-blue-600">₦{{ grandTotal.toLocaleString() }}</p></div>
            </div>
          </div>

          <!-- Bill Items -->
          <div>
            <h4 class="text-sm font-bold text-gray-900 mb-3">Bill Items</h4>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Item</th>
                    <th class="text-center text-xs font-medium text-gray-500 px-4 py-3">Qty</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in cartItems" :key="item.id || item.item_code" class="border-b border-gray-50 last:border-0">
                    <td class="px-5 py-3 text-xs font-medium text-gray-900">{{ item.name }}</td>
                    <td class="px-4 py-3 text-center text-xs text-gray-600">{{ item.qty }}</td>
                    <td class="px-5 py-3 text-right text-xs font-bold text-gray-900">₦{{ (item.price * item.qty).toLocaleString() }}</td>
                  </tr>
                  <tr v-if="discountAmount > 0" class="border-t border-gray-100">
                    <td class="px-5 py-2 text-xs text-green-600" colspan="2">Discount</td>
                    <td class="px-5 py-2 text-right text-xs font-bold text-green-600">−₦{{ discountAmount.toLocaleString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Split Configuration -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-bold text-gray-900">Payment Portions</h4>
              <div class="flex items-center gap-2">
                <button @click="equalSplit" class="btn-hover px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Equal Split</button>
                <button v-if="portions.length < 4" @click="addPortion" class="btn-hover px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">+ Add Portion</button>
              </div>
            </div>

            <div class="space-y-4">
              <div v-for="(portion, idx) in portions" :key="idx" class="bg-gray-50 rounded-xl border border-gray-200 p-5">
                <div class="flex items-center justify-between mb-4">
                  <h5 class="text-sm font-bold text-gray-900">Portion {{ String.fromCharCode(65 + idx) }}</h5>
                  <button v-if="portions.length > 2" @click="removePortion(idx)"
                    class="text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50">Remove</button>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Amount (₦)</p>
                    <input v-model.number="portion.amount" type="number" min="0"
                      class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Payment Type</p>
                    <select v-model="portion.paymentType"
                      class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                      <option value="Cash">Cash</option>
                      <option value="POS">POS</option>
                      <option value="Post to Room">Post to Room</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">{{ portion.paymentType === 'Post to Room' ? 'Room / Guest' : 'Customer (optional)' }}</p>
                    <div v-if="portion.paymentType === 'Post to Room'" class="relative">
                      <input v-model="portion.roomSearch"
                        @focus="loadRooms"
                        type="text"
                        :placeholder="portion.selectedRoom ? `Room ${portion.selectedRoom.room}` : 'Type room no. or guest…'"
                        class="w-full px-3 py-2 text-xs border rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500"
                        :class="portion.selectedRoom ? 'border-blue-300 bg-blue-50' : 'border-gray-200'" />
                      <div v-if="portionRoomResults[idx]?.length > 0"
                        class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-30 overflow-hidden">
                        <div v-for="r in portionRoomResults[idx]" :key="r.check_in"
                          @mousedown.prevent="selectRoomForPortion(idx, r)"
                          class="px-3 py-2.5 text-xs hover:bg-blue-50 cursor-pointer border-b border-gray-50 last:border-0">
                          <span class="font-bold text-gray-900">Room {{ r.room }}</span>
                          <span class="text-gray-400 ml-2">{{ r.guest }}</span>
                        </div>
                      </div>
                    </div>
                    <input v-else v-model="portion.target" type="text" placeholder="Walk In"
                      class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white" />
                  </div>
                </div>
                <div v-if="portion.selectedRoom" class="mt-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700 flex items-center justify-between">
                  <span>Posting to Room {{ portion.selectedRoom.room }} — {{ portion.selectedRoom.guest }}</span>
                  <button @click="clearRoomForPortion(idx)" class="text-blue-400 hover:text-blue-700 ml-2">✕</button>
                </div>
              </div>
            </div>

            <!-- Total validation -->
            <div class="mt-4 flex items-center gap-3 py-3 px-5 rounded-xl border"
              :class="portionTotal === grandTotal ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'">
              <svg v-if="portionTotal === grandTotal" class="w-4 h-4 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
              <svg v-else class="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <p class="text-xs" :class="portionTotal === grandTotal ? 'text-green-700' : 'text-amber-700'">
                <span v-if="portionTotal === grandTotal">Split total: ₦{{ grandTotal.toLocaleString() }} — All amounts allocated correctly.</span>
                <span v-else>Portions total ₦{{ portionTotal.toLocaleString() }} of ₦{{ grandTotal.toLocaleString() }}
                  ({{ portionTotal < grandTotal ? 'short ₦' + (grandTotal - portionTotal).toLocaleString() : 'over ₦' + (portionTotal - grandTotal).toLocaleString() }})
                </span>
              </p>
            </div>
          </div>

          <div v-if="splitError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-xs text-red-600">{{ splitError }}</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  modelValue: Boolean,
  grandTotal: { type: Number, default: 0 },
  cartItems: { type: Array, default: () => [] },
  serviceCharge: { type: Number, default: 0 },
  discountAmount: { type: Number, default: 0 },
  kitchenNote: { type: String, default: '' },
  cashier: { type: String, default: '' },
  posProfile: { type: String, default: '' },
  preSelectedRoom: { type: Object, default: null },
  existingDraft: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const applying = ref(false)
const splitError = ref('')

const subTotal = computed(() => props.cartItems.reduce((s, i) => s + i.price * i.qty, 0))

// ── Portions ───────────────────────────────────────────────────────────────
const makePortion = () => ({
  amount: 0,
  paymentType: 'Cash',
  target: '',
  roomSearch: '',
  selectedRoom: null,
  checkIn: null,
})

const portions = ref([makePortion(), makePortion()])
const portionTotal = computed(() => portions.value.reduce((s, p) => s + (Number(p.amount) || 0), 0))

function equalSplit() {
  const n = portions.value.length
  const per = Math.floor(props.grandTotal / n)
  const remainder = props.grandTotal - per * (n - 1)
  portions.value.forEach((p, i) => { p.amount = i === n - 1 ? remainder : per })
}

function addPortion() {
  portions.value.push(makePortion())
  equalSplit()
}

function removePortion(idx) {
  portions.value.splice(idx, 1)
  equalSplit()
}

// Reset when modal opens
watch(() => props.modelValue, (open) => {
  if (open) {
    splitError.value = ''
    const r = props.preSelectedRoom
    if (r?.room && (r?.check_in || r?.id)) {
      // Pre-populate first portion with the already-selected room/guest
      portions.value = [
        {
          amount: props.grandTotal,
          paymentType: 'Post to Room',
          target: '',
          roomSearch: `Room ${r.room} — ${r.guest || r.name || ''}`,
          selectedRoom: { room: r.room, guest: r.guest || r.name || '', check_in: r.check_in || r.id },
          checkIn: r.check_in || r.id,
        },
        makePortion(),
      ]
      // Second portion starts at 0; user adjusts if they want a real split
    } else {
      portions.value = [makePortion(), makePortion()]
      equalSplit()
    }
  }
})

// ── Rooms resource ─────────────────────────────────────────────────────────
const roomsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_occupied_rooms_for_pos',
  auto: false,
})

function loadRooms() {
  if (!roomsResource.data && !roomsResource.loading) roomsResource.reload()
}

// Derived room suggestions per portion — computed to avoid mutating portions (which causes infinite deep-watch loop)
const portionRoomResults = computed(() => {
  const allRooms = roomsResource.data || []
  return portions.value.map(p => {
    if (!p.roomSearch || p.selectedRoom) return []
    const q = p.roomSearch.toLowerCase()
    return allRooms.filter(r =>
      (r.room || '').toLowerCase().includes(q) || (r.guest || '').toLowerCase().includes(q)
    ).slice(0, 6)
  })
})

function selectRoomForPortion(idx, room) {
  const p = portions.value[idx]
  p.selectedRoom = room
  p.checkIn = room.check_in
  p.roomSearch = `Room ${room.room} — ${room.guest}`
}

function clearRoomForPortion(idx) {
  const p = portions.value[idx]
  p.selectedRoom = null
  p.checkIn = null
  p.roomSearch = ''
}

// ── Apply split ────────────────────────────────────────────────────────────
function callFrappeApi(url, params) {
  return new Promise((resolve, reject) => {
    const r = createResource({
      url,
      onSuccess: resolve,
      onError: (err) => reject(new Error(err?.message || 'Request failed')),
    })
    r.submit(params)
  })
}

async function applySplit() {
  if (props.cartItems.length === 0) { splitError.value = 'Cart is empty.'; return }
  if (portionTotal.value !== props.grandTotal) {
    splitError.value = `Portions must total ₦${props.grandTotal.toLocaleString()}.`; return
  }
  for (const p of portions.value) {
    if (p.paymentType === 'Post to Room' && !p.checkIn) {
      splitError.value = 'Select a room for all "Post to Room" portions.'; return
    }
  }

  applying.value = true
  splitError.value = ''

  // The draft should be deleted once (on the first API call that completes)
  let draftToDelete = props.existingDraft || null

  try {
    for (const portion of portions.value) {
      if (Number(portion.amount) <= 0) continue
      const ratio = Number(portion.amount) / props.grandTotal
      const portionItems = JSON.stringify(props.cartItems.map(i => ({
        item_code: i.item_code || i.id,
        qty: i.qty,
        price: Math.round(i.price * ratio * 100) / 100,
      })))

      if (portion.paymentType === 'Post to Room') {
        await callFrappeApi('rhohotel.rhocom_hotel.api.pos.post_bill_to_room', {
          items: portionItems,
          check_in: portion.checkIn,
          service_charge: 0,
          discount_amount: 0,
          kitchen_note: props.kitchenNote || null,
          pos_profile: props.posProfile || null,
          existing_draft: draftToDelete,
        })
      } else {
        await callFrappeApi('rhohotel.rhocom_hotel.api.pos.create_pos_invoice', {
          items: portionItems,
          mode_of_payment: portion.paymentType === 'POS' ? 'POS' : 'Cash',
          customer: portion.target || null,
          service_charge: 0,
          discount_amount: 0,
          kitchen_note: props.kitchenNote || null,
          pos_profile: props.posProfile || null,
          existing_draft: draftToDelete,
        })
      }
      draftToDelete = null  // only delete once — first successful call handles it
    }
    emit('confirmed', { split: true })
    emit('update:modelValue', false)
  } catch (err) {
    splitError.value = err.message || 'Failed to process split bill'
  } finally {
    applying.value = false
  }
}
</script>

<style scoped>
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
</style>
