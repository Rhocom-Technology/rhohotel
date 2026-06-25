<template>
  <div class="space-y-5">
    <!-- Page Header -->
    <div>
      <!-- <h1 class="text-2xl font-bold text-gray-900">POS Sales Performance</h1> -->
       <div class="flex justify-between items-center gap-3 flex-wrap">
          
        <h1 class="text-2xl font-bold text-gray-900">POS Sales Performance</h1>
       <button
          @click="downloadReport"
          class="bg-green-600 text-white px-4 py-2 rounded-lg">
          Download
        </button>
        </div>
  
      <p class="text-xs text-gray-400 mt-1">
        Comprehensive sales, payments, cashier, shift, room-posting and item performance overview.
      </p>
    </div>

    <!-- Filters Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">From Date</p>
          <input
            v-model="filters.date_from"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:140px;">
          <p class="text-xs text-gray-500 mb-1.5">To Date</p>
          <input
            v-model="filters.date_to"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">POS Profile</p>
          <select
            v-model="filters.pos_profile"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All POS Profiles</option>
            <option v-for="profile in posProfiles" :key="profile" :value="profile">
              {{ profile }}
            </option>
          </select>
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Cashier</p>
          <select
            v-model="filters.cashier"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Cashiers</option>
            <option v-for="cashier in cashiers" :key="cashier" :value="cashier">
              {{ cashier }}
            </option>
          </select>
        </div>

        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Payment Mode</p>
          <select
            v-model="filters.payment_mode"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Payment Modes</option>
            <option v-for="mode in paymentModes" :key="mode" :value="mode">
              {{ mode }}
            </option>
          </select>
        </div>

        <div class="flex-1 min-w-[220px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <div class="relative">
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>

            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search invoice, guest, cashier, item..."
              class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          @click="resetFilters"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>

        <button
          @click="fetchReport"
          :disabled="loading"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Apply' }}
        </button>
      </div>

      <p v-if="errorMessage" class="text-xs text-red-600 mt-3">
        {{ errorMessage }}
      </p>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Gross Sales</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.gross_sales) }}</p>
        <p class="text-[10px] text-blue-600 mt-1">total revenue</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Net Sales</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.net_sales) }}</p>
        <p class="text-[10px] text-green-600 mt-1">after discounts</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Total Orders</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.total_orders) }}</p>
        <p class="text-[10px] text-gray-400 mt-1">transactions</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Average Order Value</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.average_order_value) }}</p>
        <p class="text-[10px] text-indigo-600 mt-1">per transaction</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Discounts</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_discount) }}</p>
        <p class="text-[10px] text-amber-600 mt-1">total given</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.outstanding) }}</p>
        <p class="text-[10px] text-red-600 mt-1">unpaid balance</p>
      </div>
    </div>

    <!-- Payment + Shift Summary -->
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Payment Breakdown</h3>

        <div class="space-y-4">
          <div v-for="row in paymentBreakdown" :key="row.mode">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-medium text-gray-700">{{ row.mode }}</span>
              <span class="text-xs font-bold text-gray-900">₦{{ formatNumber(row.amount) }}</span>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="paymentModeColor(row.mode)"
                :style="{ width: getPercent(row.amount, maxPaymentAmount) + '%' }"
              ></div>
            </div>
          </div>

          <p v-if="!paymentBreakdown.length" class="text-xs text-gray-400">
            No payment data found.
          </p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900">Shift Performance</h3>
          <p class="text-xs text-gray-400">Cashier and shift accountability</p>
        </div>

        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Shift</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Opening</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Closing</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Orders</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Sales</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3.5">Variance</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="shift in filteredShifts"
              :key="shift.name"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs font-mono text-gray-600">{{ shift.name }}</td>
              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ shift.cashier }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500">{{ shift.opening_time }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500">{{ shift.closing_time || 'Open' }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ shift.orders }}</td>
              <td class="px-4 py-3.5 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(shift.sales) }}
              </td>
              <td
                class="px-5 py-3.5 text-xs text-right font-bold"
                :class="Number(shift.variance || 0) < 0 ? 'text-red-600' : 'text-green-600'"
              >
                ₦{{ formatNumber(shift.variance) }}
              </td>
            </tr>

            <tr v-if="!filteredShifts.length">
              <td colspan="7" class="px-5 py-8 text-center text-xs text-gray-400">
                No shift data found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Cashier + Top Items -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Cashier Ranking</h3>

        <div class="space-y-4">
          <div v-for="cashier in cashierPerformance" :key="cashier.cashier">
            <div class="flex items-center justify-between mb-1.5">
              <div>
                <p class="text-xs font-bold text-gray-900">{{ cashier.cashier }}</p>
                <p class="text-[10px] text-gray-400 mt-0.5">{{ cashier.orders }} orders</p>
              </div>
              <p class="text-xs font-bold text-gray-900">₦{{ formatNumber(cashier.sales) }}</p>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-600 rounded-full transition-all"
                :style="{ width: getPercent(cashier.sales, maxCashierSales) + '%' }"
              ></div>
            </div>
          </div>

          <p v-if="!cashierPerformance.length" class="text-xs text-gray-400">
            No cashier data found.
          </p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Top Selling Items</h3>
          <p class="text-xs text-gray-400 mt-0.5">Quantity and revenue</p>
        </div>

        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3">Item</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Category</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Qty</th>
              <th class="text-right text-xs font-medium text-gray-500 px-5 py-3">Revenue</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="item in topItems"
              :key="item.item_code"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ item.item_name }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-500">{{ item.category }}</td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700">{{ item.qty }}</td>
              <td class="px-5 py-3.5 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(item.revenue) }}
              </td>
            </tr>

            <tr v-if="!topItems.length">
              <td colspan="4" class="px-5 py-8 text-center text-xs text-gray-400">
                No item data found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detailed Sales Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Detailed POS Sales</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Invoice-level sales, guest, room posting, payment and cashier details.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedSales.length }} of {{ filteredSales.length }} records
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1200px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>

              <th
                class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer hover:text-gray-700"
                @click="sortBy('invoice')"
              >
                Invoice
                <span v-if="sortKey === 'invoice'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>

              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Date</th>
              <th class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest / Customer</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">POS Profile</th>
              <th class="min-w-[120px] text-left text-xs font-medium text-gray-500 px-4 py-3.5">Payment</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Gross</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Discount</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Tax</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Net</th>
              <th class="min-w-[160px] text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-24">Status</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(sale, index) in paginatedSales"
              :key="sale.invoice"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * Number(pageSize) + index + 1 }}
              </td>

              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="min-w-[160px]">
                  <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                    {{ sale.invoice }}
                  </span>
                </div>
              </td>

              <td class="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">{{ sale.date }}</td>
              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ sale.customer }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ sale.room || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-700">{{ sale.cashier }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ sale.pos_profile }}</td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full bg-gray-100 text-gray-600">
                  {{ sale.payment_mode }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs text-right text-gray-700 whitespace-nowrap">
                ₦{{ formatNumber(sale.gross_amount) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right text-amber-600 whitespace-nowrap">
                ₦{{ formatNumber(sale.discount) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700 whitespace-nowrap">
                ₦{{ formatNumber(sale.tax) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right font-bold text-gray-900 whitespace-nowrap">
                ₦{{ formatNumber(sale.net_amount) }}
              </td>

              <td class="px-5 py-3.5">
                <span
                  class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full"
                  :class="statusClass(sale.status)"
                >
                  {{ sale.status }}
                </span>
              </td>
            </tr>

            <tr v-if="!paginatedSales.length">
              <td colspan="13" class="px-5 py-10 text-center text-xs text-gray-400">
                No sales record found for the selected filters.
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="8" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">
                Total
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(totals.gross_amount) }}
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-amber-600">
                ₦{{ formatNumber(totals.discount) }}
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(totals.tax) }}
              </td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">
                ₦{{ formatNumber(totals.net_amount) }}
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">
          Page {{ currentPage }} of {{ totalPages }}
        </p>

        <div class="flex items-center gap-1">
          <button
            @click="currentPage = 1"
            :disabled="currentPage === 1"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            «
          </button>

          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            ‹
          </button>

          <button
            v-for="page in visiblePages"
            :key="page"
            @click="page !== '...' && (currentPage = page)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="page === currentPage
              ? 'bg-blue-600 text-white font-semibold'
              : page === '...'
                ? 'text-gray-400 cursor-default'
                : 'text-gray-600 hover:bg-gray-50 border border-gray-200'"
          >
            {{ page }}
          </button>

          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            ›
          </button>

          <button
            @click="currentPage = totalPages"
            :disabled="currentPage === totalPages"
            class="w-7 h-7 flex items-center justify-center text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            »
          </button>

          <select
            v-model="pageSize"
            @change="currentPage = 1"
            class="ml-2 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        POS note: Monitor discounts, room posting, cashier variance, unpaid invoices, and shift closure accuracy.
      </p>
      <p class="text-xs text-gray-400">Execution Time: {{ executionTime }} sec</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')
const executionTime = ref('0.0')

const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)

const todayDate = new Date()
const fromDate = new Date()
fromDate.setDate(fromDate.getDate() - 7)

const today = todayDate.toISOString().slice(0, 10)
const weekAgo = fromDate.toISOString().slice(0, 10)

const filters = ref({
  date_from: weekAgo,
  date_to: today,
  pos_profile: '',
  cashier: '',
  payment_mode: '',
})

const sales = ref([])
const shifts = ref([])
const topItemsRaw = ref([])
const posProfiles = ref([])
const cashiers = ref([])
const paymentModes = ref([])

let searchTimer = null
let filterTimer = null

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  const start = performance.now()

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.pos_sales_performance.get_pos_sales_performance_report',
      {
        date_from: filters.value.date_from || '',
        date_to: filters.value.date_to || '',
        pos_profile: filters.value.pos_profile || '',
        cashier: filters.value.cashier || '',
        payment_mode: filters.value.payment_mode || '',
        search: searchQuery.value || '',
      }
    )

    sales.value = result?.sales || []
    shifts.value = result?.shifts || []
    topItemsRaw.value = result?.top_items || []

    posProfiles.value = result?.pos_profiles || []
    cashiers.value = result?.cashiers || []
    paymentModes.value = result?.payment_modes || []

    executionTime.value = ((performance.now() - start) / 1000).toFixed(1)
    currentPage.value = 1
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading POS sales performance report.'

    sales.value = []
    shifts.value = []
    topItemsRaw.value = []
    posProfiles.value = []
    cashiers.value = []
    paymentModes.value = []
  } finally {
    loading.value = false
  }
}

function paymentModeColor(mode) {
  return {
    Cash: 'bg-green-500',
    POS: 'bg-blue-500',
    Transfer: 'bg-purple-500',
    'Room Posting': 'bg-amber-500',
    Unknown: 'bg-gray-500',
  }[mode] || 'bg-gray-900'
}

const filteredSales = computed(() => {
  let rows = sales.value || []

  if (sortKey.value) {
    rows = [...rows].sort((a, b) => {
      const av = a[sortKey.value] ?? ''
      const bv = b[sortKey.value] ?? ''

      const aNum = Number(av)
      const bNum = Number(bv)

      if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
        return sortDir.value === 'asc' ? aNum - bNum : bNum - aNum
      }

      return sortDir.value === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
  }

  return rows
})

const filteredShifts = computed(() => {
  return shifts.value || []
})

const summary = computed(() => {
  const gross = filteredSales.value.reduce((sum, row) => sum + Number(row.gross_amount || 0), 0)
  const net = filteredSales.value.reduce((sum, row) => sum + Number(row.net_amount || 0), 0)
  const discount = filteredSales.value.reduce((sum, row) => sum + Number(row.discount || 0), 0)
  const outstanding = filteredSales.value.reduce((sum, row) => sum + Number(row.outstanding || 0), 0)
  const totalOrders = filteredSales.value.length

  return {
    gross_sales: gross,
    net_sales: net,
    total_orders: totalOrders,
    average_order_value: totalOrders ? net / totalOrders : 0,
    total_discount: discount,
    outstanding,
  }
})

const totals = computed(() => ({
  gross_amount: filteredSales.value.reduce((sum, row) => sum + Number(row.gross_amount || 0), 0),
  discount: filteredSales.value.reduce((sum, row) => sum + Number(row.discount || 0), 0),
  tax: filteredSales.value.reduce((sum, row) => sum + Number(row.tax || 0), 0),
  net_amount: filteredSales.value.reduce((sum, row) => sum + Number(row.net_amount || 0), 0),
}))

const paymentBreakdown = computed(() => {
  const map = {}

  filteredSales.value.forEach(row => {
    const modes = String(row.payment_mode || 'Unknown').split(',')

    modes.forEach(modeRaw => {
      const mode = modeRaw.trim() || 'Unknown'
      map[mode] = (map[mode] || 0) + Number(row.net_amount || 0)
    })
  })

  return Object.entries(map)
    .map(([mode, amount]) => ({ mode, amount }))
    .sort((a, b) => b.amount - a.amount)
})

const cashierPerformance = computed(() => {
  const map = {}

  filteredSales.value.forEach(row => {
    const cashier = row.cashier || 'Unknown'

    if (!map[cashier]) {
      map[cashier] = {
        cashier,
        orders: 0,
        sales: 0,
      }
    }

    map[cashier].orders += 1
    map[cashier].sales += Number(row.net_amount || 0)
  })

  return Object.values(map).sort((a, b) => b.sales - a.sales)
})

const topItems = computed(() => {
  return [...topItemsRaw.value].sort((a, b) => Number(b.revenue || 0) - Number(a.revenue || 0))
})

const maxPaymentAmount = computed(() => {
  return Math.max(...paymentBreakdown.value.map(row => row.amount), 1)
})

const maxCashierSales = computed(() => {
  return Math.max(...cashierPerformance.value.map(row => row.sales), 1)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredSales.value.length / Number(pageSize.value)))
})

const paginatedSales = computed(() => {
  const start = (currentPage.value - 1) * Number(pageSize.value)
  return filteredSales.value.slice(start, start + Number(pageSize.value))
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

watch(filteredSales, () => {
  currentPage.value = 1
})

watch(
  () => ({
    date_from: filters.value.date_from,
    date_to: filters.value.date_to,
    pos_profile: filters.value.pos_profile,
    cashier: filters.value.cashier,
    payment_mode: filters.value.payment_mode,
  }),
  () => {
    clearTimeout(filterTimer)
    filterTimer = setTimeout(() => {
      fetchReport()
    }, 250)
  },
  { deep: true }
)

watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchReport()
  }, 450)
})

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function resetFilters() {
  filters.value = {
    date_from: weekAgo,
    date_to: today,
    pos_profile: '',
    cashier: '',
    payment_mode: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
  fetchReport()
}

function getPercent(value, max) {
  if (!max) return 0
  return Math.min(100, Math.round((Number(value || 0) / Number(max)) * 100))
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-NG', {
    maximumFractionDigits: 0,
  })
}

function statusClass(status) {
  return {
    Paid: 'bg-green-100 text-green-700',
    'Part Payment': 'bg-yellow-100 text-yellow-700',
    Unpaid: 'bg-red-100 text-red-600',
    'Posted to Room': 'bg-blue-100 text-blue-700',
    Return: 'bg-gray-100 text-gray-500',
    Cancelled: 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

onMounted(() => {
  fetchReport()
})

function downloadReport() {
  const params = new URLSearchParams({
    date_from: filters.value.date_from || '',
    date_to: filters.value.date_to || '',
    pos_profile: filters.value.pos_profile || '',
    cashier: filters.value.cashier || '',
    payment_mode: filters.value.payment_mode || '',
    search: searchQuery.value || '',
  })

  window.open(
    `/api/method/rhohotel.rhocom_hotel.api.reports.download_pos_sales_performance_report?${params.toString()}`,
    '_blank'
  )
}
</script>