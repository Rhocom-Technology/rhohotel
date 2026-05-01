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
      <p class="text-sm text-gray-400">Loading task...</p>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="flex flex-col items-center justify-center h-64 gap-3">
      <p class="text-sm font-medium text-gray-700">Failed to load task</p>
      <p class="text-xs text-gray-400">{{ loadError }}</p>
      <button @click="loadTask" class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg">Retry</button>
    </div>

    <template v-else-if="task">

      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div>
            <h2 class="text-sm font-bold text-gray-900">Task Control</h2>
            <p class="text-xs text-gray-400 mt-0.5">Manage issue reporting, diagnosis, work execution, and technician completion.</p>
          </div>
          <!-- Docstatus badge -->
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
            :class="{
              'bg-yellow-100 text-yellow-700': task.docstatus === 0,
              'bg-green-100 text-green-700':   task.docstatus === 1,
              'bg-red-100 text-red-600':        task.docstatus === 2,
            }">
            <span class="w-1.5 h-1.5 rounded-full"
              :class="{
                'bg-yellow-500': task.docstatus === 0,
                'bg-green-500':  task.docstatus === 1,
                'bg-red-500':    task.docstatus === 2,
              }"></span>
            {{ task.docstatus === 0 ? 'Draft' : task.docstatus === 1 ? 'Submitted' : 'Cancelled' }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/maintenance/list')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Cancel
          </button>

          <!-- Draft actions -->
          <template v-if="task.docstatus === 0">
            <button @click="saveDraft" :disabled="saving"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5">
              <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ saving ? 'Saving...' : 'Save Draft' }}
            </button>
            <button @click="completeTask" :disabled="submitting"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
              <svg v-if="submitting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ submitting ? 'Submitting...' : 'Complete Task' }}
            </button>
          </template>

          <!-- Submitted actions -->
          <template v-else-if="task.docstatus === 1">
            <button @click="cancelTask"
              class="px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
              Cancel Task
            </button>
          </template>
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
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900 font-mono">
                  {{ task.name }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
                <select v-model="form.task_type" :disabled="isReadOnly"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                  :class="{'bg-gray-100': isReadOnly}">
                  <option value="Corrective">Corrective</option>
                  <option value="Preventive">Preventive</option>
                  <option value="Routine">Routine</option>
                  <option value="Inspection">Inspection</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Priority</p>
                <select v-model="form.priority" :disabled="isReadOnly"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                  :class="{'bg-gray-100': isReadOnly}">
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>
            <!-- Linked request -->
            <div v-if="task.maintenance_request" class="mt-3 px-3 py-2.5 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2">
              <span class="text-[10px] font-semibold text-blue-500 uppercase tracking-wide">From Request</span>
              <span class="text-xs text-blue-700 font-medium">{{ task.maintenance_request }}</span>
              <span v-if="task.request_title" class="text-xs text-blue-500">— {{ task.request_title }}</span>
            </div>
          </div>

          <!-- Asset Details -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Asset Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Asset</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 font-mono">
                  {{ task.asset || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Asset Name</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
                  {{ task.asset_name || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Location</p>
                <input v-model="form.location" :disabled="isReadOnly" type="text"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                  :class="{'bg-gray-100': isReadOnly}" />
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Issue / Task Description</p>
              <textarea v-model="form.task_description" :disabled="isReadOnly" rows="3"
                placeholder="Describe fault, incident, or maintenance task details..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                :class="{'bg-gray-100': isReadOnly}"></textarea>
            </div>
          </div>

          <!-- Assignment -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Assigned Technician</p>
                <select v-model="form.assigned_technician" :disabled="isReadOnly"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                  :class="{'bg-gray-100': isReadOnly}">
                  <option value="">— select technician —</option>
                  <option v-for="t in technicians" :key="t.name" :value="t.name">
                    {{ t.technician_name }}
                    {{ t.availability !== 'Available' ? `(${t.availability})` : '' }}
                  </option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
                <select v-model="form.supervisor" :disabled="isReadOnly"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                  :class="{'bg-gray-100': isReadOnly}">
                  <option value="">— select supervisor —</option>
                  <option v-for="s in supervisors" :key="s.name" :value="s.name">
                    {{ s.employee_name }}{{ s.designation ? ` · ${s.designation}` : '' }}
                  </option>
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Start Time</p>
                <input v-model="form.start_time" :disabled="isReadOnly" type="datetime-local"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                  :class="{'bg-gray-100': isReadOnly}" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">End Time</p>
                <input v-model="form.end_time" :disabled="isReadOnly" type="datetime-local"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                  :class="{'bg-gray-100': isReadOnly}" />
              </div>
            </div>
          </div>

          <!-- Parts / Material Usage -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-gray-900">Parts / Material Usage</h3>
              <span v-if="task.parts_approval_status" class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="task.parts_approval_status === 'Approved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                {{ task.parts_approval_status }}
              </span>
            </div>
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
                    <th v-if="!isReadOnly" class="pb-2 w-6"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="(part, idx) in partsUsed" :key="idx">
                    <td class="py-2.5 pr-2">
                      <select v-model="part.item_code" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}"
                        @change="onPartSelect(part)">
                        <option value="">— select item —</option>
                        <option v-for="item in stockItems" :key="item.name" :value="item.name">
                          {{ item.item_name || item.name }}
                        </option>
                      </select>
                    </td>
                    <td class="py-2.5 pr-2">
                      <input v-model.number="part.qty" :disabled="isReadOnly" type="number" min="0.001"
                        class="w-14 px-2 py-1.5 text-xs border border-gray-200 rounded text-center"
                        :class="{'bg-gray-100': isReadOnly}" />
                    </td>
                    <td class="py-2.5 pr-2">
                      <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                    </td>
                    <td class="py-2.5 pr-2">
                      <input v-model="part.warehouse" :disabled="isReadOnly" type="text" placeholder="Warehouse"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}" />
                    </td>
                    <td class="py-2.5 pr-2">
                      <select v-model="part.store_impact" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}">
                        <option value="Reduce Stock">Reduce Stock</option>
                        <option value="No Impact">No Impact</option>
                        <option value="Return to Store">Return to Store</option>
                      </select>
                    </td>
                    <td class="py-2.5 pr-2">
                      <input v-model.number="part.cost" :disabled="isReadOnly" type="number" min="0"
                        class="w-24 px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}" />
                    </td>
                    <td v-if="!isReadOnly" class="py-2.5">
                      <button @click="partsUsed.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                    </td>
                  </tr>
                  <tr v-if="partsUsed.length === 0">
                    <td :colspan="isReadOnly ? 6 : 7" class="py-4 text-center text-xs text-gray-400">
                      No parts added yet.
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="!isReadOnly">
                  <tr>
                    <td colspan="7" class="pt-3">
                      <button @click="partsUsed.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '', cost: 0, store_impact: 'Reduce Stock' })"
                        class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Part</button>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <p v-if="task.stock_entry" class="text-xs text-gray-400 mt-3">
              Stock Entry: <span class="font-mono text-gray-600">{{ task.stock_entry }}</span>
            </p>
          </div>

          <!-- Maintenance Checklist -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Maintenance Checklist</h3>
            <div class="flex items-center gap-6 flex-wrap">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.fault_diagnosed" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Fault diagnosed</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.parts_replaced" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Parts replaced</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.test_run_passed" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Test run passed</span>
              </label>
              <label v-if="form.inspection_required" class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.supervisor_verified" :disabled="isReadOnly" class="w-4 h-4 accent-blue-500" />
                <span class="text-xs text-gray-700">Supervisor verified</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Right: Status panel -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Status Update</h3>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Current Task Status</p>
              <select v-model="form.status" :disabled="isReadOnly"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="{'bg-gray-100': isReadOnly}">
                <option value="Open">Open</option>
                <option value="In Progress">In Progress</option>
                <option value="Hold">On Hold</option>
                <option value="Done">Done</option>
              </select>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Final Asset Status</p>
              <select v-model="form.final_asset_status" :disabled="isReadOnly"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="{'bg-gray-100': isReadOnly}">
                <option value="">— select —</option>
                <option value="Operational">Operational</option>
                <option value="Out of Service">Out of Service</option>
                <option value="Under Repair">Under Repair</option>
                <option value="Decommissioned">Decommissioned</option>
              </select>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Inspection Required</p>
              <label class="flex items-center gap-2 cursor-pointer bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200"
                :class="{'opacity-60 pointer-events-none': isReadOnly}">
                <input type="checkbox" v-model="form.inspection_required" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Yes, supervisor must verify repair</span>
              </label>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Work Performed</p>
              <textarea v-model="form.work_performed" :disabled="isReadOnly" rows="3"
                placeholder="Describe what was done..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                :class="{'bg-gray-100': isReadOnly}"></textarea>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Completion Notes</p>
              <textarea v-model="form.completion_notes" :disabled="isReadOnly" rows="4"
                placeholder="Diagnosis, repair actions, testing result, or follow-up recommendation..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                :class="{'bg-gray-100': isReadOnly}"></textarea>
            </div>
            <div v-if="isReadOnly" class="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2">
              <span class="text-blue-400">🔒</span>
              <p class="text-xs text-blue-600">This task has been submitted and is read-only.</p>
            </div>
          </div>

          <!-- Quick Summary -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
            <h4 class="text-xs font-bold text-blue-700 mb-3">Task Summary</h4>
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Type</span>
                <span class="text-xs font-medium text-blue-800">{{ form.task_type || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Status</span>
                <span class="text-xs font-medium text-blue-800">{{ form.status || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Priority</span>
                <span class="text-xs font-semibold"
                  :class="{'text-red-600': form.priority === 'High', 'text-yellow-600': form.priority === 'Medium', 'text-blue-800': form.priority === 'Low'}">
                  {{ form.priority || '—' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Technician</span>
                <span class="text-xs font-medium text-blue-800 text-right max-w-[140px] truncate">
                  {{ technicianLabel || task.technician_name || '—' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Asset</span>
                <span class="text-xs font-medium text-blue-800 text-right max-w-[140px] truncate">
                  {{ task.asset_name || task.asset || '—' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-blue-500">Final Asset</span>
                <span class="text-xs font-medium text-blue-800">{{ form.final_asset_status || '—' }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-blue-200">
                <span class="text-xs text-blue-500">Parts</span>
                <span class="text-xs font-medium text-blue-800">{{ partsUsed.filter(p => p.item_code).length }} item(s)</span>
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
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const route = useRoute()
const taskId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const submitting = ref(false)
const task = ref(null)
const technicians = ref([])
const supervisors = ref([])
const stockItems = ref([])
const partsUsed = ref([])

// ─── Form ─────────────────────────────────────────────────────────────────────
const form = ref({
  task_type: '',
  priority: '',
  status: '',
  assigned_technician: '',
  supervisor: '',
  start_time: '',
  end_time: '',
  location: '',
  task_description: '',
  work_performed: '',
  completion_notes: '',
  final_asset_status: '',
  inspection_required: false,
  fault_diagnosed: false,
  parts_replaced: false,
  test_run_passed: false,
  supervisor_verified: false,
})

const isReadOnly = computed(() => task.value?.docstatus !== 0)

const technicianLabel = computed(() => {
  if (!form.value.assigned_technician) return null
  const t = technicians.value.find(x => x.name === form.value.assigned_technician)
  return t?.technician_name || null
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
const taskResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_task',
  auto: false
})
const saveResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.save_maintenance_task',
  auto: false
})
const submitResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.submit_maintenance_task',
  auto: false
})
const cancelResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.cancel_maintenance_task',
  auto: false
})
const techResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_technicians_for_task',
  auto: false
})
const supResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_supervisors_for_task',
  auto: false
})
const itemsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_items_for_parts',
  auto: false
})

// ─── Load task ────────────────────────────────────────────────────────────────
async function loadTask() {
  loading.value = true
  loadError.value = null
  try {
    const res = await taskResource.fetch({ task_name: taskId })
    console.log('[MaintenanceTask] get_maintenance_task:', res)
    task.value = res

    // Populate form
    form.value = {
      task_type: res.task_type || '',
      priority: res.priority || 'Medium',
      status: res.status || 'Open',
      assigned_technician: res.assigned_technician || '',
      supervisor: res.supervisor || '',
      start_time: res.start_time ? res.start_time.slice(0, 16) : '',
      end_time: res.end_time ? res.end_time.slice(0, 16) : '',
      location: res.location || '',
      task_description: res.task_description || '',
      work_performed: res.work_performed || '',
      completion_notes: res.completion_notes || '',
      final_asset_status: res.final_asset_status || '',
      inspection_required: Boolean(res.inspection_required),
      fault_diagnosed: Boolean(res.fault_diagnosed),
      parts_replaced: Boolean(res.parts_replaced),
      test_run_passed: Boolean(res.test_run_passed),
      supervisor_verified: Boolean(res.supervisor_verified),
    }

    partsUsed.value = (res.parts_used || []).map(p => ({
      item_code: p.item_code || '',
      item_name: p.item_name || '',
      qty: p.qty || 1,
      uom: p.uom || '',
      warehouse: p.warehouse || '',
      cost: p.cost || 0,
      store_impact: p.store_impact || 'Reduce Stock',
    }))

  } catch (e) {
    console.error('[MaintenanceTask] load error:', e)
    loadError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

// ─── Load dropdowns ───────────────────────────────────────────────────────────
async function loadDropdowns() {
  const [techRes, supRes, itemRes] = await Promise.all([
    techResource.fetch(),
    supResource.fetch(),
    itemsResource.fetch()
  ])
  technicians.value = techRes || []
  supervisors.value = supRes || []
  stockItems.value = itemRes || []
}

// ─── Part select: auto-fill UOM ───────────────────────────────────────────────
function onPartSelect(part) {
  const item = stockItems.value.find(i => i.name === part.item_code)
  if (item) {
    part.item_name = item.item_name || item.name
    part.uom = item.stock_uom || ''
  }
}

// ─── Save draft ───────────────────────────────────────────────────────────────
async function saveDraft() {
  saving.value = true
  try {
    const res = await saveResource.fetch({
      task_name: taskId,
      task_data: form.value,
      parts_used: partsUsed.value.filter(p => p.item_code)
    })
    console.log('[MaintenanceTask] saveDraft:', res)
    if (res?.success) {
      showToast('Task saved', 'success')
      await loadTask()
    } else {
      showToast('Failed to save: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    console.error('[MaintenanceTask] saveDraft error:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    saving.value = false
  }
}

// ─── Complete / submit ────────────────────────────────────────────────────────
async function completeTask() {
  // Client-side guard
  if (!form.value.assigned_technician) {
    showToast('Assign a technician before completing', 'warning')
    return
  }
  if (!form.value.work_performed?.trim()) {
    showToast('Describe the work performed before completing', 'warning')
    return
  }

  // Save first, then submit
  submitting.value = true
  try {
    const saveRes = await saveResource.fetch({
      task_name: taskId,
      task_data: { ...form.value, status: 'Done' },
      parts_used: partsUsed.value.filter(p => p.item_code)
    })
    if (!saveRes?.success) {
      showToast('Save failed: ' + (saveRes?.error || 'Unknown error'))
      return
    }

    const res = await submitResource.fetch({ task_name: taskId })
    console.log('[MaintenanceTask] completeTask:', res)
    if (res?.success) {
      showToast('Task completed and submitted', 'success')
      await loadTask()
    } else {
      showToast('Failed to submit: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    console.error('[MaintenanceTask] completeTask error:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    submitting.value = false
  }
}

// ─── Cancel submitted task ────────────────────────────────────────────────────
async function cancelTask() {
  if (!confirm('Are you sure you want to cancel this submitted task?')) return
  try {
    const res = await cancelResource.fetch({ task_name: taskId })
    if (res?.success) {
      showToast('Task cancelled', 'warning')
      await loadTask()
    } else {
      showToast('Failed to cancel: ' + (res?.error || ''))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(() => {
  loadTask()
  loadDropdowns()
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>