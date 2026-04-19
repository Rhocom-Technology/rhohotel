<template>
  <div class="p-6">

    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ type === 'Corporate' ? 'Corporate Reservation' : 'New Reservation' }}</h1>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ type === 'Corporate' ? 'Corporate bulk reservation workflow' : 'Individual and corporate reservations with guest selection, stay dates, room choice, rate auto-fill, discount control, and grand total' }}
        </p>
      </div>
      <button v-if="type === 'Individual'" class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">
        Save Reservation
      </button>
    </div>

    <!-- Reservation Type Toggle -->
    <div class="flex items-center gap-3 mb-5" v-if="type === 'Corporate'">
      <p class="text-xs text-gray-500">Reservation Type</p>
      <div class="flex items-center gap-1 bg-gray-100 rounded-full p-1">
        <button @click="mode = 'Individual'" class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
          :class="mode === 'Individual' ? 'bg-white text-gray-900 shadow' : 'text-gray-400'">Individual</button>
        <button @click="mode = 'Corporate'" class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
          :class="mode === 'Corporate' ? 'bg-gray-900 text-white' : 'text-gray-400'">Corporate</button>
      </div>
      <div class="flex items-center gap-2 ml-auto">
        <button @click="$emit('close')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Submit</button>
      </div>
    </div>

    <!-- Individual Form -->
    <div v-if="type === 'Individual'" style="display:grid;grid-template-columns:1fr 360px;gap:24px;">
      <div>
        <!-- Reservation Type Toggle -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <p class="text-xs text-gray-500 mb-2">Reservation Type</p>
          <div class="flex items-center gap-2 mb-1">
            <div class="flex items-center gap-1 bg-gray-100 rounded-full p-1">
              <button class="px-4 py-1.5 text-xs font-semibold bg-gray-900 text-white rounded-full">Individual</button>
              <button @click="$emit('close'); $emit('switchToCorporate')" class="px-4 py-1.5 text-xs font-medium text-gray-400 rounded-full">Corporate</button>
            </div>
            <p class="text-xs text-gray-400 ml-2">Individual mode is tailored to a single guest booking workflow.</p>
          </div>
        </div>

        <!-- Individual Reservation Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Individual Reservation Details</h3>

          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Guest Selection</p>
            <div class="flex items-center gap-2">
              <input type="text" placeholder="Search existing guest by name, phone, email or ID"
                class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 whitespace-nowrap">Create New Guest</button>
            </div>
            <div class="mt-2 bg-blue-50 rounded-lg p-3 border border-blue-100">
              <p class="text-xs font-semibold text-blue-600">Selected Guest Preview</p>
              <p class="text-xs text-gray-500 mt-1">No guest selected yet. Existing guest details will appear here after search.</p>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">From Date</p>
              <input v-model="form.from_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" placeholder="Select date" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">To Date</p>
              <input v-model="form.to_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" placeholder="Select date" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Number of Nights</p>
              <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-700">{{ nightsCount }}</div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Adults</p>
              <input v-model="form.adults" type="number" value="2" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Children</p>
              <input v-model="form.children" type="number" value="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reservation Status</p>
              <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-700">Draft</div>
            </div>
          </div>
        </div>

        <!-- Room and Pricing -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Room and Pricing</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <input type="text" placeholder="Select room type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Selection</p>
              <input type="text" placeholder="Select room" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Rate</p>
              <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-500 italic">₦120,000.00 (auto-filled)</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
              <input type="text" value="Percentage" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Value</p>
              <input type="text" value="10%" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Reservation Notes</p>
            <textarea rows="4" placeholder="Add arrival notes, pickup requests, payment notes, or special requests"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Right: Reservation Summary -->
      <div>
        <h3 class="text-sm font-bold text-gray-900 mb-4">Reservation Summary</h3>

        <div class="bg-white border border-blue-200 rounded-xl p-4 mb-3">
          <h4 class="text-sm font-bold text-blue-600 mb-2">Current Booking Snapshot</h4>
          <p class="text-xs text-gray-500">Guest: Pending selection</p>
          <p class="text-xs text-gray-500 mt-0.5">From: 21 Mar 2026 • To: 24 Mar 2026 • Nights: 3</p>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 mb-3">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Grand Total Calculation</h4>
          <p class="text-xs text-gray-600">Rate per night: ₦120,000.00</p>
          <p class="text-xs text-gray-600">Nights: 3</p>
          <p class="text-xs text-gray-600">Gross total: ₦360,000.00</p>
          <p class="text-xs text-red-500">Discount: 10% = ₦36,000.00</p>
          <p class="text-sm font-bold text-gray-900 mt-1">Grand Total: ₦324,000.00</p>
        </div>

        <div class="bg-yellow-50 border border-yellow-100 rounded-xl p-4 mb-3">
          <h4 class="text-sm font-bold text-yellow-600 mb-1">Corporate Reservation Option</h4>
          <p class="text-xs text-yellow-600">Corporate mode can still hold one guest reservation without group workflow.</p>
        </div>

        <div class="bg-green-50 border border-green-100 rounded-xl p-4 mb-5">
          <h4 class="text-sm font-bold text-green-600 mb-1">Rate Auto-fill Logic</h4>
          <p class="text-xs text-green-600">Room selection loads the negotiated or standard rate automatically.</p>
          <p class="text-xs text-green-600 mt-0.5">Grand total updates immediately after discount change.</p>
        </div>

        <h4 class="text-sm font-bold text-gray-900 mb-3">Quick Actions</h4>
        <div class="space-y-2">
          <button class="w-full py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700">Save Draft</button>
          <button class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-xl hover:bg-green-600">Confirm Reservation</button>
          <button class="w-full py-2.5 text-xs font-semibold text-gray-600 bg-gray-200 rounded-xl hover:bg-gray-300">Early Check-In</button>
        </div>
      </div>
    </div>

    <!-- Corporate Form -->
    <div v-if="type === 'Corporate'" style="display:grid;grid-template-columns:1fr 320px;gap:24px;">
      <div>
        <!-- Corporate / Booker Information -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Corporate / Booker Information</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Corporate Account</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Apex Holdings Limited</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Booking Contact Person</p>
              <input type="text" placeholder="Ngozi Eze" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Email</p>
              <input type="email" placeholder="traveldesk@apexholdings.com" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone Number</p>
              <input type="text" placeholder="+234 803 555 0198" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
        </div>

        <!-- Reservation Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Reservation Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reservation Name / Event</p>
              <input type="text" placeholder="Apex Annual Strategy Retreat" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reservation Source</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Corporate Contract</option>
                <option>Direct</option>
                <option>Travel Agent</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Arrival Date</p>
              <input v-model="form.from_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Departure Date</p>
              <input v-model="form.to_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">No. of Nights</p>
              <div class="px-3 py-2.5 text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg text-gray-700">{{ nightsCount }} Nights</div>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Special Instructions</p>
            <input type="text" placeholder="Quiet floors, early breakfast setup, airport pickup for VIP guests"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
          </div>
        </div>

        <!-- Room Requirements -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Room Requirements & Availability</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Executive Deluxe</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Rooms Required</p>
              <input type="number" value="12" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-center font-bold" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guests / Occupancy Rule</p>
              <input type="text" value="2 Adults per room" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
          <div class="flex items-center gap-2 mb-4">
            <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Get Available Rooms</button>
            <button class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Add Another Room Type</button>
          </div>
          <div>
            <h4 class="text-xs font-semibold text-gray-700 mb-2">Selected Rooms</h4>
            <table class="w-full border border-gray-100 rounded-lg overflow-hidden">
              <thead>
                <tr class="bg-gray-50">
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">No</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room Number</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room Type</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate per Night</th>
                  <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="5" class="px-3 py-4 text-center text-xs text-gray-300">No rooms selected yet</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Right sidebar -->
      <div class="space-y-4">
        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Bulk Summary</h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Company</span>
              <span class="text-xs font-semibold text-gray-900">Apex Holdings</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Rooms Requested</span>
              <span class="text-xs font-semibold text-gray-900">12 Rooms</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Occupancy</span>
              <span class="text-xs font-semibold text-gray-900">24 Guests</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Stay Period</span>
              <span class="text-xs font-semibold text-gray-900">{{ nightsCount }} Nights</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Room Type</span>
              <span class="text-xs font-semibold text-gray-900">Executive Deluxe</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">Estimated Room Value</span>
              <span class="text-xs font-bold text-gray-900">₦4,320,000</span>
            </div>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Guest Rooming List</h4>
          <button class="w-full py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 mb-3">
            Upload Rooming List
          </button>
          <div class="space-y-1.5 text-xs">
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Rooming file</span>
              <span class="font-medium text-blue-600">Apex_Rooming_List.xlsx</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Imported guests</span>
              <span class="font-semibold text-gray-900">24 Guests</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Pending assignment</span>
              <span class="font-semibold text-orange-500">4 Guests</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Assigned rooms</span>
              <span class="font-semibold text-gray-900">8 Rooms</span>
            </div>
          </div>
          <button class="w-full mt-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100">
            Preview Rooming List
          </button>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4">
          <h4 class="text-sm font-bold text-gray-900 mb-3">Pricing</h4>
          <div class="space-y-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Sub Total</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400">—</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400">—</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Value</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400">—</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Grand Total</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400">—</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ type: { type: String, required: true } })
defineEmits(['close', 'saved', 'switchToCorporate'])

const mode = ref(props.type)
const form = ref({
  from_date: '',
  to_date: '',
  adults: 2,
  children: 0,
})

const nightsCount = computed(() => {
  if (!form.value.from_date || !form.value.to_date) return 3
  const diff = Math.round((new Date(form.value.to_date) - new Date(form.value.from_date)) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 0
})
</script>