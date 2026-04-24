<template>
  <div class="space-y-5">

    <!-- Guest Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-start justify-between">
        <div class="flex items-start gap-4">
          <div class="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-500 flex-shrink-0">GW</div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900 mb-1">OGUMBA WAYNE</h1>
            <p class="text-xs text-gray-500 mb-1">+2347034600835 • ogumba@example.com • Nigeria</p>
            <p class="text-xs text-gray-400">Last Stay: 21 Feb 2026 • Guest Since: Jan 2025</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">VIP</span>
              <span class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-600 rounded-full">Gold Tier</span>
              <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Corporate Guest</span>
              <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Checked In</span>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4 text-xs" style="min-width:220px;">
          <p class="font-bold text-gray-900 mb-2">Current Stay Snapshot</p>
          <p class="text-gray-600 mb-0.5">Room: 8408 • Executive Room</p>
          <p class="text-gray-600 mb-0.5">Check-in: 21 Feb 2026</p>
          <p class="text-gray-600 mb-0.5">Check-out: 24 Feb 2026</p>
          <p class="font-bold text-red-500 mt-1">Balance: ₦41,000</p>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Total Stays</p>
        <p class="text-3xl font-bold text-gray-900">12</p>
        <p class="text-xs font-medium text-green-600 mt-1">Frequent returning guest</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Lifetime Spend</p>
        <p class="text-3xl font-bold text-gray-900">₦2.45M</p>
        <p class="text-xs font-medium text-blue-600 mt-1">High value account</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Loyalty Points</p>
        <p class="text-3xl font-bold text-gray-900">18,200</p>
        <p class="text-xs font-medium text-yellow-600 mt-1">Gold tier active</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-2">Guest Score</p>
        <p class="text-3xl font-bold text-gray-900">82 / 100</p>
        <p class="text-xs font-medium text-green-600 mt-1">Low risk • high service value</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-xl border border-gray-200 px-6">
      <div class="flex items-center gap-1 border-b border-gray-100 overflow-x-auto">
        <button v-for="tab in tabs" :key="tab"
          @click="activeTab = tab"
          class="px-4 py-3.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 -mb-px"
          :class="activeTab === tab ? 'text-gray-900 border-gray-900 bg-gray-900 text-white rounded-lg mb-1' : 'text-gray-500 border-transparent hover:text-gray-700'">
          {{ tab }}
        </button>
      </div>
    </div>

    <!-- Profile Tab -->
    <div v-if="activeTab === 'Profile'" style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Left -->
      <div class="space-y-5">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900">Editable Guest Information</h3>
            <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              @click="$router.push('/guests/' + guestId + '/edit')">Edit Guest</button>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Full Name</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">OGUMBA WAYNE</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">+2347034600835</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">ogumba@example.com</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Nigeria</div>
            </div>
            <div style="grid-column:span 2;">
              <p class="text-xs text-gray-500 mb-1.5">ID Type / Number</p>
              <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Passport • A0192391</div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Guest Preferences</h3>
          <div class="flex items-center gap-2 flex-wrap px-3 py-3 bg-gray-50 border border-gray-200 rounded-lg">
            <span class="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">High Floor</span>
            <span class="px-3 py-1 text-xs font-medium bg-green-100 text-green-600 rounded-full">Quiet Wing</span>
            <span class="px-3 py-1 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Late Checkout</span>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Stay and Spend Timeline</h3>
          <div class="space-y-4">
            <div v-for="t in timeline" :key="t.date" class="flex items-start gap-3">
              <div class="w-3 h-3 rounded-full flex-shrink-0 mt-0.5" :style="{ background: t.color }"></div>
              <div>
                <p class="text-xs font-bold text-gray-900">{{ t.date }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ t.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Guest Intelligence -->
      <div class="space-y-3">
        <h3 class="text-sm font-bold text-gray-900">Guest Intelligence</h3>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-2">Current Stay Snapshot</p>
          <p class="text-xs text-gray-600">Room: 8408 • Executive Room</p>
          <p class="text-xs text-gray-600">Check-in: 21 Feb 2026</p>
          <p class="text-xs text-gray-600">Check-out: 24 Feb 2026</p>
          <p class="text-xs font-bold text-red-500 mt-1">Outstanding: ₦41,000</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs font-bold text-gray-900 mb-2">Stay History</p>
          <p class="text-xs text-gray-600">12 completed stays</p>
          <p class="text-xs text-gray-600">Most booked room type: Executive Room</p>
          <p class="text-xs text-gray-600">Preferred channel: Walk-in / Corporate</p>
          <p class="text-xs text-gray-600">Average stay length: 3.2 nights</p>
        </div>

        <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
          <p class="text-xs font-bold text-blue-700 mb-2">Spend Mix and Composition</p>
          <p class="text-xs text-blue-600">Rooms: ₦1.8M (72%)</p>
          <p class="text-xs text-blue-600">Restaurant: ₦400K (16%)</p>
          <p class="text-xs text-blue-600">Bar: ₦150K (6%)</p>
          <p class="text-xs text-blue-600">Other: ₦100K (6%)</p>
          <div class="mt-2 h-2 bg-blue-200 rounded-full"><div class="h-2 bg-blue-600 rounded-full w-3/4"></div></div>
        </div>

        <div class="bg-purple-50 rounded-xl border border-purple-100 px-5 py-4">
          <p class="text-xs font-bold text-purple-700 mb-2">Loyalty</p>
          <p class="text-xs text-purple-600">Tier: Gold • Points: 18,200</p>
          <p class="text-xs text-purple-600">Redeemed this year: 2,400 pts</p>
        </div>

        <div class="bg-red-50 rounded-xl border border-red-100 px-5 py-4">
          <p class="text-xs font-bold text-red-600 mb-2">Messages and Risk</p>
          <p class="text-xs text-red-500">Last message: Welcome back sent on 21 Feb 2026</p>
          <p class="text-xs text-red-500">Risk: Low payment risk • Medium complaint sensitivity</p>
        </div>
      </div>
    </div>

    <!-- Other tabs placeholder -->
    <div v-if="activeTab !== 'Profile'" class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-sm text-gray-400">{{ activeTab }} content coming soon</p>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const guestId = route.params.id
const activeTab = ref('Profile')
const tabs = ['Profile', 'Stay History', 'Spend', 'Loyalty', 'Messages', 'Risk', 'Intelligence']

const timeline = [
  { date: 'Jan 2025', desc: 'First stay • ₦200,000 • Executive Room', color: '#3b82f6' },
  { date: 'Mar 2025', desc: 'Returned stay • ₦350,000 • Added dining spend', color: '#22c55e' },
  { date: 'Jul 2025', desc: 'Service complaint logged • Resolved same day', color: '#f59e0b' },
  { date: 'Feb 2026', desc: 'Current stay • ₦300,000 room charges • Balance open', color: '#8b5cf6' },
]
</script>