<template>
  <div class="space-y-4">

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Hall Booking Dashboard</h2>
        <p class="text-xs text-gray-400 mt-0.5">
          Monitor hall reservation performance, upcoming events, payment status, and hall utilization from one screen.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <router-link to="/hall/booking">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Hall Booking List
          </button>
        </router-link>

        <router-link to="/hall">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Hall List
          </button>
        </router-link>

        <router-link to="/hall/booking/new">
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            New Hall Booking
          </button>
        </router-link>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400">Total Bookings</p>
        <p class="text-2xl font-bold text-gray-900 mt-2">{{ stats.total_bookings }}</p>
        <p class="text-xs text-gray-400 mt-1">All bookings in selected period</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400">Today</p>
        <p class="text-2xl font-bold text-gray-900 mt-2">{{ stats.today }}</p>
        <p class="text-xs text-gray-400 mt-1">Events active today</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400">Pending Payment</p>
        <p class="text-2xl font-bold text-gray-900 mt-2">₦{{ money(stats.pending_payment) }}</p>
        <p class="text-xs text-gray-400 mt-1">Outstanding hall balances</p>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400">Hall Utilization</p>
        <p class="text-2xl font-bold text-gray-900 mt-2">{{ stats.utilization }}%</p>
        <p class="text-xs text-gray-400 mt-1">Usage in selected period</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Filters</h3>

      <div class="flex items-end gap-3">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">From Date</label>
          <input v-model="filters.from_date" type="date" class="text-xs border border-gray-200 rounded-lg px-3 py-2" />
        </div>

        <div>
          <label class="text-xs text-gray-500 mb-1 block">To Date</label>
          <input v-model="filters.to_date" type="date" class="text-xs border border-gray-200 rounded-lg px-3 py-2" />
        </div>

        <div>
          <label class="text-xs text-gray-500 mb-1 block">Hall</label>
          <select v-model="filters.hall" class="text-xs border border-gray-200 rounded-lg px-3 py-2 min-w-[150px]">
            <option value="">All Halls</option>
            <option v-for="h in halls" :key="h.name" :value="h.name">{{ h.hall_name }}</option>
          </select>
        </div>

        <div>
          <label class="text-xs text-gray-500 mb-1 block">Status</label>
          <select v-model="filters.status" class="text-xs border border-gray-200 rounded-lg px-3 py-2 min-w-[150px]">
            <option value="">All Status</option>
            <option>Draft</option>
            <option>Confirmed</option>
            <option>Cancelled</option>
          </select>
        </div>

        <button @click="resetFilters" class="px-5 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Reset
        </button>

        <button @click="load" class="px-5 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          Apply
        </button>
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-8 text-center text-xs text-gray-400">
      Loading dashboard…
    </div>

    <template v-else>
      <div style="display:grid;grid-template-columns:1.1fr 0.9fr;gap:16px;">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Revenue Trend</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-4">Hall booking revenue over the selected period.</p>

          <div class="h-48 flex items-end gap-10 border-b border-gray-200 px-2">
            <div v-for="w in revenueTrend" :key="w.label" class="flex flex-col items-center flex-1">
              <div class="w-10 bg-blue-600 rounded-t-lg" :style="{ height: w.bar + 'px' }"></div>
              <p class="text-xs text-gray-400 mt-2">{{ w.label }}</p>
              <p class="text-[10px] text-gray-400">₦{{ money(w.amount) }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Booking Status</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-5">Distribution of hall bookings by status.</p>

          <div class="flex items-center justify-between">
            <div class="w-36 h-36 rounded-full border-[18px] border-blue-600 flex items-center justify-center">
              <div class="text-center">
                <p class="text-2xl font-bold text-gray-900">{{ stats.total_bookings }}</p>
                <p class="text-xs text-gray-400">Bookings</p>
              </div>
            </div>

            <div class="space-y-3 text-xs w-40">
              <div class="flex justify-between"><span class="text-gray-600">Draft</span><b>{{ bookingStatus.draft }}</b></div>
              <div class="flex justify-between"><span class="text-gray-600">Confirmed</span><b>{{ bookingStatus.confirmed }}</b></div>
              <div class="flex justify-between"><span class="text-gray-600">Cancelled</span><b>{{ bookingStatus.cancelled }}</b></div>
              <div class="flex justify-between"><span class="text-gray-600">Paid</span><b>{{ bookingStatus.paid }}</b></div>
              <div class="flex justify-between"><span class="text-gray-600">Unpaid</span><b>{{ bookingStatus.unpaid }}</b></div>
            </div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1.1fr 0.9fr;gap:16px;">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Hall Occupancy</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-4">Booked days divided by total days in selected period.</p>

          <div class="space-y-4">
            <div v-for="h in occupancy" :key="h.hall">
              <div class="flex justify-between text-xs font-semibold mb-1">
                <span class="text-gray-800">{{ h.name }}</span>
                <span class="text-gray-500">
                  {{ h.status }} · {{ h.percent }}% · {{ h.booked_days }}/{{ h.total_days }} days
                </span>
              </div>
              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-blue-600" :style="{ width: h.percent + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Upcoming Events</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-4">Next scheduled hall bookings.</p>

          <table class="w-full">
            <thead>
              <tr class="bg-gray-50 border border-gray-100">
                <th class="text-left px-3 py-2 text-xs text-gray-500 font-semibold rounded-l-lg">Client</th>
                <th class="text-left px-3 py-2 text-xs text-gray-500 font-semibold">Hall</th>
                <th class="text-left px-3 py-2 text-xs text-gray-500 font-semibold">Date</th>
                <th class="text-left px-3 py-2 text-xs text-gray-500 font-semibold rounded-r-lg">Status</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-gray-50">
              <tr v-for="e in upcomingEvents" :key="e.name">
                <td class="px-3 py-3 text-xs font-semibold text-gray-900">{{ e.customer_name }}</td>
                <td class="px-3 py-3 text-xs text-gray-500">{{ e.hall_name }}</td>
                <td class="px-3 py-3 text-xs text-gray-500">{{ dateOnly(e.start_datetime) }}</td>
                <td class="px-3 py-3">
                  <span class="px-3 py-1 rounded-lg text-[10px] font-bold" :class="statusClass(e.status_label)">
                    {{ e.status_label }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:0.8fr 1.2fr;gap:16px;">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Payment Summary</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-4">Hall payment performance in selected period.</p>

          <div class="space-y-2 text-xs">
            <div class="flex justify-between border-b border-gray-100 pb-2">
              <span class="text-gray-500">Paid</span>
              <b>₦{{ money(payment.paid_today) }}</b>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Pending</span>
              <b>₦{{ money(payment.pending) }}</b>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900">Operational Alerts</h3>
          <p class="text-xs text-gray-400 mt-0.5 mb-4">Items needing quick attention.</p>

          <div class="space-y-3">
            <div class="px-4 py-2 text-xs font-semibold rounded-lg bg-yellow-100 text-yellow-700">
              {{ alerts.pending_approval }} draft bookings awaiting submission
            </div>
            <div class="px-4 py-2 text-xs font-semibold rounded-lg bg-red-100 text-red-600">
              {{ alerts.maintenance }} hall scheduled for maintenance
            </div>
            <div class="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-100 text-blue-600">
              {{ alerts.pending_invoice }} invoices have pending balances
            </div>
          </div>
        </div>
      </div>
    </template>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-2">
      <p class="text-xs text-gray-400">Hall Booking Dashboard • Live operational view for reservations and events.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

const loading = ref(false)

const halls = ref([])
const upcomingEvents = ref([])
const revenueTrend = ref([])
const occupancy = ref([])

const stats = ref({
  total_bookings: 0,
  today: 0,
  pending_payment: 0,
  utilization: 0,
})

const payment = ref({
  paid_today: 0,
  pending: 0,
})

const alerts = ref({
  pending_approval: 0,
  maintenance: 0,
  pending_invoice: 0,
})

const bookingStatus = ref({
  draft: 0,
  confirmed: 0,
  cancelled: 0,
  paid: 0,
  unpaid: 0,
})

const filters = ref({
  from_date: '',
  to_date: '',
  hall: '',
  status: '',
})

async function load() {
  loading.value = true

  try {
    const data = await callMethod('rhohotel.rhocom_hotel.api.hall_dashboard.get_dashboard_data', {
      from_date: filters.value.from_date,
      to_date: filters.value.to_date,
      hall: filters.value.hall,
      status: filters.value.status,
    })

    filters.value.from_date = data.filters.from_date
    filters.value.to_date = data.filters.to_date
    filters.value.hall = data.filters.hall
    filters.value.status = data.filters.status

    halls.value = data.halls || []
    stats.value = data.stats || stats.value
    payment.value = data.payment || payment.value
    alerts.value = data.alerts || alerts.value
    bookingStatus.value = data.booking_status || bookingStatus.value
    revenueTrend.value = data.revenue_trend || []
    occupancy.value = data.occupancy || []
    upcomingEvents.value = data.upcoming_events || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    from_date: '',
    to_date: '',
    hall: '',
    status: '',
  }

  load()
}

function money(v) {
  return Number(v || 0).toLocaleString()
}

function dateOnly(v) {
  if (!v) return ''
  return String(v).slice(0, 10)
}

function statusClass(status) {
  if (status === 'Confirmed') return 'bg-green-100 text-green-700'
  if (status === 'Draft') return 'bg-yellow-100 text-yellow-700'
  if (status === 'Cancelled') return 'bg-red-100 text-red-600'
  return 'bg-blue-100 text-blue-600'
}

onMounted(load)
</script>