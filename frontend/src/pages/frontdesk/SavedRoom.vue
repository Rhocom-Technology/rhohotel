<template>
  <div class="space-y-5">

    <!-- Room Record Summary Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Room Record Summary</h3>
        <p class="text-xs text-gray-400 mt-0.5">Room 305 • Executive Suite • Floor 3 • occupied and linked to active check-in record</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/room-view')">Room List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Print</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Block Room</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Edit Room</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Base Rate</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">BAR</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦120,000</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Current Guest</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">In House</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">Sarah Johnson</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Current Check-in ID</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Linked</span>
        </div>
        <p class="text-base font-bold text-gray-900 mt-1">CHK-2026-000421</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Housekeeping Default</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Open</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">Clean</p>
      </div>
    </div>

    <!-- Details + Operational Setup -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

      <!-- Room Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Room Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Number</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">305</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Floor</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">3</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">Executive Suite</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Bed Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">1 King Bed</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Guest</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Sarah Johnson</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-in ID</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">CHK-2026-000421</div>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Room Description</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            Spacious executive suite with lounge corner, premium furnishing, smart TV, minibar, and work desk for premium stays.
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Operational Notes</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            Room currently occupied. Inspection required after checkout. Maintenance flag currently not active.
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Amenities / Features</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">
            Wi-Fi • Minibar • Smart TV • Bathtub • Balcony • Work Desk • Coffee Station
          </div>
        </div>
      </div>

      <!-- Operational Setup -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Operational Setup</h3>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
          <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
            <option>Occupied</option>
            <option>Vacant</option>
            <option>Reserved</option>
            <option>Maintenance</option>
          </select>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Keycard Enabled</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Yes, keycard activation allowed</span>
            </label>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Maintenance Block</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Out of service on save</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Require inspection before release</span>
            </label>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Inventory Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg">
            Occupied and linked to active stay
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Audit Trail</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3 space-y-3">
            <div v-for="a in audit" :key="a.time">
              <p class="text-xs font-semibold text-gray-900">{{ a.time }}</p>
              <p class="text-xs text-gray-500">{{ a.action }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
const audit = [
  { time: '18 Apr 2026 • 10:22 AM', action: 'Room record created by Admin' },
  { time: '18 Apr 2026 • 10:30 AM', action: 'Rate plan attached: Standard BAR' },
  { time: '18 Apr 2026 • 02:05 PM', action: 'Linked to check-in CHK-2026-000421' },
]
</script>