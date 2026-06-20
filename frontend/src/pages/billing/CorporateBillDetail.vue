<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <router-link to="/billing/corporate" class="hover:text-gray-600 transition-colors">Corporate Billing</router-link> /
      <span class="text-gray-600">{{ bill.billNo || route.params.id }}</span>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-10 text-center text-xs text-gray-400">Loading bill…</div>
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-xs text-red-600">{{ error }}</div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">{{ bill.billNo || route.params.id }}</h1>
      <p class="text-xs text-gray-400 mt-1">Corporate bill detail — review charges, payment history, allocation status, and take follow-up or settlement actions.</p>
    </div>

    <!-- Action Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end gap-2">
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        @click="$router.push('/billing/corporate')">Back to List</button>
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Print Bill</button>
      <button v-if="bill.status === 'Overdue' || bill.status === 'Unpaid'"
        class="px-4 py-2 text-xs font-medium text-yellow-700 border border-yellow-200 rounded-lg hover:bg-yellow-50 transition-colors">Send Reminder</button>
      <button v-if="bill.status !== 'Paid'"
        class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        @click="showPaymentModal = true">Record Payment</button>
    </div>

    <!-- Status Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Bill Amount</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Total</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ bill.amount }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Outstanding Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium"
            :class="bill.status === 'Paid' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-500'">
            {{ bill.status === 'Paid' ? 'Cleared' : 'Due' }}
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ bill.balance }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Status</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="statusBadgeClass(bill.status)">{{ bill.status }}</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">{{ bill.status }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Due Date</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Deadline</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">{{ bill.dueDate }}</p>
      </div>
    </div>

    <!-- AI Corporate Bill Summary -->
    <AIInsightPanel
      title="AI Bill Summary"
      context-type="corporate_bill_summary"
      :context-data="billAiContext"
      :auto-load="false"
      panel-id="corporate-bill-detail"
    />

    <!-- Details + Payment History -->
    <div style="display:grid;grid-template-columns:1fr 340px;gap:12px;">

      <!-- Bill Details -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-5">Bill Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Bill Number</p>
              <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.billNo }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Statement Period</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.period }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Client</p>
              <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.client }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Client Note</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.clientNote }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.issueDate }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Due Date</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.dueDate }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Bill Amount</p>
              <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ bill.amount }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Outstanding Balance</p>
              <div class="px-3 py-2.5 text-xs font-bold bg-gray-50 border border-gray-200 rounded-lg"
                :class="bill.balance === '₦0.00' ? 'text-green-600' : 'text-red-500'">{{ bill.balance }}</div>
            </div>
          </div>
        </div>

        <!-- Charge Breakdown -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Charge Breakdown</h3>
          </div>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-6 py-3">Description</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Date</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Guests</th>
                <th class="text-right text-xs font-medium text-gray-500 px-6 py-3">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in bill.charges" :key="c.desc" class="border-b border-gray-50 last:border-0">
                <td class="px-6 py-3.5 text-xs font-medium text-gray-900">{{ c.desc }}</td>
                <td class="px-4 py-3.5 text-xs text-gray-500">{{ c.date }}</td>
                <td class="px-4 py-3.5 text-xs text-gray-500">{{ c.guests }}</td>
                <td class="px-6 py-3.5 text-xs font-semibold text-gray-900 text-right">{{ c.amount }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t-2 border-gray-200 bg-gray-50">
                <td colspan="3" class="px-6 py-3.5 text-xs font-bold text-gray-900">Total</td>
                <td class="px-6 py-3.5 text-xs font-bold text-gray-900 text-right">{{ bill.amount }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Payment History + Audit -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Payment History</h3>
          </div>
          <div v-if="bill.payments.length === 0" class="px-5 py-8 text-center">
            <p class="text-xs text-gray-400">No payments recorded yet.</p>
          </div>
          <div v-else class="divide-y divide-gray-50">
            <div v-for="p in bill.payments" :key="p.receipt" class="px-5 py-4">
              <div class="flex items-center justify-between mb-1">
                <p class="text-xs font-bold text-gray-900">{{ p.receipt }}</p>
                <span class="text-xs font-semibold text-green-600">{{ p.amount }}</span>
              </div>
              <p class="text-xs text-gray-500">{{ p.method }} • {{ p.date }}</p>
              <p class="text-xs text-gray-400 mt-0.5">Ref: {{ p.reference }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Audit Trail</h3>
          <div class="space-y-3">
            <div v-for="a in bill.audit" :key="a.action" class="flex items-start gap-3">
              <div class="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0"></div>
              <div>
                <p class="text-xs font-medium text-gray-800">{{ a.action }}</p>
                <p class="text-xs text-gray-400">{{ a.by }} • {{ a.at }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Record Payment Modal -->
  <Teleport to="body">
    <div v-if="showPaymentModal" class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="showPaymentModal = false">
      <div class="bg-white rounded-2xl w-full shadow-2xl" style="max-width:520px;">

        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-xl font-bold text-gray-900">Record Payment</h2>
            <p class="text-xs text-gray-400 mt-1">{{ bill.billNo }} · Balance: {{ bill.balance }}</p>
          </div>
          <button @click="showPaymentModal = false"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">✕</button>
        </div>

        <div class="px-8 py-6 space-y-4">
          <div v-if="paymentError" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-600">{{ paymentError }}</div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Mode of Payment <span class="text-red-400">*</span></p>
              <select v-model="paymentForm.mode_of_payment"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select mode</option>
                <option v-for="m in paymentModes" :key="m.name" :value="m.name">{{ m.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Amount <span class="text-red-400">*</span></p>
              <input type="number" v-model.number="paymentForm.paid_amount" min="0.01" step="0.01"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Payment Date</p>
              <input type="date" v-model="paymentForm.payment_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference No</p>
              <input type="text" v-model="paymentForm.reference_no" placeholder="Bank / terminal reference"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reference Date</p>
              <input type="date" v-model="paymentForm.reference_date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Remarks</p>
              <input type="text" v-model="paymentForm.remarks" placeholder="Optional note"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              @click="showPaymentModal = false">Cancel</button>
            <button
              :disabled="paymentSubmitting || !paymentForm.mode_of_payment || !(paymentForm.paid_amount > 0)"
              @click="submitPayment"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {{ paymentSubmitting ? 'Processing…' : 'Confirm Payment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { callMethodForm } from '@/lib/api'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const route = useRoute()

const bill = ref({
  billNo: '', client: '', clientNote: '', period: '', issueDate: '', dueDate: '',
  amount: '', balance: '', status: '',
  charges: [], payments: [], audit: [],
})
const loading = ref(false)
const error = ref('')

const billAiContext = computed(() => {
  if (!bill.value.billNo) return null
  return {
    bill_no: bill.value.billNo,
    client: bill.value.client,
    status: bill.value.status,
    amount: bill.value.amount,
    balance: bill.value.balance,
    due_date: bill.value.dueDate,
    issue_date: bill.value.issueDate,
    payment_count: bill.value.payments?.length || 0,
    recent_payments: (bill.value.payments || []).slice(0, 5).map(
      p => ({ date: p.date, amount: p.amount, method: p.method })
    ),
  }
})

async function fetchBill() {
  loading.value = true
  error.value = ''
  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_billing.get_corporate_bill_detail',
      { invoice_name: route.params.id }
    )
    if (result) bill.value = result
  } catch (e) {
    error.value = e.message || 'Failed to load bill'
  } finally {
    loading.value = false
  }
}

// ── Payment modal ──────────────────────────────────────────
const showPaymentModal = ref(false)
const paymentModes = ref([])
const paymentSubmitting = ref(false)
const paymentError = ref('')
const today = new Date().toISOString().slice(0, 10)
const paymentForm = reactive({
  mode_of_payment: '',
  paid_amount: 0,
  payment_date: today,
  reference_no: '',
  reference_date: '',
  remarks: '',
})

async function loadPaymentModes() {
  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_billing.get_payment_modes', {}
    )
    paymentModes.value = result || []
  } catch {
    paymentModes.value = []
  }
}

async function submitPayment() {
  if (!paymentForm.mode_of_payment || !(paymentForm.paid_amount > 0)) return
  paymentSubmitting.value = true
  paymentError.value = ''
  try {
    await callMethodForm(
      'rhohotel.rhocom_hotel.api.corporate_billing.record_corporate_payment',
      {
        invoice_name: route.params.id,
        mode_of_payment: paymentForm.mode_of_payment,
        paid_amount: paymentForm.paid_amount,
        payment_date: paymentForm.payment_date,
        reference_no: paymentForm.reference_no,
        reference_date: paymentForm.reference_date,
        remarks: paymentForm.remarks,
      }
    )
    showPaymentModal.value = false
    paymentForm.mode_of_payment = ''
    paymentForm.paid_amount = 0
    paymentForm.reference_no = ''
    paymentForm.reference_date = ''
    paymentForm.remarks = ''
    await fetchBill()
  } catch (e) {
    paymentError.value = e.message || 'Failed to record payment'
  } finally {
    paymentSubmitting.value = false
  }
}

function statusBadgeClass(s) {
  return {
    'Unpaid':    'bg-yellow-100 text-yellow-600',
    'Part Paid': 'bg-blue-100 text-blue-600',
    'Paid':      'bg-green-100 text-green-600',
    'Overdue':   'bg-red-100 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

onMounted(() => {
  fetchBill()
  loadPaymentModes()
})
</script>
