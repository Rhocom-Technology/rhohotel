<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Track new tickets, preparation progress, ready pickups, and delayed kitchen orders across restaurant and room service.</p>
    </div>

    <!-- Kitchen Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Kitchen Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Live kitchen board for restaurant dining, room service, takeaway, and bar snack preparation.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="showSettings = true">Kitchen Settings</button>
        <button class="px-4 py-2 text-xs font-semibold rounded-lg transition-colors"
          :class="autoRefresh ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="autoRefresh = !autoRefresh">
          {{ autoRefresh ? 'Auto Refresh On' : 'Auto Refresh Off' }}
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">New Tickets</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">8</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">In Preparation</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Busy</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">14</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Ready for Pickup</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">5</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Delayed Orders</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">3</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Kitchen Board Filters</h3>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1" style="min-width:180px;">
          <input v-model="search" type="text" placeholder="Search ticket, room, table..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterStation" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Stations</option>
          <option>Hot Kitchen</option>
          <option>Cold Kitchen</option>
          <option>Bar Snacks</option>
        </select>
        <select v-model="filterSource" class="px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
          <option value="">All Sources</option>
          <option>Restaurant Dining</option>
          <option>Room Service</option>
          <option>Takeaway</option>
        </select>
        <button @click="search='';filterStation='';filterSource='';showDelayedOnly=false"
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors"
          :class="showDelayedOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showDelayedOnly = !showDelayedOnly">
          {{ showDelayedOnly ? 'Show All Tickets' : 'Show Delayed Tickets Only' }}
        </button>
      </div>
    </div>

    <!-- Kanban Board -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;align-items:start;">

      <!-- New -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <h3 class="text-sm font-bold text-gray-900">New</h3>
          <span class="px-2 py-0.5 text-xs font-bold bg-blue-100 text-blue-600 rounded-full">{{ newTickets.length }}</span>
        </div>
        <div class="p-3 space-y-3">
          <div v-for="t in newTickets" :key="t.id"
            class="bg-white rounded-xl border border-gray-200 px-4 py-3 hover:border-blue-200 transition-colors cursor-pointer">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-blue-600">{{ t.id }} • {{ t.table }}</span>
              <span class="text-xs text-gray-400">{{ t.time }}</span>
            </div>
            <div v-for="item in t.items" :key="item" class="text-xs font-bold text-gray-900 leading-tight">{{ item }}</div>
            <div v-for="extra in t.extras" :key="extra" class="text-xs text-gray-500">{{ extra }}</div>
            <div class="text-xs text-gray-400 mt-1">Source: {{ t.source }}</div>
            <button class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Start Prep</button>
          </div>
        </div>
      </div>

      <!-- Preparing -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <h3 class="text-sm font-bold text-gray-900">Preparing</h3>
          <span class="px-2 py-0.5 text-xs font-bold bg-yellow-100 text-yellow-600 rounded-full">{{ preparingTickets.length }}</span>
        </div>
        <div class="p-3 space-y-3">
          <div v-for="t in preparingTickets" :key="t.id"
            class="rounded-xl border px-4 py-3 transition-colors cursor-pointer"
            :class="t.mins >= 20 ? 'bg-orange-50 border-orange-200' : 'bg-white border-gray-200 hover:border-yellow-200'">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-yellow-600">{{ t.id }} • {{ t.table }}</span>
              <span class="text-xs text-gray-400">{{ t.time }}</span>
            </div>
            <div v-for="item in t.items" :key="item" class="text-xs font-bold text-gray-900 leading-tight">{{ item }}</div>
            <div v-for="extra in t.extras" :key="extra" class="text-xs text-gray-500">{{ extra }}</div>
            <div class="text-xs text-gray-400 mt-1">Chef Station: {{ t.station }}</div>
            <div class="flex items-center gap-2 mt-2.5">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="t.mins >= 20 ? 'bg-orange-100 text-orange-600' : 'bg-yellow-100 text-yellow-600'">
                {{ t.mins }} mins
              </span>
              <button class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Mark Ready</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Ready -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <h3 class="text-sm font-bold text-gray-900">Ready</h3>
          <span class="px-2 py-0.5 text-xs font-bold bg-green-100 text-green-600 rounded-full">{{ readyTickets.length }}</span>
        </div>
        <div class="p-3 space-y-3">
          <div v-for="t in readyTickets" :key="t.id"
            class="bg-green-50 rounded-xl border border-green-200 px-4 py-3 cursor-pointer hover:border-green-300 transition-colors">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-green-700">{{ t.id }} • {{ t.table }}</span>
              <span class="text-xs text-gray-400">{{ t.time }}</span>
            </div>
            <div v-for="item in t.items" :key="item" class="text-xs font-bold text-gray-900 leading-tight">{{ item }}</div>
            <div v-for="extra in t.extras" :key="extra" class="text-xs text-gray-500">{{ extra }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ t.note }}</div>
            <button class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Dispatch</button>
          </div>
        </div>
      </div>

      <!-- Delayed -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <h3 class="text-sm font-bold text-gray-900">Delayed</h3>
          <span class="px-2 py-0.5 text-xs font-bold bg-red-100 text-red-500 rounded-full">{{ delayedTickets.length }}</span>
        </div>
        <div class="p-3 space-y-3">
          <div v-for="t in delayedTickets" :key="t.id"
            class="bg-red-50 rounded-xl border border-red-200 px-4 py-3 cursor-pointer hover:border-red-300 transition-colors">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-red-500">{{ t.id }} • {{ t.table }}</span>
              <span class="text-xs text-gray-400">{{ t.time }}</span>
            </div>
            <div v-for="item in t.items" :key="item" class="text-xs font-bold text-gray-900 leading-tight">{{ item }}</div>
            <div v-for="extra in t.extras" :key="extra" class="text-xs text-gray-500">{{ extra }}</div>
            <div class="text-xs text-gray-400 mt-1">Delay reason: {{ t.reason }}</div>
            <div class="flex items-center gap-2 mt-2.5">
              <span class="px-2.5 py-1 text-xs font-semibold bg-red-100 text-red-500 rounded-full">{{ t.mins }} mins</span>
              <button class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Escalate Chef</button>
            </div>
            <button class="mt-2 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Mark Ready</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Kitchen Status Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-500">
        <span class="font-semibold text-gray-700">Kitchen Status: </span>
        14 orders in active preparation, 5 ready for service, 3 delayed tickets need intervention.
      </p>
    </div>

    <!-- Kitchen Settings Modal -->
    <KitchenSettingsModal v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import KitchenSettingsModal from '@/components/kitchen/KitchenSettingsModal.vue'

const autoRefresh = ref(true)
const showSettings = ref(false)
const search = ref('')
const filterStation = ref('')
const filterSource = ref('')
const showDelayedOnly = ref(false)

const newTickets = [
  { id: 'KOT-00184', table: 'Table 03', time: '10:46 AM', items: ['2 × Grilled Chicken Meal'], extras: ['1 × Fresh Orange Juice'], source: 'Restaurant Dining' },
  { id: 'KOT-00185', table: 'Room 305', time: '10:49 AM', items: ['1 × Club Sandwich'],        extras: ['1 × Cappuccino'],           source: 'Room Service' },
]

const preparingTickets = [
  { id: 'KOT-00178', table: 'Table 08', time: '09:58 AM', items: ['2 × Pepper Soup'],  extras: ['1 × Grilled Fish'],    station: 'Hot Kitchen', mins: 12 },
  { id: 'KOT-00180', table: 'Table 02', time: '10:12 AM', items: ['3 × Fried Rice'],   extras: ['2 × Chicken Wings'],   station: 'Hot Kitchen', mins: 18 },
  { id: 'KOT-00182', table: 'Room 214', time: '10:22 AM', items: ['2 × Club Sandwich'],extras: ['1 × Orange Juice'],    station: 'Cold Kitchen', mins: 8 },
]

const readyTickets = [
  { id: 'KOT-00174', table: 'Table 01', time: '09:42 AM', items: ['1 × Burger Combo'],  extras: ['1 × Sparkling Water'], note: 'Awaiting service pickup' },
  { id: 'KOT-00176', table: 'Room 402', time: '09:51 AM', items: ['1 × Caesar Salad'],  extras: ['1 × Orange Juice'],    note: 'Room service tray ready' },
]

const delayedTickets = [
  { id: 'KOT-00169', table: 'Table 06', time: '09:20 AM', items: ['2 × Grilled Chicken Meal'], extras: ['1 × Jollof Rice'],  reason: 'ingredient refill', mins: 32 },
  { id: 'KOT-00171', table: 'Table 11', time: '09:28 AM', items: ['1 × Seafood Pasta'],        extras: ['1 × Garlic Bread'], reason: 'recook requested',  mins: 27 },
]
</script>