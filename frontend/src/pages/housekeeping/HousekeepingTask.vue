<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Toast Notifications -->
    <transition-group name="toast" tag="div" class="fixed top-4 right-4 z-50 space-y-2" style="min-width:280px;max-width:360px;">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border"
        :class="{
          'bg-white border-green-200 text-green-800': toast.type === 'success',
          'bg-white border-red-200 text-red-800': toast.type === 'error',
          'bg-white border-blue-200 text-blue-800': toast.type === 'info',
          'bg-white border-yellow-200 text-yellow-800': toast.type === 'warning',
        }"
      >
        <span class="text-base leading-none mt-0.5">
          {{ toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : toast.type === 'warning' ? '⚠️' : 'ℹ️' }}
        </span>
        <span class="flex-1 leading-snug">{{ toast.message }}</span>
        <button @click="removeToast(toast.id)" class="opacity-50 hover:opacity-100 text-xs leading-none mt-0.5">✕</button>
      </div>
    </transition-group>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Task Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track room servicing task, assign staff, confirm replenishment, and update final room readiness.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/housekeeping')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>

        <template v-if="!isSubmitted">
          <button @click="saveTask" :disabled="saving" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
            <span v-if="saving" class="flex items-center gap-1.5">
              <svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
              Saving...
            </span>
            <span v-else>Save</span>
          </button>
          <button @click="submitTask" :disabled="submitting" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            <span v-if="submitting" class="flex items-center gap-1.5">
              <svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
              Submitting...
            </span>
            <span v-else>Submit Task</span>
          </button>
        </template>

        <template v-else>
          <button @click="cancelTask" class="px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">Cancel Task</button>
          <button @click="deleteTask" class="px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">Delete Task</button>
        </template>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col justify-center items-center h-64 gap-3">
      <svg class="animate-spin w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
      </svg>
      <p class="text-sm text-gray-400">Loading task details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="flex flex-col justify-center items-center h-64 gap-3">
      <div class="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center text-2xl">❌</div>
      <p class="text-sm font-medium text-gray-700">Failed to load task</p>
      <p class="text-xs text-gray-400 max-w-xs text-center">{{ loadError }}</p>
      <button @click="retryLoad" class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">Retry</button>
    </div>

    <div v-else-if="taskData" style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

      <!-- Left Column -->
      <div class="space-y-4">

        <!-- Task Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900">Task Details</h3>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
              :class="{
                'bg-yellow-100 text-yellow-700': taskData.docstatus === 0,
                'bg-green-100 text-green-700':   taskData.docstatus === 1,
                'bg-red-100 text-red-600':        taskData.docstatus === 2,
              }">
              <span class="w-1.5 h-1.5 rounded-full"
                :class="{
                  'bg-yellow-500': taskData.docstatus === 0,
                  'bg-green-500':  taskData.docstatus === 1,
                  'bg-red-500':    taskData.docstatus === 2,
                }"></span>
              {{ taskData.docstatus === 0 ? 'Draft' : taskData.docstatus === 1 ? 'Submitted' : 'Cancelled' }}
            </span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">
                {{ taskData.name }}
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
              <select v-model="formData.task_type" :disabled="isSubmitted" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700" :class="{'bg-gray-100': isSubmitted}">
                <option value="Checkout Cleaning">Checkout Cleaning</option>
                <option value="Deep Cleaning">Deep Cleaning</option>
                <option value="Turndown Service">Turndown Service</option>
                <option value="Guest Request">Guest Request</option>
                <option value="Emergency Cleaning">Emergency Cleaning</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority</p>
              <select v-model="formData.priority" :disabled="isSubmitted" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700" :class="{'bg-gray-100': isSubmitted}">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Urgent">Urgent</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Room Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Room Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Number</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">{{ roomDetails.room_number || taskData.room || 'N/A' }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ roomDetails.room_type_name || roomDetails.room_type || 'N/A' }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Floor</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ roomDetails.floor || 'N/A' }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ roomDetails.status || 'N/A' }}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Housekeeping Status</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ roomDetails.housekeeping_status || 'N/A' }}</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Current Guest</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ roomDetails.current_guest || 'Vacant' }}</div>
            </div>
          </div>
        </div>

        <!-- Assignment -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Staff <span class="text-red-400">*</span></p>
              <select v-model="formData.employee" :disabled="isSubmitted" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600" :class="{'bg-gray-100': isSubmitted, 'border-red-300': submitAttempted && !formData.employee}">
                <option value="">Select room attendant</option>
                <option v-for="emp in employees.data" :key="emp.name" :value="emp.name">
                  {{ emp.employee_name || emp.name }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Start Time <span class="text-red-400">*</span></p>
              <input v-model="formData.start_time" :disabled="isSubmitted" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="{'bg-gray-100': isSubmitted, 'border-red-300': submitAttempted && !formData.start_time}" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">End Time <span class="text-red-400">*</span></p>
              <input v-model="formData.end_time" :disabled="isSubmitted" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="{'bg-gray-100': isSubmitted, 'border-red-300': submitAttempted && !formData.end_time}" />
            </div>
          </div>
        </div>

        <!-- Inventory Update -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Inventory Update Section</h3>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 pb-2 w-2/5">Item</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2 w-16">Qty</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Change Type</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Reason</th>
                <th v-if="!isSubmitted" class="pb-2 w-6"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="(invItem, index) in inventoryItems" :key="index">
                <td class="py-2.5 pr-3">
                  <!-- Select pulling from ERPNext Item doctype -->
                  <div class="relative">
                    <select
                      v-model="invItem.item"
                      :disabled="isSubmitted"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded appearance-none"
                      :class="{'bg-gray-100': isSubmitted}"
                    >
                      <option value="">— select item —</option>
                      <option v-for="sysItem in systemItems" :key="sysItem.name" :value="sysItem.name">
                        {{ sysItem.item_name && sysItem.item_name !== sysItem.name
                          ? `${sysItem.item_name} (${sysItem.name})`
                          : sysItem.name }}
                      </option>
                    </select>
                    <span v-if="loadingItems" class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                      <svg class="animate-spin w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                      </svg>
                    </span>
                  </div>
                </td>
                <td class="py-2.5 pr-3">
                  <input v-model.number="invItem.quantity_changed" :disabled="isSubmitted" type="number" min="1"
                    class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center"
                    :class="{'bg-gray-100': isSubmitted}" />
                </td>
                <td class="py-2.5 pr-3">
                  <select v-model="invItem.change_type" :disabled="isSubmitted" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" :class="{'bg-gray-100': isSubmitted}">
                    <option value="Added">Added</option>
                    <option value="Removed">Removed</option>
                    <option value="Replaced">Replaced</option>
                  </select>
                </td>
                <td class="py-2.5 pr-2">
                  <input v-model="invItem.reason" :disabled="isSubmitted" type="text" placeholder="Reason"
                    class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                    :class="{'bg-gray-100': isSubmitted}" />
                </td>
                <td v-if="!isSubmitted" class="py-2.5">
                  <button @click="removeInventoryItem(index)" class="text-red-400 hover:text-red-600 transition-colors">✕</button>
                </td>
              </tr>
              <tr v-if="inventoryItems.length === 0">
                <td colspan="5" class="py-6 text-center text-xs text-gray-400">No inventory changes yet. Click "+ Add Item" to begin.</td>
              </tr>
            </tbody>
            <tfoot v-if="!isSubmitted">
              <tr>
                <td colspan="5" class="pt-3">
                  <button @click="addInventoryItem" class="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Item</button>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Housekeeping Checklist -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900">Housekeeping Checklist</h3>
            <div class="flex items-center gap-2">
              <span v-if="checklistItems.length > 0" class="px-2.5 py-1 rounded-full text-xs font-semibold"
                :class="checklistProgress === 100 ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-600'">
                {{ completedChecklistCount }}/{{ checklistItems.length }} done
              </span>
              <button
                v-if="!isSubmitted && formData.checklist_template"
                @click="reloadChecklistFromTemplate"
                :disabled="loadingChecklist"
                class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
              >
                <svg v-if="loadingChecklist" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582M20 20v-5h-.581M5.635 19A9 9 0 104.583 9"/>
                </svg>
                Reload from Template
              </button>
            </div>
          </div>

          <!-- Inline template picker when none selected -->
          <div v-if="!formData.checklist_template && !isSubmitted" class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
            <span class="text-yellow-500 text-base shrink-0">📋</span>
            <p class="text-xs text-yellow-700 flex-1">No template selected. Pick one:</p>
            <select
              v-model="formData.checklist_template"
              class="px-2 py-1.5 text-xs border border-yellow-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-300 min-w-[160px]"
            >
              <option value="">Select template...</option>
              <option v-for="t in checklistTemplates" :key="t.name" :value="t.name">{{ t.name }}</option>
            </select>
          </div>

          <!-- Progress bar -->
          <div v-if="checklistItems.length > 0" class="mb-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-green-500 rounded-full transition-all duration-500" :style="`width:${checklistProgress}%`"></div>
          </div>

          <!-- Items -->
          <div class="space-y-1.5">
            <div
              v-for="(item, idx) in checklistItems"
              :key="idx"
              class="flex items-start gap-3 px-3 py-2.5 rounded-lg transition-colors group"
              :class="item.is_completed ? 'bg-green-50' : 'bg-gray-50 hover:bg-gray-100'"
            >
              <input
                type="checkbox"
                v-model="item.is_completed"
                :disabled="isSubmitted"
                class="w-4 h-4 accent-green-500 mt-0.5 shrink-0"
              />
              <div class="flex-1 min-w-0">
                <span class="text-xs text-gray-700 leading-relaxed" :class="{ 'line-through text-gray-400': item.is_completed }">
                  {{ item.item_description }}
                </span>
                <span v-if="item.is_mandatory" class="ml-1.5 text-[10px] font-semibold text-red-500 uppercase tracking-wide">required</span>
              </div>
              <!-- Checkmark when done, remove button when draft -->
              <span v-if="item.is_completed && isSubmitted" class="text-green-500 text-xs shrink-0">✓</span>
              <template v-if="!isSubmitted">
                <span v-if="item.is_completed" class="text-green-500 text-xs shrink-0">✓</span>
                <button
                  @click="removeChecklistItem(idx)"
                  class="shrink-0 text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 text-xs leading-none"
                  title="Remove item"
                >✕</button>
              </template>
            </div>

            <!-- Skeleton while loading -->
            <template v-if="loadingChecklist">
              <div v-for="n in 4" :key="'sk'+n" class="flex items-center gap-3 px-3 py-2.5 bg-gray-50 rounded-lg animate-pulse">
                <div class="w-4 h-4 rounded bg-gray-200 shrink-0"></div>
                <div class="h-3 rounded bg-gray-200 flex-1"></div>
              </div>
            </template>

            <div v-if="checklistItems.length === 0 && !loadingChecklist" class="text-center py-6 text-gray-400 text-xs">
              {{ formData.checklist_template ? 'No items in this template.' : 'Select a checklist template to load items.' }}
            </div>
          </div>

          <!-- Manual add -->
          <div v-if="!isSubmitted" class="mt-4 pt-4 border-t border-gray-100">
            <div class="flex items-center gap-2">
              <input
                v-model="newChecklistItem"
                @keydown.enter.prevent="addManualChecklistItem"
                type="text"
                placeholder="Add a checklist item manually..."
                class="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
              <button
                @click="addManualChecklistItem"
                :disabled="!newChecklistItem.trim()"
                class="px-3 py-2 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-40"
              >
                + Add
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Status Update Section</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Current Task Status</p>
            <select v-model="formData.status" :disabled="isSubmitted" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700" :class="{'bg-gray-100': isSubmitted}">
              <option value="Pending">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Assigned">Assigned</option>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="On Hold">On Hold</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Checklist Template</p>
            <select v-model="formData.checklist_template" :disabled="isSubmitted" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600" :class="{'bg-gray-100': isSubmitted}">
              <option value="">Select Checklist Template</option>
              <option v-for="template in checklistTemplates" :key="template.name" :value="template.name">
                {{ template.name }}
              </option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Task Notes <span class="text-red-400">*</span></p>
            <textarea v-model="formData.notes" :disabled="isSubmitted" rows="4"
              placeholder="Enter completion note, maintenance issue, lost item, or guest-related comment..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
              :class="{'bg-gray-100': isSubmitted}"></textarea>
          </div>
          <div v-if="isSubmitted" class="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2">
            <span class="text-blue-400">🔒</span>
            <p class="text-xs text-blue-600">This task has been submitted and is read-only.</p>
          </div>
        </div>

        <!-- Quick Summary -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-3">Task Summary</h4>
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Type</span>
              <span class="text-xs font-medium text-blue-800">{{ formData.task_type || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Status</span>
              <span class="text-xs font-medium text-blue-800">{{ formData.status || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Priority</span>
              <span class="text-xs font-medium"
                :class="{
                  'text-red-600': formData.priority === 'Urgent',
                  'text-orange-500': formData.priority === 'High',
                  'text-blue-800': formData.priority === 'Medium' || formData.priority === 'Low'
                }">{{ formData.priority || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Assigned</span>
              <span class="text-xs font-medium text-blue-800">{{ getEmployeeName(formData.employee) || 'Unassigned' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Room</span>
              <span class="text-xs font-medium text-blue-800">{{ roomDetails.room_number || taskData.room || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-blue-200">
              <span class="text-xs text-blue-500">Doc Status</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                :class="taskData.docstatus === 1 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                {{ taskData.docstatus === 1 ? 'Submitted' : 'Draft' }}
              </span>
            </div>
            <div v-if="checklistItems.length > 0" class="flex items-center justify-between">
              <span class="text-xs text-blue-500">Checklist</span>
              <span class="text-xs font-medium text-blue-800">{{ completedChecklistCount }}/{{ checklistItems.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const route = useRoute()
const taskId = route.params.id

const saving = ref(false)
const submitting = ref(false)
const loading = ref(true)
const loadError = ref(null)
const loadingChecklist = ref(false)
const loadingItems = ref(false)
const newChecklistItem = ref('')
const systemItems = ref([])
const submitAttempted = ref(false)

// ─── Toast system ──────────────────────────────────────────────────────────────
const toasts = ref([])
let toastCounter = 0

function showToast(message, type = 'info', duration = 4000) {
  const id = ++toastCounter
  toasts.value.push({ id, message, type })
  setTimeout(() => removeToast(id), duration)
}
function removeToast(id) {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

// ─── Computed ──────────────────────────────────────────────────────────────────
const isSubmitted = computed(() => taskData.value?.docstatus === 1)
const completedChecklistCount = computed(() => checklistItems.value.filter(i => i.is_completed).length)
const checklistProgress = computed(() => {
  if (!checklistItems.value.length) return 0
  return Math.round((completedChecklistCount.value / checklistItems.value.length) * 100)
})

// ─── Form state ────────────────────────────────────────────────────────────────
const formData = ref({ task_type: '', priority: '', employee: '', status: '', start_time: '', end_time: '', notes: '', checklist_template: '' })
const inventoryItems = ref([])
const checklistItems = ref([])
const roomDetails = ref({})

// Flag: true while onSuccess is populating form data.
// Prevents the checklist_template watcher from firing a fresh template fetch
// and overwriting checklist items that were just restored from saved task data.
let _suppressChecklistWatch = false

// ─── Resources ─────────────────────────────────────────────────────────────────
const checklistTemplatesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_checklist_templates',
  auto: true
})
const checklistTemplates = computed(() => checklistTemplatesResource.data || [])

const employees = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_employees',
  auto: true
})

const roomResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_room_details',
  auto: false,
  onSuccess: (data) => { roomDetails.value = data || {} },
  onError: (err) => {
    console.error('[TaskControl] get_room_details error:', err)
    showToast('Could not load room details', 'warning')
  }
})

const taskResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_task_details',
  params: { task_name: taskId },
  auto: false,
  onSuccess: (data) => {
    console.log('[TaskControl] get_task_details response:', data)
    if (data?.length > 0) {
      const task = data[0]

      // Suppress the checklist_template watcher while we populate formData
      // so it doesn't overwrite the checklist items we're about to restore.
      _suppressChecklistWatch = true

      formData.value = {
        task_type: task.task_type || '',
        priority: task.priority || 'Medium',
        employee: task.employee || '',
        status: task.status || 'Pending',
        start_time: task.start_time ? task.start_time.slice(0, 16) : '',
        end_time: task.end_time ? task.end_time.slice(0, 16) : '',
        notes: task.notes || '',
        checklist_template: task.checklist_template || ''
      }

      if (task.room) roomResource.fetch({ room_name: task.room })
      inventoryItems.value = task.room_inventory_changes?.length ? [...task.room_inventory_changes] : []

      if (task.checklist_items?.length) {
        checklistItems.value = task.checklist_items.map(i => ({
          item_description: i.item_description || '',
          is_mandatory: Boolean(i.is_mandatory),
          is_completed: Boolean(i.is_completed),
          sequence: i.sequence || 0,
          notes: i.notes || ''
        }))
        console.log(
          '[TaskControl] Restored', checklistItems.value.length, 'checklist items,',
          checklistItems.value.filter(i => i.is_completed).length, 'checked'
        )
        // Release flag after next tick — the sync watcher already ran above,
        // this just ensures any queued microtasks also see the suppressed state.
        nextTick(() => { _suppressChecklistWatch = false })
      } else if (task.checklist_template) {
        nextTick(() => {
          _suppressChecklistWatch = false
          fetchChecklistItems(task.checklist_template, false)
        })
      } else {
        nextTick(() => { _suppressChecklistWatch = false })
      }
    }
    loading.value = false
    loadError.value = null
  },
  onError: (err) => {
    console.error('[TaskControl] get_task_details error:', err)
    loading.value = false
    loadError.value = err?.message || String(err) || 'Unknown error'
    showToast('Failed to load task: ' + loadError.value, 'error', 6000)
  }
})

const taskData = computed(() => taskResource.data?.length > 0 ? taskResource.data[0] : null)

// ─── Load ERPNext Items for inventory select ───────────────────────────────────
// Requires this in housekeeping.py:
//
//   @frappe.whitelist()
//   def get_items():
//       return frappe.get_all("Item",
//           filters={"disabled": 0, "is_stock_item": 1},
//           fields=["name", "item_name"],
//           order_by="item_name asc",
//           limit_page_length=500
//       )
async function loadSystemItems() {
  loadingItems.value = true
  try {
    const csrfToken = window.frappe?.csrf_token || ''
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.housekeeping.get_items', {
      headers: { 'X-Frappe-CSRF-Token': csrfToken }
    })
    const json = await res.json()
    console.log('[TaskControl] get_items response:', json)
    systemItems.value = json?.message || []
    if (!systemItems.value.length) {
      console.warn('[TaskControl] get_items returned 0 items. Check the API and item filters.')
    }
  } catch (err) {
    console.error('[TaskControl] loadSystemItems error:', err)
    showToast('Could not load item list: ' + (err?.message || String(err)), 'warning')
  } finally {
    loadingItems.value = false
  }
}

// ─── Checklist template watcher ────────────────────────────────────────────────
// flush:'sync' makes the watcher fire in the same tick as the assignment,
// so _suppressChecklistWatch is still true when it runs during task load.
watch(() => formData.value.checklist_template, (newVal, oldVal) => {
  if (_suppressChecklistWatch) return
  if (newVal && newVal !== oldVal) {
    fetchChecklistItems(newVal, true)
  } else if (!newVal) {
    checklistItems.value = []
  }
}, { flush: 'sync' })

// ─── Fetch checklist items from template ───────────────────────────────────────
// Task Checklist Template → child table "Checklist Template Item" (field: checklist_items)
// Each row has: item_description, is_mandatory, sequence, estimated_time
// API returns: { name, items: [ { item_description, is_mandatory, sequence, ... } ] }
// We do a raw fetch here so we can log the full raw JSON and debug easily.
async function fetchChecklistItems(templateName, showFeedback = true) {
  if (!templateName) return
  loadingChecklist.value = true
  try {
    const csrfToken = window.frappe?.csrf_token || ''
    const url = `/api/method/rhohotel.rhocom_hotel.api.housekeeping.get_checklist_template?template_name=${encodeURIComponent(templateName)}`
    const res = await fetch(url, { headers: { 'X-Frappe-CSRF-Token': csrfToken } })
    const json = await res.json()
    console.log('[TaskControl] get_checklist_template raw JSON:', JSON.stringify(json, null, 2))

    // Frappe always wraps response in { message: <return_value> }
    const payload = json?.message
    console.log('[TaskControl] checklist payload:', payload)

    // The API returns { name, items: [...] }
    // "items" comes from template.checklist_items which is the "Checklist Template Item" child table
    const items = Array.isArray(payload?.items) ? payload.items : []
    console.log('[TaskControl] checklist items count:', items.length, 'items:', items)

    if (items.length > 0) {
      checklistItems.value = items.map(i => ({
        item_description: i.item_description || '',
        is_mandatory: !!i.is_mandatory,
        is_completed: false,
        sequence: i.sequence || 0,
        notes: ''
      }))
      if (showFeedback) showToast(`Loaded ${checklistItems.value.length} checklist items`, 'success')
    } else {
      checklistItems.value = []
      // Log full payload so we can see exactly what came back
      console.warn('[TaskControl] 0 items returned. Full payload was:', JSON.stringify(payload, null, 2))
      if (showFeedback) {
        showToast(
          'Template returned 0 items. Check browser console for the raw API response.',
          'warning',
          7000
        )
      }
    }
  } catch (err) {
    console.error('[TaskControl] fetchChecklistItems error:', err)
    checklistItems.value = []
    showToast('Failed to load template: ' + (err?.message || String(err)), 'error')
  } finally {
    loadingChecklist.value = false
  }
}

function reloadChecklistFromTemplate() {
  if (!formData.value.checklist_template) { showToast('No template selected', 'warning'); return }
  fetchChecklistItems(formData.value.checklist_template, true)
}

function addManualChecklistItem() {
  const text = newChecklistItem.value.trim()
  if (!text) return
  checklistItems.value.push({ item_description: text, is_mandatory: false, is_completed: false, sequence: checklistItems.value.length + 1, notes: '' })
  newChecklistItem.value = ''
}

function removeChecklistItem(index) {
  checklistItems.value.splice(index, 1)
}

// ─── Inventory helpers ─────────────────────────────────────────────────────────
function addInventoryItem() {
  inventoryItems.value.push({ item: '', quantity_changed: 1, change_type: 'Added', reason: '' })
}
function removeInventoryItem(index) {
  inventoryItems.value.splice(index, 1)
}

// ─── Employee lookup ───────────────────────────────────────────────────────────
function getEmployeeName(employeeId) {
  if (!employeeId || !employees.data) return null
  const emp = employees.data.find(e => e.name === employeeId)
  return emp ? emp.employee_name : employeeId
}

// ─── Retry ─────────────────────────────────────────────────────────────────────
function retryLoad() {
  loading.value = true
  loadError.value = null
  taskResource.fetch()
}

// ─── Save ──────────────────────────────────────────────────────────────────────
const saveTaskResource = createResource({ url: 'rhohotel.rhocom_hotel.api.housekeeping.update_task', auto: false })

async function saveTask() {
  saving.value = true
  try {
    const response = await saveTaskResource.fetch({
      task_name: taskId,
      task_data: formData.value,
      inventory_items: inventoryItems.value,
      checklist_items: checklistItems.value
    })
    console.log('[TaskControl] saveTask response:', response)
    // frappe-ui unwraps .message, so response IS message directly
    if (response?.success) {
      showToast('Task saved successfully', 'success')
      taskResource.reload()
    } else {
      const errMsg = response?.error || response?.message?.error || JSON.stringify(response)
      console.error('[TaskControl] saveTask failed:', errMsg)
      showToast('Failed to save: ' + errMsg, 'error')
    }
  } catch (err) {
    console.error('[TaskControl] saveTask exception:', err)
    showToast('Failed to save: ' + (err?.message || String(err)), 'error')
  } finally {
    saving.value = false
  }
}

// ─── Submit ────────────────────────────────────────────────────────────────────
const submitTaskResource = createResource({ url: 'rhohotel.rhocom_hotel.api.housekeeping.submit_task', auto: false })

async function submitTask() {
  submitAttempted.value = true
  const errors = []

  // 1. Status must be Completed
  if (formData.value.status !== 'Completed') {
    errors.push(`Status must be "Completed" before submitting (currently "${formData.value.status}")`)
  }

  // 2. Assigned staff required
  if (!formData.value.employee) {
    errors.push('Assigned staff is required')
  }

  // 3. Start time required
  if (!formData.value.start_time) {
    errors.push('Start time is required')
  }

  // 4. End time required
  if (!formData.value.end_time) {
    errors.push('End time is required')
  }

  // 5. End time must be after start time
  if (formData.value.start_time && formData.value.end_time && formData.value.end_time <= formData.value.start_time) {
    errors.push('End time must be after start time')
  }

  // 6. Notes required
  if (!formData.value.notes?.trim()) {
    errors.push('Task notes are required')
  }

  // 7. Mandatory checklist items
  const incomplete = checklistItems.value.filter(i => i.is_mandatory && !i.is_completed)
  if (incomplete.length > 0) {
    errors.push(`${incomplete.length} mandatory checklist item(s) not yet completed`)
  }

  if (errors.length > 0) {
    errors.forEach(e => showToast(e, 'error', 5000))
    return
  }

  // Save first to persist any unsaved changes, then submit
  submitting.value = true
  try {
    // Persist current state before submitting
    const saveRes = await saveTaskResource.fetch({
      task_name: taskId,
      task_data: formData.value,
      inventory_items: inventoryItems.value,
      checklist_items: checklistItems.value
    })
    if (!saveRes?.success) {
      const errMsg = saveRes?.error || 'Failed to save before submit'
      console.error('[TaskControl] pre-submit save failed:', errMsg)
      showToast('Save failed: ' + errMsg, 'error')
      return
    }

    const response = await submitTaskResource.fetch({ task_name: taskId })
    console.log('[TaskControl] submitTask response:', response)
    if (response?.success) {
      submitAttempted.value = false
      showToast('Task submitted successfully', 'success')
      taskResource.reload()
    } else {
      const errMsg = response?.error || JSON.stringify(response)
      console.error('[TaskControl] submitTask failed:', errMsg)
      showToast('Failed to submit: ' + errMsg, 'error')
    }
  } catch (err) {
    console.error('[TaskControl] submitTask exception:', err)
    showToast('Failed to submit: ' + (err?.message || String(err)), 'error')
  } finally {
    submitting.value = false
  }
}

// ─── Cancel ────────────────────────────────────────────────────────────────────
const cancelTaskResource = createResource({ url: 'rhohotel.rhocom_hotel.api.housekeeping.cancel_task', auto: false })

async function cancelTask() {
  if (!confirm('Are you sure you want to cancel this task?')) return
  try {
    const response = await cancelTaskResource.fetch({ task_name: taskId })
    console.log('[TaskControl] cancelTask response:', response)
    if (response?.success) {
      showToast('Task cancelled', 'info')
      taskResource.reload()
    } else {
      const errMsg = response?.error || JSON.stringify(response)
      console.error('[TaskControl] cancelTask failed:', errMsg)
      showToast('Failed to cancel: ' + errMsg, 'error')
    }
  } catch (err) {
    console.error('[TaskControl] cancelTask exception:', err)
    showToast('Failed to cancel: ' + (err?.message || String(err)), 'error')
  }
}

// ─── Delete ────────────────────────────────────────────────────────────────────
const deleteTaskResource = createResource({ url: 'rhohotel.rhocom_hotel.api.housekeeping.delete_task', auto: false })

async function deleteTask() {
  if (!confirm('Are you sure you want to delete this task? This cannot be undone.')) return
  try {
    const response = await deleteTaskResource.fetch({ task_name: taskId })
    console.log('[TaskControl] deleteTask response:', response)
    if (response?.success) {
      showToast('Task deleted', 'info')
      router.push('/housekeeping')
    } else {
      const errMsg = response?.error || JSON.stringify(response)
      console.error('[TaskControl] deleteTask failed:', errMsg)
      showToast('Failed to delete: ' + errMsg, 'error')
    }
  } catch (err) {
    console.error('[TaskControl] deleteTask exception:', err)
    showToast('Failed to delete: ' + (err?.message || String(err)), 'error')
  }
}

// ─── Mount ─────────────────────────────────────────────────────────────────────
onMounted(() => {
  loadSystemItems()
  if (taskId && taskId !== 'new') {
    taskResource.fetch()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to { opacity: 0; transform: translateX(20px); }
</style>