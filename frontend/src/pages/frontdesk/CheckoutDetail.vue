<template>
  <div class="space-y-5">

    <!-- Guest Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-start gap-3 mb-2 flex-wrap">
        <h2 class="text-2xl font-bold text-gray-900">OGUMBA WAYNE</h2>
        <span class="px-3 py-1 text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-200 rounded-full">Room 8408</span>
        <span class="px-3 py-1 text-xs font-semibold bg-red-50 text-red-500 border border-red-200 rounded-full">Balance ₦41,000</span>
      </div>
      <p class="text-xs text-gray-400 mb-3">Executive Room • Check-in 21 Feb 2026 09:27 • Due out 24 Feb 2026 12:00 • 3 nights • Walk-in</p>
      <div class="flex items-center gap-3">
        <p class="text-xs text-gray-500 font-medium">Check-in Reference ID</p>
        <input type="text" class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" style="min-width:200px;" />
      </div>
    </div>

    <!-- Stat Cards -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Total Charges</p>
        <p class="text-3xl font-bold text-gray-900">₦342,000</p>
        <p class="text-xs text-blue-500 font-medium mt-1">Room, F&B, laundry, incidentals</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Amount Paid</p>
        <p class="text-3xl font-bold text-gray-900">₦300,000</p>
        <p class="text-xs text-green-600 font-medium mt-1">Payments received</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-3xl font-bold text-red-500">₦41,000</p>
        <p class="text-xs text-red-400 font-medium mt-1">Must settle before departure</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Departure Checklist</p>
        <p class="text-sm font-bold text-gray-900 mt-1">Payment, key return, room inspection, and folio</p>
        <p class="text-xs text-gray-400 mt-1">Front desk closes stay only after all controls are complete.</p>
      </div>
    </div>

    <!-- Main Content -->
    <div style="display:grid;grid-template-columns:1fr 380px;gap:12px;">

      <!-- Left: Stay and Settlement Details -->
      <div class="space-y-5">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Stay and Settlement Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-5">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">OGUMBA WAYNE</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">8408 • Executive Room</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-in Time</p>
              <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">21 Feb 2026 09:27</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-out Time</p>
              <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">24 Feb 2026 12:00</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Length of Stay</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">3 Nights</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Payment Status</p>
              <div class="px-3 py-2.5 text-xs font-semibold text-red-500 bg-red-50 border border-red-200 rounded-lg">Outstanding balance remains</div>
            </div>
          </div>

          <!-- Charge Breakdown -->
          <h3 class="text-sm font-bold text-gray-900 mb-3">Charge Breakdown</h3>
          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 bg-gray-50">
                  <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Charge</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Date</th>
                  <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in charges" :key="c.name" class="border-b border-gray-50 last:border-0">
                  <td class="px-5 py-3 text-xs" :class="c.name === 'Total Charges' ? 'font-bold text-gray-900' : 'text-gray-700'">{{ c.name }}</td>
                  <td class="px-4 py-3 text-xs text-gray-500">{{ c.date }}</td>
                  <td class="px-5 py-3 text-xs text-right" :class="c.name === 'Total Charges' ? 'font-bold text-gray-900' : 'text-gray-700'">{{ c.amount }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Departure Notes -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Departure Notes</h3>
          <textarea rows="4"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Add room status note, minibar confirmation, laundry release, or guest departure comment"></textarea>
        </div>
      </div>

      <!-- Right: Checkout Control Panel -->
      <div class="space-y-5">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-5">
          <h3 class="text-sm font-bold text-gray-900">Checkout Control Panel</h3>

          <!-- Alert -->
          <div class="bg-red-50 rounded-xl border border-red-200 px-4 py-4">
            <p class="text-xs font-bold text-red-600 mb-1">Outstanding Balance Alert</p>
            <p class="text-xs text-red-500 leading-relaxed">Guest still owes ₦41,000. Receive payment or transfer approved charges before completing checkout. Checkout completion should remain blocked until settlement is resolved.</p>
          </div>

          <!-- Payment Entries -->
          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-3">Payment Entries</h4>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Payment Entry</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-3 py-3">Date</th>
                    <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Paid</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-gray-50">
                    <td class="px-4 py-3 text-xs text-gray-700">ACC-PAY-2026-01066</td>
                    <td class="px-3 py-3 text-xs text-gray-500">21 Feb</td>
                    <td class="px-4 py-3 text-xs text-right font-semibold text-gray-900">₦300,000</td>
                  </tr>
                  <tr>
                    <td class="px-4 py-3 text-xs font-bold text-gray-900">Total Paid</td>
                    <td></td>
                    <td class="px-4 py-3 text-xs text-right font-bold text-gray-900">₦300,000</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Departure Checklist -->
          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-3">Departure Checklist</h4>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-3">
              <label v-for="item in checklist" :key="item" class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="checked[item]" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">{{ item }}</span>
              </label>
            </div>
          </div>

          <!-- Quick Actions -->
          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-3">Quick Actions</h4>
            <div class="flex items-center gap-2 flex-wrap">
              <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Receive Payment</button>
              <button class="px-4 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Bill Transfer</button>
              <button class="flex-1 px-4 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">Finalize Check-out</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'

const charges = [
  { name: 'Room Charge',     date: '21 Feb', amount: '₦300,000' },
  { name: 'Restaurant Bill', date: '22 Feb', amount: '₦18,000' },
  { name: 'Laundry',         date: '22 Feb', amount: '₦6,000' },
  { name: 'Total Charges',   date: '',       amount: '₦342,000' },
]

const checklist = [
  'Receive final outstanding payment',
  'Confirm room key returned or deactivated',
  'Confirm housekeeping / minibar / laundry sign-off',
  'Close folio and issue final receipt',
]
const checked = ref({})
</script>