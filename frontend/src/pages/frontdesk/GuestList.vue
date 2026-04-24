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
        <p class="text-3xl font-bold text-gray-900">8,462</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">In-House Guests</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Today</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">96</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">VIP / Loyalty</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">Elite</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">314</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-500">Outstanding Balance</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Review</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦6.8M</p>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Filters & Search</h3>
      <div class="flex items-end gap-3 flex-wrap">
        <div class="flex-1 min-w-48">
          <p class="text-xs text-gray-500 mb-1.5">Search guest</p>
          <input v-model="search" type="text" placeholder="Guest name, phone, email, ID no..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div class="min-w-36">
          <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
          <select v-model="filterType"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700 focus:ring-2 focus:ring-blue-500">
            <option value="">All Guests</option>
            <option value="Returning Guest">Returning Guest</option>
            <option value="Individual Guest">Individual Guest</option>
            <option value="Corporate Contact">Corporate Contact</option>
            <option value="Corporate Booker">Corporate Booker</option>
            <option value="Walk-in Guest">Walk-in Guest</option>
          </select>
        </div>
        <div class="min-w-36">
          <p class="text-xs text-gray-500 mb-1.5">Loyalty</p>
          <select v-model="filterLoyalty"
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
          <select v-model="filterStatus"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700 focus:ring-2 focus:ring-blue-500">
            <option value="">All Statuses</option>
            <option value="In-House">In-House</option>
            <option value="Checked Out">Checked Out</option>
            <option value="Reserved">Reserved</option>
          </select>
        </div>
        <button @click="resetFilters"
          class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Reset
        </button>
        <button class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          New Guest
        </button>
      </div>
    </div>

    <!-- Guest Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900">All Guests</h3>
        <p class="text-xs text-gray-400">Showing {{ startIdx + 1 }}–{{ endIdx }} of {{ filtered.length }} guests</p>
      </div>

      <table class="w-full">
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
          <tr v-for="guest in paginated" :key="guest.id"
            class="hover:bg-gray-50 transition-colors">
            <!-- Guest -->
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :style="{ backgroundColor: guest.avatarBg, color: guest.avatarColor }">
                  {{ guest.initials }}
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-900">{{ guest.name }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">{{ guest.type }}</p>
                </div>
              </div>
            </td>
            <!-- Contact -->
            <td class="px-4 py-4">
              <p class="text-xs text-gray-700">{{ guest.phone }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ guest.email }}</p>
            </td>
            <!-- Stay History -->
            <td class="px-4 py-4">
              <p class="text-xs text-gray-700">{{ guest.stays }} {{ guest.stays === 1 ? 'Stay' : 'Stays' }}</p>
              <p class="text-xs text-gray-400 mt-0.5">Last stay: {{ guest.lastStay }}</p>
            </td>
            <!-- Loyalty -->
            <td class="px-4 py-4">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="loyaltyClass(guest.loyalty)">
                {{ guest.loyalty }}
              </span>
            </td>
            <!-- Balance -->
            <td class="px-4 py-4">
              <p class="text-xs font-medium text-gray-900">{{ guest.balance }}</p>
            </td>
            <!-- Actions -->
            <td class="px-4 py-4">
              <button class="px-4 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors">
                Open
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
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
import { ref, computed } from 'vue'

// ── Filters ────────────────────────────────────────────────────────
const search = ref('')
const filterType = ref('')
const filterLoyalty = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 10

function resetFilters() {
  search.value = ''
  filterType.value = ''
  filterLoyalty.value = ''
  filterStatus.value = ''
  currentPage.value = 1
}

// ── Dummy Data ─────────────────────────────────────────────────────
const avatarPalette = [
  { bg: '#dbeafe', color: '#1d4ed8' },
  { bg: '#dcfce7', color: '#15803d' },
  { bg: '#fce7f3', color: '#be185d' },
  { bg: '#fef9c3', color: '#a16207' },
  { bg: '#ede9fe', color: '#6d28d9' },
  { bg: '#ffedd5', color: '#c2410c' },
  { bg: '#cffafe', color: '#0e7490' },
  { bg: '#f1f5f9', color: '#475569' },
]

function palette(i) {
  return avatarPalette[i % avatarPalette.length]
}

function initials(name) {
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
}

const rawGuests = [
  { id: 1, name: 'Chinedu Okafor', type: 'Returning Guest', phone: '+234 803 000 1288', email: 'chinedu.okafor@email.com', stays: 6, lastStay: '12 Apr 2026', loyalty: 'Gold', balance: '₦91,000', status: 'Checked Out' },
  { id: 2, name: 'Sarah Johnson', type: 'Individual Guest', phone: '+44 7700 882011', email: 'sarah.johnson@mail.com', stays: 2, lastStay: '11 Apr 2026', loyalty: 'Silver', balance: '₦0.00', status: 'Checked Out' },
  { id: 3, name: 'Emeka Adeyemi', type: 'Corporate Contact', phone: '+234 805 211 4545', email: 'emeka@apexholdings.com', stays: 10, lastStay: '05 Apr 2026', loyalty: 'VIP', balance: '₦240,000', status: 'Reserved' },
  { id: 4, name: 'Grace Cole', type: 'Returning Guest', phone: '+234 809 884 1003', email: 'grace.cole@domain.com', stays: 14, lastStay: '09 Apr 2026', loyalty: 'Platinum', balance: '₦0.00', status: 'Checked Out' },
  { id: 5, name: 'Bamidele Akin', type: 'Individual Guest', phone: '+234 802 197 8830', email: 'bamidele.akin@mail.com', stays: 1, lastStay: '14 Apr 2026', loyalty: 'Silver', balance: '₦18,000', status: 'In-House' },
  { id: 6, name: 'Ngozi Lawson', type: 'Corporate Booker', phone: '+234 803 555 0198', email: 'traveldesk@apexholdings.com', stays: 22, lastStay: '18 Apr 2026', loyalty: 'Corporate', balance: '₦0.00', status: 'In-House' },
  { id: 7, name: 'Michael Obi', type: 'Walk-in Guest', phone: '+234 811 700 0061', email: 'mikeobi@webmail.com', stays: 3, lastStay: '10 Apr 2026', loyalty: 'Base', balance: '₦0.00', status: 'Checked Out' },
  { id: 8, name: 'Fatima Ahmed', type: 'Returning Guest', phone: '+234 805 661 8882', email: 'fatima.a@domain.com', stays: 8, lastStay: '14 Apr 2026', loyalty: 'Platinum', balance: '₦54,000', status: 'In-House' },
  { id: 9, name: 'Tunde Balogun', type: 'Individual Guest', phone: '+234 806 312 9901', email: 'tundeb@gmail.com', stays: 4, lastStay: '08 Apr 2026', loyalty: 'Gold', balance: '₦12,500', status: 'Reserved' },
  { id: 10, name: 'Amina Suleiman', type: 'Corporate Contact', phone: '+234 817 223 4450', email: 'amina.s@corp.ng', stays: 17, lastStay: '20 Apr 2026', loyalty: 'VIP', balance: '₦380,000', status: 'In-House' },
  { id: 11, name: 'David Mensah', type: 'Returning Guest', phone: '+233 244 567 890', email: 'david.mensah@mail.gh', stays: 5, lastStay: '15 Apr 2026', loyalty: 'Silver', balance: '₦7,200', status: 'Checked Out' },
  { id: 12, name: 'Chidinma Eze', type: 'Individual Guest', phone: '+234 803 778 2210', email: 'chidinma.eze@yahoo.com', stays: 2, lastStay: '17 Apr 2026', loyalty: 'Base', balance: '₦0.00', status: 'In-House' },
  { id: 13, name: 'Oluwaseun Adebayo', type: 'Corporate Booker', phone: '+234 802 444 6620', email: 'seun.adebayo@company.ng', stays: 31, lastStay: '19 Apr 2026', loyalty: 'Corporate', balance: '₦0.00', status: 'In-House' },
  { id: 14, name: 'Halima Usman', type: 'Returning Guest', phone: '+234 811 900 3344', email: 'halima.u@domain.com', stays: 9, lastStay: '07 Apr 2026', loyalty: 'Gold', balance: '₦29,000', status: 'Reserved' },
  { id: 15, name: 'Ifeanyi Nwosu', type: 'Walk-in Guest', phone: '+234 805 119 8870', email: 'ifeanyi.n@webmail.com', stays: 1, lastStay: '18 Apr 2026', loyalty: 'Base', balance: '₦5,000', status: 'Checked Out' },
  { id: 16, name: 'Yewande Okonkwo', type: 'Individual Guest', phone: '+234 809 335 7712', email: 'yewande.o@mail.com', stays: 6, lastStay: '11 Apr 2026', loyalty: 'Silver', balance: '₦0.00', status: 'Checked Out' },
  { id: 17, name: 'Kelechi Onyeka', type: 'Returning Guest', phone: '+234 806 220 4490', email: 'kelechi.o@domain.com', stays: 12, lastStay: '16 Apr 2026', loyalty: 'Platinum', balance: '₦142,000', status: 'In-House' },
  { id: 18, name: 'Adaeze Chukwu', type: 'Corporate Contact', phone: '+234 803 991 5544', email: 'adaeze@bigcorp.ng', stays: 7, lastStay: '13 Apr 2026', loyalty: 'VIP', balance: '₦88,000', status: 'Reserved' },
  { id: 19, name: 'Biodun Fashola', type: 'Individual Guest', phone: '+234 812 774 3310', email: 'biodun.f@gmail.com', stays: 3, lastStay: '06 Apr 2026', loyalty: 'Base', balance: '₦0.00', status: 'Checked Out' },
  { id: 20, name: 'Zainab Musa', type: 'Returning Guest', phone: '+234 808 553 6619', email: 'zainab.m@domain.com', stays: 11, lastStay: '20 Apr 2026', loyalty: 'Gold', balance: '₦33,500', status: 'In-House' },
].map((g, i) => ({
  ...g,
  initials: initials(g.name),
  avatarBg: palette(i).bg,
  avatarColor: palette(i).color,
}))

// ── Filtered ───────────────────────────────────────────────────────
const filtered = computed(() => {
  let data = rawGuests
  if (search.value) {
    const q = search.value.toLowerCase()
    data = data.filter(g =>
      g.name.toLowerCase().includes(q) ||
      g.phone.includes(q) ||
      g.email.toLowerCase().includes(q)
    )
  }
  if (filterType.value) data = data.filter(g => g.type === filterType.value)
  if (filterLoyalty.value) data = data.filter(g => g.loyalty === filterLoyalty.value)
  if (filterStatus.value) data = data.filter(g => g.status === filterStatus.value)
  return data
})

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 2) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

// ── Loyalty Badge ──────────────────────────────────────────────────
function loyaltyClass(loyalty) {
  return {
    'Base':      'bg-gray-100 text-gray-600',
    'Silver':    'bg-slate-100 text-slate-600',
    'Gold':      'bg-yellow-100 text-yellow-700',
    'Platinum':  'bg-purple-100 text-purple-600',
    'VIP':       'bg-orange-100 text-orange-600',
    'Corporate': 'bg-blue-100 text-blue-600',
  }[loyalty] || 'bg-gray-100 text-gray-500'
}
</script>