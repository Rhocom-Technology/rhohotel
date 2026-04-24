<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Professional front desk check-in flow</p>
    </div>

    <!-- Top Action Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end">
      <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
        Proceed to Confirm Check-In
      </button>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

      <!-- LEFT COLUMN -->
      <div class="space-y-5">

        <!-- Reservation -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center gap-4">
            <p class="text-xs font-medium text-gray-500 flex-shrink-0">Reservation</p>
            <input type="text" v-model="form.reservation"
              class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <!-- Guest Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Guest Details</h3>
          <p class="text-xs text-gray-400 mb-4">Identity, contact, and arrival information for the incoming guest</p>

          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Guest Selection</p>
            <div class="flex items-center gap-3">
              <input type="text" v-model="form.guest" placeholder="Search existing guest by name, phone, email or ID"
                class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex-shrink-0">
                Create New Guest
              </button>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone</p>
              <input type="text" placeholder="Auto-filled after guest selection"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50" readonly />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input type="text" placeholder="Auto-filled after guest selection"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50" readonly />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID or Passport</p>
              <input type="text" placeholder="Auto-filled or capture ID"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
              <input type="text" placeholder="Auto-filled or capture ID"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Room and Rate -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Room and Rate</h3>
          <p class="text-xs text-gray-400 mb-4">Assign room, define pricing, discount, and billing setup before arrival is completed</p>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-in Date</p>
              <input type="text" v-model="form.checkinDate" placeholder="Select date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nights</p>
              <input type="text" v-model="form.nights" placeholder="Select date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected check-out Date</p>
              <input type="text" placeholder="Auto / editable"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-gray-50" readonly />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <input type="text" v-model="form.roomType" placeholder="Select room type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Number</p>
              <input type="text" v-model="form.roomNumber" placeholder="Assign room"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Rate</p>
              <input type="text" v-model="form.rate" placeholder="Nightly rate auto fill"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-gray-50" readonly />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
              <input type="text" v-model="form.discountType"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount</p>
              <input type="text" v-model="form.discount" placeholder="Enter discount amount or percent"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Notes</h3>
          <textarea v-model="form.notes" rows="5"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none bg-gray-50"></textarea>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="space-y-5">

        <!-- Guest Preferences -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Guest Preferences</h3>
          <p class="text-xs text-gray-400 mb-4">Preference tags, special instructions, internal notes, and arrival requests</p>

          <p class="text-xs text-gray-500 mb-2">Preference Tags</p>
          <div class="flex items-center gap-2 flex-wrap mb-5">
            <span v-for="tag in preferenceTags" :key="tag.label"
              class="px-3 py-1 text-xs font-medium rounded-full cursor-pointer transition-colors"
              :class="tag.active ? tag.activeClass : 'bg-gray-100 text-gray-500'"
              @click="tag.active = !tag.active">
              {{ tag.label }}
            </span>
          </div>

          <div class="space-y-4">
            <label class="flex items-center justify-between cursor-pointer">
              <span class="text-sm font-medium text-gray-700">Early Check in</span>
              <div class="relative">
                <input type="checkbox" v-model="form.earlyCheckin" class="sr-only" />
                <div class="w-10 h-5 rounded-full transition-colors" :class="form.earlyCheckin ? 'bg-blue-600' : 'bg-gray-200'">
                  <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform" :class="form.earlyCheckin ? 'translate-x-5' : ''"></div>
                </div>
              </div>
            </label>
            <label class="flex items-center justify-between cursor-pointer">
              <span class="text-sm font-medium text-gray-700">Late Check Out</span>
              <div class="relative">
                <input type="checkbox" v-model="form.lateCheckout" class="sr-only" />
                <div class="w-10 h-5 rounded-full transition-colors" :class="form.lateCheckout ? 'bg-blue-600' : 'bg-gray-200'">
                  <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform" :class="form.lateCheckout ? 'translate-x-5' : ''"></div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- Key Card and Operational Setup -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Key Card and Operational Setup</h3>
          <p class="text-xs text-gray-400 mb-4">Prepare access, occupancy profile, and front office control information</p>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Generate Access</p>
              <button class="w-full px-4 py-2.5 text-xs font-bold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
                Generate Key Card
              </button>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Access Level</p>
              <input type="text" placeholder="Guest room only / executive floor"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Occupancy</p>
              <input type="text" placeholder="Adults / children"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Billing Plan</p>
              <input type="text" placeholder="Cash / company / transfer"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Internal Ops Note</p>
            <input type="text" v-model="form.opsNote"
              placeholder="Enter reception handover note, escort requirement, bell desk note, or card issuance comment"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <!-- Actions -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Actions</h3>
          <div class="flex items-center gap-3">
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              Confirm Check-In
            </button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              Save Draft
            </button>
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              @click="$router.back()">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive } from 'vue'

const form = reactive({
  reservation: '',
  guest: '',
  checkinDate: '',
  nights: '',
  roomType: '',
  roomNumber: '',
  rate: '',
  discountType: '',
  discount: '',
  notes: '',
  earlyCheckin: false,
  lateCheckout: false,
  opsNote: '',
})

const preferenceTags = reactive([
  { label: 'High Floor',   active: true,  activeClass: 'bg-blue-100 text-blue-600' },
  { label: 'Quiet Wing',   active: true,  activeClass: 'bg-green-100 text-green-600' },
  { label: 'Late Arrival', active: true,  activeClass: 'bg-yellow-100 text-yellow-600' },
  { label: 'VIP',          active: false, activeClass: 'bg-purple-100 text-purple-600' },
  { label: 'Extra Towels', active: false, activeClass: 'bg-gray-100 text-gray-600' },
])
</script>