<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:960px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Bill Transfer</h2>
            <p class="text-xs text-gray-400 mt-1">Move selected charges between guest folios and corporate billing profiles while keeping audit trace intact</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <!-- ─── STEP: FORM ─── -->
        <div v-if="step === 'form'" class="px-8 py-6 space-y-5">

          <!-- Current Billing Context -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4 flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-blue-700 mb-1">Current Billing Context</p>
              <p class="text-xs text-blue-600">{{ checkIn.guest }} • Room {{ checkIn.room_number }} • Outstanding {{ fmt(displayOutstanding) }}</p>
            </div>
            <span class="px-3 py-1 text-xs font-semibold bg-yellow-100 text-yellow-600 rounded-full flex-shrink-0">{{ checkIn.status }}</span>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

            <!-- Transfer Setup -->
            <div class="bg-white rounded-xl border-2 border-blue-300 px-5 py-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Transfer Setup</h3>
              <div class="space-y-4">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Transfer Type</p>
                    <select v-model="transferType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option>Transfer Out</option>
                      <option>Transfer In</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Target Party Type</p>
                    <select v-model="targetPartyType" @change="clearTarget" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option>Corporate</option>
                      <option>Individual Guest</option>
                    </select>
                  </div>
                </div>

                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Target Party <span class="text-red-400">*</span></p>
                  <div class="relative">
                    <input type="text" v-model="targetSearch"
                      @input="searchTargets" @focus="showTargetDropdown = true" @blur="hideTargetDropdown"
                      :placeholder="targetPartyType === 'Corporate' ? 'Search corporate account...' : 'Search in-house guest by name or phone...'"
                      class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      :class="selectedTarget ? 'border-green-300 bg-green-50' : 'border-gray-200'" />
                    <div v-if="showTargetDropdown && targetResults.length > 0"
                      class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
                      <button v-for="t in targetResults" :key="t.name" @mousedown.prevent="selectTarget(t)"
                        class="block w-full text-left px-4 py-2.5 text-xs hover:bg-gray-50 border-b border-gray-50 last:border-0">
                        <span class="font-semibold text-gray-900">{{ t.hotel_guest_name || t.name }}</span>
                        <span v-if="t.phone_number" class="text-gray-400 ml-2">{{ t.phone_number }}</span>
                        <span v-if="t.room_number" class="text-blue-500 ml-2">· Room {{ t.room_number }}</span>
                      </button>
                    </div>
                    <div v-if="showTargetDropdown && targetSearch.length >= 2 && targetResults.length === 0"
                      class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                      <p class="text-xs text-gray-400">{{ targetPartyType === 'Individual Guest' ? 'No in-house guests found matching your search.' : 'No results found.' }}</p>
                    </div>
                    <p v-if="selectedTarget" class="mt-1 text-xs text-green-600 font-medium">✓ {{ selectedTarget.hotel_guest_name || selectedTarget.name }} selected</p>
                  </div>
                </div>

                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Transfer Reason <span class="text-red-400">*</span></p>
                  <select v-model="transferReason" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                    <option value="">Select reason</option>
                    <option>Corporate billing arrangement</option>
                    <option>Guest split billing</option>
                    <option>Management instruction</option>
                    <option>Error correction</option>
                  </select>
                </div>

                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Transfer Note</p>
                  <textarea v-model="transferNote" rows="3"
                    placeholder="Add internal explanation, guest approval, corporate billing note, or finance instruction"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
              </div>
            </div>

            <!-- Invoice Selection -->
            <div class="space-y-4">
              <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <h3 class="text-sm font-bold text-gray-900">Select Invoices to Transfer</h3>
                  <span class="text-xs text-gray-400">{{ selectedInvoices.length }} selected • {{ fmt(transferTotal) }}</span>
                </div>
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-100 bg-gray-50">
                      <th class="px-4 py-3 w-8"></th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Invoice</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Type</th>
                      <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Date</th>
                      <th class="text-right text-xs font-medium text-gray-500 px-3 py-3">Outstanding</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!transferableInvoices || transferableInvoices.length === 0">
                      <td colspan="5" class="px-4 py-6 text-center text-xs text-gray-400">No invoices found for this check-in</td>
                    </tr>
                    <tr v-for="c in transferableInvoices" :key="c.invoice"
                      class="border-b border-gray-50 last:border-0"
                      :class="c.invoice_type === 'POS Invoice' ? 'opacity-40' : 'cursor-pointer hover:bg-gray-50'"
                      @click="c.invoice_type !== 'POS Invoice' && (c.selected = !c.selected)">
                      <td class="px-4 py-3">
                        <input type="checkbox" v-model="c.selected" :disabled="c.invoice_type === 'POS Invoice'"
                          class="accent-blue-600 w-3.5 h-3.5" @click.stop />
                      </td>
                      <td class="px-3 py-3 text-xs font-medium text-blue-600">{{ c.invoice }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ formatInvoiceType(c.invoice_type) }}</td>
                      <td class="px-3 py-3 text-xs text-gray-500">{{ c.posting_date || '—' }}</td>
                      <td class="px-3 py-3 text-xs text-right font-semibold"
                        :class="invoiceOutstanding(c) > 0 ? 'text-red-500' : 'text-gray-400'">
                        {{ fmt(invoiceOutstanding(c)) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Policy Notes -->
              <div class="bg-yellow-50 rounded-xl border border-yellow-200 px-5 py-4">
                <p class="text-xs font-bold text-yellow-700 mb-2">Policy Notes</p>
                <p class="text-xs text-yellow-600">Transfer Out removes selected charges from the active guest folio.</p>
                <p class="text-xs text-yellow-600 mt-1">Transfer In brings selected charges from another party into this current guest folio.</p>
                <p class="text-xs text-yellow-500 mt-1">Only Sales Invoices with outstanding balances can be transferred.</p>
              </div>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-700">{{ errorMsg }}</p>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button @click="$emit('close')"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
            <button @click="submitTransfer" :disabled="submitting"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60">
              {{ submitting ? 'Creating Transfer...' : 'Transfer Charges' }}
            </button>
          </div>
        </div>

        <!-- ─── STEP: PENDING APPROVAL ─── -->
        <div v-else-if="step === 'pending'" class="px-8 py-6 space-y-5">

          <div class="bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-4">
            <p class="text-sm font-bold text-yellow-700 mb-1">Transfer Pending Approval</p>
            <p class="text-xs text-yellow-600">The following bill transfer(s) have been created and are awaiting approval. Click <strong>Approve &amp; Execute</strong> to process the transfers and post the accounting entries.</p>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 bg-gray-50">
                  <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Transfer Ref</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Source Invoice</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">To Guest</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Amount</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in createdTransfers" :key="t.name" class="border-b border-gray-50 last:border-0">
                  <td class="px-5 py-3 text-xs font-medium text-blue-600">{{ t.name }}</td>
                  <td class="px-4 py-3 text-xs text-gray-700">{{ t.invoice }}</td>
                  <td class="px-4 py-3 text-xs text-gray-700">{{ selectedTarget?.hotel_guest_name || selectedTarget?.name }}</td>
                  <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">{{ fmt(t.amount) }}</td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs font-semibold bg-yellow-100 text-yellow-700 rounded-full">Pending Approval</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Error Message -->
          <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-700 whitespace-pre-line">{{ errorMsg }}</p>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button @click="$emit('close')"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Close</button>
            <button @click="approveAndExecute" :disabled="approving"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-60">
              {{ approving ? 'Processing...' : 'Approve & Execute Transfer' }}
            </button>
          </div>
        </div>

        <!-- ─── STEP: DONE ─── -->
        <div v-else-if="step === 'done'" class="px-8 py-12 flex flex-col items-center justify-center space-y-4">
          <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <span class="text-3xl text-green-600">✓</span>
          </div>
          <p class="text-lg font-bold text-gray-900">Transfer Completed</p>
          <p class="text-xs text-gray-500 text-center">Bill transfer(s) have been approved and accounting entries posted successfully.</p>
          <div class="space-y-1.5 w-full max-w-sm">
            <div v-for="t in approvedTransfers" :key="t.name"
              class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5">
              <span class="text-xs font-medium text-gray-700">{{ t.name }}</span>
              <span class="text-xs text-green-600 font-semibold">{{ t.journal_entry || 'JE created' }}</span>
            </div>
          </div>
          <button @click="$emit('close')"
            class="mt-2 px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close</button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { humanizeErrorMessage } from '@/lib/api'

const props = defineProps({ checkIn: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const step = ref('form') // 'form' | 'pending' | 'done'
const transferType = ref('Transfer Out')
const targetPartyType = ref('Corporate')
const transferReason = ref('')
const transferNote = ref('')
const errorMsg = ref('')
const targetSearch = ref('')
const targetResults = ref([])
const selectedTarget = ref(null)
const showTargetDropdown = ref(false)
const submitting = ref(false)
const approving = ref(false)
const createdTransfers = ref([])
const approvedTransfers = ref([])
let searchTimeout = null

function fmt(v) {
  return v || v === 0 ? `₦ ${Number(v).toLocaleString('en-NG', { minimumFractionDigits: 2 })}` : '₦ 0.00'
}

function invoiceOutstanding(invoice) {
  const value = invoice?.net_outstanding_amount ?? invoice?.outstanding_amount ?? 0
  return Math.max(0, Number(value) || 0)
}

function formatInvoiceType(type) {
  if (type === 'Sales Invoice') return 'Room Charge'
  if (type === 'POS Invoice') return 'Restaurant'
  if (type === 'Restaurant') return 'Restaurant'
  return type || 'Room Charge'
}

async function apiPost(method, params) {
  const res = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body: new URLSearchParams(params),
  })
  return res.json()
}

function parseErr(data) {
  try {
    const msgs = JSON.parse(data._server_messages || '[]')
    if (msgs.length) return humanizeErrorMessage(JSON.parse(msgs[0]).message)
  } catch {}
  return humanizeErrorMessage(data.exception || data._error_message || 'Request failed. Please try again.')
}

function clearTarget() {
  selectedTarget.value = null
  targetSearch.value = ''
  targetResults.value = []
}

function searchTargets() {
  selectedTarget.value = null
  clearTimeout(searchTimeout)
  if (targetSearch.value.length < 2) { targetResults.value = []; return }
  searchTimeout = setTimeout(async () => {
    try {
      const guestType = targetPartyType.value === 'Corporate' ? 'Corporate' : 'Individual'
      const isIndividual = targetPartyType.value === 'Individual Guest'
      const data = await apiPost('rhohotel.rhocom_hotel.api.checkin.search_guests', {
        query: targetSearch.value,
        guest_type: guestType,
        in_house_only: isIndividual ? '1' : '0',
      })
      targetResults.value = (data.message || []).filter(g => g.name !== props.checkIn.guest)
    } catch {
      targetResults.value = []
    }
  }, 300)
}

function selectTarget(t) {
  selectedTarget.value = t
  targetSearch.value = t.hotel_guest_name || t.name
  showTargetDropdown.value = false
  targetResults.value = []
}

function hideTargetDropdown() {
  setTimeout(() => { showTargetDropdown.value = false }, 150)
}

// Credit notes (is_return = 1) and zero/negative amounts must not be transferable
const transferableInvoices = computed(() =>
  (props.checkIn.invoices || []).filter(c => (c.amount || 0) > 0 && !c.is_return && invoiceOutstanding(c) > 0)
)

const selectedInvoices = computed(() =>
  transferableInvoices.value
    .filter(c => c.selected && c.invoice_type !== 'POS Invoice')
    .map(c => c.invoice)
)

const transferTotal = computed(() =>
  transferableInvoices.value
    .filter(c => c.selected && c.invoice_type !== 'POS Invoice')
    .reduce((sum, c) => sum + invoiceOutstanding(c), 0)
)

const displayOutstanding = computed(() =>
  props.checkIn.billing_summary?.balance_amount ?? props.checkIn.total_outstanding_amount ?? 0
)

async function submitTransfer() {
  errorMsg.value = ''
  if (!transferReason.value) { errorMsg.value = 'Please select a transfer reason.'; return }
  if (!selectedTarget.value) { errorMsg.value = 'Please select a target party.'; return }
  if (selectedInvoices.value.length === 0) {
    errorMsg.value = 'Please select at least one Sales Invoice to transfer.'
    return
  }

  submitting.value = true
  try {
    const data = await apiPost('rhohotel.rhocom_hotel.api.checkin.create_bill_transfer', {
      from_check_in: props.checkIn.name,
      to_guest: selectedTarget.value.name,
      invoices: JSON.stringify(selectedInvoices.value),
      reason: transferReason.value,
      note: transferNote.value,
    })
    if (data.exc) { errorMsg.value = parseErr(data); return }
    createdTransfers.value = data.message || []
    step.value = 'pending'
  } catch {
    errorMsg.value = 'Failed to create transfer. Please try again.'
  } finally {
    submitting.value = false
  }
}

async function approveAndExecute() {
  errorMsg.value = ''
  approving.value = true
  const results = []
  const errors = []

  for (const transfer of createdTransfers.value) {
    try {
      const data = await apiPost(
        'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.approve_and_execute_transfer',
        { docname: transfer.name }
      )
      if (data.exc) {
        errors.push(`${transfer.name}: ${parseErr(data)}`)
      } else {
        results.push({ ...transfer, journal_entry: data.message?.journal_entry })
      }
    } catch {
      errors.push(`${transfer.name}: Request failed.`)
    }
  }

  approving.value = false
  if (errors.length) errorMsg.value = errors.join('\n')
  if (results.length) {
    approvedTransfers.value = results
    step.value = 'done'
    emit('done')
  }
}
</script>
