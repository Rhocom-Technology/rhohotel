<template>
  <div class="space-y-5">

    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Housekeeping / Dashboard</p>
      <h1 class="text-2xl font-bold text-gray-900">Housekeeping Dashboard</h1>
      <p class="text-xs text-gray-400 mt-1">Monitor room status, attendant workload, cleaning progress, linen movement, and priority tasks across the hotel.</p>
    </div>

    <!-- Date Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Today • 15 Apr 2026</h2>
        <p class="text-xs text-gray-400 mt-0.5">Morning shift active • 8 attendants on duty • 126 rooms tracked</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Refresh</button>
        <router-link to="/housekeeping">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Housekeeping List</button>
        </router-link>
      </div>
    </div>

    <!-- Room Status Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="rounded-xl px-5 py-4" style="background:#ef4444;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-red-100">Dirty Rooms</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-300 text-white rounded-full">Priority</span>
        </div>
        <p class="text-3xl font-bold text-white">38</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#d1fae5;border:1px solid #a7f3d0;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-green-700">Clean & Ready</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-200 text-green-700 rounded-full">Available</span>
        </div>
        <p class="text-3xl font-bold text-green-800">64</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#e0e7ff;border:1px solid #c7d2fe;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-indigo-700">Inspected Rooms</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-indigo-200 text-indigo-700 rounded-full">QA</span>
        </div>
        <p class="text-3xl font-bold text-indigo-800">19</p>
      </div>
      <div class="rounded-xl px-5 py-4" style="background:#fef9c3;border:1px solid #fde68a;">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-yellow-700">Out of Order</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-200 text-yellow-700 rounded-full">Blocked</span>
        </div>
        <p class="text-3xl font-bold text-yellow-800">5</p>
      </div>
    </div>

    <!-- Main Grid -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">

      <!-- Left -->
      <div class="space-y-4">

        <!-- Room Status Board -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Room Status Board</h3>
          </div>
          <div class="p-4 space-y-2">
            <div class="flex items-center justify-between bg-red-50 rounded-xl border border-red-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room 402 • Dirty</p>
                <p class="text-xs text-gray-400 mt-0.5">Due-out room • high priority • VIP arrival scheduled</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold bg-red-100 text-red-500 rounded-full">Urgent</span>
            </div>
            <div class="flex items-center justify-between bg-blue-50 rounded-xl border border-blue-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room 305 • Cleaning in Progress</p>
                <p class="text-xs text-gray-400 mt-0.5">Assigned to Blessing • ETA 15 mins</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold bg-blue-100 text-blue-600 rounded-full">In Progress</span>
            </div>
            <div class="flex items-center justify-between bg-green-50 rounded-xl border border-green-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room 118 • Clean & Ready</p>
                <p class="text-xs text-gray-400 mt-0.5">Inspected and released to front desk</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold bg-green-100 text-green-600 rounded-full">Released</span>
            </div>
            <div class="flex items-center justify-between bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room 511 • Out of Order</p>
                <p class="text-xs text-gray-400 mt-0.5">Maintenance issue reported • plumbing repair pending</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold bg-purple-100 text-purple-600 rounded-full">Blocked</span>
            </div>
            <div class="flex items-center justify-between bg-yellow-50 rounded-xl border border-yellow-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">Room 214 • Inspection Pending</p>
                <p class="text-xs text-gray-400 mt-0.5">Cleaning completed • awaiting supervisor check</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold bg-yellow-100 text-yellow-600 rounded-full">Inspection</span>
            </div>
          </div>
        </div>

        <!-- Attendant Workload -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Attendant Workload</h3>
          </div>
          <div class="p-4 space-y-3">
            <div v-for="attendant in attendants" :key="attendant.name"
              class="flex items-center justify-between bg-gray-50 rounded-xl border border-gray-100 px-4 py-3">
              <div>
                <p class="text-xs font-bold text-gray-900">{{ attendant.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ attendant.summary }}</p>
              </div>
              <button class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100">View Tasks</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right -->
      <div class="space-y-4">

        <!-- Priority Queue -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Priority Queue</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Early Arrivals Waiting</span>
              <span class="text-xs font-bold text-gray-900">6 Rooms</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">VIP Rooms Pending Prep</span>
              <span class="text-xs font-bold text-gray-900">3 Rooms</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Deep Cleaning Scheduled</span>
              <span class="text-xs font-bold text-gray-900">4 Rooms</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Linen Refill Required</span>
              <span class="text-xs font-bold text-gray-900">12 Rooms</span>
            </div>
          </div>
          <button class="mt-3 px-3 py-1.5 text-xs font-semibold text-yellow-600 bg-yellow-50 rounded-lg border border-yellow-100">High Attention</button>
        </div>

        <!-- Linen & Laundry -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Linen & Laundry</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Fresh Linen Issued</span>
              <span class="text-xs font-bold text-gray-900">186 Sets</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Soiled Linen Returned</span>
              <span class="text-xs font-bold text-gray-900">164 Sets</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-600">Laundry Backlog</span>
              <span class="text-xs font-bold text-red-500">22 Items</span>
            </div>
          </div>
          <button class="mt-3 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg border border-blue-100">View Stock</button>
        </div>

        <!-- Supervisor Notes -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Supervisor Notes</h3>
          <div class="text-xs text-gray-600 space-y-2">
            <p>Morning inspection flagged 3 VIP rooms for rushed turnaround before 2 PM arrivals.</p>
            <p>Room 511 remains blocked pending plumbing repair and final maintenance signoff.</p>
            <p>Housekeeping pantry on 3rd floor requires refill of toiletries and bath towels.</p>
          </div>
          <div class="flex items-center gap-2 mt-4">
            <button class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Add Note</button>
            <button @click="router.push('/housekeeping/task/new')" class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">New Task</button>
            <button class="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Report View</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const attendants = [
  { name: 'Blessing Okoro', summary: '12 rooms assigned • 7 completed • 3 in progress • 2 pending' },
  { name: 'Ifeoma Nnadi', summary: '10 rooms assigned • 6 completed • 2 in progress • 2 pending' },
  { name: 'Boma Eze', summary: '9 rooms assigned • 5 completed • 1 in progress • 3 pending' },
]
</script>