<template>
  <div class="space-y-4">

    <!-- Loading / Error -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-xs">Loading booking…</span>
      </div>
    </div>

    <template v-else-if="booking.name">

      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">

  <h2 class="text-sm font-bold text-gray-900">
    {{ booking.name }}
  </h2>

  <!-- Document Status -->
  <span
    class="px-2.5 py-1 text-xs font-semibold rounded-full"
    :class="statusClass(booking.docstatus)"
  >
    {{ statusLabel(booking.docstatus) }}
  </span>

  <!-- Event Status -->
  <span
    class="px-2.5 py-1 text-xs font-semibold rounded-full"
    :class="eventStatusClass(booking.event_status)"
  >
    {{ booking.event_status || 'Scheduled' }}
  </span>

</div>
          <p class="text-xs text-gray-400 mt-0.5">{{ booking.customer_name }} • {{ booking.hall_name || booking.hall }} • {{ booking.event_type }}</p>
        </div>
          <div class="flex items-center gap-2">

            <button
              v-if="booking.docstatus === 0"
              @click="router.push(`/hall/booking/${booking.name}/edit`)"
              class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Edit Booking
            </button>

            <!-- Submit button for drafts -->
            <button v-if="booking.docstatus === 0" @click="submitBooking" :disabled="submitting"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
              {{ submitting ? 'Submitting…' : 'Submit Booking' }}
            </button>

          <button
              v-if="booking.docstatus === 1 && !booking.sales_invoice && !isCompleted"
              @click="createInvoice"
              :disabled="creatingInvoice"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {{ creatingInvoice ? 'Creating…' : 'Create Invoice' }}
            </button>

            <!-- Receive Payment -->
            <button v-if="booking.docstatus === 1 && booking.sales_invoice && booking.payment_status !== 'Paid' && !isCompleted"
              @click="showPaymentModal = true"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              Receive Payment
            </button>
            
            <!-- Adjust Booking -->
            <button
              v-if="booking.docstatus === 1 && !isCompleted"
              @click="showAdjustModal = true"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Adjust Booking
            </button>

            <button
                v-if="booking.docstatus === 1 && !isCompleted"
                @click="markEventStatus('Completed')" :disabled="actionSaving"
                class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
              >
                Mark Complete
              </button>

              <button
                v-if="booking.docstatus === 1 && booking.event_status !== 'No Show' && !isCompleted"
                @click="markEventStatus('No Show')" :disabled="actionSaving"
                class="px-4 py-2 text-xs font-medium text-orange-600 border border-orange-200 rounded-lg hover:bg-orange-50 transition-colors"
              >
                Mark No Show
              </button>

              <button
              v-if="booking.docstatus === 1 && !isCompleted"
                @click="cancelBooking" :disabled="actionSaving"
                class="px-4 py-2 text-xs font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Cancel Booking
              </button>

              <button
                v-if="booking.name"
                @click="printBooking"
                class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Print
              </button>


          </div>
      </div>

      <!-- Status strip -->
      <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Payment</p>
          <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="paymentClass(booking.payment_status)">
            {{ booking.payment_status }}
          </span>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Total Days</p>
          <p class="text-2xl font-bold text-gray-900">{{ booking.total_days }} day(s)</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Net Total</p>
          <p class="text-2xl font-bold text-gray-900">₦{{ Number((booking.net_total_computed ?? booking.net_total) || 0).toLocaleString() }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Outstanding</p>
          <p class="text-2xl font-bold" :class="booking.outstanding_amount > 0 ? 'text-red-500' : 'text-green-600'">
            <!-- ₦{{ Number(booking.outstanding_amount || 0).toLocaleString() }} -->
            ₦{{ Number(booking.outstanding_amount || 0).toLocaleString() }}
          </p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Paid Amount</p>
          <p class="text-2xl font-bold text-green-600">
            ₦{{ Number(booking.paid_amount || 0).toLocaleString() }}
          </p>
        </div>
        
      </div>

      <div
        v-if="actionError"
        class="bg-red-50 border border-red-100 text-red-600 text-xs px-4 py-3 rounded-lg"
      >
        {{ actionError }}
      </div>

      <div
        v-if="actionSuccess"
        class="bg-green-50 border border-green-100 text-green-700 text-xs px-4 py-3 rounded-lg"
      >
        {{ actionSuccess }}
      </div>

      <div style="display:grid;grid-template-columns:1fr 280px;gap:16px;align-items:start;">

        <!-- Left -->
        <div class="space-y-4">

          <!-- Booking Info -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Booking Information</h3>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
              <div><p class="text-xs text-gray-400 mb-0.5">Customer</p><p class="text-xs font-semibold text-gray-900">{{ booking.customer_name }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Mobile</p><p class="text-xs font-semibold text-gray-900">{{ booking.mobile_number || '–' }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Hall</p><p class="text-xs font-semibold text-gray-900">{{ booking.hall_name || booking.hall }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Event Type</p><p class="text-xs font-semibold text-gray-900">{{ booking.event_type }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Start</p><p class="text-xs font-semibold text-gray-900">{{ fmtDatetime(booking.start_datetime) }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">End</p><p class="text-xs font-semibold text-gray-900">{{ fmtDatetime(booking.end_datetime) }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Rate/day</p><p class="text-xs font-semibold text-gray-900">₦{{ Number(booking.rate || 0).toLocaleString() }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Total Days</p><p class="text-xs font-semibold text-gray-900">{{ booking.total_days }} day(s)</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Total Amount</p><p class="text-xs font-semibold text-gray-900">₦{{ Number(booking.total_amount || 0).toLocaleString() }}</p></div>
              <div v-if="booking.discount_amount"><p class="text-xs text-gray-400 mb-0.5">Discount</p><p class="text-xs font-semibold text-red-500">{{ booking.discount_type === 'Percentage' ? booking.discount_amount + '%' : '₦' + Number(booking.discount_amount).toLocaleString() }}</p></div>
              <div><p class="text-xs text-gray-400 mb-0.5">Net Total</p><p class="text-xs font-bold text-gray-900">₦{{ Number((booking.net_total_computed ?? booking.net_total) || 0).toLocaleString() }}</p></div>
              <div v-if="booking.sales_invoice"><p class="text-xs text-gray-400 mb-0.5">Invoice</p><p class="text-xs font-semibold text-blue-600">{{ booking.sales_invoice }}</p></div>
            </div>
          </div>

          <!-- Additional Services -->
          <div v-if="booking.additional_billings?.length" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-sm font-bold text-gray-900">Additional Services</h3>
            </div>
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Service</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Qty</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Rate</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Discount Type</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Discount Value</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Discount Amount</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Amount</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="(r, i) in booking.additional_billings" :key="i">
                  <td class="px-6 py-3 text-xs text-gray-700">{{ r.service }}</td>
                  <td class="px-6 py-3 text-xs text-gray-600">{{ r.qty }}</td>
                  <td class="px-6 py-3 text-xs text-gray-600">₦{{ Number(r.rate || 0).toLocaleString() }}</td>
                  <td class="px-6 py-3 text-xs text-gray-600">{{ r.discount_type || '—' }}</td>
                  <td class="px-6 py-3 text-xs text-gray-700 font-medium">
                     <template v-if="r.discount_type === 'Percentage'">
                        {{ r.discount_amount }}%
                      </template>

                      <template v-else>
                        ₦{{ Number(r.discount_amount || 0).toLocaleString() }}
                      </template>
                  </td>
                    <td class="px-6 py-3 text-xs text-gray-700 font-medium"> ₦{{ Number(r.discount_value || 0).toLocaleString() }}</td>
                    <td class="px-6 py-3 text-xs text-gray-700 font-medium">  ₦{{ Number(r.amount || 0).toLocaleString() }}</td>
                  
                  </tr>
              </tbody>
            </table>
          </div>

          <!-- Adjustment History -->
          <div v-if="booking.adjustment_history?.length" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-sm font-bold text-gray-900">Adjustment History</h3>
            </div>
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Previous Start</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Previous End</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Prev Days</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">New Start</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">New End</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">New Days</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Reason</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Status</th>
                  <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Invoice</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="(a, i) in booking.adjustment_history" :key="i">
                  <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(a.previous_start) }}</td>
                  <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(a.previous_end) }}</td>
                  <td class="px-6 py-3 text-xs text-gray-600">{{ a.previous_days }}</td>
                  <td class="px-6 py-3 text-xs text-gray-700 font-medium">{{ fmtDatetime(a.new_start) }}</td>
                  <td class="px-6 py-3 text-xs text-gray-700 font-medium">{{ fmtDatetime(a.new_end) }}</td>
                  <td class="px-6 py-3 text-xs text-gray-700 font-medium">{{ a.new_days }}</td>
                  <td class="px-6 py-3 text-xs text-gray-500">{{ a.adjustment_reason || '–' }}</td>
                  <td class="px-6 py-3 text-xs text-gray-500">
                    <div
                        class="mt-1 inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold"
                        :class="{
                            'bg-green-100 text-green-700': a.invoice_status === 'Paid',
                            'bg-red-100 text-red-700': a.invoice_status === 'Unpaid',
                            'bg-yellow-100 text-yellow-700': a.invoice_status === 'Partial'
                        }"
                        >
                        {{ a.invoice_status || 'Unknown' }}
                        </div>
                  </td>
                 <td class="px-6 py-3 text-xs">
                    <div v-if="a.adjustment_invoice">
                        <div class="text-blue-600 font-medium">
                        {{ a.adjustment_invoice }}
                        </div>

                        
                    </div>

                    <span v-else class="text-gray-400">—</span>
                </td>
                </tr>
              </tbody>
            </table>
          </div>

        </div>

        <!-- Right -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
  <h3 class="text-sm font-bold text-gray-900 mb-3">Financial Summary</h3>

  <div class="space-y-2 text-xs">
    <div class="flex justify-between">
      <span class="text-gray-500">Hall Gross</span>
      <span class="font-medium">
        ₦{{ Number(booking.hall_gross_total || booking.total_amount || 0).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between text-red-500">
      <span>Hall Discount</span>
      <span>
        –₦{{ Number(booking.hall_discount_value ?? hallDiscountValue).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between">
      <span class="text-gray-500">Hall Net</span>
      <span class="font-semibold">
        ₦{{ Number(booking.hall_net_total ?? hallNetTotal).toLocaleString() }}
      </span>
    </div>

    <div class="border-t border-gray-100 pt-2 flex justify-between">
      <span class="text-gray-500">Services Gross</span>
      <span class="font-medium">
        ₦{{ Number(booking.services_gross_total ?? servicesGrossTotal).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between text-red-500">
      <span>Services Discount</span>
      <span>
        –₦{{ Number(booking.services_discount_total ?? servicesDiscountTotal).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between">
      <span class="text-gray-500">Services Net</span>
      <span class="font-semibold">
        ₦{{ Number(booking.services_net_total ?? servicesNetTotal).toLocaleString() }}
      </span>
    </div>

    <div class="border-t border-gray-100 pt-2 flex justify-between font-bold">
      <span class="text-gray-700">Net Total</span>
      <span class="text-gray-900">
        ₦{{ Number((booking.net_total_computed ?? booking.net_total) || 0).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between">
      <span class="text-gray-500">Invoice Total</span>
      <span class="font-medium">
        ₦{{ Number(booking.invoice_grand_total || 0).toLocaleString() }}
      </span>
    </div>

    <div class="border-t border-gray-100 pt-2 flex justify-between">
      <span class="text-gray-500">Outstanding</span>
      <span
        class="font-bold"
        :class="booking.outstanding_amount > 0 ? 'text-red-500' : 'text-green-600'"
      >
        ₦{{ Number(booking.outstanding_amount || 0).toLocaleString() }}
      </span>
    </div>

    <div class="flex justify-between">
      <span class="text-gray-500">Paid Amount</span>
      <span class="font-semibold text-green-600">
        ₦{{ Number(booking.paid_amount || 0).toLocaleString() }}
      </span>
    </div>
  </div>
</div>

          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Audit</h3>
            <div class="space-y-2 text-xs">
              <div><p class="text-gray-400">Created</p><p class="text-gray-700">{{ fmtDatetime(booking.creation) }}</p></div>
              <div><p class="text-gray-400">Modified</p><p class="text-gray-700">{{ fmtDatetime(booking.modified) }}</p></div>
              <div v-if="booking.amended_from"><p class="text-gray-400">Amended From</p><p class="text-blue-600">{{ booking.amended_from }}</p></div>
              <div v-if="booking.completed_by">
                <p class="text-gray-400">Completed By</p>
                <p class="text-gray-700">{{ booking.completed_by }}</p>
              </div>

              <div v-if="booking.completed_on">
                <p class="text-gray-400">Completed On</p>
                <p class="text-gray-700">{{ fmtDatetime(booking.completed_on) }}</p>
              </div>
            </div>
          </div>
        </div>

      </div>

    </template>

    <!-- ── Receive Payment Modal ── -->
    <div v-if="showPaymentModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Receive Payment</h3>
          <button @click="showPaymentModal = false" class="text-gray-400 hover:text-gray-600 text-lg leading-none">✕</button>
        </div>
        <div class="px-6 py-4 space-y-3">
          <div class="bg-blue-50 rounded-lg px-4 py-2 text-xs text-blue-700">
            Outstanding: <strong>₦{{ Number(booking.outstanding_amount || 0).toLocaleString() }}</strong>
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Amount <span class="text-red-500">*</span></label>
            <input v-model="payment.paid_amount" type="number" min="0"
              :max="booking.outstanding_amount"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Mode of Payment <span class="text-red-500">*</span></label>
            <select v-model="payment.payment_mode"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">— select —</option>
              <option v-for="m in paymentModes" :key="m.name" :value="m.name">{{ m.name }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Payment Date <span class="text-red-500">*</span></label>
            <input v-model="payment.payment_date" type="date"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Reference No</label>
            <input v-model="payment.reference_no" type="text" placeholder="Cheque / transfer ref"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Reference Date</label>
            <input v-model="payment.reference_date" type="date"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Remarks</label>
            <textarea v-model="payment.remarks" rows="2"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>
          <p v-if="paymentError" class="text-xs text-red-500">{{ paymentError }}</p>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex gap-2">
          <button @click="showPaymentModal = false"
            class="flex-1 px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="receivePayment" :disabled="paymentSaving"
            class="flex-1 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {{ paymentSaving ? 'Processing…' : 'Post Payment' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Adjust Booking Modal ── -->
    <div v-if="showAdjustModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Adjust Booking</h3>
          <button @click="showAdjustModal = false" class="text-gray-400 hover:text-gray-600 text-lg leading-none">✕</button>
        </div>
        <div class="px-6 py-4 space-y-3">
          <div class="bg-yellow-50 rounded-lg px-4 py-2 text-xs text-yellow-700">
            Current: {{ fmtDatetime(booking.start_datetime) }} → {{ fmtDatetime(booking.end_datetime) }}
            ({{ booking.total_days }} day(s))
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">New Start <span class="text-red-500">*</span></label>
            <input v-model="adjust.start_datetime" type="datetime-local"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">New End <span class="text-red-500">*</span></label>
            <input v-model="adjust.end_datetime" type="datetime-local"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div v-if="adjustDays > 0" class="text-xs text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
            New duration: <strong>{{ adjustDays }} day(s)</strong>
            <span v-if="adjustDays !== booking.total_days" class="ml-2"
              :class="adjustDays > booking.total_days ? 'text-blue-600' : 'text-red-500'">
              ({{ adjustDays > booking.total_days ? '+' : '' }}{{ adjustDays - booking.total_days }} day(s) — {{ adjustDays > booking.total_days ? 'additional invoice' : 'return invoice' }} will be created)
            </span>
          </div>

          <div
              v-if="adjustmentDiffDays !== 0"
              class="text-xs bg-gray-50 rounded-lg px-4 py-3 space-y-2"
            >
              <div class="flex justify-between">
                <span class="text-gray-500">Rate / Day</span>
                <span class="font-semibold">
                  ₦{{ Number(booking.rate || 0).toLocaleString() }}
                </span>
              </div>

              <div class="flex justify-between">
                <span class="text-gray-500">
                  {{ adjustmentDiffDays > 0 ? 'Extra Days' : 'Reduced Days' }}
                </span>
                <span class="font-semibold">
                  {{ adjustmentDiffDays }}
                </span>
              </div>

              <div class="flex justify-between">
                <span class="text-gray-500">Adjustment Gross</span>
                <span class="font-semibold">
                  ₦{{ Number(adjustmentGross || 0).toLocaleString() }}
                </span>
              </div>

              <div class="flex justify-between text-red-500">
                <span>Discount Impact</span>
                <span>
                  –₦{{ Number(adjustmentDiscountValue || 0).toLocaleString() }}
                </span>
              </div>

              <div class="border-t border-gray-100 pt-2 flex justify-between font-bold">
                <span>Balance Impact</span>
                <span :class="adjustmentNetImpact >= 0 ? 'text-blue-600' : 'text-red-500'">
                  {{ adjustmentNetImpact >= 0 ? '+' : '-' }}₦{{ Number(Math.abs(adjustmentNetImpact || 0)).toLocaleString() }}
                </span>
              </div>
            </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Discount Type</label>
            <select
              v-model="adjust.discount_type"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Fixed Amount">Fixed Amount</option>
              <option value="Percentage">Percentage</option>
            </select>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">
              Discount {{ adjust.discount_type === 'Percentage' ? '(%)' : '(₦)' }}
            </label>
            <input
              v-model.number="adjust.discount_amount"
              type="number"
              min="0"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 mb-1 block">Reason</label>
            <textarea v-model="adjust.reason" rows="2" placeholder="Why is this booking being adjusted?"
              class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>
          <p v-if="adjustError" class="text-xs text-red-500">{{ adjustError }}</p>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex gap-2">
          <button @click="showAdjustModal = false"
            class="flex-1 px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="doAdjust" :disabled="adjustSaving || !adjust.start_datetime || !adjust.end_datetime"
            class="flex-1 px-4 py-2 text-xs font-semibold text-white bg-yellow-500 rounded-lg hover:bg-yellow-600 disabled:opacity-50">
            {{ adjustSaving ? 'Adjusting…' : 'Confirm Adjustment' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { callMethod } from '@/lib/api'

const route   = useRoute()
const router = useRouter()

const loading = ref(false)
const booking = ref({})

// Submit
const submitting = ref(false)

const creatingInvoice = ref(false)

// Payment modal
const showPaymentModal = ref(false)
const paymentSaving    = ref(false)
const paymentError     = ref(null)
const paymentModes     = ref([])
const payment = ref({ paid_amount: '', payment_mode: '', payment_date: today(), reference_no: '', reference_date: '', remarks: '' })

// Adjust modal
const showAdjustModal = ref(false)
const adjustSaving    = ref(false)
const adjustError     = ref(null)
const adjust = ref({
  start_datetime: '',
  end_datetime: '',
  reason: '',
  discount_type: 'Fixed Amount',
  discount_amount: 0,
})


const actionError = ref(null)
const actionSuccess = ref(null)
const actionSaving = ref(false)


const adjustDays = computed(() => {
  if (!adjust.value.start_datetime || !adjust.value.end_datetime) return 0
  const diff = new Date(adjust.value.end_datetime) - new Date(adjust.value.start_datetime)
  return diff > 0 ? Math.ceil(diff / (1000 * 60 * 60 * 24)) : 0
})

function today() { return new Date().toISOString().slice(0, 10) }

function fmtDatetime(dt) {
  if (!dt) return '–'

  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

function statusLabel(s) { return { 0: 'Draft', 1: 'Confirmed', 2: 'Cancelled' }[s] || 'Unknown' }
function statusClass(s)  { return { 0: 'bg-yellow-100 text-yellow-600', 1: 'bg-green-100 text-green-700', 2: 'bg-red-100 text-red-500' }[s] || 'bg-gray-100 text-gray-500' }
function paymentClass(s) { return { 'Paid': 'bg-green-100 text-green-700', 'Unpaid': 'bg-red-100 text-red-500', 'Partial': 'bg-yellow-100 text-yellow-600', 'Draft': 'bg-gray-100 text-gray-500', 'No Invoice': 'bg-gray-100 text-gray-400' }[s] || 'bg-gray-100 text-gray-500' }

async function load() {
  loading.value = true
  try {
    const [b, modes] = await Promise.all([
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_booking', { name: route.params.id }),
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_payment_modes'),
    ])
    booking.value      = b || {}
    paymentModes.value = modes || []
    // Pre-fill adjust modal with current times
    if (b?.start_datetime) adjust.value.start_datetime = toLocalInput(b.start_datetime)
    if (b?.end_datetime)   adjust.value.end_datetime   = toLocalInput(b.end_datetime)
    adjust.value.discount_type =
     b?.discount_type || 'Fixed Amount'

    adjust.value.discount_amount =
      Number(b?.discount_amount || 0)
    // Pre-fill payment amount
    payment.value.paid_amount = b?.outstanding_amount || ''
  } catch(e) { console.error(e) }
  finally { loading.value = false }
}

function toLocalInput(dt) {
  if (!dt) return ''

  const d = new Date(dt)

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hour}:${minute}`
}

async function submitBooking() {
  submitting.value = true
  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.submit_booking', { name: booking.value.name })
    await load()
  } catch(e) { alert(e.message) }
  finally { submitting.value = false }
}

async function createInvoice() {
  creatingInvoice.value = true

  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.create_invoice', {
      booking_name: booking.value.name,
    })

    await load()
  } catch (e) {
    alert(e.message || 'Failed to create invoice.')
  } finally {
    creatingInvoice.value = false
  }
}

async function receivePayment() {
  if (!payment.value.paid_amount || !payment.value.payment_mode || !payment.value.payment_date) {
    paymentError.value = 'Amount, mode of payment, and date are required.'
    return
  }
  paymentSaving.value = true
  paymentError.value  = null
  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.receive_payment', {
      booking_name: booking.value.name,
      data: JSON.stringify(payment.value),
    })
    showPaymentModal.value = false
    await load()
  } catch(e) {
    paymentError.value = e.message || 'Failed to post payment.'
  } finally { paymentSaving.value = false }
}

async function doAdjust() {
  if (!adjust.value.start_datetime || !adjust.value.end_datetime) return

  const currentDays = Number(booking.value.total_days || 0)
  const newDays = Number(adjustDays.value || 0)
  const diffDays = Math.abs(newDays - currentDays)
  const rate = Number(booking.value.rate || 0)
  const adjustmentGross = diffDays * rate

  let discountAmount = Number(adjust.value.discount_amount || 0)

  if (adjust.value.discount_type === 'Percentage' && discountAmount > 100) {
    adjustError.value = 'Discount percentage cannot be greater than 100%.'
    return
  }

  if (adjust.value.discount_type === 'Fixed Amount' && discountAmount > adjustmentGross) {
    adjustError.value = 'Discount amount cannot be greater than the adjustment amount.'
    return
  }

  adjustSaving.value = true
  adjustError.value = null

  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.adjust_booking', {
      booking_name: booking.value.name,
      start_datetime: adjust.value.start_datetime,
      end_datetime: adjust.value.end_datetime,
      reason: adjust.value.reason,
      discount_type: adjust.value.discount_type,
      discount_amount: discountAmount,
    })

    showAdjustModal.value = false
    await load()
  } catch (e) {
    adjustError.value = e.message || 'Failed to adjust booking.'
  } finally {
    adjustSaving.value = false
  }
}

const hallDiscountValue = computed(() => {
  const hallTotal = Number(booking.value.total_amount || 0)
  const discountAmount = Number(booking.value.discount_amount || 0)

  if (!discountAmount) return 0

  if (booking.value.discount_type === 'Percentage') {
    return hallTotal * (discountAmount / 100)
  }

  return discountAmount
})

const hallNetTotal = computed(() =>
  Math.max(
    0,
    Number(booking.value.total_amount || 0) - hallDiscountValue.value
  )
)

const servicesGrossTotal = computed(() =>
  (booking.value.additional_billings || []).reduce((sum, r) => {
    return sum + ((Number(r.qty) || 0) * (Number(r.rate) || 0))
  }, 0)
)

const servicesDiscountTotal = computed(() =>
  (booking.value.additional_billings || []).reduce((sum, r) => {
    return sum + (Number(r.discount_value) || 0)
  }, 0)
)

const servicesNetTotal = computed(() =>
  (booking.value.additional_billings || []).reduce((sum, r) => {
    return sum + (Number(r.amount) || 0)
  }, 0)
)


const adjustmentDiffDays = computed(() => {
  const currentDays = Number(booking.value.total_days || 0)
  return Number(adjustDays.value || 0) - currentDays
})

const adjustmentGross = computed(() => {
  return Math.abs(adjustmentDiffDays.value) * Number(booking.value.rate || 0)
})

const adjustmentDiscountValue = computed(() => {
  const discount = Number(adjust.value.discount_amount || 0)

  if (!adjustmentGross.value || !discount) return 0

  if (adjust.value.discount_type === 'Percentage') {
    return adjustmentGross.value * (discount / 100)
  }

  return Math.min(discount, adjustmentGross.value)
})

const adjustmentNetImpact = computed(() => {
  const net = adjustmentGross.value - adjustmentDiscountValue.value
  return adjustmentDiffDays.value < 0 ? -net : net
})


function eventStatusClass(status) {
  return {
    Scheduled: 'bg-blue-100 text-blue-700',
    Completed: 'bg-green-100 text-green-700',
    'No Show': 'bg-orange-100 text-orange-700',
    Cancelled: 'bg-red-100 text-red-700',
  }[status] || 'bg-gray-100 text-gray-500'
}

async function markEventStatus(status) {
  actionSaving.value = true
  actionError.value = null
  actionSuccess.value = null

  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.mark_event_status', {
      booking_name: booking.value.name,
      event_status: status,
    })

    actionSuccess.value = `Booking marked as ${status}.`
    await load()
  } catch (e) {
    actionError.value = e.message || 'Failed to update event status.'
  } finally {
    actionSaving.value = false
  }
}

async function cancelBooking() {
  if (!confirm('Cancel this booking and all attached invoices?')) return

  actionSaving.value = true
  actionError.value = null
  actionSuccess.value = null

  try {
    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.cancel_hall_booking', {
      booking_name: booking.value.name,
    })

    actionSuccess.value = 'Booking cancelled successfully.'
    await load()
  } catch (e) {
    actionError.value = e.message || 'Failed to cancel booking.'
  } finally {
    actionSaving.value = false
  }
}

function printBooking() {
  window.open(
    `/api/method/rhohotel.rhocom_hotel.api.hall_booking.download_hall_booking?booking_name=${booking.value.name}`,
    '_blank'
  )
}

const isCompleted = computed(
  () => booking.value.event_status === 'Completed'
)


onMounted(load)
</script>

