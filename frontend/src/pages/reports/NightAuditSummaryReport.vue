<template>
  <div class="space-y-5">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Night Audit Summary Report</h1>
      <p class="text-xs text-gray-400 mt-1">
        Daily revenue, payments, room movement, occupancy, exceptions and audit transaction summary.
      </p>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Audit Date</p>
          <input
            v-model="filters.audit_date"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          />
        </div>

        <div style="min-width:170px;">
          <p class="text-xs text-gray-500 mb-1.5">Revenue Type</p>
          <select
            v-model="filters.revenue_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Revenue</option>
            <option value="Room Revenue">Room Revenue</option>
            <option value="POS Revenue">POS Revenue</option>
            <option value="Other Revenue">Other Revenue</option>
          </select>
        </div>

        <div style="min-width:180px;">
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

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select
            v-model="filters.status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Status</option>
            <option value="Paid">Paid</option>
            <option value="Unpaid">Unpaid</option>
            <option value="Overdue">Overdue</option>
            <option value="Return">Return</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>

        <div class="flex-1 min-w-[240px]">
          <p class="text-xs text-gray-500 mb-1.5">Search</p>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search invoice, guest, room, reservation..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
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

    <!-- Summary Cards -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-blue-500">
        <p class="text-xs text-gray-400 mb-1">Total Revenue</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_revenue) }}</p>
        <p class="text-[10px] text-blue-600 mt-1">gross revenue</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-green-500">
        <p class="text-xs text-gray-400 mb-1">Total Paid</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_paid) }}</p>
        <p class="text-[10px] text-green-600 mt-1">cash received</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-red-500">
        <p class="text-xs text-gray-400 mb-1">Outstanding</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_outstanding) }}</p>
        <p class="text-[10px] text-red-600 mt-1">unpaid balance</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-amber-500">
        <p class="text-xs text-gray-400 mb-1">Discounts</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ formatNumber(summary.total_discount) }}</p>
        <p class="text-[10px] text-amber-600 mt-1">total discount</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-purple-500">
        <p class="text-xs text-gray-400 mb-1">Transactions</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.transaction_count) }}</p>
        <p class="text-[10px] text-purple-600 mt-1">audit records</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 border-l-4 border-l-indigo-500">
        <p class="text-xs text-gray-400 mb-1">Exceptions</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.exceptions_count) }}</p>
        <p class="text-[10px] text-indigo-600 mt-1">audit flags</p>
      </div>
    </div>

    <!-- Room Movement Cards -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Total Rooms</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.total_rooms) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Occupied</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.occupied_rooms) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Vacant</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.vacant_rooms) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Occupancy</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatPercent(summary.occupancy_percent) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Arrivals</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.arrivals) }}</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-1">Departures</p>
        <p class="text-3xl font-bold text-gray-900">{{ formatNumber(summary.departures) }}</p>
      </div>
    </div>

    <!-- Revenue + Payment Breakdown -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Revenue Breakdown</h3>

        <div class="space-y-4">
          <div v-for="row in revenueBreakdown" :key="row.type">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-medium text-gray-700">{{ row.type }}</span>
              <span class="text-xs font-bold text-gray-900">₦{{ formatNumber(row.amount) }}</span>
            </div>

            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="revenueColor(row.type)"
                :style="{ width: getPercent(row.amount, maxRevenueAmount) + '%' }"
              ></div>
            </div>
          </div>

          <p v-if="!revenueBreakdown.length" class="text-xs text-gray-400">
            No revenue breakdown found.
          </p>
        </div>
      </div>

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
            No payment breakdown found.
          </p>
        </div>
      </div>
    </div>

    <!-- Exceptions -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Audit Exceptions</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Outstanding balances, discounts and items requiring audit review.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedExceptions.length }} of {{ exceptions.length }} exceptions
        </p>
      </div>

      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Reference</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Description</th>
            <!-- <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th> -->
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Exception Amount</th>
            <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Amount to be Paid</th>
            <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5">Status</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="item in paginatedExceptions"
            :key="item.type + '-' + item.reference"
            class="border-b border-gray-50 last:border-0 hover:bg-gray-50"
          >
            <td class="px-5 py-3.5 text-xs font-semibold text-gray-900">{{ item.type }}</td>
            <td class="px-4 py-3.5">
              <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                {{ item.reference }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-xs text-gray-600">{{ item.description || '—' }}</td>
            <!-- <td class="px-4 py-3.5 text-xs text-right font-bold text-red-600">
              ₦{{ formatNumber(item.amount) }}
            </td> -->
            <td class="px-4 py-3.5 text-xs text-right font-bold text-red-600">
              ₦{{ formatNumber(item.exception_amount) }}
            </td>
            <td class="px-4 py-3.5 text-xs text-right font-bold text-red-600">
              ₦{{ formatNumber(item.amount_to_be_paid) }}
            </td>
            <td class="px-5 py-3.5">
              <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="statusClass(item.status)">
                {{ item.status || 'Review' }}
              </span>
            </td>
          </tr>

          <tr v-if="!paginatedExceptions.length">
            <td colspan="5" class="px-5 py-8 text-center text-xs text-gray-400">
              No audit exceptions found.
            </td>
          </tr>
        </tbody>
      </table>

      <div class="px-6 py-3 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <p class="text-xs text-gray-400">Page {{ exceptionPage }} of {{ exceptionTotalPages }}</p>

        <div class="flex items-center gap-1">
          <button @click="exceptionPage = 1" :disabled="exceptionPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">«</button>
          <button @click="exceptionPage--" :disabled="exceptionPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">‹</button>
          <button @click="exceptionPage++" :disabled="exceptionPage === exceptionTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">›</button>
          <button @click="exceptionPage = exceptionTotalPages" :disabled="exceptionPage === exceptionTotalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">»</button>
        </div>
      </div>
    </div>

    <!-- Detailed Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Detailed Night Audit Transactions</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            Revenue, payment, room, guest, reservation and outstanding transaction details.
          </p>
        </div>

        <p class="text-xs text-gray-400">
          Showing {{ paginatedRows.length }} of {{ filteredRows.length }} records
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full" style="min-width:1350px;">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5 w-10">No</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
              <th
                class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 cursor-pointer"
                @click="sortBy('reference')"
              >
                Reference
                <span v-if="sortKey === 'reference'">{{ sortDir === 'asc' ? ' ↑' : ' ↓' }}</span>
              </th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[200px]">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5 min-w-[160px]">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5  min-w-[160px]">Reservation</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5  min-w-[160px]">POS Profile</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5  min-w-[180px]">Payment</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Gross</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Tax</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Discount</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Paid</th>
              <th class="text-right text-xs font-medium text-gray-500 px-4 py-3.5">Outstanding</th>
              <th class="text-left text-xs font-medium text-gray-500 px-5 py-3.5  min-w-[160px]">Status</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(row, index) in paginatedRows"
              :key="row.reference + '-' + index"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50"
            >
              <td class="px-5 py-3.5 text-xs text-gray-400">
                {{ (currentPage - 1) * Number(pageSize) + index + 1 }}
              </td>

              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="transactionClass(row.transaction_type)">
                  {{ row.transaction_type }}
                </span>
              </td>

              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="min-w-[150px]">
                  <span class="px-2 py-0.5 text-[10px] font-mono font-medium bg-gray-100 text-gray-600 rounded">
                    {{ row.reference }}
                  </span>
                </div>
              </td>

              <td class="px-4 py-3.5 text-xs font-semibold text-gray-900">{{ row.guest || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.room || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.reservation || '—' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-600">{{ row.pos_profile || '—' }}</td>
              <td class="px-4 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full bg-gray-100 text-gray-600">
                  {{ row.payment_mode || '—' }}
                </span>
              </td>

              <td class="px-4 py-3.5 text-xs text-right text-gray-700 whitespace-nowrap">
                ₦{{ formatNumber(row.gross_amount) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right text-gray-700 whitespace-nowrap">
                ₦{{ formatNumber(row.tax) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right text-amber-600 whitespace-nowrap">
                ₦{{ formatNumber(row.discount) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right text-green-600 whitespace-nowrap">
                ₦{{ formatNumber(row.paid_amount) }}
              </td>
              <td class="px-4 py-3.5 text-xs text-right font-bold text-red-600 whitespace-nowrap">
                ₦{{ formatNumber(row.outstanding_amount) }}
              </td>

              <td class="px-5 py-3.5">
                <span class="px-2.5 py-0.5 text-[10px] font-semibold rounded-full" :class="statusClass(row.status)">
                  {{ row.status }}
                </span>
              </td>
            </tr>

            <tr v-if="!paginatedRows.length">
              <td colspan="14" class="px-5 py-10 text-center text-xs text-gray-400">
                No night audit transaction found for the selected filters.
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr class="border-t-2 border-gray-200 bg-gray-50">
              <td colspan="8" class="px-5 py-4 text-xs font-bold text-gray-900 text-right">Total</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">₦{{ formatNumber(totals.gross_amount) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-gray-900">₦{{ formatNumber(totals.tax) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-amber-600">₦{{ formatNumber(totals.discount) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-green-600">₦{{ formatNumber(totals.paid_amount) }}</td>
              <td class="px-4 py-4 text-xs text-right font-bold text-red-600">₦{{ formatNumber(totals.outstanding_amount) }}</td>
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
          <button @click="currentPage = 1" :disabled="currentPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">«</button>
          <button @click="currentPage--" :disabled="currentPage === 1" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">‹</button>

          <button
            v-for="page in visiblePages"
            :key="page"
            @click="page !== '...' && (currentPage = page)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg"
            :class="page === currentPage ? 'bg-blue-600 text-white font-semibold' : page === '...' ? 'text-gray-400 cursor-default' : 'text-gray-600 hover:bg-gray-50 border border-gray-200'"
          >
            {{ page }}
          </button>

          <button @click="currentPage++" :disabled="currentPage === totalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">›</button>
          <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="w-7 h-7 text-xs border border-gray-200 rounded-lg disabled:opacity-40">»</button>

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

    <div class="flex items-center justify-between">
      <p class="text-xs text-gray-400">
        Night audit note: Review revenue, payments, exceptions, occupancy and unsettled balances before closing the business day.
      </p>
      <p class="text-xs text-gray-400">Audit Date: {{ summary.audit_date || filters.audit_date }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { callMethodForm } from '@/lib/api'

const loading = ref(false)
const errorMessage = ref('')

const todayDate = new Date()
const today = todayDate.toISOString().slice(0, 10)

const filters = ref({
  audit_date: today,
  revenue_type: '',
  pos_profile: '',
  status: '',
})

const searchQuery = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)

const exceptionPage = ref(1)
const exceptionPageSize = ref(10)

const rows = ref([])
const paymentBreakdown = ref([])
const revenueBreakdown = ref([])
const exceptions = ref([])
const posProfiles = ref([])

const summary = ref({
  audit_date: today,
  room_revenue: 0,
  pos_revenue: 0,
  other_revenue: 0,
  total_revenue: 0,
  total_tax: 0,
  total_discount: 0,
  total_paid: 0,
  total_outstanding: 0,
  transaction_count: 0,
  exceptions_count: 0,
  total_rooms: 0,
  occupied_rooms: 0,
  vacant_rooms: 0,
  occupancy_percent: 0,
  arrivals: 0,
  departures: 0,
  stayovers: 0,
})

let searchTimer = null

async function fetchReport() {
  loading.value = true
  errorMessage.value = ''

  try {
    const result = await callMethodForm(
      'rhohotel.rhocom_hotel.api.night_audit_summary_report.get_night_audit_summary_report',
      {
        audit_date: filters.value.audit_date || '',
        revenue_type: filters.value.revenue_type || '',
        pos_profile: filters.value.pos_profile || '',
        status: filters.value.status || '',
        search: searchQuery.value || '',
      }
    )

    rows.value = result?.rows || []
    paymentBreakdown.value = result?.payment_breakdown || []
    revenueBreakdown.value = result?.revenue_breakdown || []
    exceptions.value = result?.exceptions || []
    posProfiles.value = result?.pos_profiles || []
    summary.value = result?.summary || summary.value

    currentPage.value = 1
    exceptionPage.value = 1
  } catch (error) {
    errorMessage.value = error?.message || 'Something went wrong while loading night audit summary report.'
    rows.value = []
    paymentBreakdown.value = []
    revenueBreakdown.value = []
    exceptions.value = []
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  let data = rows.value || []

  if (sortKey.value) {
    data = [...data].sort((a, b) => {
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

  return data
})

const totals = computed(() => ({
  gross_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.gross_amount || 0), 0),
  tax: filteredRows.value.reduce((sum, row) => sum + Number(row.tax || 0), 0),
  discount: filteredRows.value.reduce((sum, row) => sum + Number(row.discount || 0), 0),
  paid_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.paid_amount || 0), 0),
  outstanding_amount: filteredRows.value.reduce((sum, row) => sum + Number(row.outstanding_amount || 0), 0),
}))

const maxRevenueAmount = computed(() => {
  return Math.max(...revenueBreakdown.value.map(row => Number(row.amount || 0)), 1)
})

const maxPaymentAmount = computed(() => {
  return Math.max(...paymentBreakdown.value.map(row => Number(row.amount || 0)), 1)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRows.value.length / Number(pageSize.value)))
})

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * Number(pageSize.value)
  return filteredRows.value.slice(start, start + Number(pageSize.value))
})

const exceptionTotalPages = computed(() => {
  return Math.max(1, Math.ceil(exceptions.value.length / Number(exceptionPageSize.value)))
})

const paginatedExceptions = computed(() => {
  const start = (exceptionPage.value - 1) * Number(exceptionPageSize.value)
  return exceptions.value.slice(start, start + Number(exceptionPageSize.value))
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

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
    audit_date: today,
    revenue_type: '',
    pos_profile: '',
    status: '',
  }

  searchQuery.value = ''
  currentPage.value = 1
  exceptionPage.value = 1

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

function formatPercent(value) {
  return `${Number(value || 0).toLocaleString('en-NG', {
    maximumFractionDigits: 1,
  })}%`
}

function revenueColor(type) {
  return {
    'Room Revenue': 'bg-blue-500',
    'POS Revenue': 'bg-purple-500',
    'Other Revenue': 'bg-gray-500',
    Payment: 'bg-green-500',
  }[type] || 'bg-gray-900'
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

function transactionClass(type) {
  return {
    'Room Revenue': 'bg-blue-100 text-blue-700',
    'POS Revenue': 'bg-purple-100 text-purple-700',
    'Other Revenue': 'bg-gray-100 text-gray-700',
    Payment: 'bg-green-100 text-green-700',
  }[type] || 'bg-gray-100 text-gray-600'
}

function statusClass(status) {
  return {
    Paid: 'bg-green-100 text-green-700',
    Unpaid: 'bg-red-100 text-red-600',
    Overdue: 'bg-red-100 text-red-700',
    'Part Payment': 'bg-yellow-100 text-yellow-700',
    Return: 'bg-gray-100 text-gray-500',
    Cancelled: 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

onMounted(() => {
  fetchReport()
})
</script>