<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Toast -->
    <transition-group name="toast" tag="div" class="fixed top-4 right-4 z-50 space-y-2" style="min-width:280px;max-width:360px;">
      <div v-for="t in toasts" :key="t.id"
        class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border"
        :class="{
          'bg-white border-green-200 text-green-800': t.type === 'success',
          'bg-white border-red-200 text-red-800': t.type === 'error',
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
      <p class="text-sm text-gray-400">Loading request...</p>
    </div>

    <div v-else-if="loadError" class="flex flex-col items-center justify-center h-64 gap-3">
      <p class="text-sm font-medium text-gray-700">Failed to load request</p>
      <p class="text-xs text-gray-400">{{ loadError }}</p>
      <button @click="loadRequest" class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg">Retry</button>
    </div>

    <template v-else-if="req">

      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-900">{{ req.name }}</h2>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ req.issue_type }} • {{ req.room_number || req.room }} •
            <span :class="priorityTextClass(req.priority)">{{ req.priority }}</span>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/maintenance/request')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Request List
          </button>

          <!-- Edit (unapproved only) -->
          <template v-if="!req.approved && req.status === 'Pending'">
            <button v-if="!editMode" @click="enterEdit"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Edit</button>
            <template v-else>
              <button @click="cancelEdit" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel Edit</button>
              <button @click="saveEdit" :disabled="saving"
                class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
                <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                {{ saving ? 'Saving...' : 'Save Changes' }}
              </button>
            </template>
          </template>

          <!-- Approve -->
          <button v-if="!req.approved && req.status === 'Pending' && !editMode"
            @click="approveRequest" :disabled="approving"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
            <svg v-if="approving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            {{ approving ? 'Approving...' : 'Approve' }}
          </button>

          <!-- Convert to Task (Maintenance type only) -->
          <button v-if="req.approved && req.status === 'Pending' && !req.linked_task && !editMode && req.request_type === 'Maintenance'"
            @click="showConvertModal = true"
            class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">
            Convert to Task
          </button>

          <!-- View linked task -->
          <button v-if="req.linked_task && !editMode"
            @click="router.push({ name: 'MaintenanceTask', params: { id: req.linked_task.name } })"
            class="px-4 py-2 text-xs font-semibold text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
            View Task → {{ req.linked_task.name }}
          </button>
        </div>
      </div>

      <!-- Status bar -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-3 flex items-center gap-5 flex-wrap">
        <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusBadgeClass(req.status)">{{ req.status }}</span>
        <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
          :class="req.request_type === 'Repair' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
          {{ req.request_type === 'Repair' ? '🔧 Repair' : '🛠 Maintenance' }}
        </span>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Priority:</span>
          <span class="text-xs font-semibold" :class="priorityTextClass(req.priority)">{{ req.priority }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Approved:</span>
          <span class="text-xs font-semibold" :class="req.approved ? 'text-green-600' : 'text-gray-400'">
            {{ req.approved ? '✓ Yes' : 'Not yet' }}
          </span>
        </div>
        <div v-if="req.approval_time" class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Approved at:</span>
          <span class="text-xs text-gray-600">{{ formatDate(req.approval_time) }}</span>
        </div>
        <div v-if="req.linked_task" class="flex items-center gap-1.5 ml-auto">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          <span class="text-xs text-green-600 font-medium">Task → {{ req.linked_task.name }}</span>
        </div>
        <div v-if="editMode" class="flex items-center gap-1.5 ml-auto">
          <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          <span class="text-xs text-blue-600 font-medium">Editing</span>
        </div>
      </div>

      <!-- Body -->
      <div style="display:grid;grid-template-columns:1fr 300px;gap:20px;">

        <!-- Left -->
        <div class="space-y-4">

          <!-- VIEW -->
          <template v-if="!editMode">
            <div class="bg-white rounded-xl border border-gray-200 p-5">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Request Details</h3>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Request ID</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-mono text-gray-700">{{ req.name }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Issue Type</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.issue_type }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Priority</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold" :class="priorityTextClass(req.priority)">{{ req.priority }}</div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Room</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                    {{ req.room_number || '—' }}<span v-if="req.room" class="text-gray-400 ml-1">({{ req.room }})</span>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Asset</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                    {{ req.asset_name || '—' }}<span v-if="req.asset" class="text-gray-400 ml-1">({{ req.asset }})</span>
                  </div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Reported By</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.reported_by_name || req.reported_by || '—' }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Reported At</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatDate(req.reported_at) }}</div>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-gray-200 p-5">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Issue Description</h3>
              <div v-if="req.issue_description" class="bg-gray-50 rounded-lg px-3 py-3 text-xs text-gray-700 leading-relaxed"
                v-html="req.issue_description"></div>
              <p v-else class="text-xs text-gray-400 italic">No description provided.</p>
            </div>
          </template>

          <!-- EDIT MODE -->
          <template v-else>
            <div class="bg-white rounded-xl border border-blue-200 p-5">
              <div class="flex items-center gap-2 mb-4">
                <h3 class="text-sm font-bold text-gray-900">Edit Request</h3>
                <span class="px-2 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 rounded-full">Editing</span>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Room <span class="text-red-400">*</span></p>
                  <select v-model="editForm.room"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="">— select room —</option>
                    <option v-for="r in rooms" :key="r.name" :value="r.name">{{ r.room_number || r.name }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Asset <span class="text-red-400">*</span></p>
                  <select v-model="editForm.asset"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="">— select asset —</option>
                    <option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name || a.name }}</option>
                  </select>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Issue Type <span class="text-red-400">*</span></p>
                  <select v-model="editForm.issue_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="Plumbing">Plumbing</option><option value="Electrical">Electrical</option>
                    <option value="HVAC">HVAC</option><option value="Furniture">Furniture</option>
                    <option value="Appliance">Appliance</option><option value="Electronics">Electronics</option>
                    <option value="Structural">Structural</option><option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Priority <span class="text-red-400">*</span></p>
                  <select v-model="editForm.priority" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="Low">Low</option><option value="Medium">Medium</option>
                    <option value="High">High</option><option value="Critical">Critical</option>
                  </select>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reported By <span class="text-red-400">*</span></p>
                  <select v-model="editForm.reported_by" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                    <option value="">— select employee —</option>
                    <option v-for="e in employees" :key="e.name" :value="e.name">
                      {{ e.employee_name }}{{ e.department ? ` · ${e.department}` : '' }}
                    </option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reported At <span class="text-red-400">*</span></p>
                  <input v-model="editForm.reported_at" type="datetime-local"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Issue Description</p>
                <textarea v-model="editForm.issue_description" rows="4" placeholder="Describe the issue..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </div>
            </div>
          </template>

          <!-- Linked Task -->
          <div v-if="req.linked_task" class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Linked Maintenance Task</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-400 mb-1">Task ID</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-mono font-semibold text-blue-600 cursor-pointer hover:underline"
                  @click="router.push({ name: 'MaintenanceTask', params: { id: req.linked_task.name } })">
                  {{ req.linked_task.name }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Task Status</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.linked_task.status || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Technician</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.technician_name || '—' }}</div>
              </div>
            </div>
          </div>

          <!-- ─── ASSET REPAIR SECTION (Repair type + approved + asset_repair exists) ─── -->
          <div v-if="req.request_type === 'Repair' && req.approved && req.asset_repair"
            class="bg-white rounded-xl border border-gray-200 p-5">

            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-gray-900">Asset Repair</h3>
              <div class="flex items-center gap-2">
                <span v-if="assetRepair" class="px-2.5 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-yellow-100 text-yellow-700': assetRepair.repair_status === 'Pending',
                    'bg-blue-100 text-blue-700':     assetRepair.repair_status === 'In Progress',
                    'bg-green-100 text-green-700':   assetRepair.repair_status === 'Completed',
                  }">
                  {{ assetRepair.repair_status }}
                </span>
                <span v-if="assetRepair?.docstatus === 1" class="px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">
                  ✓ Submitted
                </span>
              </div>
            </div>

            <div v-if="arLoading" class="flex items-center gap-2 py-4">
              <svg class="animate-spin w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              <span class="text-xs text-gray-400">Loading asset repair...</span>
            </div>

            <template v-else-if="assetRepair">
              <!-- Read-only if submitted -->
              <template v-if="assetRepair.docstatus === 1">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-3">
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Repair ID</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-mono text-gray-700">{{ assetRepair.name }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Asset</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ assetRepair.asset_name || assetRepair.asset }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Failure Date</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatDate(assetRepair.failure_date) }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Completion Date</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatDate(assetRepair.completion_date) }}</div>
                  </div>
                </div>
                <div v-if="assetRepair.description" class="mb-3">
                  <p class="text-xs text-gray-400 mb-1">Description</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ assetRepair.description }}</div>
                </div>
                <div v-if="assetRepair.actions_performed" class="mb-3">
                  <p class="text-xs text-gray-400 mb-1">Actions Performed</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ assetRepair.actions_performed }}</div>
                </div>

                <!-- Mark request complete after submission -->
                <div v-if="req.status !== 'Completed'" class="mt-4 pt-4 border-t border-gray-100">
                  <button @click="markComplete" :disabled="completing"
                    class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center justify-center gap-1.5">
                    <svg v-if="completing" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    {{ completing ? 'Completing...' : '✓ Mark Request as Completed' }}
                  </button>
                  <p class="text-xs text-gray-400 mt-1.5 text-center">
                    Asset Repair is submitted. Mark request completed to allow new requests for this asset/room.
                  </p>
                </div>
                <div v-else class="mt-4 pt-4 border-t border-gray-100 text-center">
                  <span class="text-xs text-green-600 font-semibold">✓ Request Completed</span>
                </div>
              </template>

              <!-- EDITABLE — draft asset repair -->
              <template v-else>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Repair ID</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-mono text-gray-700">{{ assetRepair.name }}</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400 mb-1">Asset</p>
                    <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ assetRepair.asset_name || assetRepair.asset }}</div>
                  </div>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Repair Status <span class="text-red-400">*</span></p>
                    <select v-model="arForm.repair_status"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                      <option value="Pending">Pending</option>
                      <option value="Completed">Completed</option>
                      <option value="Cancelled">Cancelled</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">
                      Completion Date
                      <span v-if="arForm.repair_status === 'Completed'" class="text-red-400">*</span>
                    </p>
                    <input v-model="arForm.completion_date" type="datetime-local"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                  </div>
                </div>

                <div class="mb-4">
                  <p class="text-xs text-gray-500 mb-1.5">Error Description</p>
                  <textarea v-model="arForm.description" rows="3"
                    placeholder="Describe the fault or issue found..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
                </div>

                <div class="mb-4">
                  <p class="text-xs text-gray-500 mb-1.5">Actions Performed</p>
                  <textarea v-model="arForm.actions_performed" rows="3"
                    placeholder="What was done to fix the issue..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
                </div>

                <div class="mb-4">
                  <p class="text-xs text-gray-500 mb-1.5">Repair Cost (₦)</p>
                  <input v-model.number="arForm.repair_cost" type="number" min="0" placeholder="0"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </div>

                <!-- Save + Submit buttons -->
                <div class="flex items-center gap-2 pt-2 border-t border-gray-100">
                  <button @click="saveAssetRepair" :disabled="arSaving"
                    class="flex-1 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center justify-center gap-1.5">
                    <svg v-if="arSaving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    {{ arSaving ? 'Saving...' : 'Save Asset Repair' }}
                  </button>
                  <button @click="submitAssetRepair" :disabled="arSubmitting || arForm.repair_status === 'Pending'"
                    class="flex-1 py-2.5 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center justify-center gap-1.5"
                    :title="arForm.repair_status === 'Pending' ? 'Set status to Completed first' : ''">
                    <svg v-if="arSubmitting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    {{ arSubmitting ? 'Submitting...' : 'Submit Asset Repair' }}
                  </button>
                </div>
                <p v-if="arForm.repair_status === 'Pending'" class="text-xs text-yellow-600 mt-2">
                  ⚠ Set Repair Status to "Completed" before submitting.
                </p>
              </template>
            </template>

            <div v-else class="text-xs text-gray-400 italic py-2">
              Asset repair ref: <span class="font-mono">{{ req.asset_repair }}</span>
            </div>
          </div>

          <!-- Repair type + approved but no asset_repair yet (waiting for controller) -->
          <div v-else-if="req.request_type === 'Repair' && req.approved && !req.asset_repair"
            class="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
            <p class="text-xs text-yellow-700 font-semibold mb-1">Asset Repair pending creation</p>
            <p class="text-xs text-yellow-600">The Asset Repair will be created automatically by the system. Refresh the page if it hasn't appeared yet.</p>
            <button @click="loadRequest" class="mt-2 px-3 py-1.5 text-xs font-medium text-yellow-700 border border-yellow-300 rounded-lg hover:bg-yellow-100">
              Refresh
            </button>
          </div>

        </div>

        <!-- Right panel -->
        <div class="space-y-4">

          <!-- Summary -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Request Summary</h3>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Status</span>
                <span class="text-xs font-semibold" :class="{ 'text-blue-600': req.status === 'Pending', 'text-green-600': req.status === 'Completed', 'text-red-500': req.status === 'Cancelled' }">{{ req.status }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Request Type</span>
                <span class="text-xs font-medium text-gray-700">{{ req.request_type === 'Repair' ? '🔧 Repair' : '🛠 Maintenance' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Issue Type</span>
                <span class="text-xs font-medium text-gray-700">{{ req.issue_type }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Room</span>
                <span class="text-xs font-medium text-gray-700">{{ req.room_number || req.room || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Asset</span>
                <span class="text-xs font-medium text-gray-700 truncate max-w-[130px]">{{ req.asset_name || '—' }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-gray-100">
                <span class="text-xs text-gray-400">Approved</span>
                <span class="text-xs font-semibold" :class="req.approved ? 'text-green-600' : 'text-gray-400'">{{ req.approved ? '✓ Yes' : 'No' }}</span>
              </div>
              <div v-if="req.asset_repair" class="flex justify-between">
                <span class="text-xs text-gray-400">Asset Repair</span>
                <span class="text-xs font-mono text-gray-600">{{ req.asset_repair }}</span>
              </div>
              <div v-if="req.linked_task" class="flex justify-between">
                <span class="text-xs text-gray-400">Task</span>
                <span class="text-xs font-semibold text-blue-600">{{ req.linked_task.name }}</span>
              </div>
              <div v-if="req.completion_date" class="flex justify-between">
                <span class="text-xs text-gray-400">Completed</span>
                <span class="text-xs text-gray-600">{{ formatDate(req.completion_date) }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
            <p class="text-xs font-semibold text-gray-700 mb-3">Actions</p>

            <button v-if="!req.approved && req.status === 'Pending' && !editMode"
              @click="approveRequest" :disabled="approving"
              class="w-full py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 disabled:opacity-50">
              {{ approving ? 'Approving...' : '✓ Approve Request' }}
            </button>

            <button v-if="req.approved && req.status === 'Pending' && !req.linked_task && !editMode && req.request_type === 'Maintenance'"
              @click="showConvertModal = true"
              class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-xl hover:bg-green-600">
              Convert to Maintenance Task
            </button>

            <button v-if="req.linked_task"
              @click="router.push({ name: 'MaintenanceTask', params: { id: req.linked_task.name } })"
              class="w-full py-2.5 text-xs font-semibold text-blue-600 border border-blue-200 rounded-xl hover:bg-blue-50">
              Open Linked Task
            </button>

            <div v-if="req.approved" class="px-3 py-2.5 bg-green-50 rounded-lg border border-green-100 flex items-center gap-2">
              <span class="text-green-500">✓</span>
              <span class="text-xs text-green-700">Approved {{ formatDate(req.approval_time) }}</span>
            </div>

            <div v-if="!req.approved && req.status === 'Pending'" class="px-3 py-2.5 bg-yellow-50 rounded-lg border border-yellow-100">
              <p class="text-xs text-yellow-700">Not yet approved.</p>
            </div>

            <!-- Workflow hint -->
            <div class="px-3 py-2.5 bg-gray-50 rounded-lg border border-gray-100 mt-2">
              <p class="text-xs text-gray-500 font-medium mb-1">Workflow</p>
              <template v-if="req.request_type === 'Repair'">
                <p class="text-xs text-gray-400">1. Approve → Asset Repair created</p>
                <p class="text-xs text-gray-400 mt-0.5">2. Fill &amp; submit Asset Repair</p>
                <p class="text-xs text-gray-400 mt-0.5">3. Mark request Completed</p>
              </template>
              <template v-else>
                <p class="text-xs text-gray-400">1. Approve request</p>
                <p class="text-xs text-gray-400 mt-0.5">2. Convert to Maintenance Task</p>
                <p class="text-xs text-gray-400 mt-0.5">3. Assign technician &amp; track</p>
              </template>
            </div>
          </div>

        </div>
      </div>

    </template>

    <!-- Convert Modal -->
    <Teleport to="body">
      <div v-if="showConvertModal" class="fixed inset-0 z-50 flex items-center justify-center"
        style="background:rgba(0,0,0,0.55);" @click.self="showConvertModal = false">
        <div class="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-y-auto" style="max-width:560px;max-height:90vh;">
          <div class="p-6">
            <div class="flex items-start justify-between mb-5">
              <div>
                <h2 class="text-base font-bold text-gray-900">Convert to Maintenance Task</h2>
                <p class="text-xs text-gray-400 mt-1">A new Maintenance Task will be created and linked to this request.</p>
              </div>
              <button @click="showConvertModal = false" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Asset</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ req?.asset_name || req?.asset || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Priority (mapped)</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ mapPriority(req?.priority) }}</div>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
                <select v-model="convertForm.task_type"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                  <option value="Corrective">Corrective</option>
                  <option value="Preventive">Preventive</option>
                  <option value="Inspection">Inspection</option>
                  <option value="Routine">Routine</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Assign Technician</p>
                <select v-model="convertForm.assigned_technician"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                  <option value="">— select technician —</option>
                  <option v-for="t in technicians" :key="t.name" :value="t.name">
                    {{ t.technician_name }}{{ t.availability !== 'Available' ? ` (${t.availability})` : '' }}
                  </option>
                </select>
              </div>
            </div>

            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Location</p>
              <input v-model="convertForm.location" type="text" placeholder="Enter location"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>

            <div class="mb-5">
              <p class="text-xs text-gray-500 mb-1.5">Task Description</p>
              <textarea v-model="convertForm.task_description" rows="3" placeholder="Describe the work..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
            </div>

            <div class="flex items-center justify-end gap-2">
              <button @click="showConvertModal = false" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button @click="convertToTask" :disabled="converting"
                class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
                <svg v-if="converting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                {{ converting ? 'Converting...' : 'Create Task' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const route = useRoute()
const requestId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const approving = ref(false)
const saving = ref(false)
const converting = ref(false)
const completing = ref(false)
const arSaving = ref(false)
const arSubmitting = ref(false)
const arLoading = ref(false)
const showConvertModal = ref(false)
const editMode = ref(false)
const req = ref(null)
const assetRepair = ref(null)
const technicians = ref([])
const rooms = ref([])
const assets = ref([])
const employees = ref([])

// Asset repair form — matches Asset Repair doctype editable fields
const arForm = ref({
  repair_status: 'Pending',
  completion_date: '',
  description: '',
  actions_performed: '',
  repair_cost: 0,
})

const editForm = ref({})
const convertForm = ref({ task_type: 'Corrective', assigned_technician: '', location: '', task_description: '' })

// ─── Toast ────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 5000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

// ─── Resources ────────────────────────────────────────────────────────────────
const reqResource          = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_maintenance_request', auto: false })
const approveResource      = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.approve_request', auto: false })
const updateResource       = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.update_maintenance_request', auto: false })
const convertResource      = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.convert_to_task', auto: false })
const completeResource     = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.complete_maintenance_request', auto: false })
const assetRepairResource  = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_asset_repair', auto: false })
const saveArResource       = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.save_asset_repair', auto: false })
const submitArResource     = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.submit_asset_repair', auto: false })
const techResource         = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_technicians_for_task', auto: false })
const roomsResource        = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_rooms_for_request', auto: false })
const assetsResource       = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_task.get_assets_for_task', auto: false })
const employeesResource    = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_employees_for_request', auto: false })

// ─── Load ─────────────────────────────────────────────────────────────────────
async function loadRequest() {
  loading.value = true
  loadError.value = null
  try {
    const res = await reqResource.fetch({ request_name: requestId })
    req.value = res
    if (res?.issue_description) {
      convertForm.value.task_description = res.issue_description.replace(/<[^>]*>/g, '').trim()
    }
    if (res?.asset_repair) await fetchAssetRepair(res.asset_repair)
  } catch (e) {
    loadError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function fetchAssetRepair(name) {
  arLoading.value = true
  try {
    const ar = await assetRepairResource.fetch({ asset_repair_name: name })
    assetRepair.value = ar
    if (ar) {
      // Populate arForm from fetched data
      arForm.value = {
        repair_status: ar.repair_status || 'Pending',
        completion_date: ar.completion_date ? ar.completion_date.slice(0, 16) : '',
        description: ar.description || '',
        actions_performed: ar.actions_performed || '',
        repair_cost: ar.repair_cost || 0,
      }
    }
  } catch (e) {
    assetRepair.value = null
  } finally {
    arLoading.value = false
  }
}

// ─── Asset Repair actions ─────────────────────────────────────────────────────
async function saveAssetRepair() {
  arSaving.value = true
  try {
    const res = await saveArResource.fetch({
      asset_repair_name: req.value.asset_repair,
      repair_data: arForm.value
    })
    if (res?.success) { showToast('Asset Repair saved', 'success'); await fetchAssetRepair(req.value.asset_repair) }
    else showToast('Failed to save: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { arSaving.value = false }
}

async function submitAssetRepair() {
  if (arForm.value.repair_status === 'Pending') {
    showToast('Set Repair Status to "Completed" before submitting', 'warning'); return
  }
  if (!arForm.value.completion_date) {
    showToast('Completion Date is required before submitting', 'warning'); return
  }
  arSubmitting.value = true
  try {
    // Save first, then submit
    const saveRes = await saveArResource.fetch({ asset_repair_name: req.value.asset_repair, repair_data: arForm.value })
    if (!saveRes?.success) { showToast('Save failed: ' + (saveRes?.error || '')); return }

    const res = await submitArResource.fetch({ asset_repair_name: req.value.asset_repair })
    if (res?.success) {
      showToast('Asset Repair submitted successfully', 'success')
      await fetchAssetRepair(req.value.asset_repair)
    } else {
      showToast('Failed to submit: ' + (res?.error || 'Unknown'))
    }
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { arSubmitting.value = false }
}

// ─── Mark request complete ────────────────────────────────────────────────────
async function markComplete() {
  if (!confirm('Mark this request as Completed?')) return
  completing.value = true
  try {
    const res = await completeResource.fetch({ request_name: requestId })
    if (res?.success) { showToast('Request marked as Completed', 'success'); await loadRequest() }
    else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { completing.value = false }
}

// ─── Approve ──────────────────────────────────────────────────────────────────
async function approveRequest() {
  approving.value = true
  try {
    const res = await approveResource.fetch({ request_name: requestId })
    if (res?.success) { showToast('Request approved', 'success'); await loadRequest() }
    else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { approving.value = false }
}

// ─── Edit mode ────────────────────────────────────────────────────────────────
async function enterEdit() {
  editForm.value = {
    room: req.value.room || '',
    asset: req.value.asset || '',
    issue_type: req.value.issue_type || '',
    priority: req.value.priority || 'Medium',
    reported_by: req.value.reported_by || '',
    reported_at: req.value.reported_at ? req.value.reported_at.slice(0, 16) : '',
    issue_description: req.value.issue_description || '',
  }
  editMode.value = true
}

function cancelEdit() { editMode.value = false; editForm.value = {} }

async function saveEdit() {
  if (!editForm.value.room || !editForm.value.asset || !editForm.value.issue_type ||
      !editForm.value.priority || !editForm.value.reported_by) {
    showToast('Room, Asset, Issue Type, Priority and Reported By are required', 'warning'); return
  }
  saving.value = true
  try {
    const res = await updateResource.fetch({ request_name: requestId, request_data: editForm.value })
    if (res?.success) { showToast('Request updated', 'success'); editMode.value = false; await loadRequest() }
    else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { saving.value = false }
}

// ─── Convert to task ──────────────────────────────────────────────────────────
async function convertToTask() {
  converting.value = true
  try {
    const res = await convertResource.fetch({ request_name: requestId, task_data: convertForm.value })
    if (res?.success && res?.task_name) {
      showToast('Task created: ' + res.task_name, 'success')
      showConvertModal.value = false
      await loadRequest()
      setTimeout(() => router.push({ name: 'MaintenanceTask', params: { id: res.task_name } }), 800)
    } else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { converting.value = false }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function mapPriority(p) { return { Critical: 'High', High: 'High', Medium: 'Medium', Low: 'Low' }[p] || 'Medium' }
function priorityTextClass(p) { return { Critical: 'text-red-600', High: 'text-orange-500', Medium: 'text-yellow-600', Low: 'text-blue-500' }[p] || 'text-gray-600' }
function statusBadgeClass(s) { return { Pending: 'bg-blue-100 text-blue-600', Completed: 'bg-green-100 text-green-600', Cancelled: 'bg-red-100 text-red-500' }[s] || 'bg-gray-100 text-gray-500' }

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadRequest()
  const [tRes, rRes, aRes, eRes] = await Promise.all([techResource.fetch(), roomsResource.fetch(), assetsResource.fetch(), employeesResource.fetch()])
  technicians.value = tRes || []
  rooms.value = rRes || []
  assets.value = aRes || []
  employees.value = eRes || []
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>