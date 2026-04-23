<template>
  <div class="space-y-4">

    <!-- Top bar info -->
    <div>
      <p class="text-xs text-gray-400">Quick billing workspace for restaurant, bar, mini-mart and in-house guest charges with direct room posting support.</p>
    </div>

    <!-- Terminal header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Current Terminal</h3>
        <p class="text-xs text-gray-400 mt-0.5">Main Restaurant POS • Cashier: Adaeze • Shift: Morning</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/pos/shift-close')"
          class="btn-hover px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
          Close POS
        </button>
        <button class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Hold Sale
        </button>
        <button @click="showDraftOrders = true"
          class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Draft Orders
        </button>
        <button @click="showOpenTables = true"
          class="btn-hover px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
          Open Tables
        </button>
        <button class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          New Sale
        </button>
      </div>
    </div>

    <!-- Main body -->
    <div style="display:grid;grid-template-columns:1fr 460px;gap:20px;align-items:start;">

      <!-- Left: Menu & Order Builder -->
      <div>
        <h2 class="text-base font-bold text-gray-900 mb-3">Menu & Order Builder</h2>

        <!-- Search -->
        <div class="relative mb-3">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input v-model="menuSearch" type="text" placeholder="Search item, SKU, category or room charge..."
            class="w-full pl-9 pr-4 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow" />
        </div>

        <!-- Category tabs -->
        <div class="flex items-center gap-2 flex-wrap mb-4">
          <button v-for="cat in categories" :key="cat"
            @click="activeCategory = cat"
            class="px-4 py-2 text-xs font-medium rounded-lg transition-all duration-200"
            :class="activeCategory === cat
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'">
            {{ cat }}
          </button>
        </div>

        <!-- Menu grid -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
          <div v-for="item in filteredMenuItems" :key="item.id"
            @click="addToCart(item)"
            class="menu-card bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer relative select-none"
            :class="item.stock === 0 ? 'opacity-60 cursor-not-allowed' : ''">
            <div class="absolute top-2 right-2 z-10 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
              :class="item.stock === 0 ? 'bg-red-500 text-white' : item.stock < 10 ? 'bg-orange-400 text-white' : 'bg-green-500 text-white'">
              {{ item.stock }}
            </div>
            <div class="h-24 bg-gray-100 overflow-hidden">
              <img v-if="item.image" :src="item.image" :alt="item.name"
                class="w-full h-full object-cover transition-transform duration-300 hover:scale-105" />
              <div v-else class="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                <span class="text-gray-300 text-2xl">🍽</span>
              </div>
            </div>
            <div class="px-3 py-2.5">
              <p class="text-xs font-semibold text-gray-900 leading-snug">{{ item.name }}</p>
              <p class="text-xs font-bold text-blue-600 mt-0.5">₦{{ item.price.toLocaleString() }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Current Sale -->
      <div class="bg-white rounded-xl border border-gray-200 p-5 sticky top-4">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Current Sale</h3>

        <!-- Bill To -->
        <div class="mb-4">
          <p class="text-xs font-medium text-gray-500 mb-2">Bill To</p>

          <div v-if="!selectedBillTo">
            <div class="flex gap-2 mb-2">
              <div class="flex-1 relative">
                <input v-model="billToSearch"
                  @focus="billToFocused = true"
                  @blur="delayBlur('billToFocused')"
                  type="text" placeholder="Search customer name, Table, phone..."
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow" />
                <div v-if="billToFocused || billToSearch"
                  class="dropdown-panel absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-20 overflow-hidden">
                  <div v-if="billToResults.length === 0" class="px-4 py-3 text-xs text-gray-400 text-center">No results</div>
                  <div v-for="r in billToResults" :key="r.id"
                    @mousedown="selectBillTo(r)"
                    class="px-4 py-3 text-xs hover:bg-blue-50 cursor-pointer border-b border-gray-50 last:border-0 flex items-center gap-3 transition-colors">
                    <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                      style="background:#dbeafe;color:#1d4ed8">{{ r.name[0] }}</div>
                    <div>
                      <p class="font-semibold text-gray-900">{{ r.name }}</p>
                      <p class="text-gray-400 mt-0.5">{{ r.room ? `Room ${r.room}` : r.type }}</p>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="settlementMethod === 'Post to Room'" class="relative w-32">
                <input v-model="roomNumber"
                  @focus="roomFocused = true"
                  @blur="delayBlur('roomFocused')"
                  type="text" placeholder="Room No."
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow" />
                <div v-if="roomFocused || roomNumber"
                  class="dropdown-panel absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-20 overflow-hidden">
                  <div v-for="r in filteredRoomSuggestions" :key="r.room"
                    @mousedown="selectRoomFromNumber(r)"
                    class="px-3 py-2.5 text-xs hover:bg-blue-50 cursor-pointer border-b border-gray-50 last:border-0 transition-colors">
                    <span class="font-bold text-gray-900">Room {{ r.room }}</span>
                    <span class="text-gray-400 ml-2">{{ r.guest }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex items-center gap-3 px-3 py-2.5 bg-blue-50 rounded-xl border border-blue-100 transition-all">
            <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm">
              {{ selectedBillTo.name[0] }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-semibold text-gray-900">{{ selectedBillTo.name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ selectedBillTo.room ? `Room ${selectedBillTo.room}` : selectedBillTo.type }}</p>
            </div>
            <button @click="clearBillTo"
              class="text-gray-300 hover:text-red-500 transition-colors w-5 h-5 flex items-center justify-center rounded-full hover:bg-red-50 text-xs">✕</button>
          </div>
        </div>

        <!-- Item Cart -->
        <div class="mb-4">
          <p class="text-xs font-semibold text-gray-700 mb-2">Item Cart</p>
          <div v-if="cart.length === 0"
            class="text-center py-10 text-xs text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">
            <span class="text-2xl block mb-2">🛒</span>
            Click any menu item to add it here
          </div>
          <table v-else class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="w-4 pb-2"></th>
                <th class="text-left text-xs font-medium text-gray-400 pb-2">Item</th>
                <th class="text-left text-xs font-medium text-gray-400 pb-2">Quantity</th>
                <th class="text-right text-xs font-medium text-gray-400 pb-2">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in cart" :key="item.id" class="cart-item border-b border-gray-50 last:border-0">
                <td class="py-2 pr-1"><input type="checkbox" class="w-3.5 h-3.5 accent-blue-600" /></td>
                <td class="py-2 pr-2"><span class="text-xs font-medium text-gray-900">{{ item.name }}</span></td>
                <td class="py-2">
                  <div class="flex items-center gap-1">
                    <button @click="decrementCart(item)" class="qty-btn w-5 h-5 flex items-center justify-center text-gray-400 border border-gray-200 rounded text-xs font-bold">−</button>
                    <span class="text-xs text-gray-700 w-5 text-center font-medium">{{ item.qty }}</span>
                    <button @click="incrementCart(item)" class="qty-btn w-5 h-5 flex items-center justify-center text-gray-400 border border-gray-200 rounded text-xs font-bold">+</button>
                    <span class="text-xs text-gray-400 ml-1">× ₦{{ item.price.toLocaleString() }}</span>
                  </div>
                </td>
                <td class="py-2 text-right text-xs font-bold text-gray-900">₦{{ (item.price * item.qty).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Discount -->
        <button class="w-full py-2 text-xs font-medium text-gray-400 border border-dashed border-gray-200 rounded-lg hover:bg-gray-50 hover:text-gray-600 hover:border-gray-300 transition-all mb-4">
          + Add Discount
        </button>

        <!-- Totals -->
        <div class="space-y-1.5 mb-4 border-t border-gray-100 pt-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Sub Total</span>
            <span class="text-xs font-medium text-gray-700">₦{{ subTotal.toLocaleString() }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Discount</span>
            <span class="text-xs font-medium text-gray-700">₦0.00</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Service Charge</span>
            <span class="text-xs font-medium text-gray-700">₦{{ serviceCharge.toLocaleString() }}</span>
          </div>
          <div class="flex items-center justify-between pt-2.5 mt-1 border-t border-gray-200">
            <span class="text-sm font-bold text-gray-900">Grand Total</span>
            <span class="text-sm font-bold text-blue-600">₦{{ grandTotal.toLocaleString() }}</span>
          </div>
        </div>

        <!-- Settlement -->
        <div class="mb-4">
          <p class="text-xs font-semibold text-blue-600 mb-2">Settlement</p>
          <div class="flex gap-1.5">
            <button v-for="method in settlementMethods" :key="method"
              @click="setSettlementMethod(method)"
              class="settlement-btn flex-1 py-2 text-xs font-medium rounded-lg border transition-all"
              :class="settlementMethod === method
                ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'">
              {{ method }}
            </button>
          </div>
        </div>

        <!-- Note -->
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Note / Kitchen Instruction</p>
          <textarea v-model="kitchenNote" rows="2"
            placeholder="No pepper on meal. Deliver to room within 20 mins..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <!-- Actions -->
        <div class="flex gap-2">
          <button class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Edit Selection</button>
          <button class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Print Bill</button>
          <button @click="onChargeNow" class="btn-hover flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            Charge Now
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <DraftOrdersModal v-model="showDraftOrders" />
    <OpenTablesModal v-model="showOpenTables" />
    <PostToRoomModal
      v-model="showPostToRoom"
      :grand-total="grandTotal"
      @room-selected="onRoomSelected"
      @confirmed="onPostConfirmed"
    />
    <SplitBillModal
      v-model="showSplitBill"
      :grand-total="grandTotal"
      :cart-items="cart"
      :service-charge="serviceCharge"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'
import OpenTablesModal from '@/components/pos/OpenTablesModal.vue'
import PostToRoomModal from '@/components/pos/PostToRoomModal.vue'
import SplitBillModal from '@/components/pos/SplitBillModal.vue'

const router = useRouter()

// ── Modals ─────────────────────────────────────────────────────────
const showDraftOrders = ref(false)
const showOpenTables = ref(false)
const showPostToRoom = ref(false)
const showSplitBill = ref(false)

// ── POS state ──────────────────────────────────────────────────────
const menuSearch = ref('')
const activeCategory = ref('All Items')
const settlementMethod = ref('Post to Room')
const settlementMethods = ['Post to Room', 'Cash', 'POS', 'Split']
const kitchenNote = ref('No pepper on meal. Deliver to room within 20 mins...')
const billToSearch = ref('')
const billToFocused = ref(false)
const roomNumber = ref('305')
const roomFocused = ref(false)
const selectedBillTo = ref({ id: 1, name: 'Sarah Johnson', room: '305', type: 'Direct Guest' })

const categories = ['All Items', 'Food', 'Drinks', 'Bar', 'Mini-Mart', 'Laundry']

const menuItems = [
  { id: 1, name: 'Grilled Chicken Meal', price: 18500, stock: 42, category: 'Food', image: 'https://images.unsplash.com/photo-1598103442097-8b74394b95c3?w=400&q=80' },
  { id: 2, name: 'Club Sandwich', price: 12000, stock: 28, category: 'Food', image: 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400&q=80' },
  { id: 3, name: 'Fresh Orange Juice', price: 6500, stock: 19, category: 'Drinks', image: 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400&q=80' },
  { id: 4, name: 'Heineken Beer', price: 5000, stock: 12, category: 'Bar', image: 'https://images.unsplash.com/photo-1608270586620-248524c67de9?w=400&q=80' },
  { id: 5, name: 'Sparkling Water', price: 3000, stock: 53, category: 'Drinks', image: 'https://images.unsplash.com/photo-1564419320461-6870880221ad?w=400&q=80' },
  { id: 6, name: 'Express Laundry Shirt', price: 4500, stock: 16, category: 'Laundry', image: null },
  { id: 7, name: 'Caesar Salad', price: 9500, stock: 24, category: 'Food', image: 'https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400&q=80' },
  { id: 8, name: 'Chocolate Cake', price: 7000, stock: 9, category: 'Food', image: 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&q=80' },
  { id: 9, name: 'Cappuccino', price: 5500, stock: 31, category: 'Drinks', image: 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400&q=80' },
  { id: 10, name: 'Bottled Water', price: 1500, stock: 66, category: 'Mini-Mart', image: 'https://images.unsplash.com/photo-1616118132534-381055b65ef0?w=400&q=80' },
  { id: 11, name: 'Red Wine Glass', price: 8500, stock: 14, category: 'Bar', image: 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=400&q=80' },
  { id: 12, name: 'Burger Combo', price: 14000, stock: 23, category: 'Food', image: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&q=80' },
  { id: 13, name: 'Egg & Toast', price: 4500, stock: 0, category: 'Food', image: null },
  { id: 14, name: 'Malt Drink', price: 1500, stock: 0, category: 'Drinks', image: null },
  { id: 15, name: 'Yoghurt Cup', price: 2500, stock: 0, category: 'Mini-Mart', image: null },
]

const filteredMenuItems = computed(() => {
  let items = menuItems
  if (activeCategory.value !== 'All Items') items = items.filter(i => i.category === activeCategory.value)
  if (menuSearch.value) {
    const q = menuSearch.value.toLowerCase()
    items = items.filter(i => i.name.toLowerCase().includes(q))
  }
  return items
})

// ── Cart ───────────────────────────────────────────────────────────
const cart = ref([
  { id: 1, name: 'Grilled Chicken Meal', price: 18500, qty: 1 },
  { id: 3, name: 'Fresh Orange Juice', price: 6500, qty: 2 },
  { id: 5, name: 'Sparkling Water', price: 3000, qty: 1 },
])

function addToCart(item) {
  if (item.stock === 0) return
  const existing = cart.value.find(c => c.id === item.id)
  if (existing) existing.qty++
  else cart.value.push({ ...item, qty: 1 })
}
function incrementCart(item) { item.qty++ }
function decrementCart(item) {
  if (item.qty > 1) item.qty--
  else cart.value = cart.value.filter(c => c.id !== item.id)
}

const subTotal = computed(() => cart.value.reduce((s, i) => s + i.price * i.qty, 0))
const serviceCharge = computed(() => Math.round(subTotal.value * 0.07))
const grandTotal = computed(() => subTotal.value + serviceCharge.value)

// ── Guests ─────────────────────────────────────────────────────────
const guests = [
  { id: 1, name: 'Sarah Johnson', room: '305', type: 'Direct Guest' },
  { id: 2, name: 'Uche Bassey', room: '402', type: 'Corporate' },
  { id: 3, name: 'Daniel Ayo', room: '118', type: 'Direct Guest' },
  { id: 4, name: 'Ngozi Cole', room: '511', type: 'Corporate' },
  { id: 5, name: 'Chinedu Okafor', room: '214', type: 'Direct Guest' },
  { id: 6, name: 'Fatima Ahmed', room: '401', type: 'Direct Guest' },
  { id: 7, name: 'Table 01', room: null, type: 'Table' },
  { id: 8, name: 'Table 02', room: null, type: 'Table' },
  { id: 9, name: 'Bar 04', room: null, type: 'Bar' },
]

const occupiedRooms = [
  { room: '305', type: 'Premium Queen', guest: 'Sarah Johnson', balance: 12500, paymentType: 'Direct Guest' },
  { room: '402', type: 'Executive Deluxe', guest: 'Uche Bassey', balance: 0, paymentType: 'Corporate' },
  { room: '118', type: 'Standard Room', guest: 'Daniel Ayo', balance: 8750, paymentType: 'Direct Guest' },
  { room: '511', type: 'Executive Suite', guest: 'Ngozi Cole', balance: 21200, paymentType: 'Corporate' },
  { room: '214', type: 'Deluxe King', guest: 'Chinedu Okafor', balance: 5000, paymentType: 'Direct Guest' },
  { room: '401', type: 'Premium Twin', guest: 'Fatima Ahmed', balance: 9800, paymentType: 'Direct Guest' },
]

const billToResults = computed(() => {
  const q = billToSearch.value.toLowerCase()
  if (!q) return guests.slice(0, 5)
  return guests.filter(g => g.name.toLowerCase().includes(q) || (g.room && g.room.includes(q)))
})

const filteredRoomSuggestions = computed(() => {
  if (!roomNumber.value) return occupiedRooms.slice(0, 5)
  return occupiedRooms.filter(r =>
    r.room.includes(roomNumber.value) ||
    r.guest.toLowerCase().includes(roomNumber.value.toLowerCase())
  )
})

function delayBlur(field) {
  setTimeout(() => {
    if (field === 'billToFocused') billToFocused.value = false
    if (field === 'roomFocused') roomFocused.value = false
  }, 200)
}

function selectBillTo(guest) {
  selectedBillTo.value = guest
  billToSearch.value = ''
  billToFocused.value = false
  if (settlementMethod.value === 'Post to Room' && guest.room) roomNumber.value = guest.room
}

function clearBillTo() {
  selectedBillTo.value = null
  billToSearch.value = ''
  roomNumber.value = ''
}

function selectRoomFromNumber(r) {
  roomNumber.value = r.room
  roomFocused.value = false
  selectedBillTo.value = { id: r.room, name: r.guest, room: r.room, type: r.paymentType }
}

// ── Settlement ─────────────────────────────────────────────────────
function setSettlementMethod(method) {
  settlementMethod.value = method
  if (method === 'Split') { showSplitBill.value = true; return }
  if (method === 'Post to Room') { showPostToRoom.value = true; return }
  roomNumber.value = ''
}

function onChargeNow() {
  if (settlementMethod.value === 'Post to Room') showPostToRoom.value = true
  else if (settlementMethod.value === 'Split') showSplitBill.value = true
}

function onRoomSelected(guest) {
  selectedBillTo.value = guest
  roomNumber.value = guest.room || ''
}

function onPostConfirmed() {
  // handle post confirmed
}

watch(settlementMethod, (val) => {
  if (val !== 'Post to Room') roomNumber.value = ''
  else if (selectedBillTo.value?.room) roomNumber.value = selectedBillTo.value.room
})
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
@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-6px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes cartItemIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(37,99,235,0.3); }
  70% { box-shadow: 0 0 0 6px rgba(37,99,235,0); }
  100% { box-shadow: 0 0 0 0 rgba(37,99,235,0); }
}
.modal-enter { animation: overlayIn 0.2s ease; }
.modal-panel { animation: modalIn 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.dropdown-panel { animation: dropdownIn 0.15s ease; }
.cart-item { animation: cartItemIn 0.2s ease; }
.btn-hover { transition: all 0.15s ease; }
.btn-hover:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-hover:active { transform: translateY(0); }
.menu-card { transition: all 0.18s ease; }
.menu-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
.menu-card:active { transform: scale(0.97); }
.settlement-btn { transition: all 0.2s cubic-bezier(0.34,1.2,0.64,1); }
.table-row { transition: background 0.15s ease; }
.qty-btn { transition: all 0.1s ease; }
.qty-btn:hover { background: #dbeafe; color: #2563eb; border-color: #93c5fd; }
</style>