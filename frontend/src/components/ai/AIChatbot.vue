<template>
  <!-- Floating container (bottom-right) -->
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

    <!-- Chat Panel -->
    <Transition name="chat-slide">
      <div
        v-if="aiStore.isChatOpen"
        class="bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col"
        style="width:390px;height:580px;max-height:calc(100vh - 100px);"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 bg-gray-900 rounded-t-2xl flex-shrink-0">
          <div class="flex items-center gap-2">
            <BrainCircuit class="w-4 h-4 text-blue-400" />
            <span class="text-sm font-semibold text-white">Hotel AI Assistant</span>
          </div>
          <div class="flex items-center gap-2">
            <!-- Provider badge (read-only) -->
            <div
              v-if="aiStore.provider"
              class="flex items-center gap-1 px-2 py-0.5 bg-gray-800 rounded-full cursor-default"
              title="Configure provider in Hotel Setup → AI Settings"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"></span>
              <span class="text-xs text-gray-300">{{ aiStore.provider }}</span>
            </div>
            <!-- Role badge -->
            <span class="px-2 py-0.5 text-xs bg-blue-900 text-blue-300 rounded-full">{{ roleLabel }}</span>
            <!-- Auto-speak toggle -->
            <button
              v-if="ttsSupported"
              @click="toggleAutoSpeak"
              class="p-1 rounded transition-colors"
              :class="autoSpeak ? 'text-green-400 hover:text-green-200' : 'text-gray-500 hover:text-gray-200'"
              :title="autoSpeak ? 'Auto-speak ON — click to disable' : 'Auto-speak OFF — click to enable'"
            >
              <Volume2 class="w-3.5 h-3.5" />
            </button>
            <!-- Stop TTS -->
            <button
              v-if="isSpeaking"
              @click="stopSpeaking"
              class="p-1 text-yellow-400 hover:text-yellow-200 rounded transition-colors"
              title="Stop speaking"
            >
              <VolumeX class="w-3.5 h-3.5" />
            </button>
            <!-- Clear history -->
            <button
              v-if="aiStore.chatHistory.length"
              @click="clearAll"
              class="p-1 text-gray-400 hover:text-gray-200 transition-colors rounded"
              title="Clear conversation"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
            <!-- Close -->
            <button
              @click="aiStore.closeChat()"
              class="p-1 text-gray-400 hover:text-gray-200 transition-colors rounded"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Messages area -->
        <div ref="messagesEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">

          <!-- AI not enabled -->
          <div
            v-if="!aiStore.aiEnabled && aiStore.settingsLoaded"
            class="flex flex-col items-center justify-center h-full text-center"
          >
            <BrainCircuit class="w-8 h-8 text-gray-300 mb-3" />
            <p class="text-xs font-medium text-gray-500 mb-1">AI Assistant Not Configured</p>
            <p class="text-xs text-gray-400 leading-relaxed">
              Contact your administrator to enable AI in<br/>
              <strong>Hotel Setup → AI Settings</strong>
            </p>
          </div>

          <!-- Empty state with suggestions -->
          <div v-else-if="!aiStore.chatHistory.length" class="flex flex-col gap-3 pt-3 pb-2">
            <div class="text-center">
              <BrainCircuit class="w-8 h-8 text-blue-500 mx-auto mb-1.5" />
              <p class="text-xs font-semibold text-gray-700">How can I help you?</p>
              <p class="text-xs text-gray-400 mt-0.5">
                Tap a topic or type your question.
                <span v-if="sttSupported">🎤 Tap mic to speak.</span>
              </p>
            </div>

            <!-- Categorised keyword chips -->
            <div class="space-y-2.5 overflow-y-auto" style="max-height:380px;">
              <div v-for="cat in promptCategories" :key="cat.label">
                <p class="text-xs font-semibold mb-1 flex items-center gap-1" :style="{ color: cat.color }">
                  <span>{{ cat.icon }}</span> {{ cat.label }}
                </p>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="prompt in cat.prompts"
                    :key="prompt"
                    @click="sendSuggestion(prompt)"
                    class="px-2.5 py-1.5 text-xs rounded-lg border transition-colors text-left"
                    :style="{ color: cat.color, background: cat.bg, borderColor: cat.border }"
                  >{{ prompt }}</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Messages -->
          <template v-else>
            <div
              v-for="msg in aiStore.chatHistory"
              :key="msg.id"
              :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
            >
              <!-- User bubble -->
              <div
                v-if="msg.role === 'user'"
                class="px-3 py-2 rounded-xl rounded-br-sm text-xs leading-relaxed bg-blue-600 text-white"
                style="max-width:82%;white-space:pre-wrap;word-break:break-word;"
              >
                {{ msg.content }}
                <span class="block mt-1 opacity-50 text-right" style="font-size:10px;">
                  {{ fmtTime(msg.timestamp) }}
                </span>
              </div>

              <!-- AI bubble with speak button -->
              <div v-else class="flex items-end gap-1.5" style="max-width:88%;">
                <div
                  :class="[
                    'flex-1 px-3 py-2 rounded-xl rounded-bl-sm text-xs leading-relaxed',
                    msg.isError
                      ? 'bg-red-50 text-red-600 border border-red-100'
                      : 'bg-gray-100 text-gray-800',
                  ]"
                  style="white-space:pre-wrap;word-break:break-word;"
                >
                  {{ msg.content }}
                  <span class="block mt-1 opacity-40" style="font-size:10px;">
                    {{ fmtTime(msg.timestamp) }}
                  </span>
                </div>
                <!-- Per-message speak button -->
                <button
                  v-if="ttsSupported && !msg.isError"
                  @click="speakMessage(msg)"
                  class="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full transition-colors mb-4"
                  :class="speakingMsgId === msg.id
                    ? 'bg-green-100 text-green-600 animate-pulse'
                    : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'"
                  :title="speakingMsgId === msg.id ? 'Playing — click to stop' : 'Read aloud'"
                >
                  <Volume2 v-if="speakingMsgId !== msg.id" class="w-3 h-3" />
                  <VolumeX v-else class="w-3 h-3" />
                </button>
              </div>
            </div>

            <!-- Typing indicator -->
            <div v-if="aiStore.isLoading" class="flex justify-start">
              <div class="bg-gray-100 px-3 py-2.5 rounded-xl rounded-bl-sm flex items-center gap-1">
                <span class="typing-dot"></span>
                <span class="typing-dot" style="animation-delay:0.15s;"></span>
                <span class="typing-dot" style="animation-delay:0.3s;"></span>
              </div>
            </div>
          </template>
        </div>

        <!-- Voice recording bar (shown while recording) -->
        <div
          v-if="isRecording"
          class="flex items-center gap-3 px-4 py-2.5 bg-red-50 border-t border-red-100 flex-shrink-0"
        >
          <span class="w-2.5 h-2.5 rounded-full bg-red-500 flex-shrink-0 animate-pulse"></span>
          <span class="flex-1 text-xs text-red-600 truncate font-medium">
            {{ interimText || 'Listening…' }}
          </span>
          <button
            @click="stopRecording"
            class="px-2.5 py-1 text-xs font-semibold text-red-700 bg-red-100 hover:bg-red-200 rounded-lg transition-colors"
          >
            Done
          </button>
        </div>

        <!-- Input area -->
        <div class="border-t border-gray-100 px-3 py-3 flex-shrink-0">
          <div class="flex items-end gap-1.5">
            <!-- Mic button -->
            <button
              v-if="sttSupported"
              @click="toggleRecording"
              :disabled="aiStore.isLoading || !aiStore.aiEnabled"
              class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :class="isRecording
                ? 'bg-red-500 text-white mic-pulse'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
              :title="isRecording ? 'Stop recording' : 'Speak your question'"
            >
              <Mic class="w-3.5 h-3.5" />
            </button>

            <textarea
              ref="textareaEl"
              v-model="inputText"
              @keydown.enter.exact.prevent="submit"
              @keydown.enter.shift.exact="inputText += '\n'"
              @input="autoResize"
              :placeholder="isRecording ? 'Listening…' : 'Ask about hotel operations…'"
              rows="1"
              maxlength="500"
              :disabled="aiStore.isLoading || !aiStore.aiEnabled || isRecording"
              class="flex-1 resize-none text-xs border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              style="max-height:80px;overflow-y:auto;"
            ></textarea>

            <!-- Send button -->
            <button
              @click="submit"
              :disabled="!inputText.trim() || aiStore.isLoading || !aiStore.aiEnabled"
              class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Send class="w-3.5 h-3.5" />
            </button>
          </div>
          <div class="flex items-center justify-between mt-1">
            <span v-if="!sttSupported" class="text-gray-300" style="font-size:10px;">
              Voice input not supported in this browser
            </span>
            <span v-else-if="!ttsSupported" class="text-gray-300" style="font-size:10px;">
              Voice output not supported in this browser
            </span>
            <span v-else class="text-gray-300" style="font-size:10px;">
              🎤 tap mic to speak · 🔊 tap bubble to hear
            </span>
            <span class="text-gray-300" style="font-size:10px;">{{ inputText.length }}/500</span>
          </div>

          <div v-if="ttsSupported" class="mt-2 flex items-center gap-2">
            <label class="text-gray-400" style="font-size:10px;">Narrator voice</label>
            <select
              v-model="selectedVoicePreset"
              class="flex-1 text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              :disabled="isSpeaking"
              title="Voice preset is saved per user"
            >
              <option value="en-US-female">English (United States) - Female</option>
              <option value="en-US-male">English (United States) - Male</option>
              <option value="en-GB-female">English (United Kingdom) - Female</option>
              <option value="en-GB-male">English (United Kingdom) - Male</option>
            </select>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Floating trigger button -->
    <button
      @click="aiStore.toggleChat()"
      class="relative w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-all duration-200 hover:scale-110"
      :class="aiStore.isChatOpen ? 'bg-gray-800' : 'bg-blue-600'"
      :title="aiStore.isChatOpen ? 'Close AI Assistant' : 'Open AI Assistant'"
    >
      <X v-if="aiStore.isChatOpen" class="w-5 h-5 text-white" />
      <BrainCircuit v-else class="w-5 h-5 text-white" />
      <!-- Unread indicator dot -->
      <span
        v-if="!aiStore.isChatOpen && hasUnread"
        class="absolute -top-0.5 -right-0.5 w-3 h-3 bg-red-500 rounded-full border-2 border-white"
      ></span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { BrainCircuit, X, Send, Trash2, Mic, Volume2, VolumeX } from 'lucide-vue-next'
import { useAIStore } from '@/stores/ai'
import { useSessionStore } from '@/stores/session'

const aiStore = useAIStore()
const session = useSessionStore()

const inputText  = ref('')
const messagesEl = ref(null)
const textareaEl = ref(null)
const hasUnread  = ref(false)

// ── Speech-to-Text (STT) ─────────────────────────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const sttSupported = !!SpeechRecognition

const isRecording  = ref(false)
const interimText  = ref('')
let recognition    = null

function buildRecognition() {
  if (!sttSupported) return null
  const r = new SpeechRecognition()
  r.lang            = 'en-US'
  r.interimResults  = true
  r.continuous      = false
  r.maxAlternatives = 1

  r.onresult = (e) => {
    let interim = ''
    let final   = ''
    for (const result of e.results) {
      if (result.isFinal) final   += result[0].transcript
      else                interim += result[0].transcript
    }
    interimText.value = interim
    if (final) {
      inputText.value  = (inputText.value + ' ' + final).trim()
      interimText.value = ''
    }
  }

  r.onerror = (e) => {
    if (e.error !== 'aborted') console.warn('STT error:', e.error)
    isRecording.value = false
    interimText.value  = ''
  }

  r.onend = () => {
    isRecording.value = false
    interimText.value  = ''
    // Auto-submit if we got a transcript and no text was already in the box
    if (inputText.value.trim()) {
      // Small delay so the last result is committed
      setTimeout(submit, 120)
    }
  }

  return r
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  if (!sttSupported || isRecording.value) return
  stopSpeaking()
  recognition = buildRecognition()
  if (!recognition) return
  inputText.value   = ''
  interimText.value  = ''
  isRecording.value = true
  try {
    recognition.start()
  } catch {
    isRecording.value = false
  }
}

function stopRecording() {
  if (recognition) {
    try { recognition.stop() } catch { /* ignore */ }
  }
  isRecording.value = false
  interimText.value  = ''
}

// ── Text-to-Speech (TTS) ─────────────────────────────────────────────────────
const ttsSupported  = 'speechSynthesis' in window
const isSpeaking    = ref(false)
const speakingMsgId = ref(null)
const autoSpeak     = ref(localStorage.getItem('ai_auto_speak') === 'true')
const availableVoices = ref([])
const selectedVoicePreset = ref('auto')

const voiceStorageKey = computed(() => {
  const userKey = session.user || 'guest'
  return `ai_voice_preset_${userKey}`
})

const femaleHints = ['female', 'woman', 'zira', 'susan', 'hazel', 'samantha', 'victoria', 'karen', 'moira']
const maleHints = ['male', 'man', 'david', 'james', 'john', 'daniel', 'george', 'fred', 'alex']

function getDefaultVoice(voices) {
  if (!voices?.length) return null
  return voices.find(v =>
    v.lang?.toLowerCase().startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.localService)
  ) || voices.find(v => v.lang?.toLowerCase().startsWith('en')) || voices[0]
}

function hasHint(name, hints) {
  const n = (name || '').toLowerCase()
  return hints.some(h => n.includes(h))
}

function resolveVoiceByPreset(preset, voices) {
  if (!voices?.length || !preset || preset === 'auto') return null

  const [lang, region, gender] = preset.split('-')
  const locale = `${lang || ''}-${region || ''}`.toLowerCase()
  const localeVoices = voices.filter(v => (v.lang || '').toLowerCase().startsWith(locale))
  if (!localeVoices.length) return null

  if (gender === 'female') {
    return localeVoices.find(v => hasHint(v.name, femaleHints)) || localeVoices[0]
  }
  if (gender === 'male') {
    return localeVoices.find(v => hasHint(v.name, maleHints)) || localeVoices[0]
  }
  return localeVoices[0]
}

function loadSelectedVoiceFromStorage() {
  try {
    const stored = localStorage.getItem(voiceStorageKey.value)
    selectedVoicePreset.value = stored || 'en-US-female'
  } catch {
    selectedVoicePreset.value = 'en-US-female'
  }
}

function persistSelectedVoice() {
  try {
    localStorage.setItem(voiceStorageKey.value, selectedVoicePreset.value || 'auto')
  } catch {
    // Ignore storage issues.
  }
}

function refreshVoices() {
  if (!ttsSupported) return
  const voices = window.speechSynthesis.getVoices() || []
  availableVoices.value = [...voices].sort((a, b) => {
    const an = (a?.name || '').toLowerCase()
    const bn = (b?.name || '').toLowerCase()
    if (an < bn) return -1
    if (an > bn) return 1
    return 0
  })
}

function toggleAutoSpeak() {
  autoSpeak.value = !autoSpeak.value
  localStorage.setItem('ai_auto_speak', String(autoSpeak.value))
}

function speakMessage(msg) {
  if (!ttsSupported) return
  if (speakingMsgId.value === msg.id) {
    stopSpeaking()
    return
  }
  stopSpeaking()
  const utter = new SpeechSynthesisUtterance(msg.content)
  utter.lang  = 'en-US'
  utter.rate  = 1.0
  utter.pitch = 1.0

  const voices = availableVoices.value.length
    ? availableVoices.value
    : window.speechSynthesis.getVoices()
  const selected = resolveVoiceByPreset(selectedVoicePreset.value, voices)
  const preferred = selected || getDefaultVoice(voices)
  if (preferred) {
    utter.voice = preferred
    utter.lang = preferred.lang || utter.lang
  }

  utter.onstart = () => {
    isSpeaking.value    = true
    speakingMsgId.value = msg.id
  }
  utter.onend = utter.onerror = () => {
    isSpeaking.value    = false
    speakingMsgId.value = null
  }

  window.speechSynthesis.speak(utter)
}

function stopSpeaking() {
  if (ttsSupported) window.speechSynthesis.cancel()
  isSpeaking.value    = false
  speakingMsgId.value = null
}

watch(
  () => voiceStorageKey.value,
  () => {
    loadSelectedVoiceFromStorage()
    refreshVoices()
  },
  { immediate: true }
)

watch(selectedVoicePreset, () => {
  persistSelectedVoice()
})

// Auto-speak new AI responses when toggle is ON
watch(
  () => aiStore.chatHistory.length,
  async (newLen, oldLen) => {
    await nextTick()
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    if (!aiStore.isChatOpen) hasUnread.value = true

    if (autoSpeak.value && newLen > oldLen) {
      const last = aiStore.chatHistory[aiStore.chatHistory.length - 1]
      if (last?.role === 'assistant' && !last.isError) {
        speakMessage(last)
      }
    }
  }
)

// ── General ──────────────────────────────────────────────────────────────────
const roleLabel = computed(() => {
  const roles = session.roles || []
  if (roles.includes('System Manager'))        return 'System Manager'
  if (roles.includes('Hotel Manager'))         return 'Hotel Manager'
  if (roles.includes('Front Desk Manager'))    return 'Front Desk Mgr'
  if (roles.includes('Hotel Receptionist'))    return 'Receptionist'
  if (roles.includes('Housekeeping Supervisor')) return 'Housekeeping'
  if (roles.includes('POS User'))              return 'POS User'
  return 'Staff'
})

// Flat list kept for voice/report pages that use suggestedPrompts
const suggestedPrompts = computed(() => {
  const roles = session.roles || []
  if (roles.includes('System Manager') || roles.includes('Hotel Manager')) {
    return [
      "What's today's revenue and occupancy?",
      'List guests with outstanding balances',
      'Any overdue checkouts right now?',
      'How many rooms need housekeeping?',
      "What's today's total payments collected?",
      'Show maintenance summary',
    ]
  }
  if (roles.includes('Front Desk Manager') || roles.includes('Hotel Receptionist')) {
    return [
      'How many rooms are occupied right now?',
      'Any overdue checkouts today?',
      'Search for a guest by name',
      "What's today's occupancy rate?",
      'Show in-house guest list',
      'Any confirmed reservations for today?',
    ]
  }
  if (roles.includes('Housekeeping Supervisor')) {
    return [
      'How many housekeeping tasks are pending?',
      'What is the current completion rate?',
      'How many tasks are in progress?',
    ]
  }
  if (roles.includes('POS User')) {
    return [
      "What's today's POS gross sales?",
      'How many POS invoices today?',
      "What's the payment breakdown today?",
    ]
  }
  return [
    'How many rooms are occupied?',
    "What's the current occupancy rate?",
  ]
})

// Categorised chips shown on the empty state — filtered by role
const promptCategories = computed(() => {
  const roles = session.roles || []
  const isManager = roles.includes('System Manager') || roles.includes('Hotel Manager') || roles.includes('Front Desk Manager')
  const isReceptionist = roles.includes('Hotel Receptionist') || isManager
  const isHousekeeping = roles.includes('Housekeeping Supervisor') || isManager
  const isMaintenance = isManager
  const isPOS = roles.includes('POS User') || isManager

  const cats = []

  if (isReceptionist) {
    cats.push({
      label: 'Rooms & Occupancy',
      icon: '🛏️',
      color: '#1d4ed8',
      bg: '#eff6ff',
      border: '#bfdbfe',
      prompts: [
        'How many rooms are occupied?',
        'How many vacant rooms are available?',
        "What's today's occupancy rate?",
        'How many rooms are under maintenance?',
        'Show rooms that need cleaning',
        'How many rooms are dirty right now?',
      ],
    })

    cats.push({
      label: 'Check-ins & Check-outs',
      icon: '🔑',
      color: '#065f46',
      bg: '#ecfdf5',
      border: '#a7f3d0',
      prompts: [
        'Show all in-house guests',
        'Any overdue checkouts?',
        'How many guests checked in today?',
        'How many checkouts are expected today?',
        'Show guests past their checkout time',
        'Who is still checked in with an outstanding balance?',
      ],
    })

    cats.push({
      label: 'Reservations',
      icon: '📅',
      color: '#5b21b6',
      bg: '#f5f3ff',
      border: '#ddd6fe',
      prompts: [
        'Show confirmed reservations for today',
        'Any reservations on hold?',
        'How many no-shows are recorded?',
        'List reservations checking in today',
        'Show cancelled reservations',
        'Any reservations expiring soon?',
      ],
    })

    cats.push({
      label: 'Guests',
      icon: '👤',
      color: '#92400e',
      bg: '#fffbeb',
      border: '#fde68a',
      prompts: [
        'Search for a guest by name',
        'Show VIP guests currently in house',
        'List guests with outstanding balances',
        'Who are our Gold or Platinum loyalty guests?',
        'Show corporate guests currently staying',
        'Find a guest by phone number',
      ],
    })
  }

  if (isManager) {
    cats.push({
      label: 'Revenue & Billing',
      icon: '💰',
      color: '#be185d',
      bg: '#fdf2f8',
      border: '#f9a8d4',
      prompts: [
        "What's today's total revenue?",
        "What's this month's room revenue?",
        'Show unpaid invoices',
        'List overdue invoices',
        "What's the total outstanding balance?",
        "What's today's total payments collected?",
        'Show payment breakdown by method',
        'Any unallocated payment receipts?',
        'Show corporate outstanding bills',
      ],
    })
  }

  if (isHousekeeping) {
    cats.push({
      label: 'Housekeeping',
      icon: '🧹',
      color: '#0369a1',
      bg: '#f0f9ff',
      border: '#bae6fd',
      prompts: [
        'How many housekeeping tasks are pending?',
        'How many tasks are in progress?',
        'What is the task completion rate today?',
        'How many tasks are on hold?',
        'Show high priority housekeeping tasks',
        'How many tasks are approved today?',
      ],
    })
  }

  if (isMaintenance) {
    cats.push({
      label: 'Maintenance',
      icon: '🔧',
      color: '#b45309',
      bg: '#fff7ed',
      border: '#fed7aa',
      prompts: [
        'How many maintenance tasks are open?',
        'Any urgent repair requests?',
        'How many maintenance tasks completed today?',
        'Show open maintenance requests',
        'How many preventive tasks are scheduled?',
      ],
    })
  }

  if (isPOS) {
    cats.push({
      label: 'POS & Payments',
      icon: '🧾',
      color: '#065f46',
      bg: '#f0fdf4',
      border: '#bbf7d0',
      prompts: [
        "What's today's POS gross sales?",
        'How many POS invoices were raised today?',
        "What's the payment breakdown by method today?",
        'Show payments collected this week',
      ],
    })
  }

  return cats
})

async function submit() {
  const text = inputText.value.trim()
  if (!text || aiStore.isLoading || !aiStore.aiEnabled) return
  stopSpeaking()
  inputText.value = ''
  if (textareaEl.value) textareaEl.value.style.height = 'auto'
  await aiStore.sendMessage(text)
}

async function sendSuggestion(text) {
  inputText.value = text
  await submit()
}

function clearAll() {
  stopSpeaking()
  stopRecording()
  aiStore.clearHistory()
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 80) + 'px'
}

function fmtTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })
}

// Clear unread dot when panel opens; stop audio when panel closes
watch(
  () => aiStore.isChatOpen,
  async (open) => {
    if (open) {
      hasUnread.value = false
      await nextTick()
      if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    } else {
      stopSpeaking()
      stopRecording()
    }
  }
)

onMounted(() => {
  aiStore.loadSettings()
  if (ttsSupported) {
    loadSelectedVoiceFromStorage()
    refreshVoices()
    window.speechSynthesis.onvoiceschanged = refreshVoices
  }
})

onBeforeUnmount(() => {
  if (ttsSupported) window.speechSynthesis.onvoiceschanged = null
  stopSpeaking()
  stopRecording()
})
</script>

<style scoped>
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.97);
}

.typing-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typing-bounce 0.8s ease-in-out infinite;
}
@keyframes typing-bounce {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-5px); }
}

.mic-pulse {
  animation: mic-ring 1.2s ease-in-out infinite;
}
@keyframes mic-ring {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
  50%       { box-shadow: 0 0 0 7px rgba(239,68,68,0); }
}
</style>
