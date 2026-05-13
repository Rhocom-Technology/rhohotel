<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">
        <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt')">Assets</span>
        • <span class="cursor-pointer hover:text-blue-600" @click="$router.back()">Asset Repair</span>
        • New
      </p>
    </div>

    <!-- Alerts (top) -->
    <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-xl px-6 py-4 flex items-start gap-2">
      <svg class="w-4 h-4 text-green-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
      <p class="text-xs text-green-800 font-medium">{{ successMessage }}</p>
    </div>
    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-6 py-4 flex items-start gap-2">
      <svg class="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
      <p class="text-xs text-red-800 font-medium">{{ errorMessage }}</p>
    </div>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">New Asset Repair</h3>
        <p class="text-xs text-gray-400 mt-0.5">Create a new repair request. Saved as draft pending approval.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="$router.back()"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
        <button @click="submitRepair" :disabled="saving"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>

    <!-- Section: Asset -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset <span class="text-red-500">*</span></label>
          <select v-model="form.asset"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select an asset...</option>
            <option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name }} ({{ a.name }})</option>
          </select>
          <p v-if="errors.asset" class="text-xs text-red-500 mt-1">{{ errors.asset }}</p>
        </div>
      </div>
    </div>

    <!-- Section: Repair Details -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Repair Details</h4>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Failure Date <span class="text-red-500">*</span></label>
          <input v-model="form.failure_date" type="datetime-local"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <p v-if="errors.failure_date" class="text-xs text-red-500 mt-1">{{ errors.failure_date }}</p>
        </div>
      </div>
    </div>

    <!-- Section: Accounting Dimensions -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Accounting Dimensions</h4>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Cost Center</label>
          <select v-model="form.cost_center"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select cost center...</option>
            <option v-for="cc in costCenters" :key="cc.name" :value="cc.name">{{ cc.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Project</label>
          <select v-model="form.project"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select project...</option>
            <option v-for="p in projects" :key="p.name" :value="p.name">{{ p.project_name || p.name }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Section: Description -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Description</h4>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Error Description</label>
          <textarea v-model="form.description" rows="4" placeholder="Describe the issue or failure..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Actions Performed</label>
          <textarea v-model="form.actions_performed" rows="4" placeholder="Describe actions taken..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div>
      </div>
    </div>

    <!-- Section: Hotel Details (Custom rh_* fields) -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Hotel Details</h4>
      <div class="grid grid-cols-2 gap-6">

        <!-- Location Type -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Location Type</label>
          <select v-model="form.rh_location_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="Room">Room</option>
            <option value="Asset Location">Asset Location</option>
          </select>
        </div>

        <!-- Hotel Room (when Room) -->
        <div v-if="form.rh_location_type === 'Room'">
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Hotel Room</label>
          <select v-model="form.rh_hotel_room"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select room...</option>
            <option v-for="r in hotelRooms" :key="r.name" :value="r.name">{{ r.room_number }} ({{ r.name }})</option>
          </select>
        </div>

        <!-- Asset Location (when Asset Location) — Link to Location doctype -->
        <div v-if="form.rh_location_type === 'Asset Location'">
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset Location</label>
          <select v-model="form.rh_asset_location"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select location...</option>
            <option v-for="l in locations" :key="l.name" :value="l.name">{{ l.name }}</option>
          </select>
        </div>

        <!-- Reported By -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Reported By <span class="text-red-500">*</span></label>
          <select v-model="form.rh_reported_by"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select employee...</option>
            <option v-for="e in employees" :key="e.name" :value="e.name">{{ e.employee_name }} ({{ e.name }})</option>
          </select>
          <p v-if="errors.rh_reported_by" class="text-xs text-red-500 mt-1">{{ errors.rh_reported_by }}</p>
        </div>

        <!-- Priority -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Priority</label>
          <select v-model="form.rh_priority"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
        </div>

        <!-- Assigned Technician -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Assigned Technician</label>
          <select v-model="form.rh_assigned_technician"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select technician...</option>
            <option v-for="t in technicians" :key="t.name" :value="t.name">{{ t.technician_name }} ({{ t.name }})</option>
          </select>
        </div>

        <!-- Issue Type -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Issue Type</label>
          <select v-model="form.rh_issue_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select issue type...</option>
            <option>Plumbing</option>
            <option>Electrical</option>
            <option>HVAC</option>
            <option>Furniture</option>
            <option>Appliance</option>
            <option>Electronics</option>
            <option>Structural</option>
            <option>Other</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Info Note -->
    <div class="bg-yellow-50 border border-yellow-200 rounded-xl px-6 py-4">
      <p class="text-xs text-yellow-800">
        <span class="font-semibold">Note:</span> This repair request will be saved as <span class="font-bold">Pending</span>
        and requires approval from an Admin or Hotel Manager before it is processed.
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const saving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const assets = ref([])
const employees = ref([])
const technicians = ref([])
const hotelRooms = ref([])
const costCenters = ref([])
const projects = ref([])
const locations = ref([])

const form = reactive({
  asset: '',
  failure_date: '',
  description: '',
  actions_performed: '',
  cost_center: '',
  project: '',
  rh_reported_by: '',
  rh_priority: 'Medium',
  rh_issue_type: '',
  rh_assigned_technician: '',
  rh_location_type: 'Room',
  rh_hotel_room: '',
  rh_asset_location: '',
})

const errors = reactive({
  asset: '',
  failure_date: '',
  rh_reported_by: '',
})

// Derive company from selected asset
const selectedCompany = computed(() => {
  if (!form.asset) return ''
  const asset = assets.value.find(a => a.name === form.asset)
  return asset?.company || ''
})

// Load dropdowns (non-company-dependent)
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_assets_for_repair', auto: true, onSuccess(d) { assets.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_employees_for_repair', auto: true, onSuccess(d) { employees.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_technicians_for_repair', auto: true, onSuccess(d) { technicians.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_hotel_rooms_for_repair', auto: true, onSuccess(d) { hotelRooms.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_locations', auto: true, onSuccess(d) { locations.value = d } })

// Reload company-dependent dropdowns when asset changes
function loadCompanyDropdowns(company) {
  const params = company ? { company } : {}
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_cost_centers', params, auto: true, onSuccess(d) { costCenters.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_projects', params, auto: true, onSuccess(d) { projects.value = d } })
}

// Watch asset selection to reload company-scoped dropdowns
watch(() => form.asset, () => {
  // Clear company-dependent selections when asset changes
  form.cost_center = ''
  form.project = ''
  loadCompanyDropdowns(selectedCompany.value)
})

// Initial load (no company filter)
loadCompanyDropdowns('')

function validate() {
  errors.asset = ''
  errors.failure_date = ''
  errors.rh_reported_by = ''
  let valid = true

  if (!form.asset) { errors.asset = 'Please select an asset.'; valid = false }
  if (!form.failure_date) { errors.failure_date = 'Please provide the failure date.'; valid = false }
  if (!form.rh_reported_by) { errors.rh_reported_by = 'Please select who reported this repair.'; valid = false }

  return valid
}

function submitRepair() {
  if (!validate()) return

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.create_asset_repair',
    params: {
      asset: form.asset,
      failure_date: form.failure_date,
      description: form.description || null,
      actions_performed: form.actions_performed || null,
      cost_center: form.cost_center || null,
      project: form.project || null,
      rh_reported_by: form.rh_reported_by || null,
      rh_priority: form.rh_priority || null,
      rh_issue_type: form.rh_issue_type || null,
      rh_assigned_technician: form.rh_assigned_technician || null,
      rh_location_type: form.rh_location_type || null,
      rh_hotel_room: form.rh_location_type === 'Room' ? (form.rh_hotel_room || null) : null,
      rh_asset_location: form.rh_location_type === 'Asset Location' ? (form.rh_asset_location || null) : null,
    },
    onSuccess(data) {
      saving.value = false
      successMessage.value = `Asset Repair ${data.name} created successfully.`
      setTimeout(() => {
        router.push(`/assets-mgmt/repair/${data.name}`)
      }, 1000)
    },
    onError(err) {
      saving.value = false
      errorMessage.value = err?.messages?.[0] || err?.message || 'Failed to create asset repair.'
    }
  })
  resource.fetch()
}
</script>
