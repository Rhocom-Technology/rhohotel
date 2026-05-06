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
        <p class="text-xs text-gray-400 mt-0.5">
          {{ terminalInfo.pos_profile || 'POS Terminal' }}<template v-if="terminalInfo.cashier"> • Cashier: {{ terminalInfo.cashier }}</template><template v-if="terminalInfo.shift_date"> • {{ terminalInfo.shift_date }}</template><template v-if="terminalInfo.pos_opening_entry"> • Entry: {{ terminalInfo.pos_opening_entry }}</template>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/pos/shift-close')"
          class="btn-hover px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
          Close POS
        </button>
        <button @click="toggleFullscreen"
          class="btn-hover px-4 py-2 text-xs font-medium border rounded-lg"
          :class="isFullscreen
            ? 'text-gray-700 border-gray-300 hover:bg-gray-50'
            : 'text-blue-700 border-blue-300 hover:bg-blue-50'">
          {{ isFullscreen ? 'Exit Fullscreen' : 'Fullscreen' }}
        </button>
        <button @click="showDraftOrders = true"
          class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Draft Orders
        </button>
        <button @click="showOpenTables = true"
          class="btn-hover px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
          Open Tables
        </button>
        <button @click="clearCart" class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
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

        <!-- Menu loading / error -->
        <div v-if="menuResource.loading" class="py-12 text-center text-xs text-gray-400">Loading menu items…</div>
        <div v-else-if="menuResource.error" class="py-12 text-center text-xs text-red-400">Failed to load menu. Check ERPNext Item configuration.</div>

        <!-- Menu grid -->
        <div v-else class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div v-for="item in filteredMenuItems" :key="item.id"
            @click="addToCart(item)"
            class="menu-card bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer relative select-none"
            :class="item.isStockItem && item.stock === 0 ? 'opacity-60 cursor-not-allowed' : ''">
            <div class="absolute top-2 right-2 z-10 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
              :class="!item.isStockItem ? 'bg-blue-500 text-white' : item.stock === 0 ? 'bg-red-500 text-white' : item.stock < 10 ? 'bg-orange-400 text-white' : 'bg-green-500 text-white'">
              {{ item.isStockItem ? item.stock : '∞' }}
            </div>
            <div class="aspect-[4/3] lg:aspect-[5/4] bg-gray-100 overflow-hidden">
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
                <td class="py-2 pr-1">
                  <input
                    type="checkbox"
                    class="w-3.5 h-3.5 accent-blue-600"
                    :checked="isKitchenSelected(item)"
                    :disabled="!isKitchenEligible(item)"
                    @change="onKitchenSelectionChange(item, $event.target.checked)" />
                </td>
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

        <!-- Kitchen Send Mode -->
        <div class="mb-4">
          <p class="text-xs font-semibold text-orange-600 mb-2">Kitchen Send Mode</p>
          <div class="flex items-center gap-1.5">
            <button
              @click="kitchenSendScope = 'all'"
              class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-all"
              :class="kitchenSendScope === 'all'
                ? 'bg-orange-500 text-white border-orange-500'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'">
              Group Items (All)
            </button>
            <button
              @click="kitchenSendScope = 'selected'"
              class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-all"
              :class="kitchenSendScope === 'selected'
                ? 'bg-orange-500 text-white border-orange-500'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'">
              Selected Items ({{ selectedKitchenCount }})
            </button>
          </div>
          <p class="text-[11px] text-gray-400 mt-1">Only items in configured kitchen item groups are sent.</p>
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
          <button @click="clearKitchenSelection" class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Edit Selection</button>
          <button @click="printBill" class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Print Bill</button>
          <button @click="onHoldSale"
            :disabled="holding || cart.length === 0"
            class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
            {{ holding ? 'Holding…' : 'Hold Sale' }}
          </button>
          <button @click="onChargeNow"
            :disabled="charging || cart.length === 0"
            class="btn-hover flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {{ charging ? 'Processing…' : 'Charge Now' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <Teleport to="body">
      <div v-if="chargeSuccess"
        class="fixed bottom-6 right-6 z-50 px-5 py-3 bg-green-600 text-white text-xs font-semibold rounded-xl shadow-xl flex items-center gap-2">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        {{ chargeSuccess }}
      </div>
      <div v-else-if="chargeError"
        class="fixed bottom-6 right-6 z-50 px-5 py-3 bg-red-600 text-white text-xs font-semibold rounded-xl shadow-xl flex items-center gap-2">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        {{ chargeError }}
      </div>
    </Teleport>

    <!-- Modals -->
    <DraftOrdersModal :key="draftOrdersKey" v-model="showDraftOrders" @resume="onResumeDraft" />
    <OpenTablesModal v-model="showOpenTables" />
    <PostToRoomModal
      v-model="showPostToRoom"
      :grand-total="grandTotal"
      :cart-items="cart"
      :service-charge="serviceCharge"
      :kitchen-note="kitchenNote"
      @room-selected="onRoomSelected"
      @confirmed="onPostConfirmed"
    />
    <SplitBillModal
      v-model="showSplitBill"
      :grand-total="grandTotal"
      :cart-items="cart"
      :service-charge="serviceCharge"
    />

    <!-- ── Open POS Shift — enforced blocking modal ─────────────────── -->
    <Teleport to="body">
      <div v-if="showOpenShiftModal" class="fixed inset-0 z-[90] flex items-center justify-center p-4" style="background:rgba(15,23,42,0.72);">
        <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl modal-panel overflow-hidden">

          <!-- Header -->
          <div class="px-6 pt-6 pb-4 border-b border-gray-100">
            <div class="flex items-center gap-3 mb-1">
              <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
              <div>
                <h3 class="text-sm font-bold text-gray-900">Open POS Shift</h3>
                <p class="text-xs text-gray-400">A shift must be open before you can process sales.</p>
              </div>
            </div>
          </div>

          <!-- Body -->
          <div class="px-6 py-5 space-y-4">

            <!-- Loading profiles -->
            <div v-if="openingProfilesResource.loading" class="text-center py-6">
              <div class="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2"></div>
              <p class="text-xs text-gray-400">Loading POS profiles…</p>
            </div>

            <!-- API error -->
            <div v-else-if="openingProfilesResource.error" class="text-center py-6">
              <svg class="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <p class="text-xs font-semibold text-red-500 mb-1">Failed To Load POS Profiles</p>
              <p class="text-xs text-gray-400">{{ openingProfilesResource.error?.message || 'Could not fetch assigned profiles.' }}</p>
              <button
                @click="openingProfilesResource.reload()"
                class="mt-3 px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-50"
              >Retry</button>
            </div>

            <!-- No profiles mapped -->
            <div v-else-if="openingProfiles.length === 0" class="text-center py-6">
              <svg class="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <p class="text-xs font-semibold text-red-500 mb-1">No POS Profile Assigned</p>
              <p class="text-xs text-gray-400">No POS Profile mapping found for user <span class="font-semibold text-gray-500">{{ openingProfilesResource.data?.current_user || 'current user' }}</span>.</p>
            </div>

            <!-- Profile selector + cash -->
            <template v-else>
              <div>
                <label class="block text-xs font-semibold text-gray-600 mb-1.5">POS Profile</label>
                <select
                  v-model="selectedOpeningProfile"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option disabled value="">— select profile —</option>
                  <option v-for="p in openingProfiles" :key="p.name" :value="p.name">{{ p.name }}</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-gray-600 mb-1.5">Opening Cash Float (₦)</label>
                <input
                  v-model="openingCash"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </template>

            <p v-if="openShiftError" class="px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">{{ openShiftError }}</p>
          </div>

          <!-- Footer -->
          <div class="px-6 pb-6 flex gap-2">
            <button
              @click="goToShiftClose"
              class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >Shift Manager</button>
            <button
              v-if="openingProfiles.length > 0"
              @click="openShiftNow"
              :disabled="openingShift || !selectedOpeningProfile"
              class="btn-hover flex-1 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="openingShift" class="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              {{ openingShift ? 'Opening shift…' : 'Open Shift Now' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'
import OpenTablesModal from '@/components/pos/OpenTablesModal.vue'
import PostToRoomModal from '@/components/pos/PostToRoomModal.vue'
import SplitBillModal from '@/components/pos/SplitBillModal.vue'

console.log('PointOfSales component loaded')

const router = useRouter()
const route = useRoute()

// ── Modals ─────────────────────────────────────────────────────────
const showDraftOrders = ref(false)
const showOpenTables = ref(false)
const showPostToRoom = ref(false)
const showSplitBill = ref(false)
const draftOrdersKey = ref(0)
const showOpenShiftModal = ref(false)
const selectedOpeningProfile = ref('')
const openingCash = ref('0')
const openShiftError = ref('')
const openingShift = ref(false)
const localShiftOpened = ref(false)

// ── POS state ──────────────────────────────────────────────────────
const menuSearch = ref('')
const activeCategory = ref('All Items')
const settlementMethod = ref('Cash')
const settlementMethods = ['Post to Room', 'Cash', 'POS', 'Split']
const kitchenNote = ref('')
const billToSearch = ref('')
const billToFocused = ref(false)
const roomNumber = ref('')
const roomFocused = ref(false)
const selectedBillTo = ref(null)
const chargeError = ref('')
const chargeSuccess = ref('')
const charging = ref(false)
const holding = ref(false)
const sendingKitchen = ref(false)
const kitchenSendScope = ref('all')
const selectedKitchenItemMap = ref({})
const lastSubmittedItems = ref([])
const lastSubmittedContext = ref({ tableOrRoom: '', source: 'Restaurant Dining', kitchenNote: '', sendScope: 'all', selectedItemCodes: [] })

const lastInvoiceName = ref('')

const isFullscreen = computed(() => route.query.fullscreen === '1')

function toggleFullscreen() {
  const nextQuery = { ...route.query }
  if (isFullscreen.value) {
    delete nextQuery.fullscreen
  } else {
    nextQuery.fullscreen = '1'
  }
  router.replace({ query: nextQuery })
}

// ── API: Current Shift / Terminal Info ────────────────────────────
const shiftInfoResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_shift_stats',
  auto: true,
})

const terminalInfo = computed(() => {
  const d = shiftInfoResource.data || {}
  return {
    cashier: d.cashier || '',
    pos_profile: d.pos_profile || '',
    shift_date: d.shift_date || '',
    has_open_shift: !!d.has_open_shift,
    pos_opening_entry: d.pos_opening_entry || null,
  }
})

const openingProfilesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_opening_profiles',
  auto: true,
  onError() {
    // Keep modal visible even if loading fails so user can't bypass
    showOpenShiftModal.value = true
  },
})

const openingProfiles = computed(() => openingProfilesResource.data?.profiles || [])
const hasOpenShift = computed(() => {
  const fromShiftStats = !!terminalInfo.value.has_open_shift
  const fromOpeningProfiles = !!openingProfilesResource.data?.has_open_shift
  return localShiftOpened.value || fromShiftStats || fromOpeningProfiles
})

watch(() => openingProfilesResource.data, (data) => {
  if (!data) return

  if (!selectedOpeningProfile.value) {
    selectedOpeningProfile.value = data.default_profile || data.open_pos_profile || ''
  }

  if (data.has_open_shift) {
    localShiftOpened.value = true
  }

  // Always enforce: modal stays open until a shift is confirmed open
  showOpenShiftModal.value = !hasOpenShift.value
})

// Show a locked loading state immediately so the POS is never usable before check
showOpenShiftModal.value = true

watch(() => terminalInfo.value.has_open_shift, (isOpen) => {
  if (isOpen) {
    localShiftOpened.value = true
    showOpenShiftModal.value = false
  }
})

const openShiftResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.create_pos_opening_entry',
  onSuccess() {
    openingShift.value = false
    openShiftError.value = ''
    localShiftOpened.value = true
    showOpenShiftModal.value = false
    shiftInfoResource.reload()
    openingProfilesResource.reload()
    chargeSuccess.value = 'POS shift opened successfully'
    setTimeout(() => { chargeSuccess.value = '' }, 3000)
  },
  onError(err) {
    openingShift.value = false
    openShiftError.value = err?.message || 'Failed to open shift'
  },
})

function openShiftNow() {
  if (!selectedOpeningProfile.value || openingShift.value) return
  openingShift.value = true
  openShiftError.value = ''
  openShiftResource.submit({
    pos_profile: selectedOpeningProfile.value,
    opening_cash: Number(openingCash.value || 0),
  })
}

function goToShiftClose() {
  router.push('/pos/shift-close')
}

// ── API: Menu Items ────────────────────────────────────────────────
const menuResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_menu_items',
  initialData: null,
  auto: true,
})

const categoriesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_item_categories',
  auto: true,
})

const kitchenGroupsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_item_groups',
  auto: true,
})

// ── API: Occupied Rooms (for room-number dropdown) ─────────────────
const occupiedRoomsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_occupied_rooms_for_pos',
  auto: false,
})

// ── API: Bill-To search ────────────────────────────────────────────
const billToResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.search_pos_bill_to',
  params: { query: '' },
  auto: false,
})

let billToTimer = null
watch(billToSearch, (q) => {
  clearTimeout(billToTimer)
  billToTimer = setTimeout(() => {
    billToResource.params = { query: q }
    billToResource.reload()
  }, 300)
})

// ── Computed: categories ───────────────────────────────────────────
const categories = computed(() => {
  const list = categoriesResource.data || []
  return ['All Items', ...list]
})

// ── Computed: menu items ───────────────────────────────────────────
const allMenuItems = computed(() =>
  (menuResource.data || []).map(it => ({
    id: it.item_code,
    item_code: it.item_code,
    name: it.name,
    category: it.category,
    price: Number(it.price) || 0,
    stock: Number(it.stock),
    isStockItem: !!it.is_stock_item,
    image: it.image || null,
  }))
)

const filteredMenuItems = computed(() => {
  let items = allMenuItems.value
  if (activeCategory.value !== 'All Items') {
    items = items.filter(i => i.category === activeCategory.value)
  }
  if (menuSearch.value) {
    const q = menuSearch.value.toLowerCase()
    items = items.filter(i => i.name.toLowerCase().includes(q))
  }
  return items
})

const kitchenItemGroups = computed(() => new Set(kitchenGroupsResource.data || []))
const selectedKitchenCount = computed(() =>
  cart.value.filter(i => isKitchenEligible(i) && selectedKitchenItemMap.value[i.id]).length
)

// ── Computed: bill-to results ──────────────────────────────────────
const billToResults = computed(() =>
  (billToResource.data || []).map(r => ({
    id: r.id,
    name: r.name,
    room: r.room || null,
    type: r.type,
  }))
)

// ── Computed: room suggestions ─────────────────────────────────────
const occupiedRooms = computed(() => occupiedRoomsResource.data || [])

const filteredRoomSuggestions = computed(() => {
  const rooms = occupiedRooms.value
  if (!roomNumber.value) return rooms.slice(0, 5)
  const q = roomNumber.value.toLowerCase()
  return rooms.filter(r =>
    (r.room || '').includes(q) ||
    (r.guest || '').toLowerCase().includes(q)
  )
})

// ── Cart ───────────────────────────────────────────────────────────
const cart = ref([])

function addToCart(item) {
  if (item.isStockItem && item.stock === 0) return
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

// ── Bill-To interaction ────────────────────────────────────────────
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
  if (settlementMethod.value === 'Post to Room' && guest.room) {
    roomNumber.value = guest.room
  }
}

function clearBillTo() {
  selectedBillTo.value = null
  billToSearch.value = ''
  roomNumber.value = ''
}

function selectRoomFromNumber(r) {
  roomNumber.value = r.room
  roomFocused.value = false
  selectedBillTo.value = { id: r.check_in, name: r.guest, room: r.room, type: r.payment_type || 'Direct Guest' }
}

function extractApiErrorMessage(err, fallback = 'Request failed') {
  const serverMessage = err?._server_messages
  if (serverMessage) {
    try {
      const parsed = JSON.parse(serverMessage)
      if (Array.isArray(parsed) && parsed.length > 0) {
        const first = JSON.parse(parsed[0])
        if (first?.message) return String(first.message)
      }
    } catch (_) {
      // Ignore malformed server message payload and fall back below.
    }
  }
  return err?.message || fallback
}

// ── API: Create POS Invoice (Cash / POS terminal) ──────────────────
const chargeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.create_pos_invoice',
  onSuccess(data) {
    const submitted = [...lastSubmittedItems.value]
    const context = { ...lastSubmittedContext.value }

    chargeSuccess.value = `Invoice ${data.pos_invoice} created — ₦${Number(data.grand_total).toLocaleString()}`
      lastInvoiceName.value = data.pos_invoice
    clearCart()
    charging.value = false
    triggerKitchenSend(data.pos_invoice, submitted, context)
    setTimeout(() => { chargeSuccess.value = '' }, 4000)
  },
  onError(err) {
    chargeError.value = extractApiErrorMessage(err, 'Failed to create invoice')
    charging.value = false
    setTimeout(() => { chargeError.value = '' }, 6000)
  },
})

const holdSaleResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.save_pos_draft_invoice',
  onSuccess(data) {
    const submitted = [...lastSubmittedItems.value]
    const context = { ...lastSubmittedContext.value }

    chargeSuccess.value = `Sale held as draft ${data.pos_invoice}`
      lastInvoiceName.value = data.pos_invoice
    holding.value = false
    clearCart()
    showDraftOrders.value = true
    draftOrdersKey.value += 1
    triggerKitchenSend(data.pos_invoice, submitted, context)
    setTimeout(() => { chargeSuccess.value = '' }, 4000)
  },
  onError(err) {
    chargeError.value = extractApiErrorMessage(err, 'Failed to hold sale')
    holding.value = false
    setTimeout(() => { chargeError.value = '' }, 6000)
  },
})

const sendKitchenResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.send_to_kitchen',
  onSuccess(data) {
    sendingKitchen.value = false
    if (data?.skipped) return
    chargeSuccess.value = `${chargeSuccess.value || ''}${chargeSuccess.value ? ' • ' : ''}Sent ${data.item_count} kitchen item(s)`
    setTimeout(() => { chargeSuccess.value = '' }, 4000)
  },
  onError(err) {
    sendingKitchen.value = false
    chargeError.value = err?.message || 'Failed to send kitchen items'
    setTimeout(() => { chargeError.value = '' }, 6000)
  },
})

function getKitchenSource() {
  if (settlementMethod.value === 'Post to Room' || selectedBillTo.value?.room) {
    return 'Room Service'
  }
  return 'Restaurant Dining'
}

function getKitchenItemsFrom(orderItems, context) {
  const groups = kitchenItemGroups.value
  if (!groups.size) return []

  let filtered = orderItems
    .filter(i => groups.has(i.category))
    .map(i => ({
      item_code: i.item_code || i.id,
      item_name: i.name,
      qty: i.qty,
    }))

  if (context?.sendScope === 'selected') {
    const selectedCodes = new Set(context?.selectedItemCodes || [])
    filtered = filtered.filter(i => selectedCodes.has(i.item_code))
  }

  return filtered
}

function triggerKitchenSend(posInvoice, submittedItems, context) {
  const kitchenItems = getKitchenItemsFrom(submittedItems, context)
  if (kitchenItems.length === 0 || sendingKitchen.value) return

  sendingKitchen.value = true
  sendKitchenResource.submit({
    pos_invoice: posInvoice,
    table_or_room: context.tableOrRoom || '',
    source: context.source || 'Restaurant Dining',
    kitchen_note: context.kitchenNote || null,
    items: JSON.stringify(kitchenItems),
  })
}

function captureSubmissionSnapshot() {
  lastSubmittedItems.value = cart.value.map(i => ({
    id: i.id,
    item_code: i.item_code || i.id,
    name: i.name,
    category: i.category,
    qty: i.qty,
    price: i.price,
  }))
  lastSubmittedContext.value = {
    tableOrRoom: selectedBillTo.value?.room || roomNumber.value || '',
    source: getKitchenSource(),
    kitchenNote: kitchenNote.value || '',
    sendScope: kitchenSendScope.value,
    selectedItemCodes: cart.value
      .filter(i => selectedKitchenItemMap.value[i.id])
      .map(i => i.item_code || i.id),
  }
}

function isKitchenEligible(item) {
  return kitchenItemGroups.value.has(item.category)
}

  function clearKitchenSelection() {
    selectedKitchenItemMap.value = {}
  }

  function printBill() {
    if (!lastInvoiceName.value) {
      chargeError.value = 'No invoice to print. Complete a sale first.'
      setTimeout(() => { chargeError.value = '' }, 3000)
      return
    }
    window.open(
      `/printview?doctype=POS%20Invoice&name=${encodeURIComponent(lastInvoiceName.value)}&trigger_print=1`,
      '_blank'
    )
  }

  function onResumeDraft(data) {
    if (!data || !data.items || data.items.length === 0) return
    cart.value = data.items.map(i => ({
      id: i.item_code,
      item_code: i.item_code,
      name: i.name,
      category: i.category || '',
      price: Number(i.price) || 0,
      stock: Number(i.stock) || 999,
      image: i.image || null,
      qty: Number(i.qty) || 1,
    }))
    selectedKitchenItemMap.value = {}
    kitchenNote.value = data.remarks || ''
    showDraftOrders.value = false
    chargeSuccess.value = `Draft ${data.invoice} resumed`
    setTimeout(() => { chargeSuccess.value = '' }, 3000)
  }

function isKitchenSelected(item) {
  return !!selectedKitchenItemMap.value[item.id]
}

function onKitchenSelectionChange(item, checked) {
  if (!isKitchenEligible(item)) return
  selectedKitchenItemMap.value = {
    ...selectedKitchenItemMap.value,
    [item.id]: !!checked,
  }
}

function clearCart() {
  cart.value = []
  selectedKitchenItemMap.value = {}
  selectedBillTo.value = null
  roomNumber.value = ''
  kitchenNote.value = ''
  billToSearch.value = ''
}

function onHoldSale() {
  if (cart.value.length === 0 || holding.value || !hasOpenShift.value) {
    if (!hasOpenShift.value) {
      showOpenShiftModal.value = true
      chargeError.value = 'Open POS shift before saving draft.'
      setTimeout(() => { chargeError.value = '' }, 3500)
    }
    return
  }
  chargeError.value = ''
  holding.value = true
  captureSubmissionSnapshot()

  holdSaleResource.submit({
    items: JSON.stringify(cart.value.map(i => ({
      item_code: i.item_code || i.id,
      qty: i.qty,
      price: i.price,
    }))),
    // Pass Bill-To name so backend can resolve an ERPNext Customer if it exists.
    customer: selectedBillTo.value?.name || billToSearch.value || null,
    service_charge: serviceCharge.value,
    kitchen_note: kitchenNote.value || null,
    pos_profile: terminalInfo.value?.pos_profile || null,
  })
}

// ── Settlement ─────────────────────────────────────────────────────
function setSettlementMethod(method) {
  settlementMethod.value = method
  if (method === 'Post to Room') {
    occupiedRoomsResource.reload()
    return
  }
  roomNumber.value = ''
}

function onChargeNow() {
  if (cart.value.length === 0 || charging.value || !hasOpenShift.value) {
    if (!hasOpenShift.value) {
      showOpenShiftModal.value = true
      chargeError.value = 'Open POS shift before charging.'
      setTimeout(() => { chargeError.value = '' }, 3500)
    }
    return
  }
  chargeError.value = ''

  if (settlementMethod.value === 'Post to Room') {
    captureSubmissionSnapshot()
    showPostToRoom.value = true
    return
  }
  if (settlementMethod.value === 'Split') {
    showSplitBill.value = true
    return
  }

  const mopMap = { Cash: 'Cash', POS: 'POS' }
  charging.value = true
  captureSubmissionSnapshot()
  chargeResource.submit({
    items: JSON.stringify(cart.value.map(i => ({
      item_code: i.item_code || i.id,
      qty: i.qty,
      price: i.price,
    }))),
    mode_of_payment: mopMap[settlementMethod.value] || 'Cash',
    // Pass Bill-To name so backend can resolve an ERPNext Customer if it exists.
    customer: selectedBillTo.value?.name || billToSearch.value || null,
    service_charge: serviceCharge.value,
    kitchen_note: kitchenNote.value || null,
    pos_profile: terminalInfo.value?.pos_profile || null,
  })
}

function onRoomSelected(room) {
  if (room) {
    selectedBillTo.value = { id: room.check_in, name: room.guest, room: room.room, type: 'Direct Guest' }
    roomNumber.value = room.room
  }
}

function onPostConfirmed() {
  const submitted = [...lastSubmittedItems.value]
  const context = { ...lastSubmittedContext.value }
  chargeSuccess.value = 'Bill posted to room folio successfully'
  clearCart()
  triggerKitchenSend(null, submitted, context)
  setTimeout(() => { chargeSuccess.value = '' }, 4000)
}

watch(settlementMethod, (val) => {
  if (val !== 'Post to Room') roomNumber.value = ''
  else if (selectedBillTo.value?.room) roomNumber.value = selectedBillTo.value.room
})

watch(cart, (items) => {
  const validIds = new Set(items.map(i => i.id))
  const nextMap = {}
  for (const [id, checked] of Object.entries(selectedKitchenItemMap.value)) {
    if (validIds.has(id)) nextMap[id] = checked
  }
  selectedKitchenItemMap.value = nextMap
}, { deep: true })
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