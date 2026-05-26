<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Toast -->
    <transition-group name="toast" tag="div" class="fixed top-4 right-4 z-50 space-y-2" style="min-width:280px;max-width:360px;">
      <div v-for="t in toasts" :key="t.id"
        class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border"
        :class="{
          'bg-white border-green-200 text-green-800': t.type === 'success',
          'bg-white border-red-200 text-red-800': t.type === 'error',
          'bg-white border-yellow-200 text-yellow-800': t.type === 'warning',
        }">
        <span class="text-base leading-none mt-0.5">{{ t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : '⚠️' }}</span>
        <span class="flex-1 leading-snug">{{ t.message }}</span>
        <button @click="removeToast(t.id)" class="opacity-50 hover:opacity-100 text-xs">✕</button>
      </div>
    </transition-group>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Maintenance Request</h2>
        <p class="text-xs text-gray-400 mt-0.5">Capture request source, location, urgency, and issue details for quick response.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/request')"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button @click="submitRequest" :disabled="submitting"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
          <svg v-if="submitting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          {{ submitting ? 'Submitting...' : 'Submit Request' }}
        </button>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">
      <div class="space-y-4">

        <!-- Request Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Request Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Request ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">Auto-generated</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Issue Type <span class="text-red-400">*</span></p>
              <select v-model="form.issue_type"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.issue_type ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select issue type</option>
                <option value="Plumbing">Plumbing</option>
                <option value="Electrical">Electrical</option>
                <option value="HVAC">HVAC</option>
                <option value="Furniture">Furniture</option>
                <option value="Appliance">Appliance</option>
                <option value="Electronics">Electronics</option>
                <option value="Structural">Structural</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority <span class="text-red-400">*</span></p>
              <select v-model="form.priority"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.priority ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select priority</option>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Requester Information -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Requester Information</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reported By <span class="text-red-400">*</span></p>
              <select v-model="form.reported_by"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600"
                :class="attempted && !form.reported_by ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select staff</option>
                <option v-for="e in employees" :key="e.name" :value="e.name">
                  {{ e.employee_name }}{{ e.department ? ` · ${e.department}` : '' }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Reported At <span class="text-red-400">*</span></p>
              <input v-model="form.reported_at" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>
          <div v-if="requestingDepartmentLabel" class="mt-1 px-3 py-2 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2">
            <span class="text-[10px] font-semibold text-blue-500 uppercase tracking-wide">Dept</span>
            <span class="text-xs text-blue-700">{{ requestingDepartmentLabel }}</span>
            <span class="text-xs text-blue-400">— auto-resolved from employee</span>
          </div>
        </div>

        <!-- Supervisor / Witness -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Supervisor / Witness <span class="text-red-400">*</span></h3>
          <p class="text-xs text-gray-400 mb-4">The person who will verify the completed work before the Hotel Manager approves.</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor / Witness <span class="text-red-400">*</span></p>
              <select v-model="form.witness_employee"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600"
                :class="attempted && !form.witness_employee ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select supervisor / witness</option>
                <option v-for="e in employees" :key="e.name" :value="e.name">
                  {{ e.employee_name }}{{ e.department ? ` · ${e.department}` : '' }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Witness Department</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500 italic">
                {{ witnessDepartmentLabel || 'Auto-resolved from witness' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Issue Target / Location -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Issue Target</h3>

          <!-- Location Type toggle -->
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Location Type <span class="text-red-400">*</span></p>
            <div class="flex rounded-lg overflow-hidden border border-gray-200 h-[38px]">
              <button @click="form.location_type = 'Room'"
                class="flex-1 text-xs font-medium transition-colors"
                :class="form.location_type === 'Room' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                🏨 Room
              </button>
              <button @click="form.location_type = 'Asset Location'"
                class="flex-1 text-xs font-medium transition-colors border-l border-gray-200"
                :class="form.location_type === 'Asset Location' ? 'bg-purple-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                🔧 Asset Location
              </button>
              <button @click="form.location_type = 'Other Location'"
                class="flex-1 text-xs font-medium transition-colors border-l border-gray-200"
                :class="form.location_type === 'Other Location' ? 'bg-orange-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                📍 Other
              </button>
            </div>
          </div>

          <div class="mb-4">
            <!-- Room -->
            <div v-if="form.location_type === 'Room'">
              <p class="text-xs text-gray-500 mb-1.5">Room <span class="text-red-400">*</span></p>
              <select v-model="form.room"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && form.location_type === 'Room' && !form.room ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select room</option>
                <option v-for="r in rooms" :key="r.name" :value="r.name">
                  {{ r.room_number || r.name }}
                </option>
              </select>
            </div>

            <!-- Asset Location — dropdown from ERPNext Location -->
            <div v-else-if="form.location_type === 'Asset Location'">
              <p class="text-xs text-gray-500 mb-1.5">Asset Location <span class="text-red-400">*</span></p>
              <select v-model="form.asset_location"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-300 text-gray-700"
                :class="attempted && form.location_type === 'Asset Location' && !form.asset_location ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select asset location</option>
                <option v-for="loc in assetLocations" :key="loc.name" :value="loc.name">
                  {{ loc.location_name || loc.name }}
                </option>
              </select>
              <p class="text-xs text-gray-400 mt-1">Locations are managed in ERPNext → Assets → Location</p>
            </div>

            <!-- Other Location -->
            <div v-else>
              <p class="text-xs text-gray-500 mb-1.5">Location <span class="text-red-400">*</span></p>
              <input v-model="form.location" type="text"
                placeholder="e.g. Laundry, Gym, Kitchen, Pool..."
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="attempted && form.location_type === 'Other Location' && !form.location ? 'border-red-300 bg-red-50' : 'border-gray-200'" />
            </div>
          </div>


          <!-- Asset (optional, all location types) -->
          <div class="mt-4">
            <p class="text-xs text-gray-500 mb-1.5">Asset <span class="text-gray-400">(optional)</span></p>
            <select v-model="form.asset"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
              <option value="">— no specific asset —</option>
              <option v-for="a in assets" :key="a.name" :value="a.name">
                {{ a.asset_name || a.name }}{{ a.asset_category ? ` · ${a.asset_category}` : '' }}
              </option>
            </select>
            <p class="text-xs text-gray-400 mt-1">Link to a specific ERPNext asset if this issue relates to one.</p>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Description</p>
            <textarea v-model="form.issue_description" rows="5"
              placeholder="Describe the fault, when it started, symptoms, guest impact, and any temporary measures taken..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

      </div>

      <!-- Right -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Request Preview</h3>
          <div class="bg-blue-50 rounded-xl border border-blue-100 p-4 mb-4">
            <h4 class="text-xs font-bold text-blue-700 mb-3">New Request</h4>
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Location Type</span>
                <span class="text-xs font-semibold text-blue-700">
                  {{ form.location_type === 'Room' ? '🏨 Room' : form.location_type === 'Asset Location' ? '🔧 Asset' : '📍 Other' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Issue Type</span>
                <span class="text-xs font-medium text-blue-800">{{ form.issue_type || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Priority</span>
                <span class="text-xs font-semibold" :class="priorityTextClass(form.priority)">{{ form.priority || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Location</span>
                <span class="text-xs font-medium text-blue-800 truncate max-w-[130px]">{{ locationLabel || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Reported By</span>
                <span class="text-xs font-medium text-blue-800 truncate max-w-[130px]">{{ reportedByLabel || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Witness</span>
                <span class="text-xs font-medium text-blue-800 truncate max-w-[130px]">{{ witnessLabel || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Asset</span>
                <span class="text-xs font-medium text-blue-800 truncate max-w-[130px]">{{ assetLabel || '—' }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-blue-200">
                <span class="text-xs text-blue-500">Status</span>
                <span class="text-xs font-semibold text-blue-700">Pending</span>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-lg border border-gray-100 p-3">
            <p class="text-xs text-gray-500 font-medium mb-1">What happens next:</p>
            <p class="text-xs text-gray-500">1. Request created as <strong>Pending</strong></p>
            <p class="text-xs text-gray-500 mt-0.5">2. Manager assigns technician &amp; <strong>approves</strong></p>
            <p class="text-xs text-gray-500 mt-0.5">3. <strong>Maintenance Task</strong> auto-created</p>
            <p class="text-xs text-gray-500 mt-0.5">4. Technician completes work</p>
            <p class="text-xs text-gray-500 mt-0.5">5. Witness verifies → Manager approves</p>
          </div>
        </div>

        <!-- Validation errors -->
        <div v-if="attempted && validationErrors.length" class="bg-red-50 rounded-xl border border-red-200 p-4">
          <p class="text-xs font-semibold text-red-700 mb-2">Please fix:</p>
          <ul class="space-y-1">
            <li v-for="e in validationErrors" :key="e" class="text-xs text-red-600 flex gap-1.5">
              <span class="shrink-0">•</span>{{ e }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const submitting = ref(false)
const attempted = ref(false)
const rooms = ref([])
const employees = ref([])
const assetLocations = ref([])
const assets = ref([])

const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 5000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

const now = new Date()
const localNow = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

const form = ref({
  location_type:     'Room',
  room:              '',
  asset_location:    '',
  location:          '',
  issue_type:        '',
  priority:          'Medium',
  reported_by:       '',
  witness_employee:  '',
  reported_at:       localNow,
  issue_description: '',
  asset: '',
})

// ─── Computed labels ──────────────────────────────────────────────────────────
const locationLabel = computed(() => {
  if (form.value.location_type === 'Room')
    return rooms.value.find(x => x.name === form.value.room)?.room_number || null
  if (form.value.location_type === 'Asset Location') {
    const loc = assetLocations.value.find(x => x.name === form.value.asset_location)
    return loc?.location_name || form.value.asset_location || null
  }
  return form.value.location || null
})

const reportedByLabel = computed(() =>
  employees.value.find(x => x.name === form.value.reported_by)?.employee_name || null
)

const witnessLabel = computed(() =>
  employees.value.find(x => x.name === form.value.witness_employee)?.employee_name || null
)

const requestingDepartmentLabel = computed(() =>
  employees.value.find(x => x.name === form.value.reported_by)?.department || null
)

const assetLabel = computed(() =>
  assets.value.find(x => x.name === form.value.asset)?.asset_name || null
)

const witnessDepartmentLabel = computed(() =>
  employees.value.find(x => x.name === form.value.witness_employee)?.department || null
)

const validationErrors = computed(() => {
  if (!attempted.value) return []
  const e = []
  if (!form.value.issue_type)       e.push('Issue type is required')
  if (!form.value.priority)         e.push('Priority is required')
  if (form.value.location_type === 'Room' && !form.value.room)
    e.push('Room is required')
  if (form.value.location_type === 'Asset Location' && !form.value.asset_location)
    e.push('Asset Location is required')
  if (form.value.location_type === 'Other Location' && !form.value.location)
    e.push('Location is required')
  if (!form.value.reported_by)       e.push('Reported by is required')
  if (!form.value.witness_employee)  e.push('Supervisor / Witness is required')
  if (!form.value.reported_at)       e.push('Reported at is required')
  return e
})

const roomsResource          = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_rooms_for_request', auto: false })
const employeesResource      = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_employees_for_request', auto: false })
const assetLocationsResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_asset_locations_for_request', auto: false })
const assetsResource         = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_assets_for_request', auto: false })
const createResource_        = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.create_maintenance_request', auto: false })

async function submitRequest() {
  attempted.value = true
  if (validationErrors.value.length) {
    validationErrors.value.forEach(e => showToast(e, 'warning'))
    return
  }
  submitting.value = true
  try {
    const res = await createResource_.fetch({ request_data: form.value })
    if (res?.success && res?.request_name) {
      const msg = res.already_existed
        ? 'A request already exists: ' + res.request_name
        : 'Request submitted: ' + res.request_name
      showToast(msg, res.already_existed ? 'warning' : 'success')
      setTimeout(() => router.replace({
        name: 'SavedMaintenanceRequest',
        params: { id: res.request_name }
      }), 600)
    } else {
      showToast('Failed: ' + (res?.error || JSON.stringify(res)))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    submitting.value = false
  }
}

function priorityTextClass(p) {
  return { Critical: 'text-red-600', High: 'text-orange-500', Medium: 'text-yellow-600', Low: 'text-blue-500' }[p] || 'text-blue-800'
}

onMounted(async () => {
  const [rRes, eRes, aRes, asRes] = await Promise.all([
    roomsResource.fetch(),
    employeesResource.fetch(),
    assetLocationsResource.fetch(),
    assetsResource.fetch(),
  ])
  rooms.value          = rRes || []
  employees.value      = eRes || []
  assetLocations.value = aRes || []
  assets.value         = asRes || []
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>