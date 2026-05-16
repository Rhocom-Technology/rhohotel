import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { callMethod } from '@/lib/api'

export const useAIStore = defineStore('ai', () => {
  const isChatOpen = ref(false)
  const isLoading = ref(false)
  /** @type {import('vue').Ref<Array<{id:number, role:string, content:string, timestamp:string, isError?:boolean}>>} */
  const chatHistory = ref([])

  const provider = ref('')
  const providerModel = ref('')
  const aiEnabled = ref(false)
  const settingsLoaded = ref(false)

  let _idCounter = 0
  function _nextId() { return ++_idCounter }

  async function loadSettings() {
    if (settingsLoaded.value) return
    try {
      const cfg = await callMethod('rhohotel.rhocom_hotel.api.ai_engine.get_ai_config')
      aiEnabled.value = Boolean(cfg?.enabled)
      provider.value = cfg?.provider || ''
      providerModel.value = cfg?.model || ''
    } catch {
      aiEnabled.value = false
    }
    settingsLoaded.value = true
  }

  async function sendMessage(text) {
    if (!text?.trim() || isLoading.value) return

    chatHistory.value.push({
      id: _nextId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    })
    isLoading.value = true

    // Pass up to the last 10 messages as conversation history
    const history = chatHistory.value
      .slice(-11, -1)
      .map(m => ({ role: m.role, content: m.content }))

    try {
      const response = await callMethod('rhohotel.rhocom_hotel.api.ai_engine.chat', {
        message: text.trim(),
        history: JSON.stringify(history),
      })
      chatHistory.value.push({
        id: _nextId(),
        role: 'assistant',
        content: response?.answer || 'No response received.',
        timestamp: new Date().toISOString(),
      })
    } catch {
      chatHistory.value.push({
        id: _nextId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true,
      })
    } finally {
      isLoading.value = false
    }
  }

  function clearHistory() {
    chatHistory.value = []
  }

  function toggleChat() {
    isChatOpen.value = !isChatOpen.value
  }

  function openChat() { isChatOpen.value = true }
  function closeChat() { isChatOpen.value = false }

  const providerLabel = computed(() => {
    if (!provider.value) return 'AI'
    return providerModel.value
      ? `${provider.value} · ${providerModel.value}`
      : provider.value
  })

  return {
    isChatOpen,
    isLoading,
    chatHistory,
    provider,
    providerModel,
    providerLabel,
    aiEnabled,
    settingsLoaded,
    loadSettings,
    sendMessage,
    clearHistory,
    toggleChat,
    openChat,
    closeChat,
  }
})
