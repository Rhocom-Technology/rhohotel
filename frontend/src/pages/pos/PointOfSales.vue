<template>
  <div class="space-y-4 px-4 py-4 max-w-[1600px] mx-auto">

    <!-- Top bar info -->
    <div>
      <p class="text-xs text-gray-400">Quick billing workspace for restaurant, bar, mini-mart and in-house guest charges with direct room posting support.</p>
    </div>

    <!-- Terminal header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Current Terminal</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ terminalInfo.pos_profile || 'POS Terminal' }}<template v-if="terminalInfo.cashier"> • Cashier: {{ terminalInfo.cashier }}</template><template v-if="terminalInfo.shift_date"> • {{ terminalInfo.shift_date }}</template>
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
        <button @click="newSale" class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
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
      <div class="bg-white rounded-xl border border-gray-200 p-5 sticky top-4 overflow-hidden flex flex-col" style="max-height:calc(100vh - 32px);">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Current Sale</h3>

        <div class="flex-1 min-h-0 overflow-y-auto pr-1">

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
                    @mousedown="handleBillToResult(r)"
                    class="px-4 py-3 text-xs cursor-pointer border-b border-gray-50 last:border-0 flex items-center gap-3 transition-colors"
                    :class="r.active_table_invoice && r.active_table_invoice !== resumedDraftInvoice ? 'bg-orange-50 hover:bg-orange-100' : 'hover:bg-blue-50'">
                    <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                      style="background:#dbeafe;color:#1d4ed8">{{ r.name[0] }}</div>
                    <div>
                      <p class="font-semibold text-gray-900">{{ r.name }}</p>
                      <p class="text-gray-400 mt-0.5">
                        {{ r.active_table_invoice && r.active_table_invoice !== resumedDraftInvoice ? `Active table - resume ${r.active_table_invoice}` : (r.room ? `Room ${r.room}` : r.type) }}
                      </p>
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
              {{ selectedBillTo.name?.[0] || '?' }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-xs font-semibold text-gray-900">{{ selectedBillTo.name }}</p>
                <span v-if="unusedComplimentaryCount > 0"
                  class="px-2 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-full">
                  {{ unusedComplimentaryCount }} voucher{{ unusedComplimentaryCount === 1 ? '' : 's' }}
                </span>
              </div>
              <p class="text-xs text-gray-400 mt-0.5">{{ selectedBillTo.room ? `Room ${selectedBillTo.room}` : selectedBillTo.type }}</p>
            </div>
            <button @click="clearBillTo"
              class="text-gray-300 hover:text-red-500 transition-colors w-5 h-5 flex items-center justify-center rounded-full hover:bg-red-50 text-xs">✕</button>
          </div>
          <div v-if="selectedBillTo && unusedComplimentaryCount > 0"
            class="mt-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
            <p class="text-xs font-semibold text-emerald-800">Unused complimentary available</p>
            <div class="flex items-center gap-1.5 flex-wrap mt-1">
              <span v-for="voucher in unusedComplimentaries.slice(0, 3)" :key="voucher.name"
                class="px-2 py-0.5 text-xs font-medium bg-white text-emerald-700 border border-emerald-200 rounded-full">
                {{ voucher.complimentary_type }} • ₦{{ voucherRemainingValue(voucher).toLocaleString() }}
              </span>
            </div>
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
                    :key="`${item.id}-${kitchenSelectionResetKey}`"
                    type="checkbox"
                    class="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
                    :checked="isKitchenSelected(item)"
                    @change="onKitchenSelectionChange(item, $event.target.checked)" />
                </td>
                <td class="py-2 pr-2">
                  <span class="text-xs font-medium text-gray-900">{{ item.name }}</span>
                  <span v-if="kitchenSentIds.has(item.id)" class="ml-1 text-orange-500 text-xs" title="Sent to kitchen">🔥</span>
                </td>
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
        <div class="mb-4">
          <button @click="showDiscountPanel = !showDiscountPanel"
            class="w-full py-2 text-xs font-medium border border-dashed rounded-lg transition-all"
            :class="manualDiscountAmount > 0 ? 'text-green-700 border-green-300 bg-green-50 hover:bg-green-100' : 'text-gray-400 border-gray-200 hover:bg-gray-50 hover:text-gray-600 hover:border-gray-300'">
            {{ manualDiscountAmount > 0 ? `Manual discount: −₦${manualDiscountAmount.toLocaleString()}` : '+ Add Discount' }}
          </button>
          <div v-if="showDiscountPanel" class="mt-2 p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
            <div class="flex gap-1.5">
              <button @click="discountType = 'flat'"
                class="flex-1 py-1.5 text-xs font-medium rounded-lg border transition-all"
                :class="discountType === 'flat' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'">Flat (₦)</button>
              <button @click="discountType = 'percent'"
                class="flex-1 py-1.5 text-xs font-medium rounded-lg border transition-all"
                :class="discountType === 'percent' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'">Percent (%)</button>
            </div>
            <div class="flex gap-2 items-center">
              <input v-model="discountInput" type="number" min="0"
                :placeholder="discountType === 'flat' ? 'Amount (₦)' : 'Percent (%)'"
                class="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button @click="discountInput = ''; showDiscountPanel = false"
                class="px-3 py-2 text-xs text-red-500 hover:bg-red-50 rounded-lg border border-red-200 transition-colors">Clear</button>
            </div>
          </div>
        </div>

        <!-- Complimentary Voucher -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-semibold text-emerald-700">Complimentary Voucher</p>
            <button @click="loadComplimentaries" class="text-xs text-blue-600 hover:text-blue-700">Refresh</button>
          </div>
          <select v-model="selectedComplimentaryName"
            :disabled="complimentaryResource.loading"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
            <option value="">{{ complimentaryResource.loading ? 'Loading vouchers...' : 'No voucher applied' }}</option>
            <option v-for="voucher in redeemableComplimentaries" :key="voucher.name" :value="voucher.name">
              {{ voucher.name }} — {{ voucher.complimentary_type }} — ₦{{ voucherRemainingValue(voucher).toLocaleString() }} remaining
            </option>
          </select>
          <div v-if="selectedComplimentary" class="mt-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold text-emerald-800">{{ selectedComplimentary.name }} applies −₦{{ complimentaryDiscountAmount.toLocaleString() }}</p>
              <button @click="selectedComplimentaryName = ''" class="text-xs text-emerald-600 hover:text-emerald-800">Remove</button>
            </div>
            <p class="text-xs text-emerald-700 mt-1">Guest: {{ selectedComplimentary.guest || selectedBillTo?.name || 'Walk In' }}<template v-if="selectedComplimentary.expiry_date"> • Expires {{ selectedComplimentary.expiry_date }}</template></p>
          </div>
          <p v-else class="text-[11px] text-gray-400 mt-1">Approved restaurant complimentaries for the selected guest or room appear here.</p>
        </div>

        <!-- Totals -->
        <div class="space-y-1.5 mb-4 border-t border-gray-100 pt-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">Sub Total</span>
            <span class="text-xs font-medium text-gray-700">₦{{ subTotal.toLocaleString() }}</span>
          </div>
          <div v-if="discountAmount > 0" class="flex items-center justify-between">
            <span class="text-xs text-green-600">Discount</span>
            <span class="text-xs font-medium text-green-600">−₦{{ discountAmount.toLocaleString() }}</span>
          </div>
          <div v-if="selectedComplimentary" class="flex items-center justify-between">
            <span class="text-xs text-emerald-600">Voucher</span>
            <span class="text-xs font-medium text-emerald-600">{{ selectedComplimentary.name }}</span>
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
          <!-- <div class="flex items-center gap-1.5">
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
          </div> -->

          <p class="text-[11px] text-gray-400 mt-1">Only items in configured kitchen item groups are sent.</p>
          <!-- Send to Kitchen Now -->
          <button @click="sendToKitchenNow"
           :disabled="sendingKitchenNow || cart.length === 0 || !hasKitchenItems"
            class="btn-hover mt-2 w-full py-2 text-xs font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            :class="Object.keys(kitchenSentMap).length > 0
              ? 'text-orange-700 bg-orange-50 border border-orange-300 hover:bg-orange-100'
              : 'text-white bg-orange-500 hover:bg-orange-600'">
            {{ kitchenSendButtonLabel }}
          </button>
        </div>

        <!-- Note -->
        <!-- <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Note / Kitchen Instruction</p>
          <textarea v-model="kitchenNote" rows="2"
            placeholder="No pepper on meal. Deliver to room within 20 mins..."
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div> -->
        </div>

        <!-- Actions -->
        <div class="flex gap-2 flex-shrink-0 bg-white pt-3 pb-1 border-t border-gray-100">
          <button @click="clearCart" class="btn-hover px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Clear Cart</button>
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
    <OpenTablesModal v-model="showOpenTables" @resume="onResumeTable" />
    <PostToRoomModal
      v-model="showPostToRoom"
      :grand-total="grandTotal"
      :cart-items="cart"
      :service-charge="serviceCharge"
      :discount-amount="discountAmount"
      :manual-discount-amount="manualDiscountAmount"
      :complimentary-name="selectedComplimentaryName"
      :kitchen-note="kitchenNote"
      :cashier="terminalInfo.cashier"
      :pos-profile="terminalInfo.pos_profile"
      :bill-to="selectedBillTo?.name || billToSearch || ''"
      :existing-draft="resumedDraftInvoice"
      @room-selected="onRoomSelected"
      @confirmed="onPostConfirmed"
    />
    <SplitBillModal
      v-model="showSplitBill"
      :grand-total="grandTotal"
      :cart-items="cart"
      :service-charge="serviceCharge"
      :discount-amount="discountAmount"
      :manual-discount-amount="manualDiscountAmount"
      :complimentary-name="selectedComplimentaryName"
      :kitchen-note="kitchenNote"
      :cashier="terminalInfo.cashier"
      :pos-profile="terminalInfo.pos_profile"
      :pre-selected-room="selectedBillTo?.room ? { room: selectedBillTo.room, guest: selectedBillTo.name, check_in: selectedBillTo.id } : null"
      :existing-draft="resumedDraftInvoice"
      @confirmed="onSplitConfirmed"
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'
import OpenTablesModal from '@/components/pos/OpenTablesModal.vue'
import PostToRoomModal from '@/components/pos/PostToRoomModal.vue'
import SplitBillModal from '@/components/pos/SplitBillModal.vue'
import { clearReservedPOSInvoicePrintPreview, openReservedPrintPreview, printPOSInvoice, reservePOSInvoicePrintPreview } from '@/lib/posPrint'

const router = useRouter()
const route = useRoute()

// ── Modals ─────────────────────────────────────────────────────────
const showDraftOrders = ref(false)
const showOpenTables = ref(false)
const showPostToRoom = ref(false)
const showSplitBill = ref(false)
const draftOrdersKey = ref(0)

// Track the draft invoice currently loaded in the cart (so re-holding replaces it)
const resumedDraftInvoice = ref(null)
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
const kitchenSelectionResetKey = ref(0)
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
    menuResource.reload()
    categoriesResource.reload()
    kitchenGroupsResource.reload()
  }
}, { immediate: true })

const openShiftResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.create_pos_opening_entry',
  onSuccess() {
    openingShift.value = false
    openShiftError.value = ''
    localShiftOpened.value = true
    showOpenShiftModal.value = false
    shiftInfoResource.reload()
    openingProfilesResource.reload()
    menuResource.reload()
    categoriesResource.reload()
    kitchenGroupsResource.reload()
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
  auto: false,
})

const categoriesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_item_categories',
  auto: false,
})

const kitchenGroupsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_item_groups',
  auto: false,
})

// ── API: Occupied Rooms (for room-number dropdown) ─────────────────
const occupiedRoomsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_occupied_rooms_for_pos',
  auto: false,
})

// ── API: Bill-To search ────────────────────────────────────────────
// REPLACE with:
const billToResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.search_pos_bill_to',
  auto: false,
})

const openTablesGuardResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_open_pos_tables',
  auto: true,
})

// let billToTimer = null
// watch(billToSearch, (q) => {
//   clearTimeout(billToTimer)
//   billToTimer = setTimeout(() => {
//     billToResource.params = { query: q }
//     billToResource.reload()
//   }, 300)
// })

// // Load default results (including Walk In) when the Bill-To input gains focus
// watch(billToFocused, (focused) => {
//   if (focused && !billToSearch.value) {
//     billToResource.params = { query: '' }
//     billToResource.reload()
//   }
// })


const clearingCart = ref(false)

// REPLACE with:
let billToTimer = null

function reloadBillTo(q) {
  try {
    billToResource.submit({ query: q || '' })
  } catch (_) {}
}

watch(billToSearch, (q) => {
  clearTimeout(billToTimer)
  billToTimer = setTimeout(() => reloadBillTo(q), 300)
})

watch(billToFocused, (focused) => {
  if (focused && !billToSearch.value) reloadBillTo('')
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
const selectedCartItems = computed(() =>
  cart.value.filter(i => isKitchenSelected(i))
)
const selectedKitchenCount = computed(() =>
  selectedCartItems.value.filter(i => isKitchenEligible(i)).length
)
const hasSelectedCartItems = computed(() => selectedCartItems.value.length > 0)

// ── Computed: bill-to results ──────────────────────────────────────
const billToResults = computed(() =>
  (billToResource.data || []).map(r => {
    const activeTable = getActiveTableForName(r.name || r.customer)
    return {
      id: r.check_in || r.id,
      check_in: r.check_in || null,
      customer: r.customer || r.id,
      guest: r.guest || null,
      name: r.name,
      room: r.room || null,
      room_type: r.room_type || null,
      type: r.type,
      payment_type: r.payment_type || null,
      active_table_invoice: r.active_table_invoice || activeTable?.invoice || null,
      active_table_bill: Number(r.active_table_bill || activeTable?.bill || 0),
    }
  })
)

const activeTableByName = computed(() => {
  const map = new Map()
  for (const table of (openTablesGuardResource.data || [])) {
    if (table.name) map.set(normalizeTableName(table.name), table)
  }
  return map
})

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
const serviceCharge = computed(() => 0)
const showDiscountPanel = ref(false)
const discountType = ref('flat')
const discountInput = ref('')
const selectedComplimentaryName = ref('')
const redeemableComplimentaries = ref([])
const unusedComplimentaries = ref([])

const manualDiscountAmount = computed(() => {
  const val = parseFloat(discountInput.value) || 0
  if (!val) return 0
  if (discountType.value === 'percent') return Math.min(Math.round(subTotal.value * val / 100), subTotal.value)
  return Math.min(val, subTotal.value)
})
const selectedComplimentary = computed(() =>
  redeemableComplimentaries.value.find(v => v.name === selectedComplimentaryName.value) || null
)
const complimentaryDiscountAmount = computed(() => {
  if (!selectedComplimentary.value) return 0
  return Math.min(voucherRemainingValue(selectedComplimentary.value), Math.max(0, subTotal.value - manualDiscountAmount.value))
})
const discountAmount = computed(() => Math.min(subTotal.value, manualDiscountAmount.value + complimentaryDiscountAmount.value))
const grandTotal = computed(() => Math.max(0, subTotal.value - discountAmount.value))
const unusedComplimentaryCount = computed(() => unusedComplimentaries.value.length)

const complimentaryResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_redeemable_complimentaries',
  auto: false,
  onSuccess(data) {
    redeemableComplimentaries.value = Array.isArray(data) ? data : []
    if (selectedComplimentaryName.value && !redeemableComplimentaries.value.some(v => v.name === selectedComplimentaryName.value)) {
      selectedComplimentaryName.value = ''
    }
  },
  onError() {
    redeemableComplimentaries.value = []
    selectedComplimentaryName.value = ''
  },
})

const complimentaryIndicatorResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_unused_complimentary_indicator',
  auto: false,
  onSuccess(data) {
    unusedComplimentaries.value = data?.items || []
  },
  onError() {
    unusedComplimentaries.value = []
  },
})

function loadComplimentaries() {
  complimentaryResource.submit({
    check_in: selectedBillTo.value?.id || null,
    room: selectedBillTo.value?.room || roomNumber.value || null,
    guest: selectedBillTo.value?.name || billToSearch.value || null,
    department: 'Restaurant',
  })
  loadComplimentaryIndicator()
}

function loadComplimentaryIndicator() {
  complimentaryIndicatorResource.submit({
    check_in: selectedBillTo.value?.id || null,
    room: selectedBillTo.value?.room || roomNumber.value || null,
    guest: selectedBillTo.value?.name || billToSearch.value || null,
  })
}

function voucherRemainingValue(voucher) {
  if (!voucher) return 0
  if (voucher.remaining_value !== undefined && voucher.remaining_value !== null) {
    return Number(voucher.remaining_value || 0)
  }
  return Math.max(0, Number(voucher.value || 0) - Number(voucher.redeemed_amount || 0))
}

// ── Kitchen send tracking ─────────────────────────────────────────
const kitchenSentMap = ref({}) // { item_code: qty_already_sent_to_kitchen }
const sendingKitchenNow = ref(false)
const kitchenSentIds = computed(() => {
  const sent = new Set()
  for (const item of cart.value) {
    const code = item.item_code || item.id
    if ((kitchenSentMap.value[code] || 0) >= item.qty) sent.add(item.id)
  }
  return sent
})

const hasKitchenItems = computed(() =>
  cart.value.some(i => kitchenItemGroups.value.has(i.category))
)

const kitchenSendButtonLabel = computed(() => {
  if (sendingKitchenNow.value) return 'Sending to Kitchen…'
  if (Object.keys(kitchenSentMap.value).length > 0) return '🔥 Send More to Kitchen'
  return `🔥 Send to Kitchen${hasSelectedCartItems.value ? ` (${selectedCartItems.value.length} selected)` : ' (All)'}`
})

// ── Bill-To interaction ────────────────────────────────────────────
function delayBlur(field) {
  setTimeout(() => {
    if (field === 'billToFocused') billToFocused.value = false
    if (field === 'roomFocused') roomFocused.value = false
  }, 200)
}

function normalizeTableName(value) {
  return String(value || '').trim().replace(/\s+/g, ' ').toLowerCase()
}

function extractTableDisplayName(value) {
  const name = String(value || '').trim()
  return /^(Table|Bar|Pool)\s*\S/i.test(name) ? name : ''
}

function getActiveTableForName(value) {
  const tableName = extractTableDisplayName(value)
  if (!tableName) return null
  return activeTableByName.value.get(normalizeTableName(tableName)) || null
}

function showOccupiedTableResumeMessage(table) {
  chargeError.value = `${table.name} already has a held sale. Resume it from Open Tables.`
  showOpenTables.value = true
  try { openTablesGuardResource.reload() } catch (_) {}
  setTimeout(() => { chargeError.value = '' }, 5000)
}

function guardOccupiedTableSelection(value) {
  const table = getActiveTableForName(value)
  if (!table || table.invoice === resumedDraftInvoice.value) return false
  showOccupiedTableResumeMessage(table)
  return true
}

function handleBillToResult(guest) {
  const activeTable = guest.active_table_invoice
    ? { invoice: guest.active_table_invoice, name: guest.name }
    : getActiveTableForName(guest.name || guest.customer)
  if (activeTable && activeTable.invoice !== resumedDraftInvoice.value) {
    billToSearch.value = ''
    billToFocused.value = false
    showOccupiedTableResumeMessage(activeTable)
    return
  }
  selectBillTo(guest)
}

function selectBillTo(guest) {
  selectedBillTo.value = {
    ...guest,
    id: guest.check_in || guest.id,
  }
  billToSearch.value = ''
  billToFocused.value = false
  if (guest.room) {
    roomNumber.value = guest.room
  }
  loadComplimentaries()
}

// REPLACE with:
function clearBillTo() {
  selectedBillTo.value = null
  billToSearch.value = ''
  roomNumber.value = ''
  selectedComplimentaryName.value = ''
  redeemableComplimentaries.value = []
  unusedComplimentaries.value = []
}

function selectRoomFromNumber(r) {
  roomNumber.value = r.room
  roomFocused.value = false
  selectedBillTo.value = { id: r.check_in, name: r.guest, room: r.room, type: r.payment_type || 'Direct Guest' }
  loadComplimentaries()
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

function printReceiptFromResponse(data) {
  const posInvoice = data?.pos_invoice || data?.pos_invoice_name || ''
  if (posInvoice) {
    printPOSInvoice(posInvoice)
    return posInvoice
  }

  const salesInvoice = data?.sales_invoice || data?.room_sales_invoices?.[0]?.sales_invoice || ''
  if (salesInvoice) {
    openReservedPrintPreview('Sales Invoice', salesInvoice)
    return salesInvoice
  }

  clearReservedPOSInvoicePrintPreview()
  return ''
}

// ── API: Create POS Invoice (Cash / POS terminal) ──────────────────
const chargeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.create_pos_invoice',
  onSuccess(data) {
    const submitted = [...lastSubmittedItems.value]
    const context = { ...lastSubmittedContext.value }

    chargeSuccess.value = `Invoice ${data.pos_invoice} created — ₦${Number(data.grand_total).toLocaleString()}`
    lastInvoiceName.value = data.pos_invoice
    playSuccessSound()
    clearCart()
    clearBillTo()
    charging.value = false
    menuResource.reload()
    openTablesGuardResource.reload()
    // Auto-print receipt
    printReceiptFromResponse(data)
    triggerKitchenSend(data.pos_invoice, submitted, context)
    setTimeout(() => { chargeSuccess.value = '' }, 4000)
  },
  onError(err) {
    clearReservedPOSInvoicePrintPreview()
    chargeError.value = extractApiErrorMessage(err, 'Failed to create invoice')
    charging.value = false
    setTimeout(() => { chargeError.value = '' }, 6000)
  },
})

const holdSaleResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.save_pos_draft_invoice',
  onSuccess(data) {
    chargeSuccess.value = `Sale held as draft ${data.pos_invoice}`
    lastInvoiceName.value = data.pos_invoice
    playSuccessSound()
    holding.value = false
    clearCart()
    clearBillTo()
    menuResource.reload()
    openTablesGuardResource.reload()
    draftOrdersKey.value++
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

// ── API: Post to Room (direct — when room already selected) ──────────────
const postToRoomDirectResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.post_bill_to_room',
  onSuccess(data) {
    const submitted = [...lastSubmittedItems.value]
    const context = { ...lastSubmittedContext.value }
    lastInvoiceName.value = data?.pos_invoice || data?.sales_invoice || ''
    chargeSuccess.value = 'Bill posted to room folio successfully'
    playSuccessSound()
    clearCart()
    clearBillTo()
    charging.value = false
    menuResource.reload()
    openTablesGuardResource.reload()
    printReceiptFromResponse(data)
    triggerKitchenSend(data?.pos_invoice || null, submitted, context)
    setTimeout(() => { chargeSuccess.value = '' }, 4000)
  },
  onError(err) {
    clearReservedPOSInvoicePrintPreview()
    chargeError.value = extractApiErrorMessage(err, 'Failed to post bill to room')
    charging.value = false
    setTimeout(() => { chargeError.value = '' }, 6000)
  },
})

// Draft saved silently when user taps "Send to Kitchen" — keeps cart alive
const kitchenDraftResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.save_pos_draft_invoice',
  onSuccess(data) {
    lastInvoiceName.value = data.pos_invoice
    resumedDraftInvoice.value = data.pos_invoice  // track so re-hold replaces it
    openTablesGuardResource.reload()
    // Now fire the kitchen ticket linked to this draft
    const toSend = kitchenDraftResource._pendingKitchenItems
    if (toSend && toSend.length > 0) {
      sendKitchenNowResource.submit({
        pos_invoice: data.pos_invoice,
        table_or_room: selectedBillTo.value?.room || roomNumber.value || '',
        source: getKitchenSource(),
        kitchen_note: kitchenNote.value || null,
        items: JSON.stringify(toSend),
      })
    } else {
      sendingKitchenNow.value = false
    }
  },
  onError(err) {
    sendingKitchenNow.value = false
    chargeError.value = extractApiErrorMessage(err, 'Failed to save draft order')
    setTimeout(() => { chargeError.value = '' }, 5000)
  },
})

// Pre-billing kitchen send (explicit "Send to Kitchen" button)
const sendKitchenNowResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.send_to_kitchen',
  onSuccess(data) {
    sendingKitchenNow.value = false
    if (data?.skipped) {
      chargeSuccess.value = 'All kitchen items already sent for this order'
      setTimeout(() => { chargeSuccess.value = '' }, 3000)
      return
    }
    // Mark items as sent locally so billing doesn't double-send them
    const sentCodes = new Set(data.item_codes || [])
    const updated = { ...kitchenSentMap.value }
    for (const item of cart.value) {
      const code = item.item_code || item.id
      if (sentCodes.has(code)) updated[code] = item.qty
    }
    kitchenSentMap.value = updated
    chargeSuccess.value = `Sent ${data.item_count} item(s) to kitchen — Ticket ${data.ticket} (order saved as draft)`
    setTimeout(() => { chargeSuccess.value = '' }, 5000)
  },
  onError(err) {
    sendingKitchenNow.value = false
    chargeError.value = err?.message || 'Failed to send to kitchen'
    setTimeout(() => { chargeError.value = '' }, 5000)
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
    .map(i => {
      const code = i.item_code || i.id
      const alreadySent = context?.dedupeOnServer ? 0 : (kitchenSentMap.value[code] || 0)
      return {
        item_code: code,
        item_name: i.name,
        qty: Math.max(0, i.qty - alreadySent),
      }
    })
    .filter(i => i.qty > 0)

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

function sendToKitchenNow() {
  if (cart.value.length === 0 || sendingKitchenNow.value) return

  // 1. Customer must be selected
  const customer = selectedBillTo.value?.name || billToSearch.value || null
  if (!customer) {
    chargeError.value = 'Select a customer before sending to kitchen.'
    setTimeout(() => { chargeError.value = '' }, 4000)
    return
  }
  if (guardOccupiedTableSelection(customer)) return

  // 2. Resolve items to send (checked first, then all)
  const sourceItems = hasSelectedCartItems.value ? selectedCartItems.value : cart.value

  const groups = kitchenItemGroups.value
  const eligibleItems = groups.size
    ? sourceItems.filter(i => groups.has(i.category))
    : sourceItems

  const toSend = eligibleItems
    .map(i => {
      const code = i.item_code || i.id
      return { item_code: code, item_name: i.name, qty: i.qty }
    })
    .filter(i => i.qty > 0)

  if (toSend.length === 0) {
    chargeSuccess.value = 'All selected items already sent to kitchen'
    setTimeout(() => { chargeSuccess.value = '' }, 3000)
    return
  }

  // 3. Save a draft order first (persists order on refresh), then send to kitchen
  sendingKitchenNow.value = true
  kitchenDraftResource._pendingKitchenItems = toSend
  kitchenDraftResource.submit({
    items: JSON.stringify(cart.value.map(i => ({
      item_code: i.item_code || i.id,
      qty: i.qty,
      price: i.price,
    }))),
    customer,
    service_charge: serviceCharge.value,
    discount_amount: discountAmount.value,
    kitchen_note: kitchenNote.value || null,
    pos_profile: terminalInfo.value?.pos_profile || null,
    existing_draft: resumedDraftInvoice.value || null,
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
    selectedItemCodes: selectedCartItems.value
      .map(i => i.item_code || i.id),
    dedupeOnServer: !!resumedDraftInvoice.value,
  }
}

function isKitchenEligible(item) {
  return kitchenItemGroups.value.has(item.category)
}

function clearKitchenSelection() {
  selectedKitchenItemMap.value = {}
  kitchenSelectionResetKey.value++
  kitchenSendScope.value = 'all'
  chargeSuccess.value = 'Kitchen item selection cleared'
  setTimeout(() => { chargeSuccess.value = '' }, 2000)
}

  function printBill() {
    if (!lastInvoiceName.value) {
      chargeError.value = 'No invoice to print. Complete a sale first.'
      setTimeout(() => { chargeError.value = '' }, 3000)
      return
    }
    printPOSInvoice(lastInvoiceName.value)
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
    kitchenSentMap.value = normalizeKitchenSentMap(data.sent_to_kitchen)
    kitchenNote.value = data.remarks || ''
    // Restore discount
    const dAmt = Number(data.discount_amount || 0)
    discountType.value = 'flat'
    discountInput.value = dAmt > 0 ? String(dAmt) : ''
    showDiscountPanel.value = dAmt > 0
    // Restore bill-to from customer
    if (data.customer) {
      selectedBillTo.value = { id: data.customer, name: data.customer, room: null, type: 'Customer' }
    }
    // Track this draft so re-holding replaces it instead of creating a new one
    resumedDraftInvoice.value = data.invoice
    lastInvoiceName.value = data.invoice
    showDraftOrders.value = false
    chargeSuccess.value = `Draft ${data.invoice} resumed`
    setTimeout(() => { chargeSuccess.value = '' }, 3000)
  }

function playSuccessSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const notes = [523.25, 659.25, 783.99] // C5, E5, G5 — ascending major arpeggio
    notes.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'sine'
      osc.frequency.value = freq
      const t = ctx.currentTime + i * 0.13
      gain.gain.setValueAtTime(0, t)
      gain.gain.linearRampToValueAtTime(0.28, t + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.38)
      osc.start(t)
      osc.stop(t + 0.38)
    })
  } catch (_) {}
}

function isKitchenSelected(item) {
  return !!selectedKitchenItemMap.value[item.id]
}

function onKitchenSelectionChange(item, checked) {
  const nextMap = { ...selectedKitchenItemMap.value }
  if (checked) nextMap[item.id] = true
  else delete nextMap[item.id]
  selectedKitchenItemMap.value = nextMap
}

// ── POS state persistence ──────────────────────────────────────────
const POS_STATE_KEY = 'rhohotel_pos_draft_state'

function savePosState() {
  try {
    localStorage.setItem(POS_STATE_KEY, JSON.stringify({
      cart: cart.value,
      selectedBillTo: selectedBillTo.value,
      kitchenNote: kitchenNote.value,
      discountType: discountType.value,
      discountInput: discountInput.value,
      showDiscountPanel: showDiscountPanel.value,
      settlementMethod: settlementMethod.value,
      resumedDraftInvoice: resumedDraftInvoice.value,
      lastInvoiceName: lastInvoiceName.value,
      kitchenSentMap: kitchenSentMap.value,
    }))
  } catch (_) {}
}

function restorePosState() {
  try {
    const raw = localStorage.getItem(POS_STATE_KEY)
    if (!raw) return
    const s = JSON.parse(raw)
    if (Array.isArray(s.cart) && s.cart.length) {
      cart.value = s.cart
      chargeSuccess.value = 'Cart restored from your last session'
      setTimeout(() => { chargeSuccess.value = '' }, 4000)
    }
    if (s.selectedBillTo) selectedBillTo.value = s.selectedBillTo
    if (s.kitchenNote) kitchenNote.value = s.kitchenNote
    if (s.discountType) discountType.value = s.discountType
    if (s.discountInput) discountInput.value = s.discountInput
    showDiscountPanel.value = !!s.showDiscountPanel
    if (s.settlementMethod) settlementMethod.value = s.settlementMethod
    if (s.resumedDraftInvoice) resumedDraftInvoice.value = s.resumedDraftInvoice
    if (s.lastInvoiceName) lastInvoiceName.value = s.lastInvoiceName
    if (s.kitchenSentMap) kitchenSentMap.value = s.kitchenSentMap
  } catch (_) {}
}

onMounted(() => {
  try {
    const shiftCloseMessage = sessionStorage.getItem('rhohotel_pos_shift_close_success')
    if (shiftCloseMessage) {
      sessionStorage.removeItem('rhohotel_pos_shift_close_success')
      chargeSuccess.value = shiftCloseMessage
      setTimeout(() => { chargeSuccess.value = '' }, 5000)
    }
  } catch (_) {}
  restorePosState()
  if (selectedBillTo.value?.id || selectedBillTo.value?.room) {
    loadComplimentaries()
  }
})

// function clearCart() {
//   cart.value = []
//   selectedKitchenItemMap.value = {}
//   kitchenSentMap.value = {}
//   selectedBillTo.value = null
//   roomNumber.value = ''
//   kitchenNote.value = ''
//   billToSearch.value = ''
//   discountInput.value = ''
//   showDiscountPanel.value = false
//   resumedDraftInvoice.value = null
//   try { localStorage.removeItem(POS_STATE_KEY) } catch (_) {}
// }


// REPLACE with:
function clearCart() {
  cart.value = []
  selectedKitchenItemMap.value = {}
  kitchenSentMap.value = {}
  kitchenNote.value = ''
  discountInput.value = ''
  selectedComplimentaryName.value = ''
  showDiscountPanel.value = false
  resumedDraftInvoice.value = null
  try { localStorage.removeItem(POS_STATE_KEY) } catch (_) {}
}

function newSale() {
  clearCart()
  clearBillTo()
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
  const customer = selectedBillTo.value?.customer || selectedBillTo.value?.name || billToSearch.value || null
  if (guardOccupiedTableSelection(customer)) return
  holding.value = true
  captureSubmissionSnapshot()

  holdSaleResource.submit({
    items: JSON.stringify(cart.value.map(i => ({
      item_code: i.item_code || i.id,
      qty: i.qty,
      price: i.price,
    }))),
    // Pass Bill-To name so backend can resolve an ERPNext Customer if it exists.
    customer,
    service_charge: serviceCharge.value,
    discount_amount: discountAmount.value,
    kitchen_note: kitchenNote.value || null,
    pos_profile: terminalInfo.value?.pos_profile || null,
    // Replace existing draft when re-holding a resumed order
    existing_draft: resumedDraftInvoice.value || null,
  })
}

// ── Settlement ─────────────────────────────────────────────────────
function setSettlementMethod(method) {
  settlementMethod.value = method
  if (method === 'Post to Room') {
    if (selectedBillTo.value?.room) roomNumber.value = selectedBillTo.value.room
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
  const customer = selectedBillTo.value?.customer || selectedBillTo.value?.name || billToSearch.value || null
  if (guardOccupiedTableSelection(customer)) return

  if (settlementMethod.value === 'Post to Room') {
    // If a room is already selected, post directly without showing the modal
    if (selectedBillTo.value?.room && (selectedBillTo.value?.check_in || selectedBillTo.value?.id)) {
      captureSubmissionSnapshot()
      charging.value = true
      reservePOSInvoicePrintPreview()
      postToRoomDirectResource.submit({
        items: JSON.stringify(cart.value.map(i => ({
          item_code: i.item_code || i.id,
          qty: i.qty,
          price: i.price,
        }))),
        check_in: selectedBillTo.value.check_in || selectedBillTo.value.id,
        service_charge: serviceCharge.value,
        discount_amount: manualDiscountAmount.value,
        complimentary_name: selectedComplimentaryName.value || null,
        kitchen_note: kitchenNote.value || null,
        pos_profile: terminalInfo.value?.pos_profile || null,
        existing_draft: resumedDraftInvoice.value || null,
      })
      return
    }
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
  reservePOSInvoicePrintPreview()
  chargeResource.submit({
    items: JSON.stringify(cart.value.map(i => ({
      item_code: i.item_code || i.id,
      qty: i.qty,
      price: i.price,
    }))),
    mode_of_payment: mopMap[settlementMethod.value] || 'Cash',
    // Pass Bill-To name so backend can resolve an ERPNext Customer if it exists.
    customer,
    service_charge: serviceCharge.value,
    discount_amount: manualDiscountAmount.value,
    complimentary_name: selectedComplimentaryName.value || null,
    kitchen_note: kitchenNote.value || null,
    pos_profile: terminalInfo.value?.pos_profile || null,
    existing_draft: resumedDraftInvoice.value || null,
  })
}

// function onSplitConfirmed() {
//   console.log('onSplitConfirmed called')
//   clearCart()
//   menuResource.reload()
//   chargeSuccess.value = 'Split bill processed successfully'
//   setTimeout(() => { chargeSuccess.value = '' }, 4000)
// }

function onSplitConfirmed(data) {
  clearCart()
  clearBillTo()
  menuResource.reload()
  openTablesGuardResource.reload()
  chargeSuccess.value = 'Split bill processed successfully'
  printReceiptFromResponse(data)
  setTimeout(() => { chargeSuccess.value = '' }, 4000)
}

function onRoomSelected(room) {
  if (room) {
    selectedBillTo.value = { id: room.id, name: room.name, room: room.room, type: room.type || 'Direct Guest' }
    roomNumber.value = room.room
  }
}

function onPostConfirmed(data) {
  const submitted = [...lastSubmittedItems.value]
  const context = { ...lastSubmittedContext.value }
  lastInvoiceName.value = data?.pos_invoice || data?.sales_invoice || ''
  chargeSuccess.value = 'Bill posted to room folio successfully'
  playSuccessSound()
  clearCart()
  clearBillTo()
  menuResource.reload()
  openTablesGuardResource.reload()
  printReceiptFromResponse(data)
  triggerKitchenSend(data?.pos_invoice || null, submitted, context)
  setTimeout(() => { chargeSuccess.value = '' }, 4000)
}

function onResumeTable(table) {
  if (!table || !table.items || table.items.length === 0) return
  cart.value = table.items.map(i => ({
    id: i.item_code || i.name,
    item_code: i.item_code || i.name,
    name: i.name,
    category: '',
    price: i.price || (i.qty > 0 ? Math.round(i.amount / i.qty) : 0),
    stock: 999,
    isStockItem: false,
    image: null,
    qty: i.qty,
  }))
  selectedKitchenItemMap.value = {}
  kitchenSentMap.value = normalizeKitchenSentMap(table.sent_to_kitchen)
  kitchenNote.value = table.notes || ''
  // Reset discount (table orders carry no discount info)
  discountInput.value = ''
  showDiscountPanel.value = false
  // Restore table as the bill-to customer
  selectedBillTo.value = { id: table.name, name: table.name, room: null, type: 'Table' }
  // Track this draft so re-holding replaces it
  resumedDraftInvoice.value = table.invoice || null
  lastInvoiceName.value = table.invoice || ''
  showOpenTables.value = false
  openTablesGuardResource.reload()
  if (table.settle) settlementMethod.value = 'Cash'
  chargeSuccess.value = `Table ${table.name} loaded — ₦${table.bill.toLocaleString()}`
  setTimeout(() => { chargeSuccess.value = '' }, 3000)
}

function normalizeKitchenSentMap(sent) {
  if (!sent) return {}
  if (!Array.isArray(sent)) return { ...sent }
  return sent.reduce((acc, row) => {
    const code = row.item_code || row.id
    if (code) acc[code] = Number(row.total_qty || row.qty || 0)
    return acc
  }, {})
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

// Persist relevant POS state to localStorage on every change
watch(
  [cart, selectedBillTo, kitchenNote, discountType, discountInput,
   showDiscountPanel, settlementMethod, resumedDraftInvoice, lastInvoiceName, kitchenSentMap],
  savePosState,
  { deep: true }
)
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
