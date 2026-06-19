<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:640px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">{{ voucherOnly ? 'Apply Room Voucher' : 'Apply Discount' }}</h2>
            <p class="text-xs text-gray-400 mt-1">{{ voucherOnly ? 'Select an invoice then apply an approved room voucher as a credit note.' : 'Select an invoice then enter the discount — a credit note will be created against it' }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Error -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-600">{{ error }}</p>
          </div>

          <!-- Context -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
            <p class="text-xs text-blue-700 font-semibold">{{ checkIn.guest }}</p>
            <p class="text-xs text-blue-500 mt-0.5">Room {{ checkIn.room_number }}</p>
          </div>

          <!-- Room Voucher -->
          <div v-if="voucherOnly" class="bg-emerald-50 rounded-xl border border-emerald-200 px-4 py-3">
            <div class="flex items-center justify-between gap-3 mb-2">
              <div>
                <p class="text-xs font-bold text-emerald-800">Room Voucher</p>
                <p class="text-xs text-emerald-600 mt-0.5">Apply an approved room voucher as a credit note on a room invoice.</p>
              </div>
              <button @click="loadRoomVouchers" class="text-xs font-medium text-blue-600 hover:text-blue-700">Refresh</button>
            </div>
            <div v-if="roomVoucherError" class="mb-2 text-xs text-red-600">{{ roomVoucherError }}</div>
            <select v-model="selectedVoucherName"
              :disabled="loadingVouchers || roomVouchers.length === 0"
              class="w-full px-3 py-2.5 text-xs border border-emerald-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-gray-700 bg-white">
              <option value="">{{ loadingVouchers ? 'Loading vouchers...' : roomVouchers.length ? 'Select room voucher' : 'No approved room voucher found' }}</option>
              <option v-for="voucher in roomVouchers" :key="voucher.name" :value="voucher.name">
                {{ voucherLabel(voucher) }}
              </option>
            </select>
            <div v-if="selectedVoucher" class="mt-2 flex items-center justify-between gap-3">
              <p class="text-xs text-emerald-700">
                Voucher will apply {{ fmt(voucherApplyAmount) }} to {{ selectedInvoice?.invoice || 'the selected invoice' }}.
              </p>
              <button
                :disabled="applyingVoucher || !selectedInvoice || voucherApplyAmount <= 0 || selectedInvoice.invoice_type === 'POS Invoice'"
                @click="applyVoucher"
                class="px-3 py-2 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed">
                {{ applyingVoucher ? 'Applying...' : 'Apply Voucher' }}
              </button>
            </div>
            <p v-if="selectedInvoice?.invoice_type === 'POS Invoice'" class="text-xs text-amber-600 mt-2">
              Room vouchers can only be applied to Sales Invoice room charges.
            </p>
          </div>

          <!-- Step 1: Invoice Selector -->
          <div>
            <h3 class="text-sm font-bold text-gray-900 mb-2">{{ voucherOnly ? 'Select Invoice' : '1. Select Invoice' }}</h3>
            <div v-if="chargeableInvoices.length === 0"
              class="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
              <p class="text-xs text-yellow-700">No invoices with an outstanding balance found for this check-in.</p>
            </div>
            <div v-else class="rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="bg-gray-50 border-b border-gray-100">
                    <th class="w-8 px-3 py-2.5"></th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Invoice</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Type</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Amount</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-2.5">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="inv in chargeableInvoices" :key="inv.invoice"
                    class="border-b border-gray-50 last:border-0 cursor-pointer hover:bg-gray-50 transition-colors"
                    :class="selectedInvoice?.invoice === inv.invoice ? 'bg-blue-50 hover:bg-blue-50' : ''"
                    @click="selectInvoice(inv)">
                    <td class="px-3 py-2.5 text-center">
                      <div class="w-4 h-4 rounded-full border-2 mx-auto flex items-center justify-center"
                        :class="selectedInvoice?.invoice === inv.invoice ? 'border-blue-600 bg-blue-600' : 'border-gray-300'">
                        <div v-if="selectedInvoice?.invoice === inv.invoice" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                      </div>
                    </td>
                    <td class="px-3 py-2.5 text-xs font-medium text-blue-600">{{ inv.invoice }}</td>
                    <td class="px-3 py-2.5 text-xs text-gray-500">{{ formatType(inv.invoice_type) }}</td>
                    <td class="px-4 py-2.5 text-xs text-right text-gray-700">{{ fmt(inv.amount) }}</td>
                    <td class="px-4 py-2.5 text-xs text-right font-semibold text-red-500">{{ fmt(inv.outstanding_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step 2: Discount details (shown only after invoice is selected, hidden when applying a voucher) -->
          <template v-if="selectedInvoice && !selectedVoucher && !voucherOnly">
            <div>
              <h3 class="text-sm font-bold text-gray-900 mb-3">2. Discount Details</h3>

              <div class="space-y-4">
                <!-- Discount Type -->
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Discount Type <span class="text-red-400">*</span></p>
                  <select v-model="discountType"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-600">
                    <option value="fixed">Fixed Amount (₦)</option>
                    <option value="percentage">Percentage (%)</option>
                  </select>
                </div>

                <div v-if="discountType === 'fixed'">
                  <p class="text-xs text-gray-500 mb-1.5">Discount Amount (₦) <span class="text-red-400">*</span></p>
                  <input type="number" v-model.number="discountAmount" min="0.01"
                    :max="selectedInvoice.outstanding_amount" step="0.01"
                    placeholder="Enter amount"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <p class="text-xs text-gray-400 mt-1">Max: {{ fmt(selectedInvoice.outstanding_amount) }}</p>
                </div>
                <div v-else>
                  <p class="text-xs text-gray-500 mb-1.5">Discount Percentage (%) <span class="text-red-400">*</span></p>
                  <input type="number" v-model.number="discountPercent" min="0.01" max="100" step="0.01"
                    placeholder="e.g. 10"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <p v-if="discountPercent > 0" class="text-xs text-blue-600 mt-1">
                    = {{ fmt(computedDiscountAmount) }}
                  </p>
                </div>

                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reason <span class="text-red-400">*</span></p>
                  <textarea v-model="reason" rows="2"
                    placeholder="Explain why the discount is being applied"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
              </div>
            </div>

            <!-- Summary -->
            <div v-if="computedDiscountAmount > 0" class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-3 space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Invoice</span>
                <span class="text-xs font-medium text-gray-700">{{ selectedInvoice.invoice }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Current Outstanding</span>
                <span class="text-xs text-red-500 font-semibold">{{ fmt(selectedInvoice.outstanding_amount) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-gray-500">Discount</span>
                <span class="text-xs text-teal-600 font-semibold">− {{ fmt(computedDiscountAmount) }}</span>
              </div>
              <div class="flex items-center justify-between pt-1.5 border-t border-gray-200">
                <span class="text-xs font-bold text-gray-900">New Outstanding</span>
                <span class="text-xs font-bold"
                  :class="(selectedInvoice.outstanding_amount - computedDiscountAmount) > 0 ? 'text-red-500' : 'text-green-600'">
                  {{ fmt(Math.max(0, selectedInvoice.outstanding_amount - computedDiscountAmount)) }}
                </span>
              </div>
            </div>
          </template>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button v-if="!selectedVoucher && !voucherOnly"
              :disabled="submitting || !selectedInvoice || !(computedDiscountAmount > 0) || !reason.trim()"
              @click="submit"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ submitting ? 'Applying…' : 'Apply Discount' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { humanizeErrorMessage } from '@/lib/api'

const props = defineProps({
  checkIn: { type: Object, required: true },
  voucherOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'done'])

const discountType = ref('fixed')
const discountAmount = ref(0)
const discountPercent = ref(0)
const reason = ref('')
const submitting = ref(false)
const error = ref('')
const selectedInvoice = ref(null)
const roomVouchers = ref([])
const selectedVoucherName = ref('')
const loadingVouchers = ref(false)
const applyingVoucher = ref(false)
const roomVoucherError = ref('')

// Only positive, non-return invoices with remaining outstanding are valid targets
const chargeableInvoices = computed(() =>
  (props.checkIn.invoices || []).filter(inv =>
    (inv.amount || 0) > 0 && !inv.is_return && (inv.outstanding_amount || 0) > 0
  )
)

const computedDiscountAmount = computed(() => {
  const max = selectedInvoice.value?.outstanding_amount || 0
  if (discountType.value === 'percentage') {
    const pct = Number(discountPercent.value) || 0
    return Math.min(Math.round(((pct / 100) * max) * 100) / 100, max)
  }
  return Math.min(Number(discountAmount.value) || 0, max)
})
const selectedVoucher = computed(() =>
  roomVouchers.value.find(v => v.name === selectedVoucherName.value) || null
)
const voucherApplyAmount = computed(() => {
  if (!selectedVoucher.value || !selectedInvoice.value) return 0
  return Math.min(voucherRemainingValue(selectedVoucher.value), Number(selectedInvoice.value.outstanding_amount || 0))
})

onMounted(() => {
  loadRoomVouchers()
})

function selectInvoice(inv) {
  selectedInvoice.value = inv
  discountAmount.value = 0
  discountPercent.value = 0
}

function fmt(v) {
  if (!v && v !== 0) return '₦ 0.00'
  return `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function formatType(type) {
  if (type === 'Sales Invoice') return 'Room Charge'
  if (type === 'POS Invoice') return 'Restaurant'
  return type || 'Room Charge'
}

function voucherLabel(voucher) {
  const expiry = voucher.expiry_date ? ` - expires ${voucher.expiry_date}` : ''
  const redeemed = Number(voucher.redeemed_amount || 0)
  const usage = redeemed > 0 ? ` remaining of ${fmt(voucher.value)}` : ''
  return `${voucher.name} - ${fmt(voucherRemainingValue(voucher))}${usage}${expiry}`
}

function voucherRemainingValue(voucher) {
  if (!voucher) return 0
  if (voucher.remaining_value !== undefined && voucher.remaining_value !== null) {
    return Number(voucher.remaining_value || 0)
  }
  return Math.max(0, Number(voucher.value || 0) - Number(voucher.redeemed_amount || 0))
}

async function loadRoomVouchers() {
  loadingVouchers.value = true
  roomVoucherError.value = ''
  try {
    const params = new URLSearchParams({
      check_in: props.checkIn.name || '',
      room: props.checkIn.room_number || '',
      guest: props.checkIn.guest || '',
      department: 'Front Desk',
      complimentary_type: 'Room Voucher',
    })
    const res = await fetch(`/api/method/rhohotel.rhocom_hotel.api.complimentary.get_redeemable_complimentaries?${params.toString()}`)
    const data = await res.json()
    if (data.exc) {
      roomVoucherError.value = 'Could not load room vouchers.'
      return
    }
    roomVouchers.value = Array.isArray(data.message) ? data.message : []
    if (selectedVoucherName.value && !roomVouchers.value.some(v => v.name === selectedVoucherName.value)) {
      selectedVoucherName.value = ''
    }
  } catch {
    roomVoucherError.value = 'Network error while loading room vouchers.'
  } finally {
    loadingVouchers.value = false
  }
}

async function applyVoucher() {
  if (!selectedVoucher.value || !selectedInvoice.value || !(voucherApplyAmount.value > 0)) return
  applyingVoucher.value = true
  roomVoucherError.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.apply_room_voucher', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
      body: new URLSearchParams({
        check_in_name: props.checkIn.name,
        complimentary_name: selectedVoucher.value.name,
        source_invoice: selectedInvoice.value.invoice,
      }),
    })
    const data = await res.json()
    if (data.exc) {
      try {
        const msgs = JSON.parse(data._server_messages || '[]')
        roomVoucherError.value = humanizeErrorMessage(JSON.parse(msgs[0]).message || 'Failed to apply room voucher.')
      } catch {
        roomVoucherError.value = humanizeErrorMessage(data.exception || data._error_message || 'Failed to apply room voucher.')
      }
      return
    }
    emit('done', data.message)
    emit('close')
  } catch {
    roomVoucherError.value = 'Network error. Please try again.'
  } finally {
    applyingVoucher.value = false
  }
}

async function submit() {
  if (!selectedInvoice.value || !(computedDiscountAmount.value > 0) || !reason.value.trim()) return
  submitting.value = true
  error.value = ''
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.doctype.hotel_room_check_in.hotel_room_check_in.apply_discount', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
      body: new URLSearchParams({
        check_in_name: props.checkIn.name,
        discount_amount: computedDiscountAmount.value,
        reason: reason.value,
        source_invoice: selectedInvoice.value.invoice,
      }),
    })
    const data = await res.json()
    if (data.exc) {
      try {
        const msgs = JSON.parse(data._server_messages || '[]')
        error.value = humanizeErrorMessage(JSON.parse(msgs[0]).message || 'Failed to apply discount.')
      } catch {
        error.value = humanizeErrorMessage(data.exception || data._error_message || 'Failed to apply discount.')
      }
      return
    }
    emit('done', data.message)
    emit('close')
  } catch {
    error.value = 'Network error. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
