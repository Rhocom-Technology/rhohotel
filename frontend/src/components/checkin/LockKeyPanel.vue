<template>
  <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-bold text-gray-900">Smart Lock / Key Card</h3>
      <button @click="refresh" :disabled="loading" class="text-xs text-blue-500 hover:text-blue-700 transition-colors">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <!-- Integration disabled -->
    <div v-if="!ctx.enabled" class="bg-gray-50 rounded-lg border border-gray-200 px-4 py-3">
      <p class="text-xs text-gray-400">Smart Lock integration is not enabled. Enable it in Hotel Settings → Smart Lock Integration.</p>
    </div>

    <!-- No room mapping -->
    <div v-else-if="!ctx.has_mapping" class="bg-amber-50 rounded-lg border border-amber-200 px-4 py-3">
      <p class="text-xs font-semibold text-amber-700 mb-0.5">No Lock Mapping</p>
      <p class="text-xs text-amber-600">This room does not have a Room Lock Mapping configured. Please set one up in the Room Lock Mapping list.</p>
    </div>

    <template v-else>
      <!-- Provider badge -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
          {{ ctx.provider || 'Unknown Provider' }}
        </span>
        <span v-if="ctx.active_key"
          class="px-2.5 py-1 text-xs font-semibold bg-green-50 text-green-600 border border-green-200 rounded-full">
          Key Active
        </span>
        <span v-else class="px-2.5 py-1 text-xs font-semibold bg-gray-100 text-gray-500 border border-gray-200 rounded-full">
          No Active Key
        </span>
      </div>

      <!-- Active key details -->
      <div v-if="ctx.active_key" class="bg-green-50 rounded-lg border border-green-200 px-4 py-3">
        <p class="text-xs font-bold text-green-700 mb-1">Active Key</p>
        <div class="grid grid-cols-2 gap-x-4 gap-y-1">
          <div>
            <p class="text-xs text-gray-500">Key Ref</p>
            <p class="text-xs font-mono text-gray-700">{{ ctx.active_key.name }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Valid Until</p>
            <p class="text-xs text-gray-700">{{ fmt(ctx.active_key.valid_until) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Issued By</p>
            <p class="text-xs text-gray-700">{{ ctx.active_key.issued_by || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Issued At</p>
            <p class="text-xs text-gray-700">{{ fmt(ctx.active_key.issued_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Card number input (IC Card mode) -->
      <div v-if="ctx.requires_card_number" class="space-y-1">
        <label class="block text-xs font-medium text-gray-700">Card UID <span class="text-red-500">*</span></label>
        <div class="flex gap-2">
          <input
            v-model="cardNumber"
            type="text"
            placeholder="Scan or type card number…"
            :disabled="busy"
            class="flex-1 px-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 font-mono disabled:bg-gray-50"
            @keydown.enter.prevent
          />
          <button
            type="button"
            @click="cardNumber = ''"
            :disabled="busy || !cardNumber"
            class="px-2 py-1 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
          >Clear</button>
        </div>
        <p class="text-xs text-gray-400">Place the card on the USB reader — it will type the UID automatically, or enter it manually.</p>
      </div>

      <!-- Error / result banner -->
      <div v-if="actionError" class="bg-red-50 rounded-lg border border-red-200 px-4 py-3">
        <p class="text-xs font-bold text-red-600 mb-0.5">Operation Failed</p>
        <p class="text-xs text-red-500">{{ actionError }}</p>
      </div>
      <div v-if="actionSuccess" class="bg-green-50 rounded-lg border border-green-200 px-4 py-3">
        <p class="text-xs font-bold text-green-700">{{ actionSuccess }}</p>
      </div>

      <!-- Action buttons -->
      <div class="flex items-center gap-2 flex-wrap">
        <button
          v-if="!ctx.active_key"
          :disabled="busy"
          @click="issueKey"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ busy ? 'Working…' : 'Issue Key' }}
        </button>
        <button
          v-if="ctx.active_key"
          :disabled="busy"
          @click="reissueKey"
          class="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ busy ? 'Working…' : 'Reissue Key' }}
        </button>
        <button
          v-if="ctx.active_key"
          :disabled="busy"
          @click="cancelKey"
          class="px-4 py-2 text-xs font-medium text-red-700 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          Cancel Key
        </button>
        <button
          @click="showLogs = !showLogs"
          class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          {{ showLogs ? 'Hide Logs' : 'View Logs' }}
        </button>
      </div>

      <!-- Operation logs -->
      <div v-if="showLogs">
        <div v-if="loadingLogs" class="py-4 text-center">
          <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
        <div v-else-if="!logs.length" class="py-4 text-center">
          <p class="text-xs text-gray-400">No lock operations recorded for this stay.</p>
        </div>
        <div v-else class="rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Operation</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Status</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Time</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">By</th>
                <th class="text-left text-xs font-medium text-gray-500 px-3 py-2.5">Error</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.name"
                class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                <td class="px-3 py-2.5 text-xs text-gray-700">{{ log.operation_type }}</td>
                <td class="px-3 py-2.5">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded-full"
                    :class="log.status === 'Success' ? 'bg-green-100 text-green-600' :
                            log.status === 'Failed' ? 'bg-red-100 text-red-600' :
                            'bg-gray-100 text-gray-500'">
                    {{ log.status }}
                  </span>
                </td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ fmt(log.request_datetime) }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ log.requested_by || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-red-500">{{ log.error_message || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { callMethodForm } from '@/lib/api'

const props = defineProps({
  checkIn: { type: Object, required: true },
})

const loading = ref(false)
const busy = ref(false)
const loadingLogs = ref(false)
const showLogs = ref(false)
const actionError = ref('')
const actionSuccess = ref('')
const cardNumber = ref('')
const logs = ref([])

const ctx = ref({
  enabled: false,
  has_mapping: false,
  provider: null,
  requires_card_number: false,
  active_key: null,
  recent_logs: [],
})

function fmt(dt) {
  if (!dt) return '—'
  try {
    return new Date(dt).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return String(dt)
  }
}

async function refresh() {
  loading.value = true
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const data = await callMethodForm('rhohotel.rhocom_hotel.api.lock_api.get_lock_context', {
      check_in_name: props.checkIn.name,
    })
    ctx.value = data || ctx.value
    if (showLogs.value) await loadLogs()
  } catch (err) {
    actionError.value = String(err?.message || 'Failed to load lock context.')
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  loadingLogs.value = true
  try {
    logs.value = await callMethodForm('rhohotel.rhocom_hotel.api.lock_api.get_operation_logs', {
      check_in_name: props.checkIn.name,
      limit: 20,
    }) || []
  } catch {
    logs.value = []
  } finally {
    loadingLogs.value = false
  }
}

async function _doAction(fn) {
  busy.value = true
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const result = await fn()
    if (result?.success === false) {
      actionError.value = result.error || 'Operation failed.'
    } else {
      actionSuccess.value = 'Operation completed successfully.'
      await refresh()
    }
  } catch (err) {
    actionError.value = String(err?.message || 'Unexpected error.')
  } finally {
    busy.value = false
  }
}

function issueKey() {
  if (ctx.value.requires_card_number && !cardNumber.value.trim()) {
    actionError.value = 'Please scan or enter the card UID before issuing.'
    return
  }
  _doAction(() =>
    callMethodForm('rhohotel.rhocom_hotel.api.lock_api.issue_key', {
      check_in_name: props.checkIn.name,
      card_number: cardNumber.value.trim() || undefined,
    })
  )
}

function reissueKey() {
  if (!ctx.value.active_key?.name) return
  if (ctx.value.requires_card_number && !cardNumber.value.trim()) {
    actionError.value = 'Please scan or enter the card UID before reissuing.'
    return
  }
  _doAction(() =>
    callMethodForm('rhohotel.rhocom_hotel.api.lock_api.reissue_key', {
      guest_key_name: ctx.value.active_key.name,
      card_number: cardNumber.value.trim() || undefined,
    })
  )
}

function cancelKey() {
  if (!ctx.value.active_key?.name) return
  if (!confirm('Cancel the active key card? The guest will lose room access until a new key is issued.')) return
  _doAction(() =>
    callMethodForm('rhohotel.rhocom_hotel.api.lock_api.cancel_key', {
      guest_key_name: ctx.value.active_key.name,
    })
  )
}

// Reload logs when the tab is toggled open
const _origShowLogs = showLogs
import { watch } from 'vue'
watch(showLogs, (val) => { if (val) loadLogs() })

onMounted(refresh)
</script>
