<template>
  <div class="rounded-xl border overflow-hidden" :class="collapsed ? 'border-blue-100' : 'border-blue-200'">

    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-3 bg-blue-50 hover:bg-blue-100 cursor-pointer select-none transition-colors"
      @click="toggle"
    >
      <div class="flex items-center gap-2 min-w-0">
        <BrainCircuit class="w-4 h-4 text-blue-600 flex-shrink-0" />
        <span class="text-xs font-semibold text-blue-800 truncate">{{ title }}</span>
        <span
          v-if="aiStore.provider"
          class="px-2 py-0.5 text-xs bg-blue-200 text-blue-700 rounded-full leading-tight flex-shrink-0"
        >{{ aiStore.provider }}</span>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">
        <!-- Manual trigger (autoLoad=false) -->
        <button
          v-if="!autoLoad && !collapsed"
          @click.stop="refresh"
          :disabled="isLoading"
          class="px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-200 hover:bg-blue-300 rounded-lg transition-colors disabled:opacity-40"
        >{{ isLoading ? 'Generating…' : 'Generate' }}</button>
        <!-- Refresh (autoLoad=true, has content) -->
        <button
          v-if="autoLoad && !collapsed && hasContent && !isLoading"
          @click.stop="refresh"
          class="px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-200 hover:bg-blue-300 rounded-lg transition-colors"
        >Refresh</button>
        <ChevronDown
          class="w-4 h-4 text-blue-400 transition-transform duration-200"
          :class="collapsed ? '' : 'rotate-180'"
        />
      </div>
    </div>

    <!-- Body -->
    <div v-if="!collapsed" class="px-4 py-3 bg-blue-50 border-t border-blue-100">
      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-2 animate-pulse">
        <div class="h-2.5 bg-blue-200 rounded-full w-3/4"></div>
        <div class="h-2.5 bg-blue-200 rounded-full w-full"></div>
        <div class="h-2.5 bg-blue-200 rounded-full w-5/6"></div>
        <div class="h-2.5 bg-blue-200 rounded-full w-4/6"></div>
      </div>

      <!-- Error -->
      <p v-else-if="error" class="text-xs text-red-500">{{ error }}</p>

      <!-- AI disabled -->
      <p v-else-if="!aiStore.aiEnabled && aiStore.settingsLoaded" class="text-xs text-gray-400 italic">
        AI insights unavailable. Contact administrator to enable AI in
        <strong>Hotel Setup → AI Settings</strong>.
      </p>

      <!-- Insight text -->
      <p v-else-if="insight" class="text-xs text-blue-900 leading-relaxed whitespace-pre-wrap">{{ insight }}</p>

      <!-- Empty — manual mode -->
      <p v-else-if="!autoLoad" class="text-xs text-blue-400 italic">
        Click "Generate" to create an AI insight from current data.
      </p>

      <!-- Empty — autoLoad not yet resolved -->
      <p v-else class="text-xs text-blue-400 italic">Preparing AI insight…</p>

      <!-- Powered-by footer -->
      <p
        v-if="insight && !isLoading"
        class="text-right mt-2"
        style="font-size:10px;color:#93c5fd;"
      >Powered by {{ aiStore.provider || 'AI' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { BrainCircuit, ChevronDown } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import { useAIStore } from '@/stores/ai'

const props = defineProps({
  title:       { type: String,  default: 'AI Insight' },
  contextType: { type: String,  required: true },
  contextData: { type: Object,  default: null },
  autoLoad:    { type: Boolean, default: false },
  panelId:     { type: String,  default: 'default' },
})

const aiStore = useAIStore()

const isLoading  = ref(false)
const insight    = ref('')
const error      = ref('')
const hasLoaded  = ref(false)
const hasContent = computed(() => !!insight.value)

const storageKey = computed(() => `ai_panel_${props.panelId}_collapsed`)
const collapsed  = ref(localStorage.getItem(storageKey.value) === 'true')

function toggle() {
  collapsed.value = !collapsed.value
  localStorage.setItem(storageKey.value, String(collapsed.value))
  // Trigger load when expanding if autoLoad and not yet loaded
  if (!collapsed.value && props.autoLoad && !hasLoaded.value && props.contextData) {
    generateInsight()
  }
}

async function generateInsight() {
  if (!aiStore.aiEnabled || !props.contextData) return
  isLoading.value = true
  error.value = ''
  try {
    const resp = await callMethod('rhohotel.rhocom_hotel.api.ai_engine.generate_insight', {
      context_type: props.contextType,
      context_data: JSON.stringify(props.contextData),
    })
    insight.value  = resp?.summary || ''
    hasLoaded.value = true
  } catch {
    error.value = 'Failed to generate insight. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function refresh() {
  hasLoaded.value = false
  insight.value   = ''
  await generateInsight()
}

// Auto-load when contextData becomes available
watch(
  () => props.contextData,
  (val) => {
    if (val && props.autoLoad && !collapsed.value && !hasLoaded.value) {
      generateInsight()
    }
  },
  { immediate: true }
)

onMounted(() => {
  aiStore.loadSettings()
})
</script>
