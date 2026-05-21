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
            <div class="relative flex-1">
              <input
                type="text"
                v-model="reservationQuery"
                @input="onReservationInput"
                @focus="onReservationFocus"
                @blur="onReservationBlur"
                placeholder="Search by ID, guest name, or phone"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                :class="form.reservation ? 'border-green-300 bg-green-50' : ''"
              />
              <div v-if="showReservationDropdown && reservationResults.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-56 overflow-y-auto">
                <button
                  v-for="r in reservationResults"
                  :key="r.name"
                  @mousedown.prevent="selectReservation(r)"
                  class="block w-full text-left px-4 py-2.5 text-xs hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                  <span class="font-semibold text-gray-900">{{ r.name }}</span>
                  <span class="text-gray-500 ml-2">{{ r.guest_name }}</span>
                  <span v-if="r.room_number" class="text-gray-400 ml-2">· Room {{ r.room_number }}</span>
                  <span class="ml-2 text-gray-400">· {{ r.from_date }}</span>
                </button>
              </div>
              <div v-if="reservationSearching"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                <p class="text-xs text-gray-400">Searching...</p>
              </div>
              <div v-if="!reservationSearching && showReservationDropdown && reservationResults.length === 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                <p class="text-xs text-gray-400">No pending reservations found.</p>
              </div>
            </div>
            <button v-if="form.reservation" @click="clearReservation"
              class="px-3 py-2.5 text-xs text-gray-500 hover:text-red-500 flex-shrink-0 transition-colors">
              ✕
            </button>
          </div>
          <p v-if="form.reservation" class="mt-1.5 text-xs text-green-600 font-medium">
            ✓ {{ form.reservation }} linked
          </p>
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
                <div v-if="!guestSearching && showGuestDropdown && guestResults.length === 0 && guestQuery.length >= 1"
                  class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 px-4 py-3">
                  <p class="text-xs text-gray-400">No guests found. Create a new one.</p>
                </div>
              </div>
              <button @click="goToNewGuest"
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
              <input v-if="selectedGuest.id_type" type="text" :value="selectedGuest.id_type" readonly
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50" />
              <select v-else v-model="form.id_type"
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
              <p class="text-xs text-gray-500 mb-1.5">ID Number</p>
              <input type="text" :value="selectedGuest.id_number || ''" readonly
                placeholder="Auto-filled from guest"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50" />
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
                <option value="Fixed Amount">Fixed Amount</option>
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

          <!-- Reservation Payment / Invoice Notice -->
          <div v-if="reservationNotices.length" class="mb-3 bg-amber-50 border border-amber-200 rounded-xl px-5 py-4 space-y-1">
            <p class="text-xs font-bold text-amber-700 mb-1">Reservation Payment Notice</p>
            <p v-for="(n, i) in reservationNotices" :key="i" class="text-xs text-amber-700">{{ n }}</p>
          </div>

          <div class="mt-3">
            <p class="text-xs text-gray-500 mb-1.5">Reservation Source</p>
            <select v-model="form.reservation_source"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">— Select source —</option>
              <option v-for="mp in marketPlaces" :key="mp" :value="mp">{{ mp }}</option>
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
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-sm font-bold text-gray-900">Guest Preferences</h3>
            <span v-if="preferencesAutoFilled" class="text-xs text-green-600 font-medium">✓ Auto-filled from guest profile</span>
          </div>
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
            <div v-if="form.discount_type !== 'None' && form.discount > 0" class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Discount ({{ form.discount_type === 'Percentage' ? form.discount + '%' : 'Fixed' }})</span>
              <span class="text-xs font-semibold text-red-500">- {{ formatCurrency(discountDisplayAmount) }}</span>
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
import { callMethodForm } from '@/lib/api'

const router = useRouter()
const route = useRoute()

// ---- Reservation search ----
const reservationQuery = ref('')
const reservationResults = ref([])
const reservationSearching = ref(false)
const showReservationDropdown = ref(false)
let reservationDebounce = null

async function fetchReservations(query = '') {
  reservationSearching.value = true
  try {
    const rows = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.search_reservations', { query })
    reservationResults.value = Array.isArray(rows) ? rows : []
  } catch {
    reservationResults.value = []
  } finally {
    reservationSearching.value = false
  }
}

function onReservationInput() {
  form.reservation = ''
  clearTimeout(reservationDebounce)
  showReservationDropdown.value = true
  reservationDebounce = setTimeout(() => fetchReservations(reservationQuery.value), 300)
}

function onReservationFocus() {
  showReservationDropdown.value = true
  if (reservationResults.value.length === 0 && !reservationSearching.value) {
    fetchReservations(reservationQuery.value)
  }
}

function onReservationBlur() {
  setTimeout(() => { showReservationDropdown.value = false }, 150)
}

async function selectReservation(r) {
  // Set canonical_reservation for canonical results so billing routing works
  if (r.source_type === 'canonical') {
    form.canonical_reservation = r.name
    form.reservation = ''  // don't set legacy reservation field for canonical
  } else {
    form.reservation = r.name
    form.canonical_reservation = ''
  }
  reservationQuery.value = r.name
  showReservationDropdown.value = false

  if (!form.reservation_source) {
    form.reservation_source = 'Reservation'
  }

  if (r.guest_phone) {
    form.contact_number = r.guest_phone
  }

  if (r.guest_name) {
    guestQuery.value = r.guest_name
    selectedGuest.value = {
      hotel_guest_name: r.guest_name,
      phone_number: r.guest_phone || '',
      email: r.guest_email || '',
    }
  }

  const lookup = (r.guest_name || r.guest_phone || r.guest_email || '').trim()
  if (lookup.length >= 2) {
    try {
      const rows = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.search_guests', {
        query: lookup,
      })
      const candidates = Array.isArray(rows) ? rows : []
      const exact = candidates.find(g =>
        (r.guest_name && (g.hotel_guest_name || '').toLowerCase() === r.guest_name.toLowerCase())
        || (r.guest_phone && g.phone_number === r.guest_phone)
        || (r.guest_email && (g.email || '').toLowerCase() === r.guest_email.toLowerCase())
      )
      const matchedGuest = exact || candidates[0]
      if (matchedGuest) {
        form.guest = matchedGuest.name
        guestQuery.value = matchedGuest.hotel_guest_name
        selectedGuest.value = matchedGuest
        applyPreferenceTagsFromGuest(matchedGuest)
        if (matchedGuest.id_type) form.id_type = matchedGuest.id_type
        if (matchedGuest.phone_number) {
          form.contact_number = matchedGuest.phone_number
        }
      }
    } catch {
      // Keep reservation guest details if lookup fails.
    }
  }

  if (r.room_number && !form.room_number) {
    form.room_number = r.room_number
    onRoomSelect()
  }
  if (r.number_of_nights && !form.number_of_nights) {
    form.number_of_nights = r.number_of_nights
  }
  if (r.rate && !form.rate_amount) {
    form.rate_amount = r.rate
  }
}

function clearReservation() {
  form.reservation = ''
  reservationQuery.value = ''
  reservationResults.value = []
}

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
  resetPreferenceTags()
  clearTimeout(guestDebounce)
  if (guestQuery.value.length < 1) {
    guestResults.value = []
    showGuestDropdown.value = false
    return
  }
  guestSearching.value = true
  showGuestDropdown.value = true
  guestDebounce = setTimeout(async () => {
    try {
      const rows = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.search_guests', {
        query: guestQuery.value,
      })
      guestResults.value = Array.isArray(rows) ? rows : []
    } catch {
      guestResults.value = []
    } finally {
      guestSearching.value = false
    }
  }, 300)
}

async function selectGuest(g) {
  form.guest = g.name
  guestQuery.value = g.hotel_guest_name
  selectedGuest.value = g
  resetPreferenceTags()
  applyPreferenceTagsFromGuest(g)
  if (g.phone_number) form.contact_number = g.phone_number
  if (g.id_type) form.id_type = g.id_type
  showGuestDropdown.value = false
  guestResults.value = []

  // Fetch full guest doc to get id_number and any other fields not in search results
  try {
    const fullDoc = await callMethodForm('frappe.client.get', {
      doctype: 'Hotel Guest',
      name: g.name,
    })
    if (fullDoc) {
      selectedGuest.value = { ...selectedGuest.value, ...fullDoc }
      if (fullDoc.id_type && !form.id_type) form.id_type = fullDoc.id_type
      // Always populate contact_number from phone_number (primary contact),
      // never from contact_number which is "Contact Person Number" (emergency contact).
      if (fullDoc.phone_number) form.contact_number = fullDoc.phone_number
    }
  } catch { /* keep partial data from search */ }
}

function goToNewGuest() {
  router.push({
    path: '/guests/new',
    query: {
      return_to: 'checkin',
      room: form.room_number || '',
      room_type: form.room_type || '',
      nights: form.number_of_nights || 1,
      check_in_dt: form.check_in_datetime || '',
    },
  })
}

function onGuestBlur() {
  setTimeout(() => { showGuestDropdown.value = false }, 150)
}

// ---- Market Places ----
const marketPlaces = ref([])

async function loadMarketPlaces() {
  try {
    const rows = await callMethodForm('frappe.client.get_list', {
      doctype: 'Market Place',
      fields: JSON.stringify(['name']),
      limit_page_length: 100,
    })
    marketPlaces.value = Array.isArray(rows) ? rows.map(r => r.name) : []
  } catch { /* ignore */ }
}

// ---- Room data ----
const availableRooms = ref([])
const loadingRooms = ref(false)
const selectedRoomType = ref('')
const roomTypes = ref([])

async function loadRoomTypes() {
  try {
    const rows = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.get_room_types')
    roomTypes.value = Array.isArray(rows) ? rows : []
  } catch { /* ignore */ }
}

async function loadAvailableRooms() {
  loadingRooms.value = true
  try {
    // Build check-out datetime from check-in + number of nights
    const params = { room_type: selectedRoomType.value }
    if (form.check_in_datetime) {
      params.check_in_dt = form.check_in_datetime
      const ciDate = parseLocalDateTime(form.check_in_datetime)
      if (ciDate) {
        ciDate.setDate(ciDate.getDate() + parseInt(form.number_of_nights || 1))
        params.check_out_dt = formatServerDateTime(ciDate)
      }
    }
    // Pass the reservation so its rooms are not excluded by availability check
    const preReservation = String(route.query.reservation || '').trim()
    if (preReservation) params.exclude_reservation = preReservation

    const rows = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.get_available_rooms', params)
    availableRooms.value = Array.isArray(rows) ? rows : []

    // Pre-fill from query params after rooms are loaded
    const preRoom = String(route.query.room || '').trim()
    const preRoomType = String(route.query.room_type || '').trim()
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
        // Room still not in list (e.g. wrong status) — inject it so the select shows it
        const injected = {
          name: preRoom,
          room_number: preRoom,
          room_type: preRoomType || '',
          floor: '',
          default_rate: 0,
        }
        availableRooms.value = [injected, ...availableRooms.value]
        form.room_number = preRoom
        if (preRoomType) {
          form.room_type = preRoomType
          selectedRoomType.value = preRoomType
        }
        onRoomSelect()
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

const defaultPreferenceTags = [
  { label: 'High Floor',   active: false, activeClass: 'bg-blue-100 text-blue-600' },
  { label: 'Quiet Wing',   active: false, activeClass: 'bg-green-100 text-green-600' },
  { label: 'Late Arrival', active: false, activeClass: 'bg-yellow-100 text-yellow-600' },
  { label: 'VIP',          active: false, activeClass: 'bg-purple-100 text-purple-600' },
  { label: 'Extra Towels', active: false, activeClass: 'bg-gray-100 text-gray-600' },
]

const preferenceTags = reactive([...defaultPreferenceTags.map(t => ({ ...t }))])

function resetPreferenceTags() {
  preferenceTags.splice(0, preferenceTags.length, ...defaultPreferenceTags.map(t => ({ ...t })))
  preferencesAutoFilled.value = false
}

const selectedPreferenceLabels = computed(() =>
  preferenceTags.filter(tag => tag.active).map(tag => tag.label)
)

const roomPreferencesPayload = computed(() => selectedPreferenceLabels.value.join(', '))

const activeClasses = [
  'bg-blue-100 text-blue-600',
  'bg-green-100 text-green-600',
  'bg-yellow-100 text-yellow-600',
  'bg-purple-100 text-purple-600',
  'bg-gray-100 text-gray-600',
  'bg-orange-100 text-orange-600',
  'bg-pink-100 text-pink-600',
  'bg-teal-100 text-teal-600',
]

const preferencesAutoFilled = ref(false)

function applyPreferenceTagsFromGuest(guest) {
  const raw = String(guest?.preference || '')
  if (!raw.trim()) {
    preferencesAutoFilled.value = false
    return
  }

  const guestPrefs = raw.split(',').map(v => v.trim()).filter(Boolean)
  const lowerPrefs = guestPrefs.map(v => v.toLowerCase())

  // Activate existing tags that match
  preferenceTags.forEach(tag => {
    tag.active = lowerPrefs.includes(tag.label.toLowerCase())
  })

  // Add any guest preference that is not already in preferenceTags
  guestPrefs.forEach((pref, idx) => {
    const exists = preferenceTags.some(t => t.label.toLowerCase() === pref.toLowerCase())
    if (!exists) {
      preferenceTags.push({
        label: pref,
        active: true,
        activeClass: activeClasses[preferenceTags.length % activeClasses.length],
      })
    }
  })

  preferencesAutoFilled.value = guestPrefs.length > 0
}

const expectedCheckoutDisplay = computed(() => {
  if (!form.check_in_datetime || !form.number_of_nights) return '—'
  const dt = parseLocalDateTime(form.check_in_datetime)
  if (!dt) return '—'
  dt.setDate(dt.getDate() + parseInt(form.number_of_nights))
  return dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
})

function parseLocalDateTime(value) {
  if (!value) return null
  const normalized = String(value).replace(' ', 'T')
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatServerDateTime(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

const estimatedTotal = computed(() => {
  const nights = parseInt(form.number_of_nights) || 0
  const rate = parseFloat(form.rate_amount) || 0
  let total = nights * rate
  if (form.discount_type === 'Percentage' && form.discount > 0) {
    total = total * (1 - form.discount / 100)
  } else if (form.discount_type === 'Fixed Amount' && form.discount > 0) {
    total = total - form.discount
  }
  return Math.max(0, total)
})

const discountDisplayAmount = computed(() => {
  const nights = parseInt(form.number_of_nights) || 0
  const rate = parseFloat(form.rate_amount) || 0
  const subtotal = nights * rate
  if (form.discount_type === 'Percentage' && form.discount > 0) {
    return subtotal * (form.discount / 100)
  } else if (form.discount_type === 'Fixed Amount' && form.discount > 0) {
    return form.discount
  }
  return 0
})

function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₦ 0.00'
  return `₦ ${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}

// ---- Submit ----
const submitting = ref(false)
const errorMsg = ref('')
const reservationNotices = ref([])

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
      canonical_reservation: form.canonical_reservation || '',
      reservation_source: form.reservation_source || '',
      discount_type: form.discount_type || 'None',
      discount: form.discount || 0,
      late_checkout: form.late_checkout ? 1 : 0,
      housekeeping_notes: form.housekeeping_notes || '',
      keycard_assigned: form.keycard_assigned || '',
      room_preferences: roomPreferencesPayload.value,
      id_type: form.id_type || '',
      contact_number: form.contact_number || '',
    }
    const data = await callMethodForm('rhohotel.rhocom_hotel.api.checkin.create_checkin', params)
    if (data?.name) {
      router.push({ name: 'CheckInDetail', params: { id: data.name } })
    } else {
      errorMsg.value = 'Unexpected response from server.'
    }
  } catch (e) {
    errorMsg.value = String(e?.message || 'Network error — please try again.')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRoomTypes()
  loadAvailableRooms()
  loadMarketPlaces()

  const preReservation = String(route.query.reservation || '').trim()
  const preGuest = String(route.query.guest || '').trim()
  const preGuestName = String(route.query.guest_name || '').trim()
  const preGuestPhone = String(route.query.guest_phone || '').trim()
  const preGuestEmail = String(route.query.guest_email || '').trim()
  const preNights = parseInt(route.query.nights || '0')
  const preCheckoutDate = String(route.query.checkout_date || '').trim()
  const preDiscountType = String(route.query.discount_type || '').trim()
  const preDiscount = parseFloat(route.query.discount || '0')
  const preAdvancePaid = parseFloat(route.query.advance_paid || '0')
  const preSalesInvoice = String(route.query.sales_invoice || '').trim()

  // Pre-fill number_of_nights from query before async reservation fetch
  // so selectReservation's guard (!form.number_of_nights) won't overwrite it.
  if (preNights >= 1) {
    form.number_of_nights = preNights
  } else if (preCheckoutDate && form.check_in_datetime) {
    const ci = new Date(form.check_in_datetime)
    const co = new Date(preCheckoutDate)
    const diff = Math.round((co - ci) / 86400000)
    if (diff >= 1) form.number_of_nights = diff
  }

  if (preDiscountType && preDiscountType !== 'None') {
    form.discount_type = preDiscountType
    if (preDiscount > 0) form.discount = preDiscount
  }

  // Build notices for the front-desk agent
  const notices = []
  if (preAdvancePaid > 0) {
    notices.push(`Advance paid from reservation: ${formatCurrency(preAdvancePaid)}. Verify before charging the guest again.`)
  }
  if (preSalesInvoice) {
    notices.push(`Sales Invoice ${preSalesInvoice} already exists for this reservation.`)
  }
  reservationNotices.value = notices

  if (preReservation) {
    reservationQuery.value = preReservation
    fetchReservations(preReservation).then(() => {
      const match = reservationResults.value.find(r => r.name === preReservation)
      if (match) selectReservation(match)
    })
  }

  if (preGuest) {
    form.guest = preGuest
    // Fetch full guest doc to populate name display and phone
    callMethodForm('frappe.client.get', { doctype: 'Hotel Guest', name: preGuest })
      .then((doc) => {
        if (doc) {
          selectedGuest.value = doc
          guestQuery.value = doc.hotel_guest_name || preGuest
          if (doc.phone_number) form.contact_number = doc.phone_number
          if (doc.id_type && !form.id_type) form.id_type = doc.id_type
          applyPreferenceTagsFromGuest(doc)
        }
      })
      .catch(() => { guestQuery.value = preGuest })
  }
  if (preGuestName) {
    guestQuery.value = preGuestName
    selectedGuest.value = {
      ...selectedGuest.value,
      hotel_guest_name: preGuestName,
      phone_number: preGuestPhone || selectedGuest.value?.phone_number || '',
      email: preGuestEmail || selectedGuest.value?.email || '',
    }

    if (!preGuest) {
      callMethodForm('rhohotel.rhocom_hotel.api.checkin.search_guests', { query: preGuestName })
        .then((rows) => {
          const list = Array.isArray(rows) ? rows : []
          const exact = list.find((g) => (g.hotel_guest_name || '').toLowerCase() === preGuestName.toLowerCase())
          const pick = exact || list[0]
          if (pick) {
            form.guest = pick.name
            selectedGuest.value = pick
            applyPreferenceTagsFromGuest(pick)
            if (pick.id_type) form.id_type = pick.id_type
            if (pick.phone_number) {
              form.contact_number = pick.phone_number
            }
          }
        })
        .catch(() => {
          // Keep name-only prefill when guest lookup fails.
        })
    }
  }
  if (preGuestPhone && !form.contact_number) {
    form.contact_number = preGuestPhone
  }
})
</script>
