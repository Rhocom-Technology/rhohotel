<template>
  <div class="space-y-5">
    <div>
      <p class="text-xs text-gray-400">Front desk • new check-in</p>
    </div>

    <!-- Top Action Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Check-In</h2>
        <p class="text-xs text-gray-400 mt-0.5">Complete all required fields to register arrival</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="$router.back()" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Cancel
        </button>
        <button @click="submitCheckIn"
          :disabled="submitting"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          {{ submitting ? 'Checking In...' : 'Confirm Check-In' }}
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <p class="text-xs font-bold text-red-600 mb-1">Check-in Failed</p>
      <p class="text-xs text-red-500">{{ errorMsg }}</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

      <!-- LEFT COLUMN -->
      <div class="space-y-5">

        <!-- Reservation -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center gap-4">
            <p class="text-xs font-medium text-gray-500 flex-shrink-0">Reservation (optional)</p>
            <input type="text" v-model="form.reservation"
              placeholder="Leave blank for walk-in"
              class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <!-- Guest Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Guest Details</h3>
          <p class="text-xs text-gray-400 mb-4">Search an existing guest or create a new one</p>

          <div class="mb-4 relative">
            <p class="text-xs text-gray-500 mb-1.5">Guest <span class="text-red-400">*</span></p>
            <div class="flex items-center gap-3">
              <div class="relative flex-1">
                <input
                  type="text"
                  v-model="guestQuery"
                  @input="onGuestInput"
                  @focus="showGuestDropdown = guestResults.length > 0"
                  @blur="onGuestBlur"
                  placeholder="Search by name, phone, or email"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :class="form.guest ? 'border-green-300 bg-green-50' : ''"
                />
                <!-- Guest Dropdown -->
                <div v-if="showGuestDropdown && guestResults.length > 0"
                  class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
                  <button
                    v-for="g in guestResults"
                    :key="g.name"
                    @mousedown.prevent="selectGuest(g)"
                    class="block w-full text-left px-4 py-2.5 text-xs hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                    <span class="font-semibold text-gray-900">{{ g.hotel_guest_name }}</span>
                    <span class="text-gray-400 ml-2">{{ g.phone_number || g.email || '' }}</span>
                  </button>
                </div>
                <div v-if="guestSearching" class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                  <p class="text-xs text-gray-400">Searching...</p>
                </div>
                <div v-if="!guestSearching && showGuestDropdown && guestResults.length === 0 && guestQuery.length >= 2"
                  class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                  <p class="text-xs text-gray-400">No guests found. Create a new one.</p>
                </div>
              </div>
              <button @click="$router.push('/guests/new')"
                class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex-shrink-0">
                New Guest
              </button>
            </div>
            <p v-if="form.guest" class="mt-1.5 text-xs text-green-600 font-medium">
              ✓ {{ guestQuery }} selected
            </p>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone</p>
              <input type="text" :value="selectedGuest.phone_number || ''" readonly
                placeholder="Auto-filled from guest"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input type="text" :value="selectedGuest.email || ''" readonly
                placeholder="Auto-filled from guest"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Type</p>
              <select v-model="form.id_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select ID type</option>
                <option>National ID</option>
                <option>International Passport</option>
                <option>Driver's License</option>
                <option>Voter's Card</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Number</p>
              <input type="text" v-model="form.contact_number"
                placeholder="Direct contact for this stay"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Room and Rate -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Room and Rate</h3>
          <p class="text-xs text-gray-400 mb-4">Assign room and define pricing for this stay</p>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Check-in Date &amp; Time <span class="text-red-400">*</span></p>
              <input type="datetime-local" v-model="form.check_in_datetime"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nights <span class="text-red-400">*</span></p>
              <input type="number" v-model.number="form.number_of_nights" min="1"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected Check-out</p>
              <input type="text" :value="expectedCheckoutDisplay" readonly
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50" />
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <select v-model="selectedRoomType" @change="onRoomTypeChange"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">All Types</option>
                <option v-for="rt in roomTypes" :key="rt.name" :value="rt.name">{{ rt.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Number <span class="text-red-400">*</span></p>
              <select v-model="form.room_number" @change="onRoomSelect"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                :disabled="loadingRooms">
                <option value="">{{ loadingRooms ? 'Loading...' : 'Select room' }}</option>
                <option v-for="r in availableRooms" :key="r.name" :value="r.name">
                  {{ r.room_number || r.name }} — {{ r.room_type }} (Floor {{ r.floor }})
                </option>
              </select>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nightly Rate <span class="text-red-400">*</span></p>
              <input type="number" v-model.number="form.rate_amount" min="0"
                placeholder="Enter room rate"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
              <select v-model="form.discount_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="None">None</option>
                <option value="Percentage">Percentage</option>
                <option value="Amount">Amount</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Discount</p>
              <input type="number" v-model.number="form.discount" min="0"
                :disabled="form.discount_type === 'None'"
                placeholder="0"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
            </div>
          </div>

          <div class="mt-3">
            <p class="text-xs text-gray-500 mb-1.5">Reservation Source</p>
            <select v-model="form.reservation_source"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Walk-in</option>
              <option value="Walk in">Walk-in</option>
              <option value="Reservation">Reservation</option>
              <option value="Online Booking">Online Booking</option>
              <option value="Corporate">Corporate</option>
              <option value="Referral">Referral</option>
            </select>
          </div>
        </div>

        <!-- Notes -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Housekeeping Notes</h3>
          <textarea v-model="form.housekeeping_notes" rows="4"
            placeholder="Special requests, room setup instructions, guest preferences for housekeeping..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="space-y-5">

        <!-- Guest Preferences -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Guest Preferences</h3>
          <p class="text-xs text-gray-400 mb-4">Preference tags and special arrival options</p>

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
              <span class="text-sm font-medium text-gray-700">Late Check Out</span>
              <div class="relative">
                <input type="checkbox" v-model="form.late_checkout" class="sr-only" />
                <div class="w-10 h-5 rounded-full transition-colors" :class="form.late_checkout ? 'bg-blue-600' : 'bg-gray-200'">
                  <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
                    :class="form.late_checkout ? 'translate-x-5' : ''"></div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- Key Card -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Key Card</h3>
          <p class="text-xs text-gray-400 mb-4">Enter access card number or reference</p>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Key Card / Access Number</p>
            <input type="text" v-model="form.keycard_assigned"
              placeholder="Key card number or reference"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <!-- Stay Summary -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Stay Summary</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Guest</span>
              <span class="text-xs font-semibold text-gray-900">{{ guestQuery || '—' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Room</span>
              <span class="text-xs font-semibold text-gray-900">{{ form.room_number || '—' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Room Type</span>
              <span class="text-xs font-semibold text-gray-900">{{ form.room_type || '—' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Nights</span>
              <span class="text-xs font-semibold text-gray-900">{{ form.number_of_nights }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Nightly Rate</span>
              <span class="text-xs font-semibold text-gray-900">{{ formatCurrency(form.rate_amount) }}</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <span class="text-xs font-bold text-gray-900">Est. Total</span>
              <span class="text-xs font-bold text-blue-600">{{ formatCurrency(estimatedTotal) }}</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Actions</h3>
          <div class="flex items-center gap-3 flex-wrap">
            <button @click="submitCheckIn"
              :disabled="submitting"
              class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50">
              {{ submitting ? 'Checking In...' : 'Confirm Check-In' }}
            </button>
            <button @click="$router.back()"
              class="px-5 py-2.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// ---- Guest search ----
const guestQuery = ref('')
const guestResults = ref([])
const guestSearching = ref(false)
const showGuestDropdown = ref(false)
const selectedGuest = ref({})
let guestDebounce = null

function onGuestInput() {
  form.guest = ''
  selectedGuest.value = {}
  clearTimeout(guestDebounce)
  if (guestQuery.value.length < 2) {
    guestResults.value = []
    showGuestDropdown.value = false
    return
  }
  guestSearching.value = true
  showGuestDropdown.value = true
  guestDebounce = setTimeout(async () => {
    try {
      const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.search_guests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
        body: new URLSearchParams({ query: guestQuery.value }),
      })
      const data = await res.json()
      guestResults.value = data.message || []
    } catch {
      guestResults.value = []
    } finally {
      guestSearching.value = false
    }
  }, 300)
}

function selectGuest(g) {
  form.guest = g.name
  guestQuery.value = g.hotel_guest_name
  selectedGuest.value = g
  if (!form.contact_number && g.phone_number) form.contact_number = g.phone_number
  showGuestDropdown.value = false
  guestResults.value = []
}

function onGuestBlur() {
  setTimeout(() => { showGuestDropdown.value = false }, 150)
}

// ---- Room data ----
const availableRooms = ref([])
const loadingRooms = ref(false)
const selectedRoomType = ref('')
const roomTypes = ref([])

async function loadRoomTypes() {
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_room_types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({}),
    })
    const data = await res.json()
    roomTypes.value = data.message || []
  } catch { /* ignore */ }
}

async function loadAvailableRooms() {
  loadingRooms.value = true
  try {
    // Build check-out datetime from check-in + number of nights
    const params = { room_type: selectedRoomType.value }
    if (form.check_in_datetime) {
      params.check_in_dt = form.check_in_datetime
      const ciDate = new Date(form.check_in_datetime)
      ciDate.setDate(ciDate.getDate() + parseInt(form.number_of_nights || 1))
      params.check_out_dt = ciDate.toISOString().slice(0, 16)
    }
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_available_rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams(params),
    })
    const data = await res.json()
    availableRooms.value = data.message || []
    // Pre-fill from query params after rooms are loaded
    const preRoom = route.query.room
    const preRoomType = route.query.room_type
    if (preRoomType && !form.room_type) {
      selectedRoomType.value = preRoomType
      form.room_type = preRoomType
    }
    if (preRoom && !form.room_number) {
      const match = availableRooms.value.find(r => r.name === preRoom || r.room_number === preRoom)
      if (match) {
        form.room_number = match.name
        onRoomSelect()
      } else {
        // Room not in available list (e.g. already occupied), still set it
        form.room_number = preRoom
      }
    }
  } catch {
    availableRooms.value = []
  } finally {
    loadingRooms.value = false
  }
}

function onRoomTypeChange() {
  form.room_number = ''
  form.room_type = selectedRoomType.value
  form.rate_amount = 0
  loadAvailableRooms()
}

function onRoomSelect() {
  const room = availableRooms.value.find(r => r.name === form.room_number)
  if (room) {
    form.room_type = room.room_type
    selectedRoomType.value = room.room_type
    if (room.default_rate) form.rate_amount = room.default_rate
  }
}

// ---- Form ----
const now = new Date()
const nowLocal = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

const form = reactive({
  guest: '',
  room_number: '',
  room_type: '',
  rate_amount: 0,
  number_of_nights: 1,
  check_in_datetime: nowLocal,
  rate_type: '',
  reservation: '',
  reservation_source: '',
  discount_type: 'None',
  discount: 0,
  late_checkout: false,
  housekeeping_notes: '',
  keycard_assigned: '',
  id_type: '',
  contact_number: '',
})

const preferenceTags = reactive([
  { label: 'High Floor',   active: false, activeClass: 'bg-blue-100 text-blue-600' },
  { label: 'Quiet Wing',   active: false, activeClass: 'bg-green-100 text-green-600' },
  { label: 'Late Arrival', active: false, activeClass: 'bg-yellow-100 text-yellow-600' },
  { label: 'VIP',          active: false, activeClass: 'bg-purple-100 text-purple-600' },
  { label: 'Extra Towels', active: false, activeClass: 'bg-gray-100 text-gray-600' },
])

const expectedCheckoutDisplay = computed(() => {
  if (!form.check_in_datetime || !form.number_of_nights) return '—'
  const dt = new Date(form.check_in_datetime)
  dt.setDate(dt.getDate() + parseInt(form.number_of_nights))
  return dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
})

const estimatedTotal = computed(() => {
  const nights = parseInt(form.number_of_nights) || 0
  const rate = parseFloat(form.rate_amount) || 0
  let total = nights * rate
  if (form.discount_type === 'Percentage' && form.discount > 0) {
    total = total * (1 - form.discount / 100)
  } else if (form.discount_type === 'Amount' && form.discount > 0) {
    total = total - form.discount
  }
  return Math.max(0, total)
})

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

// ---- Submit ----
const submitting = ref(false)
const errorMsg = ref('')

async function submitCheckIn() {
  errorMsg.value = ''

  if (!form.guest) {
    errorMsg.value = 'Please select a guest.'; return
  }
  if (!form.room_number) {
    errorMsg.value = 'Please select a room.'; return
  }
  if (!form.rate_amount || form.rate_amount <= 0) {
    errorMsg.value = 'Rate amount must be greater than zero.'; return
  }
  if (!form.number_of_nights || form.number_of_nights < 1) {
    errorMsg.value = 'Number of nights must be at least 1.'; return
  }

  submitting.value = true
  try {
    const params = {
      guest: form.guest,
      room_number: form.room_number,
      room_type: form.room_type,
      rate_amount: form.rate_amount,
      number_of_nights: form.number_of_nights,
      check_in_datetime: form.check_in_datetime,
      rate_type: form.rate_type || '',
      reservation: form.reservation || '',
      reservation_source: form.reservation_source || '',
      discount_type: form.discount_type || 'None',
      discount: form.discount || 0,
      late_checkout: form.late_checkout ? 1 : 0,
      housekeeping_notes: form.housekeeping_notes || '',
      keycard_assigned: form.keycard_assigned || '',
      id_type: form.id_type || '',
      contact_number: form.contact_number || '',
    }
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.create_checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams(params),
    })
    const data = await res.json()
    if (data.exc) {
      const match = data.exc.match(/frappe\.exceptions\.\w+: (.+)/m)
      errorMsg.value = match ? match[1] : (data.exc_type || 'Check-in failed. Please review the details.')
      return
    }
    if (data.message && data.message.name) {
      router.push('/check-ins/' + data.message.name)
    } else {
      errorMsg.value = 'Unexpected response from server.'
    }
  } catch (e) {
    errorMsg.value = 'Network error — please try again.'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRoomTypes()
  loadAvailableRooms()
})
</script>
