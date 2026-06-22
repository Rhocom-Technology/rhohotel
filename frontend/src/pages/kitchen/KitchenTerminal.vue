<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Track new tickets, preparation progress, ready pickups, and delayed kitchen orders across restaurant and room service.</p>
    </div>

    <!-- Kitchen Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Kitchen Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Live kitchen board for restaurant dining, room service, takeaway, and bar snack preparation.</p>
      </div>
      <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
        <button v-if="canEditKitchen" class="w-full px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors sm:w-auto"
          @click="showSettings = true">Kitchen Settings</button>
        <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto"
          @click="manualRefresh">Refresh</button>
        <button class="w-full px-4 py-2 text-xs font-semibold rounded-lg transition-colors sm:w-auto"
          :class="autoRefresh ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50'"
          @click="autoRefresh = !autoRefresh">
          {{ autoRefresh ? 'Auto Refresh On' : 'Auto Refresh Off' }}
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
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
    <div class="bg-white rounded-xl border border-gray-200 px-4 py-5 sm:px-6">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Kitchen Board Filters</h3>
      <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div class="w-full sm:min-w-[180px] sm:flex-1">
          <input v-model="search" type="text" placeholder="Search ticket, room, table..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <select v-model="filterStation" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Stations</option>
          <option>Hot Kitchen</option>
          <option>Cold Kitchen</option>
          <option>Bar Snacks</option>
        </select>
        <select v-model="filterSource" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Sources</option>
          <option>Restaurant Dining</option>
          <option>Room Service</option>
          <option>Takeaway</option>
        </select>
        <button @click="search='';filterStation='';filterSource='';showDelayedOnly=false"
          class="w-full px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors sm:w-auto">Reset</button>
        <button
          class="w-full px-5 py-2.5 text-xs font-semibold rounded-lg transition-colors sm:w-auto"
          :class="showDelayedOnly ? 'text-white bg-red-500 hover:bg-red-600' : 'text-white bg-blue-600 hover:bg-blue-700'"
          @click="showDelayedOnly = !showDelayedOnly">
          {{ showDelayedOnly ? 'Show All Tickets' : 'Show Delayed Tickets Only' }}
        </button>
      </div>
    </div>

    <!-- Kanban Board -->
    <div class="grid grid-cols-1 gap-3 md:grid-cols-2 2xl:grid-cols-4 items-start">

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
            class="rounded-xl border px-4 py-3 transition-colors cursor-pointer"
            :class="newTicketCardClass(t)">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-blue-600">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="flex items-center justify-between text-xs mt-1">
              <span class="text-gray-400">Source: {{ t.source }}</span>
              <span class="font-semibold" :class="newTicketAgeClass(t)">{{ countdownLabel(t, kitchenSettings.newTicketMinutes) }}</span>
            </div>
            <button v-if="canEditKitchen" class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
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
            :class="preparingCardClass(t)">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-yellow-600">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="text-xs text-gray-400 mt-1">Chef Station: {{ t.chef_station || 'General' }}</div>
            <div class="flex items-center gap-2 mt-2.5">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="preparingBadgeClass(t)">
                {{ countdownLabel(t, kitchenSettings.preparationMinutes) }}
              </span>
              <button v-if="canEditKitchen" class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
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
            class="rounded-xl border px-4 py-3 cursor-pointer transition-colors"
            :class="readyCardClass(t)">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-green-700">{{ t.id }} • {{ t.table_or_room || '—' }}</span>
              <span class="text-xs text-gray-400">{{ formatTime(t.sent_at) }}</span>
            </div>
            <div v-for="line in itemLines(t)" :key="`${t.id}-${line}`" class="text-xs font-bold text-gray-900 leading-tight">{{ line }}</div>
            <div v-for="line in noteLines(t)" :key="`${t.id}-note-${line}`" class="text-xs text-gray-500">{{ line }}</div>
            <div class="mt-2">
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="readyBadgeClass(t)">
                {{ countdownLabel(t, kitchenSettings.readyPickupMinutes) }}
              </span>
            </div>
            <button v-if="canEditKitchen" class="mt-2.5 w-full px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
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
              <span class="px-2.5 py-1 text-xs font-semibold bg-red-100 text-red-500 rounded-full">{{ timerMins(t) }} mins</span>
              <button v-if="canEditKitchen" class="px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                :disabled="updating === t.id"
                @click="setStatus(t.id, 'In Progress')">Escalate Chef</button>
            </div>
            <button v-if="canEditKitchen" class="mt-2 w-full px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
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
    <KitchenSettingsModal v-if="showSettings" :settings="kitchenSettings" @save="saveKitchenSettings" @close="showSettings = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import { ROLE_GROUPS } from '@/lib/permissions'
import KitchenSettingsModal from '@/components/kitchen/KitchenSettingsModal.vue'

const session = useSessionStore()
const canEditKitchen = computed(() => session.hasAnyRole(ROLE_GROUPS.kitchenActions))

const autoRefresh = ref(true)
const showSettings = ref(false)
const search = ref('')
const filterStation = ref('')
const filterSource = ref('')
const showDelayedOnly = ref(false)
const updating = ref(null)  // ticket name being updated
const clockNow = ref(Date.now())
let lastTicketCount = 0
let refreshInterval = null
let countdownInterval = null

const defaultKitchenSettings = {
  station: 'Hot Kitchen',
  ticketView: 'All Tickets',
  kitchenNote: '',
  newTicketMinutes: 5,
  preparationMinutes: 25,
  warningMinutes: 15,
  criticalMinutes: 25,
  readyPickupMinutes: 10,
  autoRefreshSeconds: 15,
}

function loadKitchenSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('rhohotel_kitchen_settings') || '{}')
    const settings = { ...defaultKitchenSettings, ...saved }
    if (!saved.preparationMinutes && saved.criticalMinutes) {
      settings.preparationMinutes = Number(saved.criticalMinutes) || defaultKitchenSettings.preparationMinutes
    }
    return settings
  } catch (_) {
    return { ...defaultKitchenSettings }
  }
}

const kitchenSettings = ref(loadKitchenSettings())

function kitchenTicketParams() {
  return {
    pending_delay_minutes: kitchenSettings.value.criticalMinutes,
    preparing_delay_minutes: kitchenSettings.value.preparationMinutes,
  }
}

function reloadTickets() {
  ticketsResource.params = kitchenTicketParams()
  ticketsResource.reload()
}

function reloadStats() {
  statsResource.params = kitchenTicketParams()
  statsResource.reload()
}

function setRefreshTimer() {
  if (refreshInterval) clearInterval(refreshInterval)
  refreshInterval = setInterval(() => {
    if (autoRefresh.value) {
      reloadTickets()
      reloadStats()
    }
  }, kitchenSettings.value.autoRefreshSeconds * 1000)
}

function saveKitchenSettings(nextSettings) {
  kitchenSettings.value = { ...kitchenSettings.value, ...nextSettings }
  localStorage.setItem('rhohotel_kitchen_settings', JSON.stringify(kitchenSettings.value))
  setRefreshTimer()
  reloadTickets()
  reloadStats()
}

function playNewTicketSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    // Short double-beep: urgent but not annoying
    [[880, 0], [1046.5, 0.18]].forEach(([freq, delay]) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'square'
      osc.frequency.value = freq
      const t = ctx.currentTime + delay
      gain.gain.setValueAtTime(0, t)
      gain.gain.linearRampToValueAtTime(0.15, t + 0.01)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14)
      osc.start(t)
      osc.stop(t + 0.14)
    })
  } catch (_) {}
}

// ── API ────────────────────────────────────────────────────────────────────
const ticketsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_tickets',
  params: kitchenTicketParams(),
  auto: true,
  onSuccess(data) {
    const count = (data || []).filter(t => t.status === 'Pending').length
    if (count > lastTicketCount && lastTicketCount >= 0) playNewTicketSound()
    lastTicketCount = count
  },
})

const statsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_stats',
  params: kitchenTicketParams(),
  auto: true,
})

const statusResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.update_ticket_status',
  onSuccess() {
    updating.value = null
    reloadTickets()
    reloadStats()
  },
  onError() {
    updating.value = null
  },
})

onMounted(() => {
  setRefreshTimer()
  countdownInterval = setInterval(() => {
    clockNow.value = Date.now()
  }, 1000)
})
onUnmounted(() => {
  clearInterval(refreshInterval)
  clearInterval(countdownInterval)
})

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
  return parts
}

function parseKitchenTime(value) {
  if (!value) return null
  const normalized = String(value).replace(' ', 'T')
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

function stageStartTime(t) {
  if (t.status === 'In Progress' || t.status === 'Ready') {
    return parseKitchenTime(t.modified) || parseKitchenTime(t.sent_at)
  }
  return parseKitchenTime(t.sent_at)
}

function timerMins(t) {
  const startedAt = stageStartTime(t)
  if (!startedAt) return Number(t.stage_mins ?? t.mins ?? 0)
  return Math.max(0, Math.floor((clockNow.value - startedAt) / 60000))
}

function remainingMinutes(t, limit) {
  return Math.max(0, Number(limit || 0) - timerMins(t))
}

function countdownLabel(t, limit) {
  const elapsed = timerMins(t)
  const remaining = remainingMinutes(t, limit)
  if (remaining > 0) return `${remaining} min left`
  return `Over ${Math.max(0, elapsed - Number(limit || 0))} min`
}

function preparingCardClass(t) {
  const elapsed = timerMins(t)
  if (elapsed >= kitchenSettings.value.preparationMinutes) return 'bg-red-50 border-red-200'
  if (elapsed >= kitchenSettings.value.warningMinutes) return 'bg-orange-50 border-orange-200'
  return 'bg-white border-gray-200 hover:border-yellow-200'
}

function preparingBadgeClass(t) {
  const elapsed = timerMins(t)
  if (elapsed >= kitchenSettings.value.preparationMinutes) return 'bg-red-100 text-red-600'
  if (elapsed >= kitchenSettings.value.warningMinutes) return 'bg-orange-100 text-orange-600'
  return 'bg-yellow-100 text-yellow-600'
}

function newTicketCardClass(t) {
  const elapsed = timerMins(t)
  if (elapsed >= kitchenSettings.value.criticalMinutes) return 'bg-red-50 border-red-200 hover:border-red-300'
  if (elapsed >= kitchenSettings.value.warningMinutes) return 'bg-orange-50 border-orange-200 hover:border-orange-300'
  if (elapsed < kitchenSettings.value.newTicketMinutes) return 'bg-blue-50 border-blue-200 hover:border-blue-300'
  return 'bg-white border-gray-200 hover:border-blue-200'
}

function newTicketAgeClass(t) {
  const elapsed = timerMins(t)
  if (elapsed >= kitchenSettings.value.criticalMinutes) return 'text-red-600'
  if (elapsed >= kitchenSettings.value.warningMinutes) return 'text-orange-600'
  if (elapsed < kitchenSettings.value.newTicketMinutes) return 'text-blue-600'
  return 'text-gray-400'
}

function readyCardClass(t) {
  if (remainingMinutes(t, kitchenSettings.value.readyPickupMinutes) <= 0) return 'bg-orange-50 border-orange-200 hover:border-orange-300'
  return 'bg-green-50 border-green-200 hover:border-green-300'
}

function readyBadgeClass(t) {
  if (remainingMinutes(t, kitchenSettings.value.readyPickupMinutes) <= 0) return 'bg-orange-100 text-orange-600'
  return 'bg-green-100 text-green-700'
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
  reloadTickets()
  reloadStats()
}
</script>