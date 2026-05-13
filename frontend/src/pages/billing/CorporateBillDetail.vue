<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <router-link to="/billing/corporate" class="hover:text-gray-600 transition-colors">Corporate Billing</router-link> /
      <span class="text-gray-600">{{ bill.billNo }}</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">{{ bill.billNo }}</h1>
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
        class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Record Payment</button>
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
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const allBills = [
  {
    billNo: 'CBL-000431', client: 'Wells Corporate Services', clientNote: 'Accommodation + conference charges',
    period: 'Mar 2026', issueDate: '18 Apr 2026', dueDate: '02 May 2026',
    amount: '₦1,250,000', balance: '₦1,250,000', status: 'Unpaid',
    charges: [
      { desc: 'Executive Room Accommodation (10 nights × 2 rooms)', date: '01–10 Mar 2026', guests: '2', amount: '₦800,000' },
      { desc: 'Conference Hall Booking (2 days)', date: '05–06 Mar 2026', guests: '—', amount: '₦300,000' },
      { desc: 'Catering & Refreshments', date: '05–06 Mar 2026', guests: '30', amount: '₦150,000' },
    ],
    payments: [],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '18 Apr 2026 • 09:14 AM' },
      { action: 'Payment reminder sent', by: 'System', at: '28 Apr 2026 • 08:00 AM' },
    ],
  },
  {
    billNo: 'CBL-000430', client: 'Rubiconnode Ltd', clientNote: 'Staff lodging invoice batch',
    period: 'Apr 2026', issueDate: '16 Apr 2026', dueDate: '30 Apr 2026',
    amount: '₦920,000', balance: '₦420,000', status: 'Part Paid',
    charges: [
      { desc: 'Standard Room × 4 staff (15 nights)', date: '01–15 Apr 2026', guests: '4', amount: '₦720,000' },
      { desc: 'Breakfast Package (15 days × 4)', date: '01–15 Apr 2026', guests: '4', amount: '₦200,000' },
    ],
    payments: [
      { receipt: 'RCPT-000227', amount: '₦500,000', method: 'Bank Transfer', date: '04 May 2026', reference: 'TXN-0013802' },
    ],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '16 Apr 2026 • 10:30 AM' },
      { action: 'Part payment received — ₦500,000', by: 'Finance Desk', at: '04 May 2026 • 02:15 PM' },
    ],
  },
  {
    billNo: 'CBL-000429', client: 'Herotech Ltd', clientNote: 'Executive room usage billing',
    period: 'Apr 2026', issueDate: '10 Apr 2026', dueDate: '24 Apr 2026',
    amount: '₦640,000', balance: '₦640,000', status: 'Unpaid',
    charges: [
      { desc: 'Executive Suite (8 nights)', date: '01–08 Apr 2026', guests: '1', amount: '₦640,000' },
    ],
    payments: [],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '10 Apr 2026 • 11:00 AM' },
      { action: 'Payment reminder sent', by: 'System', at: '20 Apr 2026 • 08:00 AM' },
    ],
  },
  {
    billNo: 'CBL-000428', client: 'Wells Corporate Services', clientNote: 'February lodging invoice',
    period: 'Feb 2026', issueDate: '20 Mar 2026', dueDate: '03 Apr 2026',
    amount: '₦1,980,000', balance: '₦1,980,000', status: 'Overdue',
    charges: [
      { desc: 'Executive Rooms × 3 (28 nights)', date: 'Feb 2026', guests: '3', amount: '₦1,680,000' },
      { desc: 'Meals & Entertainment', date: 'Feb 2026', guests: '—', amount: '₦300,000' },
    ],
    payments: [],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '20 Mar 2026 • 09:00 AM' },
      { action: 'Payment reminder sent ×2', by: 'System', at: '04 Apr 2026 • 08:00 AM' },
      { action: 'Escalated to accounts manager', by: 'Finance Desk', at: '10 Apr 2026 • 03:00 PM' },
    ],
  },
  {
    billNo: 'CBL-000427', client: 'Accentral Group', clientNote: 'Team stay and transport charges',
    period: 'Apr 2026', issueDate: '15 Apr 2026', dueDate: '29 Apr 2026',
    amount: '₦540,000', balance: '₦240,000', status: 'Part Paid',
    charges: [
      { desc: 'Standard Rooms × 3 (10 nights)', date: 'Apr 2026', guests: '3', amount: '₦420,000' },
      { desc: 'Airport Transfer × 6', date: 'Apr 2026', guests: '6', amount: '₦120,000' },
    ],
    payments: [
      { receipt: 'RCPT-000225', amount: '₦300,000', method: 'Cheque', date: '02 May 2026', reference: 'CHQ-00228' },
    ],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '15 Apr 2026 • 01:45 PM' },
      { action: 'Part payment received — ₦300,000', by: 'Finance Desk', at: '02 May 2026 • 11:00 AM' },
    ],
  },
  {
    billNo: 'CBL-000426', client: 'Fixcenter Services', clientNote: 'Partner accommodation charges',
    period: 'Apr 2026', issueDate: '11 Apr 2026', dueDate: '25 Apr 2026',
    amount: '₦460,000', balance: '₦0.00', status: 'Paid',
    charges: [
      { desc: 'Standard Rooms × 2 (10 nights)', date: 'Apr 2026', guests: '2', amount: '₦460,000' },
    ],
    payments: [
      { receipt: 'RCPT-000223', amount: '₦460,000', method: 'Bank Transfer', date: '30 Apr 2026', reference: 'TXN-0013751' },
    ],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '11 Apr 2026 • 10:00 AM' },
      { action: 'Payment received in full — ₦460,000', by: 'Finance Desk', at: '30 Apr 2026 • 04:00 PM' },
      { action: 'Bill marked as Paid', by: 'System', at: '30 Apr 2026 • 04:01 PM' },
    ],
  },
  {
    billNo: 'CBL-000425', client: 'Herotech Ltd', clientNote: 'Monthly corporate accommodation',
    period: 'Mar 2026', issueDate: '01 Apr 2026', dueDate: '15 Apr 2026',
    amount: '₦780,000', balance: '₦0.00', status: 'Paid',
    charges: [
      { desc: 'Executive Suite (30 nights)', date: 'Mar 2026', guests: '1', amount: '₦780,000' },
    ],
    payments: [
      { receipt: 'RCPT-000218', amount: '₦780,000', method: 'Bank Transfer', date: '14 Apr 2026', reference: 'TXN-0013610' },
    ],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '01 Apr 2026 • 09:00 AM' },
      { action: 'Payment received in full — ₦780,000', by: 'Finance Desk', at: '14 Apr 2026 • 12:00 PM' },
      { action: 'Bill marked as Paid', by: 'System', at: '14 Apr 2026 • 12:01 PM' },
    ],
  },
  {
    billNo: 'CBL-000424', client: 'Rubiconnode Ltd', clientNote: 'Conference and room charges',
    period: 'Mar 2026', issueDate: '28 Mar 2026', dueDate: '11 Apr 2026',
    amount: '₦310,000', balance: '₦310,000', status: 'Overdue',
    charges: [
      { desc: 'Standard Room × 1 (10 nights)', date: 'Mar 2026', guests: '1', amount: '₦180,000' },
      { desc: 'Conference Room (2 half-days)', date: 'Mar 2026', guests: '—', amount: '₦130,000' },
    ],
    payments: [],
    audit: [
      { action: 'Bill created and posted', by: 'Finance Desk', at: '28 Mar 2026 • 10:00 AM' },
      { action: 'Payment reminder sent ×3', by: 'System', at: '12 Apr 2026 • 08:00 AM' },
    ],
  },
]

const bill = computed(() => {
  return allBills.find(b => b.billNo === route.params.id) || allBills[0]
})

function statusBadgeClass(s) {
  return {
    'Unpaid':    'bg-yellow-100 text-yellow-600',
    'Part Paid': 'bg-blue-100 text-blue-600',
    'Paid':      'bg-green-100 text-green-600',
    'Overdue':   'bg-red-100 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>
