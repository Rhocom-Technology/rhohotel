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
        <h2 class="text-sm font-bold text-gray-900">Task Setup Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Create corrective or preventive work, assign technicians, and prepare the task for execution.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/list')"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button @click="createTask(false)" :disabled="creating"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5">
          <svg v-if="creating === 'draft'" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          {{ creating === 'draft' ? 'Saving...' : 'Save Draft' }}
        </button>
        <button @click="createTask(true)" :disabled="creating"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
          <svg v-if="creating === 'create'" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          {{ creating === 'create' ? 'Creating...' : 'Create Task' }}
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
              <input v-model="form.location" type="text" placeholder="Enter location"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="attempted && !form.location ? 'border-red-300 bg-red-50' : 'border-gray-200'" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Maintenance Request</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">Linked after creation (optional)</div>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue / Task Description</p>
            <textarea v-model="form.task_description" rows="3"
              placeholder="Describe fault, maintenance need, symptoms, or inspection reason..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

        <!-- Assignment -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Technician <span class="text-red-400">*</span></p>
              <select v-model="form.assigned_technician"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.assigned_technician ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">Select technician</option>
                <option v-for="t in technicians" :key="t.name" :value="t.name">
                  {{ t.technician_name }}
                  {{ t.availability !== 'Available' ? `(${t.availability})` : '' }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
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
        </div>

        <!-- Parts Planning -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Parts / Material Planning <span class="text-xs font-normal text-gray-400">(optional)</span></h3>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-1/4">Item</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-14">Qty</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-20">UOM</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Warehouse</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Store Impact</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-24">Cost</th>
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
                      class="w-14 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" />
                  </td>
                  <td class="py-2.5 pr-2">
                    <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                  </td>
                  <td class="py-2.5 pr-2">
                    <input v-model="part.warehouse" type="text" placeholder="Warehouse"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" />
                  </td>
                  <td class="py-2.5 pr-2">
                    <select v-model="part.store_impact" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded">
                      <option value="Reduce Stock">Reduce Stock</option>
                      <option value="No Impact">No Impact</option>
                      <option value="Return to Store">Return to Store</option>
                    </select>
                  </td>
                  <td class="py-2.5 pr-2">
                    <input v-model.number="part.cost" type="number" min="0"
                      class="w-24 px-2 py-1.5 text-xs border border-gray-200 rounded" />
                  </td>
                  <td class="py-2.5">
                    <button @click="partsUsed.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                  </td>
                </tr>
                <tr v-if="partsUsed.length === 0">
                  <td colspan="7" class="py-4 text-center text-xs text-gray-400">No parts added.</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="7" class="pt-3">
                    <button @click="partsUsed.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '', cost: 0, store_impact: 'Reduce Stock' })"
                      class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Row</button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Checklist -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Maintenance Checklist Template</h3>
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
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Preparation Notes</p>
            <textarea v-model="form.completion_notes" rows="4"
              placeholder="Instructions, escalation note, or safety warning for technician..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

        <!-- Live preview -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-3">New Task Preview</h4>
          <div class="space-y-1.5">
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Task Type</span>
              <span class="text-xs font-medium text-blue-800">{{ form.task_type || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Priority</span>
              <span class="text-xs font-semibold"
                :class="{'text-red-600': form.priority === 'High', 'text-yellow-600': form.priority === 'Medium', 'text-blue-800': form.priority === 'Low' || !form.priority}">
                {{ form.priority || '—' }}
              </span>
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
              <span class="text-xs text-blue-500">Status</span>
              <span class="text-xs font-medium text-blue-800">{{ form.status }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Parts</span>
              <span class="text-xs font-medium text-blue-800">{{ partsUsed.filter(p => p.item_code).length }} item(s)</span>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const creating = ref(false) // 'draft' | 'create' | false
const attempted = ref(false)
const technicians = ref([])
const supervisors = ref([])
const stockItems = ref([])
const partsUsed = ref([])

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
  task_type: '',
  priority: 'Medium',
  status: 'Open',
  location: '',
  task_description: '',
  assigned_technician: '',
  supervisor: '',
  start_time: '',
  end_time: '',
  inspection_required: true,
  fault_diagnosed: false,
  test_run_passed: false,
  completion_notes: '',
})

// ─── Computed helpers ─────────────────────────────────────────────────────────
const technicianLabel = computed(() => {
  const t = technicians.value.find(x => x.name === form.value.assigned_technician)
  return t?.technician_name || null
})

const validationErrors = computed(() => {
  if (!attempted.value) return []
  const errors = []
  if (!form.value.task_type) errors.push('Task type is required')
  if (!form.value.priority) errors.push('Priority is required')
  if (!form.value.location) errors.push('Location is required')
  if (!form.value.assigned_technician) errors.push('Assigned technician is required')
  return errors
})

// ─── Part item select: auto-fill UOM ─────────────────────────────────────────
function onPartSelect(part) {
  const item = stockItems.value.find(i => i.name === part.item_code)
  if (item) {
    part.item_name = item.item_name || item.name
    part.uom = item.stock_uom || ''
  }
}

// ─── Resources ────────────────────────────────────────────────────────────────
const techResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_technicians_for_task', auto: false })
const supResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_supervisors_for_task', auto: false })
const itemsResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_items_for_parts', auto: false })
const createResource_ = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.create_maintenance_task', auto: false })

async function loadDropdowns() {
  const [tRes, sRes, iRes] = await Promise.all([
    techResource.fetch(),
    supResource.fetch(),
    itemsResource.fetch(),
  ])
  technicians.value = tRes || []
  supervisors.value = sRes || []
  stockItems.value = iRes || []
}

// ─── Create task ──────────────────────────────────────────────────────────────
async function createTask(navigate = true) {
  attempted.value = true
  if (validationErrors.value.length) {
    validationErrors.value.forEach(e => showToast(e, 'error'))
    return
  }

  creating.value = navigate ? 'create' : 'draft'
  try {
    const res = await createResource_.fetch({
      task_data: form.value,
      parts_used: partsUsed.value.filter(p => p.item_code)
    })
    console.log('[NewMaintenanceTask] create:', res)
    if (res?.success && res?.task_name) {
      showToast('Task created: ' + res.task_name, 'success')
      setTimeout(() => {
        if (navigate) {
          router.replace({ name: 'MaintenanceTask', params: { id: res.task_name } })
        } else {
          router.replace('/maintenance/list')
        }
      }, 600)
    } else {
      const errMsg = res?.error || JSON.stringify(res)
      console.error('[NewMaintenanceTask] failed:', errMsg)
      showToast('Failed to create: ' + errMsg)
    }
  } catch (e) {
    console.error('[NewMaintenanceTask] exception:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    creating.value = false
  }
}

onMounted(loadDropdowns)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>