<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Billing / <span class="text-gray-600">Dashboard</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Billing Dashboard</h1>
      <p class="text-xs text-gray-400 mt-1">Manage billing across individual guests and corporate clients with quick access to invoices, payments, folios, statements, and follow-up actions.</p>
    </div>

    <!-- Billing Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-1">Billing Control Center</h3>
      <p class="text-xs text-gray-400 mb-4">Central workspace for guest billing, corporate accounts, group master folios, invoices, receipts, settlements, and aging review.</p>
      <div class="flex items-center justify-end gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Payment List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Invoice List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/billing/corporate')">Corporate Billing</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Invoice</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Individual Guest Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Guest</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦2.14M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Corporate Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Watch</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦6.18M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Invoice Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Posted</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">24</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Unallocated Payments</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">5</p>
      </div>
    </div>

   

    <!-- Activity Feed + Insights -->
    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Billing Activity Feed -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Billing Activity Feed</h3>
        </div>
        <div class="divide-y divide-gray-50">
          <div v-for="a in activityFeed" :key="a.id" class="px-6 py-4 flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold text-gray-900 mb-0.5">{{ a.title }}</p>
              <p class="text-xs text-gray-400">{{ a.desc }}</p>
            </div>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full flex-shrink-0 ml-4"
              :class="feedStatusClass(a.status)">{{ a.status }}</span>
          </div>
        </div>
      </div>

      <!-- Billing Insights -->
      <div class="space-y-3">
        <h3 class="text-sm font-bold text-gray-900">Billing Insights</h3>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Corporate Aging</p>
          <p class="text-xs text-gray-500">Current: ₦2.88M • 1–30 days: ₦1.32M • 31+ days: ₦1.98M</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Corporate Follow-up</p>
          <p class="text-xs text-gray-500">4 corporate invoices need reminders within the next 48 hours.</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-1">Individual Checkout Risk</p>
          <p class="text-xs text-gray-500">7 departures still carry unsettled folio balances.</p>
        </div>

        <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-3 text-center">
          <button class="text-xs font-semibold text-blue-600 hover:underline">Follow up overdue invoices today</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
const activityFeed = [
  { id: 1, title: 'Invoice INV-000481 posted to Wells Corporate Services',    desc: 'Corporate stay batch • ₦1,250,000 • due in 14 days',                          status: 'Unpaid' },
  { id: 2, title: 'Corporate reminder generated for overdue invoice INV-000447', desc: 'Corporate billing follow-up • reminder queued to Wells Corporate Services', status: 'Follow-up' },
  { id: 3, title: 'Guest folio FOL-000921 awaiting checkout settlement',       desc: 'Room 402 • room, minibar, and restaurant posts • ₦184,500 balance',           status: 'Open' },
  { id: 4, title: 'Receipt RCPT-000219 received and awaiting allocation',      desc: 'Bank transfer • ₦750,000 • matched to corporate account',                     status: 'Unapplied' },
]

function feedStatusClass(s) {
  return {
    'Unpaid':    'bg-yellow-50 text-yellow-600',
    'Follow-up': 'bg-yellow-100 text-yellow-700',
    'Open':      'bg-blue-50 text-blue-600',
    'Unapplied': 'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>