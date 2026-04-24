<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Guest profile • create a new guest identity, contact details, preferences, and supporting documents</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Guest Setup Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Capture guest information, contact records, nationality details, ID information, preferences, and attachment files for a new guest account.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Create Guest</button>
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
              <p class="text-xs text-gray-500 mb-1.5">Guest ID</p>
              <input type="text" placeholder="Auto generated on save"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none" readonly />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
              <select v-model="form.guestType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select guest type</option>
                <option>Individual</option><option>Corporate</option><option>Walk-in</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Title</p>
              <select v-model="form.title" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select title</option>
                <option>Mr.</option><option>Mrs.</option><option>Dr.</option><option>Prof.</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Gender</p>
              <select v-model="form.gender" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select gender</option>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Full Name</p>
            <input type="text" v-model="form.fullName" placeholder="Enter full guest name"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone Number</p>
              <input type="text" v-model="form.phone" placeholder="Enter phone number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input type="text" v-model="form.email" placeholder="Enter email address"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
              <select v-model="form.nationality" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select nationality</option>
                <option>Nigerian</option><option>Ghanaian</option><option>British</option><option>American</option><option>Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Preference</p>
              <select v-model="form.preference" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select preference</option>
                <option>Quiet room / High floor</option><option>Low floor</option><option>Near elevator</option><option>Non-smoking</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Date of Birth</p>
              <input type="text" v-model="form.dob" placeholder="Select date of birth"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Address</p>
              <input type="text" v-model="form.address" placeholder="Enter guest address"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
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
                <option value="">Select ID type</option>
                <option>National ID</option><option>Passport</option><option>Driver's License</option><option>Voter's Card</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Number</p>
              <input type="text" v-model="form.idNumber" placeholder="Enter ID number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Document Attachment</p>
            <div class="border border-dashed border-blue-300 rounded-lg px-4 py-3 text-center cursor-pointer hover:bg-blue-50 transition-colors">
              <p class="text-xs font-medium text-blue-600">Upload supporting document attachment</p>
            </div>
          </div>
        </div>

        <!-- Contact Person -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Contact Person</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Name</p>
              <input type="text" v-model="form.contactName" placeholder="Enter contact person name"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Number</p>
              <input type="text" v-model="form.contactPhone" placeholder="Enter contact person number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Notes</p>
            <textarea v-model="form.notes" rows="3"
              placeholder="Add service note, VIP detail, communication note, or guest handling instruction..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Right: Setup Summary -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Setup Summary</h3>

        <div>
          <p class="text-xs text-gray-500 mb-2">Guest Preview</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">New Guest Preview</p>
            <p class="text-xs text-blue-600">Type: {{ form.guestType || 'Not selected' }}</p>
            <p class="text-xs text-blue-600">Name: {{ form.fullName || 'Pending' }}</p>
            <p class="text-xs text-blue-600">Preference: {{ form.preference || 'Not selected' }}</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Attachment Status</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs text-gray-400 mb-1">No file uploaded yet</p>
            <button class="text-xs font-medium text-blue-600 hover:underline">Upload attachment</button>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Loyalty Default</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs font-bold text-gray-900 mb-1">Standard Guest Level</p>
            <p class="text-xs text-gray-500">Reward level starts at base tier</p>
            <p class="text-xs text-gray-500">Stay count begins from first check-in</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive } from 'vue'

const form = reactive({
  guestType: '', title: '', gender: '', fullName: '', phone: '',
  email: '', nationality: '', preference: '', dob: '', address: '',
  idType: '', idNumber: '', contactName: '', contactPhone: '', notes: '',
})
</script>