<template>
  <div class="space-y-5">

    <!-- Loading / Error States -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl px-6 py-10 text-center">
      <p class="text-sm font-semibold text-red-500 mb-2">{{ loadError }}</p>
      <button @click="$router.back()" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">← Back</button>
    </div>

    <template v-if="!loading && !loadError">
    <!-- Guest Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-start justify-between mb-2">
        <h2 class="text-2xl font-bold text-gray-900">{{ checkIn.guest || '—' }}</h2>
        <button @click="$router.back()"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          ← Back
        </button>
      </div>
      <div class="flex items-center gap-2 flex-wrap mb-2">
        <span class="px-2.5 py-1 text-xs font-semibold bg-green-50 text-green-600 rounded-full border border-green-200">
          {{ checkIn.status || 'Checked In' }}
        </span>
        <span class="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-600 rounded-full border border-blue-200">
          Room {{ checkIn.room_number || '—' }}
        </span>
        <span v-if="grandNetOutstanding > 0"
          class="px-2.5 py-1 text-xs font-semibold bg-orange-50 text-orange-600 rounded-full border border-orange-200">
          Balance {{ formatCurrency(grandNetOutstanding) }}
        </span>
        <span v-else-if="grandNetOutstanding < 0"
          class="px-2.5 py-1 text-xs font-semibold bg-teal-50 text-teal-600 rounded-full border border-teal-200">
          Credit {{ formatCurrency(Math.abs(grandNetOutstanding)) }}
        </span>
      </div>
      <p class="text-xs text-gray-400">
        {{ checkIn.room_type }} •
        {{ checkIn.reservation_source || 'Walk-in' }} •
        Check-in {{ formatDateTime(checkIn.check_in_datetime) }} •
        Check-out {{ formatDateTime(checkIn.expected_check_out_datetime) }} •
        {{ checkIn.number_of_nights }} nights
      </p>
    </div>

    <!-- Action Buttons -->
    <div v-if="checkIn.status === 'Checked In'" class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center gap-2 flex-wrap">
      <button @click="showRoomTransfer = true"
        class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Room Transfer
      </button>
      <div class="relative create-menu-container">
        <button @click="showCreateMenu = !showCreateMenu"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
          Create ▾
        </button>
        <div v-if="showCreateMenu"
          class="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 py-1 min-w-32">
          <button @click="showDiscount = true; showCreateMenu = false"
            class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Discount</button>
          <button @click="showRefund = true; showCreateMenu = false"
            class="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50">Refund</button>
        </div>
      </div>
      <button @click="showBillTransfer = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Bill Transfer
      </button>
      <button @click="showStayAdjustment = true" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Adjust Stay
      </button>
      <button @click="showPayment = true" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
        Receive Payment
      </button>
      <button @click="printFolio"
        class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
        Print
      </button>
      <button 
      class="px-4 py-2 text-xs font-semibold text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
      @click="$router.push('/check-outs/' + checkIn.name)">
      Check Out
    </button>
      <button @click="$router.back()"
        class="px-4 py-2 text-xs text-gray-400 hover:text-gray-600 transition-colors">
        Cancel
      </button>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-xl border border-gray-200 px-6">
      <div class="flex items-center gap-4 border-b border-gray-100">
        <button v-for="tab in ['Details', 'Transfer History']" :key="tab"
          @click="activeTab = tab"
          class="py-3.5 text-xs font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === tab ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'">
          {{ tab }}
        </button>
      </div>
    </div>

    <!-- Details Tab -->
    <div v-if="activeTab === 'Details'" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- Left: Guest and Stay Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <p class="text-xs text-gray-400 mb-1.5">Reservation</p>
        <div class="px-3 py-2.5 text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-lg mb-5">
          {{ checkIn.reservation || 'Walk-in' }}
        </div>

        <h3 class="text-sm font-bold text-gray-900 mb-4">Guest and Stay Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <p class="text-xs text-gray-400 mb-1">Guest</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.guest || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Check-in Time</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatDateTime(checkIn.check_in_datetime) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">ID Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.id_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Number of Nights</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.number_of_nights || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Guest Phone Number</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.contact_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Expected Check-out</p>
            <div class="px-3 py-2.5 text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg"
              :class="isOverdue ? 'text-red-500' : 'text-gray-700'">
              {{ formatDateTime(checkIn.expected_check_out_datetime) }}
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Room {{ checkIn.room_number || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Room Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.room_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Market Place</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.reservation_source || 'Walk in' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Status</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-green-600 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.status || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Rate Amount</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ formatCurrency(checkIn.rate_amount) }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Discount Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ checkIn.discount_type || '—' }}</div>
          </div>
          <div style="grid-column:span 2;" v-if="preferenceList.length">
            <p class="text-xs text-gray-400 mb-1">Room Preferences</p>
            <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg flex items-center gap-2 flex-wrap">
              <span
                v-for="pref in preferenceList"
                :key="pref"
                class="px-2.5 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full"
              >
                {{ pref }}
              </span>
            </div>
          </div>
          <div style="grid-column:span 2;" v-if="housekeepingNotes">
            <p class="text-xs text-gray-400 mb-1">Housekeeping Notes</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg whitespace-pre-line">{{ housekeepingNotes }}</div>
          </div>
          <div style="grid-column:span 2;">
            <p class="text-xs text-gray-400 mb-1">Total Charges</p>
            <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ formatCurrency(grandCharges) }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Bills and Payments -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-900">Bills and Payments</h3>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden mb-5">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Invoice</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Posting Date</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Grand Total</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="5" class="py-6 text-center">
                  <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                </td>
              </tr>
              <tr v-for="inv in invoices" :key="inv.invoice"
                class="border-b border-gray-50 last:border-0 transition-colors cursor-pointer"
                :class="inv.is_return ? 'bg-teal-50 hover:bg-teal-100' : 'hover:bg-gray-50'"
                @click="openInvoiceDetail(inv)">
                <td class="px-4 py-3 text-xs text-blue-600 font-medium underline-offset-2 hover:underline">{{ inv.invoice || '—' }}</td>
                <td class="px-3 py-3 text-xs" :class="inv.is_return ? 'text-teal-600 font-medium' : 'text-gray-500'">
                  {{ inv.is_return ? 'Credit Note' : formatInvoiceType(inv.invoice_type) }}
                </td>
                <td class="px-3 py-3 text-xs text-gray-500">{{ formatDate(inv.posting_date || checkIn.check_in_datetime) }}</td>
                <td class="px-4 py-3 text-xs text-right" :class="inv.is_return ? 'text-teal-600 font-semibold' : 'text-gray-700'">
                  {{ inv.is_return ? '− ' + formatCurrency(inv.amount) : formatCurrency(inv.amount) }}
                </td>
                <td class="px-4 py-3 text-xs text-right font-semibold"
                  :class="inv.is_return ? 'text-teal-400' : (inv.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-gray-400'">
                  {{ inv.is_return ? (inv.outstanding_amount > 0 ? formatCurrency(inv.outstanding_amount) : '—') : formatCurrency(inv.outstanding_amount) }}
                </td>
              </tr>
              <tr v-if="!loading && invoices.length === 0">
                <td colspan="5" class="py-8 text-center text-xs text-gray-400">No invoices found</td>
              </tr>
            </tbody>
            <tfoot v-if="invoices.length > 0">
              <tr class="border-t border-gray-200">
                <td colspan="3" class="px-4 py-3 text-xs font-bold text-gray-900">Invoice Total</td>
                <td class="px-4 py-3 text-xs font-bold text-right text-gray-900">{{ formatCurrency(invoiceTotal) }}</td>
                <td class="px-4 py-3 text-xs font-bold text-right"
                  :class="outstandingTotal > 0 ? 'text-red-500' : outstandingTotal < 0 ? 'text-teal-600' : 'text-gray-400'">{{ formatCurrency(Math.abs(outstandingTotal)) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Acquired Bills (Transferred In) -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden mb-5">
          <div class="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h4 class="text-xs font-bold text-gray-700">Acquired Bills <span class="text-gray-400 font-normal">(transferred in)</span></h4>
          </div>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-2.5">Transfer Ref</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">From Guest</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Source Invoice</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Date</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Status</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Amount</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Outstanding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="acquiredBills.length === 0">
                <td colspan="7" class="py-6 text-center text-xs text-gray-400">No acquired bills</td>
              </tr>
              <tr v-for="bill in acquiredBills" :key="bill.name"
                class="border-b border-gray-50 last:border-0">
                <td class="px-4 py-2.5 text-xs font-medium text-blue-600">{{ bill.name }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-700">{{ bill.from_guest || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-600">{{ bill.source_invoice || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ formatDate(bill.transfer_date) }}</td>
                <td class="px-3 py-2.5">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded-full"
                    :class="bill.status === 'Approved' ? 'bg-green-100 text-green-600' : bill.status === 'Pending Approval' ? 'bg-yellow-100 text-yellow-600' : 'bg-gray-100 text-gray-500'">
                    {{ bill.status }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-xs text-right text-gray-700">{{ formatCurrency(bill.total_amount) }}</td>
                <td class="px-4 py-2.5 text-xs text-right font-semibold"
                  :class="bill.status === 'Approved' ? ((bill.outstanding_amount || 0) > 0 ? 'text-red-500' : 'text-gray-400') : 'text-gray-300'">
                  {{ bill.status === 'Approved' ? formatCurrency(bill.outstanding_amount) : '—' }}
                </td>
              </tr>
            </tbody>
            <tfoot v-if="acquiredBills.length > 0">
              <tr class="border-t border-gray-200">
                <td colspan="5" class="px-4 py-2.5 text-xs font-bold text-gray-900">Total Acquired</td>
                <td class="px-4 py-2.5 text-xs font-bold text-right text-gray-900">
                  {{ formatCurrency(acquiredTotal) }}
                </td>
                <td class="px-4 py-2.5 text-xs font-bold text-right text-red-500">
                  {{ formatCurrency(acquiredOutstanding) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Payment / Refund Entries -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden mb-5">
          <div class="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h4 class="text-xs font-bold text-gray-700">Payment / Refund Entries</h4>
          </div>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-2.5">Payment ID</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Status</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Mode</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Date</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="payments.length === 0">
                <td colspan="6" class="py-6 text-center text-xs text-gray-400">No payment or refund entries</td>
              </tr>
              <tr v-for="pmt in payments" :key="pmt.payment_id"
                class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors cursor-pointer"
                @click="openPaymentDetail(pmt)">
                <td class="px-4 py-2.5 text-xs font-medium text-blue-600 underline-offset-2 hover:underline">{{ pmt.payment_id }}</td>
                <td class="px-3 py-2.5">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded-full"
                    :class="pmt.payment_type === 'Receive' ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'">
                    {{ pmt.payment_type === 'Receive' ? 'Receipt' : (pmt.payment_type || '—') }}
                  </span>
                </td>
                <td class="px-3 py-2.5">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded-full"
                    :class="pmt.docstatus === 1 ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'">
                    {{ pmt.docstatus === 1 ? 'Submitted' : 'Draft' }}
                  </span>
                </td>
                <td class="px-3 py-2.5 text-xs text-gray-600">{{ pmt.mode_of_payment || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ formatDate(pmt.posting_date) }}</td>
                <td class="px-4 py-2.5 text-xs text-right font-semibold"
                  :class="pmt.payment_type === 'Receive' ? 'text-green-600' : 'text-orange-500'">
                  {{ formatCurrency(pmt.paid_amount) }}
                </td>
              </tr>
            </tbody>
            <tfoot v-if="payments.length > 0">
              <tr class="border-t border-gray-200">
                <td colspan="5" class="px-4 py-2.5 text-xs font-bold text-gray-900">Total Received</td>
                <td class="px-4 py-2.5 text-xs font-bold text-right text-green-600">
                  {{ formatCurrency(totalPaid) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Billing Summary</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Gross Charges</span>
              <span class="text-xs text-gray-700">{{ formatCurrency(grandCharges) }}</span>
            </div>
            <div v-if="grandCredits > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Credits / Returns</span>
              <span class="text-xs text-teal-600">− {{ formatCurrency(grandCredits) }}</span>
            </div>
            <div v-if="acquiredTotal > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Acquired Bills</span>
              <span class="text-xs text-gray-700">{{ formatCurrency(acquiredTotal) }}</span>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-gray-200">
              <span class="text-xs font-semibold text-gray-700">Net Bill</span>
              <span class="text-xs font-bold text-gray-900">{{ formatCurrency(grandNetBill) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700">Total Received</span>
              <span class="text-xs font-bold text-green-600">{{ formatCurrency(totalPaid) }}</span>
            </div>
            <div v-if="totalRefunded > 0" class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700">Total Refunds</span>
              <span class="text-xs font-bold text-orange-500">− {{ formatCurrency(totalRefunded) }}</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-200">
              <span class="text-xs font-bold text-gray-900">Outstanding</span>
              <span class="text-xs font-bold"
                :class="grandNetOutstanding > 0 ? 'text-red-500' : grandNetOutstanding < 0 ? 'text-teal-600' : 'text-green-500'">
                {{ grandNetOutstanding < 0 ? '− ' + formatCurrency(Math.abs(grandNetOutstanding)) : formatCurrency(grandNetOutstanding) }}
              </span>
            </div>
            <div class="flex items-center justify-between pt-1">
              <span class="text-xs text-gray-500">Payment Status</span>
              <span class="text-xs font-semibold"
                :class="grandNetOutstanding > 0 ? 'text-orange-500' : grandNetOutstanding < 0 ? 'text-teal-600' : 'text-green-600'">
                {{ grandNetOutstanding > 0 ? 'Payment Pending' : grandNetOutstanding < 0 ? 'Credit Balance' : 'Fully Paid' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transfer History Tab -->
    <div v-if="activeTab === 'Transfer History'"
      class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Transfer History</h3>
      </div>
      <div v-if="!checkIn.transfer_history || checkIn.transfer_history.length === 0" class="px-6 py-16 text-center">
        <p class="text-sm text-gray-400">No transfer history available</p>
      </div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">From Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">To Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Reason</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Transferred By</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(transfer, idx) in checkIn.transfer_history" :key="idx"
            class="border-b border-gray-50 last:border-0">
            <td class="px-5 py-3 text-xs text-gray-700">{{ formatDateTime(transfer.date || transfer.creation) }}</td>
            <td class="px-4 py-3 text-xs text-gray-700">{{ transfer.from_room || '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-700">{{ transfer.to_room || '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ transfer.reason || transfer.note || '—' }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ transfer.transferred_by || transfer.owner || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modals -->
    <RoomTransferModal v-if="showRoomTransfer" :checkIn="checkIn" @close="showRoomTransfer = false" @done="onActionDone" />
    <StayAdjustmentModal v-if="showStayAdjustment" :checkIn="checkIn" @close="showStayAdjustment = false" @done="onActionDone" />
    <RefundRequestModal v-if="showRefund" :checkIn="checkIn" @close="showRefund = false" @done="onActionDone" />
    <BillTransferModal v-if="showBillTransfer" :checkIn="checkIn" @close="showBillTransfer = false" @done="onActionDone" />
    <ReceivePaymentModal v-if="showPayment" :checkIn="checkIn" @close="showPayment = false" @done="() => { showPayment = false; onActionDone() }" />
    <DiscountModal v-if="showDiscount" :checkIn="checkIn" @close="showDiscount = false" @done="onActionDone" />
    <InvoiceDetailModal v-if="showInvoiceDetail && selectedInvoice"
      :invoiceName="selectedInvoice.invoice"
      :invoiceType="selectedInvoice.invoice_type"
      @close="showInvoiceDetail = false; selectedInvoice = null" />
    <PaymentDetailModal v-if="showPaymentDetail && selectedPayment"
      :paymentId="selectedPayment.payment_id"
      :paymentType="selectedPayment.payment_type"
      @close="showPaymentDetail = false; selectedPayment = null" />

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import RoomTransferModal from '@/components/checkin/RoomTransferModal.vue'
import StayAdjustmentModal from '@/components/checkin/StayAdjustmentModal.vue'
import RefundRequestModal from '@/components/checkin/RefundRequestModal.vue'
import BillTransferModal from '@/components/checkin/BillTransferModal.vue'
import ReceivePaymentModal from '@/components/checkin/ReceivePaymentModal.vue'
import DiscountModal from '@/components/checkin/DiscountModal.vue'
import InvoiceDetailModal from '@/components/checkin/InvoiceDetailModal.vue'
import PaymentDetailModal from '@/components/checkin/PaymentDetailModal.vue'
import { callMethodForm } from '@/lib/api'

const showRoomTransfer = ref(false)
const showStayAdjustment = ref(false)
const showRefund = ref(false)
const showBillTransfer = ref(false)
const showPayment = ref(false)
const showDiscount = ref(false)
const showInvoiceDetail = ref(false)
const selectedInvoice = ref(null)
const showPaymentDetail = ref(false)
const selectedPayment = ref(null)


const route = useRoute()
const activeTab = ref('Details')
const showCreateMenu = ref(false)
const invoices = ref([])
const acquiredBills = ref([])
const payments = ref([])
const loading = ref(true)
const loadError = ref('')

const checkIn = ref({
  name: route.params.id,
})

onMounted(async () => {
  if (!route.params.id) return
  await loadCheckIn()
})

async function loadCheckIn(silent = false) {
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    const data = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.get_checkin_detail', {
      name: route.params.id,
    })
    if (data) {
      checkIn.value = data
      invoices.value = data.invoices || []
      acquiredBills.value = data.acquired_bills || []
      payments.value = data.payments || []
    }
  } catch (e) {
    loadError.value = 'Network error — please refresh.'
    console.error('Failed to load check-in detail', e)
  } finally {
    if (!silent) loading.value = false
  }
}

// Close the "Create" menu when clicking outside
const closeCreateMenu = (e) => {
  if (showCreateMenu.value && !e.target.closest('.create-menu-container')) {
    showCreateMenu.value = false
  }
}

watch(showCreateMenu, (val) => {
  if (val) {
    setTimeout(() => window.addEventListener('click', closeCreateMenu), 0)
  } else {
    window.removeEventListener('click', closeCreateMenu)
  }
})

onUnmounted(() => {
  window.removeEventListener('click', closeCreateMenu)
})

watch(() => route.params.id, (newId) => {
  if (newId) loadCheckIn()
})

async function onActionDone() {
  await loadCheckIn(true)
}

const billingSummary = computed(() => checkIn.value?.billing_summary || {})
function summaryNumber(field, fallback) {
  const value = billingSummary.value?.[field]
  return value === undefined || value === null || value === '' ? fallback : Number(value) || 0
}

// Gross positive charges (room, restaurant, extensions) — exclude credit notes which
// have positive grand_total in this Frappe version (is_return handles accounting reversal)
const chargesTotal = computed(() =>
  summaryNumber(
    'sales_charges_total',
    invoices.value.filter(inv => !inv.is_return && (inv.amount || 0) > 0).reduce((s, inv) => s + inv.amount, 0)
  )
)
// Credit notes — is_return=1 invoices with positive amounts
const creditsTotal = computed(() =>
  summaryNumber(
    'credit_notes_total',
    invoices.value.filter(inv => inv.is_return).reduce((s, inv) => s + Math.abs(inv.amount || 0), 0)
  )
)
// Net for invoice table footer
const invoiceTotal = computed(() => summaryNumber('invoice_net_total', chargesTotal.value - creditsTotal.value))
// Outstanding the guest still owes — only regular (non-return) invoices
// If Frappe reconciled the credit note via return_against, the original invoice's
// outstanding_amount is already reduced; credit note outstanding = 0.
const outstandingDue = computed(() =>
  invoices.value.filter(inv => !inv.is_return && (inv.outstanding_amount || 0) > 0).reduce((s, inv) => s + inv.outstanding_amount, 0)
)
// Credit balance the hotel owes back (negative outstanding rows, as absolute value)
const creditBalance = computed(() =>
  invoices.value.filter(inv => (inv.outstanding_amount || 0) < 0).reduce((s, inv) => s + Math.abs(inv.outstanding_amount), 0)
)
// Net for invoice table footer
const outstandingTotal = computed(() => summaryNumber('invoice_outstanding', outstandingDue.value - creditBalance.value))
const acquiredTotal = computed(() =>
  summaryNumber(
    'acquired_total',
    acquiredBills.value
      .filter(b => b.status === 'Approved')
      .reduce((s, b) => s + (b.total_amount || 0), 0)
  )
)
const acquiredOutstanding = computed(() =>
  summaryNumber(
    'acquired_outstanding',
    acquiredBills.value
      .filter(b => b.status === 'Approved')
      .reduce((s, b) => s + (b.outstanding_amount || 0), 0)
  )
)
// Grand billing summary values
const grandCharges = computed(() => summaryNumber('total_charges', chargesTotal.value + acquiredTotal.value))
const grandCredits = computed(() => summaryNumber('total_credits', creditsTotal.value))
const grandNetBill = computed(() => summaryNumber('net_bill', grandCharges.value - grandCredits.value))
const totalPaid = computed(() =>
  summaryNumber(
    'total_received',
    payments.value
      .filter(p => p.payment_type === 'Receive' && p.docstatus === 1)
      .reduce((s, p) => s + (p.paid_amount || 0), 0)
  )
)
const totalRefunded = computed(() =>
  summaryNumber(
    'total_refunded',
    payments.value
      .filter(p => p.payment_type === 'Pay' && p.docstatus === 1)
      .reduce((s, p) => s + (p.paid_amount || 0), 0)
  )
)
const grandNetOutstanding = computed(() => summaryNumber('balance_amount', grandNetBill.value - totalPaid.value + totalRefunded.value))
const isOverdue = computed(() => {
  if (!checkIn.value?.expected_check_out_datetime) return false
  return new Date(checkIn.value.expected_check_out_datetime) < new Date()
})
const preferenceList = computed(() =>
  String(
    checkIn.value?.room_preferences
      || (checkIn.value?.housekeeping_notes || '').match(/Room Preferences:\s*([^\n]+)/i)?.[1]
      || ''
  )
    .split(',')
    .map(v => v.trim())
    .filter(Boolean)
)
const housekeepingNotes = computed(() =>
  String(checkIn.value?.housekeeping_notes || '')
    .split('\n')
    .filter(line => !/^Room Preferences:\s*/i.test(line.trim()))
    .join('\n')
    .trim()
)

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
function formatInvoiceType(type) {
  if (type === 'Sales Invoice') return 'Room Charge'
  if (type === 'POS Invoice') return 'Restaurant'
  if (type === 'Restaurant') return 'Restaurant'
  return type || 'Room Charge'
}
function openInvoiceDetail(inv) {
  selectedInvoice.value = inv
  showInvoiceDetail.value = true
}
function openPaymentDetail(pmt) {
  selectedPayment.value = pmt
  showPaymentDetail.value = true
}
function printFolio() {
  const name = checkIn.value?.name
  if (!name) return
  window.open(
    `/printview?doctype=Hotel%20Room%20Check%20In&name=${encodeURIComponent(name)}&format=Standard&no_letterhead=0`,
    '_blank'
  )
}
function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>
