<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Hall Bookings</h2>
        <p class="text-xs text-gray-400 mt-0.5">All event hall bookings — confirmed, draft, and past.</p>
      </div>
      <router-link to="/hall/booking/new">
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">New Booking</button>
      </router-link>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Total Bookings</p>
        <p class="text-3xl font-bold text-gray-900">{{ bookings.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Confirmed</p>
        <p class="text-3xl font-bold text-green-600">{{ bookings.filter(b => b.docstatus === 1).length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Draft</p>
        <p class="text-3xl font-bold text-yellow-500">{{ bookings.filter(b => b.docstatus === 0).length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Unpaid</p>
        <p class="text-3xl font-bold text-red-500">{{ bookings.filter(b => b.payment_status === 'Unpaid').length }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-end gap-3">
      <div class="flex-1">
        <label class="text-xs text-gray-500 mb-1 block">Search</label>
        <input v-model="search" type="text" placeholder="Customer, hall, event…"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label class="text-xs text-gray-500 mb-1 block">Status</label>
        <select v-model="filterStatus" class="text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">All</option>
          <option value="0">Draft</option>
          <option value="1">Confirmed</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-gray-500 mb-1 block">Payment</label>
        <select v-model="filterPayment" class="text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">All</option>
          <option value="Paid">Paid</option>
          <option value="Unpaid">Unpaid</option>
          <option value="Partial">Partial</option>
        </select>
      </div>
      <button @click="search='';filterStatus='';filterPayment=''"
        class="px-4 py-2 text-xs text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div v-if="loading" class="px-6 py-8 text-center text-xs text-gray-400">Loading bookings…</div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Booking ID</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Customer</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Hall</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Event</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Start</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">End</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Hours</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Net Total</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Status</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Payment</th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-if="filtered.length === 0">
            <td colspan="10" class="px-6 py-8 text-center text-xs text-gray-400">No bookings found.</td>
          </tr>
          <tr v-for="b in paged" :key="b.name" class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-3 text-xs font-semibold text-blue-600">{{ b.name }}</td>
            <td class="px-6 py-3 text-xs text-gray-700">{{ b.customer_name }}</td>
            <td class="px-6 py-3 text-xs text-gray-600">{{ b.hall }}</td>
            <td class="px-6 py-3 text-xs text-gray-600">{{ b.event_type }}</td>
            <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(b.start_datetime) }}</td>
            <td class="px-6 py-3 text-xs text-gray-600">{{ fmtDatetime(b.end_datetime) }}</td>
            <td class="px-6 py-3 text-xs text-gray-600">{{ b.total_hours }}h</td>
            <td class="px-6 py-3 text-xs text-gray-700 font-medium">₦{{ Number(b.net_total || 0).toLocaleString() }}</td>
            <td class="px-6 py-3">
              <span class="px-2 py-0.5 text-xs font-semibold rounded-full" :class="statusClass(b.docstatus)">
                {{ b.status_label }}
              </span>
            </td>
            <td class="px-6 py-3">
              <span class="px-2 py-0.5 text-xs font-semibold rounded-full" :class="paymentClass(b.payment_status)">
                {{ b.payment_status }}
              </span>
            </td>
            <td class="px-6 py-3">
              <router-link :to="`/hall/booking/${b.name}`">
                <button class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">View</button>
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="totalPages > 1" class="px-6 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
        <p class="text-xs text-gray-400">Showing {{ pageStart + 1 }}–{{ pageEnd }} of {{ filtered.length }}</p>
        <div class="flex items-center gap-1">
          <button @click="page > 1 ? page-- : null" :disabled="page === 1"
            class="px-3 py-1.5 text-xs border rounded-lg transition-colors"
            :class="page === 1 ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Prev</button>
          <button v-for="p in totalPages" :key="p" @click="page = p"
            class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
            :class="page === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 border border-gray-200 hover:bg-white'">{{ p }}</button>
          <button @click="page < totalPages ? page++ : null" :disabled="page === totalPages"
            class="px-3 py-1.5 text-xs border rounded-lg transition-colors"
            :class="page === totalPages ? 'text-gray-300 border-gray-100 cursor-not-allowed' : 'text-gray-600 border-gray-200 hover:bg-white'">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const loading       = ref(false)
const bookings      = ref([])
const page          = ref(1)
const perPage       = 10
const search        = ref('')
const filterStatus  = ref('')
const filterPayment = ref('')

const filtered = computed(() => bookings.value.filter(b => {
  const q = search.value.toLowerCase()
  if (q && !b.customer_name?.toLowerCase().includes(q) &&
           !b.hall?.toLowerCase().includes(q) &&
           !b.event_type?.toLowerCase().includes(q) &&
           !b.name?.toLowerCase().includes(q)) return false
  if (filterStatus.value !== '' && String(b.docstatus) !== filterStatus.value) return false
  if (filterPayment.value && b.payment_status !== filterPayment.value) return false
  return true
}))

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const pageStart  = computed(() => (page.value - 1) * perPage)
const pageEnd    = computed(() => Math.min(pageStart.value + perPage, filtered.value.length))
const paged      = computed(() => filtered.value.slice(pageStart.value, pageEnd.value))

function fmtDatetime(dt) {
  if (!dt) return '–'
  return new Date(dt).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })
}

function statusClass(s) {
  return { 0: 'bg-yellow-100 text-yellow-600', 1: 'bg-green-100 text-green-700', 2: 'bg-red-100 text-red-500' }[s] || 'bg-gray-100 text-gray-500'
}

function paymentClass(s) {
  return { 'Paid': 'bg-green-100 text-green-700', 'Unpaid': 'bg-red-100 text-red-500', 'Partial': 'bg-yellow-100 text-yellow-600', 'Draft': 'bg-gray-100 text-gray-500', 'No Invoice': 'bg-gray-100 text-gray-400' }[s] || 'bg-gray-100 text-gray-500'
}

async function load() {
  loading.value = true
  try {
    bookings.value = await callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_booking_list') || []
  } catch(e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(load)
</script>