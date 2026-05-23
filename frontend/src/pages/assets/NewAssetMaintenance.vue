<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">
        <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt')">Assets</span>
        • <span class="cursor-pointer hover:text-blue-600" @click="$router.back()">Asset Maintenance</span>
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
        <h3 class="text-sm font-bold text-gray-900">New Asset Maintenance</h3>
        <p class="text-xs text-gray-400 mt-0.5">Schedule preventive maintenance for an asset. Saved as draft pending approval.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="$router.back()"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
        <button @click="submitForm" :disabled="saving"
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
          <select v-model="form.asset_name"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select an asset...</option>
            <option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name }} ({{ a.name }})</option>
          </select>
          <p v-if="errors.asset_name" class="text-xs text-red-500 mt-1">{{ errors.asset_name }}</p>
          <p v-if="assetsLoaded && assets.length === 0 && !errors.asset_name" class="text-xs text-yellow-600 mt-1">No assets available — all submitted assets already have an active maintenance schedule.</p>
        </div>
      </div>
    </div>

    <!-- Section: Maintenance Tasks (child table) -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Maintenance Tasks <span class="text-red-500">*</span></h4>
      <p v-if="errors.tasks" class="text-xs text-red-500 mb-3">{{ errors.tasks }}</p>

      <div v-for="(task, idx) in form.tasks" :key="idx" class="border border-gray-200 rounded-lg p-4 mb-3">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-gray-700">Task {{ idx + 1 }}</span>
          <button @click="removeTask(idx)" class="text-red-400 hover:text-red-600 text-xs">Remove</button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Task Name <span class="text-red-500">*</span></label>
            <input v-model="task.maintenance_task" type="text" placeholder="e.g. Oil Change"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Maintenance Type</label>
            <select v-model="task.maintenance_type"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Preventive Maintenance">Preventive Maintenance</option>
              <option value="Calibration">Calibration</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select v-model="task.maintenance_status"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Planned">Planned</option>
              <option value="Overdue">Overdue</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Periodicity <span class="text-red-500">*</span></label>
            <select v-model="task.periodicity"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Select...</option>
              <option>Daily</option><option>Weekly</option><option>Monthly</option>
              <option>Quarterly</option><option>Half-yearly</option><option>Yearly</option>
              <option>2 Yearly</option><option>3 Yearly</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="task.description" rows="2" placeholder="Task description..."
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
          </div>
        </div>
      </div>

      <button @click="addTask"
        class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors">
        + Add Task
      </button>
    </div>

    <!-- Section: Hotel Details -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-6">
      <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Hotel Details</h4>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Location Type</label>
          <select v-model="form.rh_location_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="Room">Room</option>
            <option value="Asset Location">Asset Location</option>
          </select>
        </div>
        <div v-if="form.rh_location_type === 'Room'">
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Hotel Room</label>
          <select v-model="form.rh_hotel_room"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select room...</option>
            <option v-for="r in hotelRooms" :key="r.name" :value="r.name">{{ r.room_number }} ({{ r.name }})</option>
          </select>
        </div>
        <div v-if="form.rh_location_type === 'Asset Location'">
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset Location</label>
          <select v-model="form.rh_asset_location"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select location...</option>
            <option v-for="l in locations" :key="l.name" :value="l.name">{{ l.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Reported By <span class="text-red-500">*</span></label>
          <select v-model="form.rh_reported_by"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select employee...</option>
            <option v-for="e in employees" :key="e.name" :value="e.name">{{ e.employee_name }} ({{ e.name }})</option>
          </select>
          <p v-if="errors.rh_reported_by" class="text-xs text-red-500 mt-1">{{ errors.rh_reported_by }}</p>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Priority</label>
          <select v-model="form.rh_priority"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Issue Type</label>
          <select v-model="form.rh_issue_type"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select issue type...</option>
            <option>Plumbing</option><option>Electrical</option><option>HVAC</option>
            <option>Furniture</option><option>Appliance</option><option>Electronics</option>
            <option>Structural</option><option>Other</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1.5">Assigned Technician</label>
          <select v-model="form.rh_assigned_technician"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select technician...</option>
            <option v-for="t in technicians" :key="t.name" :value="t.name">{{ t.technician_name }} ({{ t.name }})</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Info Note -->
    <div class="bg-yellow-50 border border-yellow-200 rounded-xl px-6 py-4">
      <p class="text-xs text-yellow-800">
        <span class="font-semibold">Note:</span> This maintenance schedule will be saved as <span class="font-bold">Pending</span>
        and requires approval from an Admin or Hotel Manager.
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const saving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const assets = ref([])
const assetsLoaded = ref(false)
const employees = ref([])
const technicians = ref([])
const hotelRooms = ref([])
const locations = ref([])

const form = reactive({
  asset_name: '',
  tasks: [newTaskRow()],
  rh_reported_by: '',
  rh_priority: 'Medium',
  rh_issue_type: '',
  rh_assigned_technician: '',
  rh_location_type: 'Room',
  rh_hotel_room: '',
  rh_asset_location: '',
})

const errors = reactive({
  asset_name: '',
  rh_reported_by: '',
  tasks: '',
})

// Derive company from selected asset
const selectedCompany = computed(() => {
  if (!form.asset_name) return ''
  const asset = assets.value.find(a => a.name === form.asset_name)
  return asset?.company || ''
})

function newTaskRow() {
  return {
    maintenance_task: '',
    maintenance_type: 'Preventive Maintenance',
    maintenance_status: 'Planned',
    periodicity: '',
    description: '',
  }
}

function addTask() {
  form.tasks.push(newTaskRow())
}

function removeTask(idx) {
  if (form.tasks.length > 1) {
    form.tasks.splice(idx, 1)
  }
}

// Load dropdowns
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_maintenance.get_assets_for_maintenance', auto: true, onSuccess(d) { assets.value = d; assetsLoaded.value = true } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_employees_for_repair', auto: true, onSuccess(d) { employees.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_technicians_for_repair', auto: true, onSuccess(d) { technicians.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_hotel_rooms_for_repair', auto: true, onSuccess(d) { hotelRooms.value = d } })
createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_locations', auto: true, onSuccess(d) { locations.value = d } })

function validate() {
  errors.asset_name = ''
  errors.rh_reported_by = ''
  errors.tasks = ''
  let valid = true

  if (!form.asset_name) { errors.asset_name = 'Please select an asset.'; valid = false }
  if (!form.rh_reported_by) { errors.rh_reported_by = 'Please select who reported this.'; valid = false }

  const validTasks = form.tasks.filter(t => t.maintenance_task && t.periodicity)
  if (validTasks.length === 0) {
    errors.tasks = 'At least one complete task is required (task name and periodicity).'
    valid = false
  }

  return valid
}

function submitForm() {
  if (!validate()) return

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  const validTasks = form.tasks.filter(t => t.maintenance_task)

  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.create_asset_maintenance',
    params: {
      asset_name: form.asset_name,
      company: selectedCompany.value,
      tasks: JSON.stringify(validTasks),
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
      successMessage.value = `Asset Maintenance ${data.name} created successfully.`
      setTimeout(() => {
        router.push(`/assets-mgmt/maintenance/${data.name}`)
      }, 1000)
    },
    onError(err) {
      saving.value = false
      errorMessage.value = err?.messages?.[0] || err?.message || 'Failed to create asset maintenance.'
    }
  })
  resource.fetch()
}
</script>
