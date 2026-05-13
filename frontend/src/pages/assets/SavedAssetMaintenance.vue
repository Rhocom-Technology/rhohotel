<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">
        <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt')">Assets</span>
        • <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt/maintenance')">Asset Maintenance</span>
        • {{ record?.name || 'Loading...' }}
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

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <p class="text-xs text-gray-400">Loading maintenance details...</p>
    </div>

    <template v-else-if="record">
      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="text-sm font-bold text-gray-900">{{ record.asset_name }}</h3>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass">{{ statusLabel }}</span>
          </div>
          <p class="text-xs text-gray-400 mt-0.5">{{ record.item_name || record.item_code || '' }} &bull; {{ record.company }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="$router.push('/assets-mgmt/maintenance')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Back to List</button>

          <!-- Edit -->
          <template v-if="canEdit && !editing">
            <button @click="startEditing"
              class="px-4 py-2 text-xs font-semibold text-white bg-gray-700 rounded-lg hover:bg-gray-800 transition-colors">Edit</button>
          </template>

          <!-- Save/Cancel editing -->
          <template v-if="editing">
            <button @click="cancelEditing"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel Edit</button>
            <button @click="saveEdit" :disabled="savingEdit"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
              {{ savingEdit ? 'Saving...' : 'Save Changes' }}
            </button>
          </template>

          <!-- Approve/Reject -->
          <template v-if="!editing && record.rh_approved === 'Pending' && record.docstatus === 0">
            <button @click="approveRecord"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">Approve</button>
            <button @click="showRejectModal = true"
              class="px-4 py-2 text-xs font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">Reject</button>
          </template>
        </div>
      </div>

      <!-- ============= VIEW MODE ============= -->
      <template v-if="!editing">

        <div class="grid grid-cols-2 gap-5">
          <!-- Asset Info -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Asset Info</h4>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Asset</span>
                <span class="text-xs font-medium text-gray-900">{{ record.asset_name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Category</span>
                <span class="text-xs font-medium text-gray-900">{{ record.asset_category || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Item Code</span>
                <span class="text-xs font-medium text-gray-900">{{ record.item_code || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Company</span>
                <span class="text-xs font-medium text-gray-900">{{ record.company }}</span>
              </div>
            </div>
          </div>

          <!-- Hotel Details -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Hotel Details</h4>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Location Type</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_location_type || '—' }}</span>
              </div>
              <div v-if="record.rh_location_type === 'Room'" class="flex justify-between">
                <span class="text-xs text-gray-500">Hotel Room</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_hotel_room_number || record.rh_hotel_room || '—' }}</span>
              </div>
              <div v-if="record.rh_location_type === 'Asset Location'" class="flex justify-between">
                <span class="text-xs text-gray-500">Asset Location</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_asset_location || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Reported By</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_reported_by_name || record.rh_reported_by || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Priority</span>
                <span class="text-xs font-medium" :class="priorityClass(record.rh_priority)">{{ record.rh_priority || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Issue Type</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_issue_type || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Assigned Technician</span>
                <span class="text-xs font-medium text-gray-900">{{ record.rh_technician_name || record.rh_assigned_technician || '—' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Approval Details -->
        <div v-if="record.rh_approved !== 'Pending'" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Approval Details</h4>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <span class="text-xs text-gray-500">Status</span>
              <p class="text-xs font-semibold mt-1" :class="record.rh_approved === 'Approved' ? 'text-green-600' : 'text-red-500'">{{ record.rh_approved }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Approved By</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ record.rh_approved_by_name || record.rh_approved_by || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Approved On</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(record.rh_approved_on) || '—' }}</p>
            </div>
          </div>
        </div>

        <!-- Tasks Table -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Maintenance Tasks</h4>
          </div>
          <table v-if="record.asset_maintenance_tasks && record.asset_maintenance_tasks.length" class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-6 py-3">Task</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Type</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Periodicity</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Next Due</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Last Completed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(task, idx) in record.asset_maintenance_tasks" :key="idx" class="border-b border-gray-50">
                <td class="px-6 py-3 text-xs font-semibold text-gray-900">{{ task.maintenance_task }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ task.maintenance_type || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded-full" :class="taskStatusClass(task.maintenance_status)">{{ task.maintenance_status }}</span>
                </td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ task.periodicity || '—' }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ task.next_due_date || '—' }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ task.last_completion_date || '—' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="px-6 py-4 text-xs text-gray-400">No tasks defined.</div>
        </div>

        <!-- Meta -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="grid grid-cols-3 gap-4">
            <div>
              <span class="text-xs text-gray-500">Created By</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ record.created_by }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Created On</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(record.creation) }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Last Modified</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(record.modified) }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- ============= EDIT MODE ============= -->
      <template v-if="editing">

        <!-- Asset & Company (read-only) -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Asset & Company</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Company</label>
              <input :value="record.company" type="text" readonly
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-500" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset</label>
              <input :value="editForm.asset_name" type="text" readonly
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-gray-500" />
              <p class="text-xs text-gray-400 mt-1">Asset cannot be changed (unique key).</p>
            </div>
          </div>
        </div>

        <!-- Hotel Details -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Hotel Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Location Type</label>
              <select v-model="editForm.rh_location_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Room">Room</option>
                <option value="Asset Location">Asset Location</option>
              </select>
            </div>
            <div v-if="editForm.rh_location_type === 'Room'">
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Hotel Room</label>
              <select v-model="editForm.rh_hotel_room"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select room...</option>
                <option v-for="r in hotelRoomsList" :key="r.name" :value="r.name">{{ r.room_number }} ({{ r.name }})</option>
              </select>
            </div>
            <div v-if="editForm.rh_location_type === 'Asset Location'">
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset Location</label>
              <select v-model="editForm.rh_asset_location"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select location...</option>
                <option v-for="l in locationsList" :key="l.name" :value="l.name">{{ l.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Reported By</label>
              <select v-model="editForm.rh_reported_by"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select employee...</option>
                <option v-for="e in employeesList" :key="e.name" :value="e.name">{{ e.employee_name }} ({{ e.name }})</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Priority</label>
              <select v-model="editForm.rh_priority"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Issue Type</label>
              <select v-model="editForm.rh_issue_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select issue type...</option>
                <option>Plumbing</option><option>Electrical</option><option>HVAC</option>
                <option>Furniture</option><option>Appliance</option><option>Electronics</option>
                <option>Structural</option><option>Other</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Assigned Technician</label>
              <select v-model="editForm.rh_assigned_technician"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select technician...</option>
                <option v-for="t in techniciansList" :key="t.name" :value="t.name">{{ t.technician_name }} ({{ t.name }})</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Tasks -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Maintenance Tasks</h4>

          <div v-for="(task, idx) in editForm.tasks" :key="idx" class="border border-gray-200 rounded-lg p-4 mb-3">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-semibold text-gray-700">Task {{ idx + 1 }}</span>
              <button @click="editRemoveTask(idx)" class="text-red-400 hover:text-red-600 text-xs">Remove</button>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Task Name <span class="text-red-500">*</span></label>
                <input v-model="task.maintenance_task" type="text"
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
                <textarea v-model="task.description" rows="2"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
              </div>
            </div>
          </div>

          <button @click="editAddTask"
            class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors">
            + Add Task
          </button>
        </div>
      </template>
    </template>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showRejectModal = false">
      <div class="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h4 class="text-sm font-bold text-gray-900 mb-3">Reject Asset Maintenance</h4>
        <p class="text-xs text-gray-500 mb-4">Provide a reason for rejecting this maintenance schedule.</p>
        <textarea v-model="rejectReason" rows="3" placeholder="Reason for rejection..."
          class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"></textarea>
        <div class="flex justify-end gap-2">
          <button @click="showRejectModal = false"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="rejectRecord"
            class="px-4 py-2 text-xs font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700">Confirm Reject</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const record = ref(null)
const editing = ref(false)
const savingEdit = ref(false)
const showRejectModal = ref(false)
const rejectReason = ref('')
const successMessage = ref('')
const errorMessage = ref('')

// Dropdown data for edit mode
const employeesList = ref([])
const techniciansList = ref([])
const hotelRoomsList = ref([])
const locationsList = ref([])

const editForm = reactive({
  asset_name: '',
  tasks: [],
  rh_reported_by: '',
  rh_priority: 'Medium',
  rh_issue_type: '',
  rh_assigned_technician: '',
  rh_location_type: 'Room',
  rh_hotel_room: '',
  rh_asset_location: '',
})

const canEdit = computed(() => {
  if (!record.value) return false
  return record.value.docstatus === 0 && record.value.rh_approved !== 'Rejected'
})

const statusLabel = computed(() => {
  if (!record.value) return ''
  const r = record.value
  if (r.rh_approved === 'Rejected') return 'Rejected'
  if (r.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
})

const statusClass = computed(() => {
  return {
    'Pending':  'bg-yellow-50 text-yellow-600',
    'Approved': 'bg-green-50 text-green-600',
    'Rejected': 'bg-red-50 text-red-500',
  }[statusLabel.value] || 'bg-gray-100 text-gray-500'
})

function priorityClass(p) {
  return {
    'High':   'text-orange-600 font-semibold',
    'Medium': 'text-yellow-600',
    'Low':    'text-gray-600',
  }[p] || 'text-gray-900'
}

function taskStatusClass(status) {
  return {
    'Planned':   'bg-blue-50 text-blue-600',
    'Overdue':   'bg-red-50 text-red-600',
    'Cancelled': 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

function newEditTaskRow() {
  return {
    maintenance_task: '',
    maintenance_type: 'Preventive Maintenance',
    maintenance_status: 'Planned',
    periodicity: '',
    description: '',
  }
}

function editAddTask() {
  editForm.tasks.push(newEditTaskRow())
}

function editRemoveTask(idx) {
  if (editForm.tasks.length > 1) {
    editForm.tasks.splice(idx, 1)
  }
}

function startEditing() {
  const r = record.value
  editForm.asset_name = r.asset_name || ''
  editForm.rh_reported_by = r.rh_reported_by || ''
  editForm.rh_priority = r.rh_priority || 'Medium'
  editForm.rh_issue_type = r.rh_issue_type || ''
  editForm.rh_assigned_technician = r.rh_assigned_technician || ''
  editForm.rh_location_type = r.rh_location_type || 'Room'
  editForm.rh_hotel_room = r.rh_hotel_room || ''
  editForm.rh_asset_location = r.rh_asset_location || ''

  editForm.tasks = (r.asset_maintenance_tasks || []).map(t => ({
    maintenance_task: t.maintenance_task || '',
    maintenance_type: t.maintenance_type || 'Preventive Maintenance',
    maintenance_status: t.maintenance_status || 'Planned',
    periodicity: t.periodicity || '',
    description: t.description || '',
  }))

  if (editForm.tasks.length === 0) {
    editForm.tasks.push(newEditTaskRow())
  }

  loadDropdowns()
  editing.value = true
}

function cancelEditing() {
  editing.value = false
}

function loadDropdowns() {
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_employees_for_repair', auto: true, onSuccess(d) { employeesList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_technicians_for_repair', auto: true, onSuccess(d) { techniciansList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_hotel_rooms_for_repair', auto: true, onSuccess(d) { hotelRoomsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_locations', auto: true, onSuccess(d) { locationsList.value = d } })
}

function saveEdit() {
  savingEdit.value = true
  successMessage.value = ''
  errorMessage.value = ''

  const validTasks = editForm.tasks.filter(t => t.maintenance_task)

  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.update_asset_maintenance',
    params: {
      name: record.value.name,
      tasks: JSON.stringify(validTasks),
      rh_reported_by: editForm.rh_reported_by || null,
      rh_priority: editForm.rh_priority || null,
      rh_issue_type: editForm.rh_issue_type || null,
      rh_assigned_technician: editForm.rh_assigned_technician || null,
      rh_location_type: editForm.rh_location_type || null,
      rh_hotel_room: editForm.rh_location_type === 'Room' ? (editForm.rh_hotel_room || null) : null,
      rh_asset_location: editForm.rh_location_type === 'Asset Location' ? (editForm.rh_asset_location || null) : null,
    },
    onSuccess(data) {
      savingEdit.value = false
      editing.value = false
      successMessage.value = data.message
      fetchRecord()
    },
    onError(err) {
      savingEdit.value = false
      errorMessage.value = err?.messages?.[0] || err?.message || 'Failed to update.'
    }
  })
  resource.fetch()
}

function fetchRecord() {
  loading.value = true
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.get_asset_maintenance',
    params: { name: route.params.id },
    onSuccess(data) {
      record.value = data
      loading.value = false
    },
    onError(err) {
      loading.value = false
      errorMessage.value = err?.messages?.[0] || 'Failed to load details.'
    }
  })
  resource.fetch()
}

function approveRecord() {
  successMessage.value = ''
  errorMessage.value = ''
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.approve_asset_maintenance',
    params: { name: record.value.name },
    onSuccess(data) {
      successMessage.value = data.message
      fetchRecord()
    },
    onError(err) {
      errorMessage.value = err?.messages?.[0] || err?.message || 'Failed to approve.'
    }
  })
  resource.fetch()
}

function rejectRecord() {
  successMessage.value = ''
  errorMessage.value = ''
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_maintenance.reject_asset_maintenance',
    params: { name: record.value.name, reason: rejectReason.value },
    onSuccess(data) {
      successMessage.value = data.message
      showRejectModal.value = false
      rejectReason.value = ''
      fetchRecord()
    },
    onError(err) {
      errorMessage.value = err?.messages?.[0] || err?.message || 'Failed to reject.'
    }
  })
  resource.fetch()
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => {
  fetchRecord()
})
</script>
