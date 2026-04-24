<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Guest Profile / <span class="text-gray-600">Edit Existing Guest</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Edit Existing Guest</h1>
      <p class="text-xs text-gray-400 mt-1">Update the selected guest record including identity, demographics, emergency contact, preferences, and attachment records.</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Edit Guest Record</h3>
        <p class="text-xs text-gray-400 mt-0.5">Update guest information, contact records, preferences, nationality details, ID information, and supporting attachment files.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/guests/' + guestId)">View Profile</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset Changes</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Save Changes</button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 280px;gap:12px;">

      <!-- Left: Form -->
      <div class="space-y-5">

        <!-- Guest Information -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Guest Information</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
              <select v-model="form.guestType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>Individual</option><option>Corporate</option><option>Walk-in</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Title</p>
              <select v-model="form.title" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>Mrs.</option><option>Mr.</option><option>Dr.</option><option>Prof.</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Gender</p>
              <select v-model="form.gender" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>Female</option><option>Male</option><option>Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Date of Birth</p>
              <input type="text" v-model="form.dob" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Full Name</p>
            <input type="text" v-model="form.fullName" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone Number</p>
              <input type="text" v-model="form.phone" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input type="text" v-model="form.email" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
              <select v-model="form.nationality" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>Nigerian</option><option>Ghanaian</option><option>British</option><option>American</option><option>Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Preference</p>
              <select v-model="form.preference" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>Quiet room / High floor</option><option>Low floor</option><option>Near elevator</option><option>Non-smoking</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Identification Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Identification Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Type</p>
              <select v-model="form.idType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option>National ID</option><option>Passport</option><option>Driver's License</option><option>Voter's Card</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Number</p>
              <input type="text" v-model="form.idNumber" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Document Attachment</p>
            <div class="border border-dashed border-blue-300 rounded-lg px-4 py-3 text-center cursor-pointer hover:bg-blue-50 transition-colors">
              <p class="text-xs font-medium text-blue-600">Replace or upload document attachment</p>
            </div>
          </div>
        </div>

        <!-- Contact Person -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Contact Person</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Name</p>
              <input type="text" v-model="form.contactName" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Number</p>
              <input type="text" v-model="form.contactPhone" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Address</p>
            <input type="text" v-model="form.address" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Notes</p>
            <textarea v-model="form.notes" rows="3"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Right: Edit Summary -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Edit Summary</h3>

        <div>
          <p class="text-xs text-gray-500 mb-2">Guest Preview</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">{{ form.fullName || 'Guest Name' }}</p>
            <p class="text-xs text-blue-600">Type: {{ form.guestType }}</p>
            <p class="text-xs text-blue-600">Nationality: {{ form.nationality }}</p>
            <p class="text-xs text-blue-600">Preference: {{ form.preference }}</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Record Status</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2">
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full bg-green-500"></div>
              <span class="text-xs text-gray-700">Active guest profile</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full bg-green-500"></div>
              <span class="text-xs text-gray-700">Eligible for reservations and check-in</span>
            </div>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Loyalty Snapshot</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs font-bold text-gray-900 mb-1">VIP Corporate Guest</p>
            <p class="text-xs text-gray-500">Reward level: Gold</p>
            <p class="text-xs text-gray-500">Stay count: 14 completed stays</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Attachment Status</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs text-gray-500 mb-1">Current file: National_ID_Grace.pdf</p>
            <button class="text-xs font-medium text-blue-600 hover:underline">Open attachment</button>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Quick Actions</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <button class="px-3 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Open Folio</button>
            <button class="px-3 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">View Stays</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const guestId = route.params.id

const form = reactive({
  guestType: 'Individual',
  title: 'Mrs.',
  gender: 'Female',
  dob: '14 May 1989',
  fullName: 'Grace Kelvin',
  phone: '+234 803 456 1180',
  email: 'grace.kelvin@email.com',
  nationality: 'Nigerian',
  preference: 'Quiet room / High floor',
  idType: 'National ID',
  idNumber: 'A9876543212',
  contactName: 'Daniel Kelvin',
  contactPhone: '+234 803 998 4401',
  address: '14 Rumuola Crescent, GRA Phase 2, Port Harcourt, Rivers State, Nigeria',
  notes: 'VIP returning guest. Prefers quiet room, fast check-in, and non-smoking floor.',
})
</script>