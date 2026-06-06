<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')"
    >
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:860px;max-height:92vh;">
        <div class="px-7 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Corporate Bill Transfer</h2>
            <p class="text-xs text-gray-400 mt-1">Move selected reservation invoice balances to a corporate account.</p>
          </div>
          <button
            @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm"
          >x</button>
        </div>

        <div v-if="step === 'form'" class="px-7 py-6 space-y-5">
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
            <p class="text-sm font-bold text-blue-700">{{ reservation.name }}</p>
            <p class="text-xs text-blue-600 mt-1">{{ reservation.primary_guest_name || reservation.customer || 'Reservation' }} - Outstanding {{ fmt(totalOutstanding) }}</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Corporate Account</p>
                <div class="relative">
                  <input
                    v-model="targetSearch"
                    type="text"
                    placeholder="Search corporate account..."
                    class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    :class="selectedTarget ? 'border-green-300 bg-green-50' : 'border-gray-200'"
                    @input="searchTargets"
                    @focus="showTargetDropdown = true"
                    @blur="hideTargetDropdown"
                  />
                  <div
                    v-if="showTargetDropdown && targetResults.length"
                    class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto"
                  >
                    <button
                      v-for="target in targetResults"
                      :key="target.name"
                      type="button"
                      class="block w-full text-left px-4 py-2.5 text-xs hover:bg-gray-50 border-b border-gray-50 last:border-0"
                      @mousedown.prevent="selectTarget(target)"
                    >
                      <span class="font-semibold text-gray-900">{{ target.hotel_guest_name || target.name }}</span>
                      <span v-if="target.phone_number" class="text-gray-400 ml-2">{{ target.phone_number }}</span>
                    </button>
                  </div>
                </div>
                <p v-if="selectedTarget" class="mt-1 text-xs text-green-600 font-medium">{{ selectedTarget.hotel_guest_name || selectedTarget.name }} selected</p>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Transfer Reason</p>
                <select v-model="transferReason" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">Select reason</option>
                  <option>Corporate billing arrangement</option>
                  <option>Management instruction</option>
                  <option>Error correction</option>
                </select>
              </div>

              <div>
                <p class="text-xs text-gray-500 mb-1.5">Transfer Note</p>
                <textarea
                  v-model="transferNote"
                  rows="4"
                  placeholder="Add internal note"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                ></textarea>
              </div>
            </div>

            <div class="border border-gray-200 rounded-xl overflow-hidden">
              <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                <h3 class="text-sm font-bold text-gray-900">Outstanding Invoices</h3>
                <span class="text-xs text-gray-400">{{ selectedInvoices.length }} selected</span>
              </div>
              <table class="w-full">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 w-8"></th>
                    <th class="text-left text-xs font-medium text-gray-500 px-2 py-2">Invoice</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="transferableInvoices.length === 0">
                    <td colspan="3" class="px-3 py-8 text-center text-xs text-gray-400">No outstanding reservation invoices found.</td>
                  </tr>
                  <tr
                    v-for="invoice in transferableInvoices"
                    :key="invoice.name"
                    class="border-t border-gray-100 cursor-pointer hover:bg-gray-50"
                    @click="invoice.selected = !invoice.selected"
                  >
                    <td class="px-3 py-2">
                      <input v-model="invoice.selected" type="checkbox" class="accent-blue-600 w-3.5 h-3.5" @click.stop />
                    </td>
                    <td class="px-2 py-2 text-xs font-medium text-blue-600">{{ invoice.name }}</td>
                    <td class="px-3 py-2 text-xs text-right font-semibold text-red-500">{{ fmt(invoiceOutstanding(invoice)) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-700 whitespace-pre-line">{{ errorMsg }}</p>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button @click="$emit('close')" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button
              :disabled="submitting"
              @click="submitTransfer"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-60"
            >{{ submitting ? 'Creating...' : 'Create Transfer' }}</button>
          </div>
        </div>

        <div v-else class="px-7 py-6 space-y-5">
          <div class="bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
            <p class="text-sm font-bold text-yellow-700">Transfer Pending Approval</p>
            <p class="text-xs text-yellow-600 mt-1">Approve and execute to post the accounting entries.</p>
          </div>

          <div class="border border-gray-200 rounded-xl overflow-hidden">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-2">Transfer</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Invoice</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-3 py-2">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="transfer in createdTransfers" :key="transfer.name" class="border-t border-gray-100">
                  <td class="px-4 py-2 text-xs font-medium text-blue-600">{{ transfer.name }}</td>
                  <td class="px-3 py-2 text-xs text-gray-700">{{ transfer.invoice }}</td>
                  <td class="px-3 py-2 text-xs text-right font-semibold text-gray-900">{{ fmt(transfer.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p class="text-xs text-red-700 whitespace-pre-line">{{ errorMsg }}</p>
          </div>

          <div class="flex items-center justify-end gap-2">
            <button @click="$emit('close')" class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close</button>
            <button
              :disabled="approving"
              @click="approveAndExecute"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-60"
            >{{ approving ? 'Processing...' : 'Approve & Execute' }}</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref } from 'vue'
import { callMethod } from '@/lib/api'

const props = defineProps({ reservation: { type: Object, required: true } })
const emit = defineEmits(['close', 'done'])

const step = ref('form')
const targetSearch = ref('')
const targetResults = ref([])
const selectedTarget = ref(null)
const showTargetDropdown = ref(false)
const transferReason = ref('')
const transferNote = ref('')
const errorMsg = ref('')
const submitting = ref(false)
const approving = ref(false)
const createdTransfers = ref([])
let searchTimeout = null

function fmt(value) {
  return `₦${Number(value || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

function invoiceOutstanding(invoice) {
  return Math.max(0, Number(invoice?.outstanding_amount || 0))
}

const transferableInvoices = computed(() =>
  (props.reservation?.reservation_invoices || props.reservation?.linked_invoices || [])
    .filter((invoice) => !Number(invoice?.is_return || 0) && invoiceOutstanding(invoice) > 0)
)

const selectedInvoices = computed(() =>
  transferableInvoices.value.filter((invoice) => invoice.selected).map((invoice) => invoice.name)
)

const totalOutstanding = computed(() =>
  transferableInvoices.value.reduce((sum, invoice) => sum + invoiceOutstanding(invoice), 0)
)

function hideTargetDropdown() {
  setTimeout(() => { showTargetDropdown.value = false }, 150)
}

function selectTarget(target) {
  selectedTarget.value = target
  targetSearch.value = target.hotel_guest_name || target.name
  targetResults.value = []
  showTargetDropdown.value = false
}

function searchTargets() {
  selectedTarget.value = null
  clearTimeout(searchTimeout)
  if (targetSearch.value.length < 2) {
    targetResults.value = []
    return
  }
  searchTimeout = setTimeout(async () => {
    try {
      const rows = await callMethod('rhohotel.rhocom_hotel.api.checkin.search_guests', {
        query: targetSearch.value,
        guest_type: 'Corporate',
        in_house_only: '0',
      })
      targetResults.value = rows || []
    } catch {
      targetResults.value = []
    }
  }, 300)
}

async function submitTransfer() {
  errorMsg.value = ''
  if (!selectedTarget.value) {
    errorMsg.value = 'Please select a corporate account.'
    return
  }
  if (!transferReason.value) {
    errorMsg.value = 'Please select a transfer reason.'
    return
  }
  if (!selectedInvoices.value.length) {
    errorMsg.value = 'Please select at least one invoice.'
    return
  }

  submitting.value = true
  try {
    createdTransfers.value = await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.create_bill_transfer_for_reservation',
      {
        reservation_name: props.reservation.name,
        to_guest: selectedTarget.value.name,
        invoices: selectedInvoices.value,
        reason: transferReason.value,
        note: transferNote.value,
      },
    )
    step.value = 'pending'
  } catch (error) {
    errorMsg.value = error?.message || 'Could not create bill transfer.'
  } finally {
    submitting.value = false
  }
}

async function approveAndExecute() {
  errorMsg.value = ''
  approving.value = true
  const errors = []
  for (const transfer of createdTransfers.value) {
    try {
      await callMethod(
        'rhohotel.rhocom_hotel.doctype.bill_transfer.bill_transfer.approve_and_execute_transfer',
        { docname: transfer.name },
      )
    } catch (error) {
      errors.push(`${transfer.name}: ${error?.message || 'Request failed.'}`)
    }
  }
  approving.value = false
  if (errors.length) {
    errorMsg.value = errors.join('\n')
    return
  }
  emit('done')
}
</script>
