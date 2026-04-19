<template>
  <div class="p-6">

    <!-- Header -->
    <div class="flex items-start justify-between mb-5">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Change Room</h2>
        <p class="text-xs text-gray-400 mt-1">Move this reservation to another room while validating availability, rate impact, and operational notes.</p>
      </div>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
        <span class="text-lg">✕</span>
      </button>
    </div>

    <!-- Reservation Snapshot -->
    <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6">
      <h3 class="text-xs font-bold text-gray-900 mb-3">Reservation Snapshot</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
        <div>
          <p class="text-xs text-gray-400 mb-1">Reservation ID</p>
          <p class="text-sm font-bold text-gray-900">RES-2024-00125</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Guest</p>
          <p class="text-sm font-bold text-gray-900">John Smith</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Stay Period</p>
          <p class="text-sm font-bold text-gray-900">Nov 10, 2024 → Nov 15, 2024</p>
        </div>
        <div>
          <p class="text-xs text-gray-400 mb-1">Current Room</p>
          <p class="text-sm font-bold text-gray-900">101 • Deluxe King</p>
        </div>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 280px;gap:24px;">

      <!-- Left: Room Change Details -->
      <div>
        <h3 class="text-sm font-bold text-gray-900 mb-4">Room Change Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Change Type</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Upgrade Room</option>
              <option>Downgrade Room</option>
              <option>Same Type Transfer</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Change Reason</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Guest Preference</option>
              <option>Maintenance Issue</option>
              <option>Operational</option>
              <option>Complaint Resolution</option>
            </select>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Room</p>
            <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">101 • Deluxe King</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Floor / Wing</p>
            <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">1st Floor • East Wing</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">New Room</p>
            <select class="w-full px-3 py-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700">
              <option>205 • Executive Suite</option>
              <option>301 • Deluxe King</option>
              <option>410 • Premium Suite</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Effective Date / Time</p>
            <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Nov 11, 2024 • 2:30 PM</div>
          </div>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Operational Instruction</p>
          <input type="text" value="Transfer guest after room inspection and keycard setup"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Room Change Notes</p>
          <textarea rows="3" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none">Guest requested a larger room with better city view.</textarea>
          <p class="text-xs text-gray-400 mt-1">This update will be logged in room movement history and front desk activity.</p>
        </div>

        <p class="text-xs text-gray-400 pt-4 border-t border-gray-100">
          Applying this change will update room occupancy, billing, keycard assignment, and internal movement logs.
        </p>
      </div>

      <!-- Right: Room Comparison & Rate Impact -->
      <div class="space-y-4">

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Room Comparison</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Current Room Type</span>
              <span class="text-xs font-semibold text-gray-900">Deluxe King</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">New Room Type</span>
              <span class="text-xs font-semibold text-gray-900">Executive Suite</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">View / Feature</span>
              <span class="text-xs font-semibold text-gray-900">City View • Lounge Area</span>
            </div>
            <div class="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
              <span class="text-xs text-gray-500">Housekeeping Status</span>
              <span class="px-2.5 py-1 text-xs font-semibold bg-green-100 text-green-600 rounded-full">Clean & Ready</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Rate Impact</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Current Rate</span>
              <span class="text-xs font-semibold text-gray-900">₦120,000 / night</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">New Rate</span>
              <span class="text-xs font-semibold text-gray-900">₦165,000 / night</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">Additional Charge</span>
              <span class="text-xs font-bold text-gray-900">₦45,000 / night</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Availability & Approval</h4>
          <span class="px-2.5 py-1 text-xs font-semibold bg-blue-100 text-blue-600 rounded-full">Available</span>
          <p class="text-xs text-gray-400 mt-2">New room is free for the full reservation period and ready for reassignment.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
      <button @click="$emit('close')" class="px-6 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
      <button class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Apply</button>
    </div>

  </div>
</template>

<script setup>
defineProps({ reservation: { type: Object, required: true } })
defineEmits(['close'])
</script>