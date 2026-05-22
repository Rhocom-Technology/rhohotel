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

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center h-64 gap-3">
      <svg class="animate-spin w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
      </svg>
      <p class="text-sm text-gray-400">Loading work order...</p>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="flex flex-col items-center justify-center h-64 gap-3">
      <p class="text-sm font-medium text-gray-700">Failed to load work order</p>
      <p class="text-xs text-gray-400">{{ loadError }}</p>
      <button @click="loadOrder" class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg">Retry</button>
    </div>

    <template v-else-if="order">

      <!-- Header with Actions -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div>
              <h2 class="text-sm font-bold text-gray-900">Work Order: <span class="font-mono">{{ order.name }}</span></h2>
              <p class="text-xs text-gray-400 mt-0.5">Facility Work Order Detail & Workflow Management</p>
            </div>
            <!-- Status badge -->
            <span class="px-3 py-1 text-xs font-semibold rounded-full" :class="statusClass(order.workflow_state)">
              {{ order.workflow_state }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button @click="router.push('/work-order/list')"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
              Back to List
            </button>

            <!-- Edit button (only if editable) -->
            <button v-if="canEdit" @click="enterEditMode"
              class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50"
              :class="{ 'bg-blue-50': editMode }">
              {{ editMode ? 'Editing...' : 'Edit' }}
            </button>

            <!-- Save button (only in edit mode) -->
            <button v-if="editMode" @click="saveOrder" :disabled="saving"
              class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
              <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ saving ? 'Saving...' : 'Save' }}
            </button>

            <!-- Workflow action buttons -->
            <button v-for="action in order.workflow_actions" :key="action.action"
              @click="applyAction(action.action)"
              :disabled="actionLoading"
              class="px-4 py-2 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
              :class="actionBtnClass(action.action)">
              {{ action.action }}
            </button>

            <!-- Cancel button -->
            <button v-if="canCancel" @click="cancelOrder"
              class="px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
              Cancel Order
            </button>
          </div>
        </div>
      </div>

      <!-- Linked Documents Row -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-xs font-bold text-gray-900">Linked Documents</h3>
          <router-link :to="{ name: 'NewMachineAccessLog', query: { work_order: orderId } }"
            class="px-3 py-1.5 text-[10px] font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            + New Machine Access Log
          </router-link>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <button v-for="(count, doctype) in order.linked_docs" :key="doctype"
            @click="openLinkedDoc(doctype)"
            class="px-4 py-2.5 text-xs font-medium border rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
            :class="count > 0 ? 'text-blue-700 border-blue-200 bg-blue-50 hover:bg-blue-100' : 'text-gray-600 border-gray-200'">
            <span>{{ doctype }}</span>
            <span v-if="count > 0" class="px-1.5 py-0.5 text-[10px] font-bold bg-blue-100 text-blue-600 rounded-full">{{ count }}</span>
          </button>
        </div>
      </div>

      <!-- Body Grid -->
      <div style="display:grid;grid-template-columns:1fr 340px;gap:16px;">

        <!-- Left Column -->
        <div class="space-y-4">

          <!-- Request Details -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Request Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Work Order ID</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900 font-mono">
                  {{ order.name }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Requesting Department</p>
                <template v-if="editMode && isFieldEditable('requesting_department')">
                  <select v-model="form.requesting_department"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="">— select —</option>
                    <option v-for="d in departments" :key="d.name" :value="d.name">{{ d.name }}</option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.requesting_department || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Contact Person</p>
                <template v-if="editMode && isFieldEditable('contact_person')">
                  <select v-model="form.contact_person"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="">— select —</option>
                    <option v-for="e in employees" :key="e.name" :value="e.name">{{ e.employee_name }}</option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.contact_person_name || order.contact_person || '—' }}
                </div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mt-3">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Date Reported</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ formatDateTime(order.date_reported) }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Priority</p>
                <template v-if="editMode && isFieldEditable('priority')">
                  <select v-model="form.priority"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="Routine">Routine</option>
                    <option value="Urgent">Urgent</option>
                    <option value="Emergency">Emergency</option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 rounded-lg text-xs font-semibold" :class="priorityDisplayClass(order.priority)">
                  {{ order.priority }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Category</p>
                <template v-if="editMode && isFieldEditable('category')">
                  <select v-model="form.category"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="">— select —</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Plumbing">Plumbing</option>
                    <option value="HVAC">HVAC</option>
                    <option value="Civil">Civil</option>
                    <option value="Other">Other</option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.category || '—' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Location -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Location</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Location Type</p>
                <template v-if="editMode && isFieldEditable('location_type')">
                  <select v-model="form.location_type"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="Room">Room</option>
                    <option value="Asset Location">Asset Location</option>
                    <option value="Other Location">Other Location</option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.location_type || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Location</p>
                <template v-if="editMode && isFieldEditable('room')">
                  <select v-if="form.location_type === 'Room'" v-model="form.room"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="">— select room —</option>
                    <option v-for="r in rooms" :key="r.name" :value="r.name">{{ r.name }}</option>
                  </select>
                  <input v-else-if="form.location_type === 'Other Location'" v-model="form.location_description" type="text"
                    placeholder="Describe location..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                  <input v-else v-model="form.asset_location" type="text"
                    placeholder="Asset location..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.location_display }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Asset</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.asset || '—' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Description of Problem -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Description of Problem</h3>
            <template v-if="editMode && isFieldEditable('description_of_problem')">
              <textarea v-model="form.description_of_problem" rows="4"
                placeholder="Describe the problem..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
            </template>
            <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 min-h-[60px]"
              v-html="order.description_of_problem || '<span class=\'text-gray-400 italic\'>No description</span>'"></div>
          </div>

          <!-- Inspection & Action (Supervisor section) -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Facilities / Maintenance Inspection</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Assigned Technician</p>
                <template v-if="editMode && isFieldEditable('assigned_technician')">
                  <select v-model="form.assigned_technician"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option value="">— select technician —</option>
                    <option v-for="t in technicians" :key="t.name" :value="t.name">
                      {{ t.technician_name }}
                      {{ t.availability !== 'Available' ? `(${t.availability})` : '' }}
                    </option>
                  </select>
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ order.technician_name || order.assigned_technician || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Expected Completion Date</p>
                <template v-if="editMode && isFieldEditable('expected_completion_date')">
                  <input v-model="form.expected_completion_date" type="date"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </template>
                <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ formatDate(order.expected_completion_date) }}
                </div>
              </div>
            </div>
            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Inspection Findings</p>
              <template v-if="editMode && isFieldEditable('inspection_findings')">
                <textarea v-model="form.inspection_findings" rows="3"
                  placeholder="Record inspection findings..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </template>
              <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 min-h-[40px]">
                {{ order.inspection_findings || '—' }}
              </div>
            </div>
            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Estimated Materials Required</p>
              <template v-if="editMode && isFieldEditable('estimated_materials')">
                <textarea v-model="form.estimated_materials" rows="2"
                  placeholder="List materials needed..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </template>
              <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 min-h-[40px]">
                {{ order.estimated_materials || '—' }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Action Taken</p>
              <template v-if="editMode && isFieldEditable('action_taken')">
                <textarea v-model="form.action_taken" rows="3"
                  placeholder="Describe actions taken..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </template>
              <div v-else class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 min-h-[40px]">
                {{ order.action_taken || '—' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Summary & Audit -->
        <div class="space-y-4">

          <!-- Status Summary -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Status Summary</h3>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-500">Current State</span>
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass(order.workflow_state)">
                  {{ order.workflow_state }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Priority</span>
                <span class="text-xs font-semibold" :class="priorityTextClass(order.priority)">{{ order.priority }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Category</span>
                <span class="text-xs font-medium text-gray-700">{{ order.category || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Department</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[160px] truncate">{{ order.requesting_department || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Technician</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[140px] truncate">{{ order.technician_name || 'Unassigned' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Location</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[140px] truncate">{{ order.location_display }}</span>
              </div>
              <div class="flex justify-between pt-2 border-t border-gray-100">
                <span class="text-xs text-gray-500">Expected Completion</span>
                <span class="text-xs font-medium text-gray-700">{{ formatDate(order.expected_completion_date) }}</span>
              </div>
              <div v-if="order.completion_date" class="flex justify-between">
                <span class="text-xs text-gray-500">Actual Completion</span>
                <span class="text-xs font-medium text-green-600">{{ formatDateTime(order.completion_date) }}</span>
              </div>
            </div>
          </div>

          <!-- Audit Trail -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Audit Trail</h3>
            <div class="space-y-3">
              <div v-if="order.submitted_by">
                <p class="text-xs text-gray-500">Submitted By</p>
                <p class="text-xs font-medium text-gray-700 mt-0.5">{{ order.submitted_by }}</p>
                <p class="text-[10px] text-gray-400">{{ formatDateTime(order.submitted_on) }}</p>
              </div>
              <div v-if="order.closed_by">
                <p class="text-xs text-gray-500">Closed By</p>
                <p class="text-xs font-medium text-gray-700 mt-0.5">{{ order.closed_by }}</p>
                <p class="text-[10px] text-gray-400">{{ formatDateTime(order.closed_on) }}</p>
              </div>
              <div v-if="!order.submitted_by && !order.closed_by" class="text-xs text-gray-400 italic">
                No audit entries yet
              </div>
            </div>
          </div>

          <!-- Workflow Info -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
            <h4 class="text-xs font-bold text-blue-700 mb-3">Workflow Actions</h4>
            <div v-if="order.workflow_actions.length" class="space-y-2">
              <div v-for="action in order.workflow_actions" :key="action.action"
                class="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-blue-100">
                <span class="text-xs font-medium text-blue-700">{{ action.action }}</span>
                <span class="text-[10px] text-blue-400">→ {{ action.next_state }}</span>
              </div>
            </div>
            <p v-else class="text-xs text-blue-500 italic">No actions available for your role in this state.</p>
          </div>

          <!-- Edit Mode Indicator -->
          <div v-if="editMode" class="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
            <h4 class="text-xs font-bold text-yellow-700 mb-1">Edit Mode Active</h4>
            <p class="text-xs text-yellow-600">
              You can edit fields allowed in the current workflow state.
              Click Save to persist changes.
            </p>
          </div>

          <!-- Read-only state message -->
          <div v-if="order.workflow_state === 'Closed'" class="bg-green-50 rounded-xl border border-green-100 p-4">
            <div class="flex items-center gap-2">
              <span class="text-green-500">✅</span>
              <p class="text-xs text-green-700 font-medium">This work order is closed.</p>
            </div>
          </div>
          <div v-else-if="order.workflow_state === 'Cancelled'" class="bg-red-50 rounded-xl border border-red-100 p-4">
            <div class="flex items-center gap-2">
              <span class="text-red-400">🚫</span>
              <p class="text-xs text-red-600 font-medium">This work order has been cancelled.</p>
            </div>
          </div>
          <div v-else-if="order.workflow_state === 'Rejected'" class="bg-red-50 rounded-xl border border-red-100 p-4">
            <div class="flex items-center gap-2">
              <span class="text-red-400">❌</span>
              <p class="text-xs text-red-600 font-medium">This work order was rejected.</p>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const route = useRoute()
const orderId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const actionLoading = ref(false)
const editMode = ref(false)
const order = ref(null)
const technicians = ref([])
const employees = ref([])
const departments = ref([])
const rooms = ref([])

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
  inspection_findings: '',
  assigned_technician: '',
  estimated_materials: '',
  expected_completion_date: '',
  action_taken: '',
})

// ─── Editable fields per state ────────────────────────────────────────────────
const editableFieldsMap = {
  'Draft': [
    'requesting_department', 'contact_person', 'priority', 'category',
    'location_type', 'room', 'asset_location', 'location_description',
    'asset', 'description_of_problem'
  ],
  'Pending Requesting Officer Approval': [
    'requesting_department', 'contact_person', 'priority', 'category',
    'location_type', 'room', 'asset_location', 'location_description',
    'asset', 'description_of_problem'
  ],
  'Pending Facility Supervisor Approval': [
    'inspection_findings', 'assigned_technician', 'estimated_materials',
    'expected_completion_date', 'action_taken'
  ],
  'Pending Department Head Signature': [],
  'Closed': [],
  'Rejected': [],
  'Cancelled': [],
}

// Roles allowed to edit in each state (null = All, any user can edit)
const stateRoleMap = {
  'Draft': null,
  'Pending Requesting Officer Approval': null,
  'Pending Facility Supervisor Approval': ['Facilities Supervisor', 'System Manager', 'Administrator'],
  'Pending Department Head Signature': ['Department Head', 'System Manager', 'Administrator'],
}

const canEdit = computed(() => {
  if (!order.value) return false
  const state = order.value.workflow_state
  const allowedFields = editableFieldsMap[state] || []
  if (allowedFields.length === 0) return false
  // Check if user has a role that permits editing in this state
  const requiredRoles = stateRoleMap[state]
  if (requiredRoles === null || requiredRoles === undefined) return true  // All can edit
  const userRoles = order.value.user_roles || []
  return requiredRoles.some(role => userRoles.includes(role))
})

const canCancel = computed(() => {
  if (!order.value) return false
  const state = order.value.workflow_state
  return !['Closed', 'Cancelled', 'Rejected'].includes(state)
})

function isFieldEditable(field) {
  if (!order.value) return false
  const state = order.value.workflow_state
  const allowedFields = editableFieldsMap[state] || []
  return allowedFields.includes(field)
}

function enterEditMode() {
  editMode.value = !editMode.value
}

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
const orderResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_facility_work_order',
  auto: false
})
const saveResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.save_facility_work_order',
  auto: false
})
const actionResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.apply_workflow_action',
  auto: false
})
const cancelResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.cancel_facility_work_order',
  auto: false
})
const techResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.facility_work_order_list.get_technicians_for_assignment',
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

// ─── Load order ───────────────────────────────────────────────────────────────
async function loadOrder() {
  loading.value = true
  loadError.value = null
  try {
    const res = await orderResource.fetch({ order_name: orderId })
    order.value = res

    // Populate form
    form.value = {
      requesting_department: res.requesting_department || '',
      contact_person: res.contact_person || '',
      priority: res.priority || 'Routine',
      category: res.category || '',
      location_type: res.location_type || 'Room',
      room: res.room || '',
      asset_location: res.asset_location || '',
      location_description: res.location_description || '',
      asset: res.asset || '',
      description_of_problem: res.description_of_problem || '',
      inspection_findings: res.inspection_findings || '',
      assigned_technician: res.assigned_technician || '',
      estimated_materials: res.estimated_materials || '',
      expected_completion_date: res.expected_completion_date ? res.expected_completion_date.slice(0, 10) : '',
      action_taken: res.action_taken || '',
    }
    editMode.value = false
  } catch (e) {
    loadError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

// ─── Load dropdowns ───────────────────────────────────────────────────────────
async function loadDropdowns() {
  const [techRes, empRes, deptRes, roomRes] = await Promise.all([
    techResource.fetch(),
    employeeResource.fetch(),
    deptResource.fetch(),
    roomResource.fetch()
  ])
  technicians.value = techRes || []
  employees.value = empRes || []
  departments.value = deptRes || []
  rooms.value = roomRes || []
}

// ─── Save order ───────────────────────────────────────────────────────────────
async function saveOrder() {
  saving.value = true
  try {
    const res = await saveResource.fetch({
      order_name: orderId,
      order_data: form.value
    })
    if (res?.success) {
      showToast('Work order saved', 'success')
      await loadOrder()
    } else {
      showToast('Failed to save: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    saving.value = false
  }
}

// ─── Workflow action ──────────────────────────────────────────────────────────
async function applyAction(action) {
  if (!confirm(`Apply action "${action}" to this work order?`)) return
  actionLoading.value = true
  try {
    const res = await actionResource.fetch({
      order_name: orderId,
      action: action
    })
    if (res?.success) {
      showToast(`Action "${action}" applied. New state: ${res.new_state}`, 'success')
      await loadOrder()
    } else {
      showToast('Action failed: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    actionLoading.value = false
  }
}

// ─── Cancel order ─────────────────────────────────────────────────────────────
async function cancelOrder() {
  if (!confirm('Are you sure you want to cancel this work order?')) return
  try {
    const res = await cancelResource.fetch({ order_name: orderId })
    if (res?.success) {
      showToast('Work order cancelled', 'warning')
      await loadOrder()
    } else {
      showToast('Failed to cancel: ' + (res?.error || ''))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  }
}

// ─── Open linked doc ──────────────────────────────────────────────────────────
function openLinkedDoc(doctype) {
  if (doctype === 'Machine Access Log') {
    router.push({ name: 'MachineAccessLogDashboard', query: { work_order: orderId } })
  } else {
    // Other linked docs: open Frappe list view
    const dt = doctype.replace(/ /g, '-').toLowerCase()
    window.open(`/app/${dt}?facility_work_order=${orderId}`, '_blank')
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function statusClass(s) {
  return {
    'Draft': 'bg-gray-100 text-gray-600',
    'Pending Requesting Officer Approval': 'bg-blue-50 text-blue-600',
    'Pending Facility Supervisor Approval': 'bg-yellow-50 text-yellow-700',
    'Pending Department Head Signature': 'bg-purple-50 text-purple-600',
    'Closed': 'bg-green-50 text-green-600',
    'Rejected': 'bg-red-50 text-red-500',
    'Cancelled': 'bg-red-50 text-red-400',
  }[s] || 'bg-gray-100 text-gray-500'
}

function priorityDisplayClass(p) {
  return {
    'Emergency': 'bg-red-50 border border-red-200 text-red-600',
    'Urgent': 'bg-yellow-50 border border-yellow-200 text-yellow-700',
    'Routine': 'bg-green-50 border border-green-200 text-green-600',
  }[p] || 'bg-gray-50 border border-gray-200 text-gray-600'
}

function priorityTextClass(p) {
  return {
    'Emergency': 'text-red-600',
    'Urgent': 'text-yellow-600',
    'Routine': 'text-green-600',
  }[p] || 'text-gray-600'
}

function actionBtnClass(action) {
  if (action.includes('Reject') || action === 'Cancel') {
    return 'text-red-600 border border-red-300 hover:bg-red-50'
  }
  if (action.includes('Approve') || action === 'Sign and Close') {
    return 'text-white bg-green-500 hover:bg-green-600'
  }
  return 'text-blue-600 border border-blue-300 hover:bg-blue-50'
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(() => {
  loadOrder()
  loadDropdowns()
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>
