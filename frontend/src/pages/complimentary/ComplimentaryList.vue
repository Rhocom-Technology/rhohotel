<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Operations / <span class="text-gray-600">Complimentary Management</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Complimentary List</h1>
      <p class="text-xs text-gray-400 mt-1">Review all complimentary entries, approval states, issue dates, values, consumers, and redemption or usage progress in one register.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Complimentary Register Overview</h3>
        <p class="text-xs text-gray-400 mt-0.5">96 total records • 19 active • 6 pending approval • 58 consumed • 13 expired / cancelled</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="$router.push('/complimentary')">Complimentary Dashboard</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          @click="$router.push('/complimentary/new')">New Complimentary</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Records</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">All Time</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">96</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Active Benefits</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">19</p>
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
          <p class="text-xs text-gray-400">Value This Month</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Month</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦1.82M</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search guest, code, benefit..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterType" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Types</option>
          <option>Food Voucher</option>
          <option>Transport</option>
          <option>Room Upgrade</option>
          <option>Amenity</option>
          <option>Laundry / Amenity</option>
        </select>
        <select v-model="filterStatus" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Statuses</option>
          <option>Approved</option>
          <option>In Progress</option>
          <option>Consumed</option>
          <option>Pending</option>
          <option>Expired</option>
          <option>Cancelled</option>
        </select>
        <select v-model="filterApprover" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Approvers</option>
          <option>Duty Mgr</option>
          <option>Front Desk</option>
          <option>Housekeeping</option>
          <option>GM</option>
          <option>Ops Lead</option>
        </select>
        <button @click="search='';filterType='';filterStatus='';filterApprover='';showConsumedOnly=false"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showConsumedOnly ? 'text-white bg-green-600 hover:bg-green-700' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showConsumedOnly = !showConsumedOnly">
          {{ showConsumedOnly ? 'Show All Records' : 'Show Consumed Benefits Only' }}
        </button>
      </div>
    </div>

    <!-- Records Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">Complimentary Records</h3>
        <p class="text-xs text-gray-400">Showing 1–6 of 96 records</p>
      </div>
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Code</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Issued On</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Value</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Status</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Approver</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in paged" :key="r.code" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ r.code }}</td>
            <td class="px-4 py-4">
              <div class="text-xs font-bold text-gray-900">{{ r.guest }}</div>
              <div class="text-xs text-gray-400">{{ r.note }}</div>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.room }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.issuedOn }}</td>
            <td class="px-4 py-4 text-xs font-bold text-gray-900">{{ r.value }}</td>
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(r.status)">{{ r.status }}</span>
            </td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ r.approver }}</td>
            <td class="px-4 py-4">
              <button
                class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$router.push('/complimentary/' + r.code)">
                {{ r.action }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-1">
          <button v-for="p in 4" :key="p" @click="currentPage=p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="currentPage===p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">
            {{ p }}
          </button>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-white ml-1 transition-colors">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterApprover = ref('')
const showConsumedOnly = ref(false)
const currentPage = ref(1)

const records = [
  { code: 'CMP-000431', guest: 'Sarah Johnson',  note: 'Welcome fruit basket + late checkout',     room: '305', type: 'Amenity / Late CO',    issuedOn: '18 Apr 2026', value: '₦18,000', status: 'Approved',    approver: 'Duty Mgr',    action: 'View' },
  { code: 'CMP-000432', guest: 'Michael Duke',   note: 'Airport transfer reward redemption',       room: '603', type: 'Transport',             issuedOn: '18 Apr 2026', value: '₦32,000', status: 'In Progress', approver: 'Front Desk',  action: 'Update' },
  { code: 'CMP-000433', guest: 'Grace Kelvin',   note: 'Laundry piece + premium tea tray',         room: '219', type: 'Laundry / Amenity',     issuedOn: '17 Apr 2026', value: '₦9,500',  status: 'Consumed',    approver: 'Housekeeping',action: 'View' },
  { code: 'CMP-000434', guest: 'Ngozi Cole',     note: 'Dinner voucher for service recovery',      room: '511', type: 'Food Voucher',          issuedOn: '18 Apr 2026', value: '₦15,000', status: 'Pending',     approver: 'GM',          action: 'Review' },
  { code: 'CMP-000435', guest: 'Daniel Ayo',     note: 'Room upgrade due to maintenance disruption',room:'118', type: 'Room Upgrade',          issuedOn: '16 Apr 2026', value: '₦45,000', status: 'Expired',     approver: 'Ops Lead',    action: 'View' },
  { code: 'CMP-000436', guest: 'Blessing Owen',  note: 'Airport drop and breakfast voucher',       room: '214', type: 'Transport / Food',      issuedOn: '15 Apr 2026', value: '₦21,500', status: 'Cancelled',   approver: 'Duty Mgr',    action: 'View' },
]

const paged = computed(() => records)

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