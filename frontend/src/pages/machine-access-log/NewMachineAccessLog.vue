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

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2">
          <button @click="$router.back()" class="text-gray-400 hover:text-gray-600 text-sm">← Back</button>
          <h1 class="text-lg font-bold text-gray-900">New Machine Access Log</h1>
        </div>
        <p class="text-xs text-gray-500 mt-0.5">Record machine access for maintenance or inspection.</p>
      </div>
    </div>

    <!-- Linked Work Order Banner -->
    <div v-if="form.facility_work_order && prefilled" class="bg-blue-50 border border-blue-200 rounded-xl px-5 py-3 flex items-center gap-3">
      <p class="text-xs text-blue-700">
        Linked to Work Order: <span class="font-bold">{{ form.facility_work_order }}</span>
        — Asset, machine name, and location have been pre-filled from the work order.
      </p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
      <!-- Form -->
      <div class="space-y-4">
        <!-- Facility Work Order (Required) -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Facility Work Order</h3>
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <p class="text-xs text-gray-500 mb-1.5">Facility Work Order <span class="text-red-400">*</span></p>
              <div class="flex items-center gap-2">
                <input v-model="form.facility_work_order" type="text" placeholder="e.g. FWO-00012"
                  :disabled="prefilled"
                  class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:text-gray-500" />
                <button v-if="!prefilled" @click="fetchWorkOrderData" :disabled="!form.facility_work_order || loadingWO"
                  class="px-4 py-2.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {{ loadingWO ? 'Loading...' : 'Load' }}
                </button>
              </div>
              <p class="text-[10px] text-gray-400 mt-1">Enter a Work Order ID and click Load to pre-fill asset, machine name, and location.</p>
            </div>
          </div>
        </div>

        <!-- Machine Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Machine Details</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Asset <span class="text-red-400">*</span></p>
              <input v-if="prefilled" :value="form.asset" type="text" disabled
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-500" />
              <select v-else v-model="form.asset" @change="onAssetChange"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="">Select asset...</option>
                <option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name }} ({{ a.name }})</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Machine Name</p>
              <input :value="form.machine_name" type="text" disabled
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
                placeholder="Auto-filled from asset" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Date Opened <span class="text-red-400">*</span></p>
              <input v-model="form.date_opened" type="date"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Time Opened</p>
              <input v-model="form.time_opened" type="time"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Time Closed</p>
              <input v-model="form.time_closed" type="time"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>
        </div>

        <!-- Location -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Location</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Location Type</p>
              <select v-model="form.location_type" :disabled="prefilled"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:text-gray-500">
                <option value="Room">Room</option>
                <option value="Asset Location">Asset Location</option>
                <option value="Other Location">Other Location</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">
                {{ form.location_type === 'Room' ? 'Room' : form.location_type === 'Asset Location' ? 'Asset Location' : 'Location Description' }}
              </p>
              <template v-if="prefilled">
                <input :value="form.location_type === 'Room' ? form.room : form.location_type === 'Asset Location' ? form.asset_location : form.location_description"
                  type="text" disabled
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-500" />
              </template>
              <template v-else>
                <select v-if="form.location_type === 'Room'" v-model="form.room"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                  <option value="">— select room —</option>
                  <option v-for="r in rooms" :key="r.name" :value="r.name">{{ r.name }}</option>
                </select>
                <select v-else-if="form.location_type === 'Asset Location'" v-model="form.asset_location"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                  <option value="">— select location —</option>
                  <option v-for="loc in locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option>
                </select>
                <input v-else v-model="form.location_description" type="text" placeholder="e.g. Generator House"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </template>
            </div>
          </div>
        </div>

        <!-- Access Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Access Details</h3>
          <div class="space-y-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reason for Access <span class="text-red-400">*</span></p>
              <textarea v-model="form.reason_for_access" rows="3" placeholder="Describe the reason for accessing this machine..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Technician</p>
                <select v-model="form.technician"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                  <option value="">Select technician...</option>
                  <option v-for="t in technicians" :key="t.name" :value="t.name">{{ t.technician_name }} ({{ t.name }})</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Witness</p>
                <select v-model="form.witness"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                  <option value="">Select witness...</option>
                  <option v-for="w in witnesses" :key="w.name" :value="w.name">{{ w.employee_name }} ({{ w.name }})</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Parts & Condition -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Parts &amp; Condition</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Parts Removed</p>
              <textarea v-model="form.parts_removed" rows="3" placeholder="List any parts removed..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"></textarea>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Condition on Exit</p>
              <textarea v-model="form.condition_on_exit" rows="3" placeholder="Describe machine condition after work..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"></textarea>
            </div>
          </div>
        </div>

        <!-- Confirmations -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-xs font-bold text-gray-700 mb-4">Confirmations</h3>
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.technician_confirmed" :true-value="1" :false-value="0"
                class="rounded border-gray-300" />
              <span class="text-xs text-gray-700">Technician confirms accuracy</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.witness_confirmed" :true-value="1" :false-value="0"
                class="rounded border-gray-300" />
              <span class="text-xs text-gray-700">Witness confirms presence</span>
            </label>
          </div>
        </div>

        <!-- Submit -->
        <div class="flex items-center gap-3">
          <button @click="createLog" :disabled="creating"
            class="px-6 py-3 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {{ creating ? 'Creating...' : 'Create Machine Access Log' }}
          </button>
          <button @click="$router.back()"
            class="px-6 py-3 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <h4 class="text-xs font-bold text-gray-700 mb-2">Preview</h4>
          <div class="space-y-2 text-xs">
            <div class="flex justify-between"><span class="text-gray-400">Work Order</span><span class="text-gray-700">{{ form.facility_work_order || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">Asset</span><span class="text-gray-700">{{ form.asset || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">Machine</span><span class="text-gray-700">{{ form.machine_name || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">Date</span><span class="text-gray-700">{{ form.date_opened || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">Location</span><span class="text-gray-700">{{ form.room || form.asset_location || form.location_description || '—' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">Technician</span><span class="text-gray-700">{{ form.technician || '—' }}</span></div>
          </div>
        </div>

        <div class="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <h4 class="text-xs font-bold text-gray-700 mb-2">Instructions</h4>
          <div class="space-y-2">
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">1.</span>
              <p class="text-xs text-gray-600">Enter a Facility Work Order ID and click <strong>Load</strong> to auto-fill details.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">2.</span>
              <p class="text-xs text-gray-600">Review auto-filled asset, machine, date, and location.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">3.</span>
              <p class="text-xs text-gray-600">Describe the reason for access and assign technician/witness.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">4.</span>
              <p class="text-xs text-gray-600">Click <strong>Create</strong> to save as Draft.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const router = useRouter()
const creating = ref(false)
const loadingWO = ref(false)
const prefilled = ref(false)

const technicians = ref([])
const witnesses = ref([])
const rooms = ref([])
const locations = ref([])
const assets = ref([])

const form = ref({
  facility_work_order: '',
  asset: '',
  machine_name: '',
  date_opened: new Date().toISOString().slice(0, 10),
  time_opened: '',
  time_closed: '',
  location_type: 'Room',
  room: '',
  asset_location: '',
  location_description: '',
  reason_for_access: '',
  technician: '',
  witness: '',
  parts_removed: '',
  condition_on_exit: '',
  technician_confirmed: 0,
  witness_confirmed: 0,
})

// Pre-fill work order from query param
onMounted(async () => {
  if (route.query.work_order) {
    form.value.facility_work_order = route.query.work_order
  }
  await loadDropdowns()
  if (form.value.facility_work_order) {
    await fetchWorkOrderData()
  }
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

// Resources
const techResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.machine_access_log.get_technicians_list',
  auto: false
})
const witnessResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.machine_access_log.get_witnesses_list',
  auto: false
})
const roomResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_rooms_list',
  auto: false
})
const locationResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_locations_list',
  auto: false
})
const assetResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_assets_list',
  auto: false
})

async function loadDropdowns() {
  const [techRes, witRes, roomRes, locRes, assetRes] = await Promise.all([
    techResource.fetch(),
    witnessResource.fetch(),
    roomResource.fetch(),
    locationResource.fetch(),
    assetResource.fetch(),
  ])
  technicians.value = techRes || []
  witnesses.value = witRes || []
  rooms.value = roomRes || []
  locations.value = locRes || []
  assets.value = assetRes || []
}

async function fetchWorkOrderData() {
  if (!form.value.facility_work_order?.trim()) {
    showToast('Enter a Work Order ID first', 'warning')
    return
  }
  loadingWO.value = true
  try {
    const response = await fetch('/api/method/rhohotel.rhocom_hotel.api.machine_access_log.get_work_order_prefill', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token || document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      },
      body: JSON.stringify({ work_order_name: form.value.facility_work_order.trim() })
    })
    const data = await response.json()
    if (!response.ok) {
      showToast(parseFrappeError(data), 'error')
      prefilled.value = false
      return
    }
    const res = data.message
    if (res && res.success) {
      form.value.asset = res.asset
      form.value.machine_name = res.machine_name
      form.value.location_type = res.location_type || 'Room'
      form.value.room = res.room || ''
      form.value.asset_location = res.asset_location || ''
      form.value.location_description = res.location_description || ''
      prefilled.value = true
    } else {
      showToast(res?.error || 'Work Order not found', 'warning')
      prefilled.value = false
    }
  } catch (e) {
    showToast(e.message || 'Failed to load work order', 'error')
    prefilled.value = false
  } finally {
    loadingWO.value = false
  }
}

function onAssetChange() {
  // When user manually selects asset (non-prefilled mode), derive machine_name from asset_name
  const selected = assets.value.find(a => a.name === form.value.asset)
  form.value.machine_name = selected ? selected.asset_name : ''
}

function validate() {
  if (!form.value.facility_work_order?.trim()) {
    showToast('Facility Work Order is required', 'warning')
    return false
  }
  if (!form.value.asset?.trim()) {
    showToast('Asset is required', 'warning')
    return false
  }
  if (!form.value.date_opened) {
    showToast('Date Opened is required', 'warning')
    return false
  }
  if (!form.value.reason_for_access?.trim()) {
    showToast('Reason for Access is required', 'warning')
    return false
  }
  return true
}

async function createLog() {
  if (!validate()) return
  creating.value = true
  try {
    const response = await fetch('/api/method/rhohotel.rhocom_hotel.api.machine_access_log.create_machine_access_log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token || document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      },
      body: JSON.stringify({ log_data: JSON.stringify(form.value) })
    })
    const data = await response.json()
    if (!response.ok) {
      showToast(parseFrappeError(data))
      return
    }
    const res = data.message
    if (res.success) {
      showToast('Machine Access Log created', 'success')
      setTimeout(() => {
        router.push({ name: 'MachineAccessLogDetail', params: { id: res.name } })
      }, 500)
    } else {
      showToast(res.error || 'Creation failed')
    }
  } catch (e) {
    showToast(e.message || 'Creation failed')
  } finally {
    creating.value = false
  }
}
</script>
