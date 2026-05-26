<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">
    <div
      v-if="showCheckInToast"
      class="fixed top-5 right-5 z-[60] bg-green-600 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg"
    >
      {{ checkInToastMessage }}
    </div>

    <div
      v-if="showPaymentToast"
      class="fixed top-16 right-5 z-[60] bg-emerald-600 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg"
    >
      {{ paymentToastMessage }}
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-10 text-sm text-gray-400 text-center">Loading reservation...</div>
    <div v-else-if="error && !reservation.name" class="bg-white rounded-xl border border-red-200 px-6 py-10 text-sm text-red-500 text-center">{{ error }}</div>

    <template v-else-if="!loading">
      <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">{{ error }}</div>
      <div v-if="splitInvoiceError" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">{{ splitInvoiceError }}</div>

      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <div class="flex items-start justify-between mb-3">
          <div>
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <h2 class="text-xl font-bold text-gray-900">{{ reservation.name }}</h2>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border" :class="statusClass">{{ reservation.status || 'Draft' }}</span>
              <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-500 rounded-full border border-blue-200">{{ reservation.reservation_type || 'Individual' }}</span>
            </div>
            <p class="text-xs text-gray-400">
              Guest: {{ reservation.primary_guest_name || reservation.customer || '—' }} •
              Arrival {{ formatDate(reservation.from_date) }} •
              Departure {{ formatDate(reservation.to_date) }} •
              {{ reservation.number_of_nights || 0 }} nights
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 flex-wrap mt-4">
          <button v-if="reservation.docstatus === 0" :disabled="actionLoading" @click="emit('submit-reservation')"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">Submit Reservation</button>
          <button @click="showPaymentModal = true" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Receive Payment</button>
          <button v-if="!hasAnyCheckedIn" @click="showAdjustModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Adjust Reservation</button>
          <button @click="changeRoomTargetRoom = ''; showChangeRoomModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Change Room</button>
          <button v-if="showTopCreateInvoice"
            :disabled="actionLoading" @click="emit('create-invoice')"
            class="px-4 py-2 text-xs font-semibold text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-40">Create Invoice</button>
          <button
            v-if="showTopSplitBulkInvoice"
            :disabled="actionLoading"
            @click="emit('create-invoice')"
            class="px-4 py-2 text-xs font-semibold text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-40"
          >Create Invoices (Pending Guests)</button>
          <!-- Removed invoice name button: all invoices are now shown in the ledger table below -->
          <button
            v-if="canSingleTopCheckIn"
            :disabled="actionLoading"
            @click="checkIn(singleTopCheckInRoom)"
            class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-40"
          >Check In</button>
          <button
            v-else-if="canTopBulkCheckIn"
            :disabled="actionLoading"
            @click="openBulkCheckInPicker"
            class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-40"
          >Bulk Check In</button>
          <button @click="emit('refresh')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Refresh</button>
          <button v-if="!isCancelled" :disabled="actionLoading" @click="emit('cancel-reservation')" class="px-4 py-2 text-xs font-medium text-red-500 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-40">Cancel Reservation</button>
          <button @click="showPrintModal = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print</button>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0;" class="divide-x divide-gray-100">
         
          <div class="px-6">
            <p class="text-xs text-gray-400 mb-1">Subtotal</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.subtotal) }}</p>
          </div>
          <div class="px-6">
            <p class="text-xs text-gray-400 mb-1">Discount</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.discount_amount) }}</p>
          </div>
           <div class="pr-6">
            <p class="text-xs text-gray-400 mb-1">Grand Total</p>
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(reservation.total_amount) }}</p>
          </div>
          <div class="pl-6">
            <p class="text-xs text-gray-400 mb-1">Paid Amount</p>
            <p class="text-2xl font-bold text-green-600">{{ formatCurrency(paidAmount) }}</p>
          </div>
          <div class="px-6">
            <p class="text-xs text-gray-400 mb-1">Balance Due</p>
            <p class="text-2xl font-bold" :class="computedBalance > 0 ? 'text-red-500' : 'text-gray-900'">{{ formatCurrency(computedBalance) }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-900">Reserved Rooms</h3>
          <button v-if="canTopBulkCheckIn" @click="openBulkCheckInPicker" class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Bulk Check In</button>
        </div>
        <div class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate / Plan</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Guest</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate/Night</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Total</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="rooms.length === 0">
                <td colspan="7" class="px-3 py-4 text-center text-xs text-gray-300">No room rows found.</td>
              </tr>
              <tr v-for="row in rooms" :key="row.name || row.idx" class="border-t border-gray-100">
                <td class="px-3 py-2 text-xs text-gray-700">
                  <button
                    v-if="row.check_in_reference"
                    @click="goCheckInDetail(row)"
                    class="font-semibold text-blue-600 hover:underline"
                  >{{ row.room_number || '—' }}</button>
                  <span v-else>{{ row.room_number || '—' }}</span>
                </td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ row.room_type || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-500 text-right">
                  <span v-if="row.rate_code" class="inline-flex items-center px-1.5 py-0.5 text-xs bg-blue-50 text-blue-600 rounded border border-blue-100">{{ row.rate_code }}</span>
                  <span v-if="row.meal_plan_snapshot" class="ml-1 inline-flex items-center px-1.5 py-0.5 text-xs bg-green-50 text-green-600 rounded border border-green-100">{{ row.meal_plan_snapshot }}</span>
                </td>
                <td class="px-3 py-2 text-xs text-gray-700">
                  <template v-if="isRoomCheckedIn(row) || (reservation.docstatus === 1 && reservation.reservation_type === 'Individual')">
                    <span class="text-xs text-gray-700">{{ row.occupant_name || row.guest_name || reservation.primary_guest_name || '—' }}</span>
                  </template>
                  <GuestSelector
                    v-else
                    v-model="row.occupant_name"
                    :fallback-value="row.guest_name || reservation.primary_guest_name || reservation.customer || ''"
                    v-model:guestId="row.hotel_guest"
                    @selected="onGuestSelected(row, $event)"
                  />
                </td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(row.rate_per_night) }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(row.room_total) }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">
                  <div class="flex flex-col gap-1">
                    <template v-if="isRoomCheckedIn(row)">
                      <button
                        v-if="row.check_in_reference"
                        @click="goCheckOut(row)"
                        class="px-2 py-1 text-xs font-semibold text-white bg-orange-500 rounded hover:bg-orange-600"
                      >Check Out</button>
                      <span
                        v-else
                        class="inline-flex px-2 py-1 text-xs font-semibold text-green-700 bg-green-50 border border-green-200 rounded"
                      >Checked In</span>
                      <button
                        v-if="row.check_in_reference"
                        @click="goCheckInDetail(row)"
                        class="px-2 py-1 text-xs font-semibold text-green-600 bg-green-50 border border-green-100 rounded hover:bg-green-100"
                      >View Check In</button>
                    </template>
                    <button v-else-if="canCheckInReservation" @click="checkIn(row)" class="px-2 py-1 text-xs font-semibold text-white bg-green-500 rounded hover:bg-green-600">Check In</button>
                    <span
                      v-else-if="isCancelled"
                      class="inline-flex px-2 py-1 text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded"
                    >Cancelled</span>
                    <!-- Per-room invoice for Group Split billing -->
                    <template v-if="isSplitGroup">
                      <span
                        v-if="isRowInvoiced(row)"
                        class="inline-flex px-2 py-1 text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200 rounded"
                        :title="row.split_invoice || 'Invoice created'"
                      >Invoiced</span>
                      <button
                        v-else
                        :disabled="splitInvoiceLoading === row.name"
                        @click="createSplitInvoice(row)"
                        class="px-2 py-1 text-xs font-semibold text-white bg-purple-600 rounded hover:bg-purple-700 disabled:opacity-50"
                      >{{ splitInvoiceLoading === row.name ? 'Creating…' : 'Create Invoice' }}</button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Reservation Details Section -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Reservation Details</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;" class="text-xs">
          <div>
            <p class="text-gray-400 mb-1">Source Channel</p>
            <p class="font-semibold text-gray-900">{{ reservation.source_channel || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-400 mb-1">Guest Phone</p>
            <p class="font-semibold text-gray-900">{{ reservation.primary_guest_phone || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-400 mb-1">Guest Email</p>
            <p class="font-semibold text-gray-900">{{ reservation.primary_guest_email || '—' }}</p>
          </div>
          <div v-if="reservation.reservation_type === 'Corporate'">
            <p class="text-gray-400 mb-1">Corporate Account</p>
            <p class="font-semibold text-gray-900">{{ reservation.customer || reservation.corporate_guest || '—' }}</p>
          </div>
          <div v-if="reservation.reservation_type === 'Group'">
            <p class="text-gray-400 mb-1">Group Name</p>
            <p class="font-semibold text-gray-900">{{ reservation.group_name || '—' }}</p>
          </div>
          <div v-if="reservation.reservation_type === 'Group'">
            <p class="text-gray-400 mb-1">Billing Mode</p>
            <p class="font-semibold text-gray-900">{{ reservation.group_billing_mode || '—' }}</p>
          </div>
          <div v-if="reservation.reservation_type === 'Group' && reservation.group_master_customer">
            <p class="text-gray-400 mb-1">Master Payer</p>
            <p class="font-semibold text-gray-900">{{ reservation.group_master_customer }}</p>
          </div>
          <div>
            <p class="text-gray-400 mb-1">Booking Date</p>
            <p class="font-semibold text-gray-900">{{ formatDate(reservation.creation) }}</p>
          </div>
          <div v-if="reservation.special_requests">
            <p class="text-gray-400 mb-1">Special Requests</p>
            <p class="font-semibold text-gray-900">{{ reservation.special_requests }}</p>
          </div>
          <div v-if="reservation.internal_notes || reservation.notes">
            <p class="text-gray-400 mb-1">Notes</p>
            <p class="font-semibold text-gray-900">{{ reservation.internal_notes || reservation.notes }}</p>
          </div>
        </div>
      </div>

      <!-- Split Billing Notice for Group Reservations -->
      <div v-if="reservation.reservation_type === 'Group' && reservation.group_billing_mode === 'Split'"
        class="bg-amber-50 border border-amber-200 rounded-xl px-6 py-4">
        <p class="text-xs font-bold text-amber-700 mb-1">Split Billing — Group Reservation</p>
        <p class="text-xs text-amber-600">Each room in this group reservation requires its own individual invoice. Use the "Create Invoice" action per room row to generate separate invoices. A single group invoice is not applicable for split billing.</p>
      </div>

      <!-- Group Room Blocks -->
      <div v-if="reservation.reservation_type === 'Group' && reservation.room_blocks && reservation.room_blocks.length > 0"
        class="bg-white rounded-xl border border-amber-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-3">Room Blocks</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-xs text-gray-500">
          <div>Group: <span class="font-semibold text-gray-900">{{ reservation.group_name || '—' }}</span></div>
          <div>Billing: <span class="font-semibold text-gray-900">{{ reservation.group_billing_mode || '—' }}</span></div>
          <div v-if="reservation.group_master_customer">Master Payer: <span class="font-semibold text-gray-900">{{ reservation.group_master_customer }}</span></div>
        </div>
        <div class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Blocked</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Picked Up</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Remaining</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate Code</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="block in reservation.room_blocks" :key="block.name || block.idx" class="border-t border-gray-100">
                <td class="px-3 py-2 text-xs text-gray-700">{{ block.room_type }}</td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ block.quantity }}</td>
                <td class="px-3 py-2 text-xs text-green-700 font-semibold">{{ block.picked_up || 0 }}</td>
                <td class="px-3 py-2 text-xs" :class="(block.remaining || 0) > 0 ? 'text-amber-700 font-semibold' : 'text-gray-400'">{{ block.remaining || 0 }}</td>
                <td class="px-3 py-2 text-xs text-gray-500">{{ block.rate_code || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- OTA Details -->
      <div v-if="reservation.reservation_type === 'OTA'" class="bg-white rounded-xl border border-purple-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-3">OTA Details</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-500">
          <div>Channel: <span class="font-semibold text-gray-900">{{ reservation.ota_channel || '—' }}</span></div>
          <div>Collection: <span class="font-semibold text-gray-900">{{ reservation.ota_collection_model || '—' }}</span></div>
          <div v-if="reservation.ota_commission_amount">Commission: <span class="font-semibold text-gray-900">{{ formatCurrency(reservation.ota_commission_amount) }}</span></div>
          <div v-if="reservation.ota_virtual_card_ref">Virtual Card: <span class="font-semibold text-gray-900">{{ reservation.ota_virtual_card_ref }}</span></div>
        </div>
      </div>

      <!-- House Use / Complimentary Details -->
      <div v-if="reservation.reservation_type === 'House Use' || reservation.reservation_type === 'Complimentary'"
        class="bg-white rounded-xl border border-green-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-3">{{ reservation.reservation_type }} Details</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-500">
          <div class="md:col-span-2">Reason: <span class="font-semibold text-gray-900">{{ reservation.comp_reason || '—' }}</span></div>
          <div>Cost Centre: <span class="font-semibold text-gray-900">{{ reservation.internal_cost_center || '—' }}</span></div>
          <div v-if="reservation.theoretical_room_revenue">Theoretical Revenue: <span class="font-semibold text-amber-700">{{ formatCurrency(reservation.theoretical_room_revenue) }}</span></div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Paid Amount</h3>
        <div class="flex items-center justify-between mb-3 rounded-lg bg-green-50 border border-green-100 px-3 py-2">
          <span class="text-xs font-semibold text-green-700">Total Paid</span>
          <span class="text-sm font-bold text-green-700">{{ formatCurrency(paidAmount) }}</span>
        </div>
        <div v-if="paymentLedger.length > 0" class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Payment Entry</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Date</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Mode</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Reference</th>
                <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="payment in paymentLedger" :key="payment.name" class="border-t border-gray-100">
                <td class="px-3 py-2 text-xs text-gray-800 font-medium">{{ payment.name || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-500">{{ formatDate(payment.posting_date) }}</td>
                <td class="px-3 py-2 text-xs text-gray-600">{{ payment.mode_of_payment || '—' }}</td>
                <td class="px-3 py-2 text-xs text-gray-500">{{ payment.reference_no || '—' }}</td>
                <td class="px-3 py-2 text-xs text-right font-semibold text-gray-900">{{ formatCurrency(getPaymentValue(payment)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-sm text-gray-400">No linked payments</div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Invoice Ledger</h3>
        <div v-if="invoiceLedger.length > 0" class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Invoice</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Date</th>
                <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Amount</th>
                <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Outstanding</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invoice in invoiceLedger" :key="invoice.name" class="border-t border-gray-100">
                <td class="px-3 py-2 text-xs text-gray-800 font-medium">{{ invoice.name || '—' }}</td>
                <td class="px-3 py-2 text-xs" :class="invoice.is_return ? 'text-teal-600 font-semibold' : 'text-gray-600'">
                  {{ invoice.invoice_type || (invoice.is_return ? 'Credit Note' : 'Invoice') }}
                </td>
                <td class="px-3 py-2 text-xs text-gray-500">{{ formatDate(invoice.posting_date) }}</td>
                <td class="px-3 py-2 text-xs text-right font-semibold" :class="invoice.is_return ? 'text-teal-600' : 'text-gray-900'">
                  {{ invoice.is_return ? '- ' : '' }}{{ formatCurrency(Math.abs(Number(invoice.grand_total || 0))) }}
                </td>
                <td class="px-3 py-2 text-xs text-right" :class="(Number(invoice.outstanding_amount || 0) > 0 && !invoice.is_return) ? 'text-red-500 font-semibold' : 'text-gray-500'">
                  {{ formatCurrency(invoice.outstanding_amount || 0) }}
                </td>
                <td class="px-3 py-2 text-xs text-gray-600">{{ invoice.status || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-sm text-gray-400">No linked invoices</div>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="showAdjustModal" class="fixed inset-0 z-50 overflow-y-auto" style="background:rgba(0,0,0,0.55);">
        <div class="min-h-screen flex items-start justify-center py-8 px-4">
          <div class="bg-white rounded-2xl shadow-2xl w-full" style="max-width:900px;">
            <StayAdjustment 
              :reservation="reservation" 
              @close="showAdjustModal = false" 
              @done="handleModalDone" 
              @apply-discount="applyDiscount" 
            />
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showChangeRoomModal" class="fixed inset-0 z-50 overflow-y-auto" style="background:rgba(0,0,0,0.55);">
        <div class="min-h-screen flex items-start justify-center py-8 px-4">
          <div class="bg-white rounded-2xl shadow-2xl w-full" style="max-width:900px;">
            <ChangeRoom :reservation="reservation" :preselected-room="changeRoomTargetRoom" @close="showChangeRoomModal = false" @done="handleModalDone" />
          </div>
        </div>
      </div>
    </Teleport>

    <ReceivePaymentModal
      v-if="showPaymentModal"
      :reservation="reservation"
      @close="showPaymentModal = false"
      @done="handlePaymentDone"
    />

    <PrintReservationModal
      v-if="showPrintModal"
      :reservation="reservation"
      @close="showPrintModal = false"
      @done="handleModalDone"
    />

    <Teleport to="body">
      <div
        v-if="showBulkCheckInPicker"
        class="fixed inset-0 z-50 flex items-center justify-center"
        style="background:rgba(0,0,0,0.55);"
        @click.self="closeBulkCheckInPicker"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full mx-4" style="max-width:640px;">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Bulk Check In</h3>
              <p class="text-xs text-gray-400 mt-0.5">Select rooms to check in. All pending rooms are pre-selected.</p>
            </div>
            <button @click="closeBulkCheckInPicker" class="text-xs text-gray-400 hover:text-gray-600">Close</button>
          </div>

          <div class="px-6 py-4 max-h-[320px] overflow-y-auto space-y-2">
            <label
              v-for="room in pendingRooms"
              :key="room.name || room.idx"
              class="flex items-start gap-3 rounded-lg border border-gray-100 px-3 py-2 hover:bg-gray-50"
            >
              <input
                :checked="selectedBulkRoomNames.includes(room.name)"
                type="checkbox"
                class="mt-0.5"
                @change="toggleBulkRoomSelection(room.name, $event.target.checked)"
              />
              <div>
                <p class="text-xs font-semibold text-gray-900">{{ room.room_number || 'Unassigned Room' }} • {{ room.room_type || '—' }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ room.occupant_name || room.guest_name || reservation.primary_guest_name || 'No occupant selected' }}</p>
              </div>
            </label>
          </div>

          <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-3">
            <p class="text-xs text-gray-500">Selected: {{ selectedBulkRoomNames.length }} / {{ pendingRooms.length }}</p>
            <div class="flex items-center gap-2">
              <button @click="closeBulkCheckInPicker" class="px-3 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
              <button
                :disabled="selectedBulkRoomNames.length === 0 || actionLoading"
                @click="bulkCheckInSelected"
                class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-40"
              >Check In Selected</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import StayAdjustment from '@/components/reservations/StayAdjustment.vue'
import ChangeRoom from '@/components/reservations/ChangeRoom.vue'
import ReceivePaymentModal from '@/components/reservations/ReceivePaymentModal.vue'
import PrintReservationModal from '@/components/reservations/PrintReservationModal.vue'
import GuestSelector from '@/components/reservations/GuestSelector.vue'
import { callMethod } from '@/lib/api'

const router = useRouter()

const props = defineProps({
  reservation: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  actionLoading: { type: Boolean, default: false },
})

const emit = defineEmits([
  'refresh',
  'open-payments',
  'check-in',
  'check-in-room',
  'bulk-check-in',
  'update-room',
  'update-occupant',
  'cancel-reservation',
  'create-invoice',
  'submit-reservation',
])

const showAdjustModal = ref(false)
const showChangeRoomModal = ref(false)
const changeRoomTargetRoom = ref('')
const showPaymentModal = ref(false)
const showPrintModal = ref(false)
const printFormat = ref('summary')
const showCheckInToast = ref(false)
const checkInToastMessage = ref('')
const showPaymentToast = ref(false)
const paymentToastMessage = ref('')
const showBulkCheckInPicker = ref(false)
const selectedBulkRoomNames = ref([])

function handleModalDone() {
  showAdjustModal.value = false
  showChangeRoomModal.value = false
  showPaymentModal.value = false
  showPrintModal.value = false
  emit('refresh')
}

function handlePaymentDone() {
  handleModalDone()
  paymentToastMessage.value = 'Payment recorded successfully.'
  showPaymentToast.value = true
  setTimeout(() => {
    showPaymentToast.value = false
  }, 3200)
}

const rooms = computed(() => props.reservation?.rooms || [])
const pendingRooms = computed(() => rooms.value.filter((row) => !isRoomCheckedIn(row)))
const hasAnyCheckedIn = computed(() => rooms.value.some((row) => isRoomCheckedIn(row)))
const isCancelled = computed(() => Number(props.reservation?.docstatus || 0) === 2 || String(props.reservation?.status || props.reservation?.reservation_status || '').toLowerCase() === 'cancelled')
const canCheckInReservation = computed(() => Number(props.reservation?.docstatus || 0) === 1 && !isCancelled.value && pendingRooms.value.length > 0)
const canSingleTopCheckIn = computed(() => canCheckInReservation.value && pendingRooms.value.length === 1)
const canTopBulkCheckIn = computed(() => canCheckInReservation.value && pendingRooms.value.length > 1)
const singleTopCheckInRoom = computed(() => (canSingleTopCheckIn.value ? pendingRooms.value[0] : null))
const reservationType = computed(() => String(props.reservation?.reservation_type || '').trim().toLowerCase())
const groupBillingMode = computed(() => String(props.reservation?.group_billing_mode || '').trim().toLowerCase())
const isSplitGroup = computed(() => reservationType.value === 'group' && groupBillingMode.value.startsWith('split'))
const invoiceLedger = computed(() => {
  const reservationInvoices = Array.isArray(props.reservation?.reservation_invoices)
    ? props.reservation.reservation_invoices
    : []
  const fallbackInvoices = Array.isArray(props.reservation?.linked_invoices)
    ? props.reservation.linked_invoices
    : []
  return reservationInvoices.length ? reservationInvoices : fallbackInvoices
})

const splitInvoiceLedgerCount = computed(() => invoiceLedger.value
  .filter((invoice) => Number(invoice?.is_return || 0) === 0)
  .length)

const allSplitRoomsInvoicedByLedger = computed(() => {
  if (!isSplitGroup.value || rooms.value.length === 0) return false
  return splitInvoiceLedgerCount.value >= rooms.value.length
})

const invoicedRowNames = reactive(new Set())
function isRowInvoiced(row) {
  if (allSplitRoomsInvoicedByLedger.value) return true
  return Boolean(row?.split_invoice || row?.sales_invoice) || invoicedRowNames.has(row?.name)
}
const splitInvoicePendingRooms = computed(() => (isSplitGroup.value ? rooms.value.filter((row) => !isRowInvoiced(row)) : []))
const showTopCreateInvoice = computed(() => !isSplitGroup.value && !props.reservation?.sales_invoice && Number(props.reservation?.docstatus || 0) === 1)
const showTopSplitBulkInvoice = computed(() => isSplitGroup.value && Number(props.reservation?.docstatus || 0) === 1 && splitInvoicePendingRooms.value.length > 0)

const splitInvoiceLoading = ref(null)
const splitInvoiceError = ref('')

async function createSplitInvoice(row) {
  if (!row?.name || row?.split_invoice || splitInvoiceLoading.value) return
  splitInvoiceLoading.value = row.name
  splitInvoiceError.value = ''
  try {
    const result = await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.create_invoice_for_reservation_room',
      { reservation_name: props.reservation.name, room_row_name: row.name },
    )
    row.split_invoice = result?.sales_invoice || 'created'
    invoicedRowNames.add(row.name)
    emit('refresh')
  } catch (e) {
    splitInvoiceError.value = String(e?.message || 'Failed to create invoice.')
  } finally {
    splitInvoiceLoading.value = null
  }
}

function getPaymentValue(payment) {
  return Number(payment?.amount ?? payment?.paid_amount ?? payment?.allocated_amount ?? 0)
}

const paidAmount = computed(() => {
  const entries = paymentLedger.value
  const entryTotal = entries.reduce((sum, payment) => sum + getPaymentValue(payment), 0)
  return entryTotal || Number(props.reservation?.paid_amount || 0)
})

const paymentLedger = computed(() => {
  const reservationPayments = Array.isArray(props.reservation?.reservation_payments)
    ? props.reservation.reservation_payments
    : []
  const fallbackPayments = Array.isArray(props.reservation?.payment_entries)
    ? props.reservation.payment_entries
    : []
  return reservationPayments.length ? reservationPayments : fallbackPayments
})

const computedBalance = computed(() => {
  const explicitBalance = Number(props.reservation?.balance)
  if (Number.isFinite(explicitBalance)) return Math.max(0, explicitBalance)

  const totalAmount = Number(props.reservation?.total_amount || props.reservation?.net_total || 0)
  return Math.max(0, totalAmount - paidAmount.value)
})

const statusClass = computed(() => {
  const status = String(props.reservation?.status || '').toLowerCase()
  if (status === 'confirmed') return 'bg-yellow-50 text-yellow-700 border-yellow-200'
  if (status === 'checked in') return 'bg-green-50 text-green-700 border-green-200'
  if (status === 'cancelled') return 'bg-red-50 text-red-700 border-red-200'
  return 'bg-gray-50 text-gray-700 border-gray-200'
})

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦0.00'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function updateRoom(row) {
  // Logic to update room and recalculate rate
  emit('update-room', row);
}

function updateOccupant(row) {
  emit('update-occupant', { row })
}

function onGuestSelected(row, guest) {
  row.occupant_name = guest.hotel_guest_name
  row.guest_name = guest.hotel_guest_name
  row.hotel_guest = guest.name
  emit('update-occupant', { row, guest })
}

function isRoomCheckedIn(row) {
  if (!row) return false
  return Boolean(row.check_in_reference) || String(row.status || '').toLowerCase() === 'checked in'
}

function goCheckOut(row) {
  if (!row?.check_in_reference) return
  router.push('/check-outs/' + row.check_in_reference)
}

function goCheckInDetail(row) {
  if (!row?.check_in_reference) return
  router.push({ name: 'CheckInDetail', params: { id: row.check_in_reference } })
}

async function checkIn(row) {
  if (!row || !row.name || isRoomCheckedIn(row)) return
  if (typeof window !== 'undefined') {
    const confirmed = window.confirm(`Check in ${row?.occupant_name || row?.guest_name || row?.room_number || 'this guest'} now?`)
    if (!confirmed) return
  }
  const roomLabel = row?.room_number || row?.name || 'selected room'
  showCheckInToast.value = true
  checkInToastMessage.value = `Checking in ${roomLabel}...`
  try {
    const result = await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.check_in_reservation_room',
      { reservation_name: props.reservation.name, room_row_name: row.name }
    )
    // Apply check-in reference immediately so the button updates before refresh
    if (result?.check_in_reference) {
      row.check_in_reference = result.check_in_reference
      row.status = 'Checked In'
    }
    checkInToastMessage.value = result?.message || 'Check-in complete.'
    setTimeout(() => { showCheckInToast.value = false }, 3500)
    emit('refresh')
  } catch (e) {
    checkInToastMessage.value = e?.message || 'Check-in failed.'
    setTimeout(() => { showCheckInToast.value = false }, 3500)
  }
}

function openBulkCheckInPicker() {
  if (!canTopBulkCheckIn.value) return
  selectedBulkRoomNames.value = pendingRooms.value
    .map((row) => row?.name)
    .filter(Boolean)
  showBulkCheckInPicker.value = true
}

function closeBulkCheckInPicker() {
  showBulkCheckInPicker.value = false
}

function toggleBulkRoomSelection(roomName, checked) {
  if (!roomName) return
  if (checked) {
    if (!selectedBulkRoomNames.value.includes(roomName)) {
      selectedBulkRoomNames.value = [...selectedBulkRoomNames.value, roomName]
    }
    return
  }
  selectedBulkRoomNames.value = selectedBulkRoomNames.value.filter((name) => name !== roomName)
}

async function bulkCheckInSelected() {
  if (!canTopBulkCheckIn.value || selectedBulkRoomNames.value.length === 0) return
  if (typeof window !== 'undefined') {
    const confirmed = window.confirm(`Check in ${selectedBulkRoomNames.value.length} selected room(s) now?`)
    if (!confirmed) return
  }
  showCheckInToast.value = true
  checkInToastMessage.value = 'Processing selected room check-ins...'
  try {
    const rowsToCheckIn = pendingRooms.value.filter((row) => selectedBulkRoomNames.value.includes(row.name))
    const results = await Promise.allSettled(
      rowsToCheckIn.map((row) => callMethod(
        'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.check_in_reservation_room',
        { reservation_name: props.reservation.name, room_row_name: row.name },
      ))
    )
    const successCount = results.filter((entry) => entry.status === 'fulfilled').length
    const failedCount = results.length - successCount
    checkInToastMessage.value = failedCount > 0
      ? `Checked in ${successCount} room(s); ${failedCount} failed.`
      : `Checked in ${successCount} room(s) successfully.`
    closeBulkCheckInPicker()
    setTimeout(() => { showCheckInToast.value = false }, 3500)
    emit('refresh')
  } catch (e) {
    checkInToastMessage.value = e?.message || 'Bulk check-in failed.'
    setTimeout(() => { showCheckInToast.value = false }, 3500)
  }
}

function applyDiscount(discount) {
  // Logic to apply discount to the reservation
  props.reservation.discount_amount = discount;
  props.reservation.total_amount = props.reservation.subtotal - discount;
  emit('refresh');
}

function printReservation() {
  // Logic to handle print based on selected format
  const printContent = printFormat.value === 'summary' ? generateSummary() : generateDetailed();
  const printWindow = window.open('', '_blank');
  printWindow.document.write(`
    <html>
      <head>
        <title>Print Reservation</title>
      </head>
      <body>
        <h1>${props.reservation.name}</h1>
        ${printContent}
      </body>
    </html>
  `);
  printWindow.document.close();
  printWindow.print();
}

function generateSummary() {
  return `<p>Reservation Summary for ${props.reservation.name}</p>`;
}

function generateDetailed() {
  return `<p>Detailed Reservation Information for ${props.reservation.name}</p>`;
}
</script>
