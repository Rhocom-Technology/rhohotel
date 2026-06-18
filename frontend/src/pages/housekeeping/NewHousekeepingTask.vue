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
          'bg-white border-red-200 text-red-800':   toast.type === 'error',
          'bg-white border-yellow-200 text-yellow-800': toast.type === 'warning',
        }"
      >
        <span class="text-base leading-none mt-0.5">
          {{ toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : '⚠️' }}
        </span>
        <span class="flex-1 leading-snug">{{ toast.message }}</span>
        <button @click="removeToast(toast.id)" class="opacity-50 hover:opacity-100 text-xs leading-none mt-0.5">✕</button>
      </div>
    </transition-group>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Housekeeping Task</h2>
        <p class="text-xs text-gray-400 mt-0.5">Fill in the details below and click Create Task to save.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/housekeeping')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button @click="createTask" :disabled="creating" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          <span v-if="creating" class="flex items-center gap-1.5">
            <svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Creating...
          </span>
          <span v-else>Create Task</span>
        </button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 300px;gap:20px;">

      <!-- Left Column -->
      <div class="space-y-4">

        <!-- Basic Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Basic Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">

            <!-- Room -->
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room <span class="text-red-400">*</span></p>
              <select v-model="form.room" class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                :class="attempted && !form.room ? 'border-red-300 bg-red-50' : 'border-gray-200'">
                <option value="">— select room —</option>
                <option v-for="r in roomsList" :key="r.name" :value="r.name">
                  {{ r.room_number || r.name }}{{ r.room_type ? ` · ${r.room_type}` : '' }}
                </option>
              </select>
              <p v-if="attempted && !form.room" class="text-[10px] text-red-500 mt-1">Required</p>
            </div>

            <!-- Task Type -->
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type <span class="text-red-400">*</span></p>
              <select v-model="form.task_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                <option value="Checkout Cleaning">Checkout Cleaning</option>
                <option value="Deep Cleaning">Deep Cleaning</option>
                <option value="Turndown Service">Turndown Service</option>
                <option value="Guest Request">Guest Request</option>
                <option value="Emergency Cleaning">Emergency Cleaning</option>
              </select>
            </div>

            <!-- Priority -->
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority</p>
              <select v-model="form.priority" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Urgent">Urgent</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Assignment -->
        <div v-if="isHousekeepingManager" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Staff</p>
              <select v-model="form.employee" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">Select room attendant</option>
                <option v-for="emp in employees.data" :key="emp.name" :value="emp.name">
                  {{ emp.employee_name || emp.name }}
                </option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Start Time</p>
              <input v-model="form.start_time" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">End Time</p>
              <input v-model="form.end_time" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>
        </div>

        

       <!-- Room Inventory Management -->
<div v-if="isHousekeepingManager" class="bg-white rounded-xl border border-gray-200 p-5">

  <!-- Room Inventory Before Task -->
  <div class="mb-6">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Room Inventory Before Task</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          Read-only list of items currently recorded in this room before this task.
        </p>
      </div>

      <span class="text-[10px] font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
        Read Only
      </span>
    </div>

    <div class="overflow-x-auto border border-gray-100 rounded-lg">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Item</th>
            <th class="text-left text-xs font-medium text-gray-500 px-3 py-2 w-24">Qty</th>
            <th class="text-left text-xs font-medium text-gray-500 px-3 py-2 w-24">UOM</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-50">
          <tr v-for="item in roomInventoryBefore" :key="item.item">
            <td class="px-3 py-2.5 text-xs text-gray-700">
              {{ item.item_name || item.item }}
            </td>
            <td class="px-3 py-2.5 text-xs text-gray-700">
              {{ item.quantity || item.qty || 0 }}
            </td>
            <td class="px-3 py-2.5 text-xs text-gray-500">
              {{ item.uom || '—' }}
            </td>
          </tr>

          <tr v-if="roomInventoryBefore.length === 0">
            <td colspan="3" class="px-3 py-4 text-center text-xs text-gray-400">
              {{ form.room ? 'No inventory recorded for this room.' : 'Select a room to view inventory.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

        <!-- Inventory Update Section -->
        <div>
          <h3 class="text-sm font-bold text-gray-900 mb-1">Inventory Update Section</h3>
          <p class="text-xs text-gray-400 mb-4">
            Record what changed during this task. Added/Replaced items will reduce store stock on submit.
          </p>

          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-2/5">Item</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-20">Qty</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2 w-56">Change Type</th>
                  <th class="text-left text-xs font-medium text-gray-500 pb-2">Reason</th>
                  <th class="pb-2 w-6"></th>
                </tr>
              </thead>

              <tbody class="divide-y divide-gray-50">
                <tr v-for="(inv, idx) in inventoryItems" :key="idx">
                  <td class="py-2.5 pr-3">
                    <select
                      v-model="inv.item"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                    >
                      <option value="">— select item —</option>
                      <option v-for="si in systemItems" :key="si.name" :value="si.name">
                        {{ si.item_name && si.item_name !== si.name ? `${si.item_name} (${si.name})` : si.name }}
                      </option>
                    </select>
                  </td>

                  <td class="py-2.5 pr-3">
                    <input
                      v-model.number="inv.quantity_changed"
                      type="number"
                      min="1"
                      class="w-20 px-2 py-1.5 text-xs border border-gray-200 rounded text-center"
                    />
                  </td>

                  <td class="py-2.5 pr-3">
                    <select
                      v-model="inv.change_type"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                    >
                      <option value="Added">Added</option>
                      <option value="Removed">Removed</option>
                      <option value="Replaced">Replaced</option>
                    </select>

                    <p class="text-[10px] text-gray-400 mt-1">
                      <span v-if="inv.change_type === 'Added'">Stock will reduce.</span>
                      <span v-else-if="inv.change_type === 'Replaced'">Stock will reduce.</span>
                      <span v-else-if="inv.change_type === 'Removed'">Room inventory only. Stock will not reduce.</span>
                    </p>
                  </td>

                  <td class="py-2.5 pr-2">
                    <input
                      v-model="inv.reason"
                      type="text"
                      placeholder="Reason"
                      class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded"
                    />
                  </td>

                  <td class="py-2.5">
                    <button
                      @click="inventoryItems.splice(idx, 1)"
                      class="text-red-400 hover:text-red-600"
                    >
                      ✕
                    </button>
                  </td>
                </tr>

                <tr v-if="inventoryItems.length === 0">
                  <td colspan="5" class="py-4 text-center text-xs text-gray-400">
                    No inventory changes added yet.
                  </td>
                </tr>
              </tbody>

              <tfoot>
                <tr>
                  <td colspan="5" class="pt-3">
                    <button
                      @click="inventoryItems.push({ item: '', quantity_changed: 1, change_type: 'Added', reason: '' })"
                      class="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      + Add Item
                    </button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

        <!-- Checklist -->
        <div v-if="isHousekeepingManager" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Checklist <span class="text-xs font-normal text-gray-400">(optional)</span></h3>

          <!-- Template selector -->
          <div class="mb-4 flex items-center gap-3">
            <div class="flex-1">
              <p class="text-xs text-gray-500 mb-1.5">Load from Template</p>
              <select v-model="selectedTemplate" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">Select template...</option>
                <option v-for="t in checklistTemplates" :key="t.name" :value="t.name">{{ t.name }}</option>
              </select>
            </div>
            <div class="pt-5">
              <button @click="loadTemplate" :disabled="!selectedTemplate || loadingChecklist"
                class="px-4 py-2.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-40 flex items-center gap-1.5">
                <svg v-if="loadingChecklist" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Load
              </button>
            </div>
          </div>

          <!-- Items -->
          <div class="space-y-1.5">
            <div v-for="(item, idx) in checklistItems" :key="idx"
              class="flex items-center gap-3 px-3 py-2.5 bg-gray-50 rounded-lg group hover:bg-gray-100">
              <input type="checkbox" v-model="item.is_completed" class="w-4 h-4 accent-green-500 shrink-0" />
              <span class="text-xs text-gray-700 flex-1" :class="{'line-through text-gray-400': item.is_completed}">
                {{ item.item_description }}
              </span>
              <span v-if="item.is_mandatory" class="text-[10px] font-semibold text-red-500 uppercase tracking-wide shrink-0">required</span>
              <button @click="checklistItems.splice(idx, 1)"
                class="text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity shrink-0">✕</button>
            </div>
            <div v-if="checklistItems.length === 0 && !loadingChecklist" class="text-center py-4 text-xs text-gray-400">
              No checklist items. Load a template or add manually below.
            </div>
            <div v-if="loadingChecklist" v-for="n in 3" :key="'sk'+n"
              class="flex items-center gap-3 px-3 py-2.5 bg-gray-50 rounded-lg animate-pulse">
              <div class="w-4 h-4 rounded bg-gray-200 shrink-0"></div>
              <div class="h-3 rounded bg-gray-200 flex-1"></div>
            </div>
          </div>

          <!-- Manual add -->
          <div class="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
            <input v-model="newChecklistItem" @keydown.enter.prevent="addManualItem" type="text"
              placeholder="Add a checklist item manually..."
              class="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            <button @click="addManualItem" :disabled="!newChecklistItem.trim()"
              class="px-3 py-2 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-40">
              + Add
            </button>
          </div>
        </div>

        <!-- notes -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Task Notes<span class="text-red-400">*</span></h3>
          <textarea
            v-model="form.notes"
            rows="4"
            placeholder="Enter completion note, missing item, damage, lost item, guest request, or maintenance issue..."
            class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
            :class="attempted && !form.notes ? 'border-red-300 bg-red-50' : 'border-gray-200'"
          ></textarea>
        </div>

      </div>

      <!-- Right Column -->
      <div class="space-y-4">
        <div v-if="isHousekeepingManager" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Status & Notes</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Initial Status</p>
            <select v-model="form.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
              <option value="Pending">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Assigned">Assigned</option>
              <option value="In Progress">In Progress</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Notes</p>
            <textarea v-model="form.notes" rows="5" placeholder="Any notes for this task..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
        </div>

        <!-- Summary -->
        <div v-if="isHousekeepingManager" class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-3">Summary</h4>
          <div class="space-y-1.5">
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Room</span>
              <span class="text-xs font-medium text-blue-800">{{ selectedRoomLabel || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Type</span>
              <span class="text-xs font-medium text-blue-800">{{ form.task_type }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Priority</span>
              <span class="text-xs font-medium" :class="{
                'text-red-600': form.priority === 'Urgent',
                'text-orange-500': form.priority === 'High',
                'text-blue-800': form.priority === 'Medium' || form.priority === 'Low'
              }">{{ form.priority }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Status</span>
              <span class="text-xs font-medium text-blue-800">{{ form.status }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Inventory</span>
              <span class="text-xs font-medium text-blue-800">{{ inventoryItems.filter(i => i.item).length }} item(s)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-blue-500">Checklist</span>
              <span class="text-xs font-medium text-blue-800">{{ checklistItems.length }} item(s)</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const isHousekeepingManager = computed(() => session.hasAnyRole(['Housekeeping Manager']))

const router = useRouter()
const route = useRoute()

const creating = ref(false)
const attempted = ref(false)
const loadingChecklist = ref(false)
const newChecklistItem = ref('')
const selectedTemplate = ref('')
const systemItems = ref([])
const roomInventoryBefore = ref([])
const loadingRoomInventory = ref(false)

// ─── Toast ────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 4000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

// ─── Form state ───────────────────────────────────────────────────────────────
const form = ref({
  room: '',
  task_type: 'Checkout Cleaning',
  priority: 'Medium',
  status: 'Pending',
  employee: '',
  start_time: '',
  end_time: '',
  notes: '',
})
const inventoryItems = ref([])
const checklistItems = ref([])

// ─── Resources ────────────────────────────────────────────────────────────────
const employees = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_employees',
  auto: true
})

const roomsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_rooms',
  auto: true
})
const roomsList = computed(() => roomsResource.data || [])

// Preselect room from query param once rooms list is loaded
watch(roomsList, (list) => {
  if (list.length && !form.value.room && route.query.room) {
    const match = list.find(r => r.name === route.query.room)
    if (match) form.value.room = match.name
  }
}, { immediate: true })

const checklistTemplatesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.get_checklist_templates',
  auto: true
})
const checklistTemplates = computed(() => checklistTemplatesResource.data || [])

// Load system items for inventory select
;(async () => {
  try {
    const csrfToken = window.frappe?.csrf_token || ''
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.housekeeping.get_items', {
      headers: { 'X-Frappe-CSRF-Token': csrfToken }
    })
    const json = await res.json()
    systemItems.value = json?.message || []
  } catch (e) {
    console.error('[NewTask] get_items error:', e)
  }
})()

// ─── Computed ─────────────────────────────────────────────────────────────────
const selectedRoomLabel = computed(() => {
  if (!form.value.room) return ''
  const r = roomsList.value.find(r => r.name === form.value.room)
  return r ? (r.room_number || r.name) : form.value.room
})

watch(
  () => form.value.room,
  async (roomName) => {
    roomInventoryBefore.value = []

    if (!roomName) return

    loadingRoomInventory.value = true

    try {
      const csrfToken = window.frappe?.csrf_token || ''
      const res = await fetch(
        `/api/method/rhohotel.rhocom_hotel.api.housekeeping.get_room_inventory?room_name=${encodeURIComponent(roomName)}`,
        {
          headers: {
            'X-Frappe-CSRF-Token': csrfToken
          }
        }
      )

      const json = await res.json()
      roomInventoryBefore.value = json?.message || []
    } catch (e) {
      console.error('[NewTask] get_room_inventory error:', e)
      showToast('Could not load room inventory', 'warning')
    } finally {
      loadingRoomInventory.value = false
    }
  },
  { immediate: true }
)

// ─── Checklist ────────────────────────────────────────────────────────────────
async function loadTemplate() {
  if (!selectedTemplate.value) return
  loadingChecklist.value = true
  try {
    const csrfToken = window.frappe?.csrf_token || ''
    const res = await fetch(
      `/api/method/rhohotel.rhocom_hotel.api.housekeeping.get_checklist_template?template_name=${encodeURIComponent(selectedTemplate.value)}`,
      { headers: { 'X-Frappe-CSRF-Token': csrfToken } }
    )
    const json = await res.json()
    const items = json?.message?.items || []
    if (items.length) {
      checklistItems.value = items.map(i => ({
        item_description: i.item_description || '',
        is_mandatory: !!i.is_mandatory,
        is_completed: false,
        sequence: i.sequence || 0,
      }))
      showToast(`Loaded ${items.length} items from template`, 'success')
    } else {
      showToast('Template has no items', 'warning')
    }
  } catch (e) {
    console.error('[NewTask] loadTemplate error:', e)
    showToast('Failed to load template')
  } finally {
    loadingChecklist.value = false
  }
}

function addManualItem() {
  const text = newChecklistItem.value.trim()
  if (!text) return
  checklistItems.value.push({ item_description: text, is_mandatory: false, is_completed: false, sequence: 0 })
  newChecklistItem.value = ''
}

// ─── Create ───────────────────────────────────────────────────────────────────
const createTaskResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.housekeeping.create_task',
  auto: false
})

async function createTask() {
  attempted.value = true
  if (!form.value.room) { showToast('Room is required'); return }

  creating.value = true
  try {
    const response = await createTaskResource.fetch({
      task_data: {
        ...form.value,
        checklist_template: selectedTemplate.value || ''
      },
      inventory_items: inventoryItems.value.filter(i => i.item),
      checklist_items: checklistItems.value
    })
    console.log('[NewTask] createTask response:', response)
    if (response?.success && response?.task_name) {
      showToast('Task created successfully', 'success')
      setTimeout(() => router.replace(`/housekeeping/task/${response.task_name}`), 600)
    } else {
      const errMsg = response?.error || JSON.stringify(response)
      console.error('[NewTask] createTask failed:', errMsg)
      showToast('Failed to create: ' + errMsg)
    }
  } catch (e) {
    console.error('[NewTask] createTask exception:', e)
    showToast('Failed to create: ' + (e?.message || String(e)))
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>