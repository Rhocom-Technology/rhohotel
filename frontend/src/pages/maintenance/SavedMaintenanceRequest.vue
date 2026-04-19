<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Request Summary</h2>
        <p class="text-xs text-gray-400 mt-0.5">REQ-000184 • AC not cooling - Room 305 • submitted by Housekeeping • currently open for maintenance review</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/request')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Request List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Save</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Convert to Task</button>
      </div>
    </div>

    <!-- Status Cards -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border-2 border-blue-400 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Request Status</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Open</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Priority</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Urgent</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Target</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">Room</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Room 305</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Routing</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Queue</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Pending Review</p>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

      <!-- Left: Request Details -->
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Request Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <p class="text-xs text-gray-400 mb-1">Request ID</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">REQ-000184</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Request Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Corrective Request</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Requested By</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Mary Bello</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Department</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Housekeeping</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Target Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Room</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Location / Asset Reference</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Room 305 • AC Indoor Unit</div>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-400 mb-1">Issue Title</p>
          <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">AC not cooling - Room 305</div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-400 mb-1">Issue Description</p>
          <div class="bg-gray-50 rounded-lg px-3 py-3 text-xs text-gray-600 leading-relaxed">
            Guest reported that the air conditioner is blowing air but not cooling the room. Front desk confirmed temperature remains high after reset. Guest currently in-house and uncomfortable.
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mt-4">
          <div>
            <p class="text-xs text-gray-400 mb-1">Preferred Access Time</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Immediate access requested</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Guest Impact</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">High</div>
          </div>
        </div>
      </div>

      <!-- Right: Routing & Conversion -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Routing & Conversion</h3>

          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1">Submitted On</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">18 Apr 2026 • 09:12 AM</div>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1">Current Reviewer</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Maintenance Supervisor</div>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1">Suggested Technician Group</p>
            <div class="bg-blue-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-blue-600 border border-blue-100">HVAC / Room Electronics Team</div>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1">Evidence / Attachment</p>
            <button class="w-full py-2.5 text-xs font-medium text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">Open attached photo</button>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Conversion Status</p>
            <div class="bg-gray-50 rounded-lg px-3 py-3 border border-gray-100">
              <p class="text-xs text-gray-500">This request has not yet been converted into a maintenance task.</p>
              <p class="text-xs font-bold text-gray-900 mt-2">Next action:</p>
              <p class="text-xs text-gray-500 mt-0.5">Convert request to task and assign technician.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>