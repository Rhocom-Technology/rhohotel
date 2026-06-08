<template>
  <div class="space-y-5">
    <!-- Page Header -->
    <div>
      <p class="text-xs text-gray-400 mb-1">Front Desk / Available Rooms</p>
      <h1 class="text-2xl font-bold text-gray-900">Available Rooms</h1>
      <p class="text-xs text-gray-400 mt-1">Check rooms that can be assigned for a selected stay window.</p>
    </div>

    <!-- Search Panel -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Check Room Availability</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Check-in Date</p>
          <input
            v-model="checkIn"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Check-out Date</p>
          <input
            v-model="checkOut"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select
            v-model="roomType"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600"
          >
            <option value="">All Types</option>
            <option v-for="rt in roomTypeOptions" :key="rt" :value="rt">{{ rt }}</option>
          </select>
        </div>
        <button
          @click="checkAvailability"
          :disabled="loading || !checkIn || !checkOut"
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          <span v-if="loading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span>
          {{ loading ? 'Checking...' : 'Check Availability' }}
        </button>
        <button
          @click="resetSearch"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>
      </div>
      <p v-if="error" class="mt-3 text-xs text-red-500 font-medium">{{ error }}</p>
    </div>

    <!-- Availability Results -->
    <div v-if="results !== null" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Available Rooms</h3>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ results.length }} room{{ results.length !== 1 ? 's' : '' }} available
            from {{ checkIn }} to {{ checkOut }}
            <template v-if="roomType"> · {{ roomType }}</template>
          </p>
        </div>
        <span
          class="px-2.5 py-0.5 text-xs font-medium rounded-full"
          :class="results.length > 0 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-500'"
        >
          {{ results.length > 0 ? 'Rooms Available' : 'No Availability' }}
        </span>
      </div>
      <div v-if="results.length === 0" class="px-6 py-12 text-center">
        <p class="text-sm text-gray-400">No rooms available for the selected dates and criteria.</p>
        <p class="text-xs text-gray-300 mt-1">Try adjusting the date range or room type.</p>
      </div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100 bg-gray-50">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Room No.</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Room Type</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Floor</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Capacity</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Rate / Night</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Total Amount</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="room in results" :key="room.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ room.name }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ room.room_type }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ room.floor }}</td>
            <td class="px-4 py-4 text-xs text-gray-600">{{ room.capacity || '-' }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-gray-900">{{ formatCurrency(room.rate_per_night) }}</td>
            <td class="px-4 py-4 text-xs font-semibold text-blue-700">{{ formatCurrency(room.total_amount) }}</td>
            <td class="px-4 py-4">
              <button
                class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="router.push('/rooms/' + room.name)"
              >
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Idle state before first search -->
    <div v-else class="bg-white rounded-xl border border-gray-200 px-6 py-14 text-center">
      <p class="text-sm text-gray-400">Select a date range and click <span class="font-semibold text-gray-500">Check Availability</span> to see available rooms.</p>
      <p class="text-xs text-gray-300 mt-1">Check-ins, reservations, and holds are all taken into account.</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { callMethod } from '@/lib/api'

const router = useRouter()

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function tomorrowStr() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

const defaultCheckIn = todayStr()
const defaultCheckOut = tomorrowStr()

const checkIn = ref(defaultCheckIn)
const checkOut = ref(defaultCheckOut)
const roomType = ref('')
const roomTypeOptions = ref([])
const loading = ref(false)
const error = ref('')
const results = ref(null)

onMounted(loadRoomTypes)

async function loadRoomTypes() {
  try {
    const msg = await callMethod('rhohotel.rhocom_hotel.api.room.get_room_inventory') || {}
    roomTypeOptions.value = msg.room_types || []
  } catch (e) {
    console.error(e)
  }
}

async function checkAvailability() {
  if (!checkIn.value || !checkOut.value) return
  if (checkOut.value <= checkIn.value) {
    error.value = 'Check-out date must be after check-in date.'
    return
  }

  loading.value = true
  error.value = ''
  results.value = null

  try {
    const rows = await callMethod('rhohotel.rhocom_hotel.utils.room_availability.get_available_rooms', {
      check_in_dt: checkIn.value,
      check_out_dt: checkOut.value,
      room_type: roomType.value || undefined,
    })
    results.value = Array.isArray(rows) ? rows : []
  } catch (e) {
    error.value = 'Network error - please check connection.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  checkIn.value = defaultCheckIn
  checkOut.value = defaultCheckOut
  roomType.value = ''
  results.value = null
  error.value = ''
}

function formatCurrency(val) {
  if (!val) return '₦0.00'
  return `₦${Number(val).toLocaleString('en-NG', { minimumFractionDigits: 0 })}`
}
</script>
