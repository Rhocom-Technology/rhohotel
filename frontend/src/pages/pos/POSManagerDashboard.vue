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
        <p class="text-3xl font-bold text-gray-900">₦{{ dashResource.loading ? '…' : Number(dashStats.gross_sales).toLocaleString() }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Draft Orders</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Check</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ dashResource.loading ? '…' : dashStats.open_drafts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Tables</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">—</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Shift Differences</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦{{ dashResource.loading ? '…' : Number(dashStats.shift_differences).toLocaleString() }}</p>
      </div>
    </div>

    <!-- AI POS Operations Summary -->
    <AIInsightPanel
      v-if="dashResource.data"
      title="AI POS Operations Summary"
      context-type="pos_shift_close_summary"
      :context-data="posDashAiContext"
      :auto-load="false"
      panel-id="pos-manager-dashboard"
    />

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

    <!-- Closed Shifts History -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Closed Shifts</h3>
          <p class="text-xs text-gray-400 mt-0.5">Recent shift closing records — click a shift ID to view details</p>
        </div>
        <button @click="fetchClosedShifts" class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Refresh</button>
      </div>

      <!-- Filters -->
      <div class="px-6 py-4 border-b border-gray-100 bg-gray-50">
        <div class="flex items-end gap-3 flex-wrap">
          <div>
            <p class="text-xs text-gray-500 mb-1">From</p>
            <input v-model="shiftFilter.dateFrom" type="date"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">To</p>
            <input v-model="shiftFilter.dateTo" type="date"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Terminal</p>
            <select v-model="shiftFilter.terminal"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white">
              <option value="">All Terminals</option>
              <option v-for="t in shiftFilterOptions.terminals" :key="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">Cashier</p>
            <select v-model="shiftFilter.cashier"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white">
              <option value="">All Cashiers</option>
              <option v-for="c in shiftFilterOptions.cashiers" :key="c">{{ c }}</option>
            </select>
          </div>
          <div class="flex items-center gap-1.5 pb-0.5">
            <input id="hasAttach" v-model="shiftFilter.hasAttachment" type="checkbox"
              class="w-3.5 h-3.5 accent-blue-600 cursor-pointer" />
            <label for="hasAttach" class="text-xs text-gray-600 cursor-pointer select-none">Has attachment</label>
          </div>
          <button @click="fetchClosedShifts"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Apply</button>
          <button @click="resetShiftFilters"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        </div>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Closing Entry</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Terminal</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Net Total</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Attachment</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="closedShiftsResource.loading">
            <td colspan="6" class="text-center py-8 text-xs text-gray-400">Loading…</td>
          </tr>
          <tr v-else-if="closedShifts.length === 0">
            <td colspan="6" class="text-center py-8 text-xs text-gray-400">No closed shifts found</td>
          </tr>
          <tr v-for="s in closedShifts" :key="s.name"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-3.5">
              <button @click="openShiftDetail(s.name)"
                class="text-xs font-bold text-blue-600 hover:text-blue-800 hover:underline transition-colors">
                {{ s.name }}
              </button>
            </td>
            <td class="px-4 py-3.5 text-xs text-gray-600">{{ s.posting_date }}</td>
            <td class="px-4 py-3.5 text-xs text-gray-600">{{ s.pos_profile || '—' }}</td>
            <td class="px-4 py-3.5 text-xs text-gray-600">{{ s.cashier }}</td>
            <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">₦{{ Number(s.net_total || 0).toLocaleString() }}</td>
            <td class="px-4 py-3.5">
              <a v-if="s.file_url" :href="s.file_url" target="_blank"
                class="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium rounded-lg hover:bg-blue-100 transition-colors max-w-[180px] truncate">
                <svg class="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
                {{ s.file_name }}
              </a>
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Shift Detail Modal -->
    <Teleport to="body">
      <div v-if="showShiftDetail" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.5);" @click.self="showShiftDetail = false">
        <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h3 class="text-sm font-bold text-gray-900">{{ shiftDetail?.name || '…' }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">{{ shiftDetail?.pos_profile }} • {{ shiftDetail?.posting_date }}</p>
            </div>
            <button @click="showShiftDetail = false" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <div v-if="shiftDetailResource.loading" class="px-6 py-12 text-center text-xs text-gray-400">Loading…</div>

          <div v-else-if="shiftDetail" class="px-6 py-5 space-y-5">

            <!-- Key Metrics -->
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
              <div class="bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Net Total</p>
                <p class="text-lg font-bold text-gray-900">₦{{ Number(shiftDetail.net_total || 0).toLocaleString() }}</p>
              </div>
              <div class="bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Gross Total</p>
                <p class="text-lg font-bold text-gray-900">₦{{ Number(shiftDetail.grand_total || 0).toLocaleString() }}</p>
              </div>
              <div class="bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Bills</p>
                <p class="text-lg font-bold text-gray-900">{{ shiftDetail.bills_processed }}</p>
              </div>
              <div class="bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
                <p class="text-xs text-gray-400 mb-1">Voids</p>
                <p class="text-lg font-bold text-gray-900">{{ shiftDetail.voided_count }}</p>
              </div>
            </div>

            <!-- Shift Info -->
            <div class="bg-gray-50 rounded-xl border border-gray-100 p-4">
              <h4 class="text-xs font-bold text-gray-700 mb-3">Shift Info</h4>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-gray-400">Cashier</span>
                  <span class="font-medium text-gray-800">{{ shiftDetail.user }}</span>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span class="text-gray-400">Terminal</span>
                  <span class="font-medium text-gray-800">{{ shiftDetail.pos_profile }}</span>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span class="text-gray-400">Period Start</span>
                  <span class="font-medium text-gray-800">{{ formatDateTime(shiftDetail.period_start_date) }}</span>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span class="text-gray-400">Period End</span>
                  <span class="font-medium text-gray-800">{{ formatDateTime(shiftDetail.period_end_date) }}</span>
                </div>
              </div>
            </div>

            <!-- Payment Breakdown -->
            <div>
              <h4 class="text-xs font-bold text-gray-700 mb-2">Payment Breakdown</h4>
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100">
                    <th class="text-left text-xs font-medium text-gray-400 pb-2">Method</th>
                    <th class="text-right text-xs font-medium text-gray-400 pb-2">Opening</th>
                    <th class="text-right text-xs font-medium text-gray-400 pb-2">Expected</th>
                    <th class="text-right text-xs font-medium text-gray-400 pb-2">Closing</th>
                    <th class="text-right text-xs font-medium text-gray-400 pb-2">Diff</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="p in shiftDetail.payments" :key="p.mode_of_payment">
                    <td class="py-2 text-xs font-medium text-gray-800">{{ p.mode_of_payment }}</td>
                    <td class="py-2 text-right text-xs text-gray-500">₦{{ Number(p.opening_amount||0).toLocaleString() }}</td>
                    <td class="py-2 text-right text-xs text-gray-700">₦{{ Number(p.expected_amount||0).toLocaleString() }}</td>
                    <td class="py-2 text-right text-xs font-semibold text-gray-900">₦{{ Number(p.closing_amount||0).toLocaleString() }}</td>
                    <td class="py-2 text-right text-xs font-semibold"
                      :class="Number(p.difference||0) === 0 ? 'text-green-600' : 'text-red-500'">
                      {{ Number(p.difference||0) === 0 ? '—' : (Number(p.difference)>0?'+':'') + '₦' + Math.abs(Number(p.difference)).toLocaleString() }}
                    </td>
                  </tr>
                  <tr v-if="!shiftDetail.payments?.length">
                    <td colspan="5" class="py-4 text-center text-xs text-gray-300">No payment data</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Attachment -->
            <div v-if="shiftDetail.attachment" class="flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
              <a :href="shiftDetail.attachment.file_url" target="_blank"
                class="text-xs text-blue-600 hover:underline truncate max-w-xs">
                {{ shiftDetail.attachment.file_name }}
              </a>
            </div>

          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end">
            <button @click="showShiftDetail = false"
              class="px-5 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Close</button>
          </div>

        </div>
      </div>
    </Teleport>

    <!-- Modals -->
    <DraftOrdersModal v-model="showDraftOrders" />
    <OpenTablesModal v-model="showOpenTables" />
    <ClosePOSTerminalModal v-if="showClosePOS" @close="showClosePOS = false" />
    <GenerateDailySummaryModal v-if="showGenerateSummary" @close="showGenerateSummary = false" />
    <ReviewDifferenceModal v-if="showReviewDifference" @close="showReviewDifference = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import DraftOrdersModal from '@/components/pos/DraftOrdersModal.vue'
import OpenTablesModal from '@/components/pos/OpenTablesModal.vue'
import ClosePOSTerminalModal from '@/components/pos/ClosePOSTerminalModal.vue'
import GenerateDailySummaryModal from '@/components/pos/GenerateDailySummaryModal.vue'
import ReviewDifferenceModal from '@/components/pos/ReviewDifferenceModal.vue'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const router = useRouter()

const showDraftOrders = ref(false)
const showOpenTables = ref(false)
const showClosePOS = ref(false)
const showGenerateSummary = ref(false)
const showReviewDifference = ref(false)

// ── API: Dashboard Stats ───────────────────────────────────────────
const dashResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_dashboard_stats',
  auto: true,
})

const dashStats = computed(() => {
  const d = dashResource.data || {}
  return {
    gross_sales: Number(d.gross_sales || 0),
    open_drafts: Number(d.open_drafts || 0),
    shift_differences: Number(d.shift_differences || 0),
  }
})

const terminals = computed(() =>
  (dashResource.data?.terminals || []).map(t => ({
    name: t.terminal_name || t.name || '—',
    outlet: t.terminal_name || '—',
    cashier: t.cashier || '—',
    bills: t.bills || 0,
    sales: `₦${Number(t.sales || 0).toLocaleString()}`,
    status: 'Online',
  }))
)

const outlets = computed(() =>
  (dashResource.data?.outlet_revenue || []).map(o => ({
    name: o.outlet,
    amount: `₦${Number(o.amount).toLocaleString()}`,
    pct: o.pct || 0,
  }))
)

// ── API: Closed Shifts ────────────────────────────────────────────
const shiftFilter = ref({ dateFrom: '', dateTo: '', terminal: '', cashier: '', hasAttachment: false })
const shiftFilterOptions = ref({ terminals: [], cashiers: [] })

const closedShiftsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_closed_shifts',
  auto: true,
  onSuccess(data) {
    if (data?.terminals) shiftFilterOptions.value.terminals = data.terminals
    if (data?.cashiers) shiftFilterOptions.value.cashiers = data.cashiers
  },
})

const closedShifts = computed(() =>
  ((closedShiftsResource.data?.rows) || []).map(s => ({
    name: s.name,
    posting_date: s.posting_date || '—',
    pos_profile: s.pos_profile || '—',
    cashier: s.user || '—',
    net_total: s.net_total || 0,
    file_name: s.file_name || null,
    file_url: s.file_url || null,
  }))
)

const posDashAiContext = computed(() => {
  if (!dashResource.data) return null
  return {
    gross_sales: dashStats.value.gross_sales,
    open_drafts: dashStats.value.open_drafts,
    shift_differences: dashStats.value.shift_differences,
    active_terminals: terminals.value.slice(0, 5).map(t => ({
      name: t.name, cashier: t.cashier, bills: t.bills, sales: t.sales,
    })),
    outlet_revenue: outlets.value.slice(0, 5).map(o => ({
      outlet: o.name, amount: o.amount, pct: o.pct,
    })),
  }
})

function fetchClosedShifts() {
  const f = shiftFilter.value
  closedShiftsResource.params = {
    date_from: f.dateFrom || null,
    date_to: f.dateTo || null,
    terminal: f.terminal || null,
    cashier: f.cashier || null,
    has_attachment: f.hasAttachment ? 1 : null,
  }
  closedShiftsResource.reload()
}

function resetShiftFilters() {
  shiftFilter.value = { dateFrom: '', dateTo: '', terminal: '', cashier: '', hasAttachment: false }
  closedShiftsResource.params = {}
  closedShiftsResource.reload()
}

// ── Shift Detail Modal ────────────────────────────────────────────
const showShiftDetail = ref(false)
const shiftDetail = ref(null)

const shiftDetailResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_closed_shift_detail',
  onSuccess(data) {
    shiftDetail.value = data
  },
})

function openShiftDetail(name) {
  shiftDetail.value = null
  showShiftDetail.value = true
  shiftDetailResource.submit({ closing_entry: name })
}

function formatDateTime(val) {
  if (!val) return '—'
  const d = new Date(String(val).replace(' ', 'T'))
  if (isNaN(d)) return String(val)
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true })
}
</script>