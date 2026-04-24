<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Monitor live terminals, cashier performance, open tables, draft orders, differences, and revenue trends across POS outlets.</p>
    </div>

    <!-- Live Overview -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Live Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">3 active terminals • 2 outlets • current day trading across restaurant, bar, and mini-mart POS stations</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="$router.push('/pos/invoices')">POS Invoice List</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors" @click="showDraftOrders = true">Open Drafts</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors" @click="$router.push('/pos/staff-roaster')">View Staff Roaster</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Gross POS Sales</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦3.86M</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Draft Orders</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Check</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">7</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Tables</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Shift Differences</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦41,300</p>
      </div>
    </div>

    <!-- Terminal Performance + Manager Watchlist -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

      <!-- Terminal Performance -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Active Terminal Performance</h3>
          <p class="text-xs text-gray-400">Real-time outlet and cashier activity</p>
        </div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Terminal</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Outlet</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Bills</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Sales</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in terminals" :key="t.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ t.name }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.outlet }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.cashier }}</td>
              <td class="px-4 py-4 text-xs text-gray-700">{{ t.bills }}</td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900">{{ t.sales }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                  :class="t.status === 'Online' ? 'bg-green-50 text-green-600' : t.status === 'Closing' ? 'bg-orange-50 text-orange-500' : 'bg-gray-100 text-gray-500'">
                  {{ t.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="px-6 py-3 border-t border-gray-100 bg-gray-50">
          <span class="px-3 py-1.5 text-xs font-medium bg-green-50 text-green-700 rounded-lg">Top cashier today: Adaeze • ₦1.82M</span>
        </div>
      </div>

      <!-- Manager Watchlist -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 flex flex-col gap-3">
        <h3 class="text-sm font-bold text-gray-900">Manager Watchlist</h3>
        <div class="bg-red-50 rounded-lg px-4 py-3">
          <p class="text-xs font-semibold text-red-600 mb-1">Difference Alert</p>
          <p class="text-xs text-gray-500 leading-relaxed">Morning shift closing difference on Mini-Mart POS 03. Difference amount: ₦41,300</p>
        </div>
        <div class="bg-yellow-50 rounded-lg px-4 py-3">
          <p class="text-xs font-semibold text-yellow-600 mb-1">Open Draft Orders</p>
          <p class="text-xs text-gray-500 leading-relaxed">7 draft orders still pending across 2 terminals. 2 belong to restaurant room-posting transactions.</p>
        </div>
        <div class="bg-blue-50 rounded-lg px-4 py-3">
          <p class="text-xs font-semibold text-blue-600 mb-1">Open Tables</p>
          <p class="text-xs text-gray-500 leading-relaxed">14 active tables currently open. 5 tables are ready to bill now.</p>
        </div>
        <div class="flex items-center gap-2 mt-1">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="$router.push('/pos/staff-roaster?view=list')">View Shifts</button>
          <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
            @click="showReviewDifference = true">Review Difference</button>
        </div>
      </div>
    </div>

    <!-- Revenue by Outlet + Quick Manager Actions -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

      <!-- Revenue by Outlet -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Revenue by Outlet</h3>
        <p class="text-xs text-gray-400 mb-4">Current day outlet contribution</p>
        <div v-for="o in outlets" :key="o.name" class="mb-4 last:mb-0">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-medium text-gray-700">{{ o.name }}</span>
            <span class="text-xs font-bold text-gray-900">{{ o.amount }}</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div class="bg-blue-500 h-2 rounded-full" :style="{ width: o.pct + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- Quick Manager Actions -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-1">Quick Manager Actions</h3>
        <p class="text-xs text-gray-400 mb-4">Common intervention tools for POS operations</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;" class="mb-3">
          <button class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            @click="showDraftOrders = true">Open Draft Orders</button>
          <button class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            @click="showOpenTables = true">Review Open Tables</button>
          <button class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            @click="$router.push('/pos/shift-difference-log')">Shift Difference Log</button>
          <button class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            @click="showClosePOS = true">Close POS Terminal</button>
        </div>
        <button class="w-full px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="showGenerateSummary = true">Generate POS Manager Daily Summary</button>
      </div>
    </div>

    <!-- Modals -->
    <DraftOrdersModal v-model="showDraftOrders" />
    <OpenTablesModal v-model="showOpenTables" />
    <ClosePOSTerminalModal v-if="showClosePOS" @close="showClosePOS = false" />
    <GenerateDailySummaryModal v-if="showGenerateSummary" @close="showGenerateSummary = false" />
    <ReviewDifferenceModal v-if="showReviewDifference" @close="showReviewDifference = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'
import OpenTablesModal from '@/components/pos/OpenTablesModal.vue'
import ClosePOSTerminalModal from '@/components/pos/ClosePOSTerminalModal.vue'
import GenerateDailySummaryModal from '@/components/pos/GenerateDailySummaryModal.vue'
import ReviewDifferenceModal from '@/components/pos/ReviewDifferenceModal.vue'

const router = useRouter()

const showDraftOrders = ref(false)
const showOpenTables = ref(false)
const showClosePOS = ref(false)
const showGenerateSummary = ref(false)
const showReviewDifference = ref(false)

const terminals = [
  { name: 'Restaurant POS 01', outlet: 'Main Restaurant', cashier: 'Adaeze', bills: 48, sales: '₦1.82M', status: 'Online' },
  { name: 'Bar POS 02', outlet: 'Bar Lounge', cashier: 'Ifeoma', bills: 31, sales: '₦1.06M', status: 'Online' },
  { name: 'Mini-Mart POS 03', outlet: 'Retail Corner', cashier: 'Boma', bills: 19, sales: '₦980K', status: 'Closing' },
]

const outlets = [
  { name: 'Main Restaurant', amount: '₦1.82M', pct: 100 },
  { name: 'Bar Lounge', amount: '₦1.06M', pct: 58 },
  { name: 'Retail Corner', amount: '₦980K', pct: 54 },
]
</script>