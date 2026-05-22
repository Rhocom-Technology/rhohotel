<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Toast -->
    <transition-group name="toast" tag="div" class="fixed top-4 right-4 z-50 space-y-2" style="min-width:280px;max-width:360px;">
      <div v-for="t in toasts" :key="t.id"
        class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border"
        :class="{
          'bg-white border-green-200 text-green-800': t.type === 'success',
          'bg-white border-red-200 text-red-800':     t.type === 'error',
          'bg-white border-yellow-200 text-yellow-800': t.type === 'warning',
        }">
        <span class="text-base leading-none mt-0.5">{{ t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : '⚠️' }}</span>
        <span class="flex-1 leading-snug">{{ t.message }}</span>
        <button @click="removeToast(t.id)" class="opacity-50 hover:opacity-100 text-xs">✕</button>
      </div>
    </transition-group>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-900">New Facility Work Order</h2>
          <p class="text-xs text-gray-400 mt-0.5">Create a new work order for room, asset, or location maintenance issues.</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/work-order/list')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Cancel
          </button>
          <button @click="createOrder" :disabled="creating"
            class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
            <svg v-if="creating" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            {{ creating ? 'Creating...' : 'Create Work Order' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Body Grid -->
    <div style="display:grid;grid-template-columns:1fr 340px;gap:16px;">

      <!-- Left Column -->
      <div class="space-y-4">

        <!-- Request Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Request Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Requesting Department <span class="text-red-400">*</span></p>
              <select v-model="form.requesting_department"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="">— select department —</option>
                <option v-for="d in departments" :key="d.name" :value="d.name">{{ d.name }}</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person <span class="text-red-400">*</span></p>
              <select v-model="form.contact_person"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="">— select employee —</option>
                <option v-for="e in filteredEmployees" :key="e.name" :value="e.name">
                  {{ e.employee_name }}{{ e.designation ? ` · ${e.designation}` : '' }}
                </option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mt-3">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority <span class="text-red-400">*</span></p>
              <select v-model="form.priority"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="Routine">Routine</option>
                <option value="Urgent">Urgent</option>
                <option value="Emergency">Emergency</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Category</p>
              <select v-model="form.category"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="">— select category —</option>
                <option value="Electrical">Electrical</option>
                <option value="Plumbing">Plumbing</option>
                <option value="HVAC">HVAC</option>
                <option value="Civil">Civil</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Location -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Location</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Location Type <span class="text-red-400">*</span></p>
              <select v-model="form.location_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="Room">Room</option>
                <option value="Asset Location">Asset Location</option>
                <option value="Other Location">Other Location</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">
                {{ form.location_type === 'Room' ? 'Room' : form.location_type === 'Asset Location' ? 'Asset Location' : 'Location Description' }}
                <span class="text-red-400">*</span>
              </p>
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
              <input v-else v-model="form.location_description" type="text"
                placeholder="e.g. Laundry Room, Generator House..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Asset (optional)</p>
              <select v-model="form.asset"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="">Select asset...</option>
                <option v-for="a in assets" :key="a.name" :value="a.name">
                  {{ a.asset_name }} ({{ a.name }})
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Description of Problem -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Description of Problem <span class="text-red-400">*</span></h3>
          <textarea v-model="form.description_of_problem" rows="6"
            placeholder="Describe the issue in detail — what is the problem, where exactly, any observed symptoms, urgency indicators..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
        </div>
      </div>

      <!-- Right Column -->
      <div class="space-y-4">

        <!-- Summary Preview -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-5">
          <h4 class="text-xs font-bold text-blue-700 mb-3">Work Order Preview</h4>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Department</span>
              <span class="text-xs font-medium text-blue-800 text-right max-w-[160px] truncate">{{ form.requesting_department || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Contact</span>
              <span class="text-xs font-medium text-blue-800 text-right max-w-[140px] truncate">{{ contactLabel || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Priority</span>
              <span class="text-xs font-semibold" :class="priorityTextClass(form.priority)">{{ form.priority }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Category</span>
              <span class="text-xs font-medium text-blue-800">{{ form.category || '—' }}</span>
            </div>
            <div class="flex justify-between pt-2 border-t border-blue-200">
              <span class="text-xs text-blue-500">Location Type</span>
              <span class="text-xs font-medium text-blue-800">{{ form.location_type }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Location</span>
              <span class="text-xs font-medium text-blue-800 text-right max-w-[140px] truncate">{{ locationPreview }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Description</span>
              <span class="text-xs font-medium text-blue-800">{{ form.description_of_problem ? '✓ Provided' : '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Instructions -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h4 class="text-xs font-bold text-gray-900 mb-3">Instructions</h4>
          <div class="space-y-2.5">
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">1.</span>
              <p class="text-xs text-gray-600">Fill in the requesting department and contact person.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">2.</span>
              <p class="text-xs text-gray-600">Set the priority level (Emergency for immediate attention).</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">3.</span>
              <p class="text-xs text-gray-600">Select the location type and specify the exact location.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">4.</span>
              <p class="text-xs text-gray-600">Describe the problem clearly with all relevant details.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-xs text-gray-400 mt-0.5">5.</span>
              <p class="text-xs text-gray-600">Click <strong>Create Work Order</strong> to save as Draft.</p>
            </div>
          </div>
        </div>

        <!-- Workflow info -->
        <div class="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <h4 class="text-xs font-bold text-gray-700 mb-2">After Creation</h4>
          <p class="text-xs text-gray-500">
            The work order starts in <span class="font-semibold text-gray-700">Draft</span> state.
            Use "Submit Request" to send it for Requesting Officer Approval, then it moves through
            Facility Supervisor and Department Head before being closed.
          </p>
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
const creating = ref(false)
const employees = ref([])
const departments = ref([])
const rooms = ref([])
const assets = ref([])
const locations = ref([])

// ─── Form ─────────────────────────────────────────────────────────────────────
const form = ref({
  requesting_department: '',
  contact_person: '',
  priority: 'Routine',
  category: '',
  location_type: 'Room',
  room: '',
  asset_location: '',
  location_description: '',
  asset: '',
  description_of_problem: '',
})

// ─── Computed ─────────────────────────────────────────────────────────────────
const filteredEmployees = computed(() => {
  if (!form.value.requesting_department) return employees.value
  return employees.value.filter(e => e.department === form.value.requesting_department)
})

const contactLabel = computed(() => {
  if (!form.value.contact_person) return null
  const emp = employees.value.find(e => e.name === form.value.contact_person)
  return emp?.employee_name || form.value.contact_person
})

const locationPreview = computed(() => {
  if (form.value.location_type === 'Room') return form.value.room || '—'
  if (form.value.location_type === 'Asset Location') return form.value.asset_location || '—'
  return form.value.location_description || '—'
})

// ─── Toast ────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 4500) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

// ─── Resources ────────────────────────────────────────────────────────────────
const createResource2 = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.create_facility_work_order',
  auto: false
})
const employeeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_employees_for_contact',
  auto: false
})
const deptResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_departments_list',
  auto: false
})
const roomResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_rooms_list',
  auto: false
})
const assetResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_assets_list',
  auto: false
})
const locationResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_locations_list',
  auto: false
})

// ─── Load dropdowns ───────────────────────────────────────────────────────────
async function loadDropdowns() {
  const [empRes, deptRes, roomRes, assetRes, locRes] = await Promise.all([
    employeeResource.fetch(),
    deptResource.fetch(),
    roomResource.fetch(),
    assetResource.fetch(),
    locationResource.fetch()
  ])
  employees.value = empRes || []
  departments.value = deptRes || []
  rooms.value = roomRes || []
  assets.value = assetRes || []
  locations.value = locRes || []
}

// ─── Validation ───────────────────────────────────────────────────────────────
function validate() {
  if (!form.value.requesting_department) {
    showToast('Requesting Department is required', 'warning')
    return false
  }
  if (!form.value.contact_person) {
    showToast('Contact Person is required', 'warning')
    return false
  }
  if (!form.value.description_of_problem?.trim()) {
    showToast('Description of Problem is required', 'warning')
    return false
  }
  if (form.value.location_type === 'Room' && !form.value.room) {
    showToast('Please select a Room', 'warning')
    return false
  }
  if (form.value.location_type === 'Asset Location' && !form.value.asset_location) {
    showToast('Please enter an Asset Location', 'warning')
    return false
  }
  if (form.value.location_type === 'Other Location' && !form.value.location_description) {
    showToast('Please enter a Location Description', 'warning')
    return false
  }
  return true
}

// ─── Create ───────────────────────────────────────────────────────────────────
async function createOrder() {
  if (!validate()) return

  creating.value = true
  try {
    const res = await createResource2.fetch({
      order_data: form.value
    })
    if (res?.success) {
      showToast('Work order created successfully', 'success')
      // Navigate to the newly created work order
      setTimeout(() => {
        router.push({ name: 'FacilityWorkOrderDetail', params: { id: res.order_name } })
      }, 800)
    } else {
      showToast('Failed to create: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    creating.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function priorityTextClass(p) {
  return {
    'Emergency': 'text-red-600',
    'Urgent': 'text-yellow-600',
    'Routine': 'text-green-600',
  }[p] || 'text-gray-600'
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(loadDropdowns)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>
