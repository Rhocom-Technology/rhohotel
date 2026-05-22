<template>
  <div class="p-6 space-y-4">
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ reservationType === 'Corporate' ? 'Corporate Reservation' : 'New Reservation' }}</h1>
        <p class="text-xs text-gray-400 mt-1">Create reservation records directly in Hotel Reservation.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="emit('close')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button :disabled="isSaving" @click="saveReservation(false)" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 disabled:opacity-40">Save Draft</button>
        <button :disabled="isSaving" @click="saveReservation(true)" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">Submit</button>
      </div>
    </div>

    <div v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">{{ errorMessage }}</div>
    <div v-if="successMessage" class="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-xs text-green-700">{{ successMessage }}</div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Reservation Type</p>
          <select v-model="reservationType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option>Individual</option>
            <option>Corporate</option>
            <option>Group</option>
            <option>House Use</option>
            <option>Complimentary</option>
            <option>OTA</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Arrival Date</p>
          <input v-model="form.from_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Departure Date</p>
          <input v-model="form.to_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Nights</p>
          <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-700">{{ nightsCount }}</div>
        </div>
      </div>
    </div>

    <!-- Group Details -->
    <div v-if="reservationType === 'Group'" class="bg-white rounded-xl border border-amber-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Group Details</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Group Name</p>
          <input v-model="form.group_name" type="text" placeholder="e.g. Dangote Wedding Party" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Billing Mode</p>
          <select v-model="form.group_billing_mode" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select billing mode</option>
            <option>Central</option>
            <option>Split</option>
          </select>
        </div>
        <div v-if="form.group_billing_mode === 'Central'" class="relative" ref="customerPickerRef">
          <p class="text-xs text-gray-500 mb-1.5">Master Payer (Customer) <span class="text-red-500">*</span></p>
          <input
            v-model="customerSearch"
            type="text"
            placeholder="Search customer by name…"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none"
            @input="onCustomerSearch"
            @focus="customerDropdownOpen = true"
          />
          <div v-if="customerDropdownOpen && filteredCustomers.length > 0"
            class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            <div
              v-for="c in filteredCustomers"
              :key="c.name"
              @mousedown.prevent="selectCustomer(c)"
              class="px-3 py-2 text-xs cursor-pointer hover:bg-gray-50 text-gray-700">
              {{ c.customer_name || c.name }}
            </div>
            <div v-if="filteredCustomers.length === 0 && customerSearch"
              class="px-3 py-2 text-xs text-gray-400">No customers found.</div>
          </div>
          <p v-if="form.group_master_customer" class="mt-1 text-xs text-green-600">✓ {{ form.group_master_customer }}</p>
        </div>
      </div>
    </div>

    <!-- OTA Details -->
    <div v-if="reservationType === 'OTA'" class="bg-white rounded-xl border border-purple-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">OTA Details</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">OTA Channel</p>
          <select v-model="form.ota_channel" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select channel</option>
            <option v-for="ch in otaChannels" :key="ch.name" :value="ch.name">{{ ch.name }}</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Collection Model</p>
          <select v-model="form.ota_collection_model" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select model</option>
            <option>Hotel Collect</option>
            <option>OTA Collect / Prepaid</option>
          </select>
        </div>
        <div v-if="form.ota_collection_model === 'OTA Collect / Prepaid'">
          <p class="text-xs text-gray-500 mb-1.5">Virtual Card Reference</p>
          <input v-model="form.ota_virtual_card_ref" type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Commission Amount (₦)</p>
          <input v-model.number="form.ota_commission_amount" type="number" min="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>
    </div>

    <!-- House Use / Complimentary Details -->
    <div v-if="reservationType === 'House Use' || reservationType === 'Complimentary'" class="bg-white rounded-xl border border-green-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">{{ reservationType }} Details</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Reason / Authorisation <span class="text-red-500">*</span></p>
          <textarea v-model="form.comp_reason" rows="2" placeholder="Who authorised this and why?" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Cost Centre</p>
          <input v-model="form.internal_cost_center" type="text" placeholder="Department cost centre" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Guest / Booker</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div v-if="reservationType === 'Corporate'">
          <p class="text-xs text-gray-500 mb-1.5">Corporate Guest</p>
          <select v-model="form.corporate_guest" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select corporate guest</option>
            <option v-for="g in corporateGuests" :key="g.name" :value="g.name">{{ g.hotel_guest_name || g.name }}</option>
          </select>
        </div>
        <div v-else>
          <p class="text-xs text-gray-500 mb-1.5">Individual Guest</p>
          <select v-model="form.individual_guest" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select guest</option>
            <option v-for="g in individualGuests" :key="g.name" :value="g.name">{{ g.hotel_guest_name || g.name }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <button @click="goToNewGuest" type="button" class="w-full px-3 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">+ New Guest</button>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Guest/Contact Name</p>
          <input v-model="form.primary_guest_name" type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Contact Phone</p>
          <input v-model="form.primary_guest_phone" type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Contact Email</p>
          <input v-model="form.primary_guest_email" type="email" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Rooms & Pricing</h3>
      <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select v-model="selectedRoomType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">All Types</option>
            <option v-for="t in roomTypes" :key="t.name" :value="t.name">{{ t.room_type || t.name }}</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Rate Code</p>
          <select v-model="selectedRateCode" @change="onRateCodeChange" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Default rate</option>
            <option v-for="r in eligibleRateCodes" :key="r.name" :value="r.name">{{ r.rate_code }}{{ r.rate_amount ? ' (' + Number(r.rate_amount).toLocaleString() + ')' : '' }}</option>
          </select>
        </div>
        <div class="relative" ref="roomPickerRef">
          <p class="text-xs text-gray-500 mb-1.5">Available Rooms</p>
          <!-- tag + search trigger -->
          <div
            @click="roomDropdownOpen = true"
            class="w-full min-h-[38px] px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus-within:ring-1 focus-within:ring-blue-400 cursor-text flex flex-wrap gap-1 items-center bg-white"
          >
            <span
              v-for="roomName in selectedRoom"
              :key="roomName"
              class="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium"
            >
              {{ roomName }}
              <button type="button" @click.stop="toggleRoomSelection(roomName)" class="hover:text-blue-900 leading-none">&times;</button>
            </span>
            <input
              v-model="roomSearch"
              @focus="roomDropdownOpen = true"
              @keydown.escape="roomDropdownOpen = false"
              placeholder="Search rooms…"
              class="flex-1 min-w-[80px] outline-none text-xs bg-transparent placeholder-gray-300"
            />
          </div>
          <!-- dropdown list -->
          <div
            v-if="roomDropdownOpen"
            class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
          >
            <p v-if="filteredAvailableRooms.length === 0" class="px-3 py-2.5 text-xs text-gray-400">No rooms available</p>
            <div
              v-for="room in filteredAvailableRooms"
              :key="room.name"
              @mousedown.prevent="toggleRoomSelection(room.name)"
              class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-gray-50"
              :class="selectedRoom.includes(room.name) ? 'bg-blue-50' : ''"
            >
              <span
                class="w-3.5 h-3.5 flex-shrink-0 rounded border flex items-center justify-center"
                :class="selectedRoom.includes(room.name) ? 'bg-blue-600 border-blue-600' : 'border-gray-300'"
              >
                <svg v-if="selectedRoom.includes(room.name)" class="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </span>
              <span class="text-xs text-gray-700">{{ room.name }} &bull; {{ room.room_type }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-end">
          <button @click="addRoom" class="w-full px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Add Room</button>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
          <select v-model="form.discount_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">None</option>
            <option>Percentage</option>
            <option>Fixed Amount</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Discount</p>
          <input v-model.number="form.discount" type="number" min="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>

      <div class="mt-4 overflow-x-auto border border-gray-100 rounded-lg">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate Code</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Meal Plan</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate/Night</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Nights</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Total</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="selectedRooms.length === 0">
              <td colspan="8" class="px-3 py-4 text-center text-xs text-gray-300">No rooms selected</td>
            </tr>
            <tr v-for="room in selectedRooms" :key="room.name" class="border-t border-gray-100">
              <td class="px-3 py-2 text-xs text-gray-700">{{ room.name }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ room.room_type }}</td>
              <td class="px-3 py-2 text-xs text-gray-500">{{ room.rate_code || '—' }}</td>
              <td class="px-3 py-2 text-xs text-gray-500">{{ room.meal_plan_snapshot || '—' }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(room.rate_per_night) }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ nightsCount }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(room.rate_per_night * nightsCount) }}</td>
              <td class="px-3 py-2 text-xs">
                <button @click="removeRoom(room.name)" class="text-red-500 hover:text-red-600">Remove</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Group Room Blocks -->
    <div v-if="reservationType === 'Group'" class="bg-white rounded-xl border border-amber-200 p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-gray-900">Room Blocks</h3>
        <button @click="addRoomBlock" type="button" class="px-3 py-1.5 text-xs font-medium text-amber-700 border border-amber-300 rounded-lg hover:bg-amber-50">+ Add Block</button>
      </div>
      <p class="text-xs text-gray-400 mb-3">Block room types to protect inventory for this group. Individual rooms are assigned later.</p>
      <div class="overflow-x-auto border border-gray-100 rounded-lg">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Blocked Qty</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate Code</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Notes</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="roomBlocks.length === 0">
              <td colspan="5" class="px-3 py-4 text-center text-xs text-gray-300">No blocks added</td>
            </tr>
            <tr v-for="(block, idx) in roomBlocks" :key="idx" class="border-t border-gray-100">
              <td class="px-3 py-1.5">
                <select v-model="block.room_type" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:outline-none">
                  <option value="">Select type</option>
                  <option v-for="t in roomTypes" :key="t.name" :value="t.name">{{ t.room_type || t.name }}</option>
                </select>
              </td>
              <td class="px-3 py-1.5">
                <input v-model.number="block.quantity" type="number" min="1" class="w-20 px-2 py-1.5 text-xs border border-gray-200 rounded focus:outline-none" />
              </td>
              <td class="px-3 py-1.5">
                <select v-model="block.rate_code" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:outline-none">
                  <option value="">Default</option>
                  <option v-for="r in eligibleRateCodes" :key="r.name" :value="r.name">{{ r.rate_code }}</option>
                </select>
              </td>
              <td class="px-3 py-1.5">
                <input v-model="block.notes" type="text" placeholder="Notes" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:outline-none" />
              </td>
              <td class="px-3 py-1.5">
                <button @click="removeRoomBlock(idx)" class="text-red-500 hover:text-red-600 text-xs">Remove</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Summary</h3>      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Subtotal: <span class="font-semibold">{{ formatCurrency(subTotal) }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Discount: <span class="font-semibold">{{ formatCurrency(discountAmount) }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Total Rooms: <span class="font-semibold">{{ selectedRooms.length }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-blue-50 border border-blue-100 text-xs">Grand Total: <span class="font-semibold text-blue-700">{{ formatCurrency(grandTotal) }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { callMethod } from '@/lib/api'

const props = defineProps({ type: { type: String, required: true } })
const emit = defineEmits(['close', 'saved'])
const router = useRouter()

const reservationTypes = ['Individual', 'Corporate', 'Group', 'House Use', 'Complimentary', 'OTA']
const reservationType = ref(reservationTypes.includes(props.type) ? props.type : 'Individual')
const form = ref({
  from_date: '',
  to_date: '',
  primary_guest_name: '',
  primary_guest_email: '',
  primary_guest_phone: '',
  corporate_guest: '',
  individual_guest: '',
  discount_type: '',
  discount: 0,
  // Group fields
  group_name: '',
  group_billing_mode: '',
  group_master_customer: '',
  // OTA fields
  ota_channel: '',
  ota_collection_model: '',
  ota_virtual_card_ref: '',
  ota_commission_amount: 0,
  // House Use / Comp fields
  comp_reason: '',
  internal_cost_center: '',
})

const errorMessage = ref('')
const successMessage = ref('')
const isSaving = ref(false)

const selectedRoomType = ref('')
const selectedRoom = ref([])
const selectedRooms = ref([])
const availableRooms = ref([])
const roomSearch = ref('')
const roomDropdownOpen = ref(false)
const roomPickerRef = ref(null)
const selectedRateCode = ref('')
const eligibleRateCodes = ref([])
const roomBlocks = ref([])

// Customer search for group master payer
const customerSearch = ref('')
const customerDropdownOpen = ref(false)
const customerPickerRef = ref(null)
const allCustomers = ref([])
const filteredCustomers = computed(() => {
  const q = customerSearch.value.trim().toLowerCase()
  if (!q) return allCustomers.value.slice(0, 20)
  return allCustomers.value.filter(c => (c.customer_name || c.name).toLowerCase().includes(q)).slice(0, 20)
})

async function loadCustomers() {
  try {
    const rows = await callMethod('frappe.client.get_list', {
      doctype: 'Customer',
      fields: ['name', 'customer_name'],
      order_by: 'customer_name asc',
      limit_page_length: 500,
    })
    allCustomers.value = Array.isArray(rows) ? rows : []
  } catch { allCustomers.value = [] }
}

function onCustomerSearch() {
  customerDropdownOpen.value = true
}

function selectCustomer(c) {
  form.value.group_master_customer = c.customer_name || c.name
  customerSearch.value = c.customer_name || c.name
  customerDropdownOpen.value = false
}

function handleCustomerClickOutside(e) {
  if (customerPickerRef.value && !customerPickerRef.value.contains(e.target)) {
    customerDropdownOpen.value = false
  }
}

const filteredAvailableRooms = computed(() => {
  const q = roomSearch.value.trim().toLowerCase()
  if (!q) return availableRooms.value
  return availableRooms.value.filter(
    (r) => r.name.toLowerCase().includes(q) || (r.room_type || '').toLowerCase().includes(q),
  )
})

function toggleRoomSelection(roomName) {
  const idx = selectedRoom.value.indexOf(roomName)
  if (idx === -1) {
    selectedRoom.value = [...selectedRoom.value, roomName]
  } else {
    selectedRoom.value = selectedRoom.value.filter((n) => n !== roomName)
  }
}

function handleClickOutside(e) {
  if (roomPickerRef.value && !roomPickerRef.value.contains(e.target)) {
    roomDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
  document.addEventListener('mousedown', handleCustomerClickOutside)
  loadCustomers()
})
onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
  document.removeEventListener('mousedown', handleCustomerClickOutside)
})

const corporateGuestsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Guest',
    fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
    filters: [['guest_type', '=', 'Corporate']],
    order_by: 'hotel_guest_name asc',
    limit_page_length: 500,
  },
  auto: true,
})

const individualGuestsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Guest',
    fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
    filters: [['guest_type', '=', 'Individual']],
    order_by: 'hotel_guest_name asc',
    limit_page_length: 500,
  },
  auto: true,
})

const roomTypesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Room Type',
    fields: ['name', 'room_type'],
    filters: [['is_active', '=', 1]],
    order_by: 'room_type asc',
    limit_page_length: 500,
  },
  auto: true,
})

const corporateGuests = computed(() => corporateGuestsResource.data || [])
const individualGuests = computed(() => individualGuestsResource.data || [])
const roomTypes = computed(() => roomTypesResource.data || [])

const otaChannelsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Market Place',
    fields: ['name'],
    order_by: 'name asc',
    limit_page_length: 200,
  },
  auto: true,
})
const otaChannels = computed(() => otaChannelsResource.data || [])

async function loadEligibleRateCodes() {
  try {
    const codes = await callMethod('rhohotel.rhocom_hotel.utils.billing_routing.get_eligible_rate_codes', {
      reservation_type: reservationType.value,
      check_in_date: form.value.from_date || undefined,
      room_type: selectedRoomType.value || undefined,
      nights: nightsCount.value || undefined,
    })
    eligibleRateCodes.value = Array.isArray(codes) ? codes : []
    if (selectedRateCode.value && !eligibleRateCodes.value.some((r) => r.name === selectedRateCode.value)) {
      selectedRateCode.value = ''
    }
  } catch {
    eligibleRateCodes.value = []
    selectedRateCode.value = ''
  }
}

watch(
  () => [reservationType.value, form.value.from_date, form.value.to_date, selectedRoomType.value],
  () => loadEligibleRateCodes(),
  { immediate: true },
)

async function onRateCodeChange() {
  // When a rate code changes, apply its meal plan to all existing room rows
  const rateDoc = eligibleRateCodes.value.find((r) => r.name === selectedRateCode.value)
  if (form.value.from_date && form.value.to_date && nightsCount.value > 0) {
    await loadAvailableRooms()
  }
  selectedRooms.value = selectedRooms.value.map((room) => ({
    ...room,
    rate_per_night: getPricedRoomRate(room),
    room_total: Math.max(0, (getPricedRoomRate(room) * nightsCount.value) - getRoomDiscount(room)),
    rate_code: rateDoc ? rateDoc.name : '',
    meal_plan_snapshot: rateDoc ? (rateDoc.meal_plan || '') : '',
    cancellation_policy_snapshot: rateDoc ? (rateDoc.cancellation_policy || '') : '',
  }))
}

function addRoomBlock() {
  roomBlocks.value.push({ room_type: '', quantity: 1, rate_code: '', notes: '' })
}

function removeRoomBlock(idx) {
  roomBlocks.value.splice(idx, 1)
}

const nightsCount = computed(() => {
  if (!form.value.from_date || !form.value.to_date) return 0
  const diff = Math.round((new Date(form.value.to_date) - new Date(form.value.from_date)) / 86400000)
  return diff > 0 ? diff : 0
})

function getRoomRate(room) {
  return Number(room?.rate_per_night ?? room?.rate ?? 0)
}

function getRoomDiscount(room) {
  return Number(room?.discount ?? 0)
}

function getRoomAmount(room) {
  const rate = getRoomRate(room)
  const discount = getRoomDiscount(room)
  const fallbackAmount = (rate * nightsCount.value) - discount
  return Number(room?.room_total ?? room?.total_amount ?? room?.amount ?? fallbackAmount)
}

function getPricedRoomRate(room) {
  const pricedRoom = availableRooms.value.find((r) => r.name === room.name)
  return pricedRoom ? getRoomRate(pricedRoom) : getRoomRate(room)
}

const subTotal = computed(() => selectedRooms.value.reduce((acc, room) => acc + (getRoomRate(room) * nightsCount.value), 0))
const discountAmount = computed(() => {
  const discount = Number(form.value.discount || 0)
  if (!discount || !form.value.discount_type) return 0
  if (form.value.discount_type === 'Percentage') return (subTotal.value * discount) / 100
  return discount
})
const grandTotal = computed(() => Math.max(0, subTotal.value - discountAmount.value))

watch(
  () => [form.value.from_date, form.value.to_date, selectedRoomType.value, selectedRateCode.value],
  () => {
    availableRooms.value = []
    selectedRoom.value = []
    roomSearch.value = ''
    if (form.value.from_date && form.value.to_date && nightsCount.value > 0) {
      loadAvailableRooms()
    }
  },
)

watch(
  () => form.value.corporate_guest,
  (guestName) => {
    if (!guestName) return
    const guest = corporateGuests.value.find((g) => g.name === guestName)
    if (!guest) return
    form.value.primary_guest_name = form.value.primary_guest_name || guest.hotel_guest_name || ''
    form.value.primary_guest_email = form.value.primary_guest_email || guest.email || ''
    form.value.primary_guest_phone = form.value.primary_guest_phone || guest.phone_number || ''
  },
)

watch(
  () => form.value.individual_guest,
  (guestName) => {
    if (!guestName) return
    const guest = individualGuests.value.find((g) => g.name === guestName)
    if (!guest) return
    form.value.primary_guest_name = form.value.primary_guest_name || guest.hotel_guest_name || ''
    form.value.primary_guest_email = form.value.primary_guest_email || guest.email || ''
    form.value.primary_guest_phone = form.value.primary_guest_phone || guest.phone_number || ''
  },
)

async function loadAvailableRooms() {
  try {
    const rows = await callMethod('rhohotel.rhocom_hotel.utils.room_availability.get_available_rooms', {
      check_in_dt: form.value.from_date,
      check_out_dt: form.value.to_date,
      room_type: selectedRoomType.value || undefined,
      rate_code: selectedRateCode.value || undefined,
    })
    availableRooms.value = Array.isArray(rows) ? rows : []
  } catch {
    availableRooms.value = []
  }
}

function addRoom() {
  if (!selectedRoom.value.length) return
  const rateDoc = eligibleRateCodes.value.find((r) => r.name === selectedRateCode.value)
  for (const roomName of selectedRoom.value) {
    const room = availableRooms.value.find((r) => r.name === roomName)
    if (!room) continue
    if (selectedRooms.value.some((r) => r.name === room.name)) continue
    selectedRooms.value.push({
      ...room,
      rate_per_night: getRoomRate(room),
      discount: getRoomDiscount(room),
      room_total: getRoomAmount(room),
      rate_code: rateDoc ? rateDoc.name : '',
      meal_plan_snapshot: rateDoc ? (rateDoc.meal_plan || '') : '',
      cancellation_policy_snapshot: rateDoc ? (rateDoc.cancellation_policy || '') : '',
    })
  }
  selectedRoom.value = []
  roomSearch.value = ''
  roomDropdownOpen.value = false
}

function removeRoom(roomName) {
  selectedRooms.value = selectedRooms.value.filter((r) => r.name !== roomName)
}

function goToNewGuest() {
  router.push({
    path: '/guests/new',
    query: { return_to: 'new_reservation', type: reservationType.value },
  })
}

function validateForm() {
  if (!form.value.from_date || !form.value.to_date || nightsCount.value < 1) return 'Select valid stay dates.'
  if (reservationType.value === 'Corporate' && !form.value.corporate_guest) return 'Corporate reservation requires a corporate guest.'
  if (reservationType.value === 'Group') {
    if (!form.value.primary_guest_name) return 'Group contact name is required.'
    if (selectedRooms.value.length === 0 && roomBlocks.value.length === 0) return 'Add at least one room or room block for a Group reservation.'
    if (form.value.group_billing_mode === 'Central' && !form.value.group_master_customer) return 'A master payer customer is required for Central billing mode.'
    return ''
  }
  if (reservationType.value === 'House Use' || reservationType.value === 'Complimentary') {
    if (!form.value.comp_reason) return `Reason / Authorisation is required for ${reservationType.value} reservations.`
    if (selectedRooms.value.length === 0) return 'Add at least one room.'
    return ''
  }
  if (!form.value.primary_guest_name || !form.value.primary_guest_phone) return 'Guest name and phone are required.'
  if (selectedRooms.value.length === 0) return 'Add at least one room.'
  return ''
}

async function saveReservation(submitAfterSave) {
  errorMessage.value = ''
  successMessage.value = ''

  const validationError = validateForm()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  isSaving.value = true
  try {
    const guestDoc = reservationType.value === 'Corporate'
      ? corporateGuests.value.find((g) => g.name === form.value.corporate_guest)
      : individualGuests.value.find((g) => g.name === form.value.individual_guest)

    const doc = {
      doctype: 'Hotel Reservation',
      source_channel: reservationType.value === 'OTA' ? 'Online' : 'Front Desk',
      reservation_type: reservationType.value,
      guest_profile_kind: reservationType.value === 'Corporate' ? 'Corporate Account' : 'Primary Guest',
      from_date: form.value.from_date,
      to_date: form.value.to_date,
      primary_guest_name: form.value.primary_guest_name,
      primary_guest_email: form.value.primary_guest_email,
      primary_guest_phone: form.value.primary_guest_phone,
      corporate_guest: reservationType.value === 'Corporate' ? form.value.corporate_guest : undefined,
      customer: guestDoc?.customer || undefined,
      // Group fields
      group_name: reservationType.value === 'Group' ? form.value.group_name : undefined,
      group_billing_mode: reservationType.value === 'Group' ? form.value.group_billing_mode : undefined,
      group_master_customer: (reservationType.value === 'Group' && form.value.group_billing_mode === 'Central') ? form.value.group_master_customer : undefined,
      // OTA fields
      ota_channel: reservationType.value === 'OTA' ? form.value.ota_channel : undefined,
      ota_collection_model: reservationType.value === 'OTA' ? form.value.ota_collection_model : undefined,
      ota_virtual_card_ref: (reservationType.value === 'OTA' && form.value.ota_collection_model === 'OTA Collect / Prepaid') ? form.value.ota_virtual_card_ref : undefined,
      ota_commission_amount: reservationType.value === 'OTA' ? Number(form.value.ota_commission_amount || 0) : undefined,
      // House Use / Comp fields
      comp_reason: (reservationType.value === 'House Use' || reservationType.value === 'Complimentary') ? form.value.comp_reason : undefined,
      internal_cost_center: (reservationType.value === 'House Use' || reservationType.value === 'Complimentary') ? form.value.internal_cost_center : undefined,
      // Pricing
      discount_type: form.value.discount_type || undefined,
      discount: Number(form.value.discount || 0),
      subtotal: Number(subTotal.value || 0),
      discount_amount: Number(discountAmount.value || 0),
      total_amount: Number(grandTotal.value || 0),
      net_total: Number(grandTotal.value || 0),
      rooms: selectedRooms.value.map((room) => ({
        room_number: room.name,
        rate_per_night: getRoomRate(room),
        number_of_nights: nightsCount.value,
        discount: getRoomDiscount(room),
        room_total: getRoomAmount(room),
        rate_code: room.rate_code || undefined,
        meal_plan_snapshot: room.meal_plan_snapshot || undefined,
        cancellation_policy_snapshot: room.cancellation_policy_snapshot || undefined,
        occupant_name: form.value.primary_guest_name,
        occupant_email: form.value.primary_guest_email,
        occupant_phone: form.value.primary_guest_phone,
      })),
      room_blocks: reservationType.value === 'Group' ? roomBlocks.value.filter((b) => b.room_type && b.quantity > 0).map((b) => ({
        room_type: b.room_type,
        quantity: b.quantity,
        rate_code: b.rate_code || undefined,
        notes: b.notes || undefined,
      })) : undefined,
    }

    const inserted = await callMethod('frappe.client.insert', { doc })
    let target = inserted

    if (submitAfterSave) {
      const docToSubmit = {
        ...inserted,
        reservation_status: inserted?.reservation_status || 'Confirmed',
      }
      if (docToSubmit.reservation_status === 'Draft' || docToSubmit.reservation_status === 'Hold') {
        docToSubmit.reservation_status = 'Confirmed'
      }

      target = await callMethod('frappe.client.submit', { doc: docToSubmit })
      successMessage.value = 'Reservation submitted successfully.'
    } else {
      successMessage.value = 'Reservation saved as draft.'
    }

    emit('saved', target)
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not save reservation.')
  } finally {
    isSaving.value = false
  }
}

function formatCurrency(amount) {
  return `₦${Number(amount || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>
