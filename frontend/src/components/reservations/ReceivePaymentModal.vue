<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:720px;max-height:92vh;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Receive Payment</h2>
            <p class="text-xs text-gray-400 mt-1">Collect payment for reservation {{ reservation.name }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs font-bold text-red-600 mb-1">Error</p>
            <p class="text-xs text-red-500">{{ error }}</p>
          </div>

          <div v-if="loadingInvoices" class="py-10 text-center">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p class="text-xs text-gray-400">Loading outstanding invoices…</p>
          </div>

          <template v-else>
            <div v-if="invoices.length === 0"
              class="bg-green-50 border border-green-200 rounded-xl px-5 py-5 text-center">
              <p class="text-sm font-bold text-green-600 mb-1">No Outstanding Balance</p>
              <p class="text-xs text-green-500">All invoices for this reservation have been settled.</p>
            </div>

            <template v-else>
              <div>
                <h3 class="text-sm font-bold text-gray-900 mb-3">Outstanding Invoices</h3>
                <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <table class="w-full">
                    <thead>
                      <tr class="border-b border-gray-100 bg-gray-50">
                        <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Invoice</th>
                        <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Payer / Room</th>
                        <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Date</th>
                        <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Invoice Total</th>
                        <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Credit Note</th>
                        <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Outstanding</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="inv in invoices"
                        :key="inv.name"
                        class="border-b border-gray-50 last:border-0 cursor-pointer"
                        :class="isSelected(inv.name) ? 'bg-blue-50' : 'hover:bg-gray-50'"
                        @click="toggleInvoice(inv.name)"
                      >
                        <td class="px-4 py-3 text-xs text-blue-600 font-medium">
                          <label class="inline-flex items-center gap-2 cursor-pointer" @click.stop>
                            <input
                              type="checkbox"
                              class="rounded border-gray-300"
                              :checked="isSelected(inv.name)"
                              @click.stop
                              @change="toggleInvoice(inv.name)"
                            />
                            <span>{{ inv.name }}</span>
                          </label>
                        </td>
                        <td class="px-3 py-3 text-xs text-gray-600">
                          <p class="font-semibold text-gray-800">{{ inv.occupant_name || inv.customer_name || inv.customer || '—' }}</p>
                          <p class="text-[10px] text-gray-400">{{ inv.room_number || inv.invoice_scope || 'Reservation' }}</p>
                        </td>
                        <td class="px-3 py-3 text-xs text-gray-500">{{ inv.posting_date || '—' }}</td>
                        <td class="px-4 py-3 text-xs text-right text-gray-700">{{ fmt(inv.grand_total) }}</td>
                        <td class="px-4 py-3 text-xs text-right font-semibold" :class="Number(inv.credit_note_amount || 0) > 0 ? 'text-teal-600' : 'text-gray-400'">
                          {{ Number(inv.credit_note_amount || 0) > 0 ? '- ' : '' }}{{ fmt(inv.credit_note_amount || 0) }}
                        </td>
                        <td class="px-4 py-3 text-xs text-right font-semibold text-red-500">{{ fmt(inv.outstanding_amount) }}</td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr class="border-t border-gray-200 bg-gray-50">
                        <td colspan="5" class="px-4 py-3 text-xs font-bold text-gray-900">Total Outstanding</td>
                        <td class="px-4 py-3 text-xs font-bold text-right text-red-500">{{ fmt(totalOutstanding) }}</td>
                      </tr>
                      <tr class="bg-blue-50">
                        <td colspan="5" class="px-4 py-3 text-xs font-bold text-blue-700">Selected for Payment</td>
                        <td class="px-4 py-3 text-xs font-bold text-right text-blue-700">{{ fmt(selectedOutstanding) }}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <div>
                <h3 class="text-sm font-bold text-gray-900 mb-3">Payment Details</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Mode of Payment <span class="text-red-400">*</span></p>
                    <select v-model="form.mode_of_payment"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="">Select mode</option>
                      <option v-for="m in paymentModes" :key="m.name" :value="m.name">{{ m.name }}</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Amount Received <span class="text-red-400">*</span></p>
                    <input type="text" :value="rawAmountInput" @input="onAmountInput" @focus="onAmountFocus" @blur="onAmountBlur" placeholder="0.00"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
                    <input type="date" v-model="form.payment_date"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Reference No</p>
                    <input type="text" v-model="form.reference_no" placeholder="Bank / terminal reference"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Reference Date</p>
                    <input type="date" v-model="form.reference_date"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Remarks</p>
                    <input type="text" v-model="form.remarks" placeholder="Optional note"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>

              <div v-if="form.paid_amount > 0 && form.paid_amount < selectedOutstanding"
                class="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
                <p class="text-xs text-yellow-700">
                  Partial payment of {{ fmt(form.paid_amount) }} will be allocated proportionally.
                  Remaining balance: {{ fmt(selectedOutstanding - form.paid_amount) }}
                </p>
              </div>
            </template>
          </template>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button
              :disabled="submitting || invoices.length === 0 || selectedOutstanding <= 0 || !form.mode_of_payment || !(form.paid_amount > 0)"
              @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Processing…' : 'Confirm Payment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { callMethod, callMethodForm } from '@/lib/api'

const props = defineProps({ reservation: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const loadingInvoices = ref(true)
const invoices = ref([])
const paymentModes = ref([])
const submitting = ref(false)
const error = ref('')
const selectedInvoiceNames = ref([])

const today = new Date().toISOString().slice(0, 10)
const form = reactive({
  mode_of_payment: '',
  paid_amount: 0,
  payment_date: today,
  reference_no: '',
  reference_date: '',
  remarks: '',
})

const totalOutstanding = computed(() =>
  invoices.value.reduce((s, i) => s + (Number(i.outstanding_amount) || 0), 0)
)
const selectedInvoices = computed(() =>
  invoices.value.filter((inv) => selectedInvoiceNames.value.includes(inv.name))
)
const selectedOutstanding = computed(() =>
  selectedInvoices.value.reduce((s, i) => s + (Number(i.outstanding_amount) || 0), 0)
)
const isGroupSplit = computed(() =>
  String(props.reservation?.reservation_type || '').toLowerCase() === 'group'
  && String(props.reservation?.group_billing_mode || '').toLowerCase().startsWith('split')
)

const rawAmountInput = ref('')

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function onAmountInput(e) {
  rawAmountInput.value = e.target.value
  form.paid_amount = parseFloat(String(e.target.value).replace(/[^0-9.]/g, '')) || 0
}

function onAmountFocus() {
  rawAmountInput.value = form.paid_amount > 0 ? String(form.paid_amount) : ''
}

function onAmountBlur() {
  rawAmountInput.value = form.paid_amount > 0 ? fmt(form.paid_amount) : ''
}

function isSelected(invoiceName) {
  return selectedInvoiceNames.value.includes(invoiceName)
}

function toggleInvoice(invoiceName) {
  if (isSelected(invoiceName)) {
    selectedInvoiceNames.value = selectedInvoiceNames.value.filter((name) => name !== invoiceName)
  } else {
    selectedInvoiceNames.value = [...selectedInvoiceNames.value, invoiceName]
  }
}

function syncAmountToSelection() {
  form.paid_amount = selectedOutstanding.value
  rawAmountInput.value = fmt(selectedOutstanding.value)
}

onMounted(async () => {
  try {
    const [invRows, mops] = await Promise.all([
      callMethodForm('rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.get_outstanding_invoices_for_reservation', {
        reservation_name: props.reservation.name,
      }),
      callMethod('frappe.client.get_list', {
        doctype: 'Mode of Payment',
        fields: ['name'],
        limit_page_length: 50,
      }),
    ])

    invoices.value = invRows || []
    paymentModes.value = mops || []
    selectedInvoiceNames.value = isGroupSplit.value && invoices.value.length
      ? [invoices.value[0].name]
      : invoices.value.map((inv) => inv.name)
    syncAmountToSelection()
  } catch (e) {
    error.value = String(e?.message || 'Failed to load invoices. Please try again.')
  } finally {
    loadingInvoices.value = false
  }
})

watch(selectedInvoiceNames, () => {
  syncAmountToSelection()
})

async function submit() {
  if (!form.mode_of_payment || !(form.paid_amount > 0)) return
  submitting.value = true
  error.value = ''
  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.collect_payment_for_reservation',
      {
        reservation_name: props.reservation.name,
        payment_info: JSON.stringify({
          mode_of_payment: form.mode_of_payment,
          paid_amount: form.paid_amount,
          selected_invoices: selectedInvoiceNames.value,
          payment_date: form.payment_date,
          reference_no: form.reference_no,
          reference_date: form.reference_date,
          remarks: form.remarks,
        }),
      },
    )

    emit('done', result)
    emit('close')
  } catch (e) {
    error.value = String(e?.message || 'Network error. Please try again.')
  } finally {
    submitting.value = false
  }
}
</script>
