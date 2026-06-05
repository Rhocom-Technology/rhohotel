<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">{{ hall.hall_name || 'Hall' }}</h2>
        <p class="text-xs text-gray-400 mt-0.5">Front desk • hall profile, amenities, bookings, and operating status</p>
      </div>
      <div class="flex items-center gap-2">
        <router-link :to="`/hall/${hall.name}/edit`">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Edit Hall</button>
        </router-link>
        <!-- <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Create Booking</button> -->
         <router-link
            :to="{
              name: 'NewHallBooking',
              query: { hall: hall.name }
            }"
          >
            <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              Create Booking
            </button>
        </router-link>
      </div>
    </div>

    <!-- Status strip -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl px-5 py-4 border-2"
        :class="currentStatus === 'Booked' ? 'border-blue-200' : 'border-green-200'">
        <p class="text-xs text-gray-400 mb-2">Status</p>
        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full inline-block mb-2"
          :class="currentStatus === 'Booked' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-700'">
          {{ currentStatus === 'Booked' ? 'Active' : 'Active' }}
        </span>
        <p class="text-2xl font-bold text-gray-900">{{ currentStatus }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ currentStatus === 'Booked' ? 'Currently occupied' : 'Open for booking' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Capacity</p>
        <p class="text-2xl font-bold text-gray-900">{{ hall.capacity }} Pax</p>
        <p class="text-xs text-gray-400 mt-1">{{ hall.hall_type }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Rate</p>
        <p class="text-2xl font-bold text-gray-900">₦{{ Number(hall.rate || 0).toLocaleString() }}</p>
        <p class="text-xs text-gray-400 mt-1">Per day billing</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Bookings This Month</p>
        <p class="text-2xl font-bold text-gray-900">{{ hall.bookings_this_month || 0 }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ hall.upcoming_count || 0 }} upcoming</p>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 260px;gap:16px;align-items:start;">

      <!-- Left -->
      <div class="space-y-4">

        <!-- Hall Profile -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Hall Profile</h3>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Hall Code</p>
              <p class="text-xs font-semibold text-gray-900">{{ hall.name }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Hall Name</p>
              <p class="text-xs font-semibold text-gray-900">{{ hall.hall_name }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Hall Type</p>
              <p class="text-xs font-semibold text-gray-900">{{ hall.hall_type }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Capacity</p>
              <p class="text-xs font-semibold text-gray-900">{{ hall.capacity }} Pax</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Rate</p>
              <p class="text-xs font-semibold text-gray-900">₦{{ Number(hall.rate || 0).toLocaleString() }}</p>
            </div>
            <div v-if="hall.item_name">
              <p class="text-xs text-gray-400 mb-0.5">Linked Item</p>
              <p class="text-xs font-semibold text-gray-900">{{ hall.item_name }}</p>
            </div>
          </div>
        </div>

        <!-- Amenities -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Amenities</h3>
            <p class="text-xs text-gray-400 mt-0.5">Items included with this hall.</p>
          </div>
          <div v-if="!hall.amenities?.length" class="px-6 py-6 text-center text-xs text-gray-400">
            No amenities configured.
          </div>
          <table v-else class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">#</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Item</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Amenity Name</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="(a, i) in hall.amenities" :key="i">
                <td class="px-6 py-3 text-xs text-gray-400">{{ i + 1 }}</td>
                <td class="px-6 py-3 text-xs text-gray-700">{{ a.item }}</td>
                <td class="px-6 py-3 text-xs text-gray-700">{{ a.amenity_name }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Upcoming Bookings -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-bold text-gray-900">Upcoming Bookings</h3>
            <p class="text-xs text-gray-400 mt-0.5">Scheduled events assigned to this hall.</p>
          </div>
          <div v-if="!hall.upcoming_bookings?.length" class="px-6 py-6 text-center text-xs text-gray-400">
            No upcoming bookings.
          </div>
          <table v-else class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Booking ID</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Client</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Event</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Start</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">End</th>
                <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="b in hall.upcoming_bookings" :key="b.name" class="hover:bg-gray-50">
                <td class="px-6 py-3 text-xs font-semibold text-blue-600">{{ b.name }}</td>
                <td class="px-6 py-3 text-xs text-gray-700">{{ b.customer_name }}</td>
                <td class="px-6 py-3 text-xs text-gray-600">{{ b.event_type }}</td>
                <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(b.start_datetime) }}</td>
                <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(b.end_datetime) }}</td>
                <td class="px-6 py-3 text-xs text-gray-700">₦{{ Number(b.net_total || 0).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>

      <!-- Right -->
      <div class="space-y-4">

        <!-- Hall Preview -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Hall Preview</h3>
          <div class="bg-gray-50 rounded-lg px-4 py-3 mb-2">
            <p class="text-sm font-bold text-gray-900">{{ hall.hall_name }}</p>
            <p class="text-xs text-gray-500 mt-0.5">{{ hall.hall_type }} • {{ hall.capacity }} Pax</p>
            <p class="text-xs text-gray-500">₦{{ Number(hall.rate || 0).toLocaleString() }}/day</p>
          </div>
          <div class="space-y-1 mt-2">
            <div v-for="a in (hall.amenities || [])" :key="a.item"
              class="text-xs text-gray-500 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0"></span>
              {{ a.amenity_name || a.item }}
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-3">Visible to reservation and hall booking workflows</p>
        </div>

        <!-- Active Booking -->
        <div v-if="hall.active_booking" class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
          <h3 class="text-xs font-bold text-blue-900 mb-2">Currently Active</h3>
          <p class="text-xs text-blue-700 font-semibold">{{ hall.active_booking.customer_name }}</p>
          <p class="text-xs text-blue-600">{{ hall.active_booking.event_type }}</p>
          <p class="text-xs text-blue-500 mt-1">{{ fmtDatetime(hall.active_booking.start_datetime) }} → {{ fmtDatetime(hall.active_booking.end_datetime) }}</p>
        </div>

        <!-- Audit Trail -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Audit Trail</h3>
          <div class="space-y-2">
            <div>
              <p class="text-xs text-gray-400">Created</p>
              <p class="text-xs text-gray-700">{{ fmtDatetime(hall.creation) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400">Last Updated</p>
              <p class="text-xs text-gray-700">{{ fmtDatetime(hall.modified) }}</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { callMethod } from '@/lib/api'

const route = useRoute()
const hall  = ref({})

const currentStatus = computed(() => hall.value.active_booking ? 'Booked' : 'Available')

function fmtDatetime(dt) {
  if (!dt) return '–'
  return new Date(dt).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    day: '2-digit', minute: '2-digit'
  })
}

async function load() {
  try {
    const data = await callMethod('rhohotel.rhocom_hotel.api.hall.get_hall', {
      name: route.params.id
    })
    hall.value = data || {}
  } catch (e) {
    console.error(e)
  }
}

onMounted(load)
</script>