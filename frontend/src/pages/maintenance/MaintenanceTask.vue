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

    <!-- Access Denied -->
    <div v-else-if="accessDenied" class="flex flex-col items-center justify-center h-64 gap-4">
      <div class="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center">
        <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m0 0v2m0-2h2m-2 0H10m2-6V7m0 0V5m0 2h2m-2 0H10M4.93 4.93l14.14 14.14" />
        </svg>
      </div>
      <div class="text-center">
        <p class="text-sm font-semibold text-gray-800">Access Restricted</p>
        <p class="text-xs text-gray-400 mt-1 max-w-xs">You can only view tasks where you are the assigned technician, supervisor/witness, or the person who reported the issue.</p>
      </div>
      <button @click="router.push('/maintenance/list')"
        class="px-5 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
        Back to Maintenance List
      </button>
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
            <h2 class="text-sm font-bold text-gray-900">{{ task.name }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ task.task_type }} · {{ task.location || '—' }} · <span :class="priorityTextClass(task.priority)">{{ task.priority }}</span></p>
          </div>
          <!-- Workflow state badge -->
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
            :class="workflowBadgeClass(task.workflow_state)">
            <span class="w-1.5 h-1.5 rounded-full" :class="workflowDotClass(task.workflow_state)"></span>
            {{ task.workflow_state || (task.docstatus === 1 ? 'Completed' : 'Draft') }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/maintenance/list')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Task List
          </button>
          <button v-if="task.maintenance_request"
            @click="router.push({ name: 'SavedMaintenanceRequest', params: { id: task.maintenance_request } })"
            class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
            View Request
          </button>

          <!-- Draft actions — only available when workflow_state is In Progress -->
          <template v-if="task.docstatus === 0 && isEditable">
            <button @click="saveDraft" :disabled="saving"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5">
              <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ saving ? 'Saving...' : 'Save Draft' }}
            </button>
          </template>

          <!-- Submitted / completed -->
          <template v-if="task.docstatus === 1">
            <span class="px-3 py-2 text-xs font-semibold text-green-600 bg-green-50 border border-green-200 rounded-lg">
              ✓ Completed
            </span>
          </template>
        </div>
      </div>

      <!-- Workflow state info banner -->
      <div v-if="task.docstatus === 0 && task.workflow_state && task.workflow_state !== 'In Progress'"
        class="bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-3 flex items-center gap-3">
        <span class="text-yellow-500 text-base">⏳</span>
        <div>
          <p class="text-xs font-semibold text-yellow-800">Pending Approval — {{ task.workflow_state }}</p>
          <p class="text-xs text-yellow-600 mt-0.5">This task is currently awaiting approval and cannot be edited</p>
        </div>
      </div>

      <!-- Body -->
      <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

        <!-- Left -->
        <div class="space-y-4">

          <!-- Request origin (read-only, auto-filled from request) -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-bold text-gray-900">Request Origin</h3>
              <span class="px-2 py-0.5 text-[10px] font-semibold bg-gray-100 text-gray-500 rounded-full">Read-only · auto-filled from request</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-3">
              <div>
                <p class="text-xs text-gray-400 mb-1">Reported By</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.reported_by_name || task.reported_by || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Requesting Department</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.requesting_department_name || task.requesting_department || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Issue Type</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.issue_type || '—' }}
                </div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-400 mb-1">Supervisor / Witness</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.supervisor_name || task.supervisor || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Witness Department</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.witness_department_name || task.witness_department || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Location Type</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ task.request_location_type || '—' }}
                </div>
              </div>
            </div>
              <div v-if="task.asset" class="mt-3">
                <p class="text-xs text-gray-400 mb-1.5">Asset</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  <span class="font-medium">{{ task.asset_name || task.asset }}</span>
                  <span v-if="task.asset_name" class="text-gray-400 ml-1.5 font-mono text-[10px]">{{ task.asset }}</span>
                </div>
              </div>

            <!-- Photos from the originating Maintenance Request -->
            <div v-if="requestPhotos.length" class="mt-3">
              <p class="text-xs text-gray-400 mb-1.5">Photos <span class="text-gray-300">(from request)</span></p>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <a v-for="(img, idx) in requestPhotos" :key="idx"
                  :href="img" target="_blank" rel="noopener">
                  <img :src="img" class="w-full h-24 object-cover rounded-lg border border-gray-200 hover:opacity-90" />
                </a>
              </div>
            </div>
          </div>

          <!-- Task Details -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Task Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-3">
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
                <p class="text-xs text-gray-400 mb-1.5">Priority <span class="text-gray-300">(read-only)</span></p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold" :class="priorityTextClass(task.priority)">
                  {{ task.priority || '—' }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1.5">Location <span class="text-gray-300">(read-only)</span></p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ task.location || '—' }}</div>
              </div>
            </div>

            <!-- Linked request -->
            <div v-if="task.maintenance_request" class="mt-3 px-3 py-2.5 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2">
              <span class="text-[10px] font-semibold text-blue-500 uppercase tracking-wide">Linked Request</span>
              <span class="text-xs text-blue-700 font-medium cursor-pointer hover:underline"
                @click="router.push({ name: 'SavedMaintenanceRequest', params: { id: task.maintenance_request } })">
                {{ task.maintenance_request }}
              </span>
              <span v-if="task.request_title" class="text-xs text-blue-400 truncate max-w-xs">— {{ task.request_title }}</span>
            </div>

            <!-- Task Description (read-only, from request) -->
            <div class="mt-3">
              <p class="text-xs text-gray-400 mb-1.5">Task Description <span class="text-gray-300">(read-only)</span></p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-600 leading-relaxed min-h-[60px]">
                {{ task.task_description || '—' }}
              </div>
            </div>
          </div>

          <!-- Timing & Work -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Timing & Work</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Start Time</p>
                <input v-if="isEditable" v-model="form.start_time" type="datetime-local"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                <div v-else class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ formatDate(form.start_time) }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">End Time <span class="text-gray-300">(optional)</span></p>
                <input v-if="isEditable" v-model="form.end_time" type="datetime-local"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                <div v-else class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ form.end_time ? formatDate(form.end_time) : 'N/A' }}
                </div>
              </div>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1.5">Work Performed <span v-if="!isReadOnly" class="text-red-400">*</span></p>
              <textarea v-model="form.work_performed" :disabled="isReadOnly" rows="3"
                placeholder="Describe what was done..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                :class="{'bg-gray-100': isReadOnly}"></textarea>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Completion Notes</p>
              <textarea v-model="form.completion_notes" :disabled="isReadOnly" rows="3"
                placeholder="Diagnosis, repair actions, testing result, follow-up..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                :class="{'bg-gray-100': isReadOnly}"></textarea>
            </div>
          </div>

          <!-- Parts Used / Collected from Store -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-sm font-bold text-gray-900">Parts Used / Collected from Store</h3>
                <p class="text-xs text-gray-400 mt-0.5">Items issued from store for this task</p>
              </div>
              <!-- Parts approval status badge -->
              <span v-if="task.parts_approval_status && task.parts_approval_status !== 'Not Requested'"
                class="px-2.5 py-1 text-xs font-semibold rounded-full"
                :class="partsApprovalClass(task.parts_approval_status)">
                {{ task.parts_approval_status }}
              </span>
            </div>

            <!-- Parts approval info -->
            <div v-if="task.parts_approved_by" class="mb-3 px-3 py-2 bg-green-50 border border-green-100 rounded-lg flex items-center gap-2">
              <span class="text-green-500 text-xs">✓</span>
              <span class="text-xs text-green-700">Approved by <strong>{{ task.parts_approved_by }}</strong> on {{ formatDate(task.parts_approved_on) }}</span>
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
                    <th v-if="isEditable" class="pb-2 w-6"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="(part, idx) in partsUsed" :key="idx">
                    <td class="py-2.5 pr-2">
                      <select v-model="part.item_code" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}"
                        @change="onPartSelect(part, stockItems)">
                        <option value="">— select item —</option>
                        <option v-for="item in stockItems" :key="item.name" :value="item.name">
                          {{ item.item_name || item.name }}
                        </option>
                      </select>
                    </td>
                    <td class="py-2.5 pr-2">
                      <input v-model.number="part.qty" :disabled="isReadOnly" type="number" min="1" step="1"
                        @input="normalizeQty(part)"
                        class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center"
                        :class="{'bg-gray-100': isReadOnly}" />
                    </td>
                    <td class="py-2.5 pr-2">
                      <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                    </td>
                    <td class="py-2.5 pr-2">
                      <select v-model="part.warehouse" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}"
                        @change="onWarehouseSelect(part)">
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
                   
                    <td v-if="isEditable" class="py-2.5">
                      <button @click="partsUsed.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                    </td>
                  </tr>
                  <tr v-if="partsUsed.length === 0">
                    <td :colspan="isEditable ? 6 : 5" class="py-4 text-center text-xs text-gray-400">
                      No parts added yet.
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="isEditable">
                  <tr>
                    <td colspan="6" class="pt-3">
                      <button @click="partsUsed.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '',available_qty: 0, stock_entry: '' })"
                        class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Part</button>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Material Issue Stock Entry link -->
            <div v-if="task.material_issue_stock_entry" class="mt-3 px-3 py-2 bg-gray-50 border border-gray-100 rounded-lg flex items-center gap-2">
              <span class="text-xs text-gray-400">Material Issue:</span>
              <span class="text-xs font-mono font-semibold text-gray-700">{{ task.material_issue_stock_entry }}</span>
            </div>
          </div>

          <!-- Parts Returned to Store -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="mb-4">
              <h3 class="text-sm font-bold text-gray-900">Parts Returned to Store</h3>
              <p class="text-xs text-gray-400 mt-0.5">Items returned back to warehouse after task completion</p>
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
                   
                    <th v-if="isEditable" class="pb-2 w-6"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="(part, idx) in partsReturned" :key="idx">
                    <td class="py-2.5 pr-2">
                      <select v-model="part.item_code" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}"
                        @change="onPartSelect(part, stockItems)">
                        <option value="">— select item —</option>
                        <option v-for="item in stockItems" :key="item.name" :value="item.name">
                          {{ item.item_name || item.name }}
                        </option>
                      </select>
                    </td>
                    <td class="py-2.5 pr-2">
                      <input v-model.number="part.qty" :disabled="isReadOnly" type="number" min="1" step="1"
                        @input="normalizeQty(part)"
                        class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center"
                        :class="{'bg-gray-100': isReadOnly}" />
                    </td>
                    <td class="py-2.5 pr-2">
                      <div class="px-2 py-1.5 text-xs text-gray-500">{{ part.uom || '—' }}</div>
                    </td>
                    <td class="py-2.5 pr-2">
                      <select v-model="part.warehouse" :disabled="isReadOnly"
                        class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                        :class="{'bg-gray-100': isReadOnly}"
                        @change="onWarehouseSelect(part)">
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
                    <td v-if="isEditable" class="py-2.5">
                      <button @click="partsReturned.splice(idx, 1)" class="text-red-400 hover:text-red-600">✕</button>
                    </td>
                  </tr>
                  <tr v-if="partsReturned.length === 0">
                    <td :colspan="isEditable ? 6 : 5" class="py-4 text-center text-xs text-gray-400">
                      No parts returned yet.
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="isEditable">
                  <tr>
                    <td colspan="6" class="pt-3">
                      <button @click="partsReturned.push({ item_code: '', item_name: '', qty: 1, uom: '', warehouse: '', cost: 0 })"
                        class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Returned Part</button>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Material Return Stock Entry link -->
            <div v-if="task.material_return_stock_entry" class="mt-3 px-3 py-2 bg-gray-50 border border-gray-100 rounded-lg flex items-center gap-2">
              <span class="text-xs text-gray-400">Material Return:</span>
              <span class="text-xs font-mono font-semibold text-gray-700">{{ task.material_return_stock_entry }}</span>
            </div>
          </div>

          <!-- Checklist -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Checklist</h3>
            <div class="flex items-center gap-6 flex-wrap">
              <label class="flex items-center gap-2" :class="isReadOnly ? 'opacity-60' : 'cursor-pointer'">
                <input type="checkbox" v-model="form.fault_diagnosed" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Fault diagnosed</span>
              </label>
              <label class="flex items-center gap-2" :class="isReadOnly ? 'opacity-60' : 'cursor-pointer'">
                <input type="checkbox" v-model="form.test_run_passed" :disabled="isReadOnly" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Test run passed</span>
              </label>
              <label class="flex items-center gap-2 opacity-60">
                <input type="checkbox" v-model="form.inspection_required" disabled class="w-4 h-4" />
                <span class="text-xs text-gray-500">Inspection required <span class="text-gray-400">(read-only)</span></span>
              </label>
            </div>
          </div>

        </div>

        <!-- Right: Status panel -->
        <div class="space-y-4">

          <!-- Task Summary -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Task Summary</h3>
            <div class="space-y-2.5">
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">Workflow State</span>
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full" :class="workflowBadgeClass(task.workflow_state)">
                  {{ task.workflow_state || '—' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Status</span>
                <span class="text-xs font-semibold" :class="statusTextClass(task.status)">{{ task.status }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Type</span>
                <span class="text-xs font-medium text-gray-700">{{ form.task_type || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Priority</span>
                <span class="text-xs font-semibold" :class="priorityTextClass(task.priority)">{{ task.priority || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Technician</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[140px] truncate">{{ task.technician_name || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Supervisor</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[140px] truncate">{{ task.supervisor_name || '—' }}</span>
              </div>
              <div class="border-t border-gray-100 pt-2 flex justify-between">
                <span class="text-xs text-gray-400">Parts Used</span>
                <span class="text-xs font-medium text-gray-700">{{ partsUsed.filter(p => p.item_code).length }} item(s)</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Parts Returned</span>
                <span class="text-xs font-medium text-gray-700">{{ partsReturned.filter(p => p.item_code).length }} item(s)</span>
              </div>
              <div v-if="task.parts_approval_status && task.parts_approval_status !== 'Not Requested'" class="flex justify-between">
                <span class="text-xs text-gray-400">Parts Approval</span>
                <span class="text-xs font-semibold" :class="partsApprovalTextClass(task.parts_approval_status)">
                  {{ task.parts_approval_status }}
                </span>
              </div>
            </div>
          </div>

         <!-- Actions -->
<!-- Actions -->
<div v-if="task.docstatus === 0" class="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
  <p class="text-xs font-semibold text-gray-700 mb-1">
    Actions
  </p>

  <!-- Save Draft -->
  <button
    v-if="isEditable"
    @click="saveDraft"
    :disabled="saving"
    class="w-full py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-1.5">

    <svg
      v-if="saving"
      class="animate-spin w-3 h-3"
      fill="none"
      viewBox="0 0 24 24">
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"/>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"/>
    </svg>

    {{ saving ? 'Saving...' : 'Save Draft' }}
  </button>

  <!-- Draft -> In Progress -->
  <button
    v-if="task.workflow_state === 'Draft'"
    @click="applyWorkflow('Start Task')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700">
    Start Task
  </button>

  <!-- In Progress -> Store -->
  <button
    v-if="task.workflow_state === 'In Progress' && partsUsed.length > 0"
    @click="applyWorkflow('Send to Store')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-orange-600 rounded-xl hover:bg-orange-700">
    Send to Store
  </button>

  <!-- In Progress -> Facility Manager -->
  <button
    v-if="task.workflow_state === 'In Progress' && partsUsed.length === 0"
    @click="applyWorkflow('Send for approval')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-purple-600 rounded-xl hover:bg-purple-700">
    Send for approval
  </button>

  <!-- Store Approval -->
  <button
    v-if="task.workflow_state === 'Pending Store Approval'"
    @click="applyWorkflow('Approve Store Items')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700">
    Approve Store Items
  </button>

  <!-- Witness Approval -->
  <button
    v-if="task.workflow_state === 'Pending Witness Approval'"
    @click="applyWorkflow('Verify Work')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-purple-600 rounded-xl hover:bg-purple-700">
    Verify Work
  </button>

  <!-- Facility Manager Approval -->
  <button
    v-if="task.workflow_state === 'Pending Facility Manager Approval'"
    @click="applyWorkflow('Approve')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-green-700 rounded-xl hover:bg-green-800">
    Approve
  </button>

  <!-- Reject -->
  <button
    v-if="[
      'Pending Store Approval',
      'Pending Facility Manager Approval',
      'Pending Witness Approval'
    ].includes(task.workflow_state)"
    @click="applyWorkflow('Reject')"
    class="w-full py-2.5 text-xs font-semibold text-white bg-red-600 rounded-xl hover:bg-red-700">
    Reject
  </button>

  <p class="text-xs text-gray-400 text-center">
    The workflow handles Store → Manager → Witness approval.
  </p>
</div>

          <!-- Read-only notice -->
          <div v-if="isReadOnly && task.docstatus === 0" class="bg-yellow-50 rounded-xl border border-yellow-100 p-4">
            <p class="text-xs font-semibold text-yellow-800 mb-1">🔒 Awaiting Approval</p>
            <p class="text-xs text-yellow-600">This task is in <strong>{{ task.workflow_state }}</strong> state. Editing is locked until the current approver takes action</p>
          </div>

          <div v-if="task.docstatus === 1" class="bg-green-50 rounded-xl border border-green-100 p-4">
            <p class="text-xs font-semibold text-green-800 mb-1">✓ Task Completed</p>
            <p class="text-xs text-green-600">This task has been submitted and is now read-only.</p>
            <div v-if="task.material_issue_stock_entry || task.material_return_stock_entry" class="mt-2 space-y-1">
              <p v-if="task.asset" class="text-xs text-green-700">
                Asset: <span class="font-medium">{{ task.asset_name || task.asset }}</span>
              </p>
             
            </div>
          </div>

          <div v-if="task.material_issue_stock_entry" class="bg-green-50 rounded-xl border border-green-100 p-4">
            <p class="text-xs font-semibold text-green-800 mb-1">✓ Material Issue Created</p>
            <p class="text-xs text-green-600">Created after Stock Manager approval and submitted successfully</p>
            <div v-if="task.material_issue_stock_entry" class="mt-2 space-y-1">
              <p v-if="task.material_issue_stock_entry" class="text-xs text-green-700">
                Issue: <span class="font-mono">{{ task.material_issue_stock_entry }}</span>
              </p>
            </div>
          </div>

          <div v-if="task.material_return_stock_entry" class="bg-green-50 rounded-xl border border-green-100 p-4">
            <p class="text-xs font-semibold text-green-800 mb-1">✓ Material Receipt Completed</p>
            <p class="text-xs text-green-600">This stock entry has been submitted</p>
            <div v-if=" task.material_return_stock_entry" class="mt-2 space-y-1">
              <p v-if="task.material_return_stock_entry" class="text-xs text-green-700">
                Return: <span class="font-mono">{{ task.material_return_stock_entry }}</span>
              </p>
            </div>
          </div>

          <!-- Workflow guide -->
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <p class="text-xs font-semibold text-gray-700 mb-3">Workflow Steps</p>
            <div class="space-y-2">
              <div v-for="step in workflowSteps" :key="step.state"
                class="flex items-center gap-2.5">
                <span class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  :class="getStepClass(step.state)">
                  {{ getStepIcon(step.state) }}
                </span>
                <div>
                  <p class="text-xs font-medium text-gray-700">{{ step.label }}</p>
                  <p class="text-[10px] text-gray-400">{{ step.role }}</p>
                </div>
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
const accessDenied = ref(false)
const saving = ref(false)
const task = ref(null)
const stockItems = ref([])
const warehouses = ref([])
const partsUsed = ref([])
const partsReturned = ref([])

const form = ref({
  task_type: '',
  start_time: '',
  end_time: '',
  work_performed: '',
  completion_notes: '',
  inspection_required: false,
  fault_diagnosed: false,
  test_run_passed: false,
})

// Task is editable only when docstatus=0 AND workflow_state is Draft or In Progress
const isEditable = computed(() =>
  task.value?.docstatus === 0 &&
  ['Draft', 'In Progress'].includes(task.value?.workflow_state) &&
  Boolean(task.value?.can_edit)
)
const isReadOnly = computed(() => !isEditable.value)

// Photos uploaded on the originating Maintenance Request -- read-only here,
// shown so the technician can see what was reported without navigating away.
const requestPhotos = computed(() => {
  if (!task.value) return []
  return [task.value.request_image_1, task.value.request_image_2, task.value.request_image_3].filter(Boolean)
})

const workflowSteps = [
  { state: 'Draft',                        label: 'Draft',                      role: 'Technician' },
  { state: 'In Progress',                  label: 'In Progress',                role: 'Technician' },
  { state: 'Pending Store Approval',           label: 'Pending Store Approval',         role: 'Stock Manager' },
  { state: 'Pending Facility Manager Approval', label: 'Facility Manager Approval',       role: 'Facilities Manager' },
  { state: 'Pending Witness Approval',          label: 'Pending Witness Approval',        role: 'Supervisor / Witness' },
  { state: 'Completed',                    label: 'Completed',                  role: 'System' },
]

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
const taskResource  = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_maintenance_task', auto: false })
const saveResource  = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.save_maintenance_task', auto: false })
const itemsResource = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_items_for_parts', auto: false })
const whResource    = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_warehouses_for_parts', auto: false })
const qtyResource   = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_item_available_qty', auto: false })
const workflowResource = createResource({
  url: 'frappe.model.workflow.apply_workflow',
  auto: false
})

// ─── Load task ────────────────────────────────────────────────────────────────
async function loadTask() {
  loading.value = true
  loadError.value = null
  accessDenied.value = false
  try {
    const res = await taskResource.fetch({ task_name: taskId })
    task.value = res

    form.value = {
      task_type:         res.task_type || '',
      start_time:        res.start_time ? res.start_time.slice(0, 16) : '',
      end_time:          res.end_time ? res.end_time.slice(0, 16) : '',
      work_performed:    res.work_performed || '',
      completion_notes:  res.completion_notes || '',
      inspection_required: Boolean(res.inspection_required),
      fault_diagnosed:   Boolean(res.fault_diagnosed),
      test_run_passed:   Boolean(res.test_run_passed),
    }

    partsUsed.value = (res.parts_used || []).map(p => ({
      item_code: p.item_code || '',
      item_name: p.item_name || '',
      qty: p.qty || 1,
      uom: p.uom || '',
      warehouse: p.warehouse || '',
      available_qty: p.available_qty || 0,
stock_entry: p.stock_entry || ''
    }))

    partsReturned.value = (res.parts_returned || []).map(p => ({
      item_code: p.item_code || '',
      item_name: p.item_name || '',
      qty: p.qty || 1,
      uom: p.uom || '',
      warehouse: p.warehouse || '',
      available_qty: p.available_qty || 0,
stock_entry: p.stock_entry || ''
    }))

  } catch (e) {
    const msg = e?.message || String(e)
    if (msg.toLowerCase().includes('you can only view') || msg.toLowerCase().includes('permissionerror') || e?.exc_type === 'PermissionError') {
      accessDenied.value = true
    } else {
      loadError.value = msg
    }
  } finally {
    loading.value = false
  }
}

async function loadDropdowns() {
  const [itemRes, whRes] = await Promise.all([
    itemsResource.fetch(),
    whResource.fetch(),
  ])
  stockItems.value = itemRes || []
  warehouses.value = whRes || []
}

async function onPartSelect(part, items = stockItems.value) {
  const item = items.find(i => i.name === part.item_code)

  if (item) {
    part.item_name = item.item_name || item.name
    part.uom = item.stock_uom || ''
    part.available_qty = item.available_qty || item.actual_qty || 0
  } else {
    part.item_name = ''
    part.uom = ''
    part.available_qty = 0
  }

  await refreshAvailableQty(part)
}

async function onWarehouseSelect(part) {
  await refreshAvailableQty(part)
}

async function refreshAvailableQty(part) {
  if (!part.item_code) {
    part.available_qty = 0
    return
  }

  try {
    const res = await qtyResource.fetch({ item_code: part.item_code, warehouse: part.warehouse || '' })
    part.available_qty = Number(res?.available_qty || 0)
  } catch (_e) {
    // Keep prior value if refresh fails.
  }
}

function normalizeQty(part) {
  if (part.qty === '' || part.qty === null || part.qty === undefined) return
  const n = parseInt(part.qty, 10)
  part.qty = Number.isNaN(n) || n < 1 ? 1 : n
}

function validatePartsRows() {
  const errors = []

  const validateRow = (row, label, idx) => {
    if (!row.item_code) return
    if (!row.warehouse) errors.push(`${label} row ${idx + 1}: Warehouse is required.`)
    if (!Number.isInteger(Number(row.qty)) || Number(row.qty) < 1) {
      errors.push(`${label} row ${idx + 1}: Quantity must be an integer greater than 0.`)
    }
  }

  partsUsed.value.forEach((row, idx) => validateRow(row, 'Parts Used', idx))
  partsReturned.value.forEach((row, idx) => validateRow(row, 'Parts Returned', idx))

  return errors
}

// Field requirements for transitions guarded by a workflow condition, mirrored
// from the Maintenance Task Workflow fixture so we can give a specific error
// message instead of the generic "Not a valid Workflow Action" from Frappe.
function validateTransitionFields(action) {
  const errors = []

  if (action === 'Send to Store') {
    // Keep client checks aligned with workflow transition condition:
    // doc.parts_used and doc.start_time (work_performed not required here — task is still in progress)
    const hasParts = partsUsed.value.some(p => p.item_code)
    if (!hasParts) errors.push('At least one part is required for Send to Store.')
    if (!form.value.start_time) errors.push('Start Time is required.')
    if (form.value.start_time && form.value.end_time &&
        new Date(form.value.end_time) <= new Date(form.value.start_time)) {
      errors.push('End Time must be after Start Time.')
    }
    return errors
  }

  if (action === 'Send for approval' || action === 'Send for Approval' || action === 'Send to Witness') {
    // This is the final handoff once the work is actually done, so the full
    // completion details are required.
    const hasParts = partsUsed.value.some(p => p.item_code)
    if (hasParts) errors.push('Remove parts before sending for approval without store flow.')
    if (!form.value.start_time) errors.push('Start Time is required.')
    if (form.value.start_time && form.value.end_time &&
        new Date(form.value.end_time) <= new Date(form.value.start_time)) {
      errors.push('End Time must be after Start Time.')
    }
    if (!(form.value.work_performed || '').trim()) errors.push('Work Performed is required.')
  }

  return errors
}

async function applyWorkflow(action) {
  const rowErrors = validatePartsRows()
  if (rowErrors.length) {
    rowErrors.forEach(e => showToast(e, 'warning'))
    return
  }

  const fieldErrors = validateTransitionFields(action)
  if (fieldErrors.length) {
    fieldErrors.forEach(e => showToast(e, 'warning'))
    return
  }

  saving.value = true

  try {
    // Only persist unsaved form edits when the task is actually editable (i.e.
    // the technician is working on it in "In Progress" state). For approval
    // actions (Approve Store Items, Approve, Verify Work, Reject, etc.) the
    // form is read-only and there is nothing to save. Saving anyway is risky
    // because it re-writes parts_used from client state, potentially clearing
    // them if the component loaded with empty parts.
    if (isEditable.value) {
      const saveRes = await saveResource.fetch({
        task_name: taskId,
        task_data: form.value,
        parts_used: partsUsed.value.filter(p => p.item_code),
        parts_returned: partsReturned.value.filter(p => p.item_code),
      })
      if (!saveRes?.success) {
        showToast('Failed to save before transition: ' + (saveRes?.error || 'Unknown error'))
        return
      }
      await loadTask()
    }

    const workflowDoc = {
      ...task.value,
      doctype: 'Maintenance Task'
    }

    await workflowResource.fetch({
      doc: JSON.stringify(workflowDoc),
      action: action
    })

    showToast(`${action} successful`, 'success')
    await loadTask()
  } catch (e) {
    showToast(e?.messages?.[0] || e?.message || String(e), 'error')
  } finally {
    saving.value = false
  }
}


// ─── Save draft ───────────────────────────────────────────────────────────────
async function saveDraft() {
  const rowErrors = validatePartsRows()
  if (rowErrors.length) {
    rowErrors.forEach(e => showToast(e, 'warning'))
    return
  }

  saving.value = true
  try {
    const res = await saveResource.fetch({
      task_name: taskId,
      task_data: form.value,
      parts_used: partsUsed.value.filter(p => p.item_code),
      parts_returned: partsReturned.value.filter(p => p.item_code),
    })
    if (res?.success) {
      showToast('Task saved', 'success')
      await loadTask()
    } else {
      showToast('Failed to save: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    saving.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dt) {
  if (!dt) return 'N/A'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function priorityTextClass(p) {
  return { Critical: 'text-red-600', High: 'text-orange-500', Medium: 'text-yellow-600', Low: 'text-blue-500' }[p] || 'text-gray-600'
}

function statusTextClass(s) {
  return {
    'Open':        'text-gray-600',
    'In Progress': 'text-blue-600',
    'Done':        'text-green-600',
    'Hold':        'text-yellow-600',
    'Cancelled':   'text-red-500',
  }[s] || 'text-gray-600'
}

function workflowBadgeClass(ws) {
  return {
    'Draft':                          'bg-gray-100 text-gray-600',
    'In Progress':                    'bg-blue-100 text-blue-700',
    'Pending Store Approval':         'bg-orange-100 text-orange-700',
    'Pending Witness Approval':       'bg-purple-100 text-purple-700',
    'Pending Facility Manager Approval': 'bg-yellow-100 text-yellow-700',
    'Completed':                      'bg-green-100 text-green-700',
    'Rejected':                       'bg-red-100 text-red-600',
  }[ws] || 'bg-gray-100 text-gray-600'
}

function workflowDotClass(ws) {
  return {
    'Draft':                          'bg-gray-400',
    'In Progress':                    'bg-blue-500',
    'Pending Store Approval':         'bg-orange-500',
    'Pending Witness Approval':       'bg-purple-500',
    'Pending Facility Manager Approval': 'bg-yellow-500',
    'Completed':                      'bg-green-500',
    'Rejected':                       'bg-red-500',
  }[ws] || 'bg-gray-400'
}

function partsApprovalClass(s) {
  return {
    'Approved':         'bg-green-100 text-green-700',
    'Pending Approval': 'bg-yellow-100 text-yellow-700',
    'Rejected':         'bg-red-100 text-red-600',
    'Not Requested':    'bg-gray-100 text-gray-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

function partsApprovalTextClass(s) {
  return {
    'Approved':         'text-green-600',
    'Pending Approval': 'text-yellow-600',
    'Rejected':         'text-red-500',
  }[s] || 'text-gray-500'
}

function getStepClass(state) {
  const current = task.value?.workflow_state
  const order = ['Draft', 'In Progress', 'Pending Store Approval', 'Pending Facility Manager Approval', 'Pending Witness Approval', 'Completed']
  const ci = order.indexOf(current)
  const si = order.indexOf(state)
  if (state === current) return 'bg-blue-500 text-white'
  if (si < ci || current === 'Completed') return 'bg-green-500 text-white'
  return 'bg-gray-200 text-gray-400'
}

function getStepIcon(state) {
  const current = task.value?.workflow_state
  const order = ['Draft', 'In Progress', 'Pending Store Approval', 'Pending Facility Manager Approval', 'Pending Witness Approval', 'Completed']
  const ci = order.indexOf(current)
  const si = order.indexOf(state)
  if (state === current) return '→'
  if (si < ci || current === 'Completed') return '✓'
  return (si + 1).toString()
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