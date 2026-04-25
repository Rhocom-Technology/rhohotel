<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Front desk • create room inventory record and operational setup</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border-2 border-blue-400 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Create Room Record</h3>
        <p class="text-xs text-gray-400 mt-0.5">Enter room identity, category, pricing, floor location, occupancy setup, and operational controls.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/rooms/list')">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Save Room</button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Room Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Room Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Number</p>
            <input type="text" v-model="form.roomNumber" placeholder="Enter room number"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Floor</p>
            <select v-model="form.floor" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select floor</option>
              <option v-for="f in 10" :key="f" :value="String(f)">Floor {{ f }}</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
            <select v-model="form.roomType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select room type</option>
              <option>Standard Room</option>
              <option>Deluxe Room</option>
              <option>Executive Suite</option>
              <option>Standard Twin</option>
              <option>Junior Suite</option>
              <option>Presidential Suite</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Bed Type</p>
            <select v-model="form.bedType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select bed type</option>
              <option>1 King Bed</option>
              <option>1 Queen Bed</option>
              <option>2 Twin Beds</option>
              <option>1 Double Bed</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Base Rate</p>
            <input type="text" v-model="form.baseRate" placeholder="₦0.00"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Capacity</p>
            <input type="text" v-model="form.capacity" placeholder="Adults / Children"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Rate Plan</p>
            <select v-model="form.ratePlan" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Standard BAR</option>
              <option>Corporate Rate</option>
              <option>Promotional</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
            <select v-model="form.roomStatus" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Available</option>
              <option>Out of Service</option>
              <option>Under Renovation</option>
            </select>
          </div>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Room Description</p>
          <textarea v-model="form.description" rows="3"
            placeholder="Enter room overview, style, furnishing notes, and guest-facing description..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Operational Notes</p>
          <textarea v-model="form.opNotes" rows="3"
            placeholder="Maintenance note, inspection rule, or setup note for operations..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Amenities / Features</p>
          <textarea v-model="form.amenities" rows="2"
            placeholder="Wi-Fi, minibar, balcony, smart TV, bathtub, work desk, kitchenette..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
      </div>

      <!-- Room Setup -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
          <h3 class="text-sm font-bold text-gray-900">Room Setup</h3>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Housekeeping Default</p>
            <select v-model="form.hkDefault" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Clean</option>
              <option>Dirty</option>
              <option>Inspected</option>
              <option>In Progress</option>
            </select>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Keycard Enabled</p>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.keycardEnabled" checked class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Allow keycard activation for this room</span>
              </label>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Maintenance Block</p>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.outOfService" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Mark room as out of service on save</span>
              </label>
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.requireInspection" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Require inspection before release</span>
              </label>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Classification</p>
            <select v-model="form.classification" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Sellable Room</option>
              <option>Complimentary Room</option>
              <option>Staff Room</option>
              <option>Storage</option>
            </select>
          </div>
        </div>

        <!-- Preview Summary -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
          <p class="text-xs text-gray-500 mb-2">Preview Summary</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-sm font-bold text-blue-700 mb-2">New Room Preview</p>
            <p class="text-xs text-blue-600">Room No: {{ form.roomNumber || '—' }}</p>
            <p class="text-xs text-blue-600">Type: {{ form.roomType || '—' }}</p>
            <p class="text-xs text-blue-600">Rate: {{ form.baseRate || '₦0.00' }}</p>
            <p class="text-xs text-blue-600">Status: {{ form.roomStatus }}</p>
          </div>
        </div>

        <!-- Quick Tips -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
          <p class="text-xs text-gray-500 mb-2">Quick Tips</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs text-gray-500 leading-relaxed">Use unique room number, correct floor, and room type before saving to keep inventory clean.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer note -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">New room setup page for room inventory, pricing, and operational configuration.</p>
    </div>

  </div>
</template>

<script setup>
import { reactive } from 'vue'

const form = reactive({
  roomNumber: '', floor: '', roomType: '', bedType: '',
  baseRate: '', capacity: '', ratePlan: 'Standard BAR',
  roomStatus: 'Available', description: '', opNotes: '',
  amenities: '', hkDefault: 'Clean', keycardEnabled: true,
  outOfService: false, requireInspection: false,
  classification: 'Sellable Room',
})
</script>