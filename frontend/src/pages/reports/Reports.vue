<template>
  <div class="space-y-5">
    <!-- AI Report Builder -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center gap-2 mb-1">
        <BrainCircuit class="w-5 h-5 text-blue-600" />
        <h2 class="text-base font-bold text-gray-900">AI Report Builder</h2>
        <span v-if="aiStore.provider" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
          {{ aiStore.provider }}
        </span>
      </div>
      <p class="text-xs text-gray-500 mb-4">
        Ask any question about hotel operations to generate an on-demand report or summary.
      </p>

      <div class="flex gap-2">
        <input
          v-model="query"
          @keydown.enter="submit"
          type="text"
          placeholder="e.g. What is today's revenue? How many rooms are occupied?"
          maxlength="400"
          :disabled="isLoading || !aiStore.aiEnabled"
          class="flex-1 text-xs border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          @click="submit"
          :disabled="!query.trim() || isLoading || !aiStore.aiEnabled"
          class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
        >
          <Loader2 v-if="isLoading" class="w-3.5 h-3.5 animate-spin" />
          <Send v-else class="w-3.5 h-3.5" />
          {{ isLoading ? 'Asking…' : 'Ask AI' }}
        </button>
      </div>

      <!-- Suggested queries -->
      <div class="flex flex-wrap gap-2 mt-3">
        <button
          v-for="q in suggestions"
          :key="q"
          @click="query = q; submit()"
          class="px-3 py-1.5 text-xs text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-100 rounded-lg transition-colors"
        >{{ q }}</button>
      </div>

      <!-- AI Disabled notice -->
      <div v-if="!aiStore.aiEnabled && aiStore.settingsLoaded" class="mt-4 px-4 py-3 bg-yellow-50 border border-yellow-100 rounded-xl">
        <p class="text-xs text-yellow-700">AI assistant is not enabled. Contact your administrator to configure AI in <strong>Hotel Setup → AI Settings</strong>.</p>
      </div>
    </div>

    <!-- AI Response -->
    <div v-if="response || (isLoading && !response)" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center gap-2 mb-3">
        <BrainCircuit class="w-4 h-4 text-blue-500" />
        <span class="text-xs font-semibold text-gray-700">AI Response</span>
        <span class="text-xs text-gray-400 ml-auto">{{ aiStore.provider }}</span>
      </div>
      <div v-if="isLoading && !response" class="space-y-2 animate-pulse">
        <div class="h-2.5 bg-gray-200 rounded-full w-3/4"></div>
        <div class="h-2.5 bg-gray-200 rounded-full w-full"></div>
        <div class="h-2.5 bg-gray-200 rounded-full w-5/6"></div>
      </div>
      <p v-else class="text-xs text-gray-800 leading-relaxed whitespace-pre-wrap">{{ response }}</p>
    </div>

    <!-- Standard Reports -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Standard Reports</h3>
      <div class="space-y-2">
        <router-link
          to="/reports/corporate-account-statement"
          class="flex items-center justify-between px-4 py-3 text-xs font-medium text-gray-700 hover:bg-gray-50 border border-gray-100 rounded-xl transition-colors"
        >
          <span>Corporate Account Statement</span>
          <span class="text-gray-400">→</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { BrainCircuit, Send, Loader2 } from 'lucide-vue-next'
import { useAIStore } from '@/stores/ai'

const aiStore = useAIStore()

const query    = ref('')
const response = ref('')
const isLoading = ref(false)

const suggestions = [
  "What's today's revenue?",
  'How many rooms are currently occupied?',
  'List guests with outstanding balances',
  'Any overdue checkouts?',
  "What's the housekeeping completion rate?",
]

async function submit() {
  const text = query.value.trim()
  if (!text || isLoading.value || !aiStore.aiEnabled) return
  isLoading.value = true
  response.value = ''
  try {
    await aiStore.loadSettings()
    await aiStore.sendMessage(text)
    // Show the latest assistant message
    const last = aiStore.chatHistory[aiStore.chatHistory.length - 1]
    response.value = last?.role === 'assistant' ? last.content : ''
  } finally {
    isLoading.value = false
  }
}
</script>
