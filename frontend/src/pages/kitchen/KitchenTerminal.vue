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
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="manualRefresh">Refresh</button>
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
        <p class="text-3xl font-bold text-gray-900">{{ stats.new }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">In Preparation</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Busy</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.preparing }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Ready for Pickup</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.ready }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Delayed Orders</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-500 rounded-full">Alert</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.delayed }}</p>
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

      <div v-if="ticketsResource.loading" class="col-span-4 bg-white rounded-xl border border-gray-200 p-8 text-center text-xs text-gray-400">
        Loading kitchen tickets...
      </div>
      <div v-else-if="ticketsResource.error" class="col-span-4 bg-white rounded-xl border border-red-200 p-8 text-center text-xs text-red-500">
        Failed to load kitchen tickets.
      </div>

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
              <span class="text-xs font-bold text-blue-600">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="text-xs text-gray-400 mt-1">Source: {{ t.source }}</div>
            <button class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              :disabled="updating === t.id"
              @click="setStatus(t.id, 'In Progress')">
              {{ updating === t.id ? 'Updating...' : 'Start Prep' }}
            </button>
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
              <span class="text-xs font-bold text-yellow-600">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="text-xs text-gray-400 mt-1">Chef Station: {{ t.chef_station || 'General' }}</div>
            <div class="flex items-center gap-2 mt-2.5">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="t.mins >= 20 ? 'bg-orange-100 text-orange-600' : 'bg-yellow-100 text-yellow-600'">
                {{ t.mins }} mins
              </span>
              <button class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                :disabled="updating === t.id"
                @click="setStatus(t.id, 'Ready')">Mark Ready</button>
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
              <span class="text-xs font-bold text-green-700">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <button class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="updating === t.id"
              @click="setStatus(t.id, 'Served')">Dispatch</button>
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
              <span class="text-xs font-bold text-red-500">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="flex items-center gap-2 mt-2.5">
              <span class="px-2.5 py-1 text-xs font-semibold bg-red-100 text-red-500 rounded-full">{{ t.mins }} mins</span>
              <button class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                :disabled="updating === t.id"
                @click="setStatus(t.id, 'In Progress')">Escalate Chef</button>
            </div>
            <button class="mt-2 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              :disabled="updating === t.id"
              @click="setStatus(t.id, 'Ready')">Mark Ready</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Kitchen Status Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-500">
        <span class="font-semibold text-gray-700">Kitchen Status: </span>
        {{ stats.preparing }} orders in active preparation, {{ stats.ready }} ready for service, {{ stats.delayed }} delayed tickets need intervention.
      </p>
    </div>

    <!-- Kitchen Settings Modal -->
    <KitchenSettingsModal v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import KitchenSettingsModal from '@/components/kitchen/KitchenSettingsModal.vue'

const autoRefresh = ref(true)
const showSettings = ref(false)
const search = ref('')
const filterStation = ref('')
const filterSource = ref('')
const showDelayedOnly = ref(false)
const updating = ref(null)  // ticket name being updated

// ── API ────────────────────────────────────────────────────────────────────
const ticketsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_tickets',
  auto: true,
})

const statsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_stats',
  auto: true,
})

const statusResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.update_ticket_status',
  onSuccess() {
    updating.value = null
    ticketsResource.reload()
    statsResource.reload()
  },
  onError() {
    updating.value = null
  },
})

// ── Auto-refresh ──────────────────────────────────────────────────────────
let refreshInterval = null
onMounted(() => {
  refreshInterval = setInterval(() => {
    if (autoRefresh.value) {
      ticketsResource.reload()
      statsResource.reload()
    }
  }, 15000)
})
onUnmounted(() => clearInterval(refreshInterval))

// ── Stats ─────────────────────────────────────────────────────────────────
const stats = computed(() => statsResource.data || { new: 0, preparing: 0, ready: 0, delayed: 0 })

// ── Helpers ───────────────────────────────────────────────────────────────
function formatTime(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function itemLines(t) {
  return (t.items || []).map(i => `${i.qty} × ${i.item_name || i.item_code}`)
}

function noteLines(t) {
  const parts = []
  if (t.notes) parts.push(t.notes)
  if (t.source) parts.push(`Source: ${t.source}`)
  return parts
}

// ── Ticket buckets (filtered) ─────────────────────────────────────────────
const allTickets = computed(() => {
  let list = ticketsResource.data || []
  if (filterStation.value) list = list.filter(t => t.chef_station === filterStation.value)
  if (filterSource.value)  list = list.filter(t => t.source === filterSource.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t =>
      t.id.toLowerCase().includes(q) ||
      (t.table_or_room || '').toLowerCase().includes(q) ||
      (t.pos_invoice || '').toLowerCase().includes(q)
    )
  }
  return list
})

const newTickets      = computed(() => showDelayedOnly.value ? [] : allTickets.value.filter(t => t.status === 'Pending'))
const preparingTickets = computed(() => showDelayedOnly.value ? [] : allTickets.value.filter(t => t.status === 'In Progress'))
const readyTickets    = computed(() => showDelayedOnly.value ? [] : allTickets.value.filter(t => t.status === 'Ready'))
const delayedTickets  = computed(() => allTickets.value.filter(t => t.status === 'Delayed'))

// ── Actions ───────────────────────────────────────────────────────────────
function setStatus(ticket, status) {
  if (updating.value) return
  updating.value = ticket
  statusResource.submit({ ticket_name: ticket, status })
}

function manualRefresh() {
  ticketsResource.reload()
  statsResource.reload()
}
</script>