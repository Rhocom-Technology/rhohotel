<template>
   <div class="space-y-4">

    <!-- Header -->
     <div class="">
      <div class="mb-1">
        <p class="text-xs text-gray-400">Guests / Guest List</p>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-1">Guest List</h1>
      <p class="text-xs text-gray-400">View guest profiles, contact information, stay history, loyalty status, balances, and activity.</p>
    </div>

    <!-- Stats Row -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">Total Guests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsLoading ? '—' : stats.total_guests }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">In-House Guests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsLoading ? '—' : stats.in_house }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">VIP / Loyalty</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">Elite</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsLoading ? '—' : stats.vip_count }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">Outstanding Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ statsLoading ? '—' : stats.outstanding }}</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div class="flex-1 min-w-48">
          <p class="text-xs text-gray-500 mb-1.5">Search guest</p>
          <input v-model="search" @keyup.enter="fetchGuests" type="text" placeholder="Guest name, phone, email, ID no..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div class="min-w-36">
          <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
          <select v-model="filterType" @change="fetchGuests"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700 focus:ring-2 focus:ring-blue-500">
            <option value="">All Guests</option>
            <option value="Individual">Individual</option>
            <option value="Corporate">Corporate</option>
            <option value="Walk-in">Walk-in</option>
          </select>
        </div>
        <div class="min-w-36">
          <p class="text-xs text-gray-500 mb-1.5">Loyalty</p>
          <select v-model="filterLoyalty" @change="fetchGuests"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700 focus:ring-2 focus:ring-blue-500">
            <option value="">All Levels</option>
            <option value="Base">Base</option>
            <option value="Silver">Silver</option>
            <option value="Gold">Gold</option>
            <option value="Platinum">Platinum</option>
            <option value="VIP">VIP</option>
            <option value="Corporate">Corporate</option>
          </select>
        </div>
        <div class="min-w-36">
          <p class="text-xs text-gray-500 mb-1.5">Current Status</p>
          <select v-model="filterStatus" @change="fetchGuests"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700 focus:ring-2 focus:ring-blue-500">
            <option value="">All Statuses</option>
            <option value="In-House">In-House</option>
            <option value="Checked Out">Checked Out</option>
          </select>
        </div>
        <button @click="resetFilters"
          class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Reset
        </button>
        <button @click="$router.push('/guests/new')" class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          New Guest
        </button>
      </div>
    </div>

    <!-- Guest Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">All Guests</h3>
        <p class="text-xs text-gray-400">
          {{ loading ? 'Loading…' : `Showing ${Math.min(startIdx + 1, totalCount)}–${endIdx} of ${totalCount} guests` }}
        </p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="px-6 py-16 text-center">
        <p class="text-xs text-gray-400">Loading guests…</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="px-6 py-16 text-center">
        <p class="text-xs text-red-500">{{ error }}</p>
        <button @click="fetchGuests" class="mt-3 px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Retry</button>
      </div>

      <!-- Empty -->
      <div v-else-if="!guests.length" class="px-6 py-16 text-center">
        <p class="text-xs text-gray-400">No guests found. Try adjusting your filters or add a new guest.</p>
        <button @click="$router.push('/guests/new')" class="mt-3 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">New Guest</button>
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left text-xs font-medium text-gray-500 px-6 py-3">Guest</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Contact</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Stay History</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Loyalty</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Balance</th>
            <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="guest in paginated" :key="guest.name" class="hover:bg-gray-50 transition-colors">
            <!-- Guest -->
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :style="avatarStyle(guest.hotel_guest_name)">
                  {{ initials(guest.hotel_guest_name) }}
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-900">{{ guest.hotel_guest_name }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">{{ guest.guest_type }}</p>
                </div>
              </div>
            </td>
            <!-- Contact -->
            <td class="px-4 py-4">
              <p class="text-xs text-gray-700">{{ guest.phone_number || '—' }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ guest.email || '—' }}</p>
            </td>
            <!-- Stay History -->
            <td class="px-4 py-4">
              <p class="text-xs text-gray-700">{{ guest.stays }} {{ guest.stays === 1 ? 'Stay' : 'Stays' }}</p>
              <p class="text-xs text-gray-400 mt-0.5">Last stay: {{ guest.last_stay }}</p>
            </td>
            <!-- Loyalty -->
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="loyaltyClass(guest.loyalty_tier)">
                {{ guest.loyalty_tier || 'Base' }}
              </span>
            </td>
            <!-- Balance -->
            <td class="px-4 py-4">
              <p class="text-xs font-medium text-gray-900">{{ guest.balance }}</p>
              <p v-if="guest.current_status === 'In-House'" class="text-xs text-green-600 mt-0.5">In-House</p>
            </td>
            <!-- Actions -->
            <td class="px-4 py-4">
              <button @click="router.push({ name: 'GuestProfile', params: { id: guest.name } })"
                class="px-4 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors">
                Open
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="!loading && !error && guests.length" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: {{ perPage }}</p>
        <div class="flex items-center gap-1">
          <button v-for="p in visiblePages" :key="p"
            @click="typeof p === 'number' && (currentPage = p)"
            class="w-7 h-7 flex items-center justify-center text-xs rounded"
            :class="p === currentPage ? 'bg-blue-600 text-white font-semibold' :
                    p === '...' ? 'text-gray-400 cursor-default' :
                    'text-gray-600 hover:bg-gray-100'">
            {{ p }}
          </button>
          <button @click="currentPage < totalPages && currentPage++"
            class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 ml-1"
            :disabled="currentPage === totalPages">
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const search = ref('')
const filterType = ref('')
const filterLoyalty = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 10

const loading = ref(false)
const error = ref(null)
const guests = ref([])
const totalCount = ref(0)

const statsLoading = ref(false)
const stats = ref({ total_guests: 0, in_house: 0, vip_count: 0, outstanding: '₦0' })

// ── API helper ─────────────────────────────────────────────────────
async function callMethod(method, params = {}) {
  const body = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== '' && v !== null && v !== undefined) body.append(k, String(v))
  }
  const res = await fetch('/api/method/' + method, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  if (data.exc) throw new Error(data._server_messages || data.exc)
  return data.message
}

// ── Fetch ──────────────────────────────────────────────────────────
async function fetchGuests() {
  loading.value = true
  error.value = null
  currentPage.value = 1
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.guest.get_guests', {
      search: search.value,
      guest_type: filterType.value,
      loyalty_tier: filterLoyalty.value,
      status: filterStatus.value,
      page: 1,
      page_size: 500,
    })
    guests.value = result.guests || []
    totalCount.value = result.total || 0
  } catch (e) {
    error.value = 'Failed to load guests. Please try again.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  statsLoading.value = true
  try {
    stats.value = await callMethod('rhohotel.rhocom_hotel.api.guest.get_guest_stats')
  } catch (e) {
    console.error('Failed to load guest stats', e)
  } finally {
    statsLoading.value = false
  }
}

function resetFilters() {
  search.value = ''
  filterType.value = ''
  filterLoyalty.value = ''
  filterStatus.value = ''
  fetchGuests()
}

onMounted(() => {
  fetchGuests()
  fetchStats()
})

// ── Pagination ─────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(guests.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, guests.value.length))
const paginated = computed(() => guests.value.slice(startIdx.value, endIdx.value))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

// ── Avatar ─────────────────────────────────────────────────────────
const palette = [
  { bg: '#dbeafe', color: '#1d4ed8' }, { bg: '#dcfce7', color: '#15803d' },
  { bg: '#fce7f3', color: '#be185d' }, { bg: '#fef9c3', color: '#a16207' },
  { bg: '#ede9fe', color: '#6d28d9' }, { bg: '#ffedd5', color: '#c2410c' },
  { bg: '#cffafe', color: '#0e7490' }, { bg: '#f1f5f9', color: '#475569' },
]
function initials(name) {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
}
function avatarStyle(name) {
  if (!name) return { backgroundColor: '#f1f5f9', color: '#475569' }
  const p = palette[name.charCodeAt(0) % palette.length]
  return { backgroundColor: p.bg, color: p.color }
}

// ── Loyalty Badge ──────────────────────────────────────────────────
function loyaltyClass(loyalty) {
  return {
    Base: 'bg-gray-100 text-gray-600', Silver: 'bg-slate-100 text-slate-600',
    Gold: 'bg-yellow-100 text-yellow-700', Platinum: 'bg-purple-100 text-purple-600',
    VIP: 'bg-orange-100 text-orange-600', Corporate: 'bg-blue-100 text-blue-600',
  }[loyalty] || 'bg-gray-100 text-gray-500'
}
</script>
