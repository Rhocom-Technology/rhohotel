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

    <div v-if="kitchenPrintError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-xs text-red-700">
      {{ kitchenPrintError }}
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
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
        <select v-if="posProfiles.length > 0" v-model="filterPosProfile" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 sm:w-auto">
          <option value="">All Service Points</option>
          <option v-for="p in posProfiles" :key="p" :value="p">{{ p }}</option>
        </select>
        <button @click="search='';filterStation='';filterSource='';filterPosProfile='';showDelayedOnly=false"
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
            <div v-if="t.pos_profile" class="text-xs text-gray-400 mt-0.5">Service Point: {{ t.pos_profile }}</div>
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
            <div v-if="t.pos_profile" class="text-xs text-gray-400 mt-0.5">Service Point: {{ t.pos_profile }}</div>
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
            <div v-if="t.pos_profile" class="text-xs text-gray-400 mt-0.5">Service Point: {{ t.pos_profile }}</div>
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
            <div v-if="t.pos_profile" class="text-xs text-gray-400 mt-0.5">Service Point: {{ t.pos_profile }}</div>
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
import { callMethod } from '@/lib/api.js'
import { printRawCommandsDirect } from '@/lib/posPrint'
import { socket } from '@/lib/socket'
import KitchenSettingsModal from '@/components/kitchen/KitchenSettingsModal.vue'

const session = useSessionStore()
const canEditKitchen = computed(() => session.hasAnyRole(ROLE_GROUPS.kitchenActions))
const canReceiveKitchenAlerts = computed(() => session.isLoggedIn && session.hasAnyRole(ROLE_GROUPS.kitchenActions))

const autoRefresh = ref(true)
const showSettings = ref(false)
const search = ref('')
const filterStation = ref('')
const filterSource = ref('')
const filterPosProfile = ref('')
const posProfiles = ref([])
const showDelayedOnly = ref(false)
const updating = ref(null)  // ticket name being updated
const clockNow = ref(Date.now())
const kitchenPrintError = ref('')
let refreshInterval = null
let countdownInterval = null
let kitchenAudioContext = null
let knownTicketIds = null
const printedTicketIds = new Set(JSON.parse(sessionStorage.getItem('rhohotel_printed_kitchen_tickets') || '[]'))
const failedPrintTicketIds = new Set()
const activePrintTicketIds = new Set()

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

function getKitchenAudioContext() {
  if (kitchenAudioContext) return kitchenAudioContext
  const AudioCtor = window.AudioContext || window.webkitAudioContext
  if (!AudioCtor) return null
  kitchenAudioContext = new AudioCtor()
  return kitchenAudioContext
}

async function unlockKitchenAudio() {
  try {
    const ctx = getKitchenAudioContext()
    if (ctx?.state === 'suspended') await ctx.resume()
  } catch (_) {}
}

function playNewTicketSound() {
  try {
    const ctx = getKitchenAudioContext()
    if (!ctx) return
    if (ctx.state === 'suspended') ctx.resume();
    // Short double-beep: urgent but not noisy.
    [[880, 0], [1046.5, 0.18]].forEach(([freq, delay]) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'square'
      osc.frequency.value = freq
      const t = ctx.currentTime + delay
      gain.gain.setValueAtTime(0.0001, t)
      gain.gain.linearRampToValueAtTime(0.14, t + 0.01)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14)
      osc.start(t)
      osc.stop(t + 0.14)
    })
  } catch (_) {}
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[char]))
}

function formatTicketDateTime(value) {
  if (!value) return ''
  const parsed = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleString([], {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function normalizePrinterText(value) {
  return String(value ?? '')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/[^\x20-\x7E\n]/g, '')
}

function wrapPrinterText(value, width = 32) {
  const words = normalizePrinterText(value).split(/\s+/).filter(Boolean)
  const lines = []
  let current = ''

  for (const word of words) {
    if (!current) {
      current = word
    } else if (`${current} ${word}`.length <= width) {
      current = `${current} ${word}`
    } else {
      lines.push(current)
      current = word
    }
  }

  if (current) lines.push(current)
  return lines.length ? lines : ['']
}

function centerPrinterText(value, width = 32) {
  const text = normalizePrinterText(value).slice(0, width)
  const left = Math.max(0, Math.floor((width - text.length) / 2))
  return `${' '.repeat(left)}${text}`
}

function buildKitchenTicketRawCommands(ticket) {
  const ESC = '\x1B'
  const GS = '\x1D'
  const width = 32
  const lines = []

  lines.push(`${ESC}@`)
  lines.push(`${ESC}a\x01`)
  lines.push(`${ESC}E\x01${centerPrinterText('KITCHEN TICKET', width)}${ESC}E\x00`)
  lines.push(centerPrinterText(ticket.id || '', width))
  lines.push(`${ESC}a\x00`)
  lines.push('-'.repeat(width))
  lines.push(`Where : ${normalizePrinterText(ticket.table_or_room || '-')}`.slice(0, width))
  lines.push(`Source: ${normalizePrinterText(ticket.source || '-')}`.slice(0, width))
  if (ticket.pos_profile) lines.push(`POS   : ${normalizePrinterText(ticket.pos_profile)}`.slice(0, width))
  lines.push(`Sent  : ${normalizePrinterText(formatTicketDateTime(ticket.sent_at))}`.slice(0, width))
  lines.push('-'.repeat(width))

  for (const item of ticket.items || []) {
    const qty = normalizePrinterText(item.qty || 0)
    const name = normalizePrinterText(item.item_name || item.item_code || 'Item')
    const itemLines = wrapPrinterText(`${qty} x ${name}`, width)
    lines.push(`${ESC}E\x01${itemLines[0]}${ESC}E\x00`)
    for (const continuation of itemLines.slice(1)) lines.push(continuation)
    if (item.notes) {
      for (const noteLine of wrapPrinterText(`Note: ${item.notes}`, width)) lines.push(noteLine)
    }
  }

  if (ticket.notes) {
    lines.push('-'.repeat(width))
    for (const noteLine of wrapPrinterText(`ORDER NOTE: ${ticket.notes}`, width)) lines.push(noteLine)
  }

  lines.push('-'.repeat(width))
  lines.push('\n\n')
  lines.push(`${GS}V\x42\x00`)
  return lines.join('\n')
}

async function printKitchenTicket(ticket) {
  if (!ticket?.id || activePrintTicketIds.has(ticket.id)) return false

  activePrintTicketIds.add(ticket.id)
  try {
    await printRawCommandsDirect(buildKitchenTicketRawCommands(ticket), { directTimeoutMs: 45000 })
    kitchenPrintError.value = ''
    return true
  } catch (error) {
    console.warn('[Kitchen Print] Direct print failed.', error)
    const message = error?.message || 'Direct print failed'
    kitchenPrintError.value = `${ticket.id} was not printed. ${message}. Check QZ Tray is running and allowed for this site.`
    return false
  } finally {
    activePrintTicketIds.delete(ticket.id)
  }
}

function rememberPrintedTicket(ticketId) {
  printedTicketIds.add(ticketId)
  failedPrintTicketIds.delete(ticketId)
  sessionStorage.setItem('rhohotel_printed_kitchen_tickets', JSON.stringify([...printedTicketIds].slice(-100)))
}

async function notifyAndPrintKitchenTicket(ticket, { refresh = false } = {}) {
  if (!canReceiveKitchenAlerts.value || !ticket?.id || printedTicketIds.has(ticket.id)) return
  playNewTicketSound()
  const printed = await printKitchenTicket(ticket)
  if (printed) {
    rememberPrintedTicket(ticket.id)
  } else {
    failedPrintTicketIds.add(ticket.id)
  }
  if (refresh) {
    reloadTickets()
    reloadStats()
  }
}

function handleKitchenTicketCreated(ticket) {
  notifyAndPrintKitchenTicket(ticket, { refresh: true })
}

function detectNewTicketsFromPoll(tickets) {
  const ids = new Set((tickets || []).map((ticket) => ticket.id).filter(Boolean))
  if (knownTicketIds === null) {
    knownTicketIds = ids
    return
  }

  for (const ticket of tickets || []) {
    const shouldRetry = ticket.id && failedPrintTicketIds.has(ticket.id)
    const isNewPending = ticket.status === 'Pending' && ticket.id && !knownTicketIds.has(ticket.id)
    if (shouldRetry || isNewPending) notifyAndPrintKitchenTicket(ticket)
  }
  knownTicketIds = ids
}

// ── API ────────────────────────────────────────────────────────────────────
const ticketsResource = createResource({
  url: 'rhohotel.restaurant.api.kitchen.get_kitchen_tickets',
  params: kitchenTicketParams(),
  auto: true,
  onSuccess(data) {
    detectNewTicketsFromPoll(data || [])
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

onMounted(async () => {
  setRefreshTimer()
  countdownInterval = setInterval(() => {
    clockNow.value = Date.now()
  }, 1000)
  socket?.on('rhohotel_kitchen_ticket_created', handleKitchenTicketCreated)
  window.addEventListener('pointerdown', unlockKitchenAudio, { once: true })
  window.addEventListener('keydown', unlockKitchenAudio, { once: true })
  // Load POS profile options for filter
  try {
    const profiles = await callMethod('rhohotel.restaurant.api.kitchen.get_kitchen_pos_profiles')
    posProfiles.value = profiles || []
  } catch (_) {}
})
onUnmounted(() => {
  clearInterval(refreshInterval)
  clearInterval(countdownInterval)
  socket?.off('rhohotel_kitchen_ticket_created', handleKitchenTicketCreated)
  window.removeEventListener('pointerdown', unlockKitchenAudio)
  window.removeEventListener('keydown', unlockKitchenAudio)
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
  if (filterPosProfile.value) list = list.filter(t => t.pos_profile === filterPosProfile.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t =>
      t.id.toLowerCase().includes(q) ||
      (t.table_or_room || '').toLowerCase().includes(q) ||
      (t.pos_invoice || '').toLowerCase().includes(q) ||
      (t.pos_profile || '').toLowerCase().includes(q)
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