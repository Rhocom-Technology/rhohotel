<template>
  <div class="min-h-screen bg-gray-50 p-6 space-y-5">
    <!-- Toast -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div v-for="t in toasts" :key="t.id"
        class="px-4 py-3 rounded-lg shadow-lg text-xs font-medium flex items-center gap-2 cursor-pointer"
        :class="t.type === 'success' ? 'bg-green-600 text-white' : t.type === 'warning' ? 'bg-yellow-500 text-white' : 'bg-red-600 text-white'"
        @click="removeToast(t.id)">
        {{ t.message }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
    </div>

    <template v-else-if="log">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">
            <button @click="$router.back()" class="text-gray-400 hover:text-gray-600 text-sm">← Back</button>
            <h1 class="text-lg font-bold text-gray-900">{{ log.name }}</h1>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
              :class="log.docstatus === 1 ? 'bg-green-100 text-green-700' : log.docstatus === 2 ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'">
              {{ log.docstatus === 1 ? 'Submitted' : log.docstatus === 2 ? 'Cancelled' : 'Draft' }}
            </span>
          </div>
          <p class="text-xs text-gray-500 mt-0.5">Machine: {{ log.machine_name || '—' }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="canEdit && !editMode" @click="editMode = true"
            class="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
            Edit
          </button>
          <button v-if="editMode" @click="saveLog"
            class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
          <button v-if="editMode" @click="editMode = false; resetForm()"
            class="px-4 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
            Cancel
          </button>
          <button v-if="log.docstatus === 0" @click="submitLog"
            class="px-4 py-2 text-xs font-medium text-white bg-green-600 rounded-lg hover:bg-green-700" :disabled="submitting">
            {{ submitting ? 'Submitting...' : 'Submit' }}
          </button>
          <button v-if="log.docstatus === 1" @click="cancelLog"
            class="px-4 py-2 text-xs font-medium text-white bg-red-600 rounded-lg hover:bg-red-700" :disabled="cancelling">
            {{ cancelling ? 'Cancelling...' : 'Cancel Log' }}
          </button>
        </div>
      </div>

      <!-- Linked Work Order -->
      <div v-if="log.facility_work_order" class="bg-blue-50 border border-blue-200 rounded-xl px-5 py-3 flex items-center justify-between">
        <p class="text-xs text-blue-700">
          Linked to Work Order: <span class="font-bold">{{ log.facility_work_order }}</span>
        </p>
        <router-link :to="{ name: 'FacilityWorkOrderDetail', params: { id: log.facility_work_order } }"
          class="text-xs font-medium text-blue-600 hover:underline">
          View Work Order →
        </router-link>
      </div>

      <!-- Body -->
      <div style="display:grid;grid-template-columns:1fr 340px;gap:16px;">
        <!-- Left Column -->
        <div class="space-y-4">
          <!-- Machine Details -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Machine Details</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Machine Name</p>
                <input v-if="editMode" v-model="form.machine_name" type="text"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                <p v-else class="text-xs text-gray-800">{{ log.machine_name || '—' }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Asset</p>
                <input v-if="editMode" v-model="form.asset" type="text"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                <p v-else class="text-xs text-gray-800">{{ log.asset || '—' }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Date Opened</p>
                <input v-if="editMode" v-model="form.date_opened" type="date"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                <p v-else class="text-xs text-gray-800">{{ formatDate(log.date_opened) }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Time Opened</p>
                <input v-if="editMode" v-model="form.time_opened" type="time"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                <p v-else class="text-xs text-gray-800">{{ log.time_opened || '—' }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Time Closed</p>
                <input v-if="editMode" v-model="form.time_closed" type="time"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                <p v-else class="text-xs text-gray-800">{{ log.time_closed || '—' }}</p>
              </div>
            </div>
          </div>

          <!-- Location -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Location</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Location Type</p>
                <select v-if="editMode" v-model="form.location_type"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg">
                  <option value="Room">Room</option>
                  <option value="Asset Location">Asset Location</option>
                  <option value="Other Location">Other Location</option>
                </select>
                <p v-else class="text-xs text-gray-800">{{ log.location_type || '—' }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">
                  {{ form.location_type === 'Room' ? 'Room' : form.location_type === 'Asset Location' ? 'Asset Location' : 'Description' }}
                </p>
                <template v-if="editMode">
                  <input v-if="form.location_type === 'Room'" v-model="form.room" type="text"
                    class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" placeholder="Room..." />
                  <input v-else-if="form.location_type === 'Asset Location'" v-model="form.asset_location" type="text"
                    class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" placeholder="Asset location..." />
                  <input v-else v-model="form.location_description" type="text"
                    class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" placeholder="Location description..." />
                </template>
                <p v-else class="text-xs text-gray-800">{{ log.room || log.asset_location || log.location_description || '—' }}</p>
              </div>
            </div>
          </div>

          <!-- Access Details -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Access Details</h3>
            <div class="space-y-4">
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Reason for Access</p>
                <textarea v-if="editMode" v-model="form.reason_for_access" rows="3"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg"></textarea>
                <p v-else class="text-xs text-gray-800 whitespace-pre-wrap">{{ log.reason_for_access || '—' }}</p>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-[10px] text-gray-400 mb-1">Technician</p>
                  <input v-if="editMode" v-model="form.technician" type="text"
                    class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                  <p v-else class="text-xs text-gray-800">{{ log.technician_name || log.technician || '—' }}</p>
                </div>
                <div>
                  <p class="text-[10px] text-gray-400 mb-1">Witness</p>
                  <input v-if="editMode" v-model="form.witness" type="text"
                    class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg" />
                  <p v-else class="text-xs text-gray-800">{{ log.witness_name || log.witness || '—' }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Parts & Condition -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Parts &amp; Condition</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Parts Removed</p>
                <textarea v-if="editMode" v-model="form.parts_removed" rows="3"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg"></textarea>
                <p v-else class="text-xs text-gray-800 whitespace-pre-wrap">{{ log.parts_removed || '—' }}</p>
              </div>
              <div>
                <p class="text-[10px] text-gray-400 mb-1">Condition on Exit</p>
                <textarea v-if="editMode" v-model="form.condition_on_exit" rows="3"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg"></textarea>
                <p v-else class="text-xs text-gray-800 whitespace-pre-wrap">{{ log.condition_on_exit || '—' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-4">
          <!-- Confirmations -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Confirmations</h3>
            <div class="space-y-3">
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="form.technician_confirmed" :disabled="!editMode"
                  class="rounded border-gray-300" :true-value="1" :false-value="0" />
                <span class="text-xs text-gray-700">Technician confirms this log is accurate</span>
              </label>
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="form.witness_confirmed" :disabled="!editMode"
                  class="rounded border-gray-300" :true-value="1" :false-value="0" />
                <span class="text-xs text-gray-700">Witness confirms they were present</span>
              </label>
            </div>
          </div>

          <!-- Meta Info -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-xs font-bold text-gray-700 mb-3">Information</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between">
                <span class="text-gray-400">Created by</span>
                <span class="text-gray-700">{{ log.owner }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Created</span>
                <span class="text-gray-700">{{ formatDateTime(log.creation) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Last modified</span>
                <span class="text-gray-700">{{ formatDateTime(log.modified) }}</span>
              </div>
              <div v-if="log.facility_work_order" class="flex justify-between">
                <span class="text-gray-400">Work Order</span>
                <router-link :to="{ name: 'FacilityWorkOrderDetail', params: { id: log.facility_work_order } }"
                  class="text-blue-600 hover:underline">{{ log.facility_work_order }}</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const logId = route.params.id

const loading = ref(true)
const log = ref(null)
const editMode = ref(false)
const saving = ref(false)
const submitting = ref(false)
const cancelling = ref(false)

const form = ref({})

const canEdit = computed(() => {
  return log.value && log.value.docstatus === 0
})

// Toast
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 4500) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

function parseFrappeError(data) {
  if (data._server_messages) {
    try {
      const msgs = JSON.parse(data._server_messages)
      const first = JSON.parse(msgs[0])
      return first.message || first.title || 'An error occurred'
    } catch { /* fall through */ }
  }
  if (data.exception) {
    const lines = data.exception.split('\n').filter(l => l.trim())
    const last = lines.pop() || ''
    return last.replace(/^[A-Za-z]*Error:\s*/, '') || 'An error occurred'
  }
  return data.message || 'An error occurred'
}

async function rpc(method, params = {}) {
  const response = await fetch(`/api/method/rhohotel.rhocom_hotel.api.machine_access_log.${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
    },
    body: JSON.stringify(params)
  })
  const data = await response.json()
  if (!response.ok) throw new Error(parseFrappeError(data))
  return data.message
}

onMounted(async () => {
  await loadLog()
})

async function loadLog() {
  loading.value = true
  try {
    const res = await rpc('get_machine_access_log', { name: logId })
    log.value = res
    resetForm()
  } finally {
    loading.value = false
  }
}

function resetForm() {
  if (!log.value) return
  form.value = { ...log.value }
}

async function saveLog() {
  saving.value = true
  try {
    const res = await rpc('save_machine_access_log', { name: logId, log_data: JSON.stringify(form.value) })
    if (res.success) {
      showToast('Saved successfully', 'success')
      editMode.value = false
      await loadLog()
    } else {
      showToast(res.error || 'Save failed')
    }
  } catch (e) {
    showToast(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

async function submitLog() {
  submitting.value = true
  try {
    const res = await rpc('submit_machine_access_log', { name: logId })
    if (res.success) {
      showToast('Submitted successfully', 'success')
      await loadLog()
    } else {
      showToast(res.error || 'Submit failed')
    }
  } catch (e) {
    showToast(e.message || 'Submit failed')
  } finally {
    submitting.value = false
  }
}

async function cancelLog() {
  cancelling.value = true
  try {
    const res = await rpc('cancel_machine_access_log', { name: logId })
    if (res.success) {
      showToast('Cancelled successfully', 'success')
      await loadLog()
    } else {
      showToast(res.error || 'Cancel failed')
    }
  } catch (e) {
    showToast(e.message || 'Cancel failed')
  } finally {
    cancelling.value = false
  }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
