<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Hall Directory</h2>
        <p class="text-xs text-gray-400 mt-0.5">Search, filter, and review all event halls and banquet spaces from one place.</p>
      </div>
      <div class="flex items-center gap-3">
        <router-link to="/hall/new">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Add New Hall</button>
        </router-link>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Total Halls</p>
        <p class="text-3xl font-bold text-gray-900">{{ halls.length }}</p>
        <p class="text-xs text-gray-400 mt-1">Registered event spaces</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Available Now</p>
        <p class="text-3xl font-bold text-green-600">{{ halls.filter(h => h.current_status === 'Available').length }}</p>
        <p class="text-xs text-gray-400 mt-1">Ready for booking</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Currently Booked</p>
        <p class="text-3xl font-bold text-blue-600">{{ halls.filter(h => h.current_status === 'Booked').length }}</p>
        <p class="text-xs text-gray-400 mt-1">Occupied by events</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
      <p class="text-xs text-gray-400 mb-2">Unavailable</p>
      <p class="text-3xl font-bold text-red-600">
        {{ halls.filter(h => h.current_status === 'Unavailable').length }}
      </p>
      <p class="text-xs text-gray-400 mt-1">
        Maintenance / blocked halls
      </p>
    </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Bookings Today</p>
        <p class="text-3xl font-bold text-gray-900">{{ totalBookingsToday }}</p>
        <p class="text-xs text-gray-400 mt-1">Events scheduled today</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Filters</h3>
      <div class="flex items-end gap-3">
        <div class="flex-1">
          <label class="text-xs text-gray-500 mb-1 block">Search Hall</label>
          <input v-model="search" type="text" placeholder="Search by hall name..."
            class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">Status</label>
          <select v-model="filterStatus" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Status</option>
            <option value="Available">Available</option>
            <option value="Unavailable">Unavailable</option>
            <option value="Booked">Booked</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">Type</label>
          <select
            v-model="filterType"
            class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>

            <option
              v-for="type in hallTypes"
              :key="type.name"
              :value="type.name"
            >
              {{ type.hall_type_name || type.name }}
            </option>
          </select>
        </div>
        <button @click="search = ''; filterStatus = ''; filterType = ''"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Halls</h3>
        <p class="text-xs text-gray-400 mt-0.5">Overview of all halls and their current operating state.</p>
      </div>

      <div v-if="loading" class="px-6 py-8 text-center text-xs text-gray-400">Loading halls…</div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Hall Name</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Type</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Capacity</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Rate/Hr</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Current Booking</th>
              <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-if="filtered.length === 0">
              <td colspan="7" class="px-6 py-8 text-center text-xs text-gray-400">No halls found.</td>
            </tr>
            <tr v-for="hall in paged" :key="hall.name" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-3 text-xs font-semibold text-gray-900">{{ hall.hall_name }}</td>
              <td class="px-6 py-3 text-xs text-gray-600">{{ hall.hall_type }}</td>
              <td class="px-6 py-3 text-xs text-gray-600">{{ hall.capacity }}</td>
              <td class="px-6 py-3 text-xs text-gray-600">₦{{ Number(hall.rate || 0).toLocaleString() }}</td>
              <td class="px-6 py-3">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(hall.current_status)">
                  {{ hall.current_status }}
                </span>
              </td>
              <td class="px-6 py-3 text-xs text-gray-500">
                <span v-if="hall.active_booking">
                  {{ hall.active_booking.customer_name }} • {{ hall.active_booking.event_type }}
                </span>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-6 py-3">
                <router-link :to="`/hall/${hall.name}`">
                  <button class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">View</button>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="px-6 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }} halls</p>
        <div class="flex items-center gap-1">
          <button @click="page > 1 ? page-- : null" :disabled="page === 1"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :class="page === 1 ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Previous</button>
          <button v-for="p in totalPages" :key="p" @click="page = p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="page === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-white border border-gray-200'">{{ p }}</button>
          <button @click="page < totalPages ? page++ : null" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :class="page === totalPages ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const loading = ref(false)
const halls   = ref([])
const page    = ref(1)
const perPage = 10

const search       = ref('')
const filterStatus = ref('')
const filterType   = ref('')
const hallTypes = ref([])

const totalBookingsToday = computed(() =>
  halls.value.reduce((acc, h) => acc + (h.bookings_today || 0), 0)
)

const filtered = computed(() => {
  return halls.value.filter(h => {
    if (search.value && !h.hall_name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterStatus.value && h.current_status !== filterStatus.value) return false
    if (filterType.value && h.hall_type !== filterType.value) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart  = computed(() => (page.value - 1) * perPage)
const pageEnd    = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged      = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function statusClass(s) {
  if (s === 'Booked')
    return 'bg-blue-100 text-blue-600'

  if (s === 'Unavailable')
    return 'bg-red-100 text-red-600'

  return 'bg-green-100 text-green-700'
}

async function load() {
  loading.value = true
  try {
    const data = await callMethod('rhohotel.rhocom_hotel.api.hall.get_hall_list')
    halls.value = data || []

    // fetch types from actual Hall records
    const types = await callMethod('rhohotel.rhocom_hotel.api.hall.get_hall_types')
    hallTypes.value = types || []

  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>