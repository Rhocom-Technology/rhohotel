<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Manage complimentary room nights, food vouchers, airport transfers, upgrades, amenities, approvals, and usage tracking.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Complimentary Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">19 active complimentary items • 6 pending approvals • 4 consumed today • 2 expired unused</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/complimentary/list')">Complimentary List</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Export Register</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/complimentary/new')">New Complimentary</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Issued Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Approval</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Waiting</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">6</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Consumed Today</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Used</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">4</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Budget Impact</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦286K</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search guest, voucher, approval..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Types</option>
          <option>Food Voucher</option>
          <option>Airport Transfer</option>
          <option>Room Upgrade</option>
          <option>Amenity</option>
          <option>Late Checkout</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Approved</option>
          <option>Pending</option>
          <option>In Progress</option>
          <option>Consumed</option>
        </select>
        <select v-model="filterDept" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Departments</option>
          <option>Restaurant</option>
          <option>Front Desk</option>
          <option>Housekeeping</option>
          <option>GM Office</option>
        </select>
        <button @click="search='';filterType='';filterStatus='';filterDept='';showPendingOnly=false"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showPendingOnly ? 'text-white bg-yellow-500 hover:bg-yellow-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showPendingOnly = !showPendingOnly">
          {{ showPendingOnly ? 'Show All' : 'Show Pending Approvals Only' }}
        </button>
      </div>
    </div>

    <!-- Register + Insights -->
    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Complimentary Register -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Complimentary Register</h3>
        </div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50">
              <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Guest</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Complimentary Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Value</th>
              <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Approver</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in records" :key="r.code"
              class="border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
              :class="selectedRecord === r.code ? 'bg-blue-50 border border-blue-300' : 'hover:bg-gray-50'"
              @click="selectedRecord = r.code">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.guest }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.room }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.type }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r.status)">{{ r.status }}</span>
              </td>
              <td class="px-4 py-4 text-xs font-bold text-gray-900">{{ r.value }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ r.approver }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Approval & Usage Insights -->
      <div class="space-y-3">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Top Complimentary Types</p>
          <p class="text-sm font-bold text-gray-900 mb-1">Late Checkout • Food Voucher • Amenity Basket</p>
          <p class="text-xs text-gray-400">Most issued across VIP and service-recovery cases</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-3">Pending Approval Queue</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">• 2 food vouchers awaiting GM approval</p>
          <p class="text-xs text-gray-600 py-1 border-b border-gray-100">• 1 room upgrade pending availability</p>
          <p class="text-xs text-gray-600 py-1">• 3 transport requests pending dispatch</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-sm font-bold text-gray-900 mb-2">Consumption Summary</p>
          <p class="text-xs text-gray-500 leading-relaxed">4 complimentary items consumed today. Usage rate this week is 78% of issued benefits.</p>
        </div>
        <div class="bg-blue-50 rounded-xl border border-blue-200 px-5 py-4">
          <p class="text-sm font-bold text-blue-700 mb-2">Suggested Action</p>
          <p class="text-xs text-blue-600 leading-relaxed">Review pending dinner voucher for Room 511 and close consumed items awaiting confirmation.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">Complimentary management page for approvals, issuance, consumption, and control.</p>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterDept = ref('')
const showPendingOnly = ref(false)
const selectedRecord = ref('CMP-000431')

const records = [
  { code: 'CMP-000431', guest: 'Sarah Johnson',  room: '305', type: 'Amenity + Late Checkout', status: 'Approved',    value: '₦18,000', approver: 'Duty Mgr' },
  { code: 'CMP-000432', guest: 'Michael Duke',   room: '603', type: 'Airport Transfer',        status: 'In Progress', value: '₦32,000', approver: 'Front Desk' },
  { code: 'CMP-000433', guest: 'Grace Kelvin',   room: '219', type: 'Laundry + Amenity',       status: 'Consumed',    value: '₦9,500',  approver: 'Housekeeping' },
  { code: 'CMP-000434', guest: 'Ngozi Cole',     room: '511', type: 'Food Voucher',            status: 'Pending',     value: '₦15,000', approver: 'GM' },
]

function statusClass(s) {
  return {
    'Approved':    'bg-green-50 text-green-600',
    'In Progress': 'bg-blue-50 text-blue-600',
    'Consumed':    'bg-green-100 text-green-700',
    'Pending':     'bg-yellow-50 text-yellow-600',
    'Expired':     'bg-gray-100 text-gray-500',
    'Cancelled':   'bg-red-50 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}
</script>