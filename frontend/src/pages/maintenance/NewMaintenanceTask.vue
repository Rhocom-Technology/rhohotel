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
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Maintenance Task</h2>
        <p class="text-xs text-gray-400 mt-0.5">Create a standalone corrective, preventive, or routine task and assign it to a technician.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/list')"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button @click="createTask" :disabled="!!creating"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
          <svg v-if="creating" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          {{ creating ? 'Creating...' : 'Create Task' }}
        </button>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

      <!-- Left -->
      <div class="space-y-4">

        <!-- Task Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Task Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">
                Auto-generated on save
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type <span class="text-red-400">*</span></p>
              <select v-model="form.task_type"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.task_type ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select task type</option>
                <option value="Corrective">Corrective</option>
                <option value="Preventive">Preventive</option>
                <option value="Routine">Routine</option>
                <option value="Inspection">Inspection</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority <span class="text-red-400">*</span></p>
              <select v-model="form.priority"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.priority ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select priority</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Location & Description -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Location & Description</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Location <span class="text-red-400">*</span></p>
              <input v-model="form.location" type="text" placeholder="e.g. Room 204, Generator Room, Laundry..."
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="attempted && !form.location ? 'border-red-300 bg-red-50' : 'border-gray-200'" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Maintenance Request <span class="text-gray-400">(optional)</span></p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">
                Auto-linked if created from a request
              </div>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Task Description</p>
            <textarea v-model="form.task_description" rows="3"
              placeholder="Describe fault, maintenance need, symptoms, or inspection reason..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

        <!-- Assignment -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Technician <span class="text-red-400">*</span></p>
              <select v-model="form.assigned_technician"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.assigned_technician ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select technician</option>
                <option v-for="t in technicians" :key="t.name" :value="t.name">
                  {{ t.technician_name }}{{ t.availability !== 'Available' ? ` (${t.availability})` : '' }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor / Witness</p>
              <select v-model="form.supervisor"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">Select supervisor</option>
                <option v-for="s in supervisors" :key="s.name" :value="s.name">
                  {{ s.employee_name }}{{ s.designation ? ` · ${s.designation}` : '' }}
                </option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Planned Start</p>
              <input v-model="form.start_time" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Planned End</p>
              <input v-model="form.end_time" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <!-- Asset -->
          <div class="mt-4">
            <p class="text-xs text-gray-500 mb-1.5">Asset <span class="text-gray-400">(optional)</span></p>
            <select v-model="form.asset"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
              <option value="">— no specific asset —</option>
              <option v-for="a in assets" :key="a.name" :value="a.name">
                {{ a.asset_name || a.name }}{{ a.asset_category ? ` · ${a.asset_category}` : '' }}
              </option>
            </select>
            <p class="text-xs text-gray-400 mt-1">Link to a specific ERPNext asset if this task relates to one.</p>
          </div>
        </div>

        <!-- Parts Used / Collected from Store -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="mb-4">
            <h3 class="text-sm font-bold text-gray-900">Parts Used / Collected from Store</h3>
            <p class="text-xs text-gray-400 mt-0.5">Items to be issued from the store for this task <span class="text-gray-300">(optional)</span></p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Item</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-16">Qty</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-16">UOM</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Warehouse</th>
                   <th class="text-left text-xs font-medium text-gray-500 pb-2 w-24">
                      Available Qty
                    </th>
                  
                  <th class="pb-2 w-6"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="(part, idx) in partsUsed" :key="idx">
                  <td class="py-2.5 pr-2">
                    <select v-model="part.item_code" @change="onPartSelect(part)"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded">
                      <option value="">— select item —</option>
                      <option v-for="item in stockItems" :key="item.name" :value="item.name">
                        {{ item.item_name || item.name }}
                      </option>
                    </select>
                  </td>
                  <td class="py-2.5 pr-2">
                    <input v-model.number="part.qty" type="number" min="0.001"
                      class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" />
                  </td>
                  <td class="py-2.5 pr-2">
                    <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                  </td>
                  <td class="py-2.5 pr-2">
                    <select v-model="part.warehouse"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded">
                      <option value="">— select warehouse —</option>
                      <option v-for="w in warehouses" :key="w.name" :value="w.name">
                        {{ w.warehouse_name || w.name }}
                      </option>
                    </select>
                  </td>
                  <td class="py-2.5 pr-2">
                    <div class="px-2 py-1.5 text-xs text-gray-500">
                      {{ part.available_qty || 0 }}
                    </div>
                  </td>
                  <td class="py-2.5">
                    <button @click="partsUsed.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                  </td>
                </tr>
                <tr v-if="partsUsed.length === 0">
                  <td colspan="6" class="py-4 text-center text-xs text-gray-400">No parts added yet.</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="6" class="pt-3">
                    <button @click="partsUsed.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '', available_qty: 0, stock_entry: '' })"
                      class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Part</button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Parts Returned to Store -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="mb-4">
            <h3 class="text-sm font-bold text-gray-900">Parts Returned to Store</h3>
            <p class="text-xs text-gray-400 mt-0.5">Items to be returned to the warehouse after task completion <span class="text-gray-300">(optional)</span></p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Item</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-16">Qty</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-16">UOM</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Warehouse</th>
                   <th class="text-left text-xs font-medium text-gray-500 pb-2 w-24">
                    Available Qty
                  </th>
                  
                  <th class="pb-2 w-6"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="(part, idx) in partsReturned" :key="idx">
                  <td class="py-2.5 pr-2">
                    <select v-model="part.item_code" @change="onPartSelect(part)"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded">
                      <option value="">— select item —</option>
                      <option v-for="item in stockItems" :key="item.name" :value="item.name">
                        {{ item.item_name || item.name }}
                      </option>
                    </select>
                  </td>
                  <td class="py-2.5 pr-2">
                    <input v-model.number="part.qty" type="number" min="0.001"
                      class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" />
                  </td>
                  <td class="py-2.5 pr-2">
                    <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                  </td>
                  <td class="py-2.5 pr-2">
                    <select v-model="part.warehouse"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded">
                      <option value="">— select warehouse —</option>
                      <option v-for="w in warehouses" :key="w.name" :value="w.name">
                        {{ w.warehouse_name || w.name }}
                      </option>
                    </select>
                  </td>
                  <td class="py-2.5 pr-2">
                  <div class="px-2 py-1.5 text-xs text-gray-500">
                    {{ part.available_qty || 0 }}
                  </div>
                </td>
                  <td class="py-2.5">
                    <button @click="partsReturned.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                  </td>
                </tr>
                <tr v-if="partsReturned.length === 0">
                  <td colspan="6" class="py-4 text-center text-xs text-gray-400">No parts to return yet.</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="6" class="pt-3">
                    <button @click="partsReturned.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '',  available_qty: 0,stock_entry: ''})"
                      class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Returned Part</button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Checklist -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Checklist</h3>
          <div class="flex items-center gap-6 flex-wrap">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.fault_diagnosed" class="w-4 h-4 accent-blue-500" />
              <span class="text-xs text-gray-700">Diagnosis required</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.test_run_passed" class="w-4 h-4 accent-blue-500" />
              <span class="text-xs text-gray-700">Test run on completion</span>
            </label>
          </div>
        </div>

      </div>

      <!-- Right -->
      <div class="space-y-4">

        <!-- Status Setup -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Status Setup</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Initial Task Status</p>
            <select v-model="form.status"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Hold">On Hold</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Inspection Required</p>
            <label class="flex items-center gap-2 cursor-pointer bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
              <input type="checkbox" v-model="form.inspection_required" class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Require supervisor verification on completion</span>
            </label>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Preparation Notes</p>
            <textarea v-model="form.completion_notes" rows="4"
              placeholder="Instructions, escalation note, or safety warning for technician..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

        <!-- Live Preview -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-3">Task Preview</h4>
          <div class="space-y-1.5">
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Task Type</span>
              <span class="text-xs font-medium text-blue-800">{{ form.task_type || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Priority</span>
              <span class="text-xs font-semibold" :class="priorityTextClass(form.priority)">{{ form.priority || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Location</span>
              <span class="text-xs font-medium text-blue-800 truncate max-w-[140px]">{{ form.location || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Technician</span>
              <span class="text-xs font-medium text-blue-800 truncate max-w-[140px]">{{ technicianLabel || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Supervisor</span>
              <span class="text-xs font-medium text-blue-800 truncate max-w-[140px]">{{ supervisorLabel || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Status</span>
              <span class="text-xs font-medium text-blue-800">{{ form.status }}</span>
            </div>
            <div class="flex justify-between pt-1 border-t border-blue-200">
              <span class="text-xs text-blue-500">Parts Used</span>
              <span class="text-xs font-medium text-blue-800">{{ partsUsed.filter(p => p.item_code).length }} item(s)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Parts Returned</span>
              <span class="text-xs font-medium text-blue-800">{{ partsReturned.filter(p => p.item_code).length }} item(s)</span>
            </div>
            <div v-if="form.asset" class="flex justify-between">
              <span class="text-xs text-blue-500">Asset</span>
              <span class="text-xs font-medium text-blue-800 truncate max-w-[140px]">{{ form.asset }}</span>
            </div>
          </div>
        </div>

        <!-- Validation errors -->
        <div v-if="attempted && validationErrors.length" class="bg-red-50 rounded-xl border border-red-200 p-4">
          <p class="text-xs font-semibold text-red-700 mb-2">Please fix the following:</p>
          <ul class="space-y-1">
            <li v-for="e in validationErrors" :key="e" class="text-xs text-red-600 flex gap-1.5">
              <span class="shrink-0">•</span>{{ e }}
            </li>
          </ul>
        </div>

        <!-- Note about workflow -->
        <div class="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <p class="text-xs text-gray-500 font-medium mb-1">ℹ️ Note</p>
          <p class="text-xs text-gray-400">Tasks created here start in <strong>Draft</strong> state. The technician must use the Frappe desk workflow to move through Store Approval → Witness → Hotel Manager before the task can be completed.</p>
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
const attempted = ref(false)
const technicians = ref([])
const supervisors = ref([])
const stockItems = ref([])
const warehouses = ref([])
const assets = ref([])
const partsUsed = ref([])
const partsReturned = ref([])

// ─── Toast ────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 5000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

// ─── Form ─────────────────────────────────────────────────────────────────────
const form = ref({
  task_type:           '',
  priority:            'Medium',
  status:              'Open',
  location:            '',
  task_description:    '',
  assigned_technician: '',
  supervisor:          '',
  start_time:          '',
  end_time:            '',
  inspection_required: true,
  fault_diagnosed:     false,
  test_run_passed:     false,
  completion_notes:    '',
  asset:               '',
})

// ─── Computed ─────────────────────────────────────────────────────────────────
const technicianLabel = computed(() =>
  technicians.value.find(x => x.name === form.value.assigned_technician)?.technician_name || null
)

const supervisorLabel = computed(() =>
  supervisors.value.find(x => x.name === form.value.supervisor)?.employee_name || null
)

const validationErrors = computed(() => {
  if (!attempted.value) return []
  const errors = []
  if (!form.value.task_type)           errors.push('Task type is required')
  if (!form.value.priority)            errors.push('Priority is required')
  if (!form.value.location)            errors.push('Location is required')
  if (!form.value.assigned_technician) errors.push('Assigned technician is required')
  return errors
})

// ─── Part select: auto-fill UOM ───────────────────────────────────────────────
function onPartSelect(part) {
  const item = stockItems.value.find(i => i.name === part.item_code)
  if (item) {
    part.item_name = item.item_name || item.name
    part.uom = item.stock_uom || ''
  }
}

// ─── Resources ────────────────────────────────────────────────────────────────
const techResource    = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_technicians_for_task', auto: false })
const supResource     = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_supervisors_for_task', auto: false })
const itemsResource   = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_items_for_parts', auto: false })
const whResource      = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_warehouses_for_parts', auto: false })
const assetRes        = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_assets_for_request', auto: false })
const createResource_ = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.create_maintenance_task', auto: false })

async function loadDropdowns() {
  const [tRes, sRes, iRes, wRes, aRes] = await Promise.all([
    techResource.fetch(),
    supResource.fetch(),
    itemsResource.fetch(),
    whResource.fetch(),
    assetRes.fetch(),
  ])
  technicians.value = tRes || []
  supervisors.value = sRes || []
  stockItems.value  = iRes || []
  warehouses.value  = wRes || []
  assets.value      = aRes || []
}

// ─── Create ───────────────────────────────────────────────────────────────────
async function createTask() {
  attempted.value = true
  if (validationErrors.value.length) {
    validationErrors.value.forEach(e => showToast(e, 'warning'))
    return
  }

  creating.value = true
  try {
    const res = await createResource_.fetch({
      task_data:      form.value,
      parts_used:     partsUsed.value.filter(p => p.item_code),
      parts_returned: partsReturned.value.filter(p => p.item_code),
    })
    if (res?.success && res?.task_name) {
      showToast('Task created: ' + res.task_name, 'success')
      setTimeout(() => router.replace({ name: 'MaintenanceTask', params: { id: res.task_name } }), 600)
    } else {
      showToast('Failed to create: ' + (res?.error || JSON.stringify(res)))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    creating.value = false
  }
}

function priorityTextClass(p) {
  return { Critical: 'text-red-600', High: 'text-orange-500', Medium: 'text-yellow-600', Low: 'text-blue-500' }[p] || 'text-blue-800'
}

onMounted(loadDropdowns)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>